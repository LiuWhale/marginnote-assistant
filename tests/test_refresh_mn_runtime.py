from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

from companion_url_security import TokenStrippingRedirectHandler


REFRESH_PATH = Path(__file__).resolve().parents[1] / "refresh_mn_runtime.py"


def load_refresh_module() -> Any:
    spec = importlib.util.spec_from_file_location("codex_mn_refresh_runtime", REFRESH_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RefreshRuntimeTests(unittest.TestCase):
    def test_post_json_attaches_install_token_only_to_exact_loopback_companion_urls(self) -> None:
        module = load_refresh_module()
        token = "b" * 64

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self) -> bytes:
                return b'{"ok": true}'

        cases = {
            "http://127.0.0.1:48761": True,
            "http://localhost:48761": True,
            "http://[::1]:48761": True,
            "https://127.0.0.1:48761": False,
            "http://127.0.0.1:48762": False,
            "http://localhost.evil.test:48761": False,
            "http://user@localhost:48761": False,
            "http://localhost:48761@evil.test": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "web-action-token"
            missing_token_path = Path(tmp) / "missing-token"
            token_path.write_text(token, encoding="ascii")
            for url, expects_token in cases.items():
                with self.subTest(url=url):
                    module.ACTION_TOKEN_PATH = token_path if expects_token else missing_token_path
                    captured: dict[str, Any] = {}

                    def fake_urlopen(req, timeout=0):
                        captured["request"] = req
                        return Response()

                    with mock.patch.object(module, "open_json_request", side_effect=fake_urlopen):
                        result = module.post_json(url, "/marginnote/action", {"action": "health"})

                    self.assertTrue(result["ok"])
                    headers = {key.lower(): value for key, value in captured["request"].header_items()}
                    self.assertEqual("x-codex-action-token" in headers, expects_token)

    def test_redirect_request_never_inherits_install_token(self) -> None:
        module = load_refresh_module()
        initial = module.request.Request(
            "http://localhost:48761/marginnote/action",
            data=b"{}",
            headers={"X-Codex-Action-Token": "b" * 64},
            method="POST",
        )

        redirected = TokenStrippingRedirectHandler().redirect_request(
            initial,
            None,
            302,
            "Found",
            {},
            "http://remote.example.test/marginnote/action",
        )

        self.assertIsNotNone(redirected)
        headers = {key.lower(): value for key, value in redirected.header_items()}
        self.assertNotIn("x-codex-action-token", headers)

    def test_addon_reload_urls_are_non_destructive(self) -> None:
        module = load_refresh_module()

        urls = module.addon_reload_urls("codex.mn.assistant")

        self.assertGreaterEqual(len(urls), 4)
        self.assertTrue(all(url.startswith("marginnote4app://addon/codex.mn.assistant") for url in urls))
        combined = "\n".join(urls).lower()
        self.assertIn("reload", combined)
        self.assertIn("enable", combined)
        self.assertNotIn("disable", combined)
        self.assertNotIn("unload", combined)
        self.assertEqual(len(urls), len(set(urls)))

    def test_try_addon_url_reload_records_each_attempt_without_requiring_ui_automation(self) -> None:
        module = load_refresh_module()
        opened: list[str] = []

        def fake_open(url: str) -> dict[str, Any]:
            opened.append(url)
            return {"returncode": 0, "stdout": "", "stderr": ""}

        attempts = module.try_addon_url_reload("codex.mn.assistant", open_url=fake_open, pause=lambda _seconds: None)

        self.assertEqual(opened, [attempt["url"] for attempt in attempts])
        self.assertTrue(all(attempt["ok"] for attempt in attempts))
        self.assertTrue(all(attempt["method"] == "open-url" for attempt in attempts))

    def test_latest_web_event_ts_prefers_runtime_web_controls_event(self) -> None:
        module = load_refresh_module()

        ts = module.latest_web_event_ts(
            {
                "mnRuntime": {"latestWebEventTs": "2026-06-11T12:34:56+0800"},
                "nativeApiCapabilities": {"event_ts": "2026-06-11T12:30:00+0800"},
            }
        )

        self.assertEqual(ts, "2026-06-11T12:34:56+0800")

    def test_wait_for_runtime_refresh_does_not_stop_at_first_non_ready_event(self) -> None:
        module = load_refresh_module()
        calls = 0
        statuses = [
            {
                "mnRuntime": {
                    "ready": False,
                    "latestNativeEventTs": "2026-06-11T12:31:00+0800",
                    "latestWebEventTs": "2026-06-11T12:30:00+0800",
                }
            },
            {
                "mnRuntime": {
                    "ready": True,
                    "latestNativeEventTs": "2026-06-11T12:31:01+0800",
                    "latestWebEventTs": "2026-06-11T12:30:01+0800",
                }
            },
        ]

        def fake_status(_base_url: str) -> dict[str, Any]:
            nonlocal calls
            item = statuses[min(calls, len(statuses) - 1)]
            calls += 1
            return item

        module.status_or_error = fake_status
        module.time.sleep = lambda _seconds: None

        result = module.wait_for_runtime_refresh(
            "http://127.0.0.1:48761",
            "2026-06-11T12:30:00+0800",
            timeout=2,
            interval=0.01,
            previous_web_ts="2026-06-11T12:29:00+0800",
        )

        self.assertTrue(result["mnRuntime"]["ready"])
        self.assertGreaterEqual(calls, 2)

    def test_cleanup_unprocessed_native_commands_acks_only_ids_created_by_refresh(self) -> None:
        module = load_refresh_module()
        calls: list[tuple[str, str, dict[str, Any]]] = []

        def fake_post(base_url: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
            calls.append((base_url, path, payload))
            return {"ok": True, "removed": 2, "remaining": 0}

        ids = module.collect_queued_command_ids(
            [
                {"ok": True, "queued": {"id": "R1"}},
                {"ok": True, "queued": {"id": "P1"}},
                {"ok": False, "queued": {"id": "IGNORED"}},
                {"ok": True, "queued": {"id": "R1"}},
            ]
        )
        result = module.cleanup_unprocessed_native_commands(
            "http://127.0.0.1:48761",
            "TOPIC1",
            "BOOK1",
            ids,
            post=fake_post,
        )

        self.assertEqual(ids, ["R1", "P1"])
        self.assertEqual(result["ok"], True)
        self.assertEqual(calls, [
            (
                "http://127.0.0.1:48761",
                "/marginnote/ack",
                {
                    "topicid": "TOPIC1",
                    "notebookid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "docmd5": "BOOK1",
                    "ids": ["R1", "P1"],
                    "source": "refresh_mn_runtime.py",
                },
            )
        ])


if __name__ == "__main__":
    unittest.main()
