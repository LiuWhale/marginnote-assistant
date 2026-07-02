from __future__ import annotations

import unittest

import notebook_runbook


class NotebookRunbookTests(unittest.TestCase):
    def test_builds_eight_step_workspace_runbook_with_continue_action_and_safe_auto_plan(self) -> None:
        source_repair = notebook_runbook.workspace_action(
            "cache_current_pdf",
            "缓存当前 PDF",
            "request_pdf_cache",
            {"topicid": "T1", "bookmd5": "B1"},
            "source_registry",
            "缓存当前文档。",
        )
        actions = [
            notebook_runbook.workspace_action("open_source_registry", "打开 Source Registry", "open_source_registry", {}, "source_registry", "打开来源。"),
            notebook_runbook.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {}, "object_browser", "扫描真实对象。"),
            notebook_runbook.workspace_action("open_object_browser", "打开对象浏览器", "object_browser", {}, "object_browser", "打开对象浏览器。"),
            notebook_runbook.workspace_action("read_mindmap_tree", "读取当前脑图", "mn_read_tree", {}, "mindmap_studio", "读取脑图基线。"),
            notebook_runbook.workspace_action("open_mindmap_studio", "打开 Mindmap Studio", "open_mindmap_studio", {}, "mindmap_studio", "打开脑图工作台。"),
            notebook_runbook.workspace_action("open_card_factory", "打开 Card Factory", "open_card_factory", {}, "card_factory", "查看卡片覆盖。"),
            notebook_runbook.workspace_action("plan_next_operation", "生成操作计划", "agent_plan", {}, "operation_compiler", "编译操作计划。"),
            notebook_runbook.workspace_action("open_workflows", "查看工作流", "workflow_list", {}, "workflow_builder", "查看 workflow。"),
            notebook_runbook.workspace_action("open_workflow_builder", "打开 Workflow Builder", "open_workflow_builder", {}, "workflow_builder", "打开工作流。"),
            notebook_runbook.workspace_action("open_operation_ledger", "打开账本", "operation_ledger_list", {}, "ledger_explorer", "打开账本。"),
        ]
        latest_run = {
            "schema": "codex.mn.notebookRunbookPreflightRun.v1",
            "runId": "runbook-preflight-1",
            "status": "completed",
            "writePolicy": "no_write_preflight",
        }
        summary = {
            "topicid": "T1",
            "bookmd5": "B1",
            "documentTitle": "Paper.pdf",
            "focusObject": {"objectId": "mnobj:selection:x", "kind": "selection", "title": "Patch mask"},
            "objects": {"total": 5, "registry": 5, "nativeScan": 0},
            "mindmap": {"status": "missing", "nodeCount": 0},
            "reviewQueue": {"total": 2, "due": 1, "new": 1},
            "workflows": {"runCount": 1, "latestStatus": "waiting_confirmation", "templateCount": 3},
            "ledger": {"total": 4, "filteredTotal": 3},
            "readiness": {"mnApiAvailable": True, "mnApiBackend": "url-api", "permission": "ask_each_time"},
            "sourceRegistry": {
                "summary": {"readable": 0, "total": 1, "pendingNativeCache": 1},
                "actionPlan": {"recommendedAction": source_repair},
            },
        }

        runbook = notebook_runbook.build_runbook(summary, actions, latest_run=latest_run)

        self.assertEqual(runbook["schema"], "codex.mn.notebookRunbook.v1")
        self.assertEqual(runbook["status"], "action_required")
        self.assertEqual(runbook["summary"], {"total": 8, "ready": 4, "blocked": 0, "actionRequired": 4, "pending": 0})
        steps = {step["id"]: step for step in runbook["steps"]}
        self.assertEqual(
            list(steps),
            [
                "context_scope",
                "source_inventory",
                "scan_objects",
                "mindmap_baseline",
                "card_coverage",
                "operation_plan",
                "workflow_runtime",
                "operation_evidence",
            ],
        )
        self.assertEqual(steps["context_scope"]["schema"], "codex.mn.notebookRunbookStep.v1")
        self.assertEqual(steps["source_inventory"]["status"], "action_required")
        self.assertEqual(steps["source_inventory"]["action"]["action"], "request_pdf_cache")
        self.assertIn("readable=0", steps["source_inventory"]["evidence"])
        self.assertEqual(steps["scan_objects"]["status"], "action_required")
        self.assertEqual(steps["scan_objects"]["action"]["action"], "request_mn_object_registry_scan")
        self.assertEqual(steps["mindmap_baseline"]["status"], "action_required")
        self.assertEqual(steps["mindmap_baseline"]["action"]["action"], "mn_read_tree")
        self.assertEqual(steps["card_coverage"]["status"], "ready")
        self.assertEqual(steps["card_coverage"]["action"]["action"], "open_card_factory")
        self.assertEqual(steps["operation_plan"]["action"]["action"], "agent_plan")
        self.assertEqual(steps["workflow_runtime"]["action"]["action"], "open_workflow_builder")
        self.assertEqual(steps["operation_evidence"]["action"]["action"], "operation_ledger_list")

        self.assertEqual(runbook["nextStep"]["id"], "source_inventory")
        self.assertEqual(runbook["continueAction"]["schema"], "codex.mn.notebookRunbookContinue.v1")
        self.assertEqual(runbook["continueAction"]["stepId"], "source_inventory")
        self.assertEqual(runbook["continueAction"]["action"], "request_pdf_cache")
        self.assertEqual(runbook["continueAction"]["surface"], "source_registry")

        auto_plan = runbook["autoPlan"]
        self.assertEqual(auto_plan["schema"], "codex.mn.notebookRunbookAutoPlan.v1")
        self.assertEqual(auto_plan["mode"], "safe_preflight")
        self.assertTrue(auto_plan["canRun"])
        self.assertEqual(auto_plan["latestRun"], latest_run)
        self.assertEqual(
            [item["stepId"] for item in auto_plan["actions"]],
            ["source_inventory", "scan_objects", "mindmap_baseline", "operation_plan"],
        )
        self.assertNotIn("card_coverage", [item["stepId"] for item in auto_plan["actions"]])

    def test_empty_context_blocks_runbook_and_returns_idle_latest_run(self) -> None:
        runbook = notebook_runbook.build_runbook({}, [])

        self.assertEqual(runbook["status"], "blocked")
        self.assertEqual(runbook["summary"]["blocked"], 6)
        self.assertEqual(runbook["continueAction"], {})
        self.assertFalse(runbook["autoPlan"]["canRun"])
        self.assertEqual(runbook["autoPlan"]["latestRun"]["status"], "idle")

    def test_placeholder_object_without_notebook_scope_does_not_trigger_native_scan_or_tree_read(self) -> None:
        actions = [
            notebook_runbook.workspace_action("scan_mn_objects", "扫描 MN", "request_mn_object_registry_scan", {"topicid": "", "bookmd5": ""}, "object_browser", "扫描。"),
            notebook_runbook.workspace_action("read_mindmap_tree", "读取当前脑图", "mn_read_tree", {"topicid": "", "bookmd5": ""}, "mindmap_studio", "读取。"),
            notebook_runbook.workspace_action("plan_next_operation", "生成操作计划", "agent_plan", {"topicid": "", "bookmd5": ""}, "operation_compiler", "计划。"),
        ]
        runbook = notebook_runbook.build_runbook(
            {
                "focusObject": {"objectId": "mnobj:unknown:placeholder", "kind": "unknown", "title": "未识别当前对象", "sourceRef": {}},
                "readiness": {"mnApiAvailable": True},
                "sourceRegistry": {"summary": {"readable": 2, "total": 2}},
            },
            actions,
        )

        steps = {step["id"]: step for step in runbook["steps"]}
        self.assertEqual(steps["context_scope"]["status"], "blocked")
        self.assertEqual(steps["scan_objects"]["status"], "blocked")
        self.assertEqual(steps["scan_objects"]["action"], {})
        self.assertEqual(steps["mindmap_baseline"]["status"], "blocked")
        self.assertEqual(steps["mindmap_baseline"]["action"], {})
        self.assertEqual(steps["operation_plan"]["status"], "blocked")
        self.assertEqual(runbook["continueAction"], {})
        self.assertFalse(runbook["autoPlan"]["canRun"])
        self.assertEqual(runbook["autoPlan"]["actions"], [])


if __name__ == "__main__":
    unittest.main()
