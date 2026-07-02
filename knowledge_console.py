from __future__ import annotations

from typing import Any

import object_intake


NOTEBOOK_WORKSPACE_ACTION_SCHEMA = "codex.mn.notebookWorkspaceAction.v1"
KNOWLEDGE_CONSOLE_MATRIX_SCHEMA = "codex.mn.knowledgeConsoleMatrix.v1"
KNOWLEDGE_CONSOLE_AXIS_SCHEMA = "codex.mn.knowledgeConsoleAxis.v1"


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


def axis(
    axis_id: str,
    title: str,
    status: str,
    detail: str,
    *,
    metric: str = "",
    action: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": KNOWLEDGE_CONSOLE_AXIS_SCHEMA,
        "id": axis_id,
        "title": title,
        "status": status,
        "metric": metric,
        "detail": detail,
        "action": action if isinstance(action, dict) else {},
    }


def _actions_by_id(primary_actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}


def build_matrix(summary: dict[str, Any], primary_actions: list[dict[str, Any]]) -> dict[str, Any]:
    actions_by_id = _actions_by_id(primary_actions)
    focus = summary.get("focusObject") if isinstance(summary.get("focusObject"), dict) else {}
    objects = summary.get("objects") if isinstance(summary.get("objects"), dict) else {}
    mindmap = summary.get("mindmap") if isinstance(summary.get("mindmap"), dict) else {}
    review = summary.get("reviewQueue") if isinstance(summary.get("reviewQueue"), dict) else {}
    workflows = summary.get("workflows") if isinstance(summary.get("workflows"), dict) else {}
    ledger = summary.get("ledger") if isinstance(summary.get("ledger"), dict) else {}
    readiness = summary.get("readiness") if isinstance(summary.get("readiness"), dict) else {}
    source_registry = summary.get("sourceRegistry") if isinstance(summary.get("sourceRegistry"), dict) else {}
    source_summary = source_registry.get("summary") if isinstance(source_registry.get("summary"), dict) else {}
    has_notebook_scope = bool(summary.get("topicid") or summary.get("bookmd5"))
    has_context = bool(has_notebook_scope or summary.get("documentTitle") or object_intake.object_ref_has_real_identity(focus))
    mn_api_available = bool(readiness.get("mnApiAvailable"))
    source_readable = int(source_summary.get("readable") or 0) > 0
    native_scan_count = int(objects.get("nativeScan") or 0)
    mindmap_ready = str(mindmap.get("status") or "") == "available"
    review_total = int(review.get("total") or 0)
    workflow_count = int(workflows.get("runCount") or 0)
    ledger_total = int(ledger.get("total") or 0)

    mn_objects_action = actions_by_id.get("open_object_browser") if native_scan_count > 0 else (actions_by_id.get("scan_mn_objects") if has_notebook_scope else {})
    mindmap_action = actions_by_id.get("open_mindmap_studio") if mindmap_ready else (actions_by_id.get("read_mindmap_tree") if has_notebook_scope else {})
    card_action = actions_by_id.get("open_card_factory")
    workflow_action = actions_by_id.get("open_workflow_builder") if workflow_count > 0 else actions_by_id.get("open_workflows")
    source_action_plan = source_registry.get("actionPlan") if isinstance(source_registry.get("actionPlan"), dict) else {}
    source_repair_action = source_action_plan.get("recommendedAction") if isinstance(source_action_plan.get("recommendedAction"), dict) else {}
    source_action = actions_by_id.get("open_source_registry") if source_readable else source_repair_action

    axes = [
        axis(
            "source_inventory",
            "来源清单",
            "ready" if source_readable else ("action_required" if has_context else "blocked"),
            "已登记可读来源，可进入全文任务。" if source_readable else "需要缓存 PDF、选择文件或上传材料，避免模型只能看到标题/选区。",
            metric=f"可读 {int(source_summary.get('readable') or 0)} / 总计 {int(source_summary.get('total') or 0)}",
            action=source_action,
        ),
        axis(
            "mn_objects",
            "MN 对象",
            "ready" if native_scan_count > 0 else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"已通过原生扫描确认 {native_scan_count} 个对象。" if native_scan_count > 0 else ("需要扫描当前 notebook 的真实 note/card/mindmap 对象。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能请求 MN4 扫描真实对象。"),
            metric=f"native {native_scan_count} / registry {int(objects.get('registry') or 0)}",
            action=mn_objects_action,
        ),
        axis(
            "mindmap_baseline",
            "脑图基线",
            "ready" if mindmap_ready else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"已读取 {int(mindmap.get('nodeCount') or 0)} 个脑图节点。" if mindmap_ready else ("需要读取现有脑图，后续补全/重组必须基于真实树。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能读取当前脑图树。"),
            metric=f"{int(mindmap.get('nodeCount') or 0)} 节点",
            action=mindmap_action,
        ),
        axis(
            "card_coverage",
            "卡片覆盖",
            "ready" if review_total > 0 else ("action_required" if has_context else "blocked"),
            f"已有 {review_total} 张对象级复习卡。" if review_total > 0 else "需要按概念、公式、方法、证据和局限生成可复习短卡。",
            metric=f"{review_total} 卡 / 到期 {int(review.get('due') or 0)}",
            action=card_action,
        ),
        axis(
            "workflow_runtime",
            "Workflow",
            "ready" if workflow_count > 0 else ("pending" if has_context else "blocked"),
            f"已有 {workflow_count} 个 workflow run，最近状态 {workflows.get('latestStatus') or 'unknown'}。" if workflow_count > 0 else "长任务还没有进入可暂停、可恢复、可验收 workflow。",
            metric=f"{workflow_count} run",
            action=workflow_action,
        ),
        axis(
            "operation_ledger",
            "操作账本",
            "ready" if ledger_total > 0 else ("pending" if has_context else "blocked"),
            f"已有 {ledger_total} 条对象/文档操作证据。" if ledger_total > 0 else "写入、确认和回滚还没有形成 Operation Ledger 证据。",
            metric=f"{ledger_total} 条",
            action=actions_by_id.get("open_operation_ledger"),
        ),
        axis(
            "verification_evidence",
            "验证证据",
            "ready" if ledger_total > 0 else "waiting_evidence",
            "可从 Verification Center 读取 PASS/FAIL/UNKNOWN 报告；矩阵只证明已有可检查证据，不冒充验证通过。" if ledger_total > 0 else "等待写入、回滚或来源/技能运行后产生可验证证据。",
            metric="Verification Center",
            action=actions_by_id.get("open_verification_center"),
        ),
    ]
    non_ready = [item["id"] for item in axes if item.get("status") != "ready"]
    recommended_axis_ids = non_ready[:4]
    if ledger_total > 0 and "verification_evidence" not in recommended_axis_ids:
        recommended_axis_ids.append("verification_evidence")
    ready_count = sum(1 for item in axes if item.get("status") == "ready")
    blocked_count = sum(1 for item in axes if item.get("status") == "blocked")
    action_count = sum(1 for item in axes if item.get("status") == "action_required")
    waiting_count = sum(1 for item in axes if item.get("status") in {"pending", "waiting_evidence"})
    return {
        "schema": KNOWLEDGE_CONSOLE_MATRIX_SCHEMA,
        "mode": "zero_message",
        "requiresPrompt": False,
        "status": "blocked" if blocked_count else ("action_required" if action_count else ("waiting_evidence" if waiting_count else "ready")),
        "axisCount": len(axes),
        "readyCount": ready_count,
        "actionRequiredCount": action_count,
        "blockedCount": blocked_count,
        "waitingCount": waiting_count,
        "recommendedAxisIds": recommended_axis_ids,
        "axes": axes,
    }
