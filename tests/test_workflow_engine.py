import tempfile
import unittest
from pathlib import Path

import workflow_engine


class WorkflowEngineTests(unittest.TestCase):
    def test_lists_shareable_workflow_templates(self) -> None:
        templates = workflow_engine.list_workflow_templates()

        self.assertGreaterEqual(len(templates), 3)
        self.assertIn("paper_deep_reading", [item["id"] for item in templates])
        self.assertTrue(all(item["stepCount"] > 0 for item in templates))
        self.assertTrue(all(item["confirmationPoints"] for item in templates))

    def test_infers_distinct_workflows_from_prompt(self) -> None:
        self.assertEqual(workflow_engine.infer_workflow_id("完整精读这篇论文并生成脑图"), "paper_deep_reading")
        self.assertEqual(workflow_engine.infer_workflow_id("把这个选区做成短卡"), "selection_to_cards")
        self.assertEqual(workflow_engine.infer_workflow_id("重组当前脑图结构"), "mindmap_reorganize")

    def test_preview_exposes_steps_confirmation_and_capability_status(self) -> None:
        preview = workflow_engine.build_workflow_preview(
            {"prompt": "重组当前脑图结构"},
            native_caps={"capabilityMatrix": {"nativeMindmap": {"ready": True, "available": True}}},
            mn_api={"urlApiConfigured": True},
        )

        self.assertEqual(preview["schema"], "codex.mn.workflowPreview.v1")
        self.assertEqual(preview["id"], "mindmap_reorganize")
        self.assertIn("write", preview["confirmationPoints"])
        self.assertEqual(preview["status"], "ready")
        self.assertEqual([step["action"] for step in preview["steps"]][:2], ["mn_read_tree", "reorganize_mindmap"])

    def test_workflow_run_can_resume_from_waiting_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflow_engine.configure(Path(tmp))
            created = workflow_engine.create_run(
                {"workflowId": "paper_deep_reading", "objectRef": {"objectId": "mnobj:document:x"}}
            )
            run = workflow_engine.update_step(
                created["runId"],
                "write",
                "waiting_confirmation",
                {"draftId": "draft1", "queueId": "q1"},
            )

            resumed = workflow_engine.next_runnable_step(created["runId"])

            self.assertEqual(run["workflowRun"]["status"], "waiting_confirmation")
            self.assertEqual(resumed["status"], "waiting_confirmation")
            self.assertEqual(resumed["stepId"], "write")
            self.assertEqual(resumed["evidence"]["draftId"], "draft1")

    def test_workflow_run_cancel_marks_open_steps_and_records_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workflow_engine.configure(Path(tmp))
            created = workflow_engine.create_run({"workflowId": "selection_to_cards"})
            workflow_engine.update_step(created["runId"], "explain", "queued", {"queueId": "q-explain"})

            cancelled = workflow_engine.cancel_run(created["runId"])

            self.assertTrue(cancelled["ok"], cancelled)
            self.assertEqual(cancelled["workflowRun"]["status"], "cancelled")
            self.assertEqual(cancelled["workflowRun"]["events"][-1]["event"], "workflow_cancelled")
            open_steps = [
                step
                for step in cancelled["workflowRun"]["steps"]
                if step["stepId"] in {"explain", "cards", "write"}
            ]
            self.assertTrue(all(step["status"] == "cancelled" for step in open_steps if step["status"] != "completed"))


if __name__ == "__main__":
    unittest.main()
