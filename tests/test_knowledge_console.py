from __future__ import annotations

import unittest

import knowledge_console


class KnowledgeConsoleTests(unittest.TestCase):
    def test_matrix_routes_zero_message_axes_to_real_workspace_actions(self) -> None:
        repair_action = knowledge_console.workspace_action(
            "cache_current_pdf",
            "缓存当前 PDF",
            "request_pdf_cache",
            {"topicid": "T1", "bookmd5": "B1"},
            "source_registry",
            "缓存当前 PDF。",
        )
        actions = [
            knowledge_console.workspace_action("open_source_registry", "打开 Source Registry", "open_source_registry", {}, "source_registry", "打开来源清单。"),
            knowledge_console.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {}, "object_browser", "扫描对象。"),
            knowledge_console.workspace_action("open_object_browser", "打开对象浏览器", "object_browser", {}, "object_browser", "打开对象。"),
            knowledge_console.workspace_action("read_mindmap_tree", "读取脑图", "mn_read_tree", {}, "mindmap_studio", "读取脑图。"),
            knowledge_console.workspace_action("open_mindmap_studio", "打开 Mindmap Studio", "open_mindmap_studio", {}, "mindmap_studio", "打开脑图。"),
            knowledge_console.workspace_action("open_card_factory", "打开 Card Factory", "open_card_factory", {}, "card_factory", "打开卡片工厂。"),
            knowledge_console.workspace_action("open_workflows", "查看工作流", "workflow_list", {}, "workflow_builder", "查看 workflow。"),
            knowledge_console.workspace_action("open_workflow_builder", "打开 Workflow Builder", "open_workflow_builder", {}, "workflow_builder", "打开 workflow。"),
            knowledge_console.workspace_action("open_operation_ledger", "打开账本", "operation_ledger_list", {}, "ledger_explorer", "打开账本。"),
            knowledge_console.workspace_action("open_verification_center", "打开验证中心", "verification_report_list", {}, "verification_center", "打开验证中心。"),
        ]
        summary = {
            "topicid": "T1",
            "bookmd5": "B1",
            "documentTitle": "Paper.pdf",
            "focusObject": {"objectId": "mnobj:selection:x", "kind": "selection"},
            "objects": {"nativeScan": 2, "registry": 5},
            "mindmap": {"status": "available", "nodeCount": 8},
            "reviewQueue": {"total": 3, "due": 1},
            "workflows": {"runCount": 1, "latestStatus": "waiting_confirmation"},
            "ledger": {"total": 4},
            "readiness": {"mnApiAvailable": True},
            "sourceRegistry": {"summary": {"readable": 1, "total": 2}, "actionPlan": {"recommendedAction": repair_action}},
        }

        matrix = knowledge_console.build_matrix(summary, actions)

        self.assertEqual(matrix["schema"], "codex.mn.knowledgeConsoleMatrix.v1")
        self.assertEqual(matrix["mode"], "zero_message")
        self.assertFalse(matrix["requiresPrompt"])
        self.assertEqual(matrix["axisCount"], 7)
        axes = {axis["id"]: axis for axis in matrix["axes"]}
        self.assertEqual(
            list(axes),
            [
                "source_inventory",
                "mn_objects",
                "mindmap_baseline",
                "card_coverage",
                "workflow_runtime",
                "operation_ledger",
                "verification_evidence",
            ],
        )
        self.assertEqual(axes["source_inventory"]["schema"], "codex.mn.knowledgeConsoleAxis.v1")
        self.assertEqual(axes["source_inventory"]["status"], "ready")
        self.assertEqual(axes["source_inventory"]["action"]["action"], "open_source_registry")
        self.assertEqual(axes["mn_objects"]["status"], "ready")
        self.assertEqual(axes["mn_objects"]["action"]["action"], "object_browser")
        self.assertEqual(axes["mindmap_baseline"]["action"]["action"], "open_mindmap_studio")
        self.assertEqual(axes["card_coverage"]["action"]["action"], "open_card_factory")
        self.assertEqual(axes["workflow_runtime"]["action"]["action"], "open_workflow_builder")
        self.assertEqual(axes["operation_ledger"]["status"], "ready")
        self.assertEqual(axes["verification_evidence"]["status"], "ready")
        self.assertEqual(axes["verification_evidence"]["action"]["action"], "verification_report_list")
        self.assertIn("verification_evidence", matrix["recommendedAxisIds"])

    def test_missing_sources_and_no_native_scan_stay_action_required_or_blocked(self) -> None:
        repair_action = knowledge_console.workspace_action(
            "cache_current_pdf",
            "缓存当前 PDF",
            "request_pdf_cache",
            {"topicid": "T1"},
            "source_registry",
            "缓存当前 PDF。",
        )
        matrix = knowledge_console.build_matrix(
            {
                "topicid": "T1",
                "documentTitle": "Paper.pdf",
                "objects": {"nativeScan": 0, "registry": 0},
                "readiness": {"mnApiAvailable": False},
                "sourceRegistry": {"summary": {"readable": 0, "total": 1}, "actionPlan": {"recommendedAction": repair_action}},
            },
            [],
        )

        axes = {axis["id"]: axis for axis in matrix["axes"]}
        self.assertEqual(matrix["status"], "blocked")
        self.assertEqual(axes["source_inventory"]["status"], "action_required")
        self.assertEqual(axes["source_inventory"]["action"]["action"], "request_pdf_cache")
        self.assertEqual(axes["mn_objects"]["status"], "blocked")
        self.assertEqual(axes["mindmap_baseline"]["status"], "blocked")
        self.assertEqual(axes["verification_evidence"]["status"], "waiting_evidence")

    def test_placeholder_object_without_notebook_scope_blocks_native_actions(self) -> None:
        matrix = knowledge_console.build_matrix(
            {
                "focusObject": {"objectId": "mnobj:unknown:placeholder", "kind": "unknown", "title": "未识别当前对象", "sourceRef": {}},
                "readiness": {"mnApiAvailable": True},
                "sourceRegistry": {"summary": {"readable": 1, "total": 1}},
            },
            [
                knowledge_console.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {"topicid": ""}, "object_browser", "扫描。"),
                knowledge_console.workspace_action("read_mindmap_tree", "读取脑图", "mn_read_tree", {"topicid": ""}, "mindmap_studio", "读取。"),
            ],
        )

        axes = {axis["id"]: axis for axis in matrix["axes"]}
        self.assertEqual(axes["mn_objects"]["status"], "blocked")
        self.assertEqual(axes["mn_objects"]["action"], {})
        self.assertEqual(axes["mindmap_baseline"]["status"], "blocked")
        self.assertEqual(axes["mindmap_baseline"]["action"], {})


if __name__ == "__main__":
    unittest.main()
