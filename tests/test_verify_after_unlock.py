from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from companion_url_security import TokenStrippingRedirectHandler, open_json_request


VERIFY_PATH = Path(__file__).resolve().parents[1] / "verify_after_unlock.py"


def load_verify_after_unlock():
    spec = importlib.util.spec_from_file_location("codex_mn_verify_after_unlock", VERIFY_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class VerifyAfterUnlockTests(unittest.TestCase):
    def test_http_json_attaches_token_only_to_exact_loopback_companion_urls(self) -> None:
        module = load_verify_after_unlock()
        token = "e" * 64

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
            "http://localhost.evil.test:48761": False,
            "http://user@localhost:48761": False,
        }
        with tempfile.TemporaryDirectory() as tmp:
            token_path = Path(tmp) / "web-action-token"
            token_path.write_text(token, encoding="ascii")
            module.ACTION_TOKEN_PATH = token_path
            for base_url, expects_token in cases.items():
                with self.subTest(base_url=base_url):
                    captured: dict[str, object] = {}

                    def fake_open(req, timeout=0):
                        captured["request"] = req
                        return Response()

                    module.COMPANION = base_url
                    with (
                        mock.patch.object(module, "open_json_request", side_effect=fake_open, create=True),
                        mock.patch.object(module.urllib.request, "urlopen", side_effect=fake_open),
                    ):
                        result = module.http_json("POST", "/marginnote/enqueue", {"action": "health"})

                    self.assertEqual(result, {"ok": True})
                    headers = {key.lower(): value for key, value in captured["request"].header_items()}
                    self.assertEqual("x-codex-action-token" in headers, expects_token)

    def test_http_json_allows_custom_url_without_reading_token(self) -> None:
        module = load_verify_after_unlock()

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self) -> bytes:
                return b'{"ok": true}'

        with tempfile.TemporaryDirectory() as tmp:
            module.COMPANION = "http://localhost.evil.test:48761"
            module.ACTION_TOKEN_PATH = Path(tmp) / "missing-token"
            with (
                mock.patch.object(module, "open_json_request", return_value=Response(), create=True),
                mock.patch.object(module.urllib.request, "urlopen", return_value=Response()),
            ):
                self.assertEqual(
                    module.http_json("POST", "/marginnote/enqueue", {"action": "health"}),
                    {"ok": True},
                )

    def test_http_json_uses_shared_redirect_safe_opener(self) -> None:
        module = load_verify_after_unlock()
        self.assertIs(module.open_json_request, open_json_request)

        initial = module.urllib.request.Request(
            "http://localhost:48761/marginnote/enqueue",
            data=b"{}",
            headers={"X-Codex-Action-Token": "e" * 64},
            method="POST",
        )
        redirected = TokenStrippingRedirectHandler().redirect_request(
            initial,
            None,
            302,
            "Found",
            {},
            "https://remote.example.test/marginnote/enqueue",
        )

        self.assertIsNotNone(redirected)
        headers = {key.lower(): value for key, value in redirected.header_items()}
        self.assertNotIn("x-codex-action-token", headers)
