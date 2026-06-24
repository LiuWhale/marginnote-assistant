#!/usr/bin/env python3
from __future__ import annotations

import base64
import binascii
import importlib.util
import json
import hashlib
import os
import re
import signal
import shlex
import shutil
import sqlite3
import subprocess
import sys
import threading
import time
import unicodedata
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import error, request
from urllib.parse import parse_qs, unquote, urlparse

import diagnostic_log
import update_manager
from runtime_config import (
    CODEX_CLI_REASONING,
    CODEX_CLI_TIMEOUTS,
    CONTEXT_SCOPE_ALIASES,
    CUSTOM_BUTTON_ACTIONS,
    DEFAULT_MODEL,
    DEFAULT_RUNTIME_SETTINGS,
    SPEED_MAX_OUTPUT_TOKENS,
    ai_backend_label,
    sanitize_ai_backend,
    sanitize_codex_cli_path,
    sanitize_custom_buttons,
    sanitize_default_context_scope,
    sanitize_file_search_roots,
    sanitize_github_repo,
    sanitize_model,
    sanitize_openai_api_key,
    sanitize_permission,
    sanitize_proxy_url,
    sanitize_speed,
)


HOST = "127.0.0.1"
PORT = 48761
HOME = Path.home()
ROOT = Path(os.environ.get("CODEX_MN_COMPANION_HOME", HOME / ".codex/marginnote-assistant")).expanduser()
CONFIG_PATH = ROOT / ".env"
SESSIONS_DIR = ROOT / "sessions"
EVENTS_PATH = ROOT / "events.jsonl"
DIAGNOSTIC_LOG_PATH = ROOT / "logs/diagnostics.jsonl"
DIAGNOSTIC_LOG_MAX_LINES = diagnostic_log.DEFAULT_MAX_LINES
QUEUE_DIR = ROOT / "queue"
SETTINGS_PATH = ROOT / "companion_settings.json"
GOAL_PATH = ROOT / "goal.json"
UPLOAD_DIR = ROOT / "uploads"
UPLOAD_INDEX_PATH = UPLOAD_DIR / "index.json"
PDF_CACHE_DIR = UPLOAD_DIR / "pdf-cache"
PDF_CACHE_INDEX_PATH = PDF_CACHE_DIR / "index.json"
PDF_TEXT_CACHE_DIR = PDF_CACHE_DIR / "text"
CONTROL_DIR = ROOT / "control"
STOP_PATH = CONTROL_DIR / "stop.json"
WEB_BUSY_PATH = CONTROL_DIR / "web-busy.json"
RUN_STATE_PATH = CONTROL_DIR / "current-run.json"
MINDMAP_TARGETS_PATH = CONTROL_DIR / "mindmap-targets.json"
CODEX_LITE_HOME = CONTROL_DIR / "codex-home"
DRAFTS_DIR = ROOT / "drafts"
CURRENT_PLUGIN_VERSION = "0.4.24"
NATIVE_HIGHLIGHT_WIZARD_TIMEOUT_SECONDS = 90
MN_EXTENSION_DIR = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
CURRENT_GENERATION_PROCESS_LOCK = threading.RLock()
CURRENT_GENERATION_PROCESS: Any | None = None
CURRENT_GENERATION_PROCESS_LABEL = ""
REQUIRED_NATIVE_HANDLER_FEATURES = [
    "native-highlight-arm-next-selection-default",
    "native-highlight-prefer-next-selection-v1",
    "native-highlight-command-prepared",
    "selection-popup-diagnostics-v1",
    "native-highlight-selection-poll-v1",
    "selection-popup-scene-observer-v1",
    "selection-popup-notebook-rebind-v1",
    "native-highlight-selection-text-resolver-v1",
    "context-refresh-clears-stale-selection-v1",
    "ai-edit-transaction-rollback-v1",
    "ai-edit-undo-rollback-v2",
]
ONEDRIVE_COMPANION_DIR = HOME / "Library/CloudStorage/OneDrive-个人/Codex Companion"
PDF_EXPORT_DIR = ONEDRIVE_COMPANION_DIR / "exports"
MN_DOC_ROOTS = [
    HOME / "Library/Mobile Documents/iCloud~QReader~MarginStudy~easy/Documents/MNDocs",
    HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Documents/MNDocs",
    HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Application Support/MNDocs",
]
MN_DOC_CACHE_ROOTS = [
    HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Caches/MD5CacheFiles/$$$MNDOCLINK$$$iCloud.QReader.MarginStudy.easy/MNDocs",
    HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Caches/MD5CacheFiles/$$$MNDOCLINK$$$论文文件/MNDocs",
]
ONEDRIVE_PDF_ROOTS: list[Path] = []
COMMON_CLOUD_PDF_RELS = [
    "paper",
    "papers",
    "论文",
    "MNDocs",
    "博士/论文文件/MNDocs",
    "博士/脑图/papers",
    "PostGraduate/论文",
    "研究生/论文",
    "Notability/论文",
]
STOP_SIGNAL_MAX_AGE_SECONDS = 600
DB_PATH = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
KNOWN_PDF_PATHS: dict[str, Path] = {}
MINDMAP_APPEND_HINTS = (
    "补到现在脑图",
    "补到当前脑图",
    "补充到现在脑图",
    "补充到当前脑图",
    "补进现在脑图",
    "补进当前脑图",
    "追加到现在脑图",
    "追加到当前脑图",
    "加到现在脑图",
    "加到当前脑图",
    "接到现在脑图",
    "接到当前脑图",
    "并入现在脑图",
    "并入当前脑图",
    "并入脑图",
    "合并到现在脑图",
    "合并到当前脑图",
    "合并到脑图",
    "合并脑图",
    "现有脑图",
    "已有脑图",
    "现在脑图",
    "当前脑图",
    "append to",
    "merge into",
    "merge mindmap",
    "existing mindmap",
    "current mindmap",
)
DEFENSE_REQUEST_RE = re.compile(r"defense|答辩|讲稿|讲解稿|口述|汇报|presentation|talk", re.I)
DOCUMENT_SCOPE_REQUEST_RE = re.compile(
    r"全文|整篇|这篇|当前文档|当前材料|整份|通读|精读|完整|full[-\s]?(document|text|reading)|whole\s+(document|paper|file)",
    re.I,
)
DOCUMENT_CONTEXT_MAX_CHARS = 7000
PDF_TEXT_CHUNK_MAX_CHARS = 1400
PDF_TEXT_CHUNK_OVERLAP_CHARS = 160
PDF_TEXT_MAX_CHUNKS = 1200
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
CARD_BODY_MAX_CHARS = 900
CARD_SOURCE_EXCERPT_MAX_CHARS = 220
CARD_FALLBACK_SECTION_TARGET_CHARS = 180
READ_ONLY_ACTIONS = {
    "chat",
    "explain_selection",
    "health",
    "ai_backend_probe",
    "settings_get",
    "settings_update",
    "goal_get",
    "goal_update",
    "goal_run",
    "web_busy_update",
    "upload_file",
    "cache_pdf_from_marginnote",
    "request_pdf_cache",
    "request_web_panel_reload",
    "request_native_capability_probe",
    "collect_mn_runtime_evidence",
    "restart_marginnote4",
    "release_acceptance_summary",
    "single_document_acceptance_summary",
    "native_highlight_wizard_start",
    "native_highlight_wizard_status",
    "queue_status",
    "stop_current",
    "history_list",
    "history_clear",
    "logs_recent",
    "logs_clear",
    "conversation_new",
    "conversation_list",
    "conversation_load",
    "conversation_delete",
    "diagnose_highlights",
    "diagnose_permissions",
    "open_full_disk_access_settings",
    "update_check",
    "update_install",
    "update_status",
    "open_url",
    "mindmap_target_status",
    "mindmap_target_update",
    "draft_save",
    "draft_get",
    "draft_delete",
}
NOTE_WRITE_ACTIONS = {
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
    "request_draft_write",
}
FULL_PERMISSION_ACTIONS = {"export_annotated_pdf", "request_native_highlight_selection", "native_highlight_wizard_start"}
WEB_PANEL_SOURCE = "marginnote4-web-panel"
WEB_DIRECT_BUSY_ACTIONS = {
    "chat",
    "explain_selection",
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
    "goal_run",
}
GENERATION_ACTIONS = {
    "chat",
    "explain_selection",
    "goal_run",
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
}
QUEUE_RAW_ACTIONS = GENERATION_ACTIONS | {
    "diagnose_highlights",
    "export_annotated_pdf",
    "health",
    "request_native_highlight_selection",
}
NATIVE_QUEUE_ACTIONS = {
    "cache_pdf_from_current_document",
    "highlight_current_selection",
    "reload_web_panel",
    "probe_native_api_capabilities",
    "write_draft",
}

diagnostic_log.configure(DIAGNOSTIC_LOG_PATH, max_lines=DIAGNOSTIC_LOG_MAX_LINES)
SENSITIVE_LOG_KEYS = diagnostic_log.SENSITIVE_LOG_KEYS
LARGE_LOG_KEYS = diagnostic_log.LARGE_LOG_KEYS
diagnostic_timestamp = diagnostic_log.diagnostic_timestamp
sanitize_diagnostic_value = diagnostic_log.sanitize_diagnostic_value
sanitize_diagnostic_payload = diagnostic_log.sanitize_diagnostic_payload
prune_diagnostic_log = diagnostic_log.prune_diagnostic_log
append_diagnostic_log = diagnostic_log.append_diagnostic_log
read_recent_diagnostic_logs = diagnostic_log.read_recent_diagnostic_logs
clear_diagnostic_logs = diagnostic_log.clear_diagnostic_logs


def read_json_file(path: Path, fallback: Any) -> Any:
    if not path.exists():
        return fallback
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def write_json_file(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_env_setting(key: str, value: str) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = CONFIG_PATH.read_text(encoding="utf-8").splitlines() if CONFIG_PATH.exists() else []
    output: list[str] = []
    replaced = False
    for raw in lines:
        if raw.strip().startswith(key + "="):
            if value:
                output.append(f'{key}="{value}"')
            replaced = True
        else:
            output.append(raw)
    if value and not replaced:
        output.append(f'{key}="{value}"')
    CONFIG_PATH.write_text("\n".join(output).strip() + ("\n" if output else ""), encoding="utf-8")
    if value:
        os.environ[key] = value
    else:
        os.environ.pop(key, None)


def runtime_settings() -> dict[str, Any]:
    load_env_file()
    saved = read_json_file(SETTINGS_PATH, {})
    if not isinstance(saved, dict):
        saved = {}
    settings = dict(DEFAULT_RUNTIME_SETTINGS)
    settings["model"] = get_setting("OPENAI_MODEL", DEFAULT_MODEL)
    settings["proxyUrl"] = get_setting("CODEX_PROXY_URL", "")
    for key, value in saved.items():
        if key in settings and key not in {"customButtons", "fileSearchRoots"}:
            settings[key] = str(value)
    settings["permission"] = sanitize_permission(settings.get("permission"))
    settings["speed"] = sanitize_speed(settings.get("speed"))
    settings["model"] = sanitize_model(settings.get("model"), get_setting("OPENAI_MODEL", DEFAULT_MODEL))
    settings["proxyUrl"] = sanitize_proxy_url(settings.get("proxyUrl"))
    settings["aiBackend"] = sanitize_ai_backend(settings.get("aiBackend"))
    settings["codexCliPath"] = sanitize_codex_cli_path(settings.get("codexCliPath"))
    settings["defaultContextScope"] = sanitize_default_context_scope(settings.get("defaultContextScope"))
    settings["githubRepo"] = sanitize_github_repo(settings.get("githubRepo"))
    settings["customButtons"] = sanitize_custom_buttons(saved.get("customButtons"))
    settings["fileSearchRoots"] = sanitize_file_search_roots(saved.get("fileSearchRoots"))
    return settings


def save_runtime_settings(values: dict[str, Any]) -> dict[str, Any]:
    current = runtime_settings()
    if "permission" in values:
        current["permission"] = sanitize_permission(values.get("permission"))
    if "speed" in values:
        current["speed"] = sanitize_speed(values.get("speed"))
    if "model" in values:
        current["model"] = sanitize_model(values.get("model"), get_setting("OPENAI_MODEL", DEFAULT_MODEL))
    if "proxyUrl" in values:
        current["proxyUrl"] = sanitize_proxy_url(values.get("proxyUrl"))
    if "aiBackend" in values:
        current["aiBackend"] = sanitize_ai_backend(values.get("aiBackend"))
    if "codexCliPath" in values:
        current["codexCliPath"] = sanitize_codex_cli_path(values.get("codexCliPath"))
    if "defaultContextScope" in values:
        current["defaultContextScope"] = sanitize_default_context_scope(values.get("defaultContextScope"))
    if "githubRepo" in values:
        current["githubRepo"] = sanitize_github_repo(values.get("githubRepo"))
    if "customButtons" in values:
        current["customButtons"] = sanitize_custom_buttons(values.get("customButtons"))
    if "fileSearchRoots" in values:
        current["fileSearchRoots"] = sanitize_file_search_roots(values.get("fileSearchRoots"))
    api_key = sanitize_openai_api_key(values.get("openaiApiKey")) if "openaiApiKey" in values else ""
    if api_key:
        write_env_setting("OPENAI_API_KEY", api_key)
    if values.get("clearOpenAIKey") is True:
        write_env_setting("OPENAI_API_KEY", "")
    write_json_file(SETTINGS_PATH, current)
    return current


def draft_summary(draft_id: str, draft: dict[str, Any]) -> dict[str, Any]:
    cards = draft.get("cards") if isinstance(draft.get("cards"), list) else []
    mindmap = draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None
    write_target = draft.get("writeTarget") if isinstance(draft.get("writeTarget"), dict) else {}
    write_target_label = str(write_target.get("label") or "").strip()
    if not write_target_label and mindmap and mindmap.get("mergeIntoSelected"):
        write_target_label = "当前选中节点"
    edit_text = str(draft.get("editText") or "").strip()
    if not edit_text:
        edit_text = draft_edit_text(cards, str(draft.get("reply") or ""))
    return {
        "id": draft_id,
        "original_action": str(draft.get("originalAction") or draft.get("action") or ""),
        "message": str(draft.get("message") or ""),
        "reply_preview": str(draft.get("reply") or "")[:280],
        "edit_text": edit_text,
        "card_count": len(cards),
        "has_mindmap": bool(mindmap),
        "mindmap_title": str(mindmap.get("title") or "") if mindmap else "",
        "write_target": write_target_label,
        "created_at": str(draft.get("created_at") or ""),
    }


def draft_edit_text(cards: list[Any], fallback: str = "") -> str:
    blocks: list[str] = []
    for card in cards:
        if not isinstance(card, dict):
            continue
        title = str(card.get("title") or "未命名卡片").strip() or "未命名卡片"
        body = str(card.get("body") or card.get("comment") or "").strip()
        blocks.append(f"## {title}\n{body}".strip())
    if blocks:
        return "\n\n".join(blocks)
    return str(fallback or "").strip()


def cards_from_draft_edit_text(text: str) -> list[dict[str, str]]:
    lines = str(text or "").replace("\r\n", "\n").splitlines()
    cards: list[dict[str, str]] = []
    current_title = ""
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_title, current_body
        title = current_title.strip()
        body = "\n".join(current_body).strip()
        if title or body:
            cards.append({"title": title or "未命名卡片", "body": body})
        current_title = ""
        current_body = []

    for line in lines:
        if line.startswith("## "):
            flush()
            current_title = line[3:].strip()
        else:
            current_body.append(line)
    flush()
    if not cards:
        plain = str(text or "").strip()
        if plain:
            first_line = plain.splitlines()[0].strip()
            cards.append({"title": first_line[:80] or "未命名卡片", "body": plain})
    return cards


def save_draft(payload: dict[str, Any]) -> dict[str, Any]:
    draft_payload = payload.get("draft") if isinstance(payload.get("draft"), dict) else payload
    if not isinstance(draft_payload, dict):
        return {"ok": False, "message": "缺少草稿内容。"}
    cards = draft_payload.get("cards") if isinstance(draft_payload.get("cards"), list) else []
    mindmap = draft_payload.get("mindmap") if isinstance(draft_payload.get("mindmap"), dict) else None
    write_target = (
        draft_payload.get("writeTarget")
        if isinstance(draft_payload.get("writeTarget"), dict)
        else payload.get("writeTarget") if isinstance(payload.get("writeTarget"), dict) else {}
    )
    if not write_target and isinstance(mindmap, dict) and isinstance(mindmap.get("writeTarget"), dict):
        write_target = mindmap["writeTarget"]
    if not cards and not mindmap:
        return {"ok": False, "message": "草稿没有卡片或脑图，不能写入。"}
    draft_id = hashlib.sha256(f"{time.time()}|{uuid.uuid4()}".encode("utf-8")).hexdigest()[:20]
    draft = {
        "ok": bool(draft_payload.get("ok", True)),
        "message": str(draft_payload.get("message") or "草稿已准备好。"),
        "reply": str(draft_payload.get("reply") or ""),
        "cards": cards,
        "mindmap": mindmap,
        "writeTarget": write_target,
        "originalAction": str(payload.get("originalAction") or draft_payload.get("action") or ""),
        "topicid": str(payload.get("topicid") or draft_payload.get("topicid") or ""),
        "bookmd5": str(payload.get("bookmd5") or draft_payload.get("bookmd5") or ""),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    write_json_file(DRAFTS_DIR / f"{draft_id}.json", draft)
    return {
        "ok": True,
        "message": "已生成待写入草稿，请预览后确认写入 MarginNote。",
        "draft": draft_summary(draft_id, draft),
    }


def load_draft(draft_id: str) -> dict[str, Any]:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(draft_id or ""))[:80]
    if not clean_id:
        return {"ok": False, "message": "缺少草稿 ID。"}
    draft = read_json_file(DRAFTS_DIR / f"{clean_id}.json", {})
    if not isinstance(draft, dict) or not draft:
        return {"ok": False, "message": "草稿不存在或已过期。", "id": clean_id}
    draft["id"] = clean_id
    draft["draft"] = draft_summary(clean_id, draft)
    draft["ok"] = bool(draft.get("ok", True))
    return draft


def delete_draft(draft_id: str) -> dict[str, Any]:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(draft_id or ""))[:80]
    if not clean_id:
        return {"ok": False, "message": "缺少草稿 ID。"}
    try:
        (DRAFTS_DIR / f"{clean_id}.json").unlink()
        return {"ok": True, "message": "草稿已丢弃。", "id": clean_id}
    except FileNotFoundError:
        return {"ok": True, "message": "草稿已不存在。", "id": clean_id}


def update_draft(payload: dict[str, Any]) -> dict[str, Any]:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("id") or payload.get("draftId") or ""))[:80]
    if not clean_id:
        return {"ok": False, "message": "缺少草稿 ID。"}
    path = DRAFTS_DIR / f"{clean_id}.json"
    draft = read_json_file(path, {})
    if not isinstance(draft, dict) or not draft:
        return {"ok": False, "message": "草稿不存在或已过期。", "id": clean_id}
    edit_text = str(payload.get("editText") or "").strip()
    if not edit_text:
        return {"ok": False, "message": "草稿编辑内容为空。", "id": clean_id}
    cards = cards_from_draft_edit_text(edit_text)
    if not cards and not isinstance(draft.get("mindmap"), dict):
        return {"ok": False, "message": "编辑内容没有可写入卡片。", "id": clean_id}
    if cards:
        draft["cards"] = cards
    draft["editText"] = edit_text
    draft["reply"] = edit_text
    draft["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json_file(path, draft)
    return {
        "ok": True,
        "message": "草稿编辑已保存。",
        "draft": draft_summary(clean_id, draft),
    }


def active_goal() -> dict[str, str]:
    goal = read_json_file(GOAL_PATH, {})
    if not isinstance(goal, dict):
        goal = {}
    if goal and str(goal.get("mode") or "") != "saved":
        goal = {}
    return {
        "title": str(goal.get("title") or "").strip(),
        "detail": str(goal.get("detail") or "").strip(),
        "updated_at": str(goal.get("updated_at") or "").strip(),
    }


def save_goal(goal_payload: dict[str, Any]) -> dict[str, str]:
    goal = {
        "title": str(goal_payload.get("title") or "").strip()[:160],
        "detail": str(goal_payload.get("detail") or "").strip()[:3000],
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mode": "saved",
    }
    write_json_file(GOAL_PATH, goal)
    return goal


def one_shot_goal(goal_payload: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(goal_payload.get("title") or "").strip()[:160],
        "detail": str(goal_payload.get("detail") or "").strip()[:3000],
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }


def clear_goal() -> dict[str, str]:
    write_json_file(GOAL_PATH, {"title": "", "detail": "", "updated_at": "", "mode": "cleared"})
    return active_goal()


def goal_payload_from_request(payload: dict[str, Any]) -> dict[str, str]:
    raw_goal = payload.get("goal") if isinstance(payload.get("goal"), dict) else {}
    title = str(raw_goal.get("title") or payload.get("title") or "").strip()
    detail = str(raw_goal.get("detail") or payload.get("detail") or "").strip()
    prompt = str(payload.get("prompt") or "").strip()
    if not title and prompt:
        lines = [line.strip() for line in prompt.splitlines() if line.strip()]
        if lines:
            title = re.sub(r"^目标[:：]\s*", "", lines[0]).strip()
            detail = "\n".join(lines[1:]).strip() or detail
    if not title and detail:
        title = detail[:60]
    return {"title": title[:160], "detail": detail[:3000]}


def uploaded_files() -> list[dict[str, Any]]:
    files = read_json_file(UPLOAD_INDEX_PATH, [])
    if not isinstance(files, list):
        return []
    clean: list[dict[str, Any]] = []
    for item in files[-20:]:
        if not isinstance(item, dict):
            continue
        clean.append(
            {
                "id": str(item.get("id") or ""),
                "name": str(item.get("name") or ""),
                "path": str(item.get("path") or ""),
                "size": int(item.get("size") or 0),
                "uploaded_at": str(item.get("uploaded_at") or ""),
            }
        )
    return [item for item in clean if item["id"] and item["name"] and item["path"]]


def save_uploaded_files(files: list[dict[str, Any]]) -> None:
    write_json_file(UPLOAD_INDEX_PATH, files[-20:])


def safe_upload_name(name: str) -> str:
    base = Path(name or "upload.txt").name.strip() or "upload.txt"
    base = re.sub(r"[^A-Za-z0-9._ -]+", "_", base)
    return base[:120] or "upload.txt"


def pdf_cache_index() -> dict[str, Any]:
    data = read_json_file(PDF_CACHE_INDEX_PATH, {})
    return data if isinstance(data, dict) else {}


def save_pdf_cache_index(index: dict[str, Any]) -> None:
    write_json_file(PDF_CACHE_INDEX_PATH, index)


def pdf_cache_key(book_md5: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(book_md5 or "").strip())[:96]


def cached_pdf_for_book(book_md5: str) -> Path | None:
    key = pdf_cache_key(book_md5)
    if not key:
        return None
    record = pdf_cache_index().get(key)
    if not isinstance(record, dict):
        return None
    path = Path(str(record.get("path") or ""))
    if path.is_file() and path.suffix.lower() == ".pdf":
        return path
    return None


def pdf_cache_access_status(book_md5: str) -> dict[str, Any]:
    key = pdf_cache_key(book_md5)
    if not key:
        return {
            "path": "",
            "exists": False,
            "readable": False,
            "status": "MISSING",
            "message": "没有 bookmd5，无法检查 PDF 缓存",
        }
    record = pdf_cache_index().get(key)
    if not isinstance(record, dict):
        return {
            "path": "",
            "exists": False,
            "readable": False,
            "status": "MISSING",
            "message": "当前 book 尚无缓存 PDF",
        }
    path = Path(str(record.get("path") or ""))
    result = probe_file_read_access(path)
    result["sourcePdf"] = str(record.get("sourcePdf") or "")
    result["cached_at"] = str(record.get("cached_at") or "")
    result["sha256"] = str(record.get("sha256") or "")
    result["size"] = int(record.get("size") or 0)
    return result


def pending_pdf_cache_command(topic_id: str, book_md5: str) -> dict[str, Any] | None:
    if not topic_id:
        return None
    for path in queue_paths_for_topic(topic_id, book_md5):
        for record in read_queue_lines(path):
            if str(record.get("topicid") or "") != topic_id:
                continue
            if book_md5 and str(record.get("bookmd5") or "") != book_md5:
                continue
            command = record.get("command") if isinstance(record, dict) else None
            if not isinstance(command, dict):
                continue
            if str(command.get("nativeAction") or "") != "cache_pdf_from_current_document":
                continue
            command["_queue_id"] = str(record.get("id") or "")
            return command
    return None


def clear_pending_pdf_cache_commands(topic_id: str, book_md5: str) -> dict[str, int]:
    if not topic_id:
        return {"removed": 0, "remaining": 0}
    paths = queue_paths_for_topic(topic_id, book_md5)
    removed = 0
    remaining = 0
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        kept: list[str] = []
        for line in lines:
            try:
                record = json.loads(line)
            except Exception:
                kept.append(line)
                continue
            command = record.get("command") if isinstance(record, dict) else None
            is_same_scope = str(record.get("topicid") or "") == topic_id and (
                not book_md5 or str(record.get("bookmd5") or "") == book_md5
            )
            is_pdf_cache_command = (
                isinstance(command, dict)
                and str(command.get("nativeAction") or "") == "cache_pdf_from_current_document"
            )
            if is_same_scope and is_pdf_cache_command:
                removed += 1
                continue
            kept.append(line)
        remaining += len(kept)
        if kept:
            path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    return {"removed": removed, "remaining": remaining}


def pdf_cache_progress_payload(topic_id: str = "", book_md5: str = "") -> dict[str, Any]:
    access = pdf_cache_access_status(book_md5)
    status = str(access.get("status") or "MISSING").upper()
    pending_command = pending_pdf_cache_command(topic_id, book_md5)
    base: dict[str, Any] = {
        "state": "missing",
        "label": "PDF缓存：未就绪",
        "detail": str(access.get("message") or "当前文档尚无可读取的 PDF 缓存。"),
        "pending": False,
        "status": status,
        "path": str(access.get("path") or ""),
        "sourcePdf": str(access.get("sourcePdf") or ""),
        "cached_at": str(access.get("cached_at") or ""),
        "queueId": "",
        "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if status == "OK" and access.get("readable"):
        base.update(
            {
                "state": "cached",
                "label": "PDF缓存：已就绪",
                "detail": "Companion 已能读取当前文档的缓存副本，全文解读会优先使用它。",
                "pending": False,
            }
        )
        return base
    if pending_command:
        candidate = str(pending_command.get("pdfPath") or pending_command.get("documentPath") or "")
        detail = "保持当前 PDF 打开，MN4 插件会读取并上传到 Companion 缓存。"
        if candidate:
            detail = f"{detail} 候选文件：{candidate}"
        base.update(
            {
                "state": "waiting_native",
                "label": "PDF缓存：等待 MN4 缓存",
                "detail": detail,
                "pending": True,
                "queueId": str(pending_command.get("_queue_id") or ""),
            }
        )
        return base
    if status == "PERMISSION":
        base.update(
            {
                "state": "permission",
                "label": "PDF缓存：权限受限",
                "detail": f"后台不能读取文件：{access.get('message') or 'Operation not permitted'}。已请求 MN4 进程缓存时会显示等待状态。",
            }
        )
        return base
    if status in {"ERROR", "WARN"}:
        base.update(
            {
                "state": "error" if status == "ERROR" else "warning",
                "label": "PDF缓存：读取异常",
                "detail": str(access.get("message") or "缓存文件暂时不可读。"),
            }
        )
    return base


def cache_pdf_from_marginnote(payload: dict[str, Any]) -> dict[str, Any]:
    book_md5 = normalize_book_md5(payload)
    key = pdf_cache_key(book_md5)
    if not key:
        return {"ok": False, "message": "缓存 PDF 失败：缺少 bookmd5。"}
    raw = str(payload.get("pdfBase64") or payload.get("fileBase64") or "").strip()
    if raw.startswith("data:"):
        raw = raw.split(",", 1)[1] if "," in raw else ""
    if not raw:
        return {"ok": False, "message": "缓存 PDF 失败：缺少 pdfBase64。"}
    try:
        data = base64.b64decode(raw, validate=True)
    except (binascii.Error, ValueError) as exc:
        return {"ok": False, "message": f"缓存 PDF 失败：base64 无效：{exc}"}
    if len(data) < 8 or not data.startswith(b"%PDF"):
        return {"ok": False, "message": "缓存 PDF 失败：数据不是 PDF。"}
    if len(data) > 80_000_000:
        return {"ok": False, "message": "缓存 PDF 失败：PDF 超过 80 MB。"}

    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = safe_upload_name(str(payload.get("fileName") or Path(str(payload.get("pdfPath") or "document.pdf")).name or "document.pdf"))
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    target = PDF_CACHE_DIR / f"{key}-{name}"
    target.write_bytes(data)
    record = {
        "bookmd5": book_md5,
        "path": str(target),
        "sourcePdf": str(payload.get("pdfPath") or payload.get("documentPath") or ""),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    index = pdf_cache_index()
    index[key] = record
    save_pdf_cache_index(index)
    cleared_queue = clear_pending_pdf_cache_commands(normalize_topic_id(payload), book_md5)
    pdf_cache = pdf_cache_progress_payload(normalize_topic_id(payload), book_md5)
    return {
        "ok": True,
        "message": f"已缓存当前 PDF：{name}",
        "reply": (
            "已由 MarginNote 进程把当前 PDF 缓存到 Companion。\n\n"
            f"缓存文件：`{target}`\n"
            "后续导出标注 PDF 会优先使用这个缓存副本，不再要求后台 LaunchAgent 直接读取原始 PDF。"
        ),
        "cache": record,
        "clearedPdfCacheQueue": cleared_queue,
        "pdfCache": pdf_cache,
    }


def cache_pdf_from_source_path(payload: dict[str, Any], source_pdf: Path) -> dict[str, Any] | None:
    book_md5 = normalize_book_md5(payload)
    key = pdf_cache_key(book_md5)
    if not key or not source_pdf or source_pdf.suffix.lower() != ".pdf":
        return None
    try:
        if not source_pdf.is_file():
            return None
        data = source_pdf.read_bytes()
    except Exception as exc:
        append_diagnostic_log(
            "warn",
            "pdf.cache.direct",
            f"后台直接读取 PDF 失败：{exc}",
            payload=payload,
            extra={"sourcePdf": str(source_pdf)},
            request_id=str(payload.get("_request_id") or ""),
        )
        return None
    if len(data) < 8 or not data.startswith(b"%PDF") or len(data) > 80_000_000:
        return None

    PDF_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    name = safe_upload_name(str(payload.get("fileName") or source_pdf.name or "document.pdf"))
    if not name.lower().endswith(".pdf"):
        name += ".pdf"
    target = PDF_CACHE_DIR / f"{key}-{name}"
    target.write_bytes(data)
    record = {
        "bookmd5": book_md5,
        "path": str(target),
        "sourcePdf": str(source_pdf),
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "cached_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    index = pdf_cache_index()
    index[key] = record
    save_pdf_cache_index(index)
    cleared_queue = clear_pending_pdf_cache_commands(normalize_topic_id(payload), book_md5)
    pdf_cache = pdf_cache_progress_payload(normalize_topic_id(payload), book_md5)
    append_diagnostic_log(
        "info",
        "pdf.cache.direct",
        "后台已直接缓存当前 PDF。",
        payload=payload,
        extra={"sourcePdf": str(source_pdf), "cachePath": str(target), "size": len(data)},
        request_id=str(payload.get("_request_id") or ""),
    )
    return {
        "ok": True,
        "message": f"已直接缓存当前 PDF：{name}",
        "reply": (
            "Companion 后台已直接读取并缓存当前 PDF。\n\n"
            f"缓存文件：`{target}`\n"
            "后续全文解读会优先使用这个缓存副本。"
        ),
        "cache": record,
        "clearedPdfCacheQueue": cleared_queue,
        "queue": queue_status_payload(normalize_topic_id(payload), book_md5),
        "pdfCache": pdf_cache,
    }


def register_upload(payload: dict[str, Any]) -> dict[str, Any]:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = safe_upload_name(str(payload.get("fileName") or payload.get("name") or "upload.txt"))
    content = payload.get("fileContent")
    source_path = str(payload.get("filePath") or "").strip()
    upload_id = hashlib.sha256(f"{name}|{time.time()}|{uuid.uuid4()}".encode("utf-8")).hexdigest()[:16]
    target = UPLOAD_DIR / f"{upload_id}-{name}"
    if isinstance(content, str):
        data = content.encode("utf-8")
        if len(data) > 2_000_000:
            return {"ok": False, "message": "上传文本超过 2 MB，已拒绝。"}
        target.write_bytes(data)
    elif source_path:
        src = Path(source_path).expanduser()
        if not src.exists() or not src.is_file():
            return {"ok": False, "message": f"上传文件不存在：{src}"}
        if src.stat().st_size > 20_000_000:
            return {"ok": False, "message": "上传文件超过 20 MB，已拒绝。"}
        shutil.copy2(src, target)
    else:
        return {"ok": False, "message": "缺少 fileContent 或 filePath。"}
    record = {
        "id": upload_id,
        "name": name,
        "path": str(target),
        "size": target.stat().st_size,
        "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    files = uploaded_files()
    files.append(record)
    save_uploaded_files(files)
    return {"ok": True, "message": f"已上传文件：{name}", "file": record, "files": uploaded_files()}


def uploaded_context_excerpt(max_chars: int = 1800) -> str:
    chunks: list[str] = []
    for item in uploaded_files()[-5:]:
        path = Path(str(item.get("path") or ""))
        if not path.exists() or path.stat().st_size > 300_000:
            chunks.append(f"- {item.get('name')} ({item.get('size')} bytes)")
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            chunks.append(f"- {item.get('name')} ({item.get('size')} bytes)")
            continue
        text = re.sub(r"\s+", " ", text).strip()
        chunks.append(f"文件 {item.get('name')} 摘要：{text[:700]}")
    joined = "\n".join(chunks)
    return joined[:max_chars]


def stop_status(max_age_seconds: int = STOP_SIGNAL_MAX_AGE_SECONDS) -> dict[str, Any]:
    state = read_json_file(STOP_PATH, {})
    if not isinstance(state, dict):
        state = {}
    updated_epoch = 0.0
    try:
        updated_epoch = float(state.get("updated_epoch") or 0)
    except (TypeError, ValueError):
        updated_epoch = 0.0
    requested = bool(state.get("requested"))
    expired = requested and (updated_epoch <= 0 or (time.time() - updated_epoch) > max_age_seconds)
    if expired:
        clear_stop()
        requested = False
    return {
        "requested": requested,
        "updated_at": str(state.get("updated_at") or ""),
        "updated_epoch": updated_epoch if requested else 0,
        "reason": str(state.get("reason") or ""),
        "expired": expired,
    }


def request_stop(reason: str = "user requested stop") -> dict[str, Any]:
    state = {
        "requested": True,
        "updated_epoch": time.time(),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "reason": reason,
    }
    write_json_file(STOP_PATH, state)
    return state


def update_web_busy(active: bool) -> dict[str, Any]:
    state = {
        "busy": bool(active),
        "updated_epoch": time.time(),
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    write_json_file(WEB_BUSY_PATH, state)
    return state


def web_busy_status(max_age_seconds: int = 1800) -> dict[str, Any]:
    state = read_json_file(WEB_BUSY_PATH, {})
    if not isinstance(state, dict):
        state = {}
    updated = float(state.get("updated_epoch") or 0)
    busy = bool(state.get("busy")) and updated > 0 and (time.time() - updated) <= max_age_seconds
    if bool(state.get("busy")) and not busy:
        update_web_busy(False)
    return {
        "busy": busy,
        "updated_at": str(state.get("updated_at") or ""),
    }


def run_state_time() -> tuple[float, str]:
    now = time.time()
    return now, time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now))


def active_run_status(max_age_seconds: int = 1800) -> dict[str, Any]:
    state = read_json_file(RUN_STATE_PATH, {})
    if not isinstance(state, dict):
        state = {}
    now = time.time()
    started_epoch = 0.0
    updated_epoch = 0.0
    try:
        started_epoch = float(state.get("started_epoch") or 0)
    except (TypeError, ValueError):
        started_epoch = 0.0
    try:
        updated_epoch = float(state.get("updated_epoch") or 0)
    except (TypeError, ValueError):
        updated_epoch = 0.0
    active = bool(state.get("active")) and updated_epoch > 0 and (now - updated_epoch) <= max_age_seconds
    expired = bool(state.get("active")) and not active and updated_epoch > 0
    if expired:
        state = {
            **state,
            "active": False,
            "stage": "已过期",
            "detail": "stale run state expired; UI can start or continue queued work.",
            "updated_epoch": now,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(now)),
            "expired": True,
        }
        write_json_file(RUN_STATE_PATH, state)
        updated_epoch = now
    elapsed_from = started_epoch or updated_epoch or now
    elapsed_until = now if active else (updated_epoch or now)
    return {
        "active": active,
        "expired": expired,
        "action": str(state.get("action") or ""),
        "stage": str(state.get("stage") or ("正在执行" if active else "空闲")),
        "detail": str(state.get("detail") or ("任务正在运行。" if active else "没有正在运行的任务。")),
        "topicid": str(state.get("topicid") or ""),
        "bookmd5": str(state.get("bookmd5") or ""),
        "queue_id": str(state.get("queue_id") or ""),
        "requestId": str(state.get("requestId") or state.get("request_id") or ""),
        "source": str(state.get("source") or ""),
        "started_at": str(state.get("started_at") or ""),
        "updated_at": str(state.get("updated_at") or ""),
        "elapsed_seconds": max(0, int(elapsed_until - elapsed_from)),
    }


def update_run_state(
    active: bool,
    *,
    action: str = "",
    stage: str = "",
    detail: str = "",
    topicid: str = "",
    bookmd5: str = "",
    queue_id: str = "",
    request_id: str = "",
    source: str = "",
) -> dict[str, Any]:
    existing = read_json_file(RUN_STATE_PATH, {})
    if not isinstance(existing, dict):
        existing = {}
    now, now_text = run_state_time()
    previous_active = bool(existing.get("active"))
    same_run = (
        previous_active
        and str(existing.get("action") or "") == str(action or existing.get("action") or "")
        and str(existing.get("queue_id") or "") == str(queue_id or existing.get("queue_id") or "")
        and str(existing.get("requestId") or existing.get("request_id") or "") == str(
            request_id or existing.get("requestId") or existing.get("request_id") or ""
        )
    )
    started_epoch = existing.get("started_epoch") if same_run else now
    started_at = existing.get("started_at") if same_run else now_text
    state = {
        "active": bool(active),
        "action": str(action or existing.get("action") or ""),
        "stage": str(stage or ("正在执行" if active else "已完成")),
        "detail": str(detail or existing.get("detail") or ""),
        "topicid": str(topicid or existing.get("topicid") or ""),
        "bookmd5": str(bookmd5 or existing.get("bookmd5") or ""),
        "queue_id": str(queue_id or existing.get("queue_id") or ""),
        "requestId": str(request_id or existing.get("requestId") or existing.get("request_id") or ""),
        "source": str(source or existing.get("source") or ""),
        "started_epoch": started_epoch,
        "started_at": started_at,
        "updated_epoch": now,
        "updated_at": now_text,
        "expired": False,
    }
    write_json_file(RUN_STATE_PATH, state)
    return active_run_status()


def clear_stop() -> None:
    try:
        STOP_PATH.unlink()
    except FileNotFoundError:
        pass


def register_current_generation_process(process: Any, label: str) -> None:
    global CURRENT_GENERATION_PROCESS, CURRENT_GENERATION_PROCESS_LABEL
    with CURRENT_GENERATION_PROCESS_LOCK:
        CURRENT_GENERATION_PROCESS = process
        CURRENT_GENERATION_PROCESS_LABEL = str(label or "generation")


def current_generation_process() -> Any | None:
    with CURRENT_GENERATION_PROCESS_LOCK:
        return CURRENT_GENERATION_PROCESS


def clear_current_generation_process(process: Any | None = None) -> None:
    global CURRENT_GENERATION_PROCESS, CURRENT_GENERATION_PROCESS_LABEL
    with CURRENT_GENERATION_PROCESS_LOCK:
        if process is not None and CURRENT_GENERATION_PROCESS is not process:
            return
        CURRENT_GENERATION_PROCESS = None
        CURRENT_GENERATION_PROCESS_LABEL = ""


def _signal_generation_process(process: Any, sig: int) -> str:
    pid = int(getattr(process, "pid", 0) or 0)
    if pid > 0:
        try:
            os.killpg(os.getpgid(pid), sig)
            return "process-group"
        except Exception:
            pass
    if sig == signal.SIGTERM:
        process.terminate()
        return "terminate"
    process.kill()
    return "kill"


def cancel_current_generation_process() -> dict[str, Any]:
    with CURRENT_GENERATION_PROCESS_LOCK:
        process = CURRENT_GENERATION_PROCESS
        label = CURRENT_GENERATION_PROCESS_LABEL
    if process is None:
        return {"attempted": False, "message": "no active generation process"}
    try:
        returncode = process.poll()
    except Exception:
        returncode = None
    if returncode is not None:
        clear_current_generation_process(process)
        return {
            "attempted": False,
            "alreadyExited": True,
            "returncode": returncode,
            "label": label,
        }
    method = ""
    killed = False
    try:
        method = _signal_generation_process(process, signal.SIGTERM)
        try:
            process.wait(timeout=1.5)
        except subprocess.TimeoutExpired:
            method = _signal_generation_process(process, signal.SIGKILL)
            killed = True
            try:
                process.wait(timeout=1.0)
            except Exception:
                pass
    except Exception as exc:
        clear_current_generation_process(process)
        return {
            "attempted": True,
            "terminated": False,
            "label": label,
            "message": f"cancel failed: {exc}",
        }
    clear_current_generation_process(process)
    return {
        "attempted": True,
        "terminated": True,
        "killed": killed,
        "method": method,
        "label": label,
    }


def queue_status_payload(topic_id: str = "", book_md5: str = "") -> dict[str, Any]:
    topic_id = topic_id or ""
    book_md5 = book_md5 or ""
    if topic_id:
        pending = poll_commands(topic_id, book_md5).get("pending", 0)
    elif QUEUE_DIR.exists():
        pending = sum(count_valid_queue_records(path) for path in QUEUE_DIR.glob("*.jsonl"))
    else:
        pending = 0
    return {
        "pending": int(pending or 0),
        "stop": stop_status(),
        "run": active_run_status(),
        "pdfCache": pdf_cache_progress_payload(topic_id, book_md5) if book_md5 else {
            "state": "unknown",
            "label": "PDF缓存：未识别文档",
            "detail": "当前上下文没有 bookmd5，暂时无法跟踪 PDF 缓存。",
            "pending": False,
            "status": "UNKNOWN",
            "path": "",
            "sourcePdf": "",
            "cached_at": "",
            "queueId": "",
            "updatedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        },
        "guide": [
            "排队用途：外部脚本或自动化可以把动作放入 Companion 队列，MN4 插件打开 notebook 后会轮询并执行。",
            "面板内的普通按钮会直接执行；如果要无人值守批处理，使用 send_action.py 不带 --direct 入队。",
            "状态栏开始/停止按钮会设置 stop 信号，阻断下一次生成动作；长请求返回后也会检查 stop，避免继续写入卡片或脑图。",
        ],
    }


def is_valid_queue_command(command: Any) -> bool:
    if not isinstance(command, dict):
        return False
    native_action = str(command.get("nativeAction") or "").strip()
    if native_action:
        return native_action in NATIVE_QUEUE_ACTIONS
    raw_action = str(command.get("rawAction") or command.get("action") or "").strip()
    return raw_action in QUEUE_RAW_ACTIONS


def count_valid_queue_records(path: Path) -> int:
    count = 0
    for record in read_queue_lines(path):
        command = record.get("command") if isinstance(record, dict) else None
        if is_valid_queue_command(command):
            count += 1
    return count


def format_run_status_text(run: dict[str, Any]) -> str:
    if not isinstance(run, dict):
        run = {}
    action = str(run.get("action") or "任务")
    stage = str(run.get("stage") or ("正在执行" if run.get("active") else "空闲"))
    detail = str(run.get("detail") or "")
    elapsed = int(run.get("elapsed_seconds") or 0)
    state = "运行中" if run.get("active") else "最近"
    if not str(run.get("action") or "") and not run.get("active"):
        return "运行状态：空闲。"
    return f"运行状态：{state} {generation_action_label(action)} / {stage} / {detail} / {elapsed}s"


def permission_error_for_action(action: str) -> str | None:
    permission = runtime_settings()["permission"]
    if action in READ_ONLY_ACTIONS:
        return None
    if action in NOTE_WRITE_ACTIONS and permission in {"notes", "full"}:
        return None
    if action in FULL_PERMISSION_ACTIONS and permission == "full":
        return None
    if action in FULL_PERMISSION_ACTIONS:
        return f"当前 Codex 权限是 {permission}，此动作需要 full 权限。"
    if action not in NOTE_WRITE_ACTIONS:
        return None
    return f"当前 Codex 权限是 {permission}，此动作需要 notes 或 full 权限。"


def stopped_response_if_needed(action: str) -> dict[str, Any] | None:
    if action not in GENERATION_ACTIONS:
        return None
    state = stop_status()
    if not state["requested"]:
        return None
    clear_stop()
    return {
        "ok": False,
        "message": "已停止当前或下一步生成动作。",
        "reply": "停止信号已生效；当前生成会被取消，后续写入会被阻断。",
        "stopped": True,
        "stop": state,
    }


def stop_response_after_generation(action: str) -> dict[str, Any] | None:
    if action not in GENERATION_ACTIONS:
        return None
    state = stop_status()
    if not state["requested"]:
        return None
    clear_stop()
    return {
        "ok": False,
        "message": "已停止当前生成动作，未继续写入。",
        "reply": "停止信号在生成过程中生效；已丢弃本次返回结果，未继续创建卡片或脑图。",
        "stopped": True,
        "stop": state,
        "action": action,
    }


def load_env_file() -> None:
    if not CONFIG_PATH.exists():
        return
    for raw in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_setting(key: str, default: str = "") -> str:
    load_env_file()
    return os.environ.get(key, default).strip()


def discover_codex_cli_path(settings: dict[str, str] | None = None) -> str:
    settings = settings or runtime_settings()
    configured = sanitize_codex_cli_path(settings.get("codexCliPath", ""))
    if configured:
        return configured
    env_path = sanitize_codex_cli_path(os.environ.get("CODEX_CLI_PATH", ""))
    if env_path:
        return env_path
    npm_global = HOME / ".npm-global/bin/codex"
    if npm_global.exists() and os.access(npm_global, os.X_OK):
        return str(npm_global)
    native_candidates = [
        HOME
        / ".npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/codex/codex",
        HOME
        / ".npm-global/lib/node_modules/@openai/codex/node_modules/@openai/codex-darwin-x64/vendor/x86_64-apple-darwin/codex/codex",
    ]
    for common in native_candidates + [Path("/opt/homebrew/bin/codex"), Path("/usr/local/bin/codex")]:
        if common.exists() and os.access(common, os.X_OK):
            return str(common)
    path = shutil.which("codex")
    if path:
        return path
    return ""


def codex_cli_status(settings: dict[str, str] | None = None) -> dict[str, Any]:
    path = discover_codex_cli_path(settings)
    available = bool(path and Path(path).exists() and os.access(path, os.X_OK))
    return {
        "available": available,
        "path": path,
    }


def prepare_codex_lite_home() -> Path:
    CODEX_LITE_HOME.mkdir(parents=True, exist_ok=True)
    source_auth = HOME / ".codex/auth.json"
    target_auth = CODEX_LITE_HOME / "auth.json"
    if source_auth.exists():
        try:
            shutil.copy2(source_auth, target_auth)
        except Exception:
            pass
    return CODEX_LITE_HOME


def merge_no_proxy(existing: str) -> str:
    values: list[str] = []
    seen: set[str] = set()
    for item in str(existing or "").split(","):
        value = item.strip()
        if value and value not in seen:
            values.append(value)
            seen.add(value)
    for value in ["127.0.0.1", "localhost", "::1"]:
        if value not in seen:
            values.append(value)
            seen.add(value)
    return ",".join(values)


def codex_cli_env(settings: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    settings = settings or runtime_settings()
    default_path = ":".join(
        [
            str(HOME / ".npm-global/bin"),
            "/opt/homebrew/bin",
            "/usr/local/bin",
            "/usr/bin",
            "/bin",
            "/usr/sbin",
            "/sbin",
        ]
    )
    env["PATH"] = env.get("PATH", default_path) + ":" + default_path
    env["HOME"] = str(prepare_codex_lite_home())
    env["CODEX_HOME"] = str(prepare_codex_lite_home())
    proxy_url = sanitize_proxy_url(settings.get("proxyUrl", ""))
    if proxy_url:
        for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            env[key] = proxy_url
        no_proxy = merge_no_proxy(env.get("NO_PROXY") or env.get("no_proxy") or "")
        env["NO_PROXY"] = no_proxy
        env["no_proxy"] = no_proxy
    return env


def ai_status_fields(settings: dict[str, str] | None = None) -> dict[str, Any]:
    load_env_file()
    settings = settings or runtime_settings()
    cli = codex_cli_status(settings)
    return {
        "openai_configured": bool(os.environ.get("OPENAI_API_KEY")),
        "ai_backend": settings["aiBackend"],
        "ai_backend_label": ai_backend_label(settings["aiBackend"]),
        "codex_cli_available": bool(cli["available"]),
        "codex_cli_path": cli["path"],
    }


def codex_cli_auth_detected() -> bool:
    return (HOME / ".codex/auth.json").exists() or (CODEX_LITE_HOME / "auth.json").exists()


def ai_backend_probe() -> dict[str, Any]:
    load_env_file()
    settings = runtime_settings()
    backend = sanitize_ai_backend(settings.get("aiBackend"))
    cli = codex_cli_status(settings)
    openai_configured = bool(os.environ.get("OPENAI_API_KEY"))
    proxy_url = sanitize_proxy_url(settings.get("proxyUrl", ""))
    proxy_scheme = urlparse(proxy_url).scheme if proxy_url else ""
    auth_detected = codex_cli_auth_detected()

    ready = False
    effective = ""
    next_actions: list[str] = []
    if backend == "local":
        next_actions.append("切换 AI 后端到自动、Codex CLI 或 OpenAI API，才能生成问答、卡片和脑图。")
    elif backend == "codex_cli":
        if cli.get("available"):
            ready = True
            effective = "codex_cli"
            if not auth_detected:
                next_actions.append("已找到 Codex CLI，但未检测到 ~/.codex/auth.json；如果生成失败，请先在本机完成 Codex 登录。")
        else:
            next_actions.append("安装或修复 Codex CLI，或把 AI 后端切换为 OpenAI API。")
    elif backend == "openai_api":
        if openai_configured:
            ready = True
            effective = "openai_api"
        else:
            next_actions.append("在设置页填写 OpenAI Key 后保存，或切换为自动/Codex CLI。")
    else:
        if cli.get("available"):
            ready = True
            effective = "codex_cli"
            if not auth_detected:
                next_actions.append("自动模式会先尝试 Codex CLI；未检测到 ~/.codex/auth.json，若生成失败请先登录 Codex。")
        elif openai_configured:
            ready = True
            effective = "openai_api"
        else:
            next_actions.append("自动模式未找到 Codex CLI，也没有 OpenAI Key；请安装/登录 Codex CLI，或配置 OpenAI Key。")

    if not next_actions and ready:
        next_actions.append("配置看起来可用；可以回到对话页发送一个短问题验证真实模型生成。")

    reply_lines = [
        "AI 后端快速试连完成（不会发送测试 prompt，也不会产生模型 token 消耗）。",
        "",
        f"选择：{ai_backend_label(backend)}",
        f"可尝试生成：{'是' if ready else '否'}",
        f"实际优先后端：{ai_backend_label(effective) if effective else '无'}",
        f"Codex CLI：{'已发现 ' + str(cli.get('path') or '') if cli.get('available') else '未发现'}",
        f"Codex 登录文件：{'已检测到' if auth_detected else '未检测到'}",
        f"OpenAI：{'已配置' if openai_configured else '未配置'}",
        f"代理：{'已配置 ' + proxy_scheme if proxy_scheme else '未配置'}",
        "",
        "下一步：",
    ]
    reply_lines.extend(f"- {item}" for item in next_actions)
    return {
        "ok": True,
        "ready": ready,
        "message": "AI 后端试连完成。" if ready else "AI 后端还不能生成内容。",
        "reply": "\n".join(reply_lines),
        "selectedBackend": backend,
        "selectedBackendLabel": ai_backend_label(backend),
        "effectiveBackend": effective,
        "effectiveBackendLabel": ai_backend_label(effective) if effective else "",
        "codexCli": {
            "available": bool(cli.get("available")),
            "path": str(cli.get("path") or ""),
            "authDetected": auth_detected,
        },
        "openai": {
            "configured": openai_configured,
        },
        "proxy": {
            "configured": bool(proxy_scheme),
            "scheme": proxy_scheme,
        },
        "nextActions": next_actions,
        **ai_status_fields(settings),
    }


def session_key(payload: dict[str, Any]) -> str:
    parts = [
        normalize_topic_id(payload),
        normalize_book_md5(payload),
        str(payload.get("source") or ""),
    ]
    conversation_id = normalize_conversation_id(payload)
    if conversation_id:
        parts.append(conversation_id)
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def safe_session_id(value: Any) -> str:
    raw = str(value or "").strip().lower()
    if re.fullmatch(r"[a-f0-9]{24}", raw):
        return raw
    return ""


def normalize_conversation_id(payload: dict[str, Any]) -> str:
    raw = str(payload.get("conversationId") or payload.get("conversation_id") or "").strip()
    if not raw:
        return ""
    return re.sub(r"[^A-Za-z0-9_.:-]+", "-", raw)[:80]


def session_path(payload: dict[str, Any]) -> Path:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    session_id = safe_session_id(payload.get("sessionId") or payload.get("session_id"))
    if session_id:
        return SESSIONS_DIR / f"{session_id}.json"
    return SESSIONS_DIR / f"{session_key(payload)}.json"


def queue_key(topic_id: str, book_md5: str) -> str:
    raw = f"{topic_id}|{book_md5}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def queue_path(topic_id: str, book_md5: str) -> Path:
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    return QUEUE_DIR / f"{queue_key(topic_id, book_md5)}.jsonl"


def read_queue_lines(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except Exception:
        return []
    records: list[dict[str, Any]] = []
    for line in lines:
        try:
            record = json.loads(line)
        except Exception:
            continue
        if isinstance(record, dict):
            records.append(record)
    return records


def queue_paths_for_topic(topic_id: str, book_md5: str) -> list[Path]:
    if book_md5:
        return [queue_path(topic_id, book_md5)]
    if not topic_id or not QUEUE_DIR.exists():
        return []
    paths: list[Path] = []
    for path in sorted(QUEUE_DIR.glob("*.jsonl")):
        for record in read_queue_lines(path):
            if str(record.get("topicid") or "") == topic_id:
                paths.append(path)
                break
    return paths


def enqueue_command(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "missing topicid"}
    command = payload.get("command") if isinstance(payload.get("command"), dict) else None
    if not command:
        action = str(payload.get("action") or "").strip()
        if action in QUEUE_RAW_ACTIONS:
            command = {
                "rawAction": action,
                "prompt": str(payload.get("prompt") or ""),
                "source": str(payload.get("source") or "queued-raw-action"),
                "message": str(payload.get("message") or f"queued raw action: {action}"),
            }
        else:
            return {"ok": False, "message": f"unsupported queue action: {action or '(empty)'}"}
    if not is_valid_queue_command(command):
        return {"ok": False, "message": "unsupported queue command"}
    record = {
        "id": str(uuid.uuid4()).upper(),
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "topicid": topic_id,
        "bookmd5": book_md5,
        "command": command,
    }
    with queue_path(topic_id, book_md5).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True, "message": "command queued", "queued": record}


def request_pdf_cache(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "请求缓存 PDF 失败：缺少 topicid。"}
    candidates: list[Path] = []

    def add_candidate(path: Path | None) -> None:
        if not path or path.suffix.lower() != ".pdf":
            return
        if path not in candidates:
            candidates.append(path)

    source_pdf, source_error = resolve_pdf_source(payload, book_md5)
    add_candidate(source_pdf)
    for key in ("pdfPath", "documentPath", "sourcePdfPath"):
        raw = str(payload.get(key) or "").strip()
        if raw:
            add_candidate(pdf_path_from_raw_value(raw))
    add_candidate(KNOWN_PDF_PATHS.get(book_md5))
    names = [path.name for path in candidates if path.name]
    names.extend(pdf_filename_candidates(payload_pdf_name_values(payload)))
    for name in list(dict.fromkeys(names)):
        for root in pdf_source_search_roots():
            add_candidate(root / name)

    for candidate in candidates:
        direct_result = cache_pdf_from_source_path(payload, candidate)
        if direct_result:
            return direct_result

    command = {
        "nativeAction": "cache_pdf_from_current_document",
        "message": "请 MN4 插件缓存当前 PDF。",
        "source": str(payload.get("source") or "request_pdf_cache"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    if candidates:
        command["pdfPath"] = str(candidates[0])
        command["documentPath"] = str(candidates[0])
        command["pdfPathCandidates"] = [str(path) for path in candidates]
    elif source_error:
        command["sourceError"] = source_error
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件缓存当前 PDF。",
        "reply": (
            "已把“缓存当前 PDF”命令加入当前 notebook 队列。\n\n"
            "保持该文档在 MarginNote 4 中打开，插件轮询后会由 MN4 进程读取 PDF 并上传到 Companion 缓存。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
        "pdfCache": pdf_cache_progress_payload(topic_id, book_md5),
    }


def request_native_capability_probe(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "刷新 MN 原生能力失败：缺少 topicid。"}
    command = {
        "nativeAction": "probe_native_api_capabilities",
        "message": "请 MN4 插件刷新原生 API 能力探测。",
        "source": str(payload.get("source") or "request_native_capability_probe"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求刷新 MN 原生能力。",
        "reply": (
            "已把“刷新 MN 原生能力”命令加入当前 notebook 队列。\n\n"
            "保持该文档在 MarginNote 4 中打开，插件轮询后会重新上报 nativeApiCapabilities 和 capabilityMatrix。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
        "nativeApiCapabilities": latest_native_api_capabilities(topic_id, book_md5),
    }


def request_web_panel_reload(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "重新加载 Codex 面板失败：缺少 topicid。"}
    command = {
        "nativeAction": "reload_web_panel",
        "message": "请 MN4 插件重新加载 Codex 面板。",
        "source": str(payload.get("source") or "request_web_panel_reload"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求重新加载 Codex 面板。",
        "reply": (
            "已把“重新加载 Codex 面板”命令加入当前 notebook 队列。\n\n"
            "保持该文档在 MarginNote 4 中打开，插件轮询后会关闭并重新打开 Codex 面板，不会退出 MarginNote 4。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
    }


def request_draft_write(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("id") or payload.get("draftId") or ""))[:80]
    if not topic_id:
        return {"ok": False, "message": "写入草稿失败：缺少 topicid。"}
    if not clean_id:
        return {"ok": False, "message": "写入草稿失败：缺少 draftId。"}
    draft = load_draft(clean_id)
    if not draft.get("ok"):
        return draft
    command = {
        "nativeAction": "write_draft",
        "draftId": clean_id,
        "message": "请 MN4 插件写入已确认草稿。",
        "source": str(payload.get("source") or "request_draft_write"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件写入草稿。",
        "reply": (
            "已把“写入草稿”命令加入当前 notebook 队列。\n\n"
            "保持该文档在 MarginNote 4 中打开，插件轮询后会读取草稿并写入当前笔记本。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
        "draft": draft.get("draft", {}),
    }


def latest_runtime_native_ts(status: dict[str, Any]) -> str:
    runtime = status.get("mnRuntime") if isinstance(status.get("mnRuntime"), dict) else {}
    native_ts = str(runtime.get("latestNativeEventTs") or "")
    if native_ts:
        return native_ts
    caps = status.get("nativeApiCapabilities") if isinstance(status.get("nativeApiCapabilities"), dict) else {}
    return str(caps.get("event_ts") or "")


def latest_runtime_web_ts(status: dict[str, Any]) -> str:
    runtime = status.get("mnRuntime") if isinstance(status.get("mnRuntime"), dict) else {}
    return str(runtime.get("latestWebEventTs") or "")


def wait_for_runtime_status_refresh(previous_native_ts: str, wait_seconds: float, previous_web_ts: str = "") -> dict[str, Any]:
    deadline = time.time() + max(0.0, float(wait_seconds or 0))
    latest = status_payload()
    while time.time() < deadline:
        runtime = latest.get("mnRuntime") if isinstance(latest.get("mnRuntime"), dict) else {}
        current_native_ts = latest_runtime_native_ts(latest)
        current_web_ts = latest_runtime_web_ts(latest)
        if (
            runtime.get("ready")
            or (current_native_ts and current_native_ts != previous_native_ts)
            or (current_web_ts and current_web_ts != previous_web_ts)
        ):
            return latest
        time.sleep(0.5)
        latest = status_payload()
    return latest


def classify_doctor_permission_issue(stdout: str, stderr: str) -> dict[str, Any]:
    text = f"{stdout}\n{stderr}"
    markers = [
        "PermissionError",
        "Operation not permitted",
        "permission_denied",
        "Full Disk Access",
    ]
    issue = any(marker in text for marker in markers)
    path_match = re.search(r"['\"]([^'\"]*(?:OneDrive|CloudStorage|MarginNote|QReader)[^'\"]*)['\"]", text)
    return {
        "doctorPermissionIssue": bool(issue),
        "doctorPermissionPath": path_match.group(1) if path_match else "",
    }


def run_doctor_for_runtime_evidence(timeout_seconds: int = 30) -> dict[str, Any]:
    script = ROOT / "doctor.py"
    if not script.exists():
        script = Path(__file__).resolve().with_name("doctor.py")
    if not script.exists():
        return {
            "doctorFound": False,
            "doctorPath": "",
            "doctorReturnCode": None,
            "doctorStdout": "",
            "doctorStderr": "doctor.py not found",
            "doctorPermissionIssue": False,
            "doctorPermissionPath": "",
        }
    try:
        result = subprocess.run(
            [sys.executable or "/usr/bin/python3", str(script)],
            cwd=str(script.parent),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except Exception as exc:
        permission = classify_doctor_permission_issue("", str(exc))
        return {
            "doctorFound": True,
            "doctorPath": str(script),
            "doctorReturnCode": None,
            "doctorStdout": "",
            "doctorStderr": str(exc),
            **permission,
        }
    stdout = result.stdout[-12000:]
    stderr = result.stderr[-4000:]
    permission = classify_doctor_permission_issue(stdout, stderr)
    return {
        "doctorFound": True,
        "doctorPath": str(script),
        "doctorReturnCode": result.returncode,
        "doctorStdout": stdout,
        "doctorStderr": stderr,
        **permission,
    }


def runtime_evidence_dir() -> Path:
    candidates = [
        ONEDRIVE_COMPANION_DIR / "evidence",
        ROOT / "evidence",
    ]
    for directory in candidates:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            return directory
        except Exception:
            continue
    fallback = ROOT / "evidence"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def collect_mn_runtime_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    status_before = status_payload()
    previous_native_ts = latest_runtime_native_ts(status_before)
    previous_web_ts = latest_runtime_web_ts(status_before)
    if topic_id:
        reload_payload = {
            **payload,
            "action": "request_web_panel_reload",
            "topicid": topic_id,
            "notebookid": topic_id,
            "bookmd5": book_md5,
            "docmd5": book_md5,
            "source": str(payload.get("source") or "collect_mn_runtime_evidence"),
        }
        web_panel_reload_result = request_web_panel_reload(reload_payload)
        probe_payload = {
            **payload,
            "action": "request_native_capability_probe",
            "topicid": topic_id,
            "notebookid": topic_id,
            "bookmd5": book_md5,
            "docmd5": book_md5,
            "source": str(payload.get("source") or "collect_mn_runtime_evidence"),
        }
        probe_result = request_native_capability_probe(probe_payload)
    else:
        web_panel_reload_result = {
            "ok": False,
            "message": "缺少 topicid，无法请求 MN4 插件重新加载 Codex 面板；仍会采集当前 Companion 状态。",
        }
        probe_result = {
            "ok": False,
            "message": "缺少 topicid，无法请求 MN4 插件刷新原生能力；仍会采集当前 Companion 状态。",
        }
    try:
        wait_seconds = min(15.0, max(0.0, float(payload.get("waitSeconds", 2))))
    except Exception:
        wait_seconds = 2.0
    status_after = wait_for_runtime_status_refresh(previous_native_ts, wait_seconds, previous_web_ts)
    runtime = status_after.get("mnRuntime") if isinstance(status_after.get("mnRuntime"), dict) else {}
    native_caps = status_after.get("nativeApiCapabilities") if isinstance(status_after.get("nativeApiCapabilities"), dict) else {}
    doctor = run_doctor_for_runtime_evidence()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    evidence_path = runtime_evidence_dir() / f"CodexCompanion-MNRuntimeEvidence-{stamp}.json"
    evidence = {
        "ok": bool(runtime.get("ready")),
        "message": "MN4 runtime evidence collected.",
        "topicid": topic_id,
        "bookmd5": book_md5,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "statusBefore": status_before,
        "webPanelReloadResult": web_panel_reload_result,
        "probeResult": probe_result,
        "statusAfter": status_after,
        "mnRuntime": runtime,
        "nativeApiCapabilities": native_caps,
        "doctor": doctor,
        "nextStep": runtime.get("nextStep") or "重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。",
    }
    evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
    ready_text = "ready" if runtime.get("ready") else "not ready"
    doctor_permission_text = ""
    if doctor.get("doctorPermissionIssue"):
        path = str(doctor.get("doctorPermissionPath") or "OneDrive/MarginNote 相关路径")
        doctor_permission_text = (
            "\n权限诊断：doctor 在 Companion 服务环境中被 macOS 拦截。"
            f"请给 Companion/Python Full Disk Access 后重试。路径：{path}\n"
        )
    return {
        "ok": True,
        "message": "MN4 运行态证据已生成。",
        "reply": (
            "MN4 运行态证据已生成。\n\n"
            f"路径：{evidence_path}\n"
            f"mnRuntime：{ready_text}\n"
            f"nativeApiCapabilities：{'available' if native_caps.get('available') else 'not available'}\n"
            f"doctorReturnCode：{doctor.get('doctorReturnCode')}\n\n"
            f"{doctor_permission_text}"
            f"下一步：{evidence['nextStep']}"
        ),
        "evidencePath": str(evidence_path),
        "mnRuntime": runtime,
        "nativeApiCapabilities": native_caps,
        "webPanelReloadResult": web_panel_reload_result,
        "probeResult": probe_result,
        "doctor": doctor,
        "queue": queue_status_payload(topic_id, book_md5),
    }


def restart_marginnote4(payload: dict[str, Any]) -> dict[str, Any]:
    bundle_id = "QReader.MarginStudy.easy"
    quit_script = f'tell application id "{bundle_id}" to quit'
    try:
        quit_result = subprocess.run(
            ["/usr/bin/osascript", "-e", quit_script],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:
        message = f"请求退出 MarginNote 4 失败：{exc}"
        return {"ok": False, "message": message, "reply": message}
    time.sleep(1.5)
    try:
        open_result = subprocess.run(
            ["/usr/bin/open", "-b", bundle_id],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:
        message = f"请求重新打开 MarginNote 4 失败：{exc}"
        return {
            "ok": False,
            "message": message,
            "reply": message,
            "quitReturnCode": quit_result.returncode,
        }
    ok = quit_result.returncode == 0 and open_result.returncode == 0
    if ok:
        message = "已请求重启 MarginNote 4。"
        reply = "已请求重启 MarginNote 4。应用重新打开后，请重新打开 Codex 面板，再点击“刷新MN能力”。"
    else:
        detail = (quit_result.stderr or open_result.stderr or quit_result.stdout or open_result.stdout or "").strip()
        message = "重启 MarginNote 4 请求未完全成功。"
        reply = (
            f"{message}\n\n"
            f"quit returncode: {quit_result.returncode}\n"
            f"open returncode: {open_result.returncode}\n"
            f"{detail}"
        ).strip()
    append_event(
        {
            "event": "restartMarginNote4Requested",
            "source": str(payload.get("source") or "companion"),
            "extra": {
                "quitReturnCode": quit_result.returncode,
                "openReturnCode": open_result.returncode,
                "ok": ok,
            },
        }
    )
    return {
        "ok": ok,
        "message": message,
        "reply": reply,
        "quitReturnCode": quit_result.returncode,
        "openReturnCode": open_result.returncode,
    }


def release_acceptance_script() -> Path:
    candidates = [
        ROOT / "release_acceptance.py",
        Path(__file__).resolve().with_name("release_acceptance.py"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[-1]


def is_permission_limited_text(text: Any) -> bool:
    value = str(text or "")
    return any(
        marker in value
        for marker in [
            "PermissionError",
            "Operation not permitted",
            "permission_denied",
            "authorization denied",
        ]
    )


def acceptance_permission_limited(report: dict[str, Any], stderr: str = "") -> bool:
    if is_permission_limited_text(stderr):
        return True
    evidence = report.get("evidence") if isinstance(report.get("evidence"), dict) else {}
    for item in evidence.values():
        if isinstance(item, dict) and (
            is_permission_limited_text(item.get("stderr"))
            or is_permission_limited_text(item.get("stdout"))
        ):
            return True
    blockers = report.get("blockers") if isinstance(report.get("blockers"), list) else []
    for blocker in blockers:
        if isinstance(blocker, dict) and is_permission_limited_text(blocker.get("detail")):
            return True
    return False


PREFERRED_LAUNCH_LABEL = "com.codex.paper-companion"
LEGACY_LAUNCH_LABEL = "com.liuwhale.codex-marginnote-assistant"


def full_disk_access_subjects() -> list[dict[str, Any]]:
    subjects: list[dict[str, Any]] = []
    python_path = str(Path(sys.executable or "/usr/bin/python3"))
    python_shim_path = str(Path(shutil.which("python3") or python_path))
    subjects.append(
        {
            "label": "当前 Companion 进程",
            "kind": "process",
            "pid": os.getpid(),
            "path": python_path,
            "note": "如果 Companion 由 LaunchAgent 启动，Full Disk Access 通常需要给这个 Python 运行时。",
        }
    )
    subjects.append(
        {
            "label": "Python 可执行文件",
            "kind": "executable",
            "path": python_shim_path,
            "runtimePath": python_path if python_shim_path != python_path else "",
            "note": "在 Full Disk Access 列表中添加该 Python，或添加启动它的 Terminal/Codex App。",
        }
    )
    for label in [PREFERRED_LAUNCH_LABEL, LEGACY_LAUNCH_LABEL]:
        plist = HOME / f"Library/LaunchAgents/{label}.plist"
        if plist.exists():
            subjects.append(
                {
                    "label": "LaunchAgent plist",
                    "kind": "launchagent",
                    "launchLabel": label,
                    "path": str(plist),
                    "note": "授权后重启 Companion，或重新加载该 LaunchAgent。",
                }
            )
    subjects.append(
        {
            "label": "手动兜底",
            "kind": "manual",
            "path": "/Applications/Utilities/Terminal.app 或当前 Codex App",
            "note": "如果你从终端手动启动 Companion，也要给启动它的应用 Full Disk Access。",
        }
    )
    return subjects


RELEASE_BLOCKER_GROUPS: tuple[tuple[str, set[str]], ...] = (
    (
        "基础包验证",
        {
            "unit_tests",
            "syntax_checks",
            "release_zip_smoke",
            "install_dry_run",
            "release_sha256_manifest",
        },
    ),
    ("MN4 运行态", {"runtime_web_controls", "native_api_matrix"}),
    ("真实功能证据", {"native_visible_highlight"}),
    ("签名与公证", {"release_maintainer_prerequisites", "signed_pkg", "notarized_pkg"}),
    ("跨机器安装", {"cross_machine_install"}),
)


def release_blocker_group_title(name: str) -> str:
    for title, names in RELEASE_BLOCKER_GROUPS:
        if name in names:
            return title
    return "其他"


def group_acceptance_blockers(blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not blockers:
        return []
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in blockers:
        if not isinstance(item, dict):
            continue
        title = release_blocker_group_title(str(item.get("name") or "unknown"))
        grouped.setdefault(title, []).append(item)

    groups: list[dict[str, Any]] = []
    ordered_titles = [title for title, _names in RELEASE_BLOCKER_GROUPS] + ["其他"]
    for title in ordered_titles:
        items = grouped.get(title) or []
        if items:
            groups.append({"title": title, "items": items})
    return groups


def release_recovery_actions(blockers: list[dict[str, Any]], permission_limited: bool = False) -> list[dict[str, str]]:
    blocker_names = {str(item.get("name") or "") for item in blockers if isinstance(item, dict)}
    blocker_detail_text = "\n".join(
        str(item.get("detail") or "")
        for item in blockers
        if isinstance(item, dict)
    ).lower()
    permission_limited = permission_limited or any(
        isinstance(item, dict) and is_permission_limited_text(item.get("detail"))
        for item in blockers
    )
    actions: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(action_id: str, title: str, handler: str = "", action: str = "", description: str = "") -> None:
        if action_id in seen:
            return
        item = {"id": action_id, "title": title}
        if handler:
            item["handler"] = handler
        if action:
            item["action"] = action
        if description:
            item["description"] = description
        actions.append(item)
        seen.add(action_id)

    if permission_limited:
        add(
            "open_full_disk_access_settings",
            "打开权限设置",
            handler="openPermissionSettings",
            description="给 Companion、Python、Terminal/Codex 授权 Full Disk Access 后重新验收。",
        )
    if blocker_names & {"runtime_web_controls", "native_api_matrix"}:
        add(
            "refresh_native_capabilities",
            "刷新MN能力",
            handler="refreshNativeCapabilities",
            description="让当前 MN4 面板重新上报 Web 控件和原生 API 能力。",
        )
        add(
            "collect_mn_runtime_evidence",
            "运行态采证",
            handler="collectRuntimeEvidence",
            description="生成可带入发布验收的 MN4 runtime evidence JSON。",
        )
        if (
            "reload_web_panel" in blocker_detail_text
            or "runtime handler" in blocker_detail_text
            or "旧 handler" in blocker_detail_text
            or "unknown" in blocker_detail_text
        ):
            add(
                "restart_marginnote4",
                "重启MN4",
                handler="restartMarginNote4",
                description="当前运行中的 MN4 handler 已确认过旧；点击后仍会先弹确认框。",
            )
    if "native_visible_highlight" in blocker_names:
        add(
            "diagnose_highlights",
            "高亮状态",
            action="diagnose_highlights",
            description="检查当前数据库里是否已经出现原生高亮证据。",
        )
        add(
            "request_native_highlight_selection",
            "高亮选区",
            action="request_native_highlight_selection",
            description="在 PDF 原文选中文字后，调用 MN4 原生高亮。",
        )
    if blockers:
        add(
            "rerun_release_acceptance",
            "重新验收",
            handler="checkReleaseAcceptance",
            description="在完成上面动作后重新运行发布 gate。",
        )
    return actions


def shell_open_command(path: Path) -> str:
    return f"open {shlex.quote(str(path))}"


def release_evidence_guide(blockers: list[dict[str, Any]]) -> list[dict[str, str]]:
    blocker_names = {str(item.get("name") or "") for item in blockers if isinstance(item, dict)}
    guide: list[dict[str, str]] = []
    seen: set[str] = set()

    def add(
        item_id: str,
        title: str,
        command: str,
        output_hint: str,
        note: str = "",
        blocker: str = "",
    ) -> None:
        if item_id in seen:
            return
        item = {
            "id": item_id,
            "title": title,
            "command": command,
            "outputHint": output_hint,
        }
        if note:
            item["note"] = note
        if blocker:
            item["blocker"] = blocker
        guide.append(item)
        seen.add(item_id)

    if blocker_names & {"runtime_web_controls", "native_api_matrix"}:
        evidence_path = Path("/tmp/codex-mn-runtime-evidence-current.json")
        add(
            "collect_mn_runtime_evidence",
            "采集 MN4 运行态证据",
            shell_open_command(ROOT / "Refresh MN Runtime.command"),
            f"生成 {evidence_path}；随后运行 python3 release_acceptance.py --mn-runtime-evidence {shlex.quote(str(evidence_path))}",
            "先关闭再重新打开 Codex 面板；如果旧 handler 仍不认识 reload_web_panel，再重启 MarginNote 4。",
            "runtime_web_controls",
        )
    if "native_visible_highlight" in blocker_names:
        add(
            "collect_native_highlight_evidence",
            "采集真实可见高亮证据",
            shell_open_command(ROOT / "Collect Native Highlight Evidence.command"),
            "在桌面生成 CodexCompanion-native-highlight-evidence-*.json；随后运行 python3 release_acceptance.py --native-highlight-evidence <json>",
            "优先在设置页点“高亮采证”，回到 MN4 的 PDF 原文重新选中一小段文字，确认原文中确实可见高亮；也可用本命令生成结构化证据。",
            "native_visible_highlight",
        )
    if "release_sha256_manifest" in blocker_names:
        add(
            "rebuild_release_manifest",
            "重建发布包和 SHA256 manifest",
            "python3 package_release.py && python3 build_pkg.py",
            "更新 release/SHA256SUMS.txt 并同步到 OneDrive；随后重新运行 python3 release_acceptance.py --json",
            "manifest 失败通常表示 zip/pkg 重新生成后未同步或 hash 不一致。",
            "release_sha256_manifest",
        )
    if "signed_pkg" in blocker_names:
        add(
            "build_signed_package",
            "构建 Developer ID 签名 pkg",
            shell_open_command(ROOT / "Build Signed Package.command"),
            "生成/更新 release/CodexCompanion-0.4.24-latest.pkg；随后重新运行 python3 release_acceptance.py --json",
            "需要 Keychain 里有 Developer ID Installer 证书；没有证书时此步骤只能保持阻塞。",
            "signed_pkg",
        )
    if "notarized_pkg" in blocker_names:
        add(
            "notarize_package",
            "提交 Apple 公证并 stapler",
            shell_open_command(ROOT / "Notarize Package.command"),
            "更新已公证并 stapled 的 latest.pkg；随后重新运行 python3 release_acceptance.py --json",
            "需要先配置 notarytool 凭据，例如 xcrun notarytool store-credentials。",
            "notarized_pkg",
        )
    if "cross_machine_install" in blocker_names:
        add(
            "collect_cross_machine_evidence",
            "采集跨机器/跨账号安装证据",
            shell_open_command(ROOT / "Collect Cross-Machine Evidence.command"),
            "在桌面生成 CodexCompanion-cross-machine-evidence-*.json；带回主机器后运行 python3 release_acceptance.py --cross-machine-evidence <json>",
            "应在另一个 macOS 用户或另一台机器安装 latest zip/pkg 后运行，不能用本机同一环境代替。",
            "cross_machine_install",
        )
    return guide


def summarize_acceptance_blockers(blockers: list[dict[str, Any]], limit: int = 6) -> str:
    if not blockers:
        return "当前发布验收没有阻塞项。"
    lines: list[str] = []
    rendered = 0
    for group in group_acceptance_blockers(blockers):
        if rendered >= limit:
            break
        title = str(group.get("title") or "其他")
        items = group.get("items") if isinstance(group.get("items"), list) else []
        if not items:
            continue
        lines.append(title)
        for item in items:
            if rendered >= limit:
                break
            name = str(item.get("name") or "unknown")
            detail = str(item.get("detail") or "").strip()
            lines.append(f"- {name}: {detail}")
            if is_permission_limited_text(detail):
                lines.append("  下一步：给 Companion 服务使用的 Python/终端 Full Disk Access，然后重新运行发布验收。")
            actions = item.get("nextActions") if isinstance(item.get("nextActions"), list) else []
            for action in actions[:2]:
                action_text = str(action or "").strip()
                if action_text:
                    lines.append(f"  下一步：{action_text}")
            rendered += 1
    if len(blockers) > rendered:
        lines.append(f"- 另有 {len(blockers) - rendered} 个阻塞项，查看 JSON 报告。")
    return "\n".join(lines)


def release_acceptance_env() -> dict[str, str]:
    env = dict(os.environ)
    extra_paths = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
        str(HOME / ".npm-global/bin"),
    ]
    existing = env.get("PATH", "")
    parts = [path for path in extra_paths if path]
    if existing:
        parts.append(existing)
    env["PATH"] = ":".join(parts)
    return env


def release_acceptance_summary(payload: dict[str, Any]) -> dict[str, Any]:
    script = release_acceptance_script()
    if not script.exists():
        message = "找不到 release_acceptance.py，无法运行发布验收。"
        return {"ok": False, "message": message, "reply": message, "releaseAcceptance": None}
    try:
        result = subprocess.run(
            [sys.executable or "/usr/bin/python3", str(script), "--json"],
            cwd=str(script.parent),
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
            env=release_acceptance_env(),
        )
    except Exception as exc:
        message = f"发布验收执行失败：{exc}"
        return {"ok": False, "message": message, "reply": message, "releaseAcceptance": None}
    try:
        report = json.loads(result.stdout or "{}")
    except Exception:
        report = {}
    if not isinstance(report, dict):
        report = {}
    if not report:
        stderr = result.stderr[-2000:] if result.stderr else ""
        stdout = result.stdout[-2000:] if result.stdout else ""
        detail = (stderr or stdout or "release_acceptance.py did not return JSON").strip()
        message = "发布验收报告解析失败。"
        return {
            "ok": False,
            "message": message,
            "reply": f"{message}\n\n{detail}",
            "releasable": False,
            "blockerCount": 0,
            "blockers": [],
            "releaseAcceptance": None,
            "acceptanceReturnCode": result.returncode,
            "acceptancePath": str(script),
        }
    blockers = report.get("blockers") if isinstance(report.get("blockers"), list) else []
    blockers = [item for item in blockers if isinstance(item, dict)]
    blocker_groups = group_acceptance_blockers(blockers)
    releasable = bool(report.get("releasable"))
    permission_limited = acceptance_permission_limited(report, result.stderr)
    recovery_actions = release_recovery_actions(blockers, permission_limited)
    evidence_guide = release_evidence_guide(blockers)
    permission_subjects = full_disk_access_subjects() if permission_limited else []
    status_text = "PASS" if releasable else "BLOCKED"
    permission_hint = ""
    if permission_limited:
        subject_lines = [
            f"- {item.get('label')}: {item.get('path') or ''}"
            + (f" (PID {item.get('pid')})" if item.get("pid") else "")
            for item in permission_subjects[:3]
        ]
        permission_hint = (
            "权限提示：当前 Companion/LaunchAgent 运行环境被 macOS 隐私权限限制。"
            "请给下面对象 Full Disk Access 后再试。\n"
            + "\n".join(subject_lines)
            + "\n\n"
        )
    reply = (
        f"发布验收：{status_text}\n"
        f"阻塞项：{len(blockers)}\n\n"
        f"{permission_hint}"
        f"{summarize_acceptance_blockers(blockers)}"
    )
    if result.stderr.strip():
        reply += "\n\nstderr:\n" + result.stderr[-1200:]
    return {
        "ok": True,
        "message": f"发布验收：{status_text}，阻塞项 {len(blockers)}。",
        "reply": reply,
        "releasable": releasable,
        "blockerCount": len(blockers),
        "blockers": blockers,
        "blockerGroups": blocker_groups,
        "recoveryActions": recovery_actions,
        "evidenceGuide": evidence_guide,
        "permissionLimited": permission_limited,
        "permissionSubjects": permission_subjects,
        "releaseAcceptance": report,
        "acceptanceReturnCode": result.returncode,
        "acceptancePath": str(script),
    }


def single_document_acceptance_script() -> Path:
    return Path(__file__).resolve().with_name("single_document_acceptance.py")


def load_single_document_acceptance_module() -> Any:
    script = single_document_acceptance_script()
    if not script.exists():
        return None
    spec = importlib.util.spec_from_file_location("codex_mn_single_document_acceptance_runtime", script)
    if not spec or not spec.loader:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_jsonl_file(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    rows: list[dict[str, Any]] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def load_single_document_action_results(path_text: str = "") -> list[dict[str, Any]]:
    path = Path(path_text).expanduser() if path_text else ROOT / "release/evidence/action-results.jsonl"
    return read_jsonl_file(path)


def latest_native_highlight_evidence(path_text: str = "") -> dict[str, Any]:
    if path_text:
        data = read_json_file(Path(path_text).expanduser(), {})
        return data if isinstance(data, dict) else {}
    candidates: list[Path] = []
    for directory in [ROOT / "release/evidence", ROOT / "release", HOME / "Desktop"]:
        if not directory.exists():
            continue
        for pattern in [
            "codex-companion-native-highlight-evidence-*.json",
            "CodexCompanion-native-highlight-evidence-*.json",
            "native-highlight-evidence*.json",
        ]:
            candidates.extend(path for path in directory.glob(pattern) if path.is_file())
    candidates.sort(key=lambda path: path.stat().st_mtime if path.exists() else 0, reverse=True)
    for candidate in candidates:
        data = read_json_file(candidate, {})
        if isinstance(data, dict) and data:
            return data
    return {}


def summarize_single_document_acceptance(report: dict[str, Any], limit: int = 15) -> str:
    checks = report.get("checks") if isinstance(report.get("checks"), list) else []
    lines: list[str] = []
    for check in checks[:limit]:
        if not isinstance(check, dict):
            continue
        status = str(check.get("status") or "BLOCK")
        label = str(check.get("label") or check.get("id") or "check")
        detail = str(check.get("detail") or "").strip()
        lines.append(f"- {status} {label}: {detail}")
        if status != "PASS":
            actions = check.get("nextActions") if isinstance(check.get("nextActions"), list) else []
            for action in actions[:1]:
                action_text = str(action or "").strip()
                if action_text:
                    lines.append(f"  下一步：{action_text}")
    if len(checks) > limit:
        lines.append(f"- 另有 {len(checks) - limit} 项检查，查看 JSON 详情。")
    return "\n".join(lines)


def single_document_acceptance_summary(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id or not book_md5:
        message = "本文档验收需要当前 MarginNote 文档的 topicid/bookmd5。请先打开目标 PDF 并点“刷新”。"
        return {
            "ok": False,
            "message": message,
            "reply": message,
            "singleDocumentReady": False,
            "singleDocumentBlockerCount": 0,
            "singleDocumentAcceptance": None,
        }
    module = load_single_document_acceptance_module()
    if module is None:
        message = "找不到 single_document_acceptance.py，无法运行本文档验收。"
        return {
            "ok": False,
            "message": message,
            "reply": message,
            "singleDocumentReady": False,
            "singleDocumentBlockerCount": 0,
            "singleDocumentAcceptance": None,
        }
    try:
        report = module.evaluate_single_document_acceptance(
            topicid=topic_id,
            bookmd5=book_md5,
            events=read_jsonl_file(EVENTS_PATH),
            action_results=load_single_document_action_results(str(payload.get("actionResultsPath") or "")),
            native_highlight_evidence=latest_native_highlight_evidence(str(payload.get("nativeHighlightEvidencePath") or "")),
        )
    except Exception as exc:
        message = f"本文档验收执行失败：{exc}"
        return {
            "ok": False,
            "message": message,
            "reply": message,
            "singleDocumentReady": False,
            "singleDocumentBlockerCount": 0,
            "singleDocumentAcceptance": None,
        }
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    blocked = int(summary.get("blocked") or 0)
    passed = int(summary.get("passed") or 0)
    total = int(summary.get("total") or 0)
    ready = bool(report.get("ok"))
    status_text = "PASS" if ready else "BLOCK"
    reply = (
        f"本文档验收：{status_text}\n"
        f"文档：topicid={topic_id} / bookmd5={book_md5}\n"
        f"通过：{passed}/{total}，阻塞项：{blocked}\n\n"
        f"{summarize_single_document_acceptance(report)}"
    )
    return {
        "ok": True,
        "message": f"本文档验收：{status_text}，阻塞项 {blocked}。",
        "reply": reply,
        "singleDocumentReady": ready,
        "singleDocumentBlockerCount": blocked,
        "singleDocumentPassedCount": passed,
        "singleDocumentTotalCount": total,
        "singleDocumentNextActions": report.get("nextActions") if isinstance(report.get("nextActions"), list) else [],
        "singleDocumentAcceptance": report,
    }


def latest_scoped_plugin_event(
    event_names: set[str],
    topic_id: str = "",
    book_md5: str = "",
    limit: int = 800,
) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for item in read_recent_events(limit):
        if str(item.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(item.get("event") or "") not in event_names:
            continue
        if topic_id and str(item.get("topicid") or item.get("notebookid") or "") not in {"", topic_id}:
            continue
        if book_md5 and str(item.get("bookmd5") or item.get("docmd5") or "") not in {"", book_md5}:
            continue
        matches.append(item)
    return matches[-1] if matches else None


def check_status_by_id(report: dict[str, Any], check_id: str) -> str:
    checks = report.get("checks") if isinstance(report.get("checks"), list) else []
    for item in checks:
        if isinstance(item, dict) and str(item.get("id") or "") == check_id:
            return str(item.get("status") or "BLOCK")
    return "BLOCK"


def native_highlight_wizard_status(payload: dict[str, Any], queued_result: dict[str, Any] | None = None) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    report_result = single_document_acceptance_summary(payload)
    report = report_result.get("singleDocumentAcceptance") if isinstance(report_result.get("singleDocumentAcceptance"), dict) else {}
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    blocked_checks = [
        str(item.get("id") or "")
        for item in (report.get("checks") if isinstance(report.get("checks"), list) else [])
        if isinstance(item, dict) and str(item.get("status") or "") != "PASS"
    ]
    visible_ready = check_status_by_id(report, "native_highlight_visible") == "PASS"
    popup_ready = check_status_by_id(report, "selection_popup_highlight") == "PASS"
    latest_event = latest_scoped_plugin_event(
        {
            "nativeHighlightSelectionPosted",
            "nativeHighlightSelectionFailed",
            "nativeHighlightNextSelectionArmed",
            "nativeHighlightNextSelectionConsumed",
            "nativeHighlightNextSelectionPollStarted",
            "nativeHighlightNextSelectionPollObserved",
            "nativeHighlightNextSelectionPollExpired",
            "selectionPopupHighlightObserverRegistered",
            "selectionPopupHighlightObserverFailed",
            "selectionPopupHighlightObserverUnregistered",
            "selectionPopupHighlightObserverUnregisterFailed",
            "selectionPopupHighlightNotificationObserved",
            "selectionPopupHighlightNotificationSkipped",
            "selectionPopupHighlightMenuInstalled",
            "selectionPopupHighlightMenuSkipped",
            "selectionPopupHighlightMenuFailed",
        },
        topic_id,
        book_md5,
    )
    event_name = str((latest_event or {}).get("event") or "")
    latest_event_extra = (latest_event or {}).get("extra")
    latest_event_extra = latest_event_extra if isinstance(latest_event_extra, dict) else {}
    latest_event_epoch = event_epoch(latest_event)
    latest_event_age_seconds = int(max(0, time.time() - latest_event_epoch)) if latest_event_epoch > 0 else 0
    waiting_event_expired = (
        event_name in {"nativeHighlightNextSelectionArmed", "nativeHighlightNextSelectionConsumed"}
        and latest_event_age_seconds > NATIVE_HIGHLIGHT_WIZARD_TIMEOUT_SECONDS
    )
    if visible_ready and popup_ready:
        stage = "complete"
        instruction = "原生高亮和 PDF 选区菜单证据已通过；可以重新运行本文档验收和发布验收。"
    elif waiting_event_expired:
        stage = "expired"
        instruction = "本次高亮采证等待 PDF 选区已超时。请点击“高亮采证”重新启动，然后在 90 秒内回到 PDF 原文重新选中一小段文字。"
    elif event_name in {"nativeHighlightNextSelectionArmed", "nativeHighlightNextSelectionConsumed"}:
        stage = "waiting_selection"
        instruction = "请回到 PDF 原文，重新选中一小段文字；插件会主动轮询当前 PDF 选区，并在可用时自动调用 MN4 原生高亮。"
    elif event_name == "nativeHighlightNextSelectionPollStarted":
        stage = "waiting_selection"
        instruction = "插件正在主动轮询当前 PDF 选区。请回到 PDF 原文重新选中一小段文字；即使 MN4 没弹出选区菜单，插件也会尝试捕获选区并高亮。"
    elif event_name == "nativeHighlightNextSelectionPollObserved":
        stage = "selection_observed"
        instruction = "主动轮询已观察到 PDF 选区，正在等待同一文档的原生高亮和可见高亮证据通过。"
    elif event_name == "nativeHighlightNextSelectionPollExpired":
        stage = "expired"
        instruction = "本次主动轮询 PDF 选区已超时。请点击“高亮采证”重新启动，然后在 90 秒内回到 PDF 原文重新选中一小段文字。"
    elif event_name == "nativeHighlightSelectionFailed":
        stage = "failed"
        instruction = "最近一次原生高亮失败。请刷新 MN 能力，确认 PDF 已打开，再重新启动高亮采证。"
    elif event_name == "nativeHighlightSelectionPosted":
        stage = "verifying"
        instruction = "已收到原生高亮 posted 事件，正在等待同一文档的 ZHIGHLIGHTS 和选区菜单证据通过。"
    elif event_name == "selectionPopupHighlightNotificationObserved":
        stage = "selection_observed"
        instruction = "MN4 已收到 PDF 选区通知，正在检查弹出菜单和原生高亮证据；如果仍未通过，请从同一 PDF 重新选中一小段原文。"
    elif event_name == "selectionPopupHighlightNotificationSkipped":
        stage = "selection_diagnostic"
        reason = str(latest_event_extra.get("reason") or "")
        if reason == "outside-window":
            instruction = "MN4 已收到 PDF 选区通知，但插件窗口过滤未通过。请保持同一 notebook/PDF 窗口打开，点击“高亮采证”后在原文重新选中一小段文字。"
        else:
            instruction = f"MN4 已收到 PDF 选区通知，但插件跳过了处理：{reason or 'unknown'}。请重新打开目标文档后再采证。"
    elif event_name == "selectionPopupHighlightObserverRegistered":
        stage = "waiting_selection"
        instruction = "PDF 选区 observer 已注册，但还没有收到 PDF 选区通知。请回到同一篇 PDF 原文，重新选中一小段文字并等待选区菜单出现。"
    elif event_name == "selectionPopupHighlightObserverFailed":
        stage = "selection_diagnostic"
        instruction = "PDF 选区 observer 注册失败。请重新打开 notebook 或重启 MarginNote 4 后再采证；如果反复失败，需要按 observer 错误修插件适配。"
    elif event_name in {"selectionPopupHighlightObserverUnregistered", "selectionPopupHighlightObserverUnregisterFailed"}:
        stage = "selection_diagnostic"
        instruction = "PDF 选区 observer 当前不是稳定注册状态。请重新打开目标 notebook 后再点击“高亮采证”。"
    elif event_name == "selectionPopupHighlightMenuSkipped":
        stage = "selection_diagnostic"
        reason = str(latest_event_extra.get("reason") or "")
        if reason == "missing-selection-text":
            instruction = "MN4 已触发选区菜单链路，但没有拿到可用选区文本。请不要在 Web 面板里选字，回到 PDF 原文重新框选一小段文字。"
        elif reason == "missing-popup-menu":
            instruction = "MN4 已拿到选区文本，但当前没有可追加的选区弹出菜单。请重新选中 PDF 原文，等待系统弹出菜单出现后再点 Codex 高亮入口。"
        else:
            instruction = f"MN4 选区菜单入口被跳过：{reason or 'unknown'}。请重新选中 PDF 原文后再采证。"
    elif event_name == "selectionPopupHighlightMenuFailed":
        stage = "selection_diagnostic"
        reason = str(latest_event_extra.get("reason") or "")
        instruction = f"MN4 选区菜单入口创建失败：{reason or 'unknown'}。请刷新 MN 能力采证；如果反复出现，需要按此事件修插件适配。"
    elif event_name == "selectionPopupHighlightMenuInstalled":
        stage = "verifying"
        instruction = "PDF 选区菜单入口已经安装，正在等待同一文档的原生高亮和可见高亮证据通过。"
    else:
        stage = "ready"
        instruction = "点击“高亮采证”后，回到 PDF 原文重新选中一小段文字。"
    if queued_result and queued_result.get("ok"):
        stage = "waiting_selection"
        instruction = "已请求 MN4 高亮当前或下一次 PDF 选区。请回到 PDF 原文，重新选中一小段文字。"
    wizard = {
        "stage": stage,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "timeoutSeconds": NATIVE_HIGHLIGHT_WIZARD_TIMEOUT_SECONDS,
        "instruction": instruction,
        "visibleHighlightReady": visible_ready,
        "selectionPopupReady": popup_ready,
        "blockedChecks": [item for item in blocked_checks if item],
        "latestEvent": latest_event or {},
        "latestEventAgeSeconds": latest_event_age_seconds,
        "singleDocumentSummary": summary,
    }
    message = f"高亮采证：{stage}"
    reply = (
        f"高亮采证：{stage}\n"
        f"文档：topicid={topic_id or '(missing)'} / bookmd5={book_md5 or '(missing)'}\n"
        f"原生可见高亮：{'PASS' if visible_ready else 'BLOCK'}\n"
        f"选区菜单：{'PASS' if popup_ready else 'BLOCK'}\n\n"
        f"{instruction}"
    )
    result = {
        "ok": True,
        "message": message,
        "reply": reply,
        "nativeHighlightWizard": wizard,
        "singleDocumentAcceptance": report,
        "singleDocumentReady": bool(report.get("ok")),
        "singleDocumentBlockerCount": int(summary.get("blocked") or 0),
        "singleDocumentPassedCount": int(summary.get("passed") or 0),
        "singleDocumentTotalCount": int(summary.get("total") or 0),
    }
    if queued_result:
        result["queued"] = queued_result.get("queued")
        result["queue"] = queued_result.get("queue")
    return result


def start_native_highlight_wizard(payload: dict[str, Any]) -> dict[str, Any]:
    queued_result = request_native_highlight_selection(
        {
            **payload,
            "source": str(payload.get("source") or "native_highlight_wizard_start"),
        }
    )
    if not queued_result.get("ok"):
        return queued_result
    return native_highlight_wizard_status(payload, queued_result)


def request_native_highlight_selection(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "请求原生高亮失败：缺少 topicid。"}
    selection = str(payload.get("selectionText") or payload.get("selectedText") or payload.get("prompt") or "").strip()
    command = {
        "nativeAction": "highlight_current_selection",
        "message": "请 MN4 插件等待下一次 PDF 选区并创建原生高亮。",
        "source": str(payload.get("source") or "request_native_highlight_selection"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "selectionText": selection,
        "armIfMissingSelection": True,
        "preferNextSelection": True,
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件等待下一次 PDF 选区高亮。",
        "reply": (
            "已把“高亮下一次 PDF 选区”命令加入当前 notebook 队列，会先进入等待模式。\n\n"
            "这条路线使用 MarginNote 官方 Addon API 的 `documentController.highlightFromSelection()`；"
            "如果当前 PDF 里仍保留有效选区，会立即尝试创建 MN4 原生高亮；"
            "如果 Web 面板点击导致选区丢失，则先进入等待模式，回到 PDF 后重新选中文字即可触发。"
            "整个过程不会直接写 SQLite，也不会修改原始 PDF 文件。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
    }


def web_busy_queue_response_if_needed(payload: dict[str, Any], action: str) -> dict[str, Any] | None:
    if action not in WEB_DIRECT_BUSY_ACTIONS:
        return None
    if str(payload.get("source") or "") != WEB_PANEL_SOURCE:
        return None
    if payload.get("_queue_raw") is True:
        return None
    if web_busy_status().get("busy"):
        if truthy_payload_flag(payload.get("_web_run_owner")):
            update_web_busy(True)
            return None
        queued_payload = dict(payload)
        queued_payload["_queue_raw"] = True
        queued_payload["message"] = str(payload.get("message") or "queued from web busy lock")
        result = enqueue_command(queued_payload)
        if result.get("ok"):
            result["queued_due_to_web_busy"] = True
            result["message"] = f"当前已有任务运行，已自动加入队列：{action}。"
            result["reply"] = "已加入队列，上一个任务结束后会由 MN4 轮询自动执行。"
        return result
    update_web_busy(True)
    return None


def poll_commands(topic_id: str, book_md5: str) -> dict[str, Any]:
    paths = queue_paths_for_topic(topic_id, book_md5)
    if not paths:
        return {"ok": True, "pending": 0, "commands": []}
    commands: list[dict[str, Any]] = []
    for path in paths:
        for record in read_queue_lines(path):
            if str(record.get("topicid") or "") != topic_id:
                continue
            if book_md5 and str(record.get("bookmd5") or "") != book_md5:
                continue
            command = record.get("command") if isinstance(record, dict) else None
            if not is_valid_queue_command(command):
                continue
            command["_queue_id"] = str(record.get("id") or "")
            commands.append(command)
    if web_busy_status().get("busy"):
        return {
            "ok": True,
            "pending": len(commands),
            "hasCommand": False,
            "command": None,
            "commands": [],
            "blocked": "web_busy",
        }
    return {
        "ok": True,
        "pending": len(commands),
        "hasCommand": bool(commands),
        "command": commands[0] if commands else None,
        "commands": commands[:8],
    }


def ack_commands(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    ack_ids = payload.get("ids")
    if isinstance(ack_ids, str):
        ack_set = {ack_ids}
    elif isinstance(ack_ids, list):
        ack_set = {str(item) for item in ack_ids if item}
    else:
        ack_set = set()
    if not topic_id or not ack_set:
        return {"ok": False, "message": "missing topicid or ids"}
    paths = queue_paths_for_topic(topic_id, book_md5)
    if not paths:
        return {"ok": True, "message": "queue already empty", "removed": 0}
    removed = 0
    remaining = 0
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception as exc:
            return {"ok": False, "message": f"ack read failed: {exc}"}
        kept: list[str] = []
        for line in lines:
            try:
                record = json.loads(line)
            except Exception:
                kept.append(line)
                continue
            if (
                str(record.get("topicid") or "") == topic_id
                and (not book_md5 or str(record.get("bookmd5") or "") == book_md5)
                and str(record.get("id") or "") in ack_set
            ):
                removed += 1
            else:
                kept.append(line)
        remaining += len(kept)
        if kept:
            path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        else:
            try:
                path.unlink()
            except FileNotFoundError:
                pass
    return {"ok": True, "message": "ack recorded", "removed": removed, "remaining": remaining}


def load_history(payload: dict[str, Any]) -> list[dict[str, str]]:
    path = session_path(payload)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    history = data.get("history") if isinstance(data, dict) else None
    if not isinstance(history, list):
        return []
    clean: list[dict[str, str]] = []
    for item in history[-16:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        content = str(item.get("content") or "")
        if role in {"user", "assistant"} and content:
            clean.append({"role": role, "content": content})
    return clean


def conversation_title_from_history(history: list[dict[str, str]]) -> str:
    for item in history:
        if item.get("role") == "user":
            text = re.sub(r"\s+", " ", str(item.get("content") or "")).strip()
            if text:
                return text[:40]
    return "新对话"


def conversation_last_message(history: list[dict[str, str]]) -> str:
    for item in reversed(history):
        text = re.sub(r"\s+", " ", str(item.get("content") or "")).strip()
        if text:
            return text[:80]
    return ""


def read_conversation_file(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    history = data.get("history")
    if not isinstance(history, list):
        history = []
    clean_history: list[dict[str, str]] = []
    for item in history[-16:]:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role") or "")
        content = str(item.get("content") or "")
        if role in {"user", "assistant"} and content:
            clean_history.append({"role": role, "content": content})
    topic_id = str(data.get("topicid") or "")
    book_md5 = str(data.get("bookmd5") or "")
    conversation_id = str(data.get("conversationId") or "")
    title = str(data.get("title") or conversation_title_from_history(clean_history) or "新对话")
    updated_at = str(data.get("updated_at") or "")
    return {
        "sessionId": path.stem,
        "conversationId": conversation_id,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "source": str(data.get("source") or ""),
        "title": title,
        "updatedAt": updated_at,
        "messageCount": len(clean_history),
        "lastMessage": conversation_last_message(clean_history),
        "history": clean_history,
    }


def conversation_matches_payload(item: dict[str, Any], payload: dict[str, Any]) -> bool:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if topic_id and str(item.get("topicid") or "") != topic_id:
        return False
    if book_md5 and str(item.get("bookmd5") or "") != book_md5:
        return False
    return True


def conversation_summary(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "sessionId": item.get("sessionId") or "",
        "conversationId": item.get("conversationId") or "",
        "topicid": item.get("topicid") or "",
        "bookmd5": item.get("bookmd5") or "",
        "title": item.get("title") or "新对话",
        "updatedAt": item.get("updatedAt") or "",
        "messageCount": int(item.get("messageCount") or 0),
        "lastMessage": item.get("lastMessage") or "",
    }


def conversation_payload_for_new(payload: dict[str, Any]) -> dict[str, Any]:
    conversation_id = str(uuid.uuid4()).upper()
    derived = {**payload, "conversationId": conversation_id}
    return {
        "sessionId": session_key(derived),
        "conversationId": conversation_id,
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "title": "新对话",
        "updatedAt": "",
        "messageCount": 0,
        "lastMessage": "",
    }


def list_conversations(payload: dict[str, Any]) -> dict[str, Any]:
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    for path in SESSIONS_DIR.glob("*.json"):
        item = read_conversation_file(path)
        if item and conversation_matches_payload(item, payload):
            items.append(item)
    items.sort(key=lambda item: str(item.get("updatedAt") or ""), reverse=True)
    summaries = [conversation_summary(item) for item in items]
    return {
        "ok": True,
        "message": f"已读取历史对话：{len(summaries)} 条。",
        "conversations": summaries,
        "conversation_count": len(summaries),
    }


def new_conversation(payload: dict[str, Any]) -> dict[str, Any]:
    conversation = conversation_payload_for_new(payload)
    return {
        "ok": True,
        "message": "已创建新对话。",
        "conversation": conversation,
        "history": [],
    }


def load_conversation(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = safe_session_id(payload.get("sessionId") or payload.get("session_id"))
    if not session_id:
        return {"ok": False, "message": "加载历史对话失败：缺少有效 sessionId。"}
    path = SESSIONS_DIR / f"{session_id}.json"
    item = read_conversation_file(path)
    if not item:
        return {"ok": False, "message": "加载历史对话失败：会话不存在。"}
    if not conversation_matches_payload(item, payload):
        return {"ok": False, "message": "加载历史对话失败：该会话不属于当前文档。"}
    return {
        "ok": True,
        "message": "已加载历史对话。",
        "conversation": conversation_summary(item),
        "history": item["history"],
    }


def delete_conversation(payload: dict[str, Any]) -> dict[str, Any]:
    session_id = safe_session_id(payload.get("sessionId") or payload.get("session_id"))
    if not session_id:
        return {"ok": False, "message": "删除历史对话失败：缺少有效 sessionId。"}
    path = SESSIONS_DIR / f"{session_id}.json"
    item = read_conversation_file(path)
    if not item:
        return {"ok": False, "message": "删除历史对话失败：会话不存在。"}
    if not conversation_matches_payload(item, payload):
        return {"ok": False, "message": "删除历史对话失败：该会话不属于当前文档。"}
    try:
        path.unlink()
    except Exception as exc:
        return {"ok": False, "message": f"删除历史对话失败：{exc}"}
    return {"ok": True, "message": "历史对话已删除。", "deleted": session_id}


def save_history(payload: dict[str, Any], history: list[dict[str, str]]) -> None:
    path = session_path(payload)
    conversation_id = normalize_conversation_id(payload)
    title = conversation_title_from_history(history)
    body = {
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "source": str(payload.get("source") or ""),
        "conversationId": conversation_id,
        "title": title,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "history": history[-16:],
    }
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")


def append_history(payload: dict[str, Any], user_text: str, assistant_text: str) -> None:
    history = load_history(payload)
    if user_text:
        history.append({"role": "user", "content": user_text[:5000]})
    if assistant_text:
        history.append({"role": "assistant", "content": assistant_text[:5000]})
    save_history(payload, history)


STALE_MISSING_PDF_HISTORY_RE = re.compile(
    r"(没有传入可解析的本地\s*PDF\s*路径|当前\s*MN\s*文档没有可解析|全文内容没有被读取到|拿不到.*pdfPath|pdfPath.*拿不到)",
    re.I,
)


def history_for_model(payload: dict[str, Any], model_input: str) -> list[dict[str, str]]:
    history = load_history(payload)[-8:]
    if "当前文档全文检索片段" not in model_input:
        return history
    return [item for item in history if not STALE_MISSING_PDF_HISTORY_RE.search(str(item.get("content") or ""))]


def history_payload(payload: dict[str, Any]) -> dict[str, Any]:
    history = load_history(payload)
    return {
        "ok": True,
        "message": f"已读取历史对话：{len(history)} 条。",
        "history": history,
        "history_count": len(history),
        "session": session_key(payload),
    }


def clear_history(payload: dict[str, Any]) -> dict[str, Any]:
    path = session_path(payload)
    removed = 0
    try:
        if path.exists():
            path.unlink()
            removed = 1
    except Exception as exc:
        return {"ok": False, "message": f"清空历史失败：{exc}", "removed": removed}
    return {"ok": True, "message": "历史对话已清空。", "removed": removed, "history": []}


def open_external_url(payload: dict[str, Any]) -> dict[str, Any]:
    url = str(payload.get("url") or "").strip()
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"ok": False, "message": "只允许打开 http/https 链接。", "url": url}
    try:
        result = subprocess.run(
            ["/usr/bin/open", url],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except Exception as exc:
        return {"ok": False, "message": f"打开下载页失败：{exc}", "url": url}
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        return {"ok": False, "message": f"打开下载页失败：{detail or result.returncode}", "url": url}
    return {"ok": True, "message": "已打开下载页面。", "url": url}


def generation_action_label(action: str) -> str:
    return {
        "chat": "对话",
        "explain_selection": "解释选区",
        "goal_run": "执行目标",
        "generate_card": "生成卡片",
        "generate_mindmap": "生成脑图",
        "generate_full_reading": "完整精读",
        "expand_node": "补脑图",
        "reorganize_mindmap": "整理脑图",
    }.get(action, action or "任务")


def dispatch_generation_action(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    if action == "goal_run":
        return run_goal(payload)
    if action == "generate_full_reading":
        return generate_full_reading(payload)
    if action == "generate_card":
        return generate_card(payload)
    if action == "generate_mindmap":
        return generate_mindmap(payload)
    if action == "expand_node":
        return expand_node(payload)
    if action == "reorganize_mindmap":
        return reorganize_mindmap(payload)
    if action in {"chat", "explain_selection"}:
        result = chat(payload)
        if action == "explain_selection":
            result["message"] = str(result.get("message") or "").replace("对话回复", "选中文本解释")
        return result
    return {"ok": False, "message": f"未知生成动作：{action or '(empty)'}"}


def handle_generation_action(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    queue_id = str(payload.get("_queue_id") or payload.get("queue_id") or "")
    request_id = str(payload.get("_request_id") or payload.get("requestId") or "")
    label = generation_action_label(action)
    update_run_state(
        True,
        action=action,
        stage="正在执行",
        detail=f"{label}已开始；正在等待模型或 MarginNote 上下文处理返回。",
        topicid=topic_id,
        bookmd5=book_md5,
        queue_id=queue_id,
        request_id=request_id,
        source=str(payload.get("source") or ""),
    )
    try:
        result = dispatch_generation_action(action, payload)
    except Exception as exc:
        update_run_state(
            False,
            action=action,
            stage="失败",
            detail=str(exc),
            topicid=topic_id,
            bookmd5=book_md5,
            queue_id=queue_id,
            request_id=request_id,
            source=str(payload.get("source") or ""),
        )
        raise
    if not isinstance(result, dict):
        result = {"ok": False, "message": "生成动作没有返回可用结果。"}
    ok = bool(result.get("ok"))
    stopped = bool(result.get("stopped"))
    detail = str(result.get("message") or result.get("reply") or ("动作完成。" if ok else "动作失败。"))[:500]
    run = update_run_state(
        False,
        action=action,
        stage="已停止" if stopped else ("已完成" if ok else "失败"),
        detail=detail,
        topicid=topic_id,
        bookmd5=book_md5,
        queue_id=queue_id,
        request_id=request_id,
        source=str(payload.get("source") or ""),
    )
    result["run"] = run
    return result


def append_event(payload: dict[str, Any]) -> dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    record = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "pid": os.getpid(),
        "event": str(payload.get("event") or ""),
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "docmd5": str(payload.get("docmd5") or ""),
        "notebookid": str(payload.get("notebookid") or ""),
        "source": str(payload.get("source") or ""),
        "pluginVersion": str(payload.get("pluginVersion") or ""),
        "extra": payload.get("extra") if isinstance(payload.get("extra"), dict) else {},
    }
    with EVENTS_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"ok": True, "message": "event recorded", "event": record}


def read_recent_events(limit: int = 12) -> list[dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    try:
        lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    except Exception:
        return []
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def event_epoch(event: dict[str, Any] | None) -> float:
    if not isinstance(event, dict):
        return 0.0
    ts = str(event.get("ts") or "")
    if not ts:
        return 0.0
    try:
        return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except Exception:
        return 0.0


def mn_runtime_source_mtime() -> float:
    candidates = [
        MN_EXTENSION_DIR / "main.js",
        MN_EXTENSION_DIR / "CodexWebPanelController.js",
        MN_EXTENSION_DIR / "web/app.js",
        MN_EXTENSION_DIR / "web/index.html",
        MN_EXTENSION_DIR / "web/app.css",
    ]
    mtimes: list[float] = []
    for path in candidates:
        try:
            if path.exists():
                mtimes.append(path.stat().st_mtime)
        except Exception:
            continue
    return max(mtimes) if mtimes else 0.0


def installed_required_native_handler_features() -> list[str]:
    try:
        text = (MN_EXTENSION_DIR / "main.js").read_text(encoding="utf-8")
    except Exception:
        return list(REQUIRED_NATIVE_HANDLER_FEATURES)
    features = [feature for feature in REQUIRED_NATIVE_HANDLER_FEATURES if feature in text]
    return features or list(REQUIRED_NATIVE_HANDLER_FEATURES)


def native_handler_features_from_event(event: dict[str, Any] | None) -> list[str]:
    extra = event.get("extra") if isinstance((event or {}).get("extra"), dict) else {}
    features = extra.get("handlerFeatures") if isinstance(extra.get("handlerFeatures"), list) else []
    return [str(item) for item in features if item]


def mn4_runtime_status(limit: int = 600) -> dict[str, Any]:
    events = read_recent_events(limit)
    version_events = [
        item
        for item in events
        if str(item.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
    ]
    web_events = [item for item in version_events if str(item.get("event") or "") == "webControlsReady"]
    native_events = [item for item in version_events if str(item.get("event") or "") == "nativeApiCapabilities"]
    latest_web = web_events[-1] if web_events else None
    latest_native = native_events[-1] if native_events else None
    latest_event = latest_native or latest_web
    source_mtime = mn_runtime_source_mtime()
    latest_epoch = max(event_epoch(latest_web), event_epoch(latest_native))
    stale_runtime = bool(source_mtime and latest_epoch and source_mtime > latest_epoch)
    latest_unknown_by_action: dict[str, float] = {}
    for item in version_events:
        if str(item.get("event") or "") != "nativeQueueCommandUnknown":
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        native_action = str(extra.get("nativeAction") or "")
        if native_action in {"probe_native_api_capabilities", "reload_web_panel"}:
            latest_unknown_by_action[native_action] = max(
                latest_unknown_by_action.get(native_action, 0.0),
                event_epoch(item),
            )
    runtime_handler_stale_actions = [
        action
        for action, reference_event in (
            ("probe_native_api_capabilities", latest_native),
            ("reload_web_panel", latest_web),
        )
        if latest_unknown_by_action.get(action, 0.0) > event_epoch(reference_event)
    ]
    required_handler_features = installed_required_native_handler_features()
    native_handler_features = native_handler_features_from_event(latest_native)
    missing_handler_features = (
        [feature for feature in required_handler_features if feature not in native_handler_features]
        if latest_native
        else []
    )
    if missing_handler_features:
        runtime_handler_stale_actions.append("native-handler-features")
    runtime_handler_stale = bool(runtime_handler_stale_actions)
    web_ready = latest_web is not None
    native_ready = latest_native is not None
    ready = bool(web_ready and native_ready and not stale_runtime and not runtime_handler_stale)
    if ready:
        summary = "MN4 运行态已加载当前插件。"
        next_step = "可以继续刷新 MN 能力、缓存 PDF、写入卡片/脑图或执行原生高亮。"
    elif stale_runtime or runtime_handler_stale:
        summary = "MN4 运行态未刷新：已安装插件比当前运行中的 MN4 面板更新。"
        if runtime_handler_stale_actions:
            summary += " 旧 handler 不认识：" + ", ".join(runtime_handler_stale_actions) + "。"
        if missing_handler_features:
            summary += " 缺少原生 handler 指纹：" + ", ".join(missing_handler_features) + "。"
        next_step = "重新打开 Codex 面板；如果仍旧，重启 MarginNote 4 后再点“刷新MN能力”。"
    elif not web_ready and not native_ready:
        summary = "MN4 运行态未上报：尚未看到当前版本的 WebView 和原生能力事件。"
        next_step = "在 MarginNote 4 中打开 notebook，并打开 Codex Companion 面板。"
    elif not native_ready:
        summary = "MN4 WebView 已加载，但原生能力矩阵尚未刷新。"
        next_step = "保持当前 PDF/notebook 打开，点击“刷新MN能力”。"
    else:
        summary = "MN4 运行态信息不完整。"
        next_step = "重新打开 Codex 面板后再检查。"
    return {
        "ready": ready,
        "webControlsReady": web_ready,
        "nativeApiReady": native_ready,
        "staleRuntime": stale_runtime,
        "runtimeHandlerStale": runtime_handler_stale,
        "runtimeHandlerStaleActions": runtime_handler_stale_actions,
        "requiredNativeHandlerFeatures": required_handler_features,
        "nativeHandlerFeatures": native_handler_features,
        "missingNativeHandlerFeatures": missing_handler_features,
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "latestWebEventTs": str(latest_web.get("ts") if latest_web else ""),
        "latestNativeEventTs": str(latest_native.get("ts") if latest_native else ""),
        "latestEventTs": str(latest_event.get("ts") if latest_event else ""),
        "sourceMtime": source_mtime,
        "summary": summary,
        "nextStep": next_step,
    }


def latest_native_api_capabilities(topic_id: str = "", book_md5: str = "", limit: int = 600) -> dict[str, Any]:
    events = read_recent_events(limit)
    matches: list[dict[str, Any]] = []
    for item in events:
        if str(item.get("event") or "") != "nativeApiCapabilities":
            continue
        if topic_id and str(item.get("topicid") or "") not in {"", topic_id}:
            continue
        if book_md5 and str(item.get("bookmd5") or "") not in {"", book_md5}:
            continue
        extra = item.get("extra")
        if isinstance(extra, dict):
            matches.append(item)
    if not matches:
        return {
            "available": False,
            "message": "尚未收到 MN4 插件运行时原生 API 探测事件；请打开 MN4 面板或重启 MN4 后再检查。",
            "candidateMethods": [],
            "hasNativeHighlightCandidate": False,
            "hasAnnotatedExportCandidate": False,
            "capabilityMatrix": native_api_capability_matrix({}, []),
        }
    latest = matches[-1]
    extra = latest.get("extra") if isinstance(latest.get("extra"), dict) else {}
    methods = extra.get("candidateMethods") if isinstance(extra.get("candidateMethods"), list) else []
    clean_methods = [str(item) for item in methods if item]
    matrix = native_api_capability_matrix(extra, clean_methods)
    has_native_highlight_candidate = bool(extra.get("hasNativeHighlightCandidate"))
    if not has_native_highlight_candidate:
        highlight_capability = matrix.get("nativeHighlightSelection") if isinstance(matrix, dict) else None
        has_native_highlight_candidate = bool(
            isinstance(highlight_capability, dict) and highlight_capability.get("available")
        )
    return {
        "available": True,
        "event_ts": str(latest.get("ts") or ""),
        "pluginVersion": str(latest.get("pluginVersion") or ""),
        "handlerFeatures": native_handler_features_from_event(latest),
        "candidateMethods": clean_methods,
        "hasNativeHighlightCandidate": has_native_highlight_candidate,
        "hasAnnotatedExportCandidate": bool(extra.get("hasAnnotatedExportCandidate")),
        "targetCount": int(extra.get("targetCount") or 0),
        "targets": extra.get("targets") if isinstance(extra.get("targets"), list) else [],
        "activeSelectionLength": int(extra.get("activeSelectionLength") or 0),
        "capabilityMatrix": matrix,
        "message": str(extra.get("message") or ""),
    }


def native_api_capability_matrix(extra: dict[str, Any], candidate_methods: list[str]) -> dict[str, dict[str, Any]]:
    provided = extra.get("capabilityMatrix") if isinstance(extra, dict) else None
    if isinstance(provided, dict):
        return sanitize_native_capability_matrix(provided)

    targets = extra.get("targets") if isinstance(extra, dict) and isinstance(extra.get("targets"), list) else []
    highlight_methods: list[str] = []
    export_methods: list[str] = []
    target_exists: dict[str, bool] = {}
    for target in targets:
        if not isinstance(target, dict):
            continue
        label = str(target.get("label") or "")
        if label:
            target_exists[label] = bool(target.get("exists"))
        for method in target.get("highlightMethods") if isinstance(target.get("highlightMethods"), list) else []:
            if method:
                highlight_methods.append(str(method))
        for method in target.get("exportMethods") if isinstance(target.get("exportMethods"), list) else []:
            if method:
                export_methods.append(str(method))

    if not highlight_methods:
        highlight_methods = [item for item in candidate_methods if "highlight" in item.lower()]
    if not export_methods:
        export_methods = [
            item
            for item in candidate_methods
            if "export" in item.lower() or "annotation" in item.lower() or "importpdfannotations" in item.lower()
        ]

    active_selection_length = int(extra.get("activeSelectionLength") or extra.get("selectionLength") or 0) if isinstance(extra, dict) else 0
    def document_controller_label_exists() -> bool:
        controller_markers = (
            "documentcontroller",
            "doccontroller",
            "currentdocumentcontroller",
            "readercontroller",
            "readerviewcontroller",
            "pdfcontroller",
            "pdfviewcontroller",
            "pdfreader",
            "pdfdocumentcontroller",
            "documentviewcontroller",
            "docviewcontroller",
            "pdfview",
        )
        for label, exists in target_exists.items():
            if not exists:
                continue
            lower = label.lower()
            if lower in {"selectiondocumentcontroller", "documentcontroller"}:
                return True
            if any(marker in lower for marker in controller_markers):
                return True
        return False

    selection_controller_exists = (
        target_exists.get("selectionDocumentController")
        or target_exists.get("documentController")
        or any(item.startswith(("selectionDocumentController.", "documentController.")) for item in highlight_methods)
        or document_controller_label_exists()
    )
    has_highlight_selector = any("highlightfromselection" in item.lower() for item in highlight_methods)
    if not has_highlight_selector and highlight_methods:
        has_highlight_selector = True
    can_attempt_unverified_highlight_call = bool(selection_controller_exists and not has_highlight_selector)

    highlight_blocked = ""
    highlight_next = "在 MN4 PDF 中选中文本后点击“高亮选区”。"
    if not selection_controller_exists:
        highlight_blocked = "missing-document-controller"
        highlight_next = "先打开一个 PDF 文档并让 MN4 面板刷新上下文。"
    elif not has_highlight_selector and not can_attempt_unverified_highlight_call:
        highlight_blocked = "missing-highlight-selector"
        highlight_next = "当前 MN4 运行时未暴露可调用的选区高亮 selector。"
    elif active_selection_length <= 0:
        highlight_blocked = "missing-active-pdf-selection"
        highlight_next = (
            "已发现 PDF 控制器但 selector 不可枚举；先在 PDF 里选中文本，再点击“高亮选区”尝试官方 highlightFromSelection。"
            if can_attempt_unverified_highlight_call
            else "先在 PDF 里选中文本，再点击“高亮选区”。"
        )
    elif can_attempt_unverified_highlight_call:
        highlight_next = "已发现 PDF 控制器但 selector 不可枚举；点击“高亮选区”会尝试官方 highlightFromSelection 并记录结果。"

    highlight_evidence = list(highlight_methods)
    if can_attempt_unverified_highlight_call:
        highlight_evidence.append("unverified-highlightFromSelection-call")

    create_note_ready = bool(extra.get("canCreateNote") or extra.get("canCreateCards") or extra.get("canCreateMindmap"))
    undo_ready = bool(extra.get("canGroupUndo") or extra.get("hasUndoManager"))
    refresh_ready = bool(extra.get("canRefreshAfterDBChanged") or extra.get("hasRefreshAfterDBChanged"))
    popup_ready = bool(extra.get("canInstallSelectionPopupMenu"))
    pdf_path_ready = bool(extra.get("hasPdfPath") or extra.get("pdfPathAvailable"))

    return sanitize_native_capability_matrix(
        {
            "nativeHighlightSelection": {
                "label": "原生高亮当前 PDF 选区",
                "available": bool(selection_controller_exists and (has_highlight_selector or can_attempt_unverified_highlight_call)),
                "ready": bool(selection_controller_exists and (has_highlight_selector or can_attempt_unverified_highlight_call) and active_selection_length > 0),
                "entryAction": "request_native_highlight_selection",
                "nativeAction": "highlight_current_selection",
                "blockedReason": highlight_blocked,
                "nextStep": highlight_next,
                "evidence": highlight_evidence,
            },
            "selectionPopupHighlight": {
                "label": "PDF 选区弹出菜单高亮入口",
                "available": popup_ready,
                "ready": bool(popup_ready and active_selection_length > 0),
                "entryAction": "request_native_highlight_selection",
                "blockedReason": "" if popup_ready and active_selection_length > 0 else "needs-selection-popup",
                "nextStep": "在 PDF 中选中文本后，从弹出菜单点“Codex 高亮选区”。",
                "evidence": ["PopupMenu.currentMenu", "PopupMenuItem"] if popup_ready else [],
            },
            "nativeCards": {
                "label": "创建 MN 原生卡片",
                "available": create_note_ready,
                "ready": create_note_ready,
                "entryAction": "draft_accept",
                "nativeAction": "createCards",
                "blockedReason": "" if create_note_ready else "unverified-note-api",
                "nextStep": "生成卡片草稿后点“写入 MarginNote”。",
                "evidence": ["Note.createWithTitleNotebookDocument"] if create_note_ready else [],
            },
            "nativeMindmap": {
                "label": "创建或合并 MN 原生脑图节点",
                "available": create_note_ready,
                "ready": create_note_ready,
                "entryAction": "draft_accept",
                "nativeAction": "createMindmap",
                "blockedReason": "" if create_note_ready else "unverified-note-api",
                "nextStep": "生成脑图草稿后点“写入 MarginNote”；合并会追加到当前选中节点下。",
                "evidence": ["Note.createWithTitleNotebookDocument", "addChild"] if create_note_ready else [],
            },
            "undoGroupedWrites": {
                "label": "MN Undo 分组写入",
                "available": undo_ready,
                "ready": undo_ready,
                "entryAction": "draft_accept",
                "blockedReason": "" if undo_ready else "unverified-undo-manager",
                "nextStep": "写入卡片/脑图时由 UndoManager 分组，便于撤销。",
                "evidence": ["UndoManager.sharedInstance().undoGrouping"] if undo_ready else [],
            },
            "refreshAfterWrite": {
                "label": "写入后刷新 MN 视图",
                "available": refresh_ready,
                "ready": refresh_ready,
                "entryAction": "draft_accept",
                "blockedReason": "" if refresh_ready else "unverified-refresh-api",
                "nextStep": "写入后刷新当前 topic，让新节点立即显示。",
                "evidence": ["Application.sharedInstance().refreshAfterDBChanged"] if refresh_ready else [],
            },
            "cacheCurrentPdf": {
                "label": "由 MN 插件进程缓存当前 PDF",
                "available": True,
                "ready": pdf_path_ready,
                "entryAction": "request_pdf_cache",
                "nativeAction": "cache_pdf_from_current_document",
                "blockedReason": "" if pdf_path_ready else "needs-current-pdf-path",
                "nextStep": "打开目标 PDF 后点击“缓存PDF”，由 MN4 插件进程读取文件并上传给 Companion。",
                "evidence": ["resolveContext.pdfPath"] if pdf_path_ready else [],
            },
            "annotatedPdfExport": {
                "label": "导出带标注 PDF 副本",
                "available": True,
                "ready": bool(export_methods or pdf_path_ready),
                "entryAction": "export_annotated_pdf",
                "blockedReason": "" if export_methods or pdf_path_ready else "needs-pdf-cache-or-path",
                "nextStep": "先缓存 PDF 或让 MN4 payload 带上 pdfPath；导出只写副本，不覆盖原 PDF。",
                "evidence": export_methods or (["cached/pdfPath"] if pdf_path_ready else []),
            },
        }
    )


def sanitize_native_capability_matrix(matrix: dict[str, Any]) -> dict[str, dict[str, Any]]:
    clean: dict[str, dict[str, Any]] = {}
    for key, value in matrix.items():
        if not isinstance(value, dict):
            continue
        evidence = value.get("evidence") if isinstance(value.get("evidence"), list) else []
        clean[str(key)] = {
            "label": str(value.get("label") or key),
            "available": bool(value.get("available")),
            "ready": bool(value.get("ready")),
            "entryAction": str(value.get("entryAction") or ""),
            "nativeAction": str(value.get("nativeAction") or ""),
            "blockedReason": str(value.get("blockedReason") or ""),
            "nextStep": str(value.get("nextStep") or ""),
            "evidence": [str(item) for item in evidence if item],
        }
    return clean


def native_api_capabilities_reply_block(caps: dict[str, Any]) -> str:
    if not caps.get("available"):
        return (
            "MN4 原生 API 探测：尚无运行时事件。\n"
            f"{caps.get('message') or ''}"
        ).strip()
    methods = caps.get("candidateMethods") if isinstance(caps.get("candidateMethods"), list) else []
    method_lines = "\n".join(f"  - `{item}`" for item in methods[:12]) or "  - 未发现候选 selector"
    matrix = caps.get("capabilityMatrix") if isinstance(caps.get("capabilityMatrix"), dict) else {}
    matrix_lines = native_api_capability_reply_lines(matrix)
    return (
        "MN4 原生 API 探测：\n"
        f"- 发现高亮候选: {'是' if caps.get('hasNativeHighlightCandidate') else '否'}\n"
        f"- 发现标注导出候选: {'是' if caps.get('hasAnnotatedExportCandidate') else '否'}\n"
        f"- 探测时间: `{caps.get('event_ts') or '(unknown)'}`\n"
        f"- 候选方法:\n{method_lines}"
        f"{matrix_lines}"
    )


def native_api_capability_reply_lines(matrix: dict[str, Any]) -> str:
    if not matrix:
        return ""
    order = [
        "nativeCards",
        "nativeMindmap",
        "nativeHighlightSelection",
        "selectionPopupHighlight",
        "cacheCurrentPdf",
        "annotatedPdfExport",
        "undoGroupedWrites",
        "refreshAfterWrite",
    ]
    keys = [key for key in order if key in matrix] + [key for key in matrix if key not in order]
    lines = ["", "", "MN 原生动作矩阵："]
    for key in keys:
        item = matrix.get(key)
        if not isinstance(item, dict):
            continue
        label = str(item.get("label") or key)
        entry = str(item.get("entryAction") or item.get("nativeAction") or key)
        next_step = str(item.get("nextStep") or "")
        if item.get("ready"):
            suffix = f"（`{entry}`）" if entry else ""
            lines.append(f"- 可执行：{label}{suffix}")
        elif item.get("available"):
            reason = str(item.get("blockedReason") or "needs-context")
            suffix = f"（`{entry}`）" if entry else ""
            lines.append(f"- 受阻：{label}{suffix}，原因 `{reason}`；{next_step}".rstrip())
    return "\n".join(lines)


def status_payload() -> dict[str, Any]:
    load_env_file()
    settings = runtime_settings()
    proxy_url = settings.get("proxyUrl", "")
    proxy_scheme = urlparse(proxy_url).scheme if proxy_url else ""
    ai_status = ai_status_fields(settings)
    return {
        "ok": True,
        "message": "Codex MarginNote Companion is running.",
        "pid": os.getpid(),
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        **ai_status,
        "model": settings["model"],
        "speed": settings["speed"],
        "permission": settings["permission"],
        "proxy_configured": bool(proxy_url),
        "proxy_scheme": proxy_scheme,
        "goal": active_goal(),
        "files": uploaded_files(),
        "queue": queue_status_payload(),
        "run": active_run_status(),
        "mnRuntime": mn4_runtime_status(),
        "nativeApiCapabilities": latest_native_api_capabilities(),
        "update": update_manager.read_update_status(ROOT),
        "session_count": len(list(SESSIONS_DIR.glob("*.json"))) if SESSIONS_DIR.exists() else 0,
        "recent_events": read_recent_events(),
    }


def now_mac_time() -> float:
    return time.time() - 978307200.0


def is_marginnote_running() -> bool:
    try:
        out = subprocess.run(
            ["/bin/ps", "-ax"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        ).stdout
    except Exception:
        return False
    return "MarginNote 4" in out or "QReader.MarginStudy.easy" in out


def read_defaults(key: str) -> str:
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


def normalize_topic_id(payload: dict[str, Any]) -> str:
    for key in ("topicid", "notebookid"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return read_defaults("mindbooks_lasttopicid")


def normalize_book_md5(payload: dict[str, Any]) -> str:
    for key in ("bookmd5", "docmd5"):
        value = str(payload.get(key) or "").strip()
        if value:
            return value
    return read_defaults("mindbooks_lastbookmd5")


def zbooknote_columns(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("pragma table_info(ZBOOKNOTE)").fetchall()
    return [str(row[1]) for row in rows]


def diagnose_highlights(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not DB_PATH.exists():
        return {"ok": False, "message": f"找不到 MarginNote 数据库：{DB_PATH}"}
    conn: sqlite3.Connection | None = None
    try:
        conn = sqlite3.connect(DB_PATH)
        columns = set(zbooknote_columns(conn))
        codex_row_parts: list[str] = []
        if "ZAUTHOR" in columns:
            codex_row_parts.append("coalesce(ZAUTHOR, '') like 'Codex-%'")
        if "ZNOTETITLE" in columns:
            codex_row_parts.append("coalesce(ZNOTETITLE, '') like 'Codex高亮：%'")
        codex_case = " or ".join(codex_row_parts) if codex_row_parts else "0"
        row = conn.execute(
            f"""
            select
                count(*) as total_rows,
                sum(case when ZHIGHLIGHTS is not null then 1 else 0 end) as highlight_rows,
                sum(case when {codex_case} then 1 else 0 end) as codex_rows
              from ZBOOKNOTE
             where ZBOOKMD5=?
               and ZTOPICID=?
            """,
            (book_md5, topic_id),
        ).fetchone()
    except Exception as exc:
        native_caps = latest_native_api_capabilities(topic_id, book_md5)
        reply = (
            "高亮状态只读诊断未能读取 MarginNote 数据库。\n\n"
            f"原因：{exc}\n\n"
            f"{native_api_capabilities_reply_block(native_caps)}\n\n"
            "这通常是 macOS 隐私权限导致的：LaunchAgent 后台 Python 没有 Full Disk Access。"
            "卡片、脑图和对话仍可正常通过 MN4 插件原生 API 工作；本动作没有修改数据库，也没有修改原 PDF。"
        )
        return {
            "ok": True,
            "message": "高亮诊断需要更多 macOS 权限；未修改原始 PDF。",
            "reply": reply,
            "status": "PERMISSION",
            "native_highlight_rows": None,
            "nativeApiCapabilities": native_caps,
        }
    finally:
        if conn is not None:
            conn.close()
    total_rows = int(row[0] or 0) if row else 0
    highlight_rows = int(row[1] or 0) if row else 0
    codex_rows = int(row[2] or 0) if row else 0
    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    reply = (
        "高亮状态只读诊断：\n\n"
        f"- 当前 topic: `{topic_id or '(missing)'}`\n"
        f"- 当前文档: `{book_md5 or '(missing)'}`\n"
        f"- 当前文档笔记行: {total_rows}\n"
        f"- 含 MN 原生 highlight blob 的行: {highlight_rows}\n"
        f"- Codex 高亮相关笔记行: {codex_rows}\n\n"
        f"{native_api_capabilities_reply_block(native_caps)}\n\n"
        "发布版默认不会直接写 MarginNote SQLite，也不会修改原始 PDF。"
        "下一步必须通过 MN4 原生高亮 API 或“导出标注副本”路线实现可见高亮。"
    )
    status = "OK" if highlight_rows > 0 else "WARN"
    return {
        "ok": True,
        "message": f"高亮诊断完成：native highlight rows={highlight_rows}。",
        "reply": reply,
        "status": status,
        "native_highlight_rows": highlight_rows,
        "codex_highlight_rows": codex_rows,
        "total_rows": total_rows,
        "nativeApiCapabilities": native_caps,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pdf_path_from_raw_value(raw: str) -> Path:
    raw = str(raw or "").strip()
    if raw.lower().startswith("file://"):
        parsed = urlparse(raw)
        return Path(unquote(parsed.path)).expanduser()
    return Path(raw).expanduser()


def unique_paths(paths: list[Path]) -> list[Path]:
    unique: list[Path] = []
    seen: set[str] = set()
    for path in paths:
        if not path:
            continue
        expanded = path.expanduser()
        key = str(expanded)
        if key in seen:
            continue
        seen.add(key)
        unique.append(expanded)
    return unique


def configured_extra_pdf_roots() -> list[Path]:
    raw = os.environ.get("CODEX_MN_PDF_ROOTS", "")
    roots: list[Path] = []
    if raw.strip():
        parts = [part.strip() for part in raw.replace("\n", os.pathsep).split(os.pathsep)]
        roots.extend(Path(part).expanduser() for part in parts if part)
    roots.extend(Path(item).expanduser() for item in runtime_settings().get("fileSearchRoots", []) if str(item).strip())
    return unique_paths(roots)


def cloud_storage_pdf_roots() -> list[Path]:
    cloud_storage = HOME / "Library/CloudStorage"
    if not cloud_storage.is_dir():
        return []
    roots: list[Path] = []
    try:
        providers = [path for path in cloud_storage.iterdir() if path.is_dir()]
    except Exception:
        return []
    for provider in providers:
        lower_name = provider.name.casefold()
        if "onedrive" not in lower_name and "icloud" not in lower_name:
            continue
        for rel in COMMON_CLOUD_PDF_RELS:
            roots.append(provider / rel)
    return roots


def marginnote_doclink_roots(raw: str) -> list[Path]:
    prefix = "$$$MNDOCLINK$$$"
    value = str(raw or "").strip()
    if not value.startswith(prefix):
        return []
    link = value[len(prefix) :].strip("/")
    if not link:
        return []
    roots = [
        HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Caches/MD5CacheFiles" / value,
    ]
    if link.startswith("iCloud.QReader.MarginStudy.easy/"):
        rest = link.split("/", 1)[1] if "/" in link else ""
        if rest:
            roots.append(HOME / "Library/Mobile Documents/iCloud~QReader~MarginStudy~easy/Documents" / rest)
    cloud_storage = HOME / "Library/CloudStorage"
    if cloud_storage.is_dir():
        try:
            providers = [path for path in cloud_storage.iterdir() if path.is_dir() and "onedrive" in path.name.casefold()]
        except Exception:
            providers = []
        for provider in providers:
            roots.append(provider / link)
            roots.append(provider / "博士" / link)
    return roots


def pdf_root_hints_from_raw_values(raw_values: list[str]) -> list[Path]:
    roots: list[Path] = []
    for raw in raw_values:
        if not raw:
            continue
        roots.extend(marginnote_doclink_roots(raw))
        candidate = pdf_path_from_raw_value(raw)
        if candidate.is_absolute():
            roots.append(candidate.parent if candidate.suffix.lower() == ".pdf" else candidate)
    return unique_paths(roots)


def pdf_filename_candidates(raw_values: list[str]) -> list[str]:
    names: list[str] = []
    for raw in raw_values:
        if not raw:
            continue
        if raw.startswith("$$$MNDOCLINK$$$"):
            continue
        candidate = pdf_path_from_raw_value(raw)
        name = str(candidate.name or raw).strip()
        if not name:
            continue
        name = name.replace("/", " ").replace("\\", " ").strip()
        base = re.sub(r"\.pdf$", "", name, flags=re.IGNORECASE).strip()
        variants: list[str] = []
        if base:
            copy_base = re.sub(r"\s*#\d+\s*$", "", base).strip()
            if copy_base and copy_base != base:
                variants.append(copy_base + ".pdf")
            variants.append(base + ".pdf")
        if name.lower().endswith(".pdf"):
            variants.append(name)
        for variant in variants:
            if variant and variant.lower().endswith(".pdf") and variant not in names:
                names.append(variant)
    return names


def payload_pdf_name_values(payload: dict[str, Any]) -> list[str]:
    keys = [
        "fileName",
        "filename",
        "documentFileName",
        "documentTitle",
        "documentName",
        "sourceFileName",
        "sourceDocumentTitle",
        "bookTitle",
        "bookName",
        "title",
        "ZFILE",
        "ZBOOKURL",
    ]
    values: list[str] = []
    for key in keys:
        value = str(payload.get(key) or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def normalize_pdf_title_key(text: str) -> str:
    value = Path(str(text or "").strip()).name
    value = re.sub(r"\.pdf$", "", value, flags=re.IGNORECASE)
    value = repair_pdf_extracted_math_text(value).casefold()
    value = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def iter_pdf_files_in_roots(roots: list[Path], max_files: int = 5000) -> list[Path]:
    files: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        if not root:
            continue
        path = root.expanduser()
        if path.is_file() and path.suffix.lower() == ".pdf":
            key = str(path)
            if key not in seen:
                seen.add(key)
                files.append(path)
            continue
        if not path.is_dir():
            continue
        for current_root, dirnames, names in os.walk(path):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in {".git", "node_modules", "__pycache__"} and not name.startswith(".")
            ]
            for name in names:
                if not name.lower().endswith(".pdf"):
                    continue
                candidate = Path(current_root) / name
                key = str(candidate)
                if key in seen:
                    continue
                seen.add(key)
                files.append(candidate)
                if len(files) >= max_files:
                    return files
    return files


def find_pdf_by_title_in_roots(raw_values: list[str], roots: list[Path]) -> Path | None:
    filenames = pdf_filename_candidates(raw_values)
    found = find_pdf_by_filename_in_roots(filenames, roots)
    if found:
        return found
    title_keys = [normalize_pdf_title_key(value) for value in raw_values]
    title_keys = [value for value in title_keys if len(value) >= 4]
    if not title_keys:
        return None
    for candidate in iter_pdf_files_in_roots(roots):
        candidate_key = normalize_pdf_title_key(candidate.name)
        if not candidate_key:
            continue
        for title_key in title_keys:
            if title_key == candidate_key or title_key in candidate_key or candidate_key in title_key:
                return candidate
    return None


def pdf_source_search_roots(path_hints: list[Path] | None = None) -> list[Path]:
    roots: list[Path] = []
    roots.extend(path_hints or [])
    roots.extend(MN_DOC_ROOTS)
    roots.extend(MN_DOC_CACHE_ROOTS)
    roots.extend(ONEDRIVE_PDF_ROOTS)
    roots.extend(cloud_storage_pdf_roots())
    roots.extend(configured_extra_pdf_roots())
    return unique_paths(roots)


def payload_title_search_roots() -> list[Path]:
    roots: list[Path] = []
    roots.extend(configured_extra_pdf_roots())
    roots.extend(ONEDRIVE_PDF_ROOTS)
    roots.extend(cloud_storage_pdf_roots())
    roots.extend(MN_DOC_ROOTS)
    roots.extend(MN_DOC_CACHE_ROOTS)
    return unique_paths(roots)


def find_pdf_by_filename_in_roots(filenames: list[str], roots: list[Path]) -> Path | None:
    for root in roots:
        if root.is_file() and root.suffix.lower() == ".pdf" and root.name in filenames:
            return root
        for name in filenames:
            candidate = root / name
            if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                return candidate
    max_checked = 30000
    checked = 0
    for root in roots:
        if not root.is_dir():
            continue
        for current_root, dirnames, files in os.walk(root):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in {".git", "node_modules", "__pycache__"} and not name.startswith(".")
            ]
            checked += 1
            if checked > max_checked:
                return None
            for name in filenames:
                if name in files:
                    candidate = Path(current_root) / name
                    if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                        return candidate
    return None


def configured_single_pdf_file() -> Path | None:
    files = [path for path in configured_extra_pdf_roots() if path.is_file() and path.suffix.lower() == ".pdf"]
    return files[0] if len(files) == 1 else None


def selection_text_for_pdf_discovery(payload: dict[str, Any]) -> str:
    for key in ("selectionText", "selectedText", "activeSelectionText", "sourceExcerpt"):
        text = repair_pdf_extracted_math_text(str(payload.get(key) or "")).strip()
        text = re.sub(r"\s+", " ", text)
        if len(text) >= 60:
            return text[:900]
    return ""


def find_pdf_by_selection_text_in_roots(selection_text: str, roots: list[Path]) -> Path | None:
    query = re.sub(r"\s+", " ", repair_pdf_extracted_math_text(selection_text or "")).strip()
    if len(query) < 60:
        return None
    candidates = iter_pdf_files_in_roots(roots, max_files=1200)
    if not candidates:
        return None
    python, dependency_error = find_pymupdf_python()
    if not python:
        return None
    script = r"""
import json
import re
import sys

import fitz

needle = re.sub(r"\s+", " ", sys.argv[1]).strip().casefold()
paths = json.loads(sys.argv[2])
probe = needle[:260]
stop_words = {
    "about", "after", "also", "because", "been", "being", "between", "both",
    "could", "from", "have", "into", "more", "such", "than", "that", "their",
    "there", "these", "this", "through", "under", "using", "were", "when",
    "where", "which", "with", "would",
}
tokens = []
seen_tokens = set()
for token in re.findall(r"[0-9a-z\u4e00-\u9fff]{4,}", needle):
    if token in stop_words or token in seen_tokens:
        continue
    tokens.append(token)
    seen_tokens.add(token)
    if len(tokens) >= 48:
        break
threshold = max(5, int(len(tokens) * 0.58 + 0.999)) if tokens else 9999
compact_probe = re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", probe)

def norm(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().casefold()

def compact(text):
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]+", "", str(text or "").casefold())

def score_text(text):
    compact_text = compact(text)
    if compact_probe and len(compact_probe) >= 48 and compact_probe in compact_text:
        return 10000
    if not tokens:
        return 0
    hits = 0
    for token in tokens:
        if token in text:
            hits += 1
    return hits

best_path = ""
best_score = 0
for path in paths:
    try:
        doc = fitz.open(path)
    except Exception:
        continue
    try:
        for page in doc:
            text = norm(page.get_text("text") or "")
            page_score = 10000 if probe and probe in text else score_text(text)
            if page_score > best_score:
                best_score = page_score
                best_path = path
    except Exception:
        pass
    finally:
        try:
            doc.close()
        except Exception:
            pass
if best_score >= 10000 or best_score >= threshold:
    print("__CODEX_MN_PDF_MATCH__" + best_path)
else:
    print("__CODEX_MN_PDF_MATCH__")
"""
    try:
        completed = subprocess.run(
            [str(python), "-c", script, query, json.dumps([str(path) for path in candidates], ensure_ascii=False)],
            text=True,
            capture_output=True,
            timeout=90,
            check=False,
        )
    except Exception:
        return None
    found_text = ""
    for line in (completed.stdout or "").splitlines():
        if line.startswith("__CODEX_MN_PDF_MATCH__"):
            found_text = line.removeprefix("__CODEX_MN_PDF_MATCH__").strip()
    if found_text:
        found = Path(found_text).expanduser()
        try:
            if found.is_file() and found.suffix.lower() == ".pdf":
                return found
        except OSError:
            return None
    return None


def unresolved_pdf_source_message(db_error: str = "") -> str:
    configured_roots = configured_extra_pdf_roots()
    existing_roots = [path for path in configured_roots if path.exists()]
    if existing_roots:
        permission_hint = f"；同时读取 MarginNote 数据库失败：{db_error}" if db_error else ""
        return (
            "已配置文件搜索目录，但当前请求没有可用于匹配的 PDF 文件名/标题，"
            "也没有足够长的 PDF 选区文本可用于反查全文。"
            "请在当前 PDF 中任意选中一段正文后再问，或让 MN4 传入 documentTitle/documentFileName"
            f"{permission_hint}。"
        )
    if db_error:
        return f"当前 MN 文档没有可解析的本地 PDF 路径；读取 MarginNote 数据库失败：{db_error}"
    return "当前 MN 文档没有可解析的本地 PDF 路径；请先让插件传入 pdfPath/documentTitle，或在 PDF 中选中一段正文后重试。"


def summarize_pdf_search_roots(roots: list[Path], limit: int = 8) -> str:
    visible = [str(root) for root in roots[:limit]]
    if len(roots) > limit:
        visible.append(f"... 另有 {len(roots) - limit} 个目录")
    return "; ".join(visible)


def resolve_pdf_source_from_mn_database(book_md5: str) -> tuple[Path | None, str | None]:
    if not book_md5:
        return None, None
    if not DB_PATH.exists():
        return None, None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                """
                select ZPATH, ZBOOKURL, ZFILE
                  from ZBOOK
                 where ZMD5=? or ZMD5LONG=?
                 limit 1
                """,
                (book_md5, book_md5),
            ).fetchone()
        finally:
            conn.close()
    except PermissionError as exc:
        return None, f"读取 MarginNote ZBOOK 路径被 macOS 权限拦截：{exc}"
    except Exception:
        return None, None
    if not row:
        return None, None

    raw_values = [str(row[key] or "").strip() for key in ("ZFILE", "ZBOOKURL", "ZPATH")]
    for raw in raw_values:
        if not raw:
            continue
        candidate = pdf_path_from_raw_value(raw)
        if candidate.is_absolute() and candidate.is_file() and candidate.suffix.lower() == ".pdf":
            return candidate, None

    filenames = pdf_filename_candidates(raw_values)
    search_roots = pdf_source_search_roots(pdf_root_hints_from_raw_values(raw_values))
    found = find_pdf_by_filename_in_roots(filenames, search_roots)
    if found:
        return found, None
    if filenames:
        return None, (
            "MarginNote ZBOOK 记录了 PDF 文件名，但在已知文档目录中未找到："
            f"{', '.join(filenames[:3])}。已查目录：{summarize_pdf_search_roots(search_roots)}"
        )
    return None, None


def resolve_pdf_source(payload: dict[str, Any], book_md5: str) -> tuple[Path | None, str | None]:
    explicit_error = ""
    for key in ("pdfPath", "documentPath", "sourcePdfPath"):
        raw = str(payload.get(key) or "").strip()
        if raw:
            candidate = pdf_path_from_raw_value(raw)
            if candidate.is_file() and candidate.suffix.lower() == ".pdf":
                return candidate, None
            explicit_error = f"传入的 PDF 路径不可用：{candidate}"
            break
    cached = cached_pdf_for_book(book_md5)
    if cached:
        return cached, None

    payload_names = payload_pdf_name_values(payload)
    if payload_names:
        payload_found = find_pdf_by_title_in_roots(payload_names, payload_title_search_roots())
        if payload_found:
            return payload_found, None

    db_source, db_error = resolve_pdf_source_from_mn_database(book_md5)
    if db_source:
        return db_source, None
    known = KNOWN_PDF_PATHS.get(book_md5)
    if known and known.is_file():
        return known, None
    if known:
        return None, f"已知文档路径不存在：{known}"

    single_configured_pdf = configured_single_pdf_file()
    if single_configured_pdf:
        return single_configured_pdf, None

    selection_text = selection_text_for_pdf_discovery(payload)
    if selection_text:
        text_found = find_pdf_by_selection_text_in_roots(selection_text, configured_extra_pdf_roots())
        if text_found:
            return text_found, None

    if explicit_error:
        return None, explicit_error
    return None, unresolved_pdf_source_message(db_error or "")


def normalized_highlight_queries(payload: dict[str, Any]) -> list[str]:
    raw_values = [
        payload.get("annotationText"),
        payload.get("selectionText"),
        payload.get("selectedText"),
        payload.get("sourceExcerpt"),
    ]
    texts = [str(value).strip() for value in raw_values if str(value or "").strip()]
    if not texts:
        return []

    queries: list[str] = []
    seen: set[str] = set()
    for text in texts:
        candidates = [text]
        candidates.extend(re.split(r"[\n\r]+", text))
        candidates.extend(re.split(r"(?<=[。！？.!?])\s+", text))
        for candidate in candidates:
            query = re.sub(r"\s+", " ", candidate).strip()
            query = query.strip("`*_>:- \t")
            if len(query) < 8:
                continue
            if len(query) > 240:
                query = query[:240].rsplit(" ", 1)[0] or query[:240]
            key = query.casefold()
            if key in seen:
                continue
            seen.add(key)
            queries.append(query)
            if len(queries) >= 12:
                return queries
    return queries


def truncate_utf8_filename_component(value: str, max_bytes: int) -> str:
    cleaned = value.strip(" .-_") or "document"
    if len(cleaned.encode("utf-8")) <= max_bytes:
        return cleaned
    clipped = cleaned.encode("utf-8")[:max_bytes].decode("utf-8", errors="ignore").strip(" .-_")
    return clipped or "document"


def pdf_export_filename(source_pdf: Path, book_md5: str, stamp: str) -> str:
    stem = source_pdf.stem
    if book_md5 and stem.startswith(f"{book_md5}-"):
        stem = stem[len(book_md5) + 1 :]
    safe_stem = re.sub(r"[^A-Za-z0-9._ -]+", "-", stem).strip(" .-_") or "document"
    safe_book = re.sub(r"[^A-Za-z0-9._-]+", "-", book_md5 or "document").strip("._-") or "document"
    safe_book = truncate_utf8_filename_component(safe_book, 32)
    suffix = f".codex-highlighted-{safe_book}-{stamp}.pdf"
    max_stem_bytes = max(16, 255 - len(suffix.encode("utf-8")))
    return f"{truncate_utf8_filename_component(safe_stem, max_stem_bytes)}{suffix}"


def pymupdf_python_candidates() -> list[Path]:
    raw_candidates = [
        os.environ.get("CODEX_MN_PYMUPDF_PYTHON"),
        sys.executable,
        str(HOME / "miniforge3/bin/python3"),
        "/opt/homebrew/bin/python3",
        "/opt/homebrew/bin/python3.12",
        "/usr/local/bin/python3",
        str(HOME / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
    ]
    candidates: list[Path] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            candidates.append(candidate)
    return candidates


def find_pymupdf_python() -> tuple[Path | None, str | None]:
    errors: list[str] = []
    for candidate in pymupdf_python_candidates():
        try:
            subprocess.run(
                [str(candidate), "-c", "import fitz"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=8,
            )
            return candidate, None
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
    return None, "; ".join(errors[-3:]) if errors else "没有找到 Python 解释器候选"


def run_pymupdf_highlight_copy(
    python: Path,
    source_pdf: Path,
    output_pdf: Path,
    queries: list[str],
) -> dict[str, Any]:
    script = r"""
import json
import sys

import fitz

payload = json.load(sys.stdin)
source = payload["source"]
output = payload["output"]
queries = payload["queries"]

doc = fitz.open(source)
matches = []
annotations_created = 0
rects_matched = 0
try:
    for query in queries:
        query_rects = 0
        query_annotations = 0
        for page_index in range(len(doc)):
            page = doc[page_index]
            rects = page.search_for(query)
            if not rects:
                compact_query = " ".join(query.split())
                if compact_query != query:
                    rects = page.search_for(compact_query)
            if not rects:
                continue
            annot = page.add_highlight_annot(rects)
            annot.set_info(content=f"Codex Companion: {query[:220]}")
            annot.update()
            query_rects += len(rects)
            query_annotations += 1
        matches.append({"query": query, "rects": query_rects, "annotations": query_annotations})
        rects_matched += query_rects
        annotations_created += query_annotations
    if annotations_created:
        doc.save(output, garbage=4, deflate=True)
finally:
    doc.close()

print(json.dumps({"annotations_created": annotations_created, "rects_matched": rects_matched, "matches": matches}, ensure_ascii=False))
"""
    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        [str(python), "-c", script],
        input=json.dumps({"source": str(source_pdf), "output": str(output_pdf), "queries": queries}, ensure_ascii=False),
        text=True,
        capture_output=True,
        timeout=60,
        check=True,
    )
    return json.loads(completed.stdout or "{}")


def pdf_export_permission_response(
    source_pdf: Path,
    native_caps: dict[str, Any],
    exc: Exception,
) -> dict[str, Any]:
    reply = (
        "导出标注 PDF 需要读取当前原始 PDF，但后台 Companion 进程被 macOS 隐私权限拦截。\n\n"
        f"PDF: `{source_pdf}`\n"
        f"错误：{exc}\n\n"
        "处理方式：给启动 Companion 的 Python/Terminal/Codex 或 LaunchAgent 相关运行环境 Full Disk Access，"
        "或者把 PDF 放到 Companion 可读取的位置后通过 pdfPath 传入。"
        "本次没有写入副本，也没有修改原始 PDF。"
    )
    return {
        "ok": True,
        "message": "导出标注 PDF 需要 macOS 文件访问权限；未修改原始 PDF。",
        "reply": reply,
        "backend": "local:pymupdf-highlight-copy",
        "status": "PERMISSION",
        "nativeApiCapabilities": native_caps,
        "sourcePdf": str(source_pdf),
        "modifiedOriginal": False,
    }


def probe_file_read_access(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "readable": False,
        "status": "MISSING",
        "message": "",
    }
    if not path.exists():
        result["message"] = "path does not exist"
        return result
    if not path.is_file():
        result["status"] = "WARN"
        result["message"] = "path is not a file"
        return result
    try:
        with path.open("rb") as handle:
            handle.read(1024)
        result["readable"] = True
        result["status"] = "OK"
        result["message"] = "readable"
        return result
    except PermissionError as exc:
        result["status"] = "PERMISSION"
        result["message"] = str(exc)
        return result
    except Exception as exc:
        result["status"] = "ERROR"
        result["message"] = str(exc)
        return result


def probe_directory_write_access(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
        "writable": False,
        "status": "MISSING",
        "message": "",
    }
    try:
        path.mkdir(parents=True, exist_ok=True)
        probe = path / f".codex-permission-check-{os.getpid()}-{uuid.uuid4().hex}.tmp"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        result["exists"] = True
        result["writable"] = True
        result["status"] = "OK"
        result["message"] = "writable"
        return result
    except PermissionError as exc:
        result["status"] = "PERMISSION"
        result["message"] = str(exc)
        return result
    except Exception as exc:
        result["status"] = "ERROR"
        result["message"] = str(exc)
        return result


def aggregate_permission_status(checks: list[dict[str, Any]], optional_permission_keys: set[str] | None = None) -> str:
    optional_permission_keys = optional_permission_keys or set()
    required_checks = [
        item
        for item in checks
        if not (
            str(item.get("status") or "") == "PERMISSION"
            and str(item.get("key") or "") in optional_permission_keys
        )
    ]
    optional_permission = any(
        str(item.get("status") or "") == "PERMISSION"
        and str(item.get("key") or "") in optional_permission_keys
        for item in checks
    )
    checks_to_rank = required_checks or checks
    if not checks_to_rank and optional_permission:
        return "WARN"
    statuses = {str(item.get("status") or "") for item in checks_to_rank}
    if "PERMISSION" in statuses:
        return "PERMISSION"
    if "ERROR" in statuses:
        return "ERROR"
    if optional_permission or statuses.intersection({"MISSING", "WARN"}):
        return "WARN"
    return "OK"


def diagnose_permissions(payload: dict[str, Any]) -> dict[str, Any]:
    book_md5 = normalize_book_md5(payload)
    source_pdf, source_error = resolve_pdf_source(payload, book_md5)
    file_access: dict[str, Any] = {}
    checks: list[dict[str, Any]] = []

    file_access["pdfCache"] = pdf_cache_access_status(book_md5)

    if source_pdf:
        file_access["sourcePdf"] = probe_file_read_access(source_pdf)
        file_access["sourcePdf"]["key"] = "sourcePdf"
    else:
        status = "PERMISSION" if source_error and "权限" in source_error else "WARN"
        file_access["sourcePdf"] = {
            "key": "sourcePdf",
            "path": "",
            "exists": False,
            "readable": False,
            "status": status,
            "message": source_error or "没有解析到当前 PDF 路径",
        }
    checks.append(file_access["sourcePdf"])

    file_access["mnDatabase"] = probe_file_read_access(DB_PATH)
    file_access["mnDatabase"]["key"] = "mnDatabase"
    checks.append(file_access["mnDatabase"])
    file_access["exportDir"] = probe_directory_write_access(PDF_EXPORT_DIR)
    file_access["exportDir"]["key"] = "exportDir"
    checks.append(file_access["exportDir"])

    python, pymupdf_error = find_pymupdf_python()
    file_access["pymupdf"] = {
        "key": "pymupdf",
        "path": str(python or ""),
        "status": "OK" if python else "WARN",
        "message": "PyMuPDF 可用" if python else (pymupdf_error or "PyMuPDF 不可用"),
    }
    checks.append(file_access["pymupdf"])

    status = aggregate_permission_status(checks, optional_permission_keys={"mnDatabase"})
    lines = [
        "文件访问权限诊断：",
        "",
        f"- 当前 PDF: {file_access['sourcePdf']['status']} {file_access['sourcePdf'].get('path') or '(missing)'}",
        f"  {file_access['sourcePdf'].get('message') or ''}",
        f"- PDF缓存: {file_access['pdfCache']['status']} {file_access['pdfCache'].get('path') or '(missing)'}",
        f"  {file_access['pdfCache'].get('message') or ''}",
        f"- MarginNote 数据库: {file_access['mnDatabase']['status']} {file_access['mnDatabase'].get('path')}",
        f"  {file_access['mnDatabase'].get('message') or ''}",
        f"- 导出目录: {file_access['exportDir']['status']} {file_access['exportDir'].get('path')}",
        f"  {file_access['exportDir'].get('message') or ''}",
        f"- PyMuPDF: {file_access['pymupdf']['status']} {file_access['pymupdf'].get('path') or ''}",
        f"  {file_access['pymupdf'].get('message') or ''}",
        "",
        "修复建议：",
        "1. 打开 macOS 系统设置 -> 隐私与安全性 -> 完全磁盘访问权限（Full Disk Access）。",
        "2. 给 Terminal、Codex、Python 或当前 LaunchAgent 所用运行环境授予 Full Disk Access。",
        "3. 如果只想临时导出，可以把 PDF 复制到 Companion 可读的位置，再通过 pdfPath 或文件上传路径传入。",
        "4. 这项诊断只读检查当前 PDF 和 MN 数据库；除了临时探针文件，不会修改原始 PDF。",
    ]
    message = {
        "OK": "文件访问诊断通过。",
        "PERMISSION": "文件访问被 macOS 权限拦截；请按 Full Disk Access 指引处理。",
        "ERROR": "文件访问诊断发现错误。",
        "WARN": "基础文件访问可用，但部分诊断或高级功能需要补充权限。",
    }.get(status, "文件访问诊断完成。")
    return {
        "ok": True,
        "message": message,
        "reply": "\n".join(lines),
        "status": status,
        "fileAccess": file_access,
        "permissionGuide": {
            "macosPane": "System Settings > Privacy & Security > Full Disk Access",
            "targets": ["Terminal", "Codex", "Python", "LaunchAgent runtime"],
            "subjects": full_disk_access_subjects(),
        },
    }


def open_full_disk_access_settings() -> dict[str, Any]:
    url = "x-apple.systempreferences:com.apple.preference.security?Privacy_AllFiles"
    try:
        proc = subprocess.run(
            ["/usr/bin/open", url],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:
        return {
            "ok": False,
            "message": f"打开 Full Disk Access 设置失败：{exc}",
            "reply": (
                "无法自动打开 Full Disk Access 设置。\n\n"
                "请手动打开：macOS 系统设置 -> 隐私与安全性 -> 完全磁盘访问权限（Full Disk Access），"
                "然后给 Terminal、Codex、Python 或 LaunchAgent 运行环境授权。"
            ),
            "url": url,
        }
    ok = proc.returncode == 0
    return {
        "ok": ok,
        "message": "已尝试打开 Full Disk Access 设置。" if ok else "打开 Full Disk Access 设置失败。",
        "reply": (
            "已尝试打开 macOS Full Disk Access 设置。\n\n"
            "请在列表中给 Terminal、Codex、Python 或当前 LaunchAgent 使用的运行环境授权，"
            "然后重启 Companion。授权后再点“检查权限”。"
        )
        if ok
        else f"打开设置失败：{proc.stderr or proc.stdout or proc.returncode}",
        "url": url,
        "returncode": proc.returncode,
    }


def export_annotated_pdf(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    source_pdf, source_error = resolve_pdf_source(payload, book_md5)
    queries = normalized_highlight_queries(payload)
    if source_error or source_pdf is None:
        reply = (
            "导出标注 PDF 还不能执行，因为没有拿到当前文档的本地 PDF 路径。\n\n"
            f"{source_error or ''}\n\n"
            f"当前 topic: `{topic_id or '(missing)'}`\n"
            f"当前文档: `{book_md5 or '(missing)'}`\n\n"
            f"{native_api_capabilities_reply_block(native_caps)}\n\n"
            "原始 PDF 未修改。"
        )
        return {
            "ok": False,
            "message": "导出失败：缺少可用 PDF 路径；未修改原始 PDF。",
            "reply": reply,
            "backend": "local:pymupdf-highlight-copy",
            "status": "MISSING_PDF_PATH",
            "nativeApiCapabilities": native_caps,
            "modifiedOriginal": False,
        }
    if not queries:
        reply = (
            "导出标注 PDF 还不能执行，因为没有可定位的原文摘录。\n\n"
            "请先在 PDF 中选中一段文字，或让调用方传入 annotationText/sourceExcerpt。"
            "插件不会根据泛泛的聊天指令伪造高亮位置。\n\n"
            f"当前 PDF: `{source_pdf}`\n"
            "原始 PDF 未修改。"
        )
        return {
            "ok": False,
            "message": "导出失败：没有可搜索的高亮文本；未修改原始 PDF。",
            "reply": reply,
            "backend": "local:pymupdf-highlight-copy",
            "status": "MISSING_HIGHLIGHT_TEXT",
            "nativeApiCapabilities": native_caps,
            "modifiedOriginal": False,
        }

    python, dependency_error = find_pymupdf_python()
    if python is None:
        reply = (
            "导出标注 PDF 需要 PyMuPDF，但当前 Companion 能找到的 Python 环境都没有 `fitz` 模块。\n\n"
            f"依赖探测：{dependency_error}\n\n"
            "可以安装 PyMuPDF，或设置 `CODEX_MN_PYMUPDF_PYTHON` 指向已有 PyMuPDF 的 Python。"
            "原始 PDF 未修改。"
        )
        return {
            "ok": False,
            "message": "导出失败：缺少 PyMuPDF；未修改原始 PDF。",
            "reply": reply,
            "backend": "local:pymupdf-highlight-copy",
            "status": "MISSING_PYMUPDF",
            "nativeApiCapabilities": native_caps,
            "modifiedOriginal": False,
        }

    try:
        before_hash = sha256_file(source_pdf)
    except PermissionError as exc:
        return pdf_export_permission_response(source_pdf, native_caps, exc)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    output_pdf = PDF_EXPORT_DIR / pdf_export_filename(source_pdf, book_md5, stamp)
    try:
        export_result = run_pymupdf_highlight_copy(python, source_pdf, output_pdf, queries)
    except Exception as exc:
        try:
            after_hash = sha256_file(source_pdf)
        except PermissionError as perm_exc:
            return pdf_export_permission_response(source_pdf, native_caps, perm_exc)
        return {
            "ok": False,
            "message": f"导出失败：PyMuPDF 写入副本时出错；原始 PDF {'未修改' if after_hash == before_hash else '可能已变化'}。",
            "reply": f"导出标注 PDF 失败：{exc}\n\n原始 PDF 哈希变化：{after_hash != before_hash}",
            "backend": "local:pymupdf-highlight-copy",
            "status": "EXPORT_ERROR",
            "nativeApiCapabilities": native_caps,
            "sourcePdf": str(source_pdf),
            "modifiedOriginal": after_hash != before_hash,
            "sourceSha256Before": before_hash,
            "sourceSha256After": after_hash,
        }

    try:
        after_hash = sha256_file(source_pdf)
    except PermissionError as exc:
        return pdf_export_permission_response(source_pdf, native_caps, exc)
    annotations_created = int(export_result.get("annotations_created") or 0)
    if annotations_created <= 0:
        if output_pdf.exists():
            output_pdf.unlink()
        reply = (
            "没有导出标注版 PDF，因为选中文本没有在 PDF 正文中匹配到位置。\n\n"
            f"当前 PDF: `{source_pdf}`\n"
            f"尝试匹配的文本数: {len(queries)}\n"
            "这通常是因为 PDF 文本层和屏幕显示不一致，或选区跨列/跨页。\n\n"
            "原始 PDF 未修改。"
        )
        return {
            "ok": False,
            "message": "导出失败：没有匹配到可高亮位置；未修改原始 PDF。",
            "reply": reply,
            "backend": "local:pymupdf-highlight-copy",
            "status": "NO_TEXT_MATCH",
            "nativeApiCapabilities": native_caps,
            "sourcePdf": str(source_pdf),
            "queries": queries,
            "matches": export_result.get("matches") or [],
            "modifiedOriginal": after_hash != before_hash,
            "sourceSha256Before": before_hash,
            "sourceSha256After": after_hash,
        }

    reply = (
        "已导出标注版 PDF 副本。\n\n"
        f"- 原始 PDF: `{source_pdf}`\n"
        f"- 标注副本: `{output_pdf}`\n"
        f"- 新增高亮 annotation: {annotations_created}\n"
        f"- 原始 PDF 是否变化: {'是' if after_hash != before_hash else '否'}\n"
        f"- PyMuPDF Python: `{python}`\n\n"
        f"{native_api_capabilities_reply_block(native_caps)}\n\n"
        "这是降级导出路线：不写 MarginNote SQLite，不覆盖原文件，只在副本中写 PDF highlight annotation。"
    )
    return {
        "ok": True,
        "message": f"已导出标注 PDF 副本：{output_pdf}",
        "reply": reply,
        "backend": "local:pymupdf-highlight-copy",
        "status": "OK",
        "nativeApiCapabilities": native_caps,
        "sourcePdf": str(source_pdf),
        "outputPdf": str(output_pdf),
        "annotations_created": annotations_created,
        "rects_matched": int(export_result.get("rects_matched") or 0),
        "matches": export_result.get("matches") or [],
        "queries": queries,
        "modifiedOriginal": after_hash != before_hash,
        "sourceSha256Before": before_hash,
        "sourceSha256After": after_hash,
    }


def selection_or_prompt(payload: dict[str, Any]) -> str:
    selection = repair_pdf_extracted_math_text(str(payload.get("selectionText") or "")).strip()
    prompt = repair_pdf_extracted_math_text(str(payload.get("prompt") or "")).strip()
    if selection and prompt and prompt != selection:
        return f"{prompt}\n\n选中文本：\n{selection}"
    return selection or prompt


def looks_like_pdf_math_unicode_loss(text: str) -> bool:
    if not any(0xD400 <= ord(ch) <= 0xD7A3 for ch in text):
        return False
    math_markers = {"\u0302", "∇", "√", "⋅", "∣", "−", "=", "+", "(", ")"}
    if any(marker in text for marker in math_markers) or "log" in text:
        return True
    return bool(re.search(r"[A-Za-z0-9][\uD400-\uD7A3]|[\uD400-\uD7A3][A-Za-z0-9]", text))


def move_leading_combining_hat(text: str) -> str:
    chars = list(text)
    out: list[str] = []
    i = 0
    while i < len(chars):
        if chars[i] == "\u0302":
            j = i + 1
            while j < len(chars) and chars[j].isspace():
                j += 1
            if j < len(chars):
                out.append(chars[j])
                out.append("\u0302")
                i = j + 1
                continue
        out.append(chars[i])
        i += 1
    return "".join(out)


def repair_pdf_extracted_math_text(text: str) -> str:
    text = str(text or "")
    if not looks_like_pdf_math_unicode_loss(text):
        return text
    repaired: list[str] = []
    for ch in text:
        cp = ord(ch)
        if 0xD400 <= cp <= 0xD7A3:
            candidate = cp + 0x10000
            candidate_ch = chr(candidate)
            if unicodedata.name(candidate_ch, "").startswith("MATHEMATICAL "):
                repaired.append(candidate_ch)
                continue
        repaired.append(ch)
    return move_leading_combining_hat("".join(repaired))


def selected_context(payload: dict[str, Any]) -> str:
    parts = []
    prompt = repair_pdf_extracted_math_text(str(payload.get("prompt") or "")).strip()
    selection = repair_pdf_extracted_math_text(str(payload.get("selectionText") or "")).strip()
    note_title = repair_pdf_extracted_math_text(str(payload.get("selectedNoteTitle") or "")).strip()
    note_text = repair_pdf_extracted_math_text(str(payload.get("selectedNoteText") or "")).strip()
    if prompt:
        parts.append(f"用户输入：\n{prompt}")
    if selection:
        parts.append(f"PDF 选中文本：\n{selection}")
    if note_title or note_text:
        parts.append(f"当前选中 MN 节点：{note_title}\n{note_text[:2500]}")
    return "\n\n".join(parts).strip()


def combined_user_request(payload: dict[str, Any]) -> str:
    parts = [
        repair_pdf_extracted_math_text(str(payload.get("prompt") or "")),
        repair_pdf_extracted_math_text(str(payload.get("selectionText") or "")),
        repair_pdf_extracted_math_text(str(payload.get("selectedNoteTitle") or "")),
        repair_pdf_extracted_math_text(str(payload.get("selectedNoteText") or "")),
    ]
    return "\n".join(part for part in parts if part).strip()


def truthy_payload_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def should_include_goal_context(payload: dict[str, Any], task: str) -> bool:
    return task == "goal_run" or truthy_payload_flag(payload.get("includeGoalContext"))


def has_explicit_goal_payload(payload: dict[str, Any]) -> bool:
    return (
        isinstance(payload.get("goal"), dict)
        or bool(str(payload.get("title") or "").strip())
        or bool(str(payload.get("detail") or "").strip())
    )


def goal_context_for_model(payload: dict[str, Any], task: str) -> dict[str, str]:
    if not should_include_goal_context(payload, task):
        return {"title": "", "detail": "", "updated_at": ""}
    goal = active_goal()
    request_goal = goal_payload_from_request(payload) if has_explicit_goal_payload(payload) else {"title": "", "detail": ""}
    if request_goal["title"] or request_goal["detail"]:
        goal = {
            "title": request_goal["title"] or goal["title"],
            "detail": request_goal["detail"] or goal["detail"],
            "updated_at": goal.get("updated_at", ""),
        }
    return goal


def wants_defense_guidance(payload: dict[str, Any], task: str, goal: dict[str, str]) -> bool:
    text = combined_user_request(payload)
    if should_include_goal_context(payload, task):
        text = "\n".join(part for part in [text, goal.get("title", ""), goal.get("detail", "")] if part)
    return bool(DEFENSE_REQUEST_RE.search(text))


def is_mindmap_append_request(payload: dict[str, Any]) -> bool:
    text = combined_user_request(payload).lower()
    return any(hint in text for hint in MINDMAP_APPEND_HINTS)


def quote_markdown(text: str, limit: int = 1600) -> str:
    clipped = text[:limit]
    return "> " + clipped.replace("\n", "\n> ")


def normalize_context_scope(payload_or_value: Any) -> str:
    if isinstance(payload_or_value, dict):
        raw = (
            payload_or_value.get("contextScope")
            or payload_or_value.get("context_scope")
            or payload_or_value.get("scope")
            or "auto"
        )
    else:
        raw = payload_or_value
    key = str(raw or "auto").strip().lower()
    if key in CONTEXT_SCOPE_ALIASES:
        return CONTEXT_SCOPE_ALIASES[key]
    compact = re.sub(r"[\s-]+", "_", key)
    return CONTEXT_SCOPE_ALIASES.get(compact, "auto")


def user_prompt_context(payload: dict[str, Any]) -> str:
    prompt = repair_pdf_extracted_math_text(str(payload.get("prompt") or "")).strip()
    return f"用户输入：\n{prompt}" if prompt else ""


def selected_material_context(payload: dict[str, Any]) -> str:
    parts = []
    selection = repair_pdf_extracted_math_text(
        str(payload.get("selectionText") or payload.get("selectedText") or payload.get("activeSelectionText") or "")
    ).strip()
    note_title = repair_pdf_extracted_math_text(str(payload.get("selectedNoteTitle") or "")).strip()
    note_text = repair_pdf_extracted_math_text(str(payload.get("selectedNoteText") or "")).strip()
    if selection:
        parts.append(f"PDF 选中文本：\n{selection}")
    if note_title or note_text:
        parts.append(f"当前选中 MN 节点：{note_title}\n{note_text[:2500]}")
    return "\n\n".join(parts).strip()


def has_selected_material_context(payload: dict[str, Any]) -> bool:
    return bool(selected_material_context(payload))


def prompt_requests_document_scope(payload: dict[str, Any], task: str) -> bool:
    if task == "generate_full_reading":
        return True
    text = combined_user_request(payload)
    return bool(DOCUMENT_SCOPE_REQUEST_RE.search(text))


def effective_context_scope(payload: dict[str, Any], task: str) -> str:
    scope = normalize_context_scope(payload)
    if scope != "auto":
        return scope
    if prompt_requests_document_scope(payload, task):
        return "document"
    if has_selected_material_context(payload):
        return "selection"
    return "document"


def normalize_pdf_text(text: str) -> str:
    repaired = repair_pdf_extracted_math_text(text)
    repaired = repaired.replace("\x00", " ")
    repaired = re.sub(r"[ \t\r\f\v]+", " ", repaired)
    repaired = re.sub(r"\n{3,}", "\n\n", repaired)
    return repaired.strip()


def chunk_pdf_page_text(page: int, text: str) -> list[dict[str, Any]]:
    clean = normalize_pdf_text(text)
    if not clean:
        return []
    chunks: list[dict[str, Any]] = []
    step = max(200, PDF_TEXT_CHUNK_MAX_CHARS - PDF_TEXT_CHUNK_OVERLAP_CHARS)
    start = 0
    while start < len(clean) and len(chunks) < PDF_TEXT_MAX_CHUNKS:
        end = min(len(clean), start + PDF_TEXT_CHUNK_MAX_CHARS)
        snippet = clean[start:end].strip()
        if snippet:
            chunks.append({"page": page, "start": start, "end": end, "text": snippet})
        if end >= len(clean):
            break
        start += step
    return chunks


def build_pdf_text_cache_record(source_pdf: Path, book_md5: str, source_sha: str, pages: list[dict[str, Any]]) -> dict[str, Any]:
    chunks: list[dict[str, Any]] = []
    for item in pages:
        try:
            page = int(item.get("page") or 0)
        except Exception:
            page = 0
        if page <= 0:
            continue
        chunks.extend(chunk_pdf_page_text(page, str(item.get("text") or "")))
        if len(chunks) >= PDF_TEXT_MAX_CHUNKS:
            chunks = chunks[:PDF_TEXT_MAX_CHUNKS]
            break
    return {
        "bookmd5": book_md5,
        "sourcePdf": str(source_pdf),
        "sourceSha256": source_sha,
        "pageCount": len(pages),
        "chunkCount": len(chunks),
        "extractedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "chunks": chunks,
    }


def pdf_text_cache_path(book_md5: str, source_sha: str) -> Path:
    safe_book = pdf_cache_key(book_md5) or "document"
    safe_sha = re.sub(r"[^A-Fa-f0-9]+", "", source_sha)[:16] or "unknown"
    return PDF_TEXT_CACHE_DIR / f"{safe_book}-{safe_sha}.json"


def extract_pdf_pages_with_pymupdf(python: Path, source_pdf: Path) -> list[dict[str, Any]]:
    script = r"""
import json
import sys

import fitz

source = sys.argv[1]
doc = fitz.open(source)
pages = []
try:
    for index in range(len(doc)):
        page = doc[index]
        pages.append({"page": index + 1, "text": page.get_text("text") or ""})
finally:
    doc.close()

print(json.dumps({"pages": pages}, ensure_ascii=False))
"""
    completed = subprocess.run(
        [str(python), "-c", script, str(source_pdf)],
        text=True,
        capture_output=True,
        timeout=90,
        check=True,
    )
    data = json.loads(completed.stdout or "{}")
    pages = data.get("pages")
    return pages if isinstance(pages, list) else []


def is_macos_file_permission_error(exc: Exception) -> bool:
    text = str(exc)
    return isinstance(exc, PermissionError) or "Operation not permitted" in text or "权限" in text


def ensure_pdf_text_cache(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    book_md5 = normalize_book_md5(payload)
    source_pdf, source_error = resolve_pdf_source(payload, book_md5)
    if not source_pdf:
        append_diagnostic_log(
            "warn",
            "pdf.resolve",
            source_error or "当前文档没有可读取的 PDF 路径或缓存。",
            payload=payload,
            extra={
                "bookmd5": book_md5,
                "searchRoots": summarize_pdf_search_roots(pdf_source_search_roots(), limit=12),
            },
            request_id=str(payload.get("_request_id") or ""),
        )
        return None, source_error or "当前文档没有可读取的 PDF 路径或缓存。"
    append_diagnostic_log(
        "info",
        "pdf.resolve",
        "已解析当前文档 PDF 路径。",
        payload=payload,
        extra={"bookmd5": book_md5, "sourcePdf": str(source_pdf)},
        request_id=str(payload.get("_request_id") or ""),
    )
    try:
        source_sha = sha256_file(source_pdf)
    except Exception as exc:
        message = f"读取 PDF 哈希失败：{exc}"
        if is_macos_file_permission_error(exc):
            cache_request = request_pdf_cache(payload)
            if cache_request.get("ok"):
                return None, (
                    f"{message}\n\n"
                    "已自动请求 MN4 插件缓存当前 PDF。保持该文档在 MarginNote 4 中打开，"
                    "插件轮询后会由 MN4 进程读取 PDF 并上传到 Companion 缓存；缓存完成后再发送一次即可读取全文。"
                )
        return None, message
    cache_path = pdf_text_cache_path(book_md5 or source_sha[:16], source_sha)
    cached = read_json_file(cache_path, {})
    if isinstance(cached, dict) and cached.get("sourceSha256") == source_sha and isinstance(cached.get("chunks"), list):
        return cached, None
    python, dependency_error = find_pymupdf_python()
    if not python:
        return None, dependency_error or "PyMuPDF 不可用，无法读取 PDF 全文。"
    try:
        pages = extract_pdf_pages_with_pymupdf(python, source_pdf)
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        return None, f"PDF 全文抽取失败：{detail[:800]}"
    except Exception as exc:
        return None, f"PDF 全文抽取失败：{exc}"
    record = build_pdf_text_cache_record(source_pdf, book_md5, source_sha, pages)
    PDF_TEXT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    write_json_file(cache_path, record)
    return record, None


def document_query_terms(query: str) -> list[str]:
    text = repair_pdf_extracted_math_text(query).casefold()
    terms: list[str] = []
    seen: set[str] = set()
    for phrase in document_query_label_phrases(query):
        if phrase not in seen:
            seen.add(phrase)
            terms.append(phrase)
    for term in re.findall(r"[a-z0-9][a-z0-9_\-]{1,}", text):
        if term not in seen:
            seen.add(term)
            terms.append(term)
    chinese_chars = re.findall(r"[\u4e00-\u9fff]", query)
    for index in range(max(0, len(chinese_chars) - 1)):
        term = "".join(chinese_chars[index : index + 2])
        if term not in seen:
            seen.add(term)
            terms.append(term)
    return terms[:40]


def normalize_label_text(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", repair_pdf_extracted_math_text(text).casefold()).strip()


def document_query_label_phrases(query: str) -> list[str]:
    labels: list[str] = []
    seen: set[str] = set()
    normalized_kinds = {
        "fig": "figure",
        "figure": "figure",
        "table": "table",
        "tab": "table",
        "algorithm": "algorithm",
        "alg": "algorithm",
        "section": "section",
        "sec": "section",
        "equation": "equation",
        "eq": "equation",
    }
    for match in re.finditer(
        r"\b(fig(?:ure)?|tab(?:le)?|alg(?:orithm)?|sec(?:tion)?|eq(?:uation)?)\.?\s*([0-9]+[a-z]?)\b",
        repair_pdf_extracted_math_text(query),
        re.I,
    ):
        kind = normalized_kinds.get(match.group(1).casefold().rstrip("."), match.group(1).casefold())
        number = match.group(2).casefold()
        for phrase in (f"{kind} {number}", f"{kind}{number}"):
            normalized = normalize_label_text(phrase)
            if normalized and normalized not in seen:
                seen.add(normalized)
                labels.append(normalized)
    for match in re.finditer(r"(图|表|算法|公式|式)\s*([0-9]+[a-z]?)", query, re.I):
        number = match.group(2).casefold()
        english_kind = {"图": "figure", "表": "table", "算法": "algorithm", "公式": "equation", "式": "equation"}.get(match.group(1), "")
        if english_kind:
            normalized = normalize_label_text(f"{english_kind} {number}")
            if normalized and normalized not in seen:
                seen.add(normalized)
                labels.append(normalized)
    return labels


def score_document_chunk(chunk: dict[str, Any], terms: list[str]) -> float:
    text = str(chunk.get("text") or "").casefold()
    if not text:
        return 0.0
    label_text = normalize_label_text(str(chunk.get("text") or ""))
    try:
        page = int(chunk.get("page") or 0)
    except Exception:
        page = 0
    score = 0.0
    for term in terms:
        if not term:
            continue
        count = text.count(term.casefold())
        if " " in term and term in label_text:
            score += 25.0
        if count:
            score += 3.0 + min(count, 5)
    if page and page <= 3:
        score += 0.5
    return score


def retrieved_document_context_from_cache(record: dict[str, Any], query: str, max_chars: int = DOCUMENT_CONTEXT_MAX_CHARS) -> str:
    chunks = record.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        return ""
    terms = document_query_terms(query)
    label_phrases = document_query_label_phrases(query)
    scored: list[tuple[float, int, int, dict[str, Any]]] = []
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            continue
        try:
            page = int(chunk.get("page") or 999999)
        except Exception:
            page = 999999
        scored.append((score_document_chunk(chunk, terms), page, index, chunk))
    selected: list[tuple[float, int, int, dict[str, Any]]] | None = None
    if label_phrases:
        exact_label_matches = [
            item
            for item in scored
            if any(phrase in normalize_label_text(str(item[3].get("text") or "")) for phrase in label_phrases)
        ]
        if exact_label_matches:
            selected = sorted(exact_label_matches, key=lambda item: (-item[0], item[1], item[2]))[:4]
    if selected is None:
        positive = [item for item in scored if item[0] > 0]
        if positive:
            selected = sorted(positive, key=lambda item: (-item[0], item[1], item[2]))[:8]
        else:
            selected = sorted(scored, key=lambda item: (item[1], item[2]))[:6]
    selected = sorted(selected, key=lambda item: (item[1], item[2]))
    lines = [
        "当前文档全文检索片段：",
        "说明：以下是按你的问题从 PDF 全文缓存中取出的相关片段，不是完整逐字全文。",
    ]
    used = len("\n".join(lines))
    seen_keys: set[tuple[int, int]] = set()
    for _, page, _, chunk in selected:
        start = int(chunk.get("start") or 0)
        key = (page, start)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        snippet = normalize_pdf_text(str(chunk.get("text") or ""))
        if not snippet:
            continue
        block = f"\n[第{page}页]\n{snippet}"
        if used + len(block) > max_chars:
            remaining = max_chars - used - len(f"\n[第{page}页]\n")
            if remaining <= 200:
                break
            block = f"\n[第{page}页]\n{snippet[:remaining].rstrip()}"
        lines.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(lines).strip()


def document_context_for_model(
    payload: dict[str, Any],
    query: str,
    max_chars: int = DOCUMENT_CONTEXT_MAX_CHARS,
) -> dict[str, Any]:
    record, error_message = ensure_pdf_text_cache(payload)
    if not record:
        return {"ok": False, "text": "", "error": error_message or "无法读取当前文档全文。"}
    text = retrieved_document_context_from_cache(record, query, max_chars=max_chars)
    if not text:
        return {"ok": False, "text": "", "error": "当前 PDF 已读取，但没有抽取到可用文本。"}
    return {
        "ok": True,
        "text": text,
        "sourcePdf": str(record.get("sourcePdf") or ""),
        "pageCount": int(record.get("pageCount") or 0),
        "chunkCount": int(record.get("chunkCount") or 0),
    }


def build_model_input(payload: dict[str, Any], task: str) -> str:
    requested_scope = normalize_context_scope(payload)
    scope = effective_context_scope(payload, task)
    prompt_context = user_prompt_context(payload)
    material_context = selected_material_context(payload)
    context_blocks: list[str] = []
    if prompt_context:
        context_blocks.append(prompt_context)
    if scope == "selection":
        if material_context:
            context_blocks.append(material_context)
        elif not prompt_context:
            context_blocks.append("没有选中文本或节点。")
    else:
        document_query = repair_pdf_extracted_math_text(str(payload.get("prompt") or "")).strip()
        if not document_query:
            document_query = combined_user_request(payload) if requested_scope != "document" else ""
        document_context = document_context_for_model(payload, document_query)
        if document_context.get("text"):
            context_blocks.append(str(document_context.get("text") or ""))
        else:
            context_blocks.append(f"全文读取状态：{document_context.get('error') or '无法读取当前文档全文。'}")
    goal = goal_context_for_model(payload, task)
    files_context = uploaded_context_excerpt()
    task_desc = {
        "chat": "回答用户关于当前内容、选中文本或 MN 节点的问题。",
        "goal_run": "启动并推进用户给出的一次性目标；目标上下文只用于本次目标执行和显式目标队列任务。",
        "generate_card": "生成一张适合写入 MarginNote 的中文精读卡片，包含原文角色、概念拆解、公式/notation、证据边界和可追溯原文线索。",
        "generate_mindmap": (
            "生成当前材料的完整结构化脑图大纲，目标是接近 MarginNote 自带 AI 的全文大纲效果。"
            "必须覆盖全文章节、核心问题、方法链条、关键证据、实验/案例、局限和结论边界；"
            "输出必须使用 Markdown 层级：`##` 一级主题，`###` 二级主题，`####` 三级细节点。"
            "长文或论文应尽量形成 5-8 个一级主题、18-30 个二级主题、40-80 个三级细节点；"
            "短文按材料规模压缩，但不能只给两三层空泛节点。"
            "每个叶子节点用 1-2 句写清依据、原文线索、页码或图表编号；"
            "最后单独写一行覆盖统计，格式为：覆盖统计：覆盖 X 个章节，包含 Y 个二级主题和 Z 个三级细节点。"
            "不要输出固定模板，不要在没有依据时补全固定栏目。"
        ),
        "generate_full_reading": "生成当前材料的中文精读卡片、脑图和讲解稿，要求结构完整、边界准确、可直接用于 MarginNote。",
        "expand_node": (
            "围绕当前选中的 MarginNote 节点生成可追加的子节点。"
            "只展开当前节点，不重建整篇脑图；输出必须使用 Markdown 二级标题 `## 子节点标题`，"
            "标题下面写该子节点的简短正文、原文线索和可追问方向。"
        ),
        "reorganize_mindmap": (
            "根据当前选中的 MarginNote 节点及其内容，生成一个非破坏性的重组建议分支。"
            "不要要求删除原节点；输出必须使用 Markdown 二级标题 `## 新分组标题`，"
            "标题下面写分组依据、应包含的内容和迁移建议。"
        ),
    }.get(task, "回答用户问题。")
    if task == "generate_mindmap" and is_mindmap_append_request(payload):
        task_desc = (
            "把用户提供的新内容整理成一个可追加到当前选中 MarginNote 脑图节点下的分支。"
            "不要重建整篇模板脑图；优先输出新增节点、补充解释和应挂接的位置。"
            "输出必须使用 Markdown 层级：`##` 新增分支，`###` 二级主题，`####` 三级细节点；"
            "末尾给覆盖统计，说明本次追加覆盖了多少个二级主题和三级细节点。"
        )
    if wants_defense_guidance(payload, task, goal):
        task_desc += " 用户明确要求答辩、汇报或讲稿时，请单独给出可口述版本，并标清证据边界。"

    sections = [
        f"任务：{task_desc}",
        f"当前 topic id: {normalize_topic_id(payload)}\n当前 book md5: {normalize_book_md5(payload)}",
        f"上下文范围：用户选择 {requested_scope}，本次实际使用 {scope}。",
    ]
    if should_include_goal_context(payload, task) and (goal["title"] or goal["detail"]):
        goal_lines = [f"当前目标：{goal['title'] or '未命名目标'}"]
        if goal["detail"]:
            goal_lines.append(goal["detail"])
        sections.append("\n".join(goal_lines))
    sections.append("\n\n".join(context_blocks).strip() or "没有选中文本。")
    if files_context and (scope != "document" or truthy_payload_flag(payload.get("includeUploadedContext"))):
        sections.append(f"用户上传文件：\n{files_context}")
    elif files_context and scope == "document":
        sections.append("用户上传文件：本次选择全文模式，已忽略历史上传文件；如需结合上传文件，请在问题里明确说明。")
    elif scope != "document":
        sections.append("用户上传文件：\n无上传文件。")
    sections.append("请用中文回答，直接、细致；区分材料事实、推断和你的解释，不要编造页码、实验数值或材料没有声称的结论。")
    return "\n\n".join(sections)


def extract_response_text(data: dict[str, Any]) -> str:
    direct = data.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()
    chunks: list[str] = []
    for item in data.get("output", []) if isinstance(data.get("output"), list) else []:
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
            if not isinstance(content, dict):
                continue
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def call_codex_cli(payload: dict[str, Any], task: str) -> tuple[str | None, str]:
    settings = runtime_settings()
    cli = codex_cli_status(settings)
    path = str(cli.get("path") or "")
    if not cli.get("available"):
        detail = f"Codex CLI 不可用：{path or '未找到 codex 可执行文件'}。请确认 Codex CLI 已安装并已登录。"
        return detail, "codex-cli-error"
    prompt = (
        "你是 MarginNote 4 插件中的 Codex 助手。"
        "本次调用只输出中文回答文本，不要修改本机文件，不要运行命令，不要创建补丁。"
        "请区分材料事实、推断和解释，不要编造页码或实验数值。\n\n"
        + build_model_input(payload, task)
    )
    speed = sanitize_speed(settings.get("speed"))
    timeout = CODEX_CLI_TIMEOUTS[speed]
    reasoning = CODEX_CLI_REASONING[speed]
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CONTROL_DIR / f"codex-cli-output-{uuid.uuid4().hex}.txt"
    process = None
    try:
        process = subprocess.Popen(
            [
                path,
                "exec",
                "--sandbox",
                "read-only",
                "-m",
                settings["model"],
                "-c",
                f"model_reasoning_effort={reasoning}",
                "--skip-git-repo-check",
                "--output-last-message",
                str(output_path),
                prompt,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(ROOT),
            env=codex_cli_env(settings),
            start_new_session=True,
        )
        register_current_generation_process(process, "codex-cli")
        stdout, stderr = process.communicate(input="", timeout=timeout)
        returncode = process.returncode
    except subprocess.TimeoutExpired:
        cancel_current_generation_process()
        return f"Codex CLI 调用超时（{timeout}s）。自动模式会回退到其他后端；强制 CLI 时请检查 CLI 登录状态。", "codex-cli-error"
    except Exception as exc:
        return f"Codex CLI 调用失败：{exc}", "codex-cli-error"
    finally:
        if process is not None:
            clear_current_generation_process(process)
    final_text = ""
    try:
        final_text = output_path.read_text(encoding="utf-8").strip() if output_path.exists() else ""
    finally:
        try:
            output_path.unlink()
        except FileNotFoundError:
            pass
    stdout = (stdout or "").strip()
    stderr = (stderr or "").strip()
    if returncode == 0 and final_text:
        return final_text, "codex-cli"
    if returncode == 0 and stdout and "stream error:" not in stdout and "requires a newer version of Codex" not in stdout:
        return stdout, "codex-cli"
    detail = stdout or stderr or "Codex CLI 返回为空。"
    if len(detail) > 1400:
        detail = detail[:1400] + "..."
    return f"Codex CLI 调用失败或无输出：{detail}", "codex-cli-error"


def call_openai(payload: dict[str, Any], task: str) -> tuple[str | None, str]:
    api_key = get_setting("OPENAI_API_KEY")
    if not api_key:
        return None, "local"
    settings = runtime_settings()
    model = settings["model"]
    model_input = build_model_input(payload, task)
    history = history_for_model(payload, model_input)
    input_items: list[dict[str, Any]] = [
        {
            "role": "developer",
            "content": (
                "你是嵌入 MarginNote 的 Codex 助手。回答必须面向当前内容和用户明确请求，"
                "区分材料事实、推断和你的解释；不要编造页码、实验数值或材料没有声称的结论。"
            ),
        }
    ]
    for item in history:
        input_items.append({"role": item["role"], "content": item["content"]})
    input_items.append({"role": "user", "content": model_input})
    body = {
        "model": model,
        "input": input_items,
        "max_output_tokens": int(get_setting("OPENAI_MAX_OUTPUT_TOKENS", str(SPEED_MAX_OUTPUT_TOKENS[settings["speed"]]))),
    }
    req = request.Request(
        OPENAI_RESPONSES_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen_with_proxy(req, settings, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return f"OpenAI API 请求失败：HTTP {exc.code}\n\n{detail[:1200]}", "openai-error"
    except Exception as exc:
        return f"OpenAI API 请求失败：{exc}", "openai-error"
    text = extract_response_text(data)
    return (text or "OpenAI API 返回为空。"), f"openai:{model}"


def urlopen_with_proxy(req: request.Request, settings: dict[str, str], timeout: float):
    proxy_url = sanitize_proxy_url(settings.get("proxyUrl", ""))
    if not proxy_url:
        return request.urlopen(req, timeout=timeout)
    opener = request.build_opener(request.ProxyHandler({"http": proxy_url, "https": proxy_url}))
    return opener.open(req, timeout=timeout)


def generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
    settings = runtime_settings()
    backend_choice = sanitize_ai_backend(settings.get("aiBackend"))
    cli_error_text = ""
    unavailable = (
        "真实 AI 后端不可用：当前没有可用的 Codex CLI 或 OpenAI API。"
        "请在设置中选择本机 Codex CLI，或配置 OpenAI Key 后重试。"
        "为避免内置模板冒充模型回答，本版本不会用本地规则生成问答、卡片或脑图内容。"
    )
    if backend_choice == "local":
        return unavailable, "ai-unavailable"
    if backend_choice in {"codex_cli", "auto"}:
        text, backend = call_codex_cli(payload, task)
        if text and backend != "codex-cli-error":
            return text, backend
        if backend_choice == "codex_cli":
            return text or "Codex CLI 未返回内容。", "codex-cli-error"
        if backend == "codex-cli-error":
            cli_error_text = text or "Codex CLI 调用失败。"
    if backend_choice in {"openai_api", "auto"}:
        text, backend = call_openai(payload, task)
        if text and backend != "openai-error":
            return text, backend
        if backend_choice == "openai_api":
            return text or "OpenAI API 未返回内容。", backend
    if cli_error_text:
        return cli_error_text, "codex-cli-error"
    return unavailable, "ai-unavailable"


def generation_backend_unavailable(backend: str) -> bool:
    return backend == "ai-unavailable" or backend == "local" or backend.endswith("-error")


def chat(payload: dict[str, Any]) -> dict[str, Any]:
    text = selection_or_prompt(payload)
    reply, backend = generate_reply(payload, "chat")
    stopped = stop_response_after_generation(str(payload.get("action") or "chat"))
    if stopped:
        return stopped
    append_history(payload, text, reply)
    return {
        "ok": True,
        "message": f"已生成对话回复（{backend}）。",
        "reply": reply,
        "backend": backend,
    }


def goal_text(goal: dict[str, str], payload: dict[str, Any]) -> str:
    return "\n".join(
        part
        for part in [
            str(goal.get("title") or ""),
            str(goal.get("detail") or ""),
            str(payload.get("prompt") or ""),
        ]
        if part
    )


def goal_queue_prompt(goal: dict[str, str], payload: dict[str, Any], label: str) -> str:
    context = selected_context(payload)
    parts = [
        f"目标：{goal.get('title') or '未命名目标'}",
        str(goal.get("detail") or "").strip(),
        f"当前自动拆分子任务：{label}",
    ]
    if context:
        parts.append(f"当前 MarginNote 上下文：\n{context}")
    parts.append("请只产出这个子任务需要的内容，保持短、结构化，并适合写回当前 MarginNote 位置。")
    return "\n\n".join(part for part in parts if part).strip()[:4200]


def infer_goal_queue(goal: dict[str, str], payload: dict[str, Any]) -> list[dict[str, str]]:
    text = goal_text(goal, payload)
    items: list[tuple[str, str]] = []

    def add(action: str, label: str) -> None:
        if not any(existing_action == action for existing_action, _ in items):
            items.append((action, label))

    if re.search(r"精读|全文|完整|深度|讲稿|defense|答辩|full[-\s]?reading", text, re.I):
        add("generate_full_reading", "完整精读和讲稿")
    if re.search(r"卡片|制卡|笔记卡|短卡|card", text, re.I):
        add("generate_card", "生成短卡片")
    if re.search(r"脑图|mind\s?map|mindmap", text, re.I):
        add("generate_mindmap", "生成或补充脑图")
    if re.search(r"展开|扩展|继续展开|expand|extend", text, re.I) and re.search(r"节点|node", text, re.I):
        add("expand_node", "补脑图")
    if re.search(r"重组|重排|重新组织|整理.*脑图|归类|reorganize|restructure|regroup", text, re.I):
        add("reorganize_mindmap", "重组当前脑图")
    if re.search(r"高亮|highlight", text, re.I):
        add("diagnose_highlights", "检查高亮状态")
    if re.search(r"导出|export|标注版|annotated", text, re.I) and re.search(r"pdf", text, re.I):
        add("export_annotated_pdf", "导出标注版 PDF")

    return [
        {
            "action": action,
            "title": label,
            "prompt": goal_queue_prompt(goal, payload, label),
        }
        for action, label in items[:6]
    ]


def run_goal(payload: dict[str, Any]) -> dict[str, Any]:
    stopped = stopped_response_if_needed("goal_run")
    if stopped:
        return stopped
    goal_payload = goal_payload_from_request(payload)
    if not goal_payload["title"] and not goal_payload["detail"]:
        return {"ok": False, "message": "目标为空。", "reply": "先输入一个目标，再点击执行目标。"}
    goal = one_shot_goal(goal_payload)
    clear_goal()
    prompt_parts = [f"目标：{goal['title']}"]
    if goal["detail"]:
        prompt_parts.append(goal["detail"])
    original_prompt = str(payload.get("prompt") or "").strip()
    if original_prompt and original_prompt not in "\n\n".join(prompt_parts):
        prompt_parts.append(original_prompt)
    prompt_parts.append("请开始执行这个目标。先说明当前理解、下一步动作和可直接产出的内容；如果需要持续推进，请给出后续引导。")
    run_payload = dict(payload)
    run_payload["action"] = "goal_run"
    run_payload["prompt"] = "\n\n".join(prompt_parts)
    result = chat(run_payload)
    goal_queue = infer_goal_queue(goal, payload)
    result["goal"] = goal
    result["activeGoal"] = active_goal()
    result["goalOneShot"] = True
    result["goalQueue"] = goal_queue
    if result.get("ok"):
        result["message"] = f"已启动目标：{goal['title']}"
        if result.get("reply"):
            result["reply"] = f"目标：{goal['title']}\n\n{result['reply']}"
        if goal_queue:
            queue_lines = "\n".join(f"- {item['title']}：{item['action']}" for item in goal_queue)
            result["reply"] = (
                f"{result.get('reply') or ''}\n\n"
                f"已自动拆分为 {len(goal_queue)} 个后续任务，会由 Web 面板加入队列：\n{queue_lines}"
            ).strip()
    return result


def truncate_text(text: str, limit: int) -> str:
    value = str(text or "").strip()
    if len(value) <= limit:
        return value
    return value[: max(0, limit - 3)].rstrip() + "..."


def plain_context_excerpt(text: str, limit: int = CARD_SOURCE_EXCERPT_MAX_CHARS) -> str:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    return truncate_text(value, limit)


def fallback_card_sections(reply: str) -> list[dict[str, str]]:
    value = str(reply or "").strip()
    if not value:
        return [{"title": "精读笔记", "body": "模型未返回可拆分内容。"}]
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", value) if part.strip()]
    if len(paragraphs) >= 2:
        return [
            {"title": clean_mindmap_node_title(paragraph.splitlines()[0], 40), "body": paragraph}
            for paragraph in paragraphs[:6]
        ]
    compact_sections = compact_card_sections(value)
    if compact_sections:
        return compact_sections
    return [{"title": "精读笔记", "body": value}]


def compact_card_sections(text: str, target: int = CARD_FALLBACK_SECTION_TARGET_CHARS) -> list[dict[str, str]]:
    value = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(value) <= target * 2:
        return []
    sentences = [part.strip() for part in re.split(r"(?<=[。！？!?；;])\s*", value) if part.strip()]
    if len(sentences) < 3:
        sentences = [value[i : i + target] for i in range(0, len(value), target)]
    sections: list[dict[str, str]] = []
    current = ""
    for sentence in sentences:
        candidate = (current + sentence).strip()
        if current and len(candidate) > target:
            sections.append({"title": f"精读笔记 {len(sections) + 1:02d}", "body": current})
            current = sentence
        else:
            current = candidate
        if len(sections) >= 5:
            break
    if current and len(sections) < 6:
        sections.append({"title": f"精读笔记 {len(sections) + 1:02d}", "body": current})
    return sections if len(sections) >= 2 else []


def build_card_body(section_body: str, source_text: str, backend: str, payload: dict[str, Any]) -> str:
    source = plain_context_excerpt(source_text)
    footer = f"\n\n---\n生成来源：`{backend}`；topic `{normalize_topic_id(payload)}`。"
    source_block = f"\n\n## 来源线索\n\n{source}" if source else ""
    budget = CARD_BODY_MAX_CHARS - len("## 要点\n\n") - len(source_block) - len(footer)
    body = truncate_text(section_body, max(180, budget))
    final = f"## 要点\n\n{body}{source_block}{footer}"
    return truncate_text(final, CARD_BODY_MAX_CHARS)


def build_short_cards(text: str, reply: str, backend: str, payload: dict[str, Any]) -> list[dict[str, str]]:
    sections = markdown_heading_sections(reply) or bullet_sections(reply) or fallback_card_sections(reply)
    cards: list[dict[str, str]] = []
    for index, section in enumerate(sections[:6], 1):
        title = clean_mindmap_node_title(section.get("title") or f"精读笔记 {index}", 34)
        body = build_card_body(section.get("body") or reply, text, backend, payload)
        cards.append({"title": f"Codex短卡 {index:02d}：{title}", "body": body})
    return cards or [{"title": "Codex短卡 01：精读笔记", "body": build_card_body(reply, text, backend, payload)}]


def generate_card(payload: dict[str, Any]) -> dict[str, Any]:
    text = selection_or_prompt(payload)
    if not text:
        return {"ok": False, "message": "没有选中文本或输入 prompt，未生成卡片。"}
    reply, backend = generate_reply(payload, "generate_card")
    stopped = stop_response_after_generation("generate_card")
    if stopped:
        return stopped
    if generation_backend_unavailable(backend):
        message = "未生成卡片：需要可用的 Codex CLI 或 OpenAI 后端。"
        append_history(payload, text, message)
        return {
            "ok": False,
            "message": message,
            "reply": f"{message}\n\n后端状态：{backend}\n\n{reply}",
            "backend": backend,
        }
    cards = build_short_cards(text, reply, backend, payload)
    append_history(payload, text, reply)
    return {
        "ok": True,
        "message": f"已返回 {len(cards)} 张可写入 MN4 的短卡片（{backend}）。",
        "reply": reply,
        "backend": backend,
        "cards": cards,
    }


def clean_mindmap_node_title(text: str, limit: int = 64) -> str:
    title = re.sub(r"^[#*\-\s\d.、)）]+", "", str(text or "")).strip()
    title = re.sub(r"[:：]\s*$", "", title).strip()
    title = re.sub(r"^[`*_]+|[`*_]+$", "", title).strip()
    title = re.sub(r"(\*\*|__|`)", "", title).strip()
    title = re.sub(r"\s+", " ", title)
    return title[:limit] or "模型生成节点"


def selected_node_title(payload: dict[str, Any], limit: int = 40) -> str:
    title = clean_mindmap_node_title(str(payload.get("selectedNoteTitle") or ""), limit)
    return "" if title == "模型生成节点" else title


def selected_node_write_target(payload: dict[str, Any], operation: str) -> dict[str, str]:
    title = selected_node_title(payload)
    note_id = str(payload.get("selectedNoteId") or "").strip()
    label = f"当前选中节点：{title}" if title else "当前选中节点"
    return {
        "mode": "merge_children_into_selected_node",
        "operation": operation,
        "label": label,
        "selectedNoteId": note_id,
        "selectedNoteTitle": title,
    }


def mindmap_document_key(payload: dict[str, Any]) -> str:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id or not book_md5:
        return ""
    return f"{topic_id}:{book_md5}"


def mindmap_document_title(payload: dict[str, Any]) -> str:
    for key in ("documentTitle", "bookTitle", "title", "sourceFileName", "fileName", "pdfName"):
        value = str(payload.get(key) or "").strip()
        if value:
            break
    else:
        value = normalize_book_md5(payload) or "当前文档"
    value = value.replace("\x00", "").replace("/", "／").strip()
    if value.lower().endswith(".pdf"):
        value = value[:-4].strip()
    return value or "当前文档"


def stable_mindmap_codex_id(document_key: str) -> str:
    digest = hashlib.sha256(str(document_key or "").encode("utf-8")).hexdigest()[:16]
    return f"mindmap-target:{digest}"


def default_document_mindmap_title(payload: dict[str, Any]) -> str:
    return f"{mindmap_document_title(payload)} · Codex 脑图"


def document_root_mindmap_target(payload: dict[str, Any]) -> dict[str, Any]:
    document_key = mindmap_document_key(payload)
    root_title = default_document_mindmap_title(payload)
    return {
        "mode": "document_root",
        "operation": "append_to_document_mindmap_root",
        "label": f"文档脑图：{root_title}",
        "rootTitle": root_title,
        "codexId": stable_mindmap_codex_id(document_key),
        "documentKey": document_key,
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
    }


def read_mindmap_targets() -> dict[str, Any]:
    data = read_json_file(MINDMAP_TARGETS_PATH, {})
    if not isinstance(data, dict):
        data = {}
    bindings = data.get("bindings") if isinstance(data.get("bindings"), dict) else {}
    return {"bindings": bindings}


def write_mindmap_targets(data: dict[str, Any]) -> None:
    bindings = data.get("bindings") if isinstance(data.get("bindings"), dict) else {}
    write_json_file(MINDMAP_TARGETS_PATH, {"bindings": bindings})


def normalize_mindmap_target(payload: dict[str, Any], target: Any) -> dict[str, Any]:
    if not isinstance(target, dict):
        return {}
    mode = str(target.get("mode") or target.get("targetMode") or "").strip()
    if mode in {"selected_node", "merge_selected", "merge_children_into_selected_node"}:
        note_payload = dict(payload)
        for key in ("selectedNoteId", "selectedNoteTitle", "selectedNoteText"):
            if target.get(key):
                note_payload[key] = target.get(key)
        note_target = selected_node_write_target(note_payload, str(target.get("operation") or "append_to_current_mindmap"))
        label = str(target.get("label") or "").strip()
        if label:
            note_target["label"] = label
        return note_target
    if mode == "document_root":
        root_target = document_root_mindmap_target(payload)
        for key in ("rootTitle", "label", "codexId", "documentKey", "topicid", "bookmd5"):
            value = target.get(key)
            if value:
                root_target[key] = str(value)
        root_target["mode"] = "document_root"
        root_target["operation"] = str(target.get("operation") or root_target.get("operation") or "append_to_document_mindmap_root")
        return root_target
    return {}


def mindmap_target_options(payload: dict[str, Any], current_target: dict[str, Any] | None = None) -> list[dict[str, str]]:
    options = [
        {
            "value": "document_root",
            "label": default_document_mindmap_title(payload),
            "detail": "为当前文档固定一棵 Codex 脑图；已有根节点时追加到该根下。",
        }
    ]
    current_target = current_target if isinstance(current_target, dict) else {}
    selected_saved = current_target if current_target.get("mode") == "merge_children_into_selected_node" else {}
    if selected_saved or has_selected_node_context(payload):
        target = selected_saved or selected_node_write_target(payload, "append_to_current_mindmap")
        options.append(
            {
                "value": "selected_node",
                "label": target["label"],
                "detail": "把新节点追加到当前选中的脑图节点下；写入前会校验仍选中同一节点。",
            }
        )
    return options


def mindmap_target_status(payload: dict[str, Any]) -> dict[str, Any]:
    document_key = mindmap_document_key(payload)
    if not document_key:
        return {
            "ok": True,
            "message": "目标脑图：未识别当前文档，暂不允许自动写入脑图。",
            "mindmapTarget": {
                "state": "blocked",
                "label": "目标脑图：未识别文档",
                "detail": "需要 MarginNote 当前文档的 notebook/topic 与 book/doc md5。",
                "target": {},
                "options": [],
            },
        }
    data = read_mindmap_targets()
    saved = data["bindings"].get(document_key)
    if isinstance(saved, dict):
        target = normalize_mindmap_target(payload, saved)
        state = "confirmed"
    else:
        target = document_root_mindmap_target(payload)
        state = "suggested"
    label = str(target.get("label") or target.get("rootTitle") or "目标脑图").strip()
    return {
        "ok": True,
        "message": f"目标脑图：{label}",
        "mindmapTarget": {
            "state": state,
            "label": label,
            "detail": "生成脑图会写入这个目标；可在顶部选择器切换。",
            "target": target,
            "options": mindmap_target_options(payload, target),
        },
    }


def update_mindmap_target(payload: dict[str, Any]) -> dict[str, Any]:
    document_key = mindmap_document_key(payload)
    if not document_key:
        return {
            "ok": False,
            "message": "无法设置目标脑图：未识别当前文档。",
            "mindmapTarget": mindmap_target_status(payload)["mindmapTarget"],
        }
    mode = str(payload.get("targetMode") or payload.get("mode") or "").strip()
    incoming = payload.get("target") if isinstance(payload.get("target"), dict) else {}
    if not mode and incoming:
        mode = str(incoming.get("mode") or incoming.get("targetMode") or "").strip()
    if mode == "clear":
        data = read_mindmap_targets()
        data["bindings"].pop(document_key, None)
        write_mindmap_targets(data)
        return mindmap_target_status(payload)
    if mode in {"selected_node", "merge_children_into_selected_node"}:
        if not has_selected_node_context(payload):
            return {
                "ok": False,
                "message": "无法设置目标脑图：请先在 MarginNote 脑图中选中一个节点。",
                "mindmapTarget": mindmap_target_status(payload)["mindmapTarget"],
            }
        target = selected_node_write_target(payload, "append_to_current_mindmap")
    else:
        target = document_root_mindmap_target(payload)
    data = read_mindmap_targets()
    data["bindings"][document_key] = target
    write_mindmap_targets(data)
    status = mindmap_target_status(payload)
    status["message"] = f"已设置目标脑图：{status['mindmapTarget']['label']}"
    status["mindmapTarget"]["state"] = "confirmed"
    return status


def resolve_mindmap_write_target(payload: dict[str, Any]) -> dict[str, Any]:
    explicit = normalize_mindmap_target(payload, payload.get("mindmapTarget"))
    if explicit:
        return explicit
    if is_mindmap_append_request(payload):
        return selected_node_write_target(payload, "append_to_current_mindmap")
    status = mindmap_target_status(payload).get("mindmapTarget", {})
    target = status.get("target") if isinstance(status, dict) else {}
    return normalize_mindmap_target(payload, target)


def node_action_root_title(payload: dict[str, Any], prefix: str) -> str:
    title = selected_node_title(payload)
    return f"{prefix}：{title}" if title else prefix


def mindmap_root_title(payload: dict[str, Any]) -> str:
    if is_mindmap_append_request(payload):
        selected = selected_node_title(payload)
        return f"补充到当前脑图：{selected}" if selected else "补充到当前脑图"
    target = resolve_mindmap_write_target(payload)
    if target.get("mode") == "document_root" and target.get("rootTitle"):
        return str(target.get("rootTitle"))
    if target.get("mode") == "merge_children_into_selected_node":
        selected = str(target.get("selectedNoteTitle") or selected_node_title(payload) or "").strip()
        return f"补充到当前脑图：{selected}" if selected else "补充到当前脑图"
    prompt = clean_mindmap_node_title(str(payload.get("prompt") or ""), 36)
    return f"Codex 脑图：{prompt}" if prompt and prompt != "模型生成节点" else "Codex 脑图"


def markdown_heading_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    current_title = ""
    body_lines: list[str] = []
    heading_re = re.compile(r"^\s{0,3}#{1,4}\s+(.+?)\s*$")
    for line in str(text or "").splitlines():
        match = heading_re.match(line)
        if match:
            if current_title:
                sections.append({"title": clean_mindmap_node_title(current_title), "body": "\n".join(body_lines).strip()})
            current_title = match.group(1)
            body_lines = []
        elif current_title:
            body_lines.append(line)
    if current_title:
        sections.append({"title": clean_mindmap_node_title(current_title), "body": "\n".join(body_lines).strip()})
    return [section for section in sections if section["title"]]


def bullet_sections(text: str) -> list[dict[str, str]]:
    sections: list[dict[str, str]] = []
    bullet_re = re.compile(r"^\s*(?:[-*+]\s+|\d+[.)、]\s*)([^:：\n]{2,80})(?:[:：]\s*(.*))?$")
    for line in str(text or "").splitlines():
        match = bullet_re.match(line)
        if not match:
            continue
        title = clean_mindmap_node_title(match.group(1))
        body = (match.group(2) or "").strip()
        if title:
            sections.append({"title": title, "body": body})
    return sections


def markdown_heading_tree(text: str) -> list[dict[str, Any]]:
    roots: list[dict[str, Any]] = []
    stack: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    body_lines: list[str] = []
    base_level: int | None = None
    heading_re = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")

    def flush_body() -> None:
        nonlocal body_lines
        if current is not None:
            body = "\n".join(body_lines).strip()
            if body:
                current["body"] = body
        body_lines = []

    for line in str(text or "").splitlines():
        match = heading_re.match(line)
        if not match:
            if current is not None:
                body_lines.append(line)
            continue
        flush_body()
        level = len(match.group(1))
        if base_level is None:
            base_level = level
        depth = max(1, level - base_level + 1)
        node: dict[str, Any] = {
            "title": clean_mindmap_node_title(match.group(2)),
            "body": "",
            "children": [],
        }
        while len(stack) >= depth:
            stack.pop()
        if stack:
            stack[-1].setdefault("children", []).append(node)
        else:
            roots.append(node)
        stack.append(node)
        current = node
    flush_body()
    return [node for node in roots if node.get("title")]


def prune_mindmap_nodes(nodes: list[dict[str, Any]], max_nodes: int = 120, max_siblings: int = 14) -> list[dict[str, Any]]:
    used = 0

    def walk(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        nonlocal used
        output: list[dict[str, Any]] = []
        for item in items[:max_siblings]:
            if used >= max_nodes:
                break
            used += 1
            node: dict[str, Any] = {
                "title": clean_mindmap_node_title(str(item.get("title") or "")),
                "body": str(item.get("body") or "").strip(),
            }
            children = item.get("children") if isinstance(item.get("children"), list) else []
            if children:
                node["children"] = walk(children)
            output.append(node)
        return output

    return walk(nodes)


def mindmap_tree_stats(nodes: list[dict[str, Any]]) -> dict[str, int]:
    stats = {"nodeCount": 0, "maxDepth": 0, "topLevelCount": len(nodes), "leafCount": 0}

    def visit(items: list[dict[str, Any]], depth: int) -> None:
        for item in items:
            stats["nodeCount"] += 1
            stats["maxDepth"] = max(stats["maxDepth"], depth)
            children = item.get("children") if isinstance(item.get("children"), list) else []
            if children:
                visit(children, depth + 1)
            else:
                stats["leafCount"] += 1

    visit(nodes, 1)
    return stats


def inline_list_sections(text: str) -> list[dict[str, str]]:
    value = str(text or "").strip()
    if "\n" in value:
        return []
    value = re.sub(r"^.*?[：:]", "", value, count=1).strip()
    value = re.sub(r"[。.!！]$", "", value).strip()
    pieces = [clean_mindmap_node_title(piece, 48) for piece in re.split(r"[、,，;；]\s*", value)]
    sections = [{"title": piece, "body": "模型输出中列出的脑图节点。"} for piece in pieces if 1 < len(piece) <= 48]
    return sections if len(sections) >= 2 else []


def model_reply_mindmap_tree(payload: dict[str, Any], reply: str) -> dict[str, Any]:
    children = prune_mindmap_nodes(markdown_heading_tree(reply))
    if not children:
        sections = bullet_sections(reply) or inline_list_sections(reply)
        if not sections:
            sections = [{"title": "模型输出", "body": str(reply or "").strip()[:1800]}]
        children = prune_mindmap_nodes(
            [{"title": section["title"], "body": section.get("body") or str(reply or "").strip()[:600]} for section in sections]
        )
    stats = mindmap_tree_stats(children)
    write_target = resolve_mindmap_write_target(payload)
    merge_into_selected = bool(
        is_mindmap_append_request(payload)
        or write_target.get("mode") == "merge_children_into_selected_node"
    )
    tree = {
        "title": mindmap_root_title(payload),
        "body": f"根据本次真实模型输出生成；未使用内置模板。节点 {stats['nodeCount']} 个，最大层级 {stats['maxDepth']}。",
        "mergeIntoSelected": merge_into_selected,
        "children": children,
        "stats": stats,
    }
    if write_target:
        tree["writeTarget"] = write_target
        if write_target.get("mode") == "document_root" and write_target.get("codexId"):
            tree["codexId"] = str(write_target.get("codexId"))
    return tree


def generate_mindmap(payload: dict[str, Any]) -> dict[str, Any]:
    text = selection_or_prompt(payload)
    stopped = stopped_response_if_needed("generate_mindmap")
    if stopped:
        return stopped
    if is_mindmap_append_request(payload) and not has_selected_node_context(payload):
        message = "请先在 MarginNote 脑图里选中一个脑图节点，再执行“补到当前脑图/合并脑图”。"
        append_history(payload, text, message)
        return {
            "ok": False,
            "message": message,
            "reply": (
                f"{message}\n\n"
                "为了避免误建一个新的脑图根节点，Codex Companion 只有拿到 selectedNoteId、"
                "selectedNoteTitle 或 selectedNoteText 后，才会把生成结果作为子节点合并进去。"
            ),
        }
    reply, backend = generate_reply(payload, "generate_mindmap")
    stopped = stop_response_after_generation("generate_mindmap")
    if stopped:
        return stopped
    if generation_backend_unavailable(backend):
        message = "未生成脑图：内置模板已关闭，需要可用的 Codex CLI 或 OpenAI 后端。"
        append_history(payload, text, message)
        return {
            "ok": False,
            "message": message,
            "reply": f"{message}\n\n后端状态：{backend}\n\n{reply}",
            "backend": backend,
        }
    tree = model_reply_mindmap_tree(payload, reply)
    stats = tree.get("stats") if isinstance(tree.get("stats"), dict) else mindmap_tree_stats(tree.get("children") or [])
    append_history(payload, text, reply)
    mode = "追加脑图分支" if is_mindmap_append_request(payload) else "脑图分支"
    result = {
        "ok": True,
        "message": f"已返回一个可写入 MN4 的{mode}（{backend}，{stats.get('nodeCount', 0)} 个节点，{stats.get('maxDepth', 0)} 层）。",
        "reply": reply,
        "backend": backend,
        "mindmap": tree,
        "mindmapStats": stats,
    }
    if isinstance(tree.get("writeTarget"), dict):
        result["writeTarget"] = tree["writeTarget"]
    return result


def has_selected_node_context(payload: dict[str, Any]) -> bool:
    return bool(
        str(payload.get("selectedNoteId") or "").strip()
        or str(payload.get("selectedNoteTitle") or "").strip()
        or str(payload.get("selectedNoteText") or "").strip()
    )


def generate_current_node_mindmap(
    payload: dict[str, Any],
    task: str,
    title_prefix: str,
    message_label: str,
    operation: str,
) -> dict[str, Any]:
    if not has_selected_node_context(payload):
        return {
            "ok": False,
            "message": "请先在 MarginNote 脑图里选中一个节点，再执行当前节点动作。",
            "reply": "当前请求需要 MN4 提供 selectedNoteId、selectedNoteTitle 或 selectedNoteText。",
        }
    text = selected_context(payload) or selection_or_prompt(payload)
    stopped = stopped_response_if_needed(task)
    if stopped:
        return stopped
    reply, backend = generate_reply(payload, task)
    stopped = stop_response_after_generation(task)
    if stopped:
        return stopped
    if generation_backend_unavailable(backend):
        message = f"未生成{message_label}：需要可用的 Codex CLI 或 OpenAI 后端。"
        append_history(payload, text, message)
        return {
            "ok": False,
            "message": message,
            "reply": f"{message}\n\n后端状态：{backend}\n\n{reply}",
            "backend": backend,
        }
    tree = model_reply_mindmap_tree(payload, reply)
    stats = tree.get("stats") if isinstance(tree.get("stats"), dict) else mindmap_tree_stats(tree.get("children") or [])
    write_target = selected_node_write_target(payload, operation)
    tree["title"] = node_action_root_title(payload, title_prefix)
    tree["body"] = "根据当前选中 MN 节点和本次真实模型输出生成；写入时只合并子节点，不替换原节点。"
    tree["mergeIntoSelected"] = True
    tree["writeTarget"] = write_target
    if task == "reorganize_mindmap":
        tree["replaceChildren"] = False
    append_history(payload, text, reply)
    return {
        "ok": True,
        "message": f"已返回可写入 MN4 的{message_label}（{backend}，{stats.get('nodeCount', 0)} 个节点，{stats.get('maxDepth', 0)} 层）。",
        "reply": reply,
        "backend": backend,
        "mindmap": tree,
        "writeTarget": write_target,
        "mindmapStats": stats,
    }


def expand_node(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_current_node_mindmap(
        payload,
        "expand_node",
        "展开当前节点",
        "展开当前节点分支",
        "expand_selected_node",
    )


def reorganize_mindmap(payload: dict[str, Any]) -> dict[str, Any]:
    return generate_current_node_mindmap(
        payload,
        "reorganize_mindmap",
        "重组当前脑图",
        "重组当前脑图分支",
        "non_destructive_reorganization_preview",
    )


def attach_card_ids(cards: list[dict[str, Any]], prefix: str) -> list[dict[str, Any]]:
    for index, card in enumerate(cards, start=1):
        card["codexId"] = f"{prefix}:card:{index:02d}"
    return cards


def attach_tree_ids(node: dict[str, Any], prefix: str, path: str = "root") -> dict[str, Any]:
    node["codexId"] = f"{prefix}:mindmap:{path}"
    children = node.get("children")
    if isinstance(children, list):
        for index, child in enumerate(children, start=1):
            if isinstance(child, dict):
                child_path = str(index) if path == "root" else f"{path}.{index}"
                attach_tree_ids(child, prefix, child_path)
    return node


def generate_full_reading(payload: dict[str, Any]) -> dict[str, Any]:
    text = selection_or_prompt(payload)
    stopped = stopped_response_if_needed("generate_full_reading")
    if stopped:
        return stopped
    reply, backend = generate_reply(payload, "generate_full_reading")
    stopped = stop_response_after_generation("generate_full_reading")
    if stopped:
        return stopped
    if generation_backend_unavailable(backend):
        message = "未生成完整精读：需要可用的 Codex CLI 或 OpenAI 后端。"
        append_history(payload, text or "完整精读", message)
        return {
            "ok": False,
            "message": message,
            "reply": f"{message}\n\n后端状态：{backend}\n\n{reply}",
            "backend": backend,
        }
    cards = attach_card_ids(build_short_cards(text or "完整精读", reply, backend, payload), "full-reading")
    target_tree = model_reply_mindmap_tree(payload, reply)
    root_codex_id = str(target_tree.get("codexId") or "")
    write_target = target_tree.get("writeTarget") if isinstance(target_tree.get("writeTarget"), dict) else {}
    tree = attach_tree_ids(target_tree, "full-reading")
    if root_codex_id.startswith("mindmap-target:"):
        tree["codexId"] = root_codex_id
    if write_target:
        tree["writeTarget"] = write_target
    append_history(payload, text or "完整精读", reply)
    result = {
        "ok": True,
        "message": f"已返回完整精读草稿：{len(cards)} 张短卡片 + 1 个脑图分支（{backend}）。",
        "reply": reply,
        "backend": backend,
        "cards": cards,
        "mindmap": tree,
    }
    if write_target:
        result["writeTarget"] = write_target
    return result


def handle_action(payload: dict[str, Any]) -> dict[str, Any]:
    action = str(payload.get("action") or "").strip()
    if action == "settings_get":
        settings = runtime_settings()
        topic_id = normalize_topic_id(payload)
        book_md5 = normalize_book_md5(payload)
        return {
            "ok": True,
            "message": "已读取插件设置。",
            "pluginVersion": CURRENT_PLUGIN_VERSION,
            "settings": settings,
            **ai_status_fields(settings),
            "goal": active_goal(),
            "files": uploaded_files(),
            "queue": queue_status_payload(topic_id, book_md5),
            "nativeApiCapabilities": latest_native_api_capabilities(topic_id, book_md5),
            "update": update_manager.read_update_status(ROOT),
        }
    if action == "settings_update":
        settings_payload = payload.get("settings") if isinstance(payload.get("settings"), dict) else payload
        settings = save_runtime_settings(settings_payload if isinstance(settings_payload, dict) else {})
        topic_id = normalize_topic_id(payload)
        book_md5 = normalize_book_md5(payload)
        return {
            "ok": True,
            "message": "插件设置已保存。",
            "pluginVersion": CURRENT_PLUGIN_VERSION,
            "reply": (
                "设置已保存。\n\n"
                f"权限：{settings['permission']}\n"
                f"模型：{settings['model']}\n"
                f"速度：{settings['speed']}\n"
                f"默认上下文：{settings['defaultContextScope']}\n"
                f"AI 后端：{ai_backend_label(settings['aiBackend'])}\n"
                f"代理：{'已配置' if settings.get('proxyUrl') else '未配置'}\n"
                f"OpenAI：{'已配置' if get_setting('OPENAI_API_KEY') else '未配置'}\n"
                f"文件路径：{len(settings.get('fileSearchRoots') or [])} 个\n"
                f"自定义按钮：{len(settings.get('customButtons') or [])}"
            ),
            "settings": settings,
            **ai_status_fields(settings),
            "goal": active_goal(),
            "files": uploaded_files(),
            "queue": queue_status_payload(topic_id, book_md5),
            "nativeApiCapabilities": latest_native_api_capabilities(topic_id, book_md5),
            "update": update_manager.read_update_status(ROOT),
        }
    if action == "update_status":
        update = update_manager.read_update_status(ROOT)
        return {"ok": True, "message": update.get("message") or "已读取更新状态。", "update": update}
    if action == "open_url":
        return open_external_url(payload)
    if action == "update_check":
        if payload.get("githubRepo"):
            save_runtime_settings({"githubRepo": payload.get("githubRepo")})
        settings = runtime_settings()
        update = update_manager.check_for_update(ROOT, settings, CURRENT_PLUGIN_VERSION)
        update_manager.write_update_status(ROOT, update)
        return {
            "ok": bool(update.get("ok")),
            "message": str(update.get("message") or "已检查更新。"),
            "reply": str(update.get("message") or "已检查更新。"),
            "pluginVersion": CURRENT_PLUGIN_VERSION,
            "update": update,
            "settings": settings,
        }
    if action == "update_install":
        if payload.get("githubRepo"):
            save_runtime_settings({"githubRepo": payload.get("githubRepo")})
        settings = runtime_settings()
        update = update_manager.install_update(ROOT, settings, CURRENT_PLUGIN_VERSION)
        update_manager.write_update_status(ROOT, update)
        return {
            "ok": bool(update.get("ok")),
            "message": str(update.get("message") or "已处理更新安装。"),
            "reply": str(update.get("message") or "已处理更新安装。"),
            "pluginVersion": CURRENT_PLUGIN_VERSION,
            "update": update,
            "settings": settings,
        }
    if action == "goal_get":
        return {"ok": True, "message": "已读取目标。", "goal": active_goal()}
    if action == "goal_update":
        goal_payload = payload.get("goal") if isinstance(payload.get("goal"), dict) else payload
        goal = save_goal(goal_payload if isinstance(goal_payload, dict) else {})
        return {"ok": True, "message": "目标已保存。", "reply": f"当前目标：{goal['title']}\n\n{goal['detail']}", "goal": goal}
    if action == "web_busy_update":
        busy = bool(payload.get("busy"))
        state = update_web_busy(busy)
        return {"ok": True, "message": "Web 运行锁已更新。", "web_busy": state}
    if action == "upload_file":
        return register_upload(payload)
    if action == "cache_pdf_from_marginnote":
        return cache_pdf_from_marginnote(payload)
    if action == "request_pdf_cache":
        return request_pdf_cache(payload)
    if action == "request_web_panel_reload":
        return request_web_panel_reload(payload)
    if action == "request_native_capability_probe":
        return request_native_capability_probe(payload)
    if action == "collect_mn_runtime_evidence":
        return collect_mn_runtime_evidence(payload)
    if action == "restart_marginnote4":
        return restart_marginnote4(payload)
    if action == "release_acceptance_summary":
        return release_acceptance_summary(payload)
    if action == "single_document_acceptance_summary":
        return single_document_acceptance_summary(payload)
    if action == "native_highlight_wizard_status":
        return native_highlight_wizard_status(payload)
    if action == "queue_status":
        queue = queue_status_payload(normalize_topic_id(payload), normalize_book_md5(payload))
        run_text = format_run_status_text(queue.get("run") if isinstance(queue.get("run"), dict) else {})
        reply = f"当前队列待处理：{queue['pending']}"
        if run_text:
            reply = f"{reply}\n{run_text}"
        return {
            "ok": True,
            "message": f"当前队列待处理：{queue['pending']}",
            "reply": reply,
            "queue": queue,
            "pdfCache": queue.get("pdfCache"),
        }
    if action == "stop_current":
        run_before = active_run_status()
        topic_id = normalize_topic_id(payload) or str(run_before.get("topicid") or "")
        book_md5 = normalize_book_md5(payload) or str(run_before.get("bookmd5") or "")
        queue_id = str(payload.get("queue_id") or payload.get("_queue_id") or run_before.get("queue_id") or "")
        stop = request_stop(str(payload.get("reason") or "user requested stop"))
        cancelled = cancel_current_generation_process()
        web_busy = update_web_busy(False)
        ack = None
        if queue_id and topic_id:
            ack_payload = {**payload, "topicid": topic_id, "bookmd5": book_md5, "ids": [queue_id]}
            ack = ack_commands(ack_payload)
        run = update_run_state(
            False,
            action=str(payload.get("currentAction") or run_before.get("action") or ""),
            stage="已停止",
            detail="已停止当前生成动作，未继续写入。",
            topicid=topic_id,
            bookmd5=book_md5,
            queue_id=queue_id,
            source=str(payload.get("source") or run_before.get("source") or ""),
        )
        queue = queue_status_payload(topic_id, book_md5)
        return {
            "ok": True,
            "message": "已停止当前生成并清理运行锁。",
            "reply": "已停止当前生成；不会继续写入当前队列项。",
            "stop": stop,
            "cancelledProcess": cancelled,
            "web_busy": web_busy,
            "acked": ack,
            "run": run,
            "queue": queue,
        }
    if action == "history_list":
        return history_payload(payload)
    if action == "history_clear":
        return clear_history(payload)
    if action == "logs_recent":
        try:
            limit = int(payload.get("limit") or 80)
        except Exception:
            limit = 80
        logs = read_recent_diagnostic_logs(limit)
        return {
            "ok": True,
            "message": f"已读取最近 {len(logs)} 条诊断日志。",
            "logs": logs,
            "logPath": str(DIAGNOSTIC_LOG_PATH),
            "events": read_recent_events(20),
            "eventsPath": str(EVENTS_PATH),
        }
    if action == "logs_clear":
        clear_diagnostic_logs()
        return {
            "ok": True,
            "message": "诊断日志已清空。",
            "logs": [],
            "logPath": str(DIAGNOSTIC_LOG_PATH),
            "eventsPath": str(EVENTS_PATH),
        }
    if action == "conversation_new":
        return new_conversation(payload)
    if action == "conversation_list":
        return list_conversations(payload)
    if action == "conversation_load":
        return load_conversation(payload)
    if action == "conversation_delete":
        return delete_conversation(payload)
    if action == "mindmap_target_status":
        return mindmap_target_status(payload)
    if action == "mindmap_target_update":
        return update_mindmap_target(payload)
    if action == "draft_save":
        return save_draft(payload)
    if action == "draft_get":
        return load_draft(str(payload.get("id") or payload.get("draftId") or ""))
    if action == "draft_update":
        return update_draft(payload)
    if action == "draft_delete":
        return delete_draft(str(payload.get("id") or payload.get("draftId") or ""))
    stopped = stopped_response_if_needed(action)
    if stopped:
        return stopped
    permission_error = permission_error_for_action(action)
    if permission_error:
        return {"ok": False, "message": permission_error, "reply": permission_error, "permission": runtime_settings()["permission"]}
    if action == "request_draft_write":
        return request_draft_write(payload)
    if action == "native_highlight_wizard_start":
        return start_native_highlight_wizard(payload)
    queued_for_web_busy = web_busy_queue_response_if_needed(payload, action)
    if queued_for_web_busy:
        return queued_for_web_busy
    if action in GENERATION_ACTIONS:
        return handle_generation_action(action, payload)
    if action == "repair_knows_highlights":
        message = "旧的数据库复制高亮动作已不再支持；请使用 MN4 原生选区高亮或导出带标注 PDF 副本。"
        return {"ok": False, "message": message, "reply": message}
    if action == "diagnose_highlights":
        return diagnose_highlights(payload)
    if action == "diagnose_permissions":
        return diagnose_permissions(payload)
    if action == "open_full_disk_access_settings":
        return open_full_disk_access_settings()
    if action == "export_annotated_pdf":
        return export_annotated_pdf(payload)
    if action == "request_native_highlight_selection":
        return request_native_highlight_selection(payload)
    if action == "health":
        status = status_payload()
        status["message"] = "Companion 连接正常。"
        status["reply"] = (
            "Companion 连接正常。\n\n"
            f"PID: {status.get('pid')}\n"
            f"AI 后端: {status.get('ai_backend_label')}\n"
            f"Codex CLI: {'已发现 ' + str(status.get('codex_cli_path')) if status.get('codex_cli_available') else '未发现'}\n"
            f"OpenAI: {'已配置' if status.get('openai_configured') else '未配置'}\n"
            f"Proxy: {'已配置 ' + str(status.get('proxy_scheme')) if status.get('proxy_configured') else '未配置'}\n"
            f"Model: {status.get('model')}\n"
            f"Sessions: {status.get('session_count')}"
        )
        return status
    if action == "ai_backend_probe":
        return ai_backend_probe()
    return {"ok": False, "message": f"未知动作：{action or '(empty)'}"}


def action_log_result_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(result.get("ok")),
        "message": str(result.get("message") or "")[:500],
        "hasReply": bool(result.get("reply")),
        "backend": str(result.get("backend") or result.get("ai_backend") or ""),
        "requestId": str(result.get("requestId") or ""),
        "queuePending": (
            result.get("queue", {}).get("pending")
            if isinstance(result.get("queue"), dict)
            else None
        ),
    }


def handle_action_logged(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    payload = dict(payload)
    request_id = str(payload.get("_request_id") or payload.get("requestId") or uuid.uuid4().hex[:12])
    payload["_request_id"] = request_id
    action = str(payload.get("action") or "").strip()
    started = time.time()
    append_diagnostic_log(
        "info",
        "action.start",
        f"开始动作：{action or '(empty)'}",
        payload=payload,
        request_id=request_id,
    )
    try:
        result = handle_action(payload)
    except Exception as exc:
        append_diagnostic_log(
            "error",
            "action.exception",
            f"动作异常：{exc}",
            payload=payload,
            extra={"durationMs": int((time.time() - started) * 1000), "error": repr(exc)},
            request_id=request_id,
        )
        raise
    if not isinstance(result, dict):
        result = {"ok": False, "message": "动作没有返回可用结果。"}
    result["requestId"] = request_id
    append_diagnostic_log(
        "info" if result.get("ok") else "warn",
        "action.end",
        str(result.get("message") or ("动作完成。" if result.get("ok") else "动作失败。")),
        payload=payload,
        extra={
            "durationMs": int((time.time() - started) * 1000),
            "result": action_log_result_summary(result),
        },
        request_id=request_id,
    )
    return result


class Handler(BaseHTTPRequestHandler):
    server_version = "CodexMarginNoteCompanion/0.3"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self._send_json(200, {"ok": True})

    def do_GET(self) -> None:
        if self.path.startswith("/health"):
            self._send_json(200, {"ok": True, "message": "Codex MarginNote Companion is running."})
        elif self.path.startswith("/status"):
            self._send_json(200, status_payload())
        elif self.path.startswith("/marginnote/poll"):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            topic_id = (params.get("topicid") or [""])[0]
            book_md5 = (params.get("bookmd5") or [""])[0]
            self._send_json(200, poll_commands(topic_id, book_md5))
        elif self.path.startswith("/marginnote/draft"):
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            draft_id = (params.get("id") or params.get("draftId") or [""])[0]
            result = load_draft(draft_id)
            self._send_json(200 if result.get("ok") else 404, result)
        else:
            self._send_json(404, {"ok": False, "message": "Not found"})

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            self._send_json(400, {"ok": False, "message": f"JSON 解析失败：{exc}"})
            return
        if self.path == "/marginnote/event":
            try:
                result = append_event(payload if isinstance(payload, dict) else {})
            except Exception as exc:
                result = {"ok": False, "message": f"event failed: {exc}"}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if self.path == "/marginnote/enqueue":
            try:
                result = enqueue_command(payload if isinstance(payload, dict) else {})
            except Exception as exc:
                result = {"ok": False, "message": f"enqueue failed: {exc}"}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if self.path == "/marginnote/ack":
            try:
                result = ack_commands(payload if isinstance(payload, dict) else {})
            except Exception as exc:
                result = {"ok": False, "message": f"ack failed: {exc}"}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if self.path == "/marginnote/draft":
            try:
                result = save_draft(payload if isinstance(payload, dict) else {})
            except Exception as exc:
                result = {"ok": False, "message": f"draft failed: {exc}"}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if self.path != "/marginnote/action":
            self._send_json(404, {"ok": False, "message": "Not found"})
            return
        try:
            result = handle_action_logged(payload if isinstance(payload, dict) else {})
        except Exception as exc:
            append_diagnostic_log(
                "error",
                "action.http_exception",
                f"Companion 动作失败：{exc}",
                payload=payload if isinstance(payload, dict) else {},
                extra={"path": self.path, "error": repr(exc)},
            )
            result = {"ok": False, "message": f"Companion 动作失败：{exc}"}
        self._send_json(200 if result.get("ok") else 400, result)

    def log_message(self, fmt: str, *args: Any) -> None:
        print(time.strftime("%Y-%m-%d %H:%M:%S"), fmt % args, flush=True)


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT / "logs").mkdir(parents=True, exist_ok=True)
    (ROOT / "backups").mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    QUEUE_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    load_env_file()
    (ROOT / "companion.pid").write_text(str(os.getpid()), encoding="utf-8")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Codex MarginNote Companion listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
