import unittest

import agent_workbench


class AgentWorkbenchTests(unittest.TestCase):
    def test_builds_unified_mn_object_for_selection_with_source_and_actions(self) -> None:
        mn_object = agent_workbench.build_mn_object(
            {
                "selectionText": "quoted evidence about safety filters",
                "topicid": "T1",
                "bookmd5": "B1",
                "documentTitle": "Paper A",
                "pageNumber": 7,
                "pdfPath": "/tmp/Paper A.pdf",
            }
        )

        self.assertEqual(mn_object["schema"], "codex.mn.mnObject.v1")
        self.assertEqual(mn_object["kind"], "selection")
        self.assertTrue(mn_object["objectId"].startswith("mnobj:selection:"))
        self.assertEqual(mn_object["identifiers"]["topicid"], "T1")
        self.assertEqual(mn_object["identifiers"]["bookmd5"], "B1")
        self.assertEqual(mn_object["sourceRef"]["page"], 7)
        self.assertEqual(mn_object["sourceRef"]["quote"], "quoted evidence about safety filters")
        self.assertEqual(mn_object["sourceRef"]["documentTitle"], "Paper A")
        self.assertIn(
            {"type": "belongs_to", "targetKind": "document", "targetId": "B1"},
            mn_object["relations"],
        )
        action_ids = [item["id"] for item in mn_object["availableActions"]]
        self.assertIn("explain_object", action_ids)
        self.assertIn("create_cards", action_ids)
        self.assertIn("highlight_selection", action_ids)
        self.assertTrue(mn_object["permissionBoundary"]["requiresConfirmationForWrites"])

    def test_agent_operation_embeds_unified_mn_object_reference(self) -> None:
        operation = agent_workbench.build_agent_operation(
            {
                "prompt": "重组这个节点",
                "selectedNoteId": "N1",
                "selectedNoteTitle": "Existing Node",
                "selectedNoteText": "node body",
                "topicid": "T1",
                "bookmd5": "B1",
            },
            workflow={
                "id": "mindmap_reorganize",
                "title": "当前脑图重组工作流",
                "steps": [{"id": "write", "action": "write_draft", "writes": True}],
                "confirmationPoints": ["write"],
            },
        )

        self.assertEqual(operation["mnObject"]["schema"], "codex.mn.mnObject.v1")
        self.assertEqual(operation["mnObject"]["kind"], "note")
        self.assertEqual(operation["mnObject"]["identifiers"]["noteId"], "N1")
        self.assertEqual(operation["object"]["mnObjectId"], operation["mnObject"]["objectId"])
        self.assertEqual(operation["object"]["sourceRef"], operation["mnObject"]["sourceRef"])
        self.assertEqual(operation["object"]["availableActionCount"], len(operation["mnObject"]["availableActions"]))

    def test_detects_selection_note_document_and_mindmap_focus(self) -> None:
        self.assertEqual(
            agent_workbench.detect_object_focus({"selectionText": "selected formula"})["kind"],
            "selection",
        )
        self.assertEqual(
            agent_workbench.detect_object_focus({"selectedNoteId": "n1", "selectedNoteTitle": "Method"})["kind"],
            "note",
        )
        self.assertEqual(
            agent_workbench.detect_object_focus({"documentTitle": "Paper A", "bookmd5": "B1"})["kind"],
            "document",
        )
        self.assertEqual(
            agent_workbench.detect_object_focus(
                {
                    "prompt": "重组当前脑图",
                    "mindmapTarget": {"label": "文档脑图：Paper A"},
                }
            )["kind"],
            "mindmap",
        )

    def test_builds_object_first_agent_operation_with_confirmation_gate(self) -> None:
        operation = agent_workbench.build_agent_operation(
            {
                "prompt": "把这个选区做成短卡，并关联之前的内容",
                "selectionText": "important passage",
                "topicid": "T1",
                "bookmd5": "B1",
            },
            workflow={
                "id": "selection_to_cards",
                "title": "选区制卡工作流",
                "status": "ready",
                "stepCount": 4,
                "confirmationPoints": ["write"],
                "steps": [
                    {"id": "explain", "action": "chat", "writes": False},
                    {"id": "cards", "action": "generate_card", "writes": False},
                    {"id": "write", "action": "write_draft", "writes": True},
                ],
            },
            knowledge={"count": 3, "message": "知识索引：3 条。"},
            settings={"permission": "notes"},
        )

        self.assertEqual(operation["schema"], "codex.mn.agentOperation.v1")
        self.assertEqual(operation["object"]["kind"], "selection")
        self.assertEqual(operation["contextPolicy"]["visibleScope"], "selection")
        self.assertTrue(operation["knowledge"]["enabled"])
        self.assertEqual(operation["operationPolicy"]["risk"]["status"], "write_pending_confirmation")
        self.assertTrue(operation["operationPolicy"]["mustDryRunBeforeWrite"])
        operation_plan = operation["operationPlan"]
        self.assertEqual(operation_plan["schema"], "codex.mn.operationPlan.v1")
        self.assertEqual(operation_plan["planType"], "workflow")
        self.assertEqual(operation_plan["workflowId"], "selection_to_cards")
        self.assertEqual(operation_plan["operationCount"], 3)
        self.assertEqual(operation_plan["writeCount"], 1)
        self.assertEqual(operation_plan["status"], "waiting_dry_run")
        self.assertIn("nativeCards", operation_plan["requiredCapabilities"])
        self.assertIn("rollbackLedger", operation_plan["requiredCapabilities"])
        write_ops = [item for item in operation_plan["operations"] if item["writes"]]
        self.assertEqual(len(write_ops), 1)
        self.assertEqual(write_ops[0]["action"], "write_draft")
        self.assertEqual(write_ops[0]["mutation"], "create")
        self.assertTrue(write_ops[0]["confirmationRequired"])
        self.assertEqual(write_ops[0]["rollback"]["strategy"], "ai_edit_transaction")
        verification_plan = operation["verificationPlan"]
        self.assertEqual(verification_plan["schema"], "codex.mn.verificationPlan.v1")
        self.assertEqual(verification_plan["status"], "required")
        self.assertTrue(verification_plan["mustVerifyCreatedObjects"])
        self.assertTrue(verification_plan["mustVerifyRollback"])
        self.assertTrue(verification_plan["mustReportResidualObjects"])
        self.assertIn("createCardsFinished", verification_plan["expectedEvents"])
        compiler = operation["operationCompiler"]
        self.assertEqual(compiler["schema"], "codex.mn.operationCompiler.v1")
        self.assertEqual(compiler["status"], "needs_dry_run")
        risk_register = operation["operationPolicy"]["riskRegister"]
        self.assertEqual(risk_register["schema"], "codex.mn.riskRegister.v1")
        self.assertEqual(risk_register["summary"]["status"], "write_pending_confirmation")
        risk_items = {item["id"]: item for item in risk_register["items"]}
        self.assertEqual(risk_items["permission"]["status"], "write_allowed")
        self.assertEqual(risk_items["context_scope"]["status"], "selection")
        self.assertEqual(risk_items["dry_run"]["status"], "not_available")
        self.assertEqual(risk_items["confirmation"]["status"], "required")
        self.assertIn("write", risk_items["confirmation"]["detail"])
        next_action_ids = [item["id"] for item in operation["nextActions"]]
        self.assertIn("create_card_tree", next_action_ids)
        self.assertIn("review_operation_plan", next_action_ids)
        self.assertIn("search_related_context", next_action_ids)

    def test_mindmap_workflow_offers_diff_preview_next_action(self) -> None:
        operation = agent_workbench.build_agent_operation(
            {
                "prompt": "重组当前脑图结构",
                "mindmapTarget": {"label": "文档脑图：Paper A"},
                "topicid": "T1",
                "bookmd5": "B1",
            },
            workflow={
                "id": "mindmap_reorganize",
                "title": "当前脑图重组工作流",
                "status": "ready",
                "stepCount": 4,
                "confirmationPoints": ["write"],
                "steps": [
                    {"id": "read_tree", "action": "mn_read_tree", "writes": False},
                    {"id": "reorganize", "action": "reorganize_mindmap", "writes": False},
                    {"id": "write", "action": "write_draft", "writes": True},
                ],
            },
            settings={"permission": "notes"},
        )

        next_actions = {item["id"]: item for item in operation["nextActions"]}
        self.assertEqual(operation["object"]["kind"], "mindmap")
        self.assertIn("readMindmapTree", operation["operationPlan"]["requiredCapabilities"])
        self.assertIn("nativeMindmap", operation["operationPlan"]["requiredCapabilities"])
        self.assertIn("rollbackLedger", operation["operationPlan"]["requiredCapabilities"])
        self.assertIn("mindmapDiffApplyFinished", operation["verificationPlan"]["expectedEvents"])
        self.assertIn("preview_mindmap_diff", next_actions)
        self.assertEqual(next_actions["preview_mindmap_diff"]["action"], "mindmap_diff_preview")
        self.assertTrue(next_actions["preview_mindmap_diff"]["requiresDraft"])

    def test_read_only_permission_blocks_write_operation_plan(self) -> None:
        operation = agent_workbench.build_agent_operation(
            {
                "prompt": "把当前选区做成卡片",
                "selectionText": "selected text",
                "topicid": "T1",
                "bookmd5": "B1",
            },
            workflow={
                "id": "selection_to_cards",
                "title": "选区制卡工作流",
                "status": "ready",
                "steps": [
                    {"id": "cards", "action": "generate_card", "writes": False},
                    {"id": "write", "action": "write_draft", "writes": True},
                ],
                "confirmationPoints": ["write"],
            },
            settings={"permission": "read_only"},
        )

        self.assertEqual(operation["operationPlan"]["status"], "blocked")
        compiler_checks = {item["id"]: item for item in operation["operationCompiler"]["checks"]}
        self.assertEqual(compiler_checks["permission"]["tone"], "block")
        risk_items = {item["id"]: item for item in operation["operationPolicy"]["riskRegister"]["items"]}
        self.assertEqual(risk_items["permission"]["status"], "read_only_blocked")


if __name__ == "__main__":
    unittest.main()
