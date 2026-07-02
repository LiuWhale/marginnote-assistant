from __future__ import annotations

from typing import Any


NOTEBOOK_WORKSPACE_ACTION_SCHEMA = "codex.mn.notebookWorkspaceAction.v1"
OBJECT_INTAKE_SCHEMA = "codex.mn.objectIntake.v1"
OBJECT_INTAKE_ROUTE_SCHEMA = "codex.mn.objectIntakeRoute.v1"


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


def object_ref_has_identity(object_ref: dict[str, Any]) -> bool:
    if not isinstance(object_ref, dict):
        return False
    source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
    return bool(
        object_ref.get("objectId")
        or object_ref.get("kind")
        or object_ref.get("title")
        or source_ref.get("quote")
        or source_ref.get("documentTitle")
        or source_ref.get("path")
        or source_ref.get("page") is not None
    )


def object_ref_has_real_identity(object_ref: dict[str, Any]) -> bool:
    if not isinstance(object_ref, dict):
        return False
    source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
    object_id = str(object_ref.get("objectId") or "")
    kind = str(object_ref.get("kind") or "")
    title = str(object_ref.get("title") or "")
    if object_id.startswith("mnobj:unknown:") or kind == "unknown" or title == "未识别当前对象":
        return bool(
            source_ref.get("quote")
            or source_ref.get("documentTitle")
            or source_ref.get("path")
            or source_ref.get("noteId")
            or source_ref.get("page") is not None
        )
    return object_ref_has_identity(object_ref)


def intake_route(
    route_id: str,
    title: str,
    status: str,
    detail: str,
    *,
    action: dict[str, Any] | None = None,
    evidence: str = "",
    priority: int = 50,
) -> dict[str, Any]:
    return {
        "schema": OBJECT_INTAKE_ROUTE_SCHEMA,
        "id": route_id,
        "title": title,
        "status": status,
        "detail": detail,
        "evidence": evidence,
        "priority": priority,
        "action": action if isinstance(action, dict) else {},
    }


def _actions_by_id(primary_actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}


def build_intake(summary: dict[str, Any], primary_actions: list[dict[str, Any]]) -> dict[str, Any]:
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
    source_action_plan = source_registry.get("actionPlan") if isinstance(source_registry.get("actionPlan"), dict) else {}
    source_repair_action = source_action_plan.get("recommendedAction") if isinstance(source_action_plan.get("recommendedAction"), dict) else {}

    has_focus = object_ref_has_real_identity(focus)
    has_notebook_scope = bool(summary.get("topicid") or summary.get("bookmd5"))
    has_context = bool(has_focus or has_notebook_scope or summary.get("documentTitle"))
    document_title = str(summary.get("documentTitle") or summary.get("bookmd5") or summary.get("topicid") or "")
    object_ref = focus if has_focus else {
        "objectId": f"document:{summary.get('bookmd5') or summary.get('topicid') or 'current'}",
        "kind": "document" if document_title else "",
        "title": document_title,
        "sourceRef": {
            "topicid": str(summary.get("topicid") or ""),
            "bookmd5": str(summary.get("bookmd5") or ""),
            "documentTitle": document_title,
        },
    }
    object_title = str(object_ref.get("title") or object_ref.get("objectId") or document_title or "等待 MarginNote 对象")
    object_kind = str(object_ref.get("kind") or ("document" if document_title else "unknown"))
    mn_api_available = bool(readiness.get("mnApiAvailable"))
    source_readable = int(source_summary.get("readable") or 0) > 0
    native_scan_count = int(objects.get("nativeScan") or 0)
    mindmap_ready = str(mindmap.get("status") or "") == "available"
    review_total = int(review.get("total") or 0)
    workflow_count = int(workflows.get("runCount") or 0)
    ledger_total = int(ledger.get("total") or 0)

    source_action = actions_by_id.get("open_source_registry") if source_readable else source_repair_action
    object_action = actions_by_id.get("open_object_browser") if native_scan_count > 0 else (actions_by_id.get("scan_mn_objects") if has_notebook_scope else {})
    mindmap_action = actions_by_id.get("open_mindmap_studio") if mindmap_ready else (actions_by_id.get("read_mindmap_tree") if has_notebook_scope else {})
    workflow_action = actions_by_id.get("open_workflow_builder") if workflow_count > 0 else actions_by_id.get("open_workflows")

    routes = [
        intake_route(
            "route_source_registry",
            "读材料",
            "ready" if source_readable else ("action_required" if has_context else "blocked"),
            "已有可读来源，全文任务可以直接使用真实材料。" if source_readable else "先补齐 PDF 缓存、上传文件或文件路径，避免聊天回答只看到标题。",
            action=source_action,
            evidence=f"readable={int(source_summary.get('readable') or 0)} / total={int(source_summary.get('total') or 0)}",
            priority=10,
        ),
        intake_route(
            "route_object_browser",
            "看 MN 对象",
            "ready" if native_scan_count > 0 else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"已确认 {native_scan_count} 个原生对象，可进入 Object Browser。" if native_scan_count > 0 else ("先扫描 notebook 里的真实 note/card/mindmap 对象。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能请求 MN4 扫描真实对象。"),
            action=object_action,
            evidence=f"nativeScan={native_scan_count} / registry={int(objects.get('registry') or 0)}",
            priority=20,
        ),
        intake_route(
            "route_mindmap_studio",
            "整理脑图",
            "ready" if mindmap_ready else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"已有 {int(mindmap.get('nodeCount') or 0)} 个节点的脑图基线，可进入 Mindmap Studio。" if mindmap_ready else ("先读取当前脑图树，后续重组、合并和回滚才有基线。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能读取当前脑图树。"),
            action=mindmap_action,
            evidence=f"nodes={int(mindmap.get('nodeCount') or 0)}",
            priority=30,
        ),
        intake_route(
            "route_card_factory",
            "做复习卡",
            "ready" if review_total > 0 else ("action_required" if has_context else "blocked"),
            f"已有 {review_total} 张对象级复习卡，可检查质量和到期状态。" if review_total > 0 else "进入 Card Factory 按概念、公式、方法、证据和局限制卡。",
            action=actions_by_id.get("open_card_factory"),
            evidence=f"cards={review_total} / due={int(review.get('due') or 0)}",
            priority=40,
        ),
        intake_route(
            "route_workflow_builder",
            "跑长任务",
            "ready" if workflow_count > 0 else ("pending" if has_context else "blocked"),
            f"已有 {workflow_count} 个 workflow run，可查看确认点、重试和结果。" if workflow_count > 0 else "把精读、制卡、脑图重组这类长任务放进可暂停、可恢复的 workflow。",
            action=workflow_action,
            evidence=f"runs={workflow_count} / templates={int(workflows.get('templateCount') or 0)}",
            priority=50,
        ),
        intake_route(
            "route_skill_center",
            "用技能包",
            "pending" if has_context else "blocked",
            "查看围绕当前对象可安装或运行的技能包；写入技能必须声明权限、dry-run、回滚和验收规则。",
            action=actions_by_id.get("open_skill_center"),
            evidence="Skill Runtime",
            priority=60,
        ),
        intake_route(
            "route_verification_center",
            "验证/回滚",
            "ready" if ledger_total > 0 else ("pending" if has_context else "blocked"),
            f"已有 {ledger_total} 条账本证据，可进入 Verification Center 查看 PASS/FAIL/UNKNOWN。" if ledger_total > 0 else "等待写入、缓存或 workflow 形成账本证据后再验证。",
            action=actions_by_id.get("open_verification_center"),
            evidence=f"ledger={ledger_total}",
            priority=70,
        ),
    ]
    ready_count = sum(1 for route in routes if route.get("status") == "ready")
    blocked_count = sum(1 for route in routes if route.get("status") == "blocked")
    action_count = sum(1 for route in routes if route.get("status") == "action_required")
    pending_count = sum(1 for route in routes if route.get("status") == "pending")
    recommended_ids = [
        route["id"]
        for route in routes
        if route.get("status") in {"action_required", "pending"}
        and isinstance(route.get("action"), dict)
        and route.get("action", {}).get("action")
    ][:4]
    if not recommended_ids:
        recommended_ids = [
            route["id"]
            for route in routes
            if isinstance(route.get("action"), dict) and route.get("action", {}).get("action")
        ][:3]
    return {
        "schema": OBJECT_INTAKE_SCHEMA,
        "mode": "object_first",
        "requiresPrompt": False,
        "status": "blocked" if not has_context or blocked_count == len(routes) else ("action_required" if action_count else ("pending" if pending_count else "ready")),
        "objectRef": object_ref if has_context else {},
        "objectLabel": object_title,
        "objectKind": object_kind,
        "routeCount": len(routes),
        "readyCount": ready_count,
        "actionRequiredCount": action_count,
        "pendingCount": pending_count,
        "blockedCount": blocked_count,
        "recommendedRouteIds": recommended_ids,
        "routes": routes,
    }
