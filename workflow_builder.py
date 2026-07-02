from __future__ import annotations

from typing import Any


WORKFLOW_BUILDER_BOARD_SCHEMA = "codex.mn.workflowBuilderBoard.v1"
WORKFLOW_BUILDER_LANE_SCHEMA = "codex.mn.workflowBuilderLane.v1"
WORKFLOW_BUILDER_CARD_SCHEMA = "codex.mn.workflowBuilderCard.v1"
NOTEBOOK_WORKSPACE_ACTION_SCHEMA = "codex.mn.notebookWorkspaceAction.v1"
OBJECT_TASK_WORKFLOW_CANDIDATE_SCHEMA = "codex.mn.objectTaskWorkflowCandidate.v1"


def workspace_action(
    action_id: str,
    label: str,
    action: str,
    payload: dict[str, Any],
    surface: str,
    detail: str,
    style: str = "secondary",
) -> dict[str, Any]:
    return {
        "schema": NOTEBOOK_WORKSPACE_ACTION_SCHEMA,
        "id": action_id,
        "label": label,
        "action": action,
        "payload": payload,
        "surface": surface,
        "detail": detail,
        "style": style,
    }


def build_card(
    card_id: str,
    title: str,
    status: str,
    detail: str,
    *,
    card_type: str,
    evidence: str = "",
    action: dict[str, Any] | None = None,
    start_action: dict[str, Any] | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": WORKFLOW_BUILDER_CARD_SCHEMA,
        "id": card_id,
        "type": card_type,
        "title": title,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "meta": meta if isinstance(meta, dict) else {},
        "action": action if isinstance(action, dict) else {},
        "startAction": start_action if isinstance(start_action, dict) else {},
    }


def build_lane(
    lane_id: str,
    title: str,
    status: str,
    cards: list[dict[str, Any]],
    detail: str,
) -> dict[str, Any]:
    return {
        "schema": WORKFLOW_BUILDER_LANE_SCHEMA,
        "id": lane_id,
        "title": title,
        "status": status,
        "detail": detail,
        "cardCount": len(cards),
        "cards": cards,
    }


def _list_from(container: dict[str, Any], key: str) -> list[Any]:
    value = container.get(key) if isinstance(container, dict) else []
    return value if isinstance(value, list) else []


def task_candidate_cards(object_task_composer: dict[str, Any] | None) -> list[dict[str, Any]]:
    composer = object_task_composer if isinstance(object_task_composer, dict) else {}
    cards: list[dict[str, Any]] = []
    for task in _list_from(composer, "tasks"):
        if not isinstance(task, dict):
            continue
        candidate = task.get("workflowCandidate") if isinstance(task.get("workflowCandidate"), dict) else {}
        if candidate.get("schema") != OBJECT_TASK_WORKFLOW_CANDIDATE_SCHEMA:
            continue
        confirmation_points = candidate.get("confirmationPoints")
        cards.append(
            build_card(
                str(task.get("id") or candidate.get("workflowId") or ""),
                str(task.get("title") or candidate.get("title") or "workflow candidate"),
                str(candidate.get("status") or task.get("status") or "unknown"),
                str(task.get("objective") or ""),
                card_type="task_candidate",
                evidence=(
                    f"{candidate.get('stepCount', 0)} steps / "
                    f"confirm {len(confirmation_points if isinstance(confirmation_points, list) else [])}"
                ),
                start_action=task.get("startAction") if isinstance(task.get("startAction"), dict) else {},
                meta={
                    "taskId": str(task.get("id") or ""),
                    "workflowId": str(candidate.get("workflowId") or ""),
                    "routeId": str(task.get("routeId") or ""),
                    "writePolicy": str(task.get("writePolicy") or ""),
                },
            )
        )
    return cards


def run_cards(workflow_payload: dict[str, Any] | None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    payload = workflow_payload if isinstance(workflow_payload, dict) else {}
    active_cards: list[dict[str, Any]] = []
    confirmation_cards: list[dict[str, Any]] = []
    evidence_cards: list[dict[str, Any]] = []
    for run in _list_from(payload, "workflowRuns"):
        if not isinstance(run, dict):
            continue
        run_id = str(run.get("id") or "")
        action = workspace_action(
            f"open_workflow_run_{run_id}",
            "查看",
            "workflow_status",
            {"workflowRunId": run_id},
            "workflow_builder",
            "打开 Run Inspector 查看步骤、确认点、队列和恢复动作。",
            "secondary",
        )
        card = build_card(
            run_id,
            str(run.get("title") or run.get("workflowId") or "workflow run"),
            str(run.get("status") or "unknown"),
            (
                f"queued {int(run.get('queuedCount') or 0)} / "
                f"confirm {int(run.get('waitingConfirmationCount') or 0)} / "
                f"manual {int(run.get('manualCount') or 0)}"
            ),
            card_type="workflow_run",
            evidence=str(run.get("updatedAt") or run.get("createdAt") or ""),
            action=action,
            meta={
                "workflowId": str(run.get("workflowId") or ""),
                "mnObjectId": str(run.get("mnObjectId") or ""),
                "mnObjectKind": str(run.get("mnObjectKind") or ""),
            },
        )
        if int(run.get("waitingConfirmationCount") or 0) > 0:
            confirmation_cards.append(card)
        elif str(run.get("status") or "") in {"queued", "running", "pending", "partial"} or int(run.get("queuedCount") or 0) > 0:
            active_cards.append(card)
        else:
            evidence_cards.append(card)
    return active_cards, confirmation_cards, evidence_cards


def build_board(
    workflow_payload: dict[str, Any] | None,
    object_task_composer: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_cards = task_candidate_cards(object_task_composer)
    active_cards, confirmation_cards, evidence_cards = run_cards(workflow_payload)
    lanes = [
        build_lane(
            "draft_candidates",
            "任务候选",
            "ready" if candidate_cards else "empty",
            candidate_cards,
            "Object Task Composer 生成的 workflow 候选；启动后进入 Workflow Runtime。",
        ),
        build_lane(
            "active_runs",
            "运行中",
            "ready" if active_cards else "empty",
            active_cards,
            "已入队或正在运行的 workflow run。",
        ),
        build_lane(
            "waiting_confirmation",
            "待确认",
            "action_required" if confirmation_cards else "empty",
            confirmation_cards,
            "写入类步骤停在确认点，不能自动越过。",
        ),
        build_lane(
            "evidence",
            "证据",
            "ready" if evidence_cards else "empty",
            evidence_cards,
            "已完成、取消或需要审计的 workflow 证据入口。",
        ),
    ]
    total_cards = sum(int(lane.get("cardCount") or 0) for lane in lanes)
    return {
        "schema": WORKFLOW_BUILDER_BOARD_SCHEMA,
        "status": "ready" if total_cards else "empty",
        "laneCount": len(lanes),
        "cardCount": total_cards,
        "draftCandidateCount": len(candidate_cards),
        "activeRunCount": len(active_cards),
        "waitingConfirmationCount": len(confirmation_cards),
        "evidenceCount": len(evidence_cards),
        "lanes": lanes,
    }
