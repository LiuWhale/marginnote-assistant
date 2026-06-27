from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import external_gateway


class ExternalGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        external_gateway.configure(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_rejects_direct_write_without_workflow(self) -> None:
        result = external_gateway.normalize_request(
            {
                "requestId": "req1",
                "caller": "shortcut",
                "secret": "mnsec_test",
                "action": "write",
                "payload": {"path": "@id:n1", "content": "direct write"},
            }
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DIRECT_WRITE_FORBIDDEN")
        self.assertNotIn("mnsec_test", json.dumps(result, ensure_ascii=False))

    def test_accepts_workflow_request_with_callback(self) -> None:
        result = external_gateway.normalize_request(
            {
                "requestId": "req2",
                "caller": "shortcut",
                "secret": "mnsec_test",
                "action": "workflow_start",
                "x-success": "shortcuts://success?secret=mnsec_test&value=ok",
                "x-error": "shortcuts://error?token=mnsec_test",
                "payload": {"workflowId": "paper_deep_reading", "objectRef": {"objectId": "mnobj:document:x"}},
            }
        )

        self.assertTrue(result["ok"], result)
        operation = result["agentOperation"]
        self.assertEqual(operation["schema"], "codex.mn.agentOperation.v1")
        self.assertEqual(operation["external"]["requestId"], "req2")
        self.assertEqual(operation["external"]["caller"], "shortcut")
        self.assertEqual(operation["payload"]["workflowId"], "paper_deep_reading")
        self.assertNotIn("mnsec_test", json.dumps(result, ensure_ascii=False))
        self.assertIn("value=ok", operation["external"]["callback"]["success"])
        self.assertNotIn("secret=", operation["external"]["callback"]["success"])

    def test_records_request_status_and_callback_lifecycle_without_secret(self) -> None:
        normalized = external_gateway.normalize_request(
            {
                "requestId": "req3",
                "caller": "url-api",
                "secret": "mnsec_test",
                "action": "workflow_start",
                "x-success": "marginnote4app://callback?token=mnsec_test&ok=1",
                "payload": {"workflowId": "selection_to_cards"},
            }
        )
        record = external_gateway.record_request(
            {
                **normalized["externalGatewayRequest"],
                "workflowRunId": "wf_req3",
                "stage": "workflow_started",
                "result": {"ok": True, "message": "started"},
            }
        )

        self.assertTrue(record["ok"], record)
        status = external_gateway.request_status({"requestId": "req3"})
        self.assertTrue(status["ok"], status)
        self.assertEqual(status["externalGateway"]["workflowRunId"], "wf_req3")
        self.assertNotIn("mnsec_test", json.dumps(status, ensure_ascii=False))

        callback = external_gateway.update_callback(
            {
                "requestId": "req3",
                "callbackStatus": "success",
                "payload": {"updatedNotes": 2},
                "message": "done",
            }
        )

        self.assertTrue(callback["ok"], callback)
        self.assertEqual(callback["externalGateway"]["stage"], "callback_success")
        self.assertEqual(callback["externalGateway"]["callback"]["status"], "success")
        self.assertEqual(callback["externalGateway"]["callback"]["receivedCount"], 1)
        self.assertEqual(callback["externalGateway"]["callback"]["history"][0]["payload"]["updatedNotes"], 2)


if __name__ == "__main__":
    unittest.main()
