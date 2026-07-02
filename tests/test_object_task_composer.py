from __future__ import annotations

import unittest

import object_task_composer


class ObjectTaskComposerTests(unittest.TestCase):
    def test_builds_route_backed_task_drafts_and_workflow_candidates(self) -> None:
        summary = {
            "topicid": "T1",
            "bookmd5": "B1",
            "documentTitle": "Paper.pdf",
        }
        primary_actions = [
            object_task_composer.workspace_action(
                "open_card_factory",
                "打开 Card Factory",
                "open_card_factory",
                {"topicid": "T1", "bookmd5": "B1"},
                "card_factory",
                "查看卡片覆盖。",
            ),
            object_task_composer.workspace_action(
                "open_skill_center",
                "打开 Skill Center",
                "open_skill_center",
                {"topicid": "T1", "bookmd5": "B1"},
                "skill_center",
                "查看技能包。",
            ),
        ]
        intake = {
            "schema": "codex.mn.objectIntake.v1",
            "objectRef": {"objectId": "mnobj:selection:x", "kind": "selection", "title": "Attention mask"},
            "objectLabel": "Attention mask",
            "routes": [
                {
                    "id": "route_source_registry",
                    "status": "action_required",
                    "evidence": "readable=0 / total=1",
                    "action": object_task_composer.workspace_action(
                        "cache_current_pdf",
                        "缓存当前 PDF",
                        "request_pdf_cache",
                        {"topicid": "T1", "bookmd5": "B1"},
                        "source_registry",
                        "缓存当前 PDF。",
                    ),
                },
                {
                    "id": "route_mindmap_studio",
                    "status": "ready",
                    "evidence": "nodes=8",
                    "action": object_task_composer.workspace_action(
                        "open_mindmap_studio",
                        "打开 Mindmap Studio",
                        "open_mindmap_studio",
                        {"topicid": "T1", "bookmd5": "B1"},
                        "mindmap_studio",
                        "打开脑图工作台。",
                    ),
                },
                {
                    "id": "route_card_factory",
                    "status": "action_required",
                    "evidence": "cards=0 / due=0",
                    "action": primary_actions[0],
                },
                {
                    "id": "route_workflow_builder",
                    "status": "pending",
                    "evidence": "runs=0 / templates=3",
                    "action": object_task_composer.workspace_action(
                        "open_workflows",
                        "查看工作流",
                        "workflow_list",
                        {"topicid": "T1", "bookmd5": "B1"},
                        "workflow_builder",
                        "查看 workflow。",
                    ),
                },
                {
                    "id": "route_skill_center",
                    "status": "pending",
                    "evidence": "Skill Runtime",
                    "action": primary_actions[1],
                },
                {
                    "id": "route_verification_center",
                    "status": "pending",
                    "evidence": "ledger=0",
                    "action": object_task_composer.workspace_action(
                        "open_verification_center",
                        "打开验证中心",
                        "verification_report_list",
                        {"topicid": "T1", "bookmd5": "B1"},
                        "verification_center",
                        "打开验证中心。",
                    ),
                },
            ],
        }

        composer = object_task_composer.build_composer(summary, primary_actions, intake)

        self.assertEqual(composer["schema"], "codex.mn.objectTaskComposer.v1")
        self.assertEqual(composer["mode"], "draft_first")
        self.assertFalse(composer["requiresPrompt"])
        self.assertEqual(composer["writePolicy"], "no_write_task_draft")
        self.assertEqual(composer["taskCount"], 7)
        self.assertEqual(composer["objectRef"]["objectId"], "mnobj:selection:x")
        tasks = {task["id"]: task for task in composer["tasks"]}
        self.assertEqual(
            list(tasks),
            [
                "task_source_preflight",
                "task_object_inventory",
                "task_mindmap_operation_plan",
                "task_card_operation_plan",
                "task_workflow_operation_plan",
                "task_skill_selection",
                "task_verification_review",
            ],
        )
        self.assertEqual(tasks["task_source_preflight"]["schema"], "codex.mn.objectTaskDraft.v1")
        self.assertEqual(tasks["task_source_preflight"]["routeAction"]["action"], "request_pdf_cache")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["compileAction"]["action"], "agent_plan")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["compileAction"]["payload"]["source"], "object-task-composer")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["workflowCandidate"]["schema"], "codex.mn.objectTaskWorkflowCandidate.v1")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["workflowCandidate"]["workflowId"], "mindmap_reorganize")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["startAction"]["action"], "workflow_start")
        self.assertEqual(tasks["task_mindmap_operation_plan"]["startAction"]["payload"]["taskId"], "task_mindmap_operation_plan")
        self.assertEqual(tasks["task_card_operation_plan"]["workflowCandidate"]["workflowId"], "selection_to_cards")
        self.assertEqual(tasks["task_workflow_operation_plan"]["workflowCandidate"]["workflowId"], "paper_deep_reading")
        self.assertEqual(tasks["task_workflow_operation_plan"]["writePolicy"], "confirmation_required_workflow")
        self.assertEqual(tasks["task_skill_selection"]["routeAction"]["action"], "open_skill_center")
        self.assertEqual(tasks["task_verification_review"]["routeAction"]["action"], "verification_report_list")
        self.assertIn("task_source_preflight", composer["recommendedTaskIds"])

    def test_without_context_returns_blocked_no_write_task_drafts(self) -> None:
        composer = object_task_composer.build_composer({}, [], {"routes": []})

        self.assertEqual(composer["schema"], "codex.mn.objectTaskComposer.v1")
        self.assertEqual(composer["status"], "blocked")
        self.assertEqual(composer["writePolicy"], "no_write_task_draft")
        self.assertEqual(composer["taskCount"], 7)
        self.assertTrue(all(task["writePolicy"] in {"no_write_task_draft", "confirmation_required_workflow"} for task in composer["tasks"]))
        self.assertTrue(all(task["status"] == "blocked" for task in composer["tasks"][:2]))


if __name__ == "__main__":
    unittest.main()
