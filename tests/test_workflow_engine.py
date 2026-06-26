import unittest

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


if __name__ == "__main__":
    unittest.main()
