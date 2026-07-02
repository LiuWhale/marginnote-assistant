from __future__ import annotations

import unittest

import object_intake


class ObjectIntakeTests(unittest.TestCase):
    def test_routes_current_object_to_source_object_mindmap_card_workflow_skill_and_verification(self) -> None:
        source_repair = object_intake.workspace_action(
            "cache_current_pdf",
            "缓存当前 PDF",
            "request_pdf_cache",
            {"topicid": "T1", "bookmd5": "B1"},
            "source_registry",
            "缓存当前文档。",
        )
        actions = [
            object_intake.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {}, "object_browser", "扫描真实对象。"),
            object_intake.workspace_action("open_object_browser", "打开对象浏览器", "object_browser", {}, "object_browser", "打开对象浏览器。"),
            object_intake.workspace_action("read_mindmap_tree", "读取当前脑图", "mn_read_tree", {}, "mindmap_studio", "读取脑图基线。"),
            object_intake.workspace_action("open_mindmap_studio", "打开 Mindmap Studio", "open_mindmap_studio", {}, "mindmap_studio", "打开脑图工作台。"),
            object_intake.workspace_action("open_card_factory", "打开 Card Factory", "open_card_factory", {}, "card_factory", "查看卡片覆盖。"),
            object_intake.workspace_action("open_workflows", "查看工作流", "workflow_list", {}, "workflow_builder", "查看 workflow。"),
            object_intake.workspace_action("open_workflow_builder", "打开 Workflow Builder", "open_workflow_builder", {}, "workflow_builder", "打开工作流工作台。"),
            object_intake.workspace_action("open_skill_center", "打开 Skill Center", "open_skill_center", {}, "skill_center", "打开技能中心。"),
            object_intake.workspace_action("open_verification_center", "打开验证中心", "verification_report_list", {}, "verification_center", "打开验证中心。"),
        ]
        summary = {
            "topicid": "T1",
            "bookmd5": "B1",
            "documentTitle": "Paper.pdf",
            "focusObject": {"objectId": "mnobj:selection:x", "kind": "selection", "title": "Attention mask"},
            "objects": {"nativeScan": 2, "registry": 5},
            "mindmap": {"status": "available", "nodeCount": 8},
            "reviewQueue": {"total": 3, "due": 1},
            "workflows": {"runCount": 1, "templateCount": 3},
            "ledger": {"total": 4},
            "readiness": {"mnApiAvailable": True},
            "sourceRegistry": {
                "summary": {"readable": 0, "total": 1},
                "actionPlan": {"recommendedAction": source_repair},
            },
        }

        intake = object_intake.build_intake(summary, actions)

        self.assertEqual(intake["schema"], "codex.mn.objectIntake.v1")
        self.assertEqual(intake["mode"], "object_first")
        self.assertFalse(intake["requiresPrompt"])
        self.assertEqual(intake["objectRef"]["objectId"], "mnobj:selection:x")
        self.assertEqual(intake["objectKind"], "selection")
        self.assertEqual(intake["routeCount"], 7)
        routes = {route["id"]: route for route in intake["routes"]}
        self.assertEqual(
            list(routes),
            [
                "route_source_registry",
                "route_object_browser",
                "route_mindmap_studio",
                "route_card_factory",
                "route_workflow_builder",
                "route_skill_center",
                "route_verification_center",
            ],
        )
        self.assertEqual(routes["route_source_registry"]["schema"], "codex.mn.objectIntakeRoute.v1")
        self.assertEqual(routes["route_source_registry"]["status"], "action_required")
        self.assertEqual(routes["route_source_registry"]["action"]["action"], "request_pdf_cache")
        self.assertEqual(routes["route_object_browser"]["status"], "ready")
        self.assertEqual(routes["route_object_browser"]["action"]["action"], "object_browser")
        self.assertEqual(routes["route_mindmap_studio"]["status"], "ready")
        self.assertEqual(routes["route_mindmap_studio"]["action"]["action"], "open_mindmap_studio")
        self.assertEqual(routes["route_card_factory"]["status"], "ready")
        self.assertEqual(routes["route_card_factory"]["action"]["action"], "open_card_factory")
        self.assertEqual(routes["route_workflow_builder"]["status"], "ready")
        self.assertEqual(routes["route_workflow_builder"]["action"]["action"], "open_workflow_builder")
        self.assertEqual(routes["route_skill_center"]["action"]["action"], "open_skill_center")
        self.assertEqual(routes["route_verification_center"]["status"], "ready")
        self.assertEqual(routes["route_verification_center"]["action"]["action"], "verification_report_list")
        self.assertIn("route_source_registry", intake["recommendedRouteIds"])

    def test_document_fallback_and_blocked_empty_context_are_explicit(self) -> None:
        document_intake = object_intake.build_intake(
            {"topicid": "T1", "bookmd5": "B1", "documentTitle": "Paper.pdf", "readiness": {"mnApiAvailable": False}},
            [],
        )

        self.assertEqual(document_intake["objectRef"]["objectId"], "document:B1")
        self.assertEqual(document_intake["objectKind"], "document")
        self.assertEqual(document_intake["routes"][0]["status"], "action_required")
        self.assertEqual(document_intake["routes"][1]["status"], "blocked")

        empty_intake = object_intake.build_intake({}, [])

        self.assertEqual(empty_intake["status"], "blocked")
        self.assertEqual(empty_intake["objectRef"], {})
        self.assertEqual(empty_intake["blockedCount"], 7)
        self.assertTrue(all(route["status"] == "blocked" for route in empty_intake["routes"]))

    def test_placeholder_object_without_notebook_scope_blocks_native_routes(self) -> None:
        intake = object_intake.build_intake(
            {
                "focusObject": {"objectId": "mnobj:unknown:placeholder", "kind": "unknown", "title": "未识别当前对象", "sourceRef": {}},
                "readiness": {"mnApiAvailable": True},
                "sourceRegistry": {"summary": {"readable": 1, "total": 1}},
            },
            [
                object_intake.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {"topicid": ""}, "object_browser", "扫描。"),
                object_intake.workspace_action("read_mindmap_tree", "读取脑图", "mn_read_tree", {"topicid": ""}, "mindmap_studio", "读取。"),
            ],
        )

        routes = {route["id"]: route for route in intake["routes"]}
        self.assertEqual(intake["status"], "blocked")
        self.assertEqual(routes["route_object_browser"]["status"], "blocked")
        self.assertEqual(routes["route_object_browser"]["action"], {})
        self.assertEqual(routes["route_mindmap_studio"]["status"], "blocked")
        self.assertEqual(routes["route_mindmap_studio"]["action"], {})


if __name__ == "__main__":
    unittest.main()
