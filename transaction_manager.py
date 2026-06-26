from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any


_ROOT = Path.home() / ".codex/marginnote-assistant"
_TRANSACTION_DIR = _ROOT / "control/ai-edit-transactions"
_TRACKED_EVENTS = {
    "aiEditTransactionStarted",
    "aiEditOperationReady",
    "aiEditTransactionAccepted",
    "aiEditTransactionRejected",
    "mindmapDiffApplyRequested",
    "mindmapDiffApplyFinished",
    "mindmapDeleteSuggestionPrepared",
    "mindmapDeleteSuggestionConfirmed",
    "mindmapDeleteSuggestionDismissed",
    "mnObjectExistenceProbeFinished",
}
VERIFICATION_SCHEMA = "codex.mn.aiEditVerification.v1"
RESIDUAL_PROOF_SCHEMA = "codex.mn.residualProof.v1"
OBJECT_EXISTENCE_PROBE_SCHEMA = "codex.mn.objectExistenceProbe.v1"
TRANSACTION_STATUS_SCHEMA = "codex.mn.aiEditTransactionStatus.v1"


def configure(root: Path | str) -> None:
    global _ROOT, _TRANSACTION_DIR
    _ROOT = Path(root).expanduser()
    _TRANSACTION_DIR = _ROOT / "control/ai-edit-transactions"


def safe_transaction_id(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(value or ""))[:96]


def now_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def transaction_path(transaction_id: str) -> Path:
    clean_id = safe_transaction_id(transaction_id)
    if not clean_id:
        raise ValueError("missing transaction id")
    return _TRANSACTION_DIR / f"{clean_id}.json"


def read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return value if isinstance(value, dict) else default


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp-{os.getpid()}")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def load_transaction(transaction_id: str) -> dict[str, Any]:
    clean_id = safe_transaction_id(transaction_id)
    if not clean_id:
        return {}
    return read_json(transaction_path(clean_id), {})


def unique_strings(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    if not isinstance(values, list):
        return out
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def clean_failures(values: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(values, list):
        return out
    for value in values:
        if not isinstance(value, dict):
            continue
        out.append(
            {
                "noteId": str(value.get("noteId") or ""),
                "method": str(value.get("method") or ""),
                "reason": str(value.get("reason") or ""),
            }
        )
    return out


def clean_delete_operations(values: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(values, list):
        return out
    for value in values:
        if not isinstance(value, dict):
            continue
        current_ref = value.get("currentRef") if isinstance(value.get("currentRef"), dict) else {}
        out.append(
            {
                "opId": str(value.get("opId") or ""),
                "title": str(value.get("title") or "")[:240],
                "noteId": str(current_ref.get("noteId") or value.get("noteId") or ""),
                "reason": str(value.get("reason") or ""),
            }
        )
    return out


def clean_undo_rollback(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {
        "ok": bool(value.get("ok")),
        "method": str(value.get("method") or ""),
        "deleted": int(value.get("deleted") or 0),
        "remaining": int(value.get("remaining") or 0),
        "reason": str(value.get("reason") or ""),
    }


def clean_object_existence_probe(value: Any, *, transaction_id: str = "") -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    results_in = value.get("results") if isinstance(value.get("results"), list) else []
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in results_in:
        if not isinstance(item, dict):
            continue
        note_id = str(item.get("noteId") or item.get("id") or "").strip()
        if not note_id or note_id in seen:
            continue
        seen.add(note_id)
        exists = bool(item.get("exists"))
        results.append(
            {
                "noteId": note_id,
                "objectId": str(item.get("objectId") or f"mnobj:note:{note_id}"),
                "exists": exists,
                "title": str(item.get("title") or "")[:240],
                "kind": str(item.get("kind") or "mindmap_node"),
                "reason": str(item.get("reason") or ""),
            }
        )
    existing_count = len([item for item in results if item.get("exists")])
    return {
        "schema": OBJECT_EXISTENCE_PROBE_SCHEMA,
        "probeId": str(value.get("probeId") or "")[:160],
        "transactionId": str(value.get("transactionId") or transaction_id),
        "checkedCount": len(results),
        "existingCount": existing_count,
        "missingCount": len(results) - existing_count,
        "noteIds": [item["noteId"] for item in results],
        "results": results,
        "updatedAt": str(value.get("updatedAt") or now_timestamp()),
    }


def clean_source_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    page_value = value.get("page")
    try:
        page = int(page_value) if page_value not in {None, ""} else None
    except Exception:
        page = None
    return {
        "page": page,
        "quote": str(value.get("quote") or "")[:900],
        "documentTitle": str(value.get("documentTitle") or "")[:260],
        "path": str(value.get("path") or "")[:900],
        "noteId": str(value.get("noteId") or "")[:260],
        "parentNoteId": str(value.get("parentNoteId") or "")[:260],
        "nodePath": str(value.get("nodePath") or value.get("pathInTree") or "")[:260],
    }


def clean_object_ref(extra: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = fallback if isinstance(fallback, dict) else {}
    embedded = extra.get("objectRef") if isinstance(extra.get("objectRef"), dict) else {}
    source_ref = (
        clean_source_ref(extra.get("mnObjectSourceRef"))
        or clean_source_ref(embedded.get("sourceRef"))
        or clean_source_ref(fallback.get("sourceRef"))
    )
    return {
        "objectId": str(extra.get("mnObjectId") or embedded.get("objectId") or fallback.get("objectId") or ""),
        "kind": str(extra.get("mnObjectKind") or embedded.get("kind") or fallback.get("kind") or ""),
        "title": str(extra.get("mnObjectTitle") or embedded.get("title") or fallback.get("title") or ""),
        "sourceRef": source_ref,
    }


def transaction_available_actions(transaction: dict[str, Any]) -> list[str]:
    status = str(transaction.get("status") or "")
    created_note_ids = unique_strings(transaction.get("createdNoteIds"))
    actions: list[str] = []
    if status in {"ready", "pending_confirmation"}:
        actions.extend(["retain", "rollback"])
    elif status == "delete_pending_confirmation":
        actions.extend(["confirm_delete", "dismiss"])
    elif status == "apply_failed" and created_note_ids:
        actions.append("rollback")
    actions.extend(["verify", "evidence"])
    out: list[str] = []
    seen: set[str] = set()
    for action in actions:
        if action and action not in seen:
            seen.add(action)
            out.append(action)
    return out


def transaction_requires_confirmation(transaction: dict[str, Any]) -> bool:
    return str(transaction.get("status") or "") in {
        "ready",
        "pending_confirmation",
        "delete_pending_confirmation",
    }


def base_transaction(transaction_id: str, record: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    ts = str(record.get("ts") or now_timestamp())
    return {
        "transactionId": transaction_id,
        "draftId": str(extra.get("draftId") or extra.get("id") or ""),
        "topicid": str(record.get("topicid") or extra.get("topicid") or ""),
        "bookmd5": str(record.get("bookmd5") or extra.get("bookmd5") or ""),
        "docmd5": str(record.get("docmd5") or extra.get("docmd5") or ""),
        "status": "started",
        "createdNoteIds": [],
        "createdCount": 0,
        "cardCount": int(extra.get("cards") or extra.get("card_count") or 0),
        "hasMindmap": bool(extra.get("hasMindmap") or extra.get("has_mindmap")),
        "mindmapTitle": str(extra.get("mindmap_title") or ""),
        "writeTarget": str(extra.get("write_target") or ""),
        "objectRef": clean_object_ref(extra),
        "deletedCount": 0,
        "failedCount": 0,
        "failures": [],
        "undoRollback": {},
        "message": str(extra.get("message") or ""),
        "createdAt": ts,
        "updatedAt": ts,
        "events": [],
    }


def append_event_summary(transaction: dict[str, Any], record: dict[str, Any]) -> None:
    events = transaction.get("events")
    if not isinstance(events, list):
        events = []
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    events.append(
        {
            "event": str(record.get("event") or ""),
            "ts": str(record.get("ts") or now_timestamp()),
            "nativeAction": str(extra.get("nativeAction") or ""),
            "queueId": str(extra.get("queueId") or extra.get("queue_id") or ""),
            "source": str(record.get("source") or extra.get("source") or ""),
            "operationCount": safe_int(extra.get("operationCount"), 0),
        }
    )
    transaction["events"] = events[-50:]


def apply_native_event(record: dict[str, Any]) -> dict[str, Any]:
    event_name = str(record.get("event") or "")
    if event_name not in _TRACKED_EVENTS:
        return {"ok": False, "reason": "ignored-event"}
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    transaction_id = safe_transaction_id(extra.get("transactionId") or extra.get("id"))
    if not transaction_id:
        return {"ok": False, "reason": "missing-transaction-id"}

    path = transaction_path(transaction_id)
    transaction = read_json(path, {})
    if not transaction:
        transaction = base_transaction(transaction_id, record, extra)

    transaction["transactionId"] = transaction_id
    transaction["draftId"] = str(extra.get("draftId") or extra.get("id") or transaction.get("draftId") or "")
    transaction["topicid"] = str(record.get("topicid") or extra.get("topicid") or transaction.get("topicid") or "")
    transaction["bookmd5"] = str(record.get("bookmd5") or extra.get("bookmd5") or transaction.get("bookmd5") or "")
    transaction["docmd5"] = str(record.get("docmd5") or extra.get("docmd5") or transaction.get("docmd5") or "")
    transaction["updatedAt"] = str(record.get("ts") or now_timestamp())
    object_ref = clean_object_ref(extra, transaction.get("objectRef") if isinstance(transaction.get("objectRef"), dict) else {})
    if object_ref.get("objectId") or object_ref.get("kind") or object_ref.get("title") or object_ref.get("sourceRef"):
        transaction["objectRef"] = object_ref

    if event_name == "aiEditTransactionStarted":
        transaction["status"] = "started"
        transaction["cardCount"] = int(extra.get("cards") or extra.get("card_count") or transaction.get("cardCount") or 0)
        transaction["hasMindmap"] = bool(extra.get("hasMindmap") or extra.get("has_mindmap") or transaction.get("hasMindmap"))
    elif event_name == "mindmapDiffApplyRequested":
        plan = extra.get("mindmapDiffOperationPlan") if isinstance(extra.get("mindmapDiffOperationPlan"), dict) else {}
        transaction["status"] = "started"
        transaction["hasMindmap"] = True
        transaction["mindmapTitle"] = str(extra.get("mindmapTitle") or transaction.get("mindmapTitle") or "脑图 Diff 局部应用")
        if plan:
            transaction["mindmapDiffOperationPlan"] = plan
        transaction["message"] = str(extra.get("message") or "脑图 Diff 局部应用已请求。")
    elif event_name == "aiEditOperationReady":
        created_note_ids = unique_strings(extra.get("createdNoteIds"))
        transaction["status"] = "ready"
        transaction["createdNoteIds"] = created_note_ids
        transaction["createdCount"] = int(extra.get("createdCount") or len(created_note_ids))
        transaction["cardCount"] = int(extra.get("card_count") or extra.get("cards") or transaction.get("cardCount") or 0)
        transaction["hasMindmap"] = bool(extra.get("has_mindmap") or extra.get("hasMindmap") or transaction.get("hasMindmap"))
        transaction["mindmapTitle"] = str(extra.get("mindmap_title") or transaction.get("mindmapTitle") or "")
        transaction["writeTarget"] = str(extra.get("write_target") or transaction.get("writeTarget") or "")
    elif event_name == "aiEditTransactionAccepted":
        transaction["status"] = "accepted"
        transaction["message"] = str(extra.get("message") or transaction.get("message") or "")
    elif event_name == "aiEditTransactionRejected":
        ok = bool(extra.get("ok"))
        failed_count = int(extra.get("failed") or 0)
        transaction["status"] = "rolled_back" if ok and failed_count == 0 else "rollback_failed"
        transaction["deletedCount"] = int(extra.get("deleted") or 0)
        transaction["failedCount"] = failed_count
        transaction["failures"] = clean_failures(extra.get("failures"))
        transaction["undoRollback"] = clean_undo_rollback(extra.get("undoRollback"))
        transaction["message"] = str(extra.get("message") or transaction.get("message") or "")
    elif event_name == "mindmapDiffApplyFinished":
        created_note_ids = unique_strings(extra.get("createdNoteIds"))
        applied_operations = extra.get("appliedOperations") if isinstance(extra.get("appliedOperations"), list) else []
        applied_note_ids = unique_strings(
            [item.get("noteId") for item in applied_operations if isinstance(item, dict)]
        )
        failed_count = int(extra.get("failedCount") or 0)
        verification = extra.get("verification") if isinstance(extra.get("verification"), dict) else {}
        plan = (
            extra.get("mindmapDiffOperationPlan")
            if isinstance(extra.get("mindmapDiffOperationPlan"), dict)
            else transaction.get("mindmapDiffOperationPlan") if isinstance(transaction.get("mindmapDiffOperationPlan"), dict) else {}
        )
        verification_status = str(verification.get("status") or "")
        transaction["status"] = "pending_confirmation" if failed_count == 0 and verification_status != "block" else "apply_failed"
        transaction["hasMindmap"] = True
        transaction["createdNoteIds"] = created_note_ids
        transaction["appliedNoteIds"] = applied_note_ids
        transaction["createdCount"] = int(extra.get("createdCount") or len(created_note_ids))
        transaction["appliedCount"] = int(extra.get("appliedCount") or len(applied_note_ids))
        transaction["failedCount"] = failed_count
        transaction["failures"] = clean_failures(extra.get("failures"))
        transaction["mindmapTitle"] = str(extra.get("mindmapTitle") or transaction.get("mindmapTitle") or "脑图 Diff 局部应用")
        if plan:
            transaction["mindmapDiffOperationPlan"] = plan
        transaction["mindmapDiffApply"] = {
            "verification": verification,
            "appliedOperations": applied_operations,
        }
        transaction["message"] = str(verification.get("summary") or extra.get("message") or "脑图 Diff 局部应用已完成。")
    elif event_name == "mindmapDeleteSuggestionPrepared":
        target_note_ids = unique_strings(extra.get("targetNoteIds"))
        delete_operations = clean_delete_operations(extra.get("deleteOperations"))
        if not target_note_ids:
            target_note_ids = unique_strings([item.get("noteId") for item in delete_operations])
        transaction["status"] = "delete_pending_confirmation"
        transaction["hasMindmap"] = True
        transaction["targetNoteIds"] = target_note_ids
        transaction["deleteSuggestion"] = {
            "targetNoteIds": target_note_ids,
            "deleteOperations": delete_operations,
            "operationCount": int(extra.get("operationCount") or len(delete_operations) or len(target_note_ids)),
        }
        transaction["message"] = str(extra.get("message") or f"删除建议等待确认：{len(target_note_ids)} 个节点。")
    elif event_name == "mindmapDeleteSuggestionConfirmed":
        ok = bool(extra.get("ok"))
        failed_count = int(extra.get("failed") or 0)
        deleted_count = int(extra.get("deleted") or 0)
        transaction["status"] = "delete_confirmed" if ok and failed_count == 0 else "delete_failed"
        transaction["targetNoteIds"] = unique_strings(extra.get("targetNoteIds")) or unique_strings(transaction.get("targetNoteIds"))
        transaction["deletedCount"] = deleted_count
        transaction["failedCount"] = failed_count
        transaction["failures"] = clean_failures(extra.get("failures"))
        transaction["message"] = str(extra.get("message") or ("已删除确认的脑图节点。" if transaction["status"] == "delete_confirmed" else "部分脑图节点删除失败。"))
    elif event_name == "mindmapDeleteSuggestionDismissed":
        transaction["status"] = "delete_dismissed"
        transaction["targetNoteIds"] = unique_strings(extra.get("targetNoteIds")) or unique_strings(transaction.get("targetNoteIds"))
        transaction["message"] = str(extra.get("message") or "已忽略本次脑图删除建议。")
    elif event_name == "mnObjectExistenceProbeFinished":
        probe = clean_object_existence_probe(extra, transaction_id=transaction_id)
        transaction["objectExistenceProbe"] = probe
        transaction["message"] = str(
            extra.get("message")
            or f"MN 对象存在性 probe：检查 {probe.get('checkedCount') or 0} 个，仍存在 {probe.get('existingCount') or 0} 个。"
        )

    transaction["requiresConfirmation"] = transaction_requires_confirmation(transaction)
    transaction["availableActions"] = transaction_available_actions(transaction)
    append_event_summary(transaction, record)
    write_json(path, transaction)
    return {"ok": True, "transaction": transaction}


def transaction_summary(transaction: dict[str, Any]) -> dict[str, Any]:
    created_note_ids = unique_strings(transaction.get("createdNoteIds"))
    applied_note_ids = unique_strings(transaction.get("appliedNoteIds"))
    object_ref = clean_object_ref({}, transaction.get("objectRef") if isinstance(transaction.get("objectRef"), dict) else {})
    return {
        "transactionId": str(transaction.get("transactionId") or ""),
        "draftId": str(transaction.get("draftId") or ""),
        "topicid": str(transaction.get("topicid") or ""),
        "bookmd5": str(transaction.get("bookmd5") or ""),
        "docmd5": str(transaction.get("docmd5") or ""),
        "status": str(transaction.get("status") or ""),
        "createdCount": int(transaction.get("createdCount") or len(created_note_ids)),
        "createdNoteIds": created_note_ids,
        "appliedCount": int(transaction.get("appliedCount") or len(applied_note_ids)),
        "appliedNoteIds": applied_note_ids,
        "deletedCount": int(transaction.get("deletedCount") or 0),
        "failedCount": int(transaction.get("failedCount") or 0),
        "cardCount": int(transaction.get("cardCount") or 0),
        "hasMindmap": bool(transaction.get("hasMindmap")),
        "mindmapTitle": str(transaction.get("mindmapTitle") or ""),
        "writeTarget": str(transaction.get("writeTarget") or ""),
        "updatedAt": str(transaction.get("updatedAt") or ""),
        "message": str(transaction.get("message") or ""),
        "objectRef": object_ref,
        "mindmapDiffApply": transaction.get("mindmapDiffApply") if isinstance(transaction.get("mindmapDiffApply"), dict) else {},
        "deleteSuggestion": transaction.get("deleteSuggestion") if isinstance(transaction.get("deleteSuggestion"), dict) else {},
        "targetNoteIds": unique_strings(transaction.get("targetNoteIds")),
        "requiresConfirmation": transaction_requires_confirmation(transaction),
        "availableActions": transaction_available_actions(transaction),
    }


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def rollback_remaining_note_ids(
    created_note_ids: list[str],
    deleted_count: int,
    failed_count: int,
    failures: list[dict[str, Any]],
) -> list[str]:
    expected_remaining = max(max(len(created_note_ids), 0) - max(deleted_count, 0), max(failed_count, 0))
    remaining: list[str] = []
    seen: set[str] = set()
    for failure in failures:
        note_id = str(failure.get("noteId") or "").strip()
        if note_id and note_id not in seen:
            seen.add(note_id)
            remaining.append(note_id)
    for note_id in created_note_ids[max(deleted_count, 0) :]:
        if note_id and note_id not in seen:
            seen.add(note_id)
            remaining.append(note_id)
        if len(remaining) >= expected_remaining:
            break
    return remaining


def residual_proof_source_fields(
    *,
    created_note_ids: list[str],
    target_note_ids: list[str],
    deleted_count: int,
    failed_count: int,
    failures: list[dict[str, Any]],
    status: str,
    object_existence_probe: dict[str, Any] | None = None,
) -> list[str]:
    fields: list[str] = []
    if status.startswith("delete") and target_note_ids:
        fields.append("targetNoteIds")
    if created_note_ids:
        fields.append("createdNoteIds")
    if status in {"rolled_back", "rollback_failed", "delete_confirmed", "delete_failed"} or deleted_count:
        fields.append("deletedCount")
    if status in {"rolled_back", "rollback_failed", "delete_confirmed", "delete_failed"} or failed_count:
        fields.append("failedCount")
    if failures:
        fields.append("failures")
    if isinstance(object_existence_probe, dict) and object_existence_probe.get("results"):
        fields.append("objectExistenceProbe")
    return fields


def residual_expected_state(status: str, delete_mode: bool) -> str:
    if delete_mode:
        if status == "delete_pending_confirmation":
            return "pending_delete_confirmation"
        if status == "delete_dismissed":
            return "retained_after_dismiss"
        return "deleted_after_delete_confirmation"
    if status == "accepted":
        return "retained_after_accept"
    if status in {"rolled_back", "rollback_failed"}:
        return "deleted_after_rollback"
    if status in {"ready", "started", "pending_confirmation", "apply_failed"}:
        return "pending_user_decision"
    return "unknown"


def residual_actual_state_for_note(
    *,
    note_id: str,
    index: int,
    status: str,
    delete_mode: bool,
    deleted_count: int,
    rollback_complete: bool,
    remaining_note_ids: list[str],
    failures_by_note: dict[str, dict[str, Any]],
    probe_by_note: dict[str, dict[str, Any]],
) -> tuple[str, bool, str]:
    if note_id in probe_by_note:
        probe = probe_by_note[note_id]
        exists = bool(probe.get("exists"))
        if exists:
            if status in {"accepted", "ready", "started", "pending_confirmation", "apply_failed", "delete_pending_confirmation"}:
                return "exists_confirmed", False, "native_object_probe"
            return "exists_confirmed", True, "native_object_probe"
        return "missing_confirmed", False, "native_object_probe"
    if delete_mode and status == "delete_pending_confirmation":
        return "existing_pending_confirmation", False, "transaction_state"
    if delete_mode and status == "delete_dismissed":
        return "retained_by_user", False, "transaction_state"
    if status == "accepted":
        return "retained_by_user", False, "transaction_state"
    if note_id in failures_by_note:
        return "remaining_reported", True, "native_failure"
    if note_id in set(remaining_note_ids):
        return "remaining_reported", True, "remaining_inferred"
    if status in {"rolled_back", "rollback_failed", "delete_confirmed", "delete_failed"}:
        if rollback_complete or index < max(deleted_count, 0):
            return "deleted_reported", False, "count_inferred"
        return "unknown_after_native_event", True, "count_inferred"
    if status in {"ready", "started", "pending_confirmation", "apply_failed"}:
        return "created_pending_user_decision", False, "transaction_state"
    return "unknown", False, "transaction_state"


def residual_proof(
    *,
    transaction: dict[str, Any],
    report_status: str,
    created_note_ids: list[str],
    created_count: int,
    deleted_count: int,
    failed_count: int,
    remaining_note_ids: list[str],
    failures: list[dict[str, Any]],
    rollback_complete: bool,
    target_note_ids: list[str],
    summary: str,
    object_existence_probe: dict[str, Any] | None = None,
) -> dict[str, Any]:
    status = str(transaction.get("status") or "")
    transaction_id = str(transaction.get("transactionId") or "")
    delete_mode = status.startswith("delete_")
    note_ids = target_note_ids if delete_mode and target_note_ids else created_note_ids
    expected_state = residual_expected_state(status, delete_mode)
    object_type = "mindmap_node" if bool(transaction.get("hasMindmap")) or delete_mode else "note"
    failures_by_note = {
        str(item.get("noteId") or ""): item
        for item in failures
        if isinstance(item, dict) and str(item.get("noteId") or "")
    }
    probe = object_existence_probe if isinstance(object_existence_probe, dict) else {}
    probe_results = probe.get("results") if isinstance(probe.get("results"), list) else []
    probe_by_note = {
        str(item.get("noteId") or ""): item
        for item in probe_results
        if isinstance(item, dict) and str(item.get("noteId") or "")
    }
    objects: list[dict[str, Any]] = []
    for index, note_id in enumerate(note_ids):
        actual_state, residual, verification_level = residual_actual_state_for_note(
            note_id=note_id,
            index=index,
            status=status,
            delete_mode=delete_mode,
            deleted_count=deleted_count,
            rollback_complete=rollback_complete,
            remaining_note_ids=remaining_note_ids,
            failures_by_note=failures_by_note,
            probe_by_note=probe_by_note,
        )
        failure = failures_by_note.get(note_id, {})
        probe_item = probe_by_note.get(note_id, {})
        objects.append(
            {
                "objectId": f"mnobj:note:{note_id}",
                "objectType": object_type,
                "noteId": note_id,
                "expectedState": expected_state,
                "actualState": actual_state,
                "residual": bool(residual),
                "verificationLevel": verification_level,
                "evidence": {
                    "source": "mn_object_existence_probe" if probe_item else "ai_edit_transaction_native_event",
                    "transactionStatus": status,
                    "deletedCount": deleted_count,
                    "failedCount": failed_count,
                    "failureReason": str(failure.get("reason") or ""),
                    "failureMethod": str(failure.get("method") or ""),
                    "probeId": str(probe.get("probeId") or ""),
                    "probeExists": bool(probe_item.get("exists")) if probe_item else None,
                    "probeTitle": str(probe_item.get("title") or ""),
                },
            }
        )
    residual_count = sum(1 for item in objects if item.get("residual"))
    source_fields = residual_proof_source_fields(
        created_note_ids=created_note_ids,
        target_note_ids=target_note_ids,
        deleted_count=deleted_count,
        failed_count=failed_count,
        failures=failures,
        status=status,
        object_existence_probe=probe,
    )
    if residual_count:
        proof_summary = f"逐对象残留证明：{residual_count}/{len(objects)} 个对象仍可能残留。"
    elif objects:
        proof_summary = "逐对象残留证明：未发现异常残留；逐对象状态来自事务事件和删除计数。"
    else:
        proof_summary = "逐对象残留证明：本事务没有可验证的 noteId。"
    return {
        "schema": RESIDUAL_PROOF_SCHEMA,
        "transactionId": transaction_id,
        "status": report_status,
        "summary": proof_summary,
        "verificationSummary": summary,
        "createdCount": created_count,
        "deletedCount": deleted_count,
        "failedCount": failed_count,
        "remainingCount": residual_count,
        "createdNoteIds": created_note_ids,
        "remainingNoteIds": [item["noteId"] for item in objects if item.get("residual")],
        "targetNoteIds": target_note_ids,
        "sourceFields": source_fields,
        "objects": objects,
    }


def verification_report(transaction: dict[str, Any]) -> dict[str, Any]:
    created_note_ids = unique_strings(transaction.get("createdNoteIds"))
    created_count = safe_int(transaction.get("createdCount"), len(created_note_ids))
    if created_count < len(created_note_ids):
        created_count = len(created_note_ids)
    deleted_count = safe_int(transaction.get("deletedCount"), 0)
    failed_count = safe_int(transaction.get("failedCount"), 0)
    failures = clean_failures(transaction.get("failures"))
    status = str(transaction.get("status") or "")
    transaction_id = str(transaction.get("transactionId") or "")
    object_ref = clean_object_ref({}, transaction.get("objectRef") if isinstance(transaction.get("objectRef"), dict) else {})
    mindmap_diff_apply = transaction.get("mindmapDiffApply") if isinstance(transaction.get("mindmapDiffApply"), dict) else {}
    mindmap_verification = mindmap_diff_apply.get("verification") if isinstance(mindmap_diff_apply.get("verification"), dict) else {}
    delete_suggestion = transaction.get("deleteSuggestion") if isinstance(transaction.get("deleteSuggestion"), dict) else {}
    target_note_ids = unique_strings(transaction.get("targetNoteIds")) or unique_strings(delete_suggestion.get("targetNoteIds"))
    object_existence_probe = clean_object_existence_probe(
        transaction.get("objectExistenceProbe"),
        transaction_id=transaction_id,
    )
    probe_results = (
        object_existence_probe.get("results")
        if isinstance(object_existence_probe.get("results"), list)
        else []
    )
    probe_applies_to_deletion = bool(probe_results) and status in {
        "rolled_back",
        "rollback_failed",
        "delete_confirmed",
        "delete_failed",
    }
    probe_remaining_note_ids = [
        str(item.get("noteId") or "")
        for item in probe_results
        if isinstance(item, dict) and item.get("exists") and str(item.get("noteId") or "")
    ]

    remaining_note_ids: list[str] = []
    rollback_complete = False
    accepted = status == "accepted"
    report_status = "pending"
    next_actions: list[dict[str, Any]] = []

    requires_confirmation = transaction_requires_confirmation(transaction)

    if status == "delete_pending_confirmation":
        report_status = "pending"
    elif status == "delete_confirmed":
        report_status = "pass" if failed_count == 0 else "block"
    elif status == "delete_failed":
        report_status = "block"
    elif status == "delete_dismissed":
        report_status = "pass"
    elif status == "rolled_back":
        rollback_complete = failed_count == 0 and deleted_count >= created_count
        report_status = "pass" if rollback_complete else "block"
    elif status == "rollback_failed":
        remaining_note_ids = rollback_remaining_note_ids(created_note_ids, deleted_count, failed_count, failures)
        report_status = "block"
    elif accepted:
        report_status = "pass"
    elif mindmap_diff_apply:
        report_status = "pass" if str(mindmap_verification.get("status") or "") != "block" and failed_count == 0 else "block"
    elif status in {"ready", "started"}:
        report_status = "pending"
    else:
        report_status = "block" if status else "pending"

    if report_status == "block" and not remaining_note_ids:
        remaining_note_ids = rollback_remaining_note_ids(created_note_ids, deleted_count, failed_count, failures)

    if probe_applies_to_deletion:
        remaining_note_ids = probe_remaining_note_ids
        if remaining_note_ids:
            report_status = "block"
            rollback_complete = False
        else:
            report_status = "pass"
            rollback_complete = status in {"rolled_back", "rollback_failed"}

    if probe_applies_to_deletion:
        remaining_count = len(remaining_note_ids)
        checked_count = safe_int(object_existence_probe.get("checkedCount"), len(probe_results))
        if remaining_note_ids:
            id_text = "、".join(remaining_note_ids[:8])
            summary = f"MN 对象存在性验证 BLOCK：probe 已检查 {checked_count} 个对象，仍存在 {remaining_count} 个：{id_text}。"
            next_actions.append(
                {
                    "id": "manual_cleanup",
                    "label": "手动清理残留卡片",
                    "reason": "MN 原生对象 probe 确认仍有新增对象存在。",
                }
            )
        else:
            summary = f"MN 对象存在性验证 PASS：probe 已确认 {checked_count} 个对象均不存在，无残留。"
    elif status == "delete_pending_confirmation":
        remaining_count = len(target_note_ids)
        summary = f"删除建议 PENDING：{remaining_count} 个脑图节点等待二次确认。点删除才会真正删除；点忽略不会改动原脑图。"
    elif status == "delete_confirmed":
        remaining_count = max(failed_count, 0)
        summary = f"删除建议 PASS：已删除 {deleted_count}/{max(len(target_note_ids), deleted_count)} 个确认节点。"
    elif status == "delete_failed":
        remaining_count = max(failed_count, len(target_note_ids) - deleted_count, 0)
        id_text = "、".join(target_note_ids[:8]) if target_note_ids else "未知节点"
        summary = f"删除建议 BLOCK：仍可能残留 {remaining_count} 个节点：{id_text}。"
    elif status == "delete_dismissed":
        remaining_count = len(target_note_ids)
        summary = "删除建议已忽略：没有删除任何现有脑图节点。"
    elif mindmap_diff_apply and requires_confirmation:
        remaining_count = max(created_count - deleted_count, 0)
        summary = (
            str(mindmap_verification.get("summary") or transaction.get("message") or "脑图 Diff 验证：无摘要。")
            + f" 等待确认：点保留确认本次新增 {created_count} 个对象，或点回滚删除本次新增节点。"
        )
    elif mindmap_diff_apply and not accepted:
        remaining_count = 0 if report_status == "pass" else max(failed_count, 1)
        summary = str(mindmap_verification.get("summary") or transaction.get("message") or "脑图 Diff 验证：无摘要。")
    elif rollback_complete:
        remaining_count = 0
        summary = f"回滚验证 PASS：已删除本次新增 {deleted_count}/{created_count} 个对象，无残留。"
    elif accepted:
        remaining_count = created_count
        summary = f"保留验证 PASS：用户已接受，本次新增 {created_count} 个对象保留。"
    elif report_status == "pending":
        remaining_count = max(created_count - deleted_count, 0)
        summary = "回滚验证 PENDING：AI 编辑事务尚未接受或拒绝，等待用户确认。"
    else:
        remaining_count = max(len(remaining_note_ids), failed_count, created_count - deleted_count, 0)
        id_text = "、".join(remaining_note_ids[:8]) if remaining_note_ids else "未知对象"
        failure_text = ""
        if failures:
            first_failure = failures[0]
            failure_text = f"；首个失败：{first_failure.get('noteId') or '未知'} {first_failure.get('reason') or ''}".rstrip()
        summary = f"回滚验证 BLOCK：仍可能残留 {remaining_count} 个对象：{id_text}{failure_text}。"
        next_actions.append(
            {
                "id": "manual_cleanup",
                "label": "手动清理残留卡片",
                "reason": "自动回滚未确认删除全部新增对象。",
            }
        )

    if not probe_results and status in {"rolled_back", "rollback_failed", "delete_confirmed", "delete_failed"}:
        probe_note_ids = created_note_ids if status in {"rolled_back", "rollback_failed"} else target_note_ids
        if probe_note_ids:
            next_actions.insert(
                0,
                {
                    "id": "request_object_existence_probe",
                    "label": "检查真实 MN 对象",
                    "action": "request_mn_object_existence_probe",
                    "reason": "当前残留判断仍来自删除计数或失败事件，建议让 MN4 原生侧按 noteId 复查真实对象是否仍存在。",
                    "transactionId": transaction_id,
                    "noteIds": probe_note_ids,
                },
            )

    proof = residual_proof(
        transaction=transaction,
        report_status=report_status,
        created_note_ids=created_note_ids,
        created_count=created_count,
        deleted_count=deleted_count,
        failed_count=failed_count,
        remaining_note_ids=remaining_note_ids,
        failures=failures,
        rollback_complete=rollback_complete,
        target_note_ids=target_note_ids,
        summary=summary,
        object_existence_probe=object_existence_probe,
    )

    return {
        "schema": VERIFICATION_SCHEMA,
        "transactionId": transaction_id,
        "status": report_status,
        "transactionStatus": status,
        "createdCount": created_count,
        "createdNoteIds": created_note_ids,
        "deletedCount": deleted_count,
        "failedCount": failed_count,
        "remainingCount": remaining_count,
        "remainingNoteIds": remaining_note_ids,
        "targetNoteIds": target_note_ids,
        "rollbackComplete": rollback_complete,
        "accepted": accepted,
        "failures": failures,
        "undoRollback": clean_undo_rollback(transaction.get("undoRollback")),
        "objectRef": object_ref,
        "mindmapDiffApply": mindmap_diff_apply,
        "deleteSuggestion": delete_suggestion,
        "objectExistenceProbe": object_existence_probe,
        "requiresConfirmation": requires_confirmation,
        "availableActions": transaction_available_actions(transaction),
        "residualProof": proof,
        "summary": summary,
        "nextActions": next_actions,
    }


def latest_summary(topicid: str = "", bookmd5: str = "", limit: int = 8) -> dict[str, Any]:
    topicid = str(topicid or "")
    bookmd5 = str(bookmd5 or "")
    items: list[dict[str, Any]] = []
    if not _TRANSACTION_DIR.exists():
        return {"count": 0, "items": []}
    for path in sorted(_TRANSACTION_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        tx = read_json(path, {})
        if not tx:
            continue
        if topicid and str(tx.get("topicid") or "") not in {"", topicid}:
            continue
        if bookmd5 and str(tx.get("bookmd5") or "") not in {"", bookmd5}:
            continue
        items.append(transaction_summary(tx))
        if len(items) >= max(1, int(limit or 8)):
            break
    return {"count": len(items), "items": items}


def latest_status(topicid: str = "", bookmd5: str = "") -> dict[str, Any]:
    topicid = str(topicid or "")
    bookmd5 = str(bookmd5 or "")
    if not _TRANSACTION_DIR.exists():
        return {
            "schema": TRANSACTION_STATUS_SCHEMA,
            "available": False,
            "summary": "事务中心：暂无 AI 编辑事务。",
            "latest": {},
            "verification": {},
        }
    for path in sorted(_TRANSACTION_DIR.glob("*.json"), key=lambda item: item.stat().st_mtime, reverse=True):
        tx = read_json(path, {})
        if not tx:
            continue
        if topicid and str(tx.get("topicid") or "") not in {"", topicid}:
            continue
        if bookmd5 and str(tx.get("bookmd5") or "") not in {"", bookmd5}:
            continue
        latest = transaction_summary(tx)
        verification = verification_report(tx)
        return {
            "schema": TRANSACTION_STATUS_SCHEMA,
            "available": True,
            "summary": verification.get("summary") or "事务中心：已读取最近 AI 编辑事务。",
            "latest": latest,
            "verification": verification,
        }
    return {
        "schema": TRANSACTION_STATUS_SCHEMA,
        "available": False,
        "summary": "事务中心：当前范围暂无 AI 编辑事务。",
        "latest": {},
        "verification": {},
    }
