from __future__ import annotations

import json
import unittest
from urllib.parse import parse_qs, unquote, urlparse

import marginnote_api_adapter


class MarginNoteApiAdapterTests(unittest.TestCase):
    def test_builds_url_api_gateway_request_with_callbacks_and_payload(self) -> None:
        request = marginnote_api_adapter.build_url_api_request(
            action="tree",
            secret="mnsec_test_secret_123",
            payload={"path": "@current", "depth": 3},
            callback_base_url="http://127.0.0.1:48761/mn-url-api/callback",
            request_id="req_test_1",
        )

        parsed = urlparse(request.url)
        params = parse_qs(parsed.query)
        self.assertEqual(parsed.scheme, "marginnote4app")
        self.assertEqual(parsed.netloc, "addon")
        self.assertEqual(parsed.path, "/api")
        self.assertEqual(params["requestId"], ["req_test_1"])
        self.assertEqual(params["action"], ["tree"])
        self.assertEqual(params["secret"], ["mnsec_test_secret_123"])
        self.assertEqual(params["x-success"], ["http://127.0.0.1:48761/mn-url-api/callback/success"])
        self.assertEqual(params["x-error"], ["http://127.0.0.1:48761/mn-url-api/callback/error"])
        self.assertEqual(json.loads(unquote(params["payload"][0])), {"path": "@current", "depth": 3})
        self.assertNotIn("mnsec_test_secret_123", request.redacted_url)
        self.assertIn("secret=[REDACTED]", request.redacted_url)

    def test_rejects_unknown_action_and_missing_secret(self) -> None:
        with self.assertRaises(ValueError):
            marginnote_api_adapter.build_url_api_request(action="format_disk", secret="mnsec_x", payload={})
        with self.assertRaises(ValueError):
            marginnote_api_adapter.build_url_api_request(action="ping", secret="", payload={})

    def test_status_hides_secret(self) -> None:
        status = marginnote_api_adapter.adapter_status(
            {"mnApiBackend": "url_api"},
            url_api_secret="mnsec_test_secret_123",
        )

        self.assertEqual(status["backend"], "url_api")
        self.assertTrue(status["urlApiConfigured"])
        self.assertTrue(status["available"])
        self.assertNotIn("mnsec_test_secret_123", json.dumps(status, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
