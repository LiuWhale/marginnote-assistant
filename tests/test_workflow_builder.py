from __future__ import annotations

import unittest

import workflow_builder


class WorkflowBuilderTests(unittest.TestCase):
    def test_board_groups_candidates_active_confirmation_and_evidence(self) -> None:
        composer = {
            "schema": "codex.mn.objectTaskComposer.v1",
            "tasks": [
                {
                    "id": "task_card_operation_plan",
                    "title": "卡片学习草案",
                    "objective": "把当前选区拆成可复习短卡。",
                    "routeId": "route_card_factory",
                    "writePolicy": "confirmation_required_workflow",
                    "workflowCandidate": {
                        "schema": "codex.mn.objectTaskWorkflowCandidate.v1",
                        "workflowId": "selection_to_cards",
                        "status": "ready",
                        "stepCount": 3,
                        "confirmationPoints": ["write"],
                    },
                    "startAction": {
                        "schema": "codex.mn.notebookWorkspaceAction.v1",
                        "id": "start_card_workflow",
                        "label": "启动 workflow",
                        "action": "workflow_start",
                        "payload": {"workflowId": "selection_to_cards"},
                    },
                },
                {
                    "id": "task_source_preflight",
                    "title": "材料读取预检",
                    "workflowCandidate": {"schema": "not-a-workflow-candidate"},
                },
            ],
        }
        workflow_payload = {
            "workflowRuns": [
                {
                    "id": "run-wait",
                    "title": "等待确认的 run",
                    "workflowId": "selection_to_cards",
                    "status": "waiting_confirmation",
                    "waitingConfirmationCount": 1,
                    "queuedCount": 0,
                    "updatedAt": "2026-06-28T10:00:00+0800",
                },
                {
                    "id": "run-active",
                    "title": "运行中的 run",
                    "workflowId": "paper_deep_reading",
                    "status": "running",
                    "waitingConfirmationCount": 0,
                    "queuedCount": 2,
                },
                {
                    "id": "run-done",
                    "title": "已完成 run",
                    "workflowId": "mindmap_reorganize",
                    "status": "completed",
                    "waitingConfirmationCount": 0,
                    "queuedCount": 0,
                    "createdAt": "2026-06-28T09:00:00+0800",
                },
            ]
        }

        board = workflow_builder.build_board(workflow_payload, composer)

        self.assertEqual(board["schema"], "codex.mn.workflowBuilderBoard.v1")
        self.assertEqual(board["laneCount"], 4)
        self.assertEqual(board["draftCandidateCount"], 1)
        self.assertEqual(board["activeRunCount"], 1)
        self.assertEqual(board["waitingConfirmationCount"], 1)
        self.assertEqual(board["evidenceCount"], 1)
        lanes = {lane["id"]: lane for lane in board["lanes"]}
        self.assertEqual(list(lanes), ["draft_candidates", "active_runs", "waiting_confirmation", "evidence"])

        candidate = lanes["draft_candidates"]["cards"][0]
        self.assertEqual(candidate["schema"], "codex.mn.workflowBuilderCard.v1")
        self.assertEqual(candidate["type"], "task_candidate")
        self.assertEqual(candidate["id"], "task_card_operation_plan")
        self.assertEqual(candidate["startAction"]["action"], "workflow_start")
        self.assertEqual(candidate["meta"]["workflowId"], "selection_to_cards")

        waiting = lanes["waiting_confirmation"]["cards"][0]
        self.assertEqual(waiting["id"], "run-wait")
        self.assertEqual(waiting["type"], "workflow_run")
        self.assertEqual(waiting["action"]["schema"], "codex.mn.notebookWorkspaceAction.v1")
        self.assertEqual(waiting["action"]["action"], "workflow_status")
        self.assertEqual(waiting["action"]["payload"]["workflowRunId"], "run-wait")

        active = lanes["active_runs"]["cards"][0]
        self.assertEqual(active["id"], "run-active")
        self.assertIn("queued 2", active["detail"])

        evidence = lanes["evidence"]["cards"][0]
        self.assertEqual(evidence["id"], "run-done")
        self.assertEqual(evidence["status"], "completed")

    def test_empty_board_keeps_four_lanes_for_stable_ui(self) -> None:
        board = workflow_builder.build_board({})

        self.assertEqual(board["schema"], "codex.mn.workflowBuilderBoard.v1")
        self.assertEqual(board["status"], "empty")
        self.assertEqual(board["cardCount"], 0)
        self.assertEqual([lane["id"] for lane in board["lanes"]], ["draft_candidates", "active_runs", "waiting_confirmation", "evidence"])
        self.assertTrue(all(lane["status"] == "empty" for lane in board["lanes"]))


if __name__ == "__main__":
    unittest.main()
