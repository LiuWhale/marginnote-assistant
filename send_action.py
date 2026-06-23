#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_URL = "http://127.0.0.1:48761"
DEFAULT_COMPANION_HOME = Path(os.environ.get("CODEX_MN_COMPANION_HOME", Path.home() / ".codex/marginnote-assistant")).expanduser()
DEFAULT_ACTION_RESULTS_PATH = DEFAULT_COMPANION_HOME / "release/evidence/action-results.jsonl"


def read_default(key: str) -> str:
    try:
        result = subprocess.run(
            ["/usr/bin/defaults", "read", "QReader.MarginStudy.easy", key],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip().strip('"')


def post_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=120) as response:
            raw = response.read().decode("utf-8")
    except error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code}: {raw}") from exc
    except Exception as exc:
        raise SystemExit(f"request failed: {exc}") from exc
    try:
        return json.loads(raw)
    except Exception as exc:
        raise SystemExit(f"invalid JSON response: {raw[:1000]}") from exc


def append_action_result_record(
    path: Path | str,
    *,
    endpoint: str,
    payload: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    record_path = Path(path).expanduser()
    record_path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "action": str(payload.get("action") or ""),
        "topicid": str(payload.get("topicid") or payload.get("notebookid") or ""),
        "bookmd5": str(payload.get("bookmd5") or payload.get("docmd5") or ""),
        "endpoint": endpoint,
        "payload": payload,
        "result": result,
    }
    with record_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    return row


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Programmatically trigger a Codex Companion action without screenshots or mouse clicks."
    )
    parser.add_argument(
        "action",
        choices=[
            "chat",
            "explain_selection",
            "generate_card",
            "generate_mindmap",
            "generate_full_reading",
            "health",
            "diagnose_highlights",
            "diagnose_permissions",
            "open_full_disk_access_settings",
            "export_annotated_pdf",
            "repair_knows_highlights",
            "settings_get",
            "settings_update",
            "goal_get",
            "goal_update",
            "goal_run",
            "upload_file",
            "cache_pdf_from_marginnote",
            "request_pdf_cache",
            "request_web_panel_reload",
            "request_native_capability_probe",
            "collect_mn_runtime_evidence",
            "request_draft_write",
            "request_native_highlight_selection",
            "native_highlight_wizard_start",
            "native_highlight_wizard_status",
            "single_document_acceptance_summary",
            "release_acceptance_summary",
            "queue_status",
            "stop_current",
            "history_list",
            "history_clear",
            "restart_marginnote4",
        ],
    )
    parser.add_argument("--prompt", default="", help="Prompt text passed to the plugin action.")
    parser.add_argument("--selection-text", default="", help="Text excerpt used by export_annotated_pdf for locating highlights.")
    parser.add_argument("--model", default="", help="Model name for settings_update.")
    parser.add_argument("--speed", default="", choices=["", "fast", "balanced", "deep"], help="Speed preset for settings_update.")
    parser.add_argument("--permission", default="", choices=["", "read_only", "notes", "full"], help="Permission preset for settings_update.")
    parser.add_argument("--ai-backend", default="", choices=["", "auto", "codex_cli", "openai_api", "local"], help="AI backend for settings_update.")
    parser.add_argument("--codex-cli-path", default="", help="Explicit codex executable path for settings_update.")
    parser.add_argument("--goal-title", default="", help="Goal title for goal_update or goal_run.")
    parser.add_argument("--goal-detail", default="", help="Goal detail for goal_update or goal_run.")
    parser.add_argument("--draft-id", default="", help="Draft id for request_draft_write.")
    parser.add_argument("--file-path", default="", help="File path for upload_file.")
    parser.add_argument("--file-name", default="", help="File display name for upload_file.")
    parser.add_argument("--file-content", default="", help="Inline text content for upload_file.")
    parser.add_argument("--topicid", default="", help="MarginNote notebook/topic id.")
    parser.add_argument("--bookmd5", default="", help="MarginNote document md5.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Companion base URL.")
    parser.add_argument(
        "--record",
        action="store_true",
        help=f"Append a scoped JSONL action result for single-document acceptance. Default: {DEFAULT_ACTION_RESULTS_PATH}",
    )
    parser.add_argument(
        "--record-path",
        default="",
        help="JSONL path for --record. Passing this also enables recording.",
    )
    parser.add_argument(
        "--direct",
        action="store_true",
        help="Call /marginnote/action directly. Without this flag, the command is queued for the MN4 plugin.",
    )
    args = parser.parse_args()

    topicid = args.topicid or read_default("mindbooks_lasttopicid")
    bookmd5 = args.bookmd5 or read_default("mindbooks_lastbookmd5")
    payload: dict[str, Any] = {
        "action": args.action,
        "prompt": args.prompt,
        "topicid": topicid,
        "notebookid": topicid,
        "bookmd5": bookmd5,
        "docmd5": bookmd5,
        "source": "send_action.py",
    }
    if args.action == "settings_update":
        payload["settings"] = {
            key: value
            for key, value in {
                "model": args.model,
                "speed": args.speed,
                "permission": args.permission,
                "aiBackend": args.ai_backend,
                "codexCliPath": args.codex_cli_path,
            }.items()
            if value
        }
    if args.action in {"goal_update", "goal_run"}:
        payload["goal"] = {"title": args.goal_title, "detail": args.goal_detail or args.prompt}
    if args.action == "upload_file":
        if args.file_path:
            payload["filePath"] = args.file_path
        if args.file_name:
            payload["fileName"] = args.file_name
        if args.file_content or args.prompt:
            payload["fileContent"] = args.file_content or args.prompt
    if args.action in {"export_annotated_pdf", "request_native_highlight_selection"}:
        selection_text = args.selection_text or args.prompt
        if selection_text:
            payload["selectionText"] = selection_text
    if args.action == "request_draft_write":
        payload["draftId"] = args.draft_id or args.prompt

    if args.action in {
        "health",
        "settings_get",
        "settings_update",
        "goal_get",
        "goal_update",
        "goal_run",
        "upload_file",
        "cache_pdf_from_marginnote",
        "request_pdf_cache",
        "request_web_panel_reload",
        "request_native_capability_probe",
        "collect_mn_runtime_evidence",
        "request_draft_write",
        "request_native_highlight_selection",
        "native_highlight_wizard_start",
        "native_highlight_wizard_status",
        "single_document_acceptance_summary",
        "release_acceptance_summary",
        "queue_status",
        "stop_current",
        "diagnose_permissions",
        "open_full_disk_access_settings",
        "history_list",
        "history_clear",
    }:
        endpoint = "/marginnote/action"
    else:
        endpoint = "/marginnote/action" if args.direct else "/marginnote/enqueue"

    result = post_json(args.url.rstrip("/") + endpoint, payload)
    if args.record or args.record_path:
        record_path = Path(args.record_path).expanduser() if args.record_path else DEFAULT_ACTION_RESULTS_PATH
        append_action_result_record(record_path, endpoint=endpoint, payload=payload, result=result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
