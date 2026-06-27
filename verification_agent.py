from __future__ import annotations

import time
from typing import Any


VERIFICATION_REPORT_SCHEMA = "codex.mn.verificationReport.v1"


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and text not in result:
            result.append(text)
    return result


def _report(
    *,
    subject_type: str,
    status: str,
    problems: list[str] | None = None,
    scope: str = "current_document",
    **extra: Any,
) -> dict[str, Any]:
    payload = {
        "schema": VERIFICATION_REPORT_SCHEMA,
        "subjectType": subject_type,
        "scope": scope,
        "status": status if status in {"PASS", "FAIL", "UNKNOWN"} else "UNKNOWN",
        "problems": problems or [],
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    payload.update(extra)
    return payload


def _probe_objects(native_probe: dict[str, Any]) -> list[dict[str, Any]]:
    objects = native_probe.get("objects") if isinstance(native_probe, dict) else None
    if not isinstance(objects, list):
        return []
    return [item for item in objects if isinstance(item, dict)]


def _exists(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "present", "exists", "found"}


def verify_transaction(transaction: dict[str, Any]) -> dict[str, Any]:
    transaction = transaction if isinstance(transaction, dict) else {}
    expected_note_ids = _clean_list(transaction.get("createdNoteIds") or transaction.get("noteIds"))
    expected_card_ids = _clean_list(transaction.get("createdCardIds") or transaction.get("cardIds"))
    native_probe = transaction.get("nativeProbe") if isinstance(transaction.get("nativeProbe"), dict) else {}
    objects = _probe_objects(native_probe)
    if (expected_note_ids or expected_card_ids) and not objects:
        return _report(
            subject_type="transaction",
            status="UNKNOWN",
            problems=["native_probe_missing"],
            expectedNoteIds=expected_note_ids,
            expectedCardIds=expected_card_ids,
            missingNoteIds=[],
            missingCardIds=[],
            presentNoteIds=[],
            presentCardIds=[],
        )

    note_state = {str(item.get("noteId") or ""): _exists(item.get("exists")) for item in objects if item.get("noteId")}
    card_state = {str(item.get("cardId") or ""): _exists(item.get("exists")) for item in objects if item.get("cardId")}
    missing_notes = [note_id for note_id in expected_note_ids if not note_state.get(note_id)]
    missing_cards = [card_id for card_id in expected_card_ids if not card_state.get(card_id)]
    present_notes = [note_id for note_id in expected_note_ids if note_state.get(note_id)]
    present_cards = [card_id for card_id in expected_card_ids if card_state.get(card_id)]
    problems = []
    if missing_notes:
        problems.append("missing_notes")
    if missing_cards:
        problems.append("missing_cards")
    if not expected_note_ids and not expected_card_ids:
        problems.append("no_expected_objects")
    status = "FAIL" if missing_notes or missing_cards else ("UNKNOWN" if problems else "PASS")
    return _report(
        subject_type="transaction",
        status=status,
        problems=problems,
        expectedNoteIds=expected_note_ids,
        expectedCardIds=expected_card_ids,
        missingNoteIds=missing_notes,
        missingCardIds=missing_cards,
        presentNoteIds=present_notes,
        presentCardIds=present_cards,
    )


def verify_source_registry(registry: dict[str, Any]) -> dict[str, Any]:
    registry = registry if isinstance(registry, dict) else {}
    sources = registry.get("sources") if isinstance(registry.get("sources"), list) else []
    readable = [item for item in sources if isinstance(item, dict) and bool(item.get("readable"))]
    if readable:
        return _report(
            subject_type="source_registry",
            status="PASS",
            readableSourceIds=[str(item.get("sourceId") or "") for item in readable],
            sourceCount=len(sources),
        )
    if sources:
        return _report(
            subject_type="source_registry",
            status="FAIL",
            problems=["no_readable_source"],
            sourceCount=len(sources),
        )
    return _report(subject_type="source_registry", status="UNKNOWN", problems=["no_sources"], sourceCount=0)


def verify_workflow_run(run: dict[str, Any]) -> dict[str, Any]:
    run = run if isinstance(run, dict) else {}
    status = str(run.get("status") or "").lower()
    steps = run.get("steps") if isinstance(run.get("steps"), list) else []
    failed_steps = [
        str(item.get("id") or item.get("stepId") or index)
        for index, item in enumerate(steps)
        if isinstance(item, dict) and str(item.get("status") or "").lower() in {"failed", "error", "cancelled"}
    ]
    if failed_steps or status in {"failed", "error", "cancelled"}:
        return _report(
            subject_type="workflow_run",
            status="FAIL",
            problems=["workflow_failed"],
            failedStepIds=failed_steps,
        )
    if status in {"completed", "done", "accepted"}:
        return _report(subject_type="workflow_run", status="PASS", failedStepIds=[])
    return _report(subject_type="workflow_run", status="UNKNOWN", problems=["workflow_not_terminal"])


def verify_skill_run(run: dict[str, Any]) -> dict[str, Any]:
    run = run if isinstance(run, dict) else {}
    status = str(run.get("status") or "").lower()
    acceptance = run.get("acceptance") if isinstance(run.get("acceptance"), dict) else {}
    acceptance_status = str(acceptance.get("status") or "").lower()
    if status in {"failed", "error"} or acceptance_status in {"rejected", "failed", "fail"}:
        return _report(subject_type="skill_run", status="FAIL", problems=["skill_run_failed"])
    if status in {"completed", "done"} and acceptance_status in {"accepted", "pass", "passed"}:
        return _report(subject_type="skill_run", status="PASS")
    return _report(subject_type="skill_run", status="UNKNOWN", problems=["skill_run_not_accepted"])
