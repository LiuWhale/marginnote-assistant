from __future__ import annotations

import hashlib
import re
from typing import Any


AGENT_OPERATION_SCHEMA = "codex.mn.agentOperation.v1"
MN_OBJECT_SCHEMA = "codex.mn.mnObject.v1"
OPERATION_PLAN_SCHEMA = "codex.mn.operationPlan.v1"
VERIFICATION_PLAN_SCHEMA = "codex.mn.verificationPlan.v1"
OPERATION_COMPILER_SCHEMA = "codex.mn.operationCompiler.v1"


WRITE_ACTIONS = {
    "write_draft",
    "request_native_highlight_selection",
    "mindmap_diff_apply",
    "object_graph_relation_save",
    "object_graph_relation_delete",
    "review_queue_add",
}

DRAFT_ACTIONS = {
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
}


READ_ACTION_REQUIREMENTS = {
    "request_pdf_cache": ["cacheCurrentPdf"],
    "mn_read_tree": ["readMindmapTree"],
    "knowledge_index_search": [],
    "chat": [],
    "operation_plan_preview": [],
    "ai_edit_transaction_get": ["rollbackLedger"],
}

WRITE_ACTION_REQUIREMENTS = {
    "write_draft": ["nativeCards", "nativeMindmap", "rollbackLedger"],
    "request_native_highlight_selection": ["nativeHighlightSelection"],
}

DRAFT_ACTION_REQUIREMENTS = {
    "generate_full_reading": ["aiBackend", "cacheCurrentPdf"],
    "generate_card": ["aiBackend"],
    "generate_mindmap": ["aiBackend"],
    "expand_node": ["aiBackend", "readMindmapTree"],
    "reorganize_mindmap": ["aiBackend", "readMindmapTree"],
}


def _clean(value: Any, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _first_text(payload: dict[str, Any], keys: list[str], limit: int = 500) -> str:
    for key in keys:
        text = _clean(payload.get(key), limit)
        if text:
            return text
    return ""


def _first_int(payload: dict[str, Any], keys: list[str]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def detect_object_focus(payload: dict[str, Any]) -> dict[str, Any]:
    selected_note_id = _first_text(payload, ["selectedNoteId", "noteId"], 160)
    selected_note_title = _first_text(payload, ["selectedNoteTitle", "noteTitle"], 220)
    selected_note_text = _first_text(payload, ["selectedNoteText", "noteText", "nodeText"], 700)
    selection_text = _first_text(payload, ["selectionText", "selectedText", "text"], 700)
    document_title = _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260)
    book_md5 = _first_text(payload, ["bookmd5", "bookMd5", "docmd5", "docMd5"], 200)
    target = payload.get("mindmapTarget") if isinstance(payload.get("mindmapTarget"), dict) else {}
    target_label = _first_text(target, ["label", "title", "rootTitle"], 240)

    if target_label and re.search(r"脑图|mindmap|map", str(payload.get("prompt") or target_label), re.I):
        kind = "mindmap"
        title = target_label
        summary = _clean(target.get("selectedNoteTitle") or selected_note_title or target_label, 700)
    elif selected_note_id or selected_note_title or selected_note_text:
        kind = "note"
        title = selected_note_title or selected_note_id or "当前卡片/节点"
        summary = selected_note_text or selected_note_title
    elif selection_text:
        kind = "selection"
        title = "PDF 选区"
        summary = selection_text
    elif document_title or book_md5:
        kind = "document"
        title = document_title or book_md5 or "当前文档"
        summary = document_title or book_md5
    else:
        kind = "unknown"
        title = "未识别当前对象"
        summary = ""

    return {
        "kind": kind,
        "title": title,
        "summary": summary,
        "topicid": _first_text(payload, ["topicid", "topicId", "notebookid", "notebookId"], 200),
        "bookmd5": book_md5,
        "selectedNoteId": selected_note_id,
        "documentTitle": document_title,
        "mindmapTarget": target_label,
    }


def _mn_object_id(kind: str, identifiers: dict[str, Any], summary: str) -> str:
    basis = "|".join(
        [
            kind,
            str(identifiers.get("topicid") or ""),
            str(identifiers.get("bookmd5") or ""),
            str(identifiers.get("docmd5") or ""),
            str(identifiers.get("noteId") or ""),
            str(identifiers.get("documentTitle") or ""),
            summary[:160],
        ]
    )
    digest = hashlib.sha1(basis.encode("utf-8")).hexdigest()[:12]
    return f"mnobj:{kind}:{digest}"


def _source_ref(payload: dict[str, Any], object_focus: dict[str, Any]) -> dict[str, Any]:
    quote = _first_text(payload, ["quote", "selectionText", "selectedText", "activeSelectionText", "selectedNoteText", "noteText"], 900)
    return {
        "page": _first_int(payload, ["page", "pageNumber", "pageIndex"]),
        "quote": quote,
        "documentTitle": object_focus.get("documentTitle") or _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260),
        "path": _first_text(payload, ["pdfPath", "documentPath", "sourcePath", "filePath"], 900),
    }


def _mn_object_relations(kind: str, identifiers: dict[str, Any]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    book_md5 = _clean(identifiers.get("bookmd5"), 200)
    topic_id = _clean(identifiers.get("topicid"), 200)
    note_id = _clean(identifiers.get("noteId"), 200)
    if book_md5:
        relations.append({"type": "belongs_to", "targetKind": "document", "targetId": book_md5})
    if topic_id:
        relations.append({"type": "belongs_to", "targetKind": "notebook", "targetId": topic_id})
    if kind == "mindmap" and note_id:
        relations.append({"type": "rooted_at", "targetKind": "note", "targetId": note_id})
    elif kind == "note" and note_id:
        relations.append({"type": "focuses", "targetKind": "note", "targetId": note_id})
    return relations


def _mn_object_actions(kind: str) -> list[dict[str, Any]]:
    base = [
        {"id": "explain_object", "label": "解释对象", "action": "chat", "writes": False},
        {"id": "search_related", "label": "找相关知识", "action": "knowledge_index_search", "writes": False},
    ]
    if kind == "selection":
        return [
            base[0],
            {"id": "create_cards", "label": "生成卡片", "action": "generate_card", "writes": True},
            {"id": "create_mindmap", "label": "生成脑图树", "action": "generate_mindmap", "writes": True},
            {"id": "highlight_selection", "label": "高亮选区", "action": "request_native_highlight_selection", "writes": True},
            base[1],
        ]
    if kind == "note":
        return [
            base[0],
            {"id": "create_cards", "label": "生成卡片", "action": "generate_card", "writes": True},
            {"id": "expand_node", "label": "扩展节点", "action": "expand_node", "writes": True},
            {"id": "reorganize_subtree", "label": "重组子树", "action": "reorganize_mindmap", "writes": True},
            base[1],
        ]
    if kind == "mindmap":
        return [
            {"id": "read_current_tree", "label": "读取当前脑图", "action": "mn_read_tree", "writes": False},
            {"id": "reorganize_subtree", "label": "重组脑图", "action": "reorganize_mindmap", "writes": True},
            {"id": "create_mindmap", "label": "生成脑图树", "action": "generate_mindmap", "writes": True},
            base[1],
        ]
    if kind == "document":
        return [
            base[0],
            {"id": "full_reading", "label": "精读全文", "action": "generate_full_reading", "writes": True},
            {"id": "create_mindmap", "label": "生成脑图树", "action": "generate_mindmap", "writes": True},
            base[1],
        ]
    return base[:1]


def _permission_boundary(kind: str, actions: list[dict[str, Any]]) -> dict[str, Any]:
    write_actions = [item.get("id") for item in actions if item.get("writes")]
    return {
        "readable": kind != "unknown",
        "writeActionCount": len(write_actions),
        "writeActions": write_actions,
        "requiresConfirmationForWrites": bool(write_actions),
        "requiresFullPermissionForHighlight": kind == "selection",
    }


def build_mn_object(payload: dict[str, Any]) -> dict[str, Any]:
    object_focus = detect_object_focus(payload)
    topic_id = object_focus.get("topicid") or _first_text(payload, ["topicid", "topicId", "notebookid", "notebookId"], 200)
    book_md5 = object_focus.get("bookmd5") or _first_text(payload, ["bookmd5", "bookMd5"], 200)
    identifiers = {
        "topicid": topic_id,
        "bookmd5": book_md5,
        "docmd5": _first_text(payload, ["docmd5", "docMd5"], 200),
        "noteId": object_focus.get("selectedNoteId") or _first_text(payload, ["selectedNoteId", "noteId"], 200),
        "documentTitle": object_focus.get("documentTitle") or _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260),
    }
    source_ref = _source_ref(payload, object_focus)
    actions = _mn_object_actions(str(object_focus.get("kind") or "unknown"))
    return {
        "schema": MN_OBJECT_SCHEMA,
        "objectId": _mn_object_id(str(object_focus.get("kind") or "unknown"), identifiers, str(object_focus.get("summary") or "")),
        "kind": object_focus.get("kind") or "unknown",
        "title": object_focus.get("title") or "",
        "summary": object_focus.get("summary") or "",
        "identifiers": identifiers,
        "sourceRef": source_ref,
        "relations": _mn_object_relations(str(object_focus.get("kind") or "unknown"), identifiers),
        "availableActions": actions,
        "permissionBoundary": _permission_boundary(str(object_focus.get("kind") or "unknown"), actions),
    }


def _context_policy(payload: dict[str, Any], object_focus: dict[str, Any]) -> dict[str, Any]:
    requested_scope = _clean(payload.get("contextScope") or payload.get("scope") or "auto", 80) or "auto"
    explicit_full = bool(re.search(r"全文|整篇|完整|full|whole", str(payload.get("prompt") or ""), re.I))
    explicit_knowledge = bool(payload.get("includeKnowledgeIndex")) or bool(
        re.search(r"之前|已有|历史|索引|知识库|相关|关联|跨文档|notebook|knowledge|previous|related|index", str(payload.get("prompt") or ""), re.I)
    )
    if requested_scope == "auto":
        if object_focus.get("kind") == "selection":
            visible_scope = "selection"
        elif explicit_full:
            visible_scope = "document"
        elif object_focus.get("kind") in {"note", "mindmap"}:
            visible_scope = object_focus["kind"]
        else:
            visible_scope = "document" if object_focus.get("kind") == "document" else "none"
    else:
        visible_scope = requested_scope
    return {
        "requestedScope": requested_scope,
        "visibleScope": visible_scope,
        "explicitFullDocument": explicit_full,
        "explicitKnowledgeIndex": explicit_knowledge,
        "expansionRequiresUserVisibleState": True,
    }


def _workflow_risk(workflow: dict[str, Any], dry_run: dict[str, Any] | None = None) -> dict[str, Any]:
    steps = workflow.get("steps") if isinstance(workflow.get("steps"), list) else []
    write_steps = [
        step
        for step in steps
        if isinstance(step, dict)
        and (step.get("writes") or str(step.get("action") or "") in WRITE_ACTIONS)
    ]
    confirmation_points = workflow.get("confirmationPoints") if isinstance(workflow.get("confirmationPoints"), list) else []
    dry_run = dry_run if isinstance(dry_run, dict) else {}
    if dry_run.get("status") == "blocked":
        status = "blocked"
    elif write_steps:
        status = "write_pending_confirmation"
    else:
        status = "read_only"
    return {
        "status": status,
        "writeStepCount": len(write_steps),
        "confirmationPoints": [str(item) for item in confirmation_points],
        "dryRunStatus": str(dry_run.get("status") or "not_available"),
        "requiresAcceptReject": bool(write_steps),
    }


def _risk_tone(status: str) -> str:
    value = str(status or "").lower()
    if value in {"blocked", "missing", "failed", "error", "read_only_blocked"}:
        return "block"
    if value in {"not_available", "required", "write_pending_confirmation", "unknown"}:
        return "warn"
    return "pass"


def _risk_item(item_id: str, label: str, status: str, detail: str = "", tone: str = "") -> dict[str, str]:
    return {
        "id": item_id,
        "label": label,
        "status": status,
        "detail": detail,
        "tone": tone or _risk_tone(status),
    }


def _workflow_steps(workflow: dict[str, Any]) -> list[dict[str, Any]]:
    steps = workflow.get("steps") if isinstance(workflow.get("steps"), list) else []
    return [step for step in steps if isinstance(step, dict)]


def _workflow_actions(workflow: dict[str, Any]) -> set[str]:
    return {str(step.get("action") or "") for step in _workflow_steps(workflow) if str(step.get("action") or "")}


def _step_requires(action: str, workflow_actions: set[str], writes: bool = False) -> list[str]:
    action = str(action or "")
    requirements: list[str] = []
    if action in READ_ACTION_REQUIREMENTS:
        requirements.extend(READ_ACTION_REQUIREMENTS[action])
    if not writes and action in DRAFT_ACTION_REQUIREMENTS:
        requirements.extend(DRAFT_ACTION_REQUIREMENTS[action])
    if writes and action in WRITE_ACTION_REQUIREMENTS:
        requirements.extend(WRITE_ACTION_REQUIREMENTS[action])
    if action == "write_draft":
        if "generate_card" not in workflow_actions:
            requirements = [item for item in requirements if item != "nativeCards"]
        if not ({"generate_mindmap", "expand_node", "reorganize_mindmap", "mn_read_tree"} & workflow_actions):
            requirements = [item for item in requirements if item != "nativeMindmap"]
    return sorted(set(requirements))


def _step_mutation(action: str, writes: bool) -> str:
    if not writes:
        return "none"
    if action == "request_native_highlight_selection":
        return "update"
    if action in {"reorganize_mindmap", "expand_node"}:
        return "create_update_move"
    return "create"


def _step_rollback(action: str, writes: bool) -> dict[str, Any]:
    if not writes:
        return {"strategy": "not_required", "requiresLedger": False}
    if action == "request_native_highlight_selection":
        return {
            "strategy": "manual_or_native_undo",
            "requiresLedger": True,
            "residualRisk": "native_highlight_visibility",
        }
    return {
        "strategy": "ai_edit_transaction",
        "requiresLedger": True,
        "residualRisk": "created_note_or_mindmap_node",
    }


def _confirmation_points(workflow: dict[str, Any]) -> set[str]:
    return {str(item) for item in (workflow.get("confirmationPoints") if isinstance(workflow.get("confirmationPoints"), list) else []) if str(item)}


def _operation_plan_status(write_count: int, permission: str, dry_run: dict[str, Any]) -> str:
    if write_count and permission == "read_only":
        return "blocked"
    dry_status = str(dry_run.get("status") or "")
    if dry_status == "blocked":
        return "blocked"
    if write_count:
        return "waiting_dry_run"
    return "read_only"


def build_operation_plan(
    payload: dict[str, Any],
    *,
    mn_object: dict[str, Any],
    context_policy: dict[str, Any],
    workflow: dict[str, Any],
    dry_run: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dry_run = dry_run if isinstance(dry_run, dict) else {}
    settings = settings if isinstance(settings, dict) else {}
    steps = _workflow_steps(workflow)
    workflow_actions = _workflow_actions(workflow)
    confirmations = _confirmation_points(workflow)
    object_ref = {
        "objectId": str(mn_object.get("objectId") or ""),
        "kind": str(mn_object.get("kind") or ""),
        "title": _clean(mn_object.get("title"), 220),
        "sourceRef": mn_object.get("sourceRef") if isinstance(mn_object.get("sourceRef"), dict) else {},
    }
    operations: list[dict[str, Any]] = []
    for index, step in enumerate(steps, start=1):
        step_id = _clean(step.get("id") or f"step_{index}", 80) or f"step_{index}"
        action = _clean(step.get("action"), 120)
        writes = bool(step.get("writes")) or action in {"write_draft", "request_native_highlight_selection"}
        confirmation_required = writes or step_id in confirmations or action in {"write_draft", "operation_plan_preview"}
        operations.append(
            {
                "opId": f"workflow:{step_id}",
                "op": "workflow_step",
                "action": action,
                "mutation": _step_mutation(action, writes),
                "writes": writes,
                "title": _clean(step.get("title") or action or step_id, 240),
                "stepId": step_id,
                "stepIndex": index,
                "objectRef": object_ref,
                "contextScope": str(context_policy.get("visibleScope") or "none"),
                "requires": _step_requires(action, workflow_actions, writes),
                "confirmationRequired": confirmation_required,
                "confirmationPoint": step_id if confirmation_required else "",
                "rollback": _step_rollback(action, writes),
            }
        )
    write_count = len([operation for operation in operations if operation.get("writes")])
    required_capabilities = sorted(
        {requirement for operation in operations for requirement in operation.get("requires", [])}
    )
    permission = _clean(settings.get("permission") or "notes", 80)
    return {
        "schema": OPERATION_PLAN_SCHEMA,
        "planType": "workflow",
        "compiler": OPERATION_COMPILER_SCHEMA,
        "status": _operation_plan_status(write_count, permission, dry_run),
        "workflowId": _clean(workflow.get("id") or payload.get("workflowId"), 120),
        "workflowTitle": _clean(workflow.get("title"), 220),
        "objectRef": object_ref,
        "contextPolicy": {
            "requestedScope": str(context_policy.get("requestedScope") or "auto"),
            "visibleScope": str(context_policy.get("visibleScope") or "none"),
            "explicitFullDocument": bool(context_policy.get("explicitFullDocument")),
            "explicitKnowledgeIndex": bool(context_policy.get("explicitKnowledgeIndex")),
        },
        "operationCount": len(operations),
        "writeCount": write_count,
        "confirmationPointCount": len([operation for operation in operations if operation.get("confirmationRequired")]),
        "operations": operations,
        "requiredCapabilities": required_capabilities,
        "dryRun": {
            "status": str(dry_run.get("status") or "not_available"),
            "message": _clean(dry_run.get("message"), 260),
            "blockedCount": int(dry_run.get("blockedCount") or 0),
            "unknownCount": int(dry_run.get("unknownCount") or 0),
            "checks": [
                item
                for item in (dry_run.get("checks") if isinstance(dry_run.get("checks"), list) else [])
                if isinstance(item, dict)
            ][:8],
        },
        "verify": {
            "expectedCreatedItems": write_count,
            "requiresRollbackLedger": bool(write_count),
            "requiresResidualReport": bool(write_count),
        },
    }


def build_verification_plan(operation_plan: dict[str, Any]) -> dict[str, Any]:
    operations = operation_plan.get("operations") if isinstance(operation_plan.get("operations"), list) else []
    write_operations = [operation for operation in operations if isinstance(operation, dict) and operation.get("writes")]
    write_count = len(write_operations)
    expected_events = []
    if write_count:
        expected_events.extend(["aiEditTransactionStarted", "aiEditTransactionAccepted"])
    if any("nativeMindmap" in (operation.get("requires") or []) for operation in write_operations):
        expected_events.append("mindmapDiffApplyFinished")
    if any("nativeCards" in (operation.get("requires") or []) for operation in write_operations):
        expected_events.append("createCardsFinished")
    return {
        "schema": VERIFICATION_PLAN_SCHEMA,
        "status": "required" if write_count else "not_required",
        "mustVerifyCreatedObjects": bool(write_count),
        "mustVerifyRollback": bool(write_count),
        "mustReportResidualObjects": bool(write_count),
        "expectedWriteOperationCount": write_count,
        "expectedEvents": sorted(set(expected_events)),
        "residualChecks": [
            "created_note_ids",
            "mindmap_outline_nodes",
            "card_entities",
            "manual_relations",
            "review_queue_entries",
        ] if write_count else [],
    }


def _repair_action(action_id: str, label: str, handler: str, detail: str = "") -> dict[str, str]:
    return {
        "id": action_id,
        "label": label,
        "handler": handler,
        "detail": _clean(detail, 260),
    }


def _dedupe_repair_actions(actions: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for action in actions:
        action_id = str(action.get("id") or "")
        if not action_id or action_id in seen:
            continue
        seen.add(action_id)
        result.append(action)
    return result


def operation_compiler_repair_actions(operation_plan: dict[str, Any], settings: dict[str, Any]) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    write_count = int(operation_plan.get("writeCount") or 0)
    permission = _clean(settings.get("permission") or "notes", 80)
    if write_count and permission == "read_only":
        actions.append(_repair_action("open_settings", "打开设置", "openConfigPage", "把权限从 read_only 改为 notes 或 full。"))
    dry_run = operation_plan.get("dryRun") if isinstance(operation_plan.get("dryRun"), dict) else {}
    dry_status = str(dry_run.get("status") or "")
    checks = dry_run.get("checks") if isinstance(dry_run.get("checks"), list) else []
    if dry_status in {"blocked", "unknown"} or int(dry_run.get("blockedCount") or 0) or int(dry_run.get("unknownCount") or 0):
        detail = _clean(dry_run.get("message") or "刷新 MN 原生能力后重新生成 Agent 操作计划。", 260)
        actions.append(_repair_action("refresh_native_capabilities", "刷新 MN 能力", "refreshNativeCapabilities", detail))
        actions.append(_repair_action("open_settings", "打开设置", "openConfigPage", "检查 MN API 后端、权限和 URL API Gateway 配置。"))
    for check in checks:
        if not isinstance(check, dict):
            continue
        reason = str(check.get("reason") or "")
        next_step = _clean(check.get("nextStep") or "", 260)
        if reason in {"url-api-secret-missing"} or "URL API" in next_step or "Gateway" in next_step:
            actions.append(_repair_action("open_settings", "配置 URL API", "openConfigPage", next_step or "配置 URL API Secret，或切回自动/原生插件后端。"))
        if reason in {"needs-current-pdf-path", "needs-pdf-cache-or-path"} or "缓存 PDF" in next_step:
            actions.append(_repair_action("cache_current_pdf", "缓存当前 PDF", "cacheCurrentPdf", next_step or "让 MN4 插件缓存当前 PDF 后重试。"))
    return _dedupe_repair_actions(actions)


def build_operation_compiler_report(
    *,
    operation_plan: dict[str, Any],
    verification_plan: dict[str, Any],
    context_policy: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    write_count = int(operation_plan.get("writeCount") or 0)
    permission = _clean(settings.get("permission") or "notes", 80)
    checks = [
        _risk_item("schema", "Schema", "pass", "agentOperation / operationPlan / verificationPlan schema 已生成。"),
        _risk_item(
            "context",
            "Context",
            str(context_policy.get("visibleScope") or "none"),
            "可见范围：" + str(context_policy.get("visibleScope") or "none"),
            "pass" if context_policy.get("visibleScope") not in {"", "none", None} else "warn",
        ),
        _risk_item(
            "permission",
            "Permission",
            "blocked" if write_count and permission == "read_only" else "pass",
            "只读权限会阻断写入。" if write_count and permission == "read_only" else "权限允许当前计划继续到 dry-run。",
        ),
        _risk_item(
            "dry_run",
            "Dry-run",
            str((operation_plan.get("dryRun") or {}).get("status") or "not_available"),
            "写入前仍需 dry-run。" if write_count else "只读计划不需要 dry-run。",
        ),
        _risk_item(
            "verification",
            "Verification",
            str(verification_plan.get("status") or "unknown"),
            "写入后必须验证对象、回滚和残留。" if write_count else "无写入验证要求。",
        ),
    ]
    return {
        "schema": OPERATION_COMPILER_SCHEMA,
        "status": "blocked" if any(item.get("tone") == "block" for item in checks) else ("needs_dry_run" if write_count else "ready"),
        "checkCount": len(checks),
        "checks": checks,
        "repairActions": operation_compiler_repair_actions(operation_plan, settings),
    }


def _target_mindmap_required(payload: dict[str, Any], workflow: dict[str, Any]) -> bool:
    text = " ".join(
        [
            str(payload.get("prompt") or ""),
            str(payload.get("action") or ""),
            str(payload.get("workflowId") or ""),
            str(workflow.get("id") or ""),
            str(workflow.get("title") or ""),
        ]
    )
    return bool(re.search(r"mindmap|脑图|卡片树|树|map", text, re.I))


def _risk_register(
    payload: dict[str, Any],
    *,
    mn_object: dict[str, Any],
    context_policy: dict[str, Any],
    workflow: dict[str, Any],
    risk: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, Any]:
    write_count = int(risk.get("writeStepCount") or 0)
    permission = _clean(settings.get("permission") or "notes", 80)
    if write_count and permission == "read_only":
        permission_status = "read_only_blocked"
        permission_detail = "当前权限为只读，写入步骤会被阻断。"
    elif write_count:
        permission_status = "write_allowed"
        permission_detail = f"当前权限允许 {write_count} 个写入步骤进入确认。"
    else:
        permission_status = "read_only"
        permission_detail = "当前计划不包含写入步骤。"

    visible_scope = str(context_policy.get("visibleScope") or "none")
    scope_detail = "AI 当前可见上下文：" + visible_scope
    source_ref = mn_object.get("sourceRef") if isinstance(mn_object.get("sourceRef"), dict) else {}
    if source_ref.get("quote"):
        scope_detail += " / 有选区或摘录。"
    elif source_ref.get("documentTitle") or source_ref.get("path"):
        scope_detail += " / 有文档来源。"

    target = payload.get("mindmapTarget") if isinstance(payload.get("mindmapTarget"), dict) else {}
    target_label = _clean(target.get("label") or target.get("title") or target.get("rootTitle"), 180)
    target_required = _target_mindmap_required(payload, workflow)
    if target_label:
        target_status = "selected"
        target_detail = target_label
    elif target_required:
        target_status = "missing"
        target_detail = "脑图类操作需要先确认目标脑图。"
    else:
        target_status = "not_required"
        target_detail = "当前计划不强制要求目标脑图。"

    dry_run_status = str(risk.get("dryRunStatus") or "not_available")
    dry_run_detail = (
        "写入前必须 dry-run；当前还没有 dry-run 结果。"
        if dry_run_status == "not_available" and write_count
        else "当前 dry-run 状态：" + dry_run_status
    )

    confirmations = [str(item) for item in risk.get("confirmationPoints") or [] if str(item)]
    confirmation_status = "required" if risk.get("requiresAcceptReject") else "not_required"
    confirmation_detail = "确认点：" + (", ".join(confirmations) if confirmations else "accept/reject") if confirmation_status == "required" else "当前计划不需要写入确认。"

    items = [
        _risk_item("permission", "权限", permission_status, permission_detail),
        _risk_item("context_scope", "上下文", visible_scope, scope_detail, "pass" if visible_scope != "none" else "warn"),
        _risk_item("target_mindmap", "目标脑图", target_status, target_detail),
        _risk_item("dry_run", "Dry-run", dry_run_status, dry_run_detail),
        _risk_item("confirmation", "确认点", confirmation_status, confirmation_detail),
    ]
    return {
        "schema": "codex.mn.riskRegister.v1",
        "summary": {
            "status": str(risk.get("status") or "unknown"),
            "itemCount": len(items),
            "blockedCount": len([item for item in items if item["tone"] == "block"]),
            "warningCount": len([item for item in items if item["tone"] == "warn"]),
        },
        "items": items,
    }


def next_actions(workflow: dict[str, Any], risk: dict[str, Any]) -> list[dict[str, Any]]:
    workflow_id = _clean(workflow.get("id"), 120)
    actions: list[dict[str, Any]] = [
        {
            "id": "create_card_tree",
            "label": "生成脑图树",
            "action": "generate_mindmap",
            "scope": "latest_reply",
            "promptCommand": "[create_card_tree]",
            "requiresConfirmation": False,
        },
        {
            "id": "start_workflow",
            "label": "启动工作流",
            "action": "workflow_start",
            "workflowId": workflow_id,
            "requiresConfirmation": False,
        }
    ]
    if re.search(r"mindmap|脑图", workflow_id, re.I):
        actions.append(
            {
                "id": "preview_mindmap_diff",
                "label": "预览脑图 Diff",
                "action": "mindmap_diff_preview",
                "requiresDraft": True,
                "requiresCurrentTree": True,
                "requiresConfirmation": False,
            }
        )
    if risk.get("requiresAcceptReject"):
        actions.append(
            {
                "id": "review_operation_plan",
                "label": "预览写入计划",
                "action": "operation_plan_preview",
                "requiresDraft": True,
                "requiresConfirmation": True,
            }
        )
    actions.append(
        {
            "id": "search_related_context",
            "label": "检索相关知识",
            "action": "knowledge_index_search",
            "requiresExplicitRequest": True,
            "requiresConfirmation": False,
        }
    )
    return actions


def build_agent_operation(
    payload: dict[str, Any],
    *,
    workflow: dict[str, Any] | None = None,
    knowledge: dict[str, Any] | None = None,
    dry_run: dict[str, Any] | None = None,
    settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    workflow = workflow if isinstance(workflow, dict) else {}
    knowledge = knowledge if isinstance(knowledge, dict) else {}
    settings = settings if isinstance(settings, dict) else {}
    mn_object = build_mn_object(payload)
    object_focus = detect_object_focus(payload)
    object_focus["mnObjectId"] = mn_object.get("objectId")
    object_focus["sourceRef"] = mn_object.get("sourceRef")
    object_focus["availableActionCount"] = len(mn_object.get("availableActions") or [])
    context_policy = _context_policy(payload, object_focus)
    risk = _workflow_risk(workflow, dry_run)
    permission = _clean(settings.get("permission") or "notes", 80)
    operation_plan = build_operation_plan(
        payload,
        mn_object=mn_object,
        context_policy=context_policy,
        workflow=workflow,
        dry_run=dry_run,
        settings=settings,
    )
    verification_plan = build_verification_plan(operation_plan)
    compiler_report = build_operation_compiler_report(
        operation_plan=operation_plan,
        verification_plan=verification_plan,
        context_policy=context_policy,
        settings=settings,
    )
    risk_register = _risk_register(
        payload,
        mn_object=mn_object,
        context_policy=context_policy,
        workflow=workflow,
        risk=risk,
        settings=settings,
    )
    return {
        "schema": AGENT_OPERATION_SCHEMA,
        "mnObject": mn_object,
        "object": object_focus,
        "intent": {
            "prompt": _clean(payload.get("prompt") or payload.get("query") or payload.get("text") or "", 1200),
            "workflowId": _clean(workflow.get("id") or payload.get("workflowId") or "", 120),
            "workflowTitle": _clean(workflow.get("title") or "", 200),
        },
        "contextPolicy": context_policy,
        "workflow": {
            "id": _clean(workflow.get("id"), 120),
            "title": _clean(workflow.get("title"), 200),
            "status": _clean(workflow.get("status"), 120),
            "stepCount": int(workflow.get("stepCount") or 0),
            "confirmationPoints": list(workflow.get("confirmationPoints") or []),
        },
        "knowledge": {
            "enabled": bool(context_policy.get("explicitKnowledgeIndex")),
            "scope": "current_notebook" if context_policy.get("explicitKnowledgeIndex") and re.search(r"notebook|跨文档|相关|关联", str(payload.get("prompt") or ""), re.I) else "current_document",
            "count": int(knowledge.get("count") or 0),
            "message": _clean(knowledge.get("message"), 200),
        },
        "operationPolicy": {
            "permission": permission,
            "risk": risk,
            "riskRegister": risk_register,
            "mustDryRunBeforeWrite": True,
            "mustUseAcceptRejectForWrites": True,
            "mustKeepPdfClean": True,
        },
        "operationPlan": operation_plan,
        "verificationPlan": verification_plan,
        "operationCompiler": compiler_report,
        "nextActions": next_actions(workflow, risk),
    }
