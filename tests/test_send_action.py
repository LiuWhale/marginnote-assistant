from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load_send_action():
    spec = importlib.util.spec_from_file_location("send_action_under_test", ROOT / "send_action.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class SendActionTests(unittest.TestCase):
    def test_request_native_capability_probe_uses_direct_action_endpoint(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True}

        argv = [
            "send_action.py",
            "request_native_capability_probe",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "request_native_capability_probe")

    def test_request_pdf_selection_probe_uses_direct_action_endpoint(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True}

        argv = [
            "send_action.py",
            "request_pdf_selection_probe",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "request_pdf_selection_probe")
        self.assertEqual(payload["topicid"], "T1")
        self.assertEqual(payload["bookmd5"], "B1")

    def test_request_web_panel_reload_uses_direct_action_endpoint(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True}

        argv = [
            "send_action.py",
            "request_web_panel_reload",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "request_web_panel_reload")
        self.assertEqual(payload["topicid"], "T1")
        self.assertEqual(payload["bookmd5"], "B1")

    def test_release_acceptance_summary_uses_direct_action_endpoint(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True}

        argv = [
            "send_action.py",
            "release_acceptance_summary",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "release_acceptance_summary")

    def test_export_annotated_pdf_uses_prompt_as_selection_text_for_direct_verification(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True}

        argv = [
            "send_action.py",
            "export_annotated_pdf",
            "--direct",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
            "--prompt",
            "Attention guided safety filter",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["prompt"], "Attention guided safety filter")
        self.assertEqual(payload["selectionText"], "Attention guided safety filter")

    def test_native_highlight_request_can_pass_selection_text_for_replay(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True, "queued": {"command": {"nativeAction": "highlight_current_selection"}}}

        argv = [
            "send_action.py",
            "request_native_highlight_selection",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
            "--selection-text",
            "Attention guided safety filter",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "request_native_highlight_selection")
        self.assertEqual(payload["selectionText"], "Attention guided safety filter")

    def test_record_appends_scoped_action_result_jsonl_for_single_document_acceptance(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True, "message": "saved", "settings": {"speed": "fast"}}

        with tempfile.TemporaryDirectory() as tmp:
            record_path = Path(tmp) / "actions.jsonl"
            argv = [
                "send_action.py",
                "settings_update",
                "--topicid",
                "T1",
                "--bookmd5",
                "B1",
                "--speed",
                "fast",
                "--record",
                "--record-path",
                str(record_path),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(send_action, "post_json", fake_post_json),
                mock.patch("builtins.print"),
            ):
                exit_code = send_action.main()

            self.assertEqual(exit_code, 0)
            rows = [json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["action"], "settings_update")
        self.assertEqual(row["topicid"], "T1")
        self.assertEqual(row["bookmd5"], "B1")
        self.assertEqual(row["endpoint"], "/marginnote/action")
        self.assertEqual(row["result"]["message"], "saved")
        self.assertEqual(row["payload"]["settings"], {"speed": "fast"})

    def test_goal_run_can_be_triggered_and_recorded_for_single_document_acceptance(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True, "goalQueue": [{"action": "chat", "prompt": "ok"}]}

        with tempfile.TemporaryDirectory() as tmp:
            record_path = Path(tmp) / "actions.jsonl"
            argv = [
                "send_action.py",
                "goal_run",
                "--topicid",
                "T1",
                "--bookmd5",
                "B1",
                "--goal-title",
                "同文档验收目标",
                "--goal-detail",
                "只生成一个后续动作。",
                "--record",
                "--record-path",
                str(record_path),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(send_action, "post_json", fake_post_json),
                mock.patch("builtins.print"),
            ):
                exit_code = send_action.main()

            self.assertEqual(exit_code, 0)
            rows = [json.loads(line) for line in record_path.read_text(encoding="utf-8").splitlines()]

        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "goal_run")
        self.assertEqual(payload["goal"], {"title": "同文档验收目标", "detail": "只生成一个后续动作。"})
        self.assertEqual(rows[0]["action"], "goal_run")
        self.assertTrue(rows[0]["result"]["goalQueue"])

    def test_request_draft_write_uses_direct_action_endpoint_with_draft_id(self) -> None:
        send_action = load_send_action()
        captured: dict[str, object] = {}

        def fake_post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["payload"] = payload
            return {"ok": True, "queued": {"command": {"nativeAction": "write_draft"}}}

        argv = [
            "send_action.py",
            "request_draft_write",
            "--topicid",
            "T1",
            "--bookmd5",
            "B1",
            "--draft-id",
            "draft-123",
        ]
        with (
            mock.patch.object(sys, "argv", argv),
            mock.patch.object(send_action, "post_json", fake_post_json),
            mock.patch("builtins.print"),
        ):
            exit_code = send_action.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured["url"], "http://127.0.0.1:48761/marginnote/action")
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["action"], "request_draft_write")
        self.assertEqual(payload["draftId"], "draft-123")


if __name__ == "__main__":
    unittest.main()
