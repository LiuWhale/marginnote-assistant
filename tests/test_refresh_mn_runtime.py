from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from typing import Any


REFRESH_PATH = Path(__file__).resolve().parents[1] / "refresh_mn_runtime.py"


def load_refresh_module() -> Any:
    spec = importlib.util.spec_from_file_location("codex_mn_refresh_runtime", REFRESH_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class RefreshRuntimeTests(unittest.TestCase):
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
