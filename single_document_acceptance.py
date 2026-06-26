#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
EVENTS_PATH = ROOT / "events.jsonl"
DEFAULT_ACTION_RESULTS_PATH = ROOT / "release/evidence/action-results.jsonl"
SCHEMA = "codex-companion-single-document-acceptance-v1"
NATIVE_HIGHLIGHT_SCHEMA = "codex-companion-native-highlight-v1"
CURRENT_PLUGIN_VERSION = "0.4.37"
NATIVE_HIGHLIGHT_EVIDENCE_PATTERNS = [
    "codex-companion-native-highlight-evidence-current.json",
    "codex-companion-native-highlight-evidence-*.json",
    "CodexCompanion-native-highlight-evidence-*.json",
    "native-highlight-evidence*.json",
]


def json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def read_json(path: Path | str) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def read_jsonl(path: Path | str) -> list[dict[str, Any]]:
    file_path = Path(path).expanduser()
    if not file_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in file_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def item_scope(item: dict[str, Any]) -> tuple[str, str]:
    result = item.get("result") if isinstance(item.get("result"), dict) else {}
    topicid = str(item.get("topicid") or item.get("notebookid") or result.get("topicid") or result.get("notebookid") or "")
    bookmd5 = str(item.get("bookmd5") or item.get("docmd5") or result.get("bookmd5") or result.get("docmd5") or "")
    return topicid, bookmd5


def same_document(item: dict[str, Any], topicid: str, bookmd5: str) -> bool:
    item_topic, item_book = item_scope(item)
    return item_topic == topicid and item_book == bookmd5


def event_extra(item: dict[str, Any]) -> dict[str, Any]:
    extra = item.get("extra")
    return extra if isinstance(extra, dict) else {}


def matching_events(events: list[dict[str, Any]], name: str, topicid: str, bookmd5: str) -> list[dict[str, Any]]:
    return [
        item
        for item in events
        if str(item.get("event") or "") == name and same_document(item, topicid, bookmd5)
    ]


def latest_matching_event(events: list[dict[str, Any]], name: str, topicid: str, bookmd5: str) -> dict[str, Any] | None:
    items = matching_events(events, name, topicid, bookmd5)
    return items[-1] if items else None


def has_event_name_any_scope(events: list[dict[str, Any]], name: str) -> bool:
    return any(str(item.get("event") or "") == name for item in events)


def pass_check(check_id: str, label: str, detail: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": "PASS",
        "detail": detail,
        "evidence": evidence or {},
        "nextActions": [],
    }


def block_check(
    check_id: str,
    label: str,
    detail: str,
    evidence: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": "BLOCK",
        "detail": detail,
        "evidence": evidence or {},
        "nextActions": next_actions or [],
    }


def missing_event_check(check_id: str, label: str, event_name: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    if has_event_name_any_scope(events, event_name):
        detail = f"Found {event_name}, but not for the requested same topic/book document."
    else:
        detail = f"Missing {event_name} event for the requested same topic/book document."
    return block_check(check_id, label, detail, {"event": event_name}, [f"Run {label} again in the same open MarginNote document."])


def ok_result(item: dict[str, Any]) -> bool:
    result = item.get("result") if isinstance(item.get("result"), dict) else item
    return bool(result.get("ok"))


def matching_action_results(
    action_results: list[dict[str, Any]], action: str, topicid: str, bookmd5: str
) -> list[dict[str, Any]]:
    return [
        item
        for item in action_results
        if str(item.get("action") or "") == action and same_document(item, topicid, bookmd5)
    ]


def has_action_any_scope(action_results: list[dict[str, Any]], action: str) -> bool:
    return any(str(item.get("action") or "") == action for item in action_results)


def require_action_result(
    check_id: str,
    label: str,
    action_results: list[dict[str, Any]],
    action: str,
    topicid: str,
    bookmd5: str,
    predicate: Any | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    matches = matching_action_results(action_results, action, topicid, bookmd5)
    for item in matches:
        result = item.get("result") if isinstance(item.get("result"), dict) else item
        if ok_result(item) and (predicate is None or predicate(result)):
            return pass_check(check_id, label, f"{action} result is OK for the same topic/book.", {"action": action})
    if has_action_any_scope(action_results, action):
        detail = f"Found {action} result, but no passing result for the requested same topic/book document."
    else:
        detail = f"Missing passing {action} result for the requested same topic/book document."
    return block_check(check_id, label, detail, {"action": action}, [next_action or f"Run {action} in the same document and save the JSON result."])


def check_runtime_web_controls(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    item = latest_matching_event(events, "webControlsReady", topicid, bookmd5)
    if not item:
        return missing_event_check("runtime_web_controls", "Web controls loaded", "webControlsReady", events)
    extra = event_extra(item)
    controls_text = ",".join(str(x) for x in extra.get("controls", [])) if isinstance(extra.get("controls"), list) else str(extra.get("controls") or "")
    missing = str(extra.get("missing") or "")
    required = [
        "aiChatShell",
        "modeSwitchBar",
        "chatModeButton",
        "agentWorkspaceModeButton",
        "modeIntentLine",
        "workspaceNavigator",
        "workspaceNavigatorSummary",
        "workspaceNavConsoleButton",
        "workspaceNavMindmapStudioButton",
        "workspaceNavCardFactoryButton",
        "workspaceNavLedgerExplorerButton",
        "workspaceNavKnowledgeGraphButton",
        "workspaceNavWorkflowBuilderButton",
        "workspaceNavSkillCenterButton",
        "notebookWorkspacePanel",
        "notebookWorkspaceTitle",
        "notebookWorkspaceSummary",
        "notebookWorkspaceRefreshButton",
        "notebookWorkspaceFocus",
        "notebookWorkspaceObjectCount",
        "notebookWorkspaceMindmap",
        "notebookWorkspaceReview",
        "notebookWorkspaceWorkflow",
        "notebookWorkspaceLedger",
        "notebookWorkspaceActions",
        "notebookWorkspaceStudyProgram",
        "notebookWorkspaceStudyCoverage",
        "notebookWorkspaceStudyGaps",
        "notebookWorkspaceStudyRecommendations",
        "notebookWorkspaceRunbook",
        "notebookWorkspaceRunbookSummary",
        "notebookWorkspaceRunbookAutoButton",
        "notebookWorkspaceRunbookAutoStatus",
        "notebookWorkspaceRunbookContinueButton",
        "notebookWorkspaceRunbookList",
        "commandPanePanel",
        "commandPaneHeader",
        "commandPaneStatus",
        "commandPaneToggleButton",
        "commandPaneBody",
        "commandPaneComposer",
        "workbenchTabs",
        "workbenchTabObject",
        "workbenchTabOperation",
        "workbenchTabKnowledge",
        "workbenchTabWorkflow",
        "objectWorkspacePanel",
        "objectGraphPanel",
        "objectGraphRelationAddButton",
        "objectGraphRelationEditor",
        "objectGraphRelationTargetInput",
        "objectGraphRelationTypeInput",
        "objectGraphRelationLabelInput",
        "objectGraphRelationNoteInput",
        "objectGraphRelationSaveButton",
        "objectGraphRelationCancelButton",
        "objectActivityPanel",
        "operationLedgerPanel",
        "operationWorkspacePanel",
        "operationCompilerPanel",
        "operationCompilerSummary",
        "operationPlanStats",
        "operationCompilerChecks",
        "operationDryRunDetails",
        "operationCompilerRepairActions",
        "operationWorkspaceNextActions",
        "mindmapStudioPanel",
        "mindmapStudioSummary",
        "mindmapStudioCurrentTree",
        "mindmapStudioDiffStage",
        "mindmapStudioApplyStage",
        "mindmapStudioTransactionStage",
        "mindmapStudioReadTreeButton",
        "mindmapStudioPreviewDiffButton",
        "mindmapStudioApplySelectedButton",
        "mindmapStudioVerifyButton",
        "mindmapStudioRollbackButton",
        "mindmapStudioStatusLine",
        "knowledgeWorkspacePanel",
        "workflowWorkspacePanel",
        "agentWorkbenchBar",
        "mindmapDiffWorkbench",
        "aiEditTransactionCenter",
        "aiEditTransactionResidualProof",
        "promptInput",
        "sendButton",
        "stopButton",
        "contextButton",
        "contextScopeAutoButton",
        "contextScopeSelectionButton",
        "contextScopeDocumentButton",
        "closeButton",
        "liveHistory",
        "contextSourceLine",
        "aiReadinessLine",
        "aiReadinessDetail",
        "selectionPreview",
        "statusPill",
        "contextLine",
        "readinessPanel",
        "mnApiStatusLine",
    ]
    absent = [control for control in required if control not in controls_text]
    if missing or absent:
        return block_check(
            "runtime_web_controls",
            "Web controls loaded",
            f"Web controls event is incomplete for this document: missing={missing or absent}.",
            {"event": item, "absent": absent},
            ["Reopen the Codex panel in MarginNote 4 so the latest WebView reports all controls."],
        )
    return pass_check("runtime_web_controls", "Web controls loaded", "Required Web controls were reported.", {"event": item})


def check_native_api_matrix(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    item = latest_matching_event(events, "nativeApiCapabilities", topicid, bookmd5)
    if not item:
        return missing_event_check("native_api_matrix", "MN native API matrix", "nativeApiCapabilities", events)
    matrix = event_extra(item).get("capabilityMatrix")
    if not isinstance(matrix, dict):
        return block_check("native_api_matrix", "MN native API matrix", "nativeApiCapabilities lacks capabilityMatrix.", {"event": item})
    required_ready = ["nativeCards", "nativeMindmap", "undoGroupedWrites", "refreshAfterWrite"]
    blocked = [key for key in required_ready if not bool((matrix.get(key) or {}).get("ready"))]
    available_required = ["nativeHighlightSelection", "annotatedPdfExport"]
    unavailable = [key for key in available_required if not bool((matrix.get(key) or {}).get("available"))]
    if blocked or unavailable:
        return block_check(
            "native_api_matrix",
            "MN native API matrix",
            f"Native matrix is incomplete: blocked={blocked}, unavailable={unavailable}.",
            {"capabilityMatrix": matrix},
            ["Click 刷新MN能力 in the same document and rerun this check."],
        )
    return pass_check("native_api_matrix", "MN native API matrix", "Required native capabilities are present.", {"capabilityMatrix": matrix})


def check_handle_response(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    matches = [
        item
        for item in matching_events(events, "handleResponse", topicid, bookmd5)
        if str(event_extra(item).get("action") or "") in {"chat", "explain_selection"}
    ]
    if matches:
        return pass_check("chat_or_explain", "Chat or explain response", "A chat/explain response was handled in the same document.", {"event": matches[-1]})
    return block_check(
        "chat_or_explain",
        "Chat or explain response",
        "Missing handleResponse for chat or explain_selection in the requested same topic/book document.",
        {"event": "handleResponse"},
        ["Ask or explain a selected span in the same document."],
    )


def check_card_write(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    for item in reversed(matching_events(events, "createCardsFinished", topicid, bookmd5)):
        extra = event_extra(item)
        if int(extra.get("created") or 0) > 0:
            return pass_check("card_write", "Native card write", "MN native cards were created in the same document.", {"event": item})
    return missing_event_check("card_write", "Native card write", "createCardsFinished", events)


def check_mindmap(events: list[dict[str, Any]], topicid: str, bookmd5: str, mode: str, check_id: str, label: str) -> dict[str, Any]:
    for item in reversed(matching_events(events, "createMindmapFinished", topicid, bookmd5)):
        extra = event_extra(item)
        if str(extra.get("mode") or "") == mode and int(extra.get("createdCount") or 0) > 0:
            return pass_check(check_id, label, f"Mindmap mode {mode} wrote nodes in the same document.", {"event": item})
    return block_check(
        check_id,
        label,
        f"Missing createMindmapFinished mode={mode} with created nodes for the requested same topic/book document.",
        {"event": "createMindmapFinished", "mode": mode},
        [f"Run {label} in the same document and write the draft to MarginNote."],
    )


def check_pdf_cache(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    for item in reversed(matching_events(events, "pdfCacheUploadPosted", topicid, bookmd5)):
        extra = event_extra(item)
        if bool(extra.get("ok")) or int(extra.get("size") or 0) > 0:
            return pass_check("pdf_cache", "Current PDF cache", "The current PDF was cached by the MN4 plugin process.", {"event": item})
    return missing_event_check("pdf_cache", "Current PDF cache", "pdfCacheUploadPosted", events)


def native_highlight_scope(data: dict[str, Any]) -> tuple[str, str]:
    scope = data.get("highlightScope") if isinstance(data.get("highlightScope"), dict) else {}
    blob = data.get("highlightBlobCheck") if isinstance(data.get("highlightBlobCheck"), dict) else {}
    topicid = str(data.get("topicid") or scope.get("topicid") or blob.get("topicid") or "")
    bookmd5 = str(data.get("bookmd5") or scope.get("bookmd5") or blob.get("bookmd5") or "")
    if topicid and bookmd5:
        return topicid, bookmd5
    events = data.get("events") if isinstance(data.get("events"), dict) else {}
    for name in ("latestPosted", "latestFailed", "latestArmed"):
        item = events.get(name) if isinstance(events.get(name), dict) else None
        if not item:
            continue
        item_topic, item_book = item_scope(item)
        if item_topic and item_book:
            return item_topic, item_book
    return topicid, bookmd5


def native_highlight_evidence_search_dirs() -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for directory in [
        ROOT / "release/evidence",
        ROOT / "release",
        ROOT,
        Path.cwd(),
        Path.home() / "Desktop",
    ]:
        path = directory.expanduser()
        key = str(path.resolve()) if path.exists() else str(path)
        if key in seen or not path.exists() or not path.is_dir():
            continue
        seen.add(key)
        result.append(path)
    return result


def native_highlight_evidence_candidates() -> list[Path]:
    candidates: list[Path] = []
    seen: set[str] = set()
    for directory in native_highlight_evidence_search_dirs():
        for pattern in NATIVE_HIGHLIGHT_EVIDENCE_PATTERNS:
            for path in directory.glob(pattern):
                key = str(path.resolve()) if path.exists() else str(path)
                if key in seen or not path.is_file():
                    continue
                seen.add(key)
                data = read_json(path)
                if data.get("schema") == NATIVE_HIGHLIGHT_SCHEMA:
                    candidates.append(path)
    return sorted(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)


def enrich_native_highlight_evidence(data: dict[str, Any], path: Path, auto_discovered: bool) -> dict[str, Any]:
    payload = dict(data)
    payload["sourcePath"] = str(path)
    payload["autoDiscovered"] = auto_discovered
    topicid, bookmd5 = native_highlight_scope(payload)
    payload["evidenceScope"] = {"topicid": topicid, "bookmd5": bookmd5}
    return payload


def load_native_highlight_evidence(path: str, topicid: str, bookmd5: str) -> dict[str, Any]:
    if path:
        evidence_path = Path(path).expanduser()
        data = read_json(evidence_path)
        if data:
            return enrich_native_highlight_evidence(data, evidence_path, False)
        return {"sourcePath": str(evidence_path), "autoDiscovered": False, "problems": ["native-highlight-evidence-unreadable"]}
    latest: tuple[Path, dict[str, Any]] | None = None
    for candidate in native_highlight_evidence_candidates():
        data = read_json(candidate)
        if not data:
            continue
        if latest is None:
            latest = (candidate, data)
        evidence_topic, evidence_book = native_highlight_scope(data)
        if evidence_topic == topicid and evidence_book == bookmd5:
            return enrich_native_highlight_evidence(data, candidate, True)
    if latest:
        candidate, data = latest
        return enrich_native_highlight_evidence(data, candidate, True)
    return {}


def native_highlight_block_detail(default_detail: str, evidence: dict[str, Any]) -> str:
    parts = [default_detail]
    source_path = str(evidence.get("sourcePath") or evidence.get("path") or "").strip()
    if source_path:
        parts.append(f"evidence={source_path}")
    problems = evidence.get("problems") if isinstance(evidence.get("problems"), list) else []
    if problems:
        parts.append("problems=" + ",".join(str(item) for item in problems[:6]))
    attempt = evidence.get("highlightAttemptReason")
    if not attempt:
        attempt_data = evidence.get("highlightAttempt") if isinstance(evidence.get("highlightAttempt"), dict) else {}
        attempt = attempt_data.get("reason")
    if attempt:
        parts.append(f"attempt={attempt}")
    blob = evidence.get("highlightBlobCheck") if isinstance(evidence.get("highlightBlobCheck"), dict) else {}
    blob_detail = str(blob.get("detail") or "").strip()
    if blob_detail:
        parts.append(blob_detail)
    return "; ".join(parts)


def check_native_highlight_visible(
    events: list[dict[str, Any]], native_highlight_evidence: dict[str, Any] | None, topicid: str, bookmd5: str
) -> dict[str, Any]:
    evidence = native_highlight_evidence or {}
    evidence_topic, evidence_book = native_highlight_scope(evidence)
    blob = evidence.get("highlightBlobCheck") if isinstance(evidence.get("highlightBlobCheck"), dict) else {}
    event_posted = latest_matching_event(events, "nativeHighlightSelectionPosted", topicid, bookmd5)
    if (
        evidence.get("schema") == NATIVE_HIGHLIGHT_SCHEMA
        and evidence.get("ok") is True
        and evidence_topic == topicid
        and evidence_book == bookmd5
        and str(blob.get("status") or "") == "OK"
        and int(blob.get("native_highlight_blobs") or 0) > 0
    ):
        return pass_check(
            "native_highlight_visible",
            "MN native visible highlight",
            "Native highlight evidence proves a same-document posted event and ZHIGHLIGHTS blob.",
            {"nativeHighlightEvidence": evidence},
        )
    if event_posted:
        detail = "Found nativeHighlightSelectionPosted, but missing matching native-highlight evidence with ZHIGHLIGHTS blob for the same topic/book."
    else:
        detail = "Missing native visible highlight proof for the requested same topic/book document."
    detail = native_highlight_block_detail(detail, evidence) if evidence else detail
    return block_check(
        "native_highlight_visible",
        "MN native visible highlight",
        detail,
        {"nativeHighlightEvidence": evidence},
        ["Run Collect Native Highlight Evidence.command, then either use the current PDF selection or reselect a short text span in the same PDF within the wait window; pass that JSON to this script."],
    )


def check_selection_popup(events: list[dict[str, Any]], topicid: str, bookmd5: str) -> dict[str, Any]:
    item = latest_matching_event(events, "selectionPopupHighlightMenuInstalled", topicid, bookmd5)
    if item:
        return pass_check("selection_popup_highlight", "PDF selection popup entry", "The PDF selection popup highlighter was installed.", {"event": item})
    diagnostic_names = {
        "selectionPopupHighlightObserverRegistered",
        "selectionPopupHighlightObserverFailed",
        "selectionPopupHighlightObserverUnregistered",
        "selectionPopupHighlightObserverUnregisterFailed",
        "selectionPopupHighlightNotificationObserved",
        "selectionPopupHighlightNotificationSkipped",
        "selectionPopupHighlightMenuSkipped",
        "selectionPopupHighlightMenuFailed",
    }
    latest_diagnostic = None
    for candidate in events:
        if str(candidate.get("event") or "") in diagnostic_names and same_document(candidate, topicid, bookmd5):
            latest_diagnostic = candidate
    if latest_diagnostic:
        extra = event_extra(latest_diagnostic)
        reason = str(extra.get("reason") or "")
        event_name = str(latest_diagnostic.get("event") or "")
        if event_name == "selectionPopupHighlightObserverRegistered":
            detail = (
                "Missing selectionPopupHighlightMenuInstalled for the requested same topic/book document; "
                "observer registered, but no PDF selection popup notification has been observed yet."
            )
        else:
            detail = (
                "Missing selectionPopupHighlightMenuInstalled for the requested same topic/book document; "
                f"latest diagnostic is {latest_diagnostic.get('event')}"
                + (f" reason={reason}." if reason else ".")
            )
        return block_check(
            "selection_popup_highlight",
            "PDF selection popup entry",
            detail,
            {"event": "selectionPopupHighlightMenuInstalled", "latestDiagnosticEvent": latest_diagnostic},
            ["Restart highlight evidence collection and reselect a short text span in the same PDF; inspect latestDiagnosticEvent if it remains blocked."],
        )
    return missing_event_check("selection_popup_highlight", "PDF selection popup entry", "selectionPopupHighlightMenuInstalled", events)


def evaluate_single_document_acceptance(
    *,
    topicid: str,
    bookmd5: str,
    events: list[dict[str, Any]],
    action_results: list[dict[str, Any]] | None = None,
    native_highlight_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    action_results = action_results or []
    checks = [
        check_runtime_web_controls(events, topicid, bookmd5),
        check_native_api_matrix(events, topicid, bookmd5),
        check_handle_response(events, topicid, bookmd5),
        check_card_write(events, topicid, bookmd5),
        check_mindmap(events, topicid, bookmd5, "createRoot", "mindmap_create", "New mindmap write"),
        check_mindmap(events, topicid, bookmd5, "mergeIntoSelected", "mindmap_merge", "Append to current mindmap"),
        check_pdf_cache(events, topicid, bookmd5),
        check_native_highlight_visible(events, native_highlight_evidence, topicid, bookmd5),
        check_selection_popup(events, topicid, bookmd5),
        require_action_result("settings", "Settings save/probe", action_results, "settings_update", topicid, bookmd5),
        require_action_result("file_upload", "Supplement file upload", action_results, "upload_file", topicid, bookmd5),
        require_action_result(
            "goal_run",
            "One-shot goal run",
            action_results,
            "goal_run",
            topicid,
            bookmd5,
            lambda result: bool(result.get("goalQueue")),
            "Run a one-shot goal and save the JSON result.",
        ),
        require_action_result("queue", "Queue status", action_results, "queue_status", topicid, bookmd5),
        require_action_result("history", "History list", action_results, "history_list", topicid, bookmd5),
        require_action_result(
            "annotated_pdf_export",
            "Annotated PDF export",
            action_results,
            "export_annotated_pdf",
            topicid,
            bookmd5,
            lambda result: bool(result.get("ok"))
            and str(result.get("status") or "") == "OK"
            and int(result.get("annotations_created") or 0) > 0
            and result.get("modifiedOriginal") is False,
            "Run export_annotated_pdf in the same document and save the JSON result.",
        ),
    ]
    passed = sum(1 for item in checks if item["status"] == "PASS")
    blocked = sum(1 for item in checks if item["status"] != "PASS")
    report = {
        "schema": SCHEMA,
        "ok": blocked == 0,
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "topicid": topicid,
        "bookmd5": bookmd5,
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "summary": {
            "singleDocumentAcceptance": "PASS" if blocked == 0 else "BLOCK",
            "total": len(checks),
            "passed": passed,
            "blocked": blocked,
        },
        "checks": checks,
    }
    report["nextActions"] = [
        action
        for check in checks
        if check["status"] != "PASS"
        for action in check.get("nextActions", [])
    ][:8]
    return report


def load_action_results(paths: list[str]) -> list[dict[str, Any]]:
    if not paths and DEFAULT_ACTION_RESULTS_PATH.exists():
        paths = [str(DEFAULT_ACTION_RESULTS_PATH)]
    results: list[dict[str, Any]] = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path.suffix.lower() == ".jsonl":
            results.extend(read_jsonl(path))
        else:
            data = read_json(path)
            if isinstance(data.get("results"), list):
                results.extend(item for item in data["results"] if isinstance(item, dict))
            elif data:
                results.append(data)
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that Codex Companion core workflows were tested in one MarginNote document."
    )
    parser.add_argument("--topicid", required=True, help="MarginNote notebook/topic id used for the test document.")
    parser.add_argument("--bookmd5", required=True, help="MarginNote book/document md5 used for the test document.")
    parser.add_argument("--events", default=str(EVENTS_PATH), help="Path to events.jsonl.")
    parser.add_argument(
        "--action-results",
        action="append",
        default=[],
        help=f"JSON/JSONL action result evidence from send_action.py --record or Web export runs. Can be passed multiple times. Default if present: {DEFAULT_ACTION_RESULTS_PATH}",
    )
    parser.add_argument("--native-highlight-evidence", default="", help="Native highlight evidence JSON.")
    parser.add_argument("--output", default="", help="Write report JSON to this path.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    native_highlight = load_native_highlight_evidence(args.native_highlight_evidence, args.topicid, args.bookmd5)
    report = evaluate_single_document_acceptance(
        topicid=args.topicid,
        bookmd5=args.bookmd5,
        events=read_jsonl(args.events),
        action_results=load_action_results(args.action_results),
        native_highlight_evidence=native_highlight,
    )
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json_dumps(report) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(
            f"single-document acceptance: {report['summary']['singleDocumentAcceptance']} "
            f"({report['summary']['passed']}/{report['summary']['total']} passed)"
        )
        for check in report["checks"]:
            if check["status"] != "PASS":
                print(f"- BLOCK {check['id']}: {check['detail']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
