from __future__ import annotations

import hashlib
import re
from typing import Any


AGENT_OPERATION_SCHEMA = "codex.mn.agentOperation.v1"
MN_OBJECT_SCHEMA = "codex.mn.mnObject.v1"


WRITE_ACTIONS = {
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
    "write_draft",
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
        "nextActions": next_actions(workflow, risk),
    }
