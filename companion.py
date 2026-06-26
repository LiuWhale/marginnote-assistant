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

import agent_workbench
import diagnostic_log
import knowledge_index
import marginnote_api_adapter
import operation_runtime
import skill_marketplace
import transaction_manager
import workflow_engine
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
    sanitize_mn_api_backend,
    sanitize_mn_url_api_secret,
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
MINDMAP_TREES_DIR = CONTROL_DIR / "mindmap-trees"
OBJECT_GRAPH_RELATIONS_PATH = ROOT / "object-graph-relations.json"
MN_OBJECT_REGISTRY_PATH = ROOT / "mn-object-registry.json"
REVIEW_QUEUE_PATH = ROOT / "review-queue.json"
CODEX_LITE_HOME = CONTROL_DIR / "codex-home"
DRAFTS_DIR = ROOT / "drafts"
WORKFLOW_RUNS_DIR = ROOT / "workflow-runs"
EXTERNAL_GATEWAY_DIR = ROOT / "external-gateway"
CURRENT_PLUGIN_VERSION = "0.4.28"
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
KNOWLEDGE_INDEX_REQUEST_RE = re.compile(
    r"之前|已有|历史|索引|知识库|相关|关联|跨文档|整个\s*notebook|notebook|knowledge|previous|related|existing|index",
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
CARD_FACTORY_SCHEMA = "codex.mn.cardFactory.v1"
CARD_FACTORY_CARD_SCHEMA = "codex.mn.cardFactoryCard.v1"
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
    "mn_object_registry",
    "request_mn_object_registry_scan",
    "object_browser",
    "object_graph",
    "object_graph_relation_save",
    "object_graph_relation_delete",
    "object_activity",
    "operation_ledger_list",
    "operation_ledger_get",
    "ai_edit_transaction_list",
    "ai_edit_transaction_get",
    "ai_edit_transaction_verify",
    "conversation_new",
    "conversation_list",
    "conversation_load",
    "conversation_delete",
    "diagnose_highlights",
    "diagnose_permissions",
    "open_full_disk_access_settings",
    "mn_api_status",
    "mn_url_api_build_request",
    "agent_plan",
    "operation_plan_preview",
    "mindmap_diff_preview",
    "request_mindmap_diff_apply",
    "mn_read_tree",
    "workflow_templates",
    "workflow_preview",
    "workflow_start",
    "workflow_status",
    "workflow_list",
    "workflow_cancel",
    "workflow_retry_step",
    "external_gateway_start_workflow",
    "external_gateway_request_status",
    "external_gateway_callback",
    "skill_marketplace_status",
    "skill_install",
    "skill_uninstall",
    "knowledge_index_status",
    "knowledge_index_search",
    "knowledge_index_ingest_context",
    "knowledge_index_clear",
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
    "request_mindmap_diff_apply",
    "request_mindmap_delete_confirmation",
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
    "read_mindmap_tree",
    "scan_mn_objects",
    "apply_mindmap_diff_operations",
}

diagnostic_log.configure(DIAGNOSTIC_LOG_PATH, max_lines=DIAGNOSTIC_LOG_MAX_LINES)
knowledge_index.configure(ROOT)
skill_marketplace.configure(ROOT)
transaction_manager.configure(ROOT)
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
    settings["mnApiBackend"] = sanitize_mn_api_backend(settings.get("mnApiBackend"))
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
    if "mnApiBackend" in values:
        current["mnApiBackend"] = sanitize_mn_api_backend(values.get("mnApiBackend"))
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
    mn_url_api_secret = sanitize_mn_url_api_secret(values.get("mnUrlApiSecret")) if "mnUrlApiSecret" in values else ""
    if mn_url_api_secret:
        write_env_setting("MN_URL_API_SECRET", mn_url_api_secret)
    if values.get("clearMnUrlApiSecret") is True:
        write_env_setting("MN_URL_API_SECRET", "")
    write_json_file(SETTINGS_PATH, current)
    return current


def draft_summary(draft_id: str, draft: dict[str, Any]) -> dict[str, Any]:
    cards = draft.get("cards") if isinstance(draft.get("cards"), list) else []
    mindmap = draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None
    write_target = draft.get("writeTarget") if isinstance(draft.get("writeTarget"), dict) else {}
    operation_manifest = (
        draft.get("operationManifest")
        if isinstance(draft.get("operationManifest"), dict)
        else draft_operation_manifest(cards, mindmap, write_target)
    )
    if not isinstance(operation_manifest.get("dryRun"), dict):
        operation_manifest = {
            **operation_manifest,
            "dryRun": operation_dry_run(
                operation_manifest,
                str(draft.get("topicid") or ""),
                str(draft.get("bookmd5") or ""),
            ),
        }
    write_target_label = str(write_target.get("label") or "").strip()
    if not write_target_label and mindmap and mindmap.get("mergeIntoSelected"):
        write_target_label = "当前选中节点"
    edit_text = str(draft.get("editText") or "").strip()
    if not edit_text:
        edit_text = draft_edit_text(cards, str(draft.get("reply") or ""))
    mn_object = draft.get("mnObject") if isinstance(draft.get("mnObject"), dict) else {}
    card_factory = draft.get("cardFactory") if isinstance(draft.get("cardFactory"), dict) else {}
    if not card_factory and cards:
        first_source = cards[0].get("source") if isinstance(cards[0], dict) and isinstance(cards[0].get("source"), dict) else {}
        card_factory = card_factory_summary([card for card in cards if isinstance(card, dict)], first_source)
    return {
        "id": draft_id,
        "original_action": str(draft.get("originalAction") or draft.get("action") or ""),
        "message": str(draft.get("message") or ""),
        "reply_preview": str(draft.get("reply") or "")[:280],
        "edit_text": edit_text,
        "card_count": len(cards),
        "card_factory": card_factory,
        "card_quality": operation_manifest.get("cardQuality") if isinstance(operation_manifest.get("cardQuality"), dict) else operation_runtime.audit_card_quality(cards),
        "has_mindmap": bool(mindmap),
        "mindmap_title": str(mindmap.get("title") or "") if mindmap else "",
        "write_target": write_target_label,
        "operation_manifest": operation_manifest,
        "mn_object": mn_object,
        "created_at": str(draft.get("created_at") or ""),
    }


def count_mindmap_nodes(node: Any) -> int:
    return operation_runtime.count_mindmap_nodes(node)


def operation_dry_run(manifest: dict[str, Any], topic_id: str = "", book_md5: str = "") -> dict[str, Any]:
    settings = runtime_settings()
    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    mn_api = mn_api_status_fields(settings).get("mnApi", {})
    return operation_runtime.simulate_operation_manifest(manifest, settings, native_caps, mn_api)


def workflow_operation_plan_dry_run(
    operation_plan: dict[str, Any],
    settings: dict[str, Any],
    native_caps: dict[str, Any],
    mn_api: dict[str, Any],
) -> dict[str, Any]:
    operations = operation_plan.get("operations") if isinstance(operation_plan.get("operations"), list) else []
    local_ready = {"rollbackLedger"}
    write_operations: list[dict[str, Any]] = []
    for operation in operations:
        if not isinstance(operation, dict) or not operation.get("writes"):
            continue
        clean_operation = dict(operation)
        requirements = operation.get("requires") if isinstance(operation.get("requires"), list) else []
        clean_operation["requires"] = [str(item) for item in requirements if str(item) not in local_ready]
        write_operations.append(clean_operation)
    if not write_operations:
        return {
            "schema": "codex.mn.operationDryRun.v1",
            "status": "ready",
            "message": "当前 workflow 没有写入步骤。",
            "operationCount": 0,
            "blockedCount": 0,
            "unknownCount": 0,
            "checks": [],
            "source": "agent_operation_plan",
            "localReadyCapabilities": sorted(local_ready),
        }
    dry_run = operation_runtime.simulate_operation_manifest(
        {"operationPlan": {"operations": write_operations}},
        settings,
        native_caps,
        mn_api,
    )
    return {
        **dry_run,
        "source": "agent_operation_plan",
        "localReadyCapabilities": sorted(local_ready),
    }


def draft_operation_manifest(
    cards: list[Any],
    mindmap: dict[str, Any] | None,
    write_target: dict[str, Any],
    topic_id: str = "",
    book_md5: str = "",
) -> dict[str, Any]:
    manifest = operation_runtime.build_operation_manifest(cards, mindmap, write_target)
    manifest["dryRun"] = operation_dry_run(manifest, topic_id, book_md5)
    return manifest


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
    topic_id = str(payload.get("topicid") or draft_payload.get("topicid") or "")
    book_md5 = str(payload.get("bookmd5") or draft_payload.get("bookmd5") or "")
    mn_object = (
        draft_payload.get("mnObject")
        if isinstance(draft_payload.get("mnObject"), dict)
        else payload.get("mnObject") if isinstance(payload.get("mnObject"), dict) else {}
    )
    draft = {
        "ok": bool(draft_payload.get("ok", True)),
        "message": str(draft_payload.get("message") or "草稿已准备好。"),
        "reply": str(draft_payload.get("reply") or ""),
        "cards": cards,
        "mindmap": mindmap,
        "writeTarget": write_target,
        "mnObject": mn_object,
        "cardFactory": draft_payload.get("cardFactory") if isinstance(draft_payload.get("cardFactory"), dict) else {},
        "operationManifest": draft_operation_manifest(cards, mindmap, write_target, topic_id, book_md5),
        "originalAction": str(payload.get("originalAction") or draft_payload.get("action") or ""),
        "topicid": topic_id,
        "bookmd5": book_md5,
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


def _excluded_mindmap_paths(payload: dict[str, Any]) -> list[str]:
    raw = (
        payload.get("excludedMindmapPaths")
        if isinstance(payload.get("excludedMindmapPaths"), list)
        else payload.get("excludeMindmapPaths")
        if isinstance(payload.get("excludeMindmapPaths"), list)
        else []
    )
    paths: list[str] = []
    seen: set[str] = set()
    for item in raw:
        path = str(item or "").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)*", path):
            continue
        if path in seen:
            continue
        seen.add(path)
        paths.append(path)
    return paths


def _mindmap_node_edits(payload: dict[str, Any]) -> list[dict[str, str]]:
    raw = payload.get("mindmapNodeEdits") if isinstance(payload.get("mindmapNodeEdits"), list) else []
    edits: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        path = str(item.get("proposedPath") or item.get("path") or "").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)*", path):
            continue
        edit: dict[str, str] = {"proposedPath": path}
        title = str(item.get("title") or "").strip()
        if title:
            edit["title"] = title[:180]
        if "body" in item or "shortBody" in item:
            body = str(item.get("body") if "body" in item else item.get("shortBody") or "").strip()
            edit["body"] = body[:2000]
        if len(edit) <= 1:
            continue
        key = path + "\n" + edit.get("title", "") + "\n" + edit.get("body", "")
        if key in seen:
            continue
        seen.add(key)
        edits.append(edit)
    return edits


def update_draft(payload: dict[str, Any]) -> dict[str, Any]:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(payload.get("id") or payload.get("draftId") or ""))[:80]
    if not clean_id:
        return {"ok": False, "message": "缺少草稿 ID。"}
    path = DRAFTS_DIR / f"{clean_id}.json"
    draft = read_json_file(path, {})
    if not isinstance(draft, dict) or not draft:
        return {"ok": False, "message": "草稿不存在或已过期。", "id": clean_id}
    edit_text = str(payload.get("editText") or "").strip()
    excluded_paths = _excluded_mindmap_paths(payload)
    node_edits = _mindmap_node_edits(payload)
    if not edit_text and not excluded_paths and not node_edits:
        return {"ok": False, "message": "草稿编辑内容为空。", "id": clean_id}
    cards = cards_from_draft_edit_text(edit_text) if edit_text else []
    if node_edits or excluded_paths:
        mindmap = draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None
        if not mindmap:
            return {"ok": False, "message": "当前草稿没有可编辑节点的脑图。", "id": clean_id}
        if node_edits:
            mindmap = operation_runtime.edit_mindmap_nodes_by_paths(mindmap, node_edits)
            draft["mindmap"] = mindmap
            draft["mindmapNodeEdits"] = node_edits
    if excluded_paths:
        mindmap = draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None
        if not mindmap:
            return {"ok": False, "message": "当前草稿没有可排除节点的脑图。", "id": clean_id}
        pruned_mindmap = operation_runtime.prune_mindmap_by_paths(mindmap, excluded_paths)
        if not pruned_mindmap:
            return {"ok": False, "message": "不能排除脑图根节点或排除后脑图为空。", "id": clean_id}
        draft["mindmap"] = pruned_mindmap
        draft["excludedMindmapPaths"] = excluded_paths
    if not cards and not isinstance(draft.get("mindmap"), dict):
        return {"ok": False, "message": "编辑内容没有可写入卡片。", "id": clean_id}
    if cards:
        draft["cards"] = cards
    if edit_text:
        draft["editText"] = edit_text
        draft["reply"] = edit_text
    draft["operationManifest"] = draft_operation_manifest(
        draft.get("cards") if isinstance(draft.get("cards"), list) else [],
        draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None,
        draft.get("writeTarget") if isinstance(draft.get("writeTarget"), dict) else {},
        str(payload.get("topicid") or draft.get("topicid") or ""),
        str(payload.get("bookmd5") or draft.get("bookmd5") or ""),
    )
    draft["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json_file(path, draft)
    return {
        "ok": True,
        "message": "草稿编辑已保存。",
        "draft": draft_summary(clean_id, draft),
    }


def operation_plan_preview(payload: dict[str, Any]) -> dict[str, Any]:
    draft_id = str(payload.get("id") or payload.get("draftId") or "").strip()
    draft = load_draft(draft_id)
    if not draft.get("ok"):
        return draft
    manifest = draft.get("operationManifest") if isinstance(draft.get("operationManifest"), dict) else {}
    if not manifest:
        manifest = draft_operation_manifest(
            draft.get("cards") if isinstance(draft.get("cards"), list) else [],
            draft.get("mindmap") if isinstance(draft.get("mindmap"), dict) else None,
            draft.get("writeTarget") if isinstance(draft.get("writeTarget"), dict) else {},
        )
    topic_id = str(payload.get("topicid") or draft.get("topicid") or "")
    book_md5 = str(payload.get("bookmd5") or draft.get("bookmd5") or "")
    dry_run = operation_dry_run(manifest, topic_id, book_md5)
    manifest = {**manifest, "dryRun": dry_run}
    return {
        "ok": True,
        "message": dry_run.get("message") or "已生成操作计划预览。",
        "reply": (
            f"Operation dry-run：{dry_run.get('status')}\n"
            f"操作数：{dry_run.get('operationCount', 0)}\n"
            f"阻断：{dry_run.get('blockedCount', 0)} / 未确认：{dry_run.get('unknownCount', 0)}"
        ),
        "draftId": draft_id,
        "operationManifest": manifest,
        "operationPlan": manifest.get("operationPlan") if isinstance(manifest.get("operationPlan"), dict) else {},
        "dryRun": dry_run,
        **mn_api_status_fields(runtime_settings()),
    }


def _payload_mindmap(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def mindmap_diff_preview(payload: dict[str, Any]) -> dict[str, Any]:
    draft_id = str(payload.get("id") or payload.get("draftId") or "").strip()
    draft: dict[str, Any] = {}
    if draft_id:
        loaded = load_draft(draft_id)
        if loaded.get("ok"):
            draft = loaded
        else:
            return loaded
    proposed = _payload_mindmap(
        payload.get("proposedMindmap")
        or payload.get("mindmap")
        or draft.get("mindmap")
    )
    current = _payload_mindmap(
        payload.get("currentMindmap")
        or payload.get("currentTree")
        or payload.get("existingMindmap")
        or payload.get("existingTree")
    )
    tree_cache: dict[str, Any] = {}
    if not current:
        tree_cache = read_latest_mindmap_tree(normalize_topic_id(payload) or str(draft.get("topicid") or ""), normalize_book_md5(payload) or str(draft.get("bookmd5") or ""))
        current = _payload_mindmap(tree_cache.get("currentMindmap"))
    target = (
        payload.get("mindmapTarget")
        if isinstance(payload.get("mindmapTarget"), dict)
        else draft.get("writeTarget") if isinstance(draft.get("writeTarget"), dict) else {}
    )
    if not proposed:
        return {
            "ok": False,
            "message": "缺少拟写入脑图，无法生成 diff。",
            "draftId": draft_id,
        }
    diff = operation_runtime.build_mindmap_diff(proposed, current, target=target)
    diff_operation_plan = operation_runtime.build_mindmap_diff_operation_plan(
        diff,
        excluded_paths=payload.get("excludedMindmapPaths") if isinstance(payload.get("excludedMindmapPaths"), list) else [],
    )
    summary = diff.get("summary") if isinstance(diff.get("summary"), dict) else {}
    reply = (
        "脑图 Diff 预览\n"
        f"新增 {summary.get('createCount', 0)} / 更新 {summary.get('updateCount', 0)} / "
        f"合并 {summary.get('mergeCount', 0)} / 重复 {summary.get('duplicateCount', 0)}\n"
        f"拟写入节点 {summary.get('proposedCount', 0)}，当前树节点 {summary.get('currentCount', 0)}。"
    )
    return {
        "ok": True,
        "message": "已生成脑图 Diff 预览。",
        "reply": reply,
        "draftId": draft_id,
        "mindmapDiff": diff,
        "mindmapDiffOperationPlan": diff_operation_plan,
        "mindmapTreeCache": {
            "schema": str(tree_cache.get("schema") or ""),
            "sourceEvent": str(tree_cache.get("sourceEvent") or ""),
            "nodeCount": int(tree_cache.get("nodeCount") or 0),
            "updatedAt": str(tree_cache.get("updatedAt") or ""),
        } if tree_cache else {},
    }


def workflow_preview(payload: dict[str, Any]) -> dict[str, Any]:
    settings = runtime_settings()
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    mn_api = mn_api_status_fields(settings).get("mnApi", {})
    preview = workflow_engine.build_workflow_preview(payload, native_caps=native_caps, mn_api=mn_api)
    step_lines = "\n".join(
        f"{index}. {step.get('title') or step.get('action')}"
        for index, step in enumerate(preview.get("steps") or [], start=1)
        if isinstance(step, dict)
    )
    return {
        "ok": True,
        "message": f"已生成工作流预览：{preview['title']}",
        "reply": (
            f"工作流：{preview['title']}\n"
            f"状态：{preview['status']}\n"
            f"步骤数：{preview['stepCount']}\n\n"
            f"{step_lines}"
        ).strip(),
        "workflow": preview,
        **mn_api_status_fields(settings),
    }


def agent_plan(payload: dict[str, Any]) -> dict[str, Any]:
    settings = runtime_settings()
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    mn_api = mn_api_status_fields(settings).get("mnApi", {})
    workflow = workflow_engine.build_workflow_preview(payload, native_caps=native_caps, mn_api=mn_api)
    knowledge = knowledge_index.status(topic_id, book_md5)
    dry_run: dict[str, Any] = {}
    draft_id = str(payload.get("draftId") or payload.get("id") or "").strip()
    if draft_id:
        preview = operation_plan_preview(payload)
        dry_run = preview.get("dryRun") if isinstance(preview.get("dryRun"), dict) else {}
    operation = agent_workbench.build_agent_operation(
        payload,
        workflow=workflow,
        knowledge=knowledge,
        dry_run=dry_run,
        settings=settings,
    )
    if not dry_run and isinstance(operation.get("operationPlan"), dict):
        operation_plan = operation.get("operationPlan") if isinstance(operation.get("operationPlan"), dict) else {}
        if int(operation_plan.get("writeCount") or 0) > 0:
            dry_run = workflow_operation_plan_dry_run(operation_plan, settings, native_caps, mn_api)
            operation = agent_workbench.build_agent_operation(
                payload,
                workflow=workflow,
                knowledge=knowledge,
                dry_run=dry_run,
                settings=settings,
            )
    focus = operation.get("object") if isinstance(operation.get("object"), dict) else {}
    policy = operation.get("operationPolicy") if isinstance(operation.get("operationPolicy"), dict) else {}
    risk = policy.get("risk") if isinstance(policy.get("risk"), dict) else {}
    operation_plan = operation.get("operationPlan") if isinstance(operation.get("operationPlan"), dict) else {}
    verification_plan = operation.get("verificationPlan") if isinstance(operation.get("verificationPlan"), dict) else {}
    return {
        "ok": True,
        "message": "已生成 Agent 操作计划。",
        "reply": (
            "Agent 操作计划\n"
            f"对象：{focus.get('kind')} / {focus.get('title')}\n"
            f"工作流：{workflow.get('title')} / {workflow.get('status')}\n"
            f"计划步骤：{operation_plan.get('operationCount', 0)} / 写入步骤：{operation_plan.get('writeCount', 0)}\n"
            f"写入风险：{risk.get('status')}\n"
            "后续写入必须经过 dry-run 和接受/拒绝确认。"
        ),
        "agentOperation": operation,
        "operationPlan": operation_plan,
        "verificationPlan": verification_plan,
        "operationCompiler": operation.get("operationCompiler") if isinstance(operation.get("operationCompiler"), dict) else {},
        "workflow": workflow,
        "knowledge": knowledge,
        "dryRun": dry_run,
        **mn_api_status_fields(settings),
    }


WORKFLOW_QUEUEABLE_RAW_ACTIONS = {
    "chat",
    "generate_full_reading",
    "generate_mindmap",
    "generate_card",
    "expand_node",
    "reorganize_mindmap",
}
WORKFLOW_DIRECT_ACTIONS = {"request_pdf_cache", "mn_read_tree"}
WORKFLOW_CONFIRMATION_ACTIONS = {"write_draft", "operation_plan_preview", "ai_edit_transaction_get"}


def workflow_run_path(run_id: str) -> Path:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(run_id or ""))[:80]
    return WORKFLOW_RUNS_DIR / f"{clean_id}.json"


def workflow_run_summary(run: dict[str, Any]) -> dict[str, Any]:
    steps = run.get("steps") if isinstance(run.get("steps"), list) else []
    queued = [step for step in steps if isinstance(step, dict) and step.get("status") == "queued"]
    waiting = [step for step in steps if isinstance(step, dict) and step.get("status") == "waiting_confirmation"]
    skipped = [step for step in steps if isinstance(step, dict) and step.get("status") == "manual"]
    object_ref = run.get("objectRef") if isinstance(run.get("objectRef"), dict) else {}
    external_request = run.get("externalRequest") if isinstance(run.get("externalRequest"), dict) else {}
    return {
        "id": str(run.get("id") or ""),
        "workflowId": str(run.get("workflowId") or ""),
        "title": str(run.get("title") or ""),
        "status": str(run.get("status") or "unknown"),
        "topicid": str(run.get("topicid") or ""),
        "bookmd5": str(run.get("bookmd5") or ""),
        "requestId": str(external_request.get("requestId") or ""),
        "externalCaller": str(external_request.get("caller") or ""),
        "mnObjectId": str(object_ref.get("objectId") or ""),
        "mnObjectKind": str(object_ref.get("kind") or ""),
        "mnObjectTitle": str(object_ref.get("title") or ""),
        "queuedCount": len(queued),
        "waitingConfirmationCount": len(waiting),
        "manualCount": len(skipped),
        "createdAt": str(run.get("createdAt") or ""),
        "updatedAt": str(run.get("updatedAt") or ""),
    }


def workflow_run_status_tone(status: Any) -> str:
    clean_status = str(status or "unknown").strip().lower()
    if clean_status in {"failed", "blocked", "cancelled"}:
        return "block"
    if clean_status in {"waiting_confirmation", "manual", "pending", "partial"}:
        return "warn"
    if clean_status in {"queued", "complete", "completed", "done", "saved"}:
        return "pass"
    return "idle"


def workflow_step_retryable(step: dict[str, Any]) -> bool:
    status = str(step.get("status") or "").strip().lower()
    action = str(step.get("action") or "")
    if status not in {"failed", "blocked"}:
        return False
    return action in WORKFLOW_DIRECT_ACTIONS or action in WORKFLOW_QUEUEABLE_RAW_ACTIONS


def workflow_step_next_action(step: dict[str, Any]) -> str:
    action = str(step.get("action") or "")
    status = str(step.get("status") or "").strip().lower()
    if workflow_step_retryable(step):
        return "retry_step"
    if status == "queued":
        return "watch_queue"
    if status == "waiting_confirmation":
        return "confirm_or_reject"
    if status in {"failed", "blocked"}:
        return "inspect_error"
    if status == "manual" and action == "operation_plan_preview":
        return "review_dry_run"
    if status == "manual" and action == "ai_edit_transaction_get":
        return "verify_transaction"
    if status == "manual":
        return "manual_execute"
    if status == "cancelled":
        return "stopped"
    if status == "pending":
        return "wait"
    return "inspect"


def workflow_run_inspector(run: dict[str, Any]) -> dict[str, Any]:
    summary = workflow_run_summary(run)
    raw_steps = run.get("steps") if isinstance(run.get("steps"), list) else []
    steps: list[dict[str, Any]] = []
    status_counts: dict[str, int] = {}
    confirmations: list[dict[str, Any]] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        status = str(step.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        step_id = str(step.get("id") or step.get("stepId") or step.get("action") or "")
        retryable = workflow_step_retryable(step)
        inspected = {
            "stepId": step_id,
            "index": int(step.get("index") or (len(steps) + 1)),
            "title": str(step.get("title") or step.get("action") or "工作流步骤"),
            "action": str(step.get("action") or ""),
            "status": status,
            "statusTone": workflow_run_status_tone(status),
            "writes": bool(step.get("writes")),
            "requiresConfirmation": bool(step.get("writes")) or status == "waiting_confirmation",
            "queueId": str(step.get("queueId") or ""),
            "message": str(step.get("message") or ""),
            "nextAction": workflow_step_next_action(step),
            "retryable": retryable,
            "retryAction": {
                "action": "workflow_retry_step",
                "workflowRunId": str(summary.get("id") or ""),
                "workflowStepId": step_id,
            } if retryable else {},
        }
        steps.append(inspected)
        if status == "waiting_confirmation":
            confirmations.append(
                {
                    "stepId": step_id,
                    "title": inspected["title"],
                    "action": inspected["action"],
                    "message": inspected["message"],
                    "nextAction": inspected["nextAction"],
                    "statusTone": inspected["statusTone"],
                }
            )
    step_counts = {
        "total": len(steps),
        "queued": status_counts.get("queued", 0),
        "waitingConfirmation": status_counts.get("waiting_confirmation", 0),
        "manual": status_counts.get("manual", 0),
        "blocked": status_counts.get("blocked", 0),
        "failed": status_counts.get("failed", 0),
        "pending": status_counts.get("pending", 0),
        "completed": status_counts.get("completed", 0) + status_counts.get("complete", 0) + status_counts.get("done", 0),
    }
    return {
        "schema": "codex.mn.workflowRunInspector.v1",
        "workflowRunId": str(summary.get("id") or ""),
        "workflowId": str(summary.get("workflowId") or ""),
        "title": str(summary.get("title") or ""),
        "status": str(summary.get("status") or "unknown"),
        "statusTone": workflow_run_status_tone(summary.get("status")),
        "objectRef": {
            "objectId": str(summary.get("mnObjectId") or ""),
            "kind": str(summary.get("mnObjectKind") or ""),
            "title": str(summary.get("mnObjectTitle") or ""),
        },
        "stepCounts": step_counts,
        "confirmations": confirmations,
        "steps": steps,
        "summaryText": (
            f"{step_counts['total']} steps / queued {step_counts['queued']} / "
            f"confirm {step_counts['waitingConfirmation']} / manual {step_counts['manual']}"
        ),
    }


def workflow_recalculate_status(steps: list[dict[str, Any]]) -> str:
    statuses = {str(step.get("status") or "") for step in steps if isinstance(step, dict)}
    if statuses.intersection({"failed", "blocked"}):
        return "partial"
    if "waiting_confirmation" in statuses:
        return "waiting_confirmation"
    if "queued" in statuses:
        return "queued"
    if statuses.intersection({"pending", "manual"}):
        return "pending"
    return "complete"


def load_workflow_run(run_id: str) -> dict[str, Any]:
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", str(run_id or ""))[:80]
    if not clean_id:
        return {"ok": False, "message": "缺少 workflow run id。"}
    run = read_json_file(workflow_run_path(clean_id), {})
    if not isinstance(run, dict) or not run:
        return {"ok": False, "message": "工作流不存在。", "id": clean_id}
    return {
        "ok": True,
        "message": "已读取工作流。",
        "workflowRun": run,
        "summary": workflow_run_summary(run),
        "runInspector": workflow_run_inspector(run),
    }


def workflow_retry_step(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("workflowRunId") or payload.get("id") or "")
    step_id = str(payload.get("workflowStepId") or payload.get("stepId") or "").strip()
    loaded = load_workflow_run(run_id)
    if not loaded.get("ok"):
        return loaded
    if not step_id:
        return {"ok": False, "message": "缺少 workflow step id。"}
    run = loaded["workflowRun"]
    steps = run.get("steps") if isinstance(run.get("steps"), list) else []
    target: dict[str, Any] | None = None
    for step in steps:
        if not isinstance(step, dict):
            continue
        candidate_id = str(step.get("id") or step.get("stepId") or step.get("action") or "")
        candidate_index = str(step.get("index") or "")
        if step_id in {candidate_id, candidate_index}:
            target = step
            break
    if target is None:
        return {"ok": False, "message": "未找到 workflow step。", "workflowRun": run, "summary": workflow_run_summary(run)}
    action = str(target.get("action") or "")
    if action in WORKFLOW_CONFIRMATION_ACTIONS or target.get("writes"):
        return {
            "ok": False,
            "message": "确认或写入步骤不能通过重试自动执行；请在 AI 编辑确认里接受或拒绝。",
            "workflowRun": run,
            "summary": workflow_run_summary(run),
            "runInspector": workflow_run_inspector(run),
        }
    if not workflow_step_retryable(target):
        return {
            "ok": False,
            "message": "该 workflow step 当前不可重试。",
            "workflowRun": run,
            "summary": workflow_run_summary(run),
            "runInspector": workflow_run_inspector(run),
        }

    topic_id = str(run.get("topicid") or normalize_topic_id(payload))
    book_md5 = str(run.get("bookmd5") or normalize_book_md5(payload))
    object_ref = run.get("objectRef") if isinstance(run.get("objectRef"), dict) else {}
    workflow = run.get("preview") if isinstance(run.get("preview"), dict) else {
        "id": str(run.get("workflowId") or ""),
        "title": str(run.get("title") or ""),
    }
    retry_payload = {
        **payload,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "prompt": str(run.get("prompt") or payload.get("prompt") or ""),
        "source": "workflow_retry_step",
        "workflowRunId": str(run.get("id") or run_id),
        "mnObject": run.get("mnObject") if isinstance(run.get("mnObject"), dict) else {},
        "mnObjectId": str(object_ref.get("objectId") or ""),
        "mnObjectKind": str(object_ref.get("kind") or ""),
    }

    queued_records: list[dict[str, Any]] = []
    direct_results: list[dict[str, Any]] = []
    if action in WORKFLOW_DIRECT_ACTIONS:
        if action == "request_pdf_cache":
            result = request_pdf_cache(retry_payload)
        else:
            result = request_mindmap_tree(retry_payload)
        target["status"] = "queued" if result.get("ok") else "failed"
        target["message"] = str(result.get("message") or "")
        if isinstance(result.get("queued"), dict):
            target["queueId"] = str(result["queued"].get("id") or "")
            queued_records.append(result["queued"])
        direct_results.append({"stepId": step_id, "action": action, "ok": bool(result.get("ok")), "message": result.get("message")})
    elif action in WORKFLOW_QUEUEABLE_RAW_ACTIONS:
        permission_error = permission_error_for_action(action)
        if permission_error:
            target["status"] = "blocked"
            target["message"] = permission_error
            return {
                "ok": False,
                "message": permission_error,
                "workflowRun": run,
                "summary": workflow_run_summary(run),
                "runInspector": workflow_run_inspector(run),
            }
        command = {
            "rawAction": action,
            "prompt": workflow_step_prompt(retry_payload, workflow, target),
            "source": "workflow_retry_step",
            "_queue_raw": True,
            "workflowRunId": str(run.get("id") or run_id),
            "workflowStepId": str(target.get("id") or step_id),
            "mnObjectId": str(object_ref.get("objectId") or ""),
            "mnObjectKind": str(object_ref.get("kind") or ""),
            "message": f"workflow retry {workflow.get('id') or run.get('workflowId')} step {target.get('id') or action}",
        }
        queued = enqueue_command({**retry_payload, "command": command, "_queue_raw": True, "message": command["message"]})
        target["status"] = "queued" if queued.get("ok") else "failed"
        target["message"] = str(queued.get("message") or "")
        if isinstance(queued.get("queued"), dict):
            target["queueId"] = str(queued["queued"].get("id") or "")
            queued_records.append(queued["queued"])
    else:
        return {"ok": False, "message": "该 workflow step 不是可自动执行步骤。", "workflowRun": run}

    target["retriedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    target["retryCount"] = int(target.get("retryCount") or 0) + 1
    target["lastRetrySource"] = "workflow_retry_step"
    run["status"] = workflow_recalculate_status([step for step in steps if isinstance(step, dict)])
    run["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json_file(workflow_run_path(str(run.get("id") or run_id)), run)
    inspector = workflow_run_inspector(run)
    retried_step = next((step for step in inspector.get("steps", []) if isinstance(step, dict) and step.get("stepId") == str(target.get("id") or step_id)), {})
    return {
        "ok": target.get("status") == "queued",
        "message": "已重试 workflow step。" if target.get("status") == "queued" else str(target.get("message") or "workflow step 重试失败。"),
        "workflowRun": run,
        "summary": workflow_run_summary(run),
        "runInspector": inspector,
        "retriedStep": retried_step,
        "queued": queued_records,
        "directResults": direct_results,
        "queue": queue_status_payload(topic_id, book_md5),
    }


def clean_external_gateway_id(value: Any) -> str:
    text = str(value or "").strip()
    clean = re.sub(r"[^A-Za-z0-9._-]", "", text)[:120]
    return clean or marginnote_api_adapter.generate_request_id("ext")


def external_gateway_request_path(request_id: str) -> Path:
    return EXTERNAL_GATEWAY_DIR / f"{clean_external_gateway_id(request_id)}.json"


def external_gateway_callback(payload: dict[str, Any]) -> dict[str, str]:
    success = str(payload.get("x-success") or payload.get("xSuccess") or payload.get("successCallback") or "").strip()
    error_url = str(payload.get("x-error") or payload.get("xError") or payload.get("errorCallback") or "").strip()
    base = str(payload.get("callbackBaseUrl") or "").strip()
    if base and (not success or not error_url):
        try:
            normalized = marginnote_api_adapter.normalize_callback_base_url(base)
        except ValueError:
            normalized = ""
        if normalized:
            success = success or f"{normalized}/success"
            error_url = error_url or f"{normalized}/error"
    return {"success": success, "error": error_url, "status": "pending" if (success or error_url) else "not_configured"}


def external_gateway_base_record(payload: dict[str, Any], request_id: str) -> dict[str, Any]:
    settings = runtime_settings()
    mn_object = payload.get("mnObject") if isinstance(payload.get("mnObject"), dict) else agent_workbench.build_mn_object(payload)
    object_ref = {
        "objectId": str(mn_object.get("objectId") or ""),
        "kind": str(mn_object.get("kind") or ""),
        "title": str(mn_object.get("title") or ""),
        "sourceRef": mn_object.get("sourceRef") if isinstance(mn_object.get("sourceRef"), dict) else {},
    }
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    return {
        "schema": "codex.mn.externalGatewayRequest.v1",
        "requestId": request_id,
        "caller": str(payload.get("caller") or payload.get("source") or "external")[:120],
        "permission": str(settings.get("permission") or "notes"),
        "requestedAction": "workflow_start",
        "workflowId": str(payload.get("workflowId") or ""),
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "objectRef": object_ref,
        "contextPolicy": {
            "contextScope": str(payload.get("contextScope") or settings.get("defaultContextScope") or "auto"),
            "source": "external_gateway",
        },
        "callback": external_gateway_callback(payload),
        "stage": "received",
        "result": {},
        "createdAt": now,
        "updatedAt": now,
    }


def write_external_gateway_record(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record)
    record["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json_file(external_gateway_request_path(str(record.get("requestId") or "")), record)
    return record


def external_gateway_request_status(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = clean_external_gateway_id(payload.get("requestId") or payload.get("id") or "")
    record = read_json_file(external_gateway_request_path(request_id), {})
    if not isinstance(record, dict) or not record:
        return {"ok": False, "message": "未找到外部自动化请求。", "requestId": request_id}
    return {"ok": True, "message": "已读取外部自动化请求。", "externalGateway": record}


def external_gateway_callback_update(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = clean_external_gateway_id(payload.get("requestId") or payload.get("id") or "")
    path = external_gateway_request_path(request_id)
    record = read_json_file(path, {})
    if not isinstance(record, dict) or not record:
        return {"ok": False, "message": "未找到外部自动化请求，无法记录回调。", "requestId": request_id}

    raw_status = str(payload.get("callbackStatus") or payload.get("status") or "").strip().lower()
    if raw_status in {"ok", "done", "complete", "completed"}:
        callback_status = "success"
    elif raw_status in {"fail", "failed", "failure"}:
        callback_status = "error"
    elif raw_status in {"success", "error"}:
        callback_status = raw_status
    else:
        callback_status = "unknown"

    callback_payload = payload.get("payload")
    if callback_payload is None:
        callback_payload = payload.get("result") if "result" in payload else {}
    if not isinstance(callback_payload, dict):
        callback_payload = {"value": callback_payload}

    callback = record.get("callback") if isinstance(record.get("callback"), dict) else {}
    history = callback.get("history") if isinstance(callback.get("history"), list) else []
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    event = {
        "status": callback_status,
        "message": str(payload.get("message") or ""),
        "payload": callback_payload,
        "receivedAt": now,
    }
    callback = {
        **callback,
        "status": callback_status,
        "message": event["message"],
        "payload": callback_payload,
        "receivedAt": now,
        "receivedCount": len(history) + 1,
        "history": [*history, event],
    }
    record = {
        **record,
        "stage": f"callback_{callback_status}" if callback_status in {"success", "error"} else "callback_received",
        "callback": callback,
        "result": {
            **(record.get("result") if isinstance(record.get("result"), dict) else {}),
            "callbackStatus": callback_status,
            "callbackMessage": event["message"],
        },
    }
    record = write_external_gateway_record(record)
    return {"ok": True, "message": "已记录外部自动化回调。", "externalGateway": record}


def external_gateway_start_workflow(payload: dict[str, Any]) -> dict[str, Any]:
    request_id = clean_external_gateway_id(payload.get("requestId") or payload.get("_request_id") or "")
    record = write_external_gateway_record(external_gateway_base_record(payload, request_id))
    run_payload = {
        **payload,
        "source": "external_gateway",
        "requestId": request_id,
        "externalRequest": {
            "requestId": record["requestId"],
            "caller": record["caller"],
            "permission": record["permission"],
            "callback": record["callback"],
        },
    }
    result = workflow_start(run_payload)
    workflow_run = result.get("workflowRun") if isinstance(result.get("workflowRun"), dict) else {}
    summary = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    record = {
        **record,
        "stage": "workflow_started" if result.get("ok") else "failed",
        "workflowRunId": str(summary.get("id") or workflow_run.get("id") or ""),
        "result": {
            "ok": bool(result.get("ok")),
            "message": str(result.get("message") or ""),
            "workflowStatus": str(summary.get("status") or workflow_run.get("status") or ""),
            "queuedCount": int(summary.get("queuedCount") or 0),
            "waitingConfirmationCount": int(summary.get("waitingConfirmationCount") or 0),
        },
    }
    record = write_external_gateway_record(record)
    result["externalGateway"] = record
    result["gatewayLedger"] = {"path": str(external_gateway_request_path(request_id)), "requestId": request_id}
    return result


def workflow_step_prompt(payload: dict[str, Any], workflow: dict[str, Any], step: dict[str, Any]) -> str:
    base_prompt = str(payload.get("prompt") or payload.get("title") or workflow.get("title") or "").strip()
    title = str(step.get("title") or step.get("action") or "工作流步骤")
    parts = [
        f"工作流：{workflow.get('title') or workflow.get('id')}",
        f"当前步骤：{title}",
        base_prompt,
        "请只完成当前步骤，输出要结构化、可追溯，并适合后续转换为 MarginNote 卡片或脑图草稿。",
    ]
    return "\n\n".join(part for part in parts if part).strip()[:4200]


def workflow_start(payload: dict[str, Any]) -> dict[str, Any]:
    preview_result = workflow_preview(payload)
    workflow = preview_result.get("workflow") if isinstance(preview_result.get("workflow"), dict) else {}
    if not workflow:
        return {"ok": False, "message": "无法启动工作流：缺少 workflow preview。"}
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "无法启动工作流：缺少 topicid。"}
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    run_id = hashlib.sha256(f"{now}|{uuid.uuid4()}|{workflow.get('id')}".encode("utf-8")).hexdigest()[:20]
    provided_mn_object = payload.get("mnObject") if isinstance(payload.get("mnObject"), dict) else {}
    mn_object = provided_mn_object if provided_mn_object.get("objectId") else agent_workbench.build_mn_object(payload)
    object_ref = {
        "objectId": str(mn_object.get("objectId") or ""),
        "kind": str(mn_object.get("kind") or ""),
        "title": str(mn_object.get("title") or ""),
        "sourceRef": mn_object.get("sourceRef") if isinstance(mn_object.get("sourceRef"), dict) else {},
    }
    run_steps: list[dict[str, Any]] = []
    queued_records: list[dict[str, Any]] = []
    direct_results: list[dict[str, Any]] = []
    waiting_steps: list[dict[str, Any]] = []
    for index, step in enumerate(workflow.get("steps") if isinstance(workflow.get("steps"), list) else [], start=1):
        if not isinstance(step, dict):
            continue
        action = str(step.get("action") or "")
        step_record = {
            **step,
            "index": index,
            "status": "pending",
            "queueId": "",
            "message": "",
        }
        if action in WORKFLOW_DIRECT_ACTIONS:
            if action == "request_pdf_cache":
                result = request_pdf_cache({**payload, "source": "workflow_start", "workflowRunId": run_id, "mnObjectId": object_ref["objectId"]})
            else:
                result = request_mindmap_tree({**payload, "source": "workflow_start", "workflowRunId": run_id, "mnObjectId": object_ref["objectId"]})
            step_record["status"] = "queued" if result.get("ok") else "failed"
            step_record["message"] = str(result.get("message") or "")
            if isinstance(result.get("queued"), dict):
                step_record["queueId"] = str(result["queued"].get("id") or "")
                queued_records.append(result["queued"])
            direct_results.append({"stepId": step.get("id"), "action": action, "ok": bool(result.get("ok")), "message": result.get("message")})
        elif action in WORKFLOW_QUEUEABLE_RAW_ACTIONS:
            permission_error = permission_error_for_action(action)
            if permission_error:
                step_record["status"] = "blocked"
                step_record["message"] = permission_error
                run_steps.append(step_record)
                continue
            command = {
                "rawAction": action,
                "prompt": workflow_step_prompt(payload, workflow, step),
                "source": "workflow_start",
                "_queue_raw": True,
                "workflowRunId": run_id,
                "workflowStepId": str(step.get("id") or ""),
                "mnObjectId": object_ref["objectId"],
                "mnObjectKind": object_ref["kind"],
                "message": f"workflow {workflow.get('id')} step {step.get('id') or action}",
            }
            queued = enqueue_command({**payload, "command": command, "_queue_raw": True, "message": command["message"]})
            step_record["status"] = "queued" if queued.get("ok") else "failed"
            step_record["message"] = str(queued.get("message") or "")
            if isinstance(queued.get("queued"), dict):
                step_record["queueId"] = str(queued["queued"].get("id") or "")
                queued_records.append(queued["queued"])
        elif action in WORKFLOW_CONFIRMATION_ACTIONS or step.get("writes"):
            step_record["status"] = "waiting_confirmation" if step.get("writes") else "manual"
            step_record["message"] = "该步骤需要上一步草稿或用户确认，未自动入队。"
            waiting_steps.append(step_record)
        else:
            step_record["status"] = "manual"
            step_record["message"] = "当前版本暂不自动执行该步骤。"
        run_steps.append(step_record)
    run_status = "waiting_confirmation" if waiting_steps else "queued"
    if any(step.get("status") in {"failed", "blocked"} for step in run_steps):
        run_status = "partial"
    run = {
        "id": run_id,
        "schema": "codex.mn.workflowRun.v1",
        "workflowId": str(workflow.get("id") or ""),
        "title": str(workflow.get("title") or ""),
        "status": run_status,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "mnObject": mn_object,
        "objectRef": object_ref,
        "createdAt": now,
        "updatedAt": now,
        "prompt": str(payload.get("prompt") or ""),
        "preview": workflow,
        "steps": run_steps,
    }
    if isinstance(payload.get("externalRequest"), dict):
        run["externalRequest"] = payload["externalRequest"]
    WORKFLOW_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    write_json_file(workflow_run_path(run_id), run)
    summary = workflow_run_summary(run)
    return {
        "ok": True,
        "message": f"已启动工作流：{workflow.get('title')}",
        "reply": (
            f"已启动工作流：{workflow.get('title')}\n"
            f"已入队步骤：{summary['queuedCount']}\n"
            f"等待确认步骤：{summary['waitingConfirmationCount']}\n"
            "写入类步骤不会自动执行；生成草稿后仍需要接受/拒绝。"
        ),
        "workflowRun": run,
        "summary": summary,
        "queued": queued_records,
        "directResults": direct_results,
        "queue": queue_status_payload(topic_id, book_md5),
    }


def workflow_list(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    requested_object_ref = object_ref_from_mapping(payload)
    requested_object_id = str(requested_object_ref.get("objectId") or "")
    runs: list[dict[str, Any]] = []
    for path in sorted(WORKFLOW_RUNS_DIR.glob("*.json"), reverse=True):
        run = read_json_file(path, {})
        if not isinstance(run, dict) or not run:
            continue
        if topic_id and str(run.get("topicid") or "") != topic_id:
            continue
        if book_md5 and str(run.get("bookmd5") or "") != book_md5:
            continue
        summary = workflow_run_summary(run)
        if requested_object_id and str(summary.get("mnObjectId") or "") != requested_object_id:
            continue
        runs.append(summary)
        if len(runs) >= int(payload.get("limit") or 20):
            break
    return {
        "ok": True,
        "message": f"已读取 {len(runs)} 个工作流。",
        "workflowRuns": runs,
        "runCount": len(runs),
        "latestStatus": str(runs[0].get("status") or "none") if runs else "none",
        "workflowTemplates": workflow_engine.list_workflow_templates(),
    }


def workflow_cancel(payload: dict[str, Any]) -> dict[str, Any]:
    run_id = str(payload.get("workflowRunId") or payload.get("id") or "")
    loaded = load_workflow_run(run_id)
    if not loaded.get("ok"):
        return loaded
    run = loaded["workflowRun"]
    run["status"] = "cancelled"
    run["updatedAt"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    write_json_file(workflow_run_path(str(run.get("id") or run_id)), run)
    return {"ok": True, "message": "工作流已标记为取消。", "workflowRun": run, "summary": workflow_run_summary(run)}


def knowledge_index_ingest_context(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    entities = payload.get("entities") if isinstance(payload.get("entities"), list) else []
    if entities:
        result = knowledge_index.ingest_entities(
            entities,
            topicid=topic_id,
            bookmd5=book_md5,
            source=str(payload.get("source") or "marginnote-entities"),
            metadata={
                "contextScope": str(payload.get("contextScope") or payload.get("scope") or ""),
                "documentTitle": str(payload.get("documentTitle") or payload.get("docTitle") or ""),
                "selectedNoteId": str(payload.get("selectedNoteId") or payload.get("noteid") or ""),
            },
        )
        if result.get("ok"):
            result["reply"] = f"已加入知识索引：{result.get('entityCount') or 0} 个结构化实体。"
        return result
    context_text = (
        str(payload.get("text") or "").strip()
        or selected_context(payload)
        or str(payload.get("prompt") or "").strip()
    )
    title = (
        str(payload.get("title") or "").strip()
        or str(payload.get("documentTitle") or payload.get("docTitle") or "").strip()
        or str(payload.get("selectedNoteTitle") or "").strip()
        or "当前 MarginNote 上下文"
    )
    result = knowledge_index.ingest_entry(
        kind=str(payload.get("kind") or "context"),
        title=title,
        text=context_text,
        topicid=topic_id,
        bookmd5=book_md5,
        source=str(payload.get("source") or "marginnote-context"),
        metadata={
            "contextScope": str(payload.get("contextScope") or payload.get("scope") or ""),
            "documentTitle": str(payload.get("documentTitle") or payload.get("docTitle") or ""),
            "selectedNoteId": str(payload.get("selectedNoteId") or payload.get("noteid") or ""),
        },
    )
    if result.get("ok"):
        result["reply"] = f"已加入知识索引：{result['entry']['title']}"
    return result


def knowledge_index_search_action(payload: dict[str, Any]) -> dict[str, Any]:
    result = knowledge_index.search(
        str(payload.get("query") or payload.get("prompt") or ""),
        topicid=normalize_topic_id(payload),
        bookmd5=normalize_book_md5(payload),
        limit=int(payload.get("limit") or 8),
    )
    if result.get("ok"):
        lines = []
        for item in result.get("matches", []):
            if not isinstance(item, dict):
                continue
            source_ref = item.get("sourceRef") if isinstance(item.get("sourceRef"), dict) else {}
            source_bits = []
            if item.get("noteId"):
                source_bits.append(f"noteId={item.get('noteId')}")
            if source_ref.get("page"):
                source_bits.append(f"p.{source_ref.get('page')}")
            if source_ref.get("quote"):
                source_bits.append(f"quote={source_ref.get('quote')}")
            suffix = (" / " + " / ".join(source_bits)) if source_bits else ""
            lines.append(f"- {item.get('title')} [{item.get('kind')}]：{item.get('snippet')}{suffix}")
        result["reply"] = "知识索引搜索结果：\n" + ("\n".join(lines) if lines else "未命中。")
    return result


def review_queue_store() -> dict[str, Any]:
    data = read_json_file(REVIEW_QUEUE_PATH, {})
    if not isinstance(data, dict):
        data = {}
    items = data.get("items") if isinstance(data.get("items"), list) else []
    return {"schema": "codex.mn.reviewQueue.v1", "items": items}


def write_review_queue_store(data: dict[str, Any]) -> None:
    REVIEW_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    items = data.get("items") if isinstance(data.get("items"), list) else []
    write_json_file(REVIEW_QUEUE_PATH, {"schema": "codex.mn.reviewQueue.v1", "items": items})


def review_queue_item_id(topic_id: str, book_md5: str, draft_id: str, index: int, card: dict[str, Any]) -> str:
    basis = "|".join(
        [
            topic_id,
            book_md5,
            draft_id,
            str(index),
            str(card.get("codexId") or ""),
            str(card.get("title") or ""),
            str(card.get("reviewPrompt") or ""),
        ]
    )
    return "review:" + hashlib.sha256(basis.encode("utf-8")).hexdigest()[:24]


def review_queue_summary(items: list[dict[str, Any]]) -> dict[str, Any]:
    due_count = len([item for item in items if str(item.get("state") or "") in {"new", "due"}])
    type_counts: dict[str, int] = {}
    for item in items:
        card_type = str(item.get("cardType") or "concept")
        type_counts[card_type] = type_counts.get(card_type, 0) + 1
    return {
        "schema": "codex.mn.reviewQueueSummary.v1",
        "totalCount": len(items),
        "dueCount": due_count,
        "typeCounts": type_counts,
    }


def filter_review_queue_items(items: list[dict[str, Any]], payload: dict[str, Any]) -> list[dict[str, Any]]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    requested_object = object_ref_from_mapping(payload)
    requested_object_id = str(requested_object.get("objectId") or payload.get("mnObjectId") or "").strip()
    out: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if topic_id and str(item.get("topicid") or "") != topic_id:
            continue
        if book_md5 and str(item.get("bookmd5") or "") != book_md5:
            continue
        if requested_object_id and str(item.get("mnObjectId") or "") != requested_object_id:
            continue
        out.append(item)
    return out


def review_queue_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": "codex.mn.reviewQueue.v1",
        "items": items,
        "summary": review_queue_summary(items),
    }


def review_queue_list(payload: dict[str, Any]) -> dict[str, Any]:
    store = review_queue_store()
    filtered = filter_review_queue_items([item for item in store.get("items", []) if isinstance(item, dict)], payload)
    limit = int(payload.get("limit") or 50)
    filtered = filtered[: max(1, min(limit, 200))]
    queue = review_queue_payload(filtered)
    return {
        "ok": True,
        "message": f"已读取 {len(filtered)} 张复习卡。",
        "reviewQueue": queue,
        "summary": queue["summary"],
        "items": filtered,
    }


def review_queue_add(payload: dict[str, Any]) -> dict[str, Any]:
    draft_id = str(payload.get("draftId") or payload.get("id") or "").strip()
    if not draft_id:
        return {"ok": False, "message": "缺少草稿 ID。"}
    draft = load_draft(draft_id)
    if not draft.get("ok"):
        return draft
    cards = draft.get("cards") if isinstance(draft.get("cards"), list) else []
    if not cards:
        return {"ok": False, "message": "草稿没有可加入复习队列的卡片。", "id": draft_id}
    topic_id = str(payload.get("topicid") or draft.get("topicid") or "")
    book_md5 = str(payload.get("bookmd5") or draft.get("bookmd5") or "")
    object_ref = object_ref_from_mapping(payload)
    if not object_ref_has_identity(object_ref):
        object_ref = draft.get("mnObject") if isinstance(draft.get("mnObject"), dict) else {}
    mn_object_id = str(object_ref.get("objectId") or payload.get("mnObjectId") or "").strip()
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    store = review_queue_store()
    items = [item for item in store.get("items", []) if isinstance(item, dict)]
    existing_ids = {str(item.get("reviewId") or "") for item in items}
    added: list[dict[str, Any]] = []
    duplicate_count = 0
    for index, raw_card in enumerate(cards, start=1):
        if not isinstance(raw_card, dict):
            continue
        review_id = review_queue_item_id(topic_id, book_md5, draft_id, index, raw_card)
        if review_id in existing_ids:
            duplicate_count += 1
            continue
        source = raw_card.get("source") if isinstance(raw_card.get("source"), dict) else {}
        item = {
            "schema": "codex.mn.reviewQueueItem.v1",
            "reviewId": review_id,
            "draftId": draft_id,
            "cardIndex": index,
            "topicid": topic_id,
            "bookmd5": book_md5,
            "mnObjectId": mn_object_id,
            "mnObject": object_ref if object_ref_has_identity(object_ref) else {},
            "title": str(raw_card.get("title") or f"复习卡 {index}"),
            "cardType": str(raw_card.get("cardType") or raw_card.get("type") or "concept"),
            "learningGoal": str(raw_card.get("learningGoal") or ""),
            "reviewPrompt": str(raw_card.get("reviewPrompt") or raw_card.get("title") or ""),
            "source": source,
            "state": "new",
            "dueAt": now,
            "createdAt": now,
            "updatedAt": now,
        }
        items.insert(0, item)
        existing_ids.add(review_id)
        added.append(item)
    write_review_queue_store({"items": items})
    filtered = filter_review_queue_items(items, payload)
    queue = review_queue_payload(filtered)
    return {
        "ok": True,
        "message": f"已加入复习队列：新增 {len(added)} 张，重复 {duplicate_count} 张。",
        "reviewQueue": queue,
        "summary": queue["summary"],
        "items": filtered,
        "addedItems": added,
        "addedCount": len(added),
        "duplicateCount": duplicate_count,
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


def mn_api_status_fields(settings: dict[str, Any] | None = None) -> dict[str, Any]:
    load_env_file()
    settings = settings or runtime_settings()
    status = marginnote_api_adapter.adapter_status(settings, get_setting("MN_URL_API_SECRET"))
    return {
        "mn_api_backend": status["backend"],
        "mn_api_backend_label": status["backendLabel"],
        "mn_url_api_configured": bool(status["urlApiConfigured"]),
        "mnApi": status,
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


def request_mindmap_tree(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "请求读取脑图失败：缺少 topicid。"}
    target = payload.get("mindmapTarget") if isinstance(payload.get("mindmapTarget"), dict) else {}
    command = {
        "nativeAction": "read_mindmap_tree",
        "message": "请 MN4 插件读取当前脑图或选中子树。",
        "source": str(payload.get("source") or "request_mindmap_tree"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "selectedNoteId": str(payload.get("selectedNoteId") or target.get("selectedNoteId") or ""),
        "selectedNoteTitle": str(payload.get("selectedNoteTitle") or target.get("selectedNoteTitle") or ""),
        "targetMode": str(target.get("mode") or payload.get("targetMode") or "selected_or_document_root"),
        "workflowRunId": str(payload.get("workflowRunId") or ""),
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件读取当前脑图树。",
        "reply": (
            "已把“读取当前脑图树”命令加入当前 notebook 队列。\n\n"
            "MN4 插件轮询后会尝试读取当前选中节点或目标脑图，并把结果记录到诊断事件。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
    }


def request_mn_object_registry_scan(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "请求扫描 MN 对象失败：缺少 topicid。"}
    try:
        limit = max(1, min(int(payload.get("limit") or 200), 1000))
    except Exception:
        limit = 200
    command = {
        "nativeAction": "scan_mn_objects",
        "message": "请 MN4 插件扫描当前 notebook 可见对象并写入 MNObject Registry。",
        "source": str(payload.get("source") or "request_mn_object_registry_scan"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "limit": limit,
        "selectedNoteId": str(payload.get("selectedNoteId") or ""),
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件扫描当前 notebook 对象。",
        "reply": (
            "已把“扫描 MN 对象”命令加入当前 notebook 队列。\n\n"
            "MN4 插件轮询后会尽量枚举当前 notebook 中可见的卡片/脑图节点，并把结果写入 MNObject Registry。"
        ),
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
    }


def request_mindmap_diff_apply(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "局部应用脑图 Diff 失败：缺少 topicid。"}
    permission = runtime_settings().get("permission", "notes")
    if permission == "read_only":
        return {
            "ok": False,
            "message": "局部应用脑图 Diff 失败：当前权限是 read_only，需要 notes 或 full。",
            "reply": "当前权限是 read_only，不能写入 MarginNote。请在设置页把权限改为 notes 或 full 后再试。",
            "queue": queue_status_payload(topic_id, book_md5),
        }
    plan = payload.get("mindmapDiffOperationPlan")
    if not isinstance(plan, dict):
        return {"ok": False, "message": "局部应用脑图 Diff 失败：缺少 mindmapDiffOperationPlan。"}
    operations = plan.get("operations") if isinstance(plan.get("operations"), list) else []
    raw_operations = [item for item in operations if isinstance(item, dict)]
    delete_suggestion_operations = [
        item
        for item in raw_operations
        if str(item.get("mutation") or "") in {"delete_suggest", "delete"}
        or str(item.get("op") or "") == "suggest_delete_mindmap_node"
    ]
    clean_operations = [item for item in raw_operations if item not in delete_suggestion_operations]
    skipped_delete_suggestion_count = len(delete_suggestion_operations)
    if not clean_operations:
        return {
            "ok": False,
            "message": (
                "局部应用脑图 Diff 失败：没有可执行操作。"
                if not skipped_delete_suggestion_count
                else "局部应用脑图 Diff 没有可直接执行的非删除操作；删除建议需要二次确认。"
            ),
            "applyPlan": {
                **plan,
                "operationCount": 0,
                "operations": [],
                "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
                "applyBoundary": {
                    **(plan.get("applyBoundary") if isinstance(plan.get("applyBoundary"), dict) else {}),
                    "localApplyStatus": "empty",
                    "currentApplyPath": "local_operation_queue",
                    "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
                },
            },
        }

    native_caps = latest_native_api_capabilities(topic_id, book_md5)
    matrix = native_caps.get("capabilityMatrix") if isinstance(native_caps.get("capabilityMatrix"), dict) else {}
    native_caps_for_apply = dict(native_caps)
    matrix_for_apply = dict(matrix)
    native_mindmap = matrix_for_apply.get("nativeMindmap") if isinstance(matrix_for_apply.get("nativeMindmap"), dict) else {}
    matrix_for_apply["nativeMindmap"] = {
        **native_mindmap,
        "ready": True,
        "available": True,
        "nextStep": str(native_mindmap.get("nextStep") or "create 操作走本地脑图 Diff 执行器。"),
    }
    native_caps_for_apply["capabilityMatrix"] = matrix_for_apply
    dry_run_plan = {
        **plan,
        "operationCount": len(clean_operations),
        "operations": clean_operations,
    }
    dry_run = operation_runtime.simulate_operation_manifest(
        {"operationPlan": dry_run_plan},
        {**runtime_settings(), "permission": permission, "mnApiBackend": "native"},
        native_caps_for_apply,
        {},
    )
    per_operation = dry_run.get("perOperation") if isinstance(dry_run.get("perOperation"), dict) else {}
    dry_run_items = per_operation.get("items") if isinstance(per_operation.get("items"), list) else []
    blocked = [
        {
            "opId": str(item.get("opId") or ""),
            "op": str(item.get("op") or ""),
            "mutation": str(item.get("mutation") or ""),
            "title": str(item.get("title") or ""),
            "requirement": str(item.get("requirement") or ""),
            "reason": str(item.get("reason") or ""),
            "nextStep": str(item.get("nextStep") or ""),
            "noteId": str(item.get("noteId") or ""),
            "verificationLevel": str(item.get("verificationLevel") or ""),
        }
        for item in dry_run_items
        if str(item.get("status") or "") in {"blocked", "unknown"}
    ]

    if blocked:
        apply_plan = {
            **plan,
            "operationCount": len(clean_operations),
            "operations": clean_operations,
            "dryRun": dry_run,
            "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
            "applyBoundary": {
                **(plan.get("applyBoundary") if isinstance(plan.get("applyBoundary"), dict) else {}),
                "localApplyStatus": "blocked",
                "currentApplyPath": "local_operation_queue",
                "blockedOperationCount": len(blocked),
                "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
            },
        }
        return {
            "ok": False,
            "message": f"局部应用脑图 Diff 已阻断：{len(blocked)} 个操作缺少 MN 原生能力。",
            "reply": (
                "局部应用脑图 Diff 已阻断。\n\n"
                f"阻断操作：{len(blocked)}\n"
                f"首个原因：{blocked[0]['reason']}\n"
                "请先刷新 MN 原生能力；update/merge/move/delete 不能在未确认能力时执行。"
            ),
            "applyPlan": apply_plan,
            "dryRun": dry_run,
            "blockedOperations": blocked,
            "nativeApiCapabilities": native_caps,
            "queue": queue_status_payload(topic_id, book_md5),
        }

    transaction_id = transaction_manager.safe_transaction_id(
        payload.get("transactionId") or f"mindmap-diff-{uuid.uuid4().hex[:16]}"
    )
    apply_plan = {
        **plan,
        "transactionId": transaction_id,
        "operationCount": len(clean_operations),
        "operations": clean_operations,
        "dryRun": dry_run,
        "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
        "applyBoundary": {
            **(plan.get("applyBoundary") if isinstance(plan.get("applyBoundary"), dict) else {}),
            "localApplyStatus": "queued",
            "currentApplyPath": "local_operation_queue",
            "blockedOperationCount": 0,
            "skippedDeleteSuggestionCount": skipped_delete_suggestion_count,
        },
    }
    command = {
        "nativeAction": "apply_mindmap_diff_operations",
        "message": "请 MN4 插件逐项应用脑图 Diff 操作。",
        "source": str(payload.get("source") or "request_mindmap_diff_apply"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "mindmapDiffOperationPlan": apply_plan,
        "draftId": str(payload.get("draftId") or payload.get("id") or ""),
        "transactionId": transaction_id,
        "mnObject": payload.get("mnObject") if isinstance(payload.get("mnObject"), dict) else {},
    }
    queued = enqueue_command({**payload, "command": command})
    if not queued.get("ok"):
        return queued
    return {
        "ok": True,
        "message": "已请求 MN4 插件逐项应用脑图 Diff。",
        "reply": (
            "已把“逐项应用脑图 Diff”命令加入当前 notebook 队列。\n\n"
            f"操作数：{len(clean_operations)}。保持该文档在 MarginNote 4 中打开，插件轮询后会执行并上报结果。"
        ),
        "applyPlan": apply_plan,
        "queued": queued["queued"],
        "queue": queue_status_payload(topic_id, book_md5),
        "nativeApiCapabilities": native_caps,
    }


def request_mindmap_delete_confirmation(payload: dict[str, Any]) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if not topic_id:
        return {"ok": False, "message": "删除建议确认失败：缺少 topicid。"}
    plan = payload.get("mindmapDiffOperationPlan")
    if not isinstance(plan, dict):
        return {"ok": False, "message": "删除建议确认失败：缺少 mindmapDiffOperationPlan。"}
    operations = plan.get("operations") if isinstance(plan.get("operations"), list) else []
    delete_operations = [
        item
        for item in operations
        if isinstance(item, dict)
        and (
            str(item.get("mutation") or "") in {"delete_suggest", "delete"}
            or str(item.get("op") or "") == "suggest_delete_mindmap_node"
        )
    ]
    if not delete_operations:
        return {
            "ok": False,
            "message": "删除建议确认失败：当前计划没有 delete_suggest 操作。",
            "queue": queue_status_payload(topic_id, book_md5),
        }
    target_note_ids: list[str] = []
    seen: set[str] = set()
    for operation in delete_operations:
        current_ref = operation.get("currentRef") if isinstance(operation.get("currentRef"), dict) else {}
        note_id = str(current_ref.get("noteId") or operation.get("noteId") or "").strip()
        if note_id and note_id not in seen:
            seen.add(note_id)
            target_note_ids.append(note_id)
    if not target_note_ids:
        return {
            "ok": False,
            "message": "删除建议确认失败：delete_suggest 缺少 currentRef.noteId，无法安全删除。",
            "deleteOperations": delete_operations,
            "queue": queue_status_payload(topic_id, book_md5),
        }

    transaction_id = transaction_manager.safe_transaction_id(
        payload.get("transactionId") or f"mindmap-delete-{uuid.uuid4().hex[:16]}"
    )
    event_result = append_event(
        {
            "event": "mindmapDeleteSuggestionPrepared",
            "topicid": topic_id,
            "bookmd5": book_md5,
            "source": str(payload.get("source") or "request_mindmap_delete_confirmation"),
            "extra": {
                "transactionId": transaction_id,
                "targetNoteIds": target_note_ids,
                "deleteOperations": delete_operations,
                "operationCount": len(delete_operations),
                "message": f"删除建议等待确认：{len(target_note_ids)} 个节点。",
            },
        }
    )
    transaction = event_result.get("event", {}).get("transaction") if isinstance(event_result.get("event"), dict) else {}
    return {
        "ok": True,
        "message": "已创建脑图删除建议二次确认事务。",
        "reply": (
            "已把脑图删除建议放入事务中心，尚未删除任何现有节点。\n\n"
            f"建议删除节点：{len(target_note_ids)}\n"
            "请在事务中心点击“删除”确认，或点击“忽略”保留原脑图。"
        ),
        "transactionId": transaction_id,
        "deleteConfirmation": {
            "schema": "codex.mn.mindmapDeleteConfirmation.v1",
            "status": "delete_pending_confirmation",
            "targetNoteIds": target_note_ids,
            "operationCount": len(delete_operations),
            "transaction": transaction,
        },
        "queue": queue_status_payload(topic_id, book_md5),
    }


def mindmap_tree_cache_path(topic_id: str, book_md5: str) -> Path:
    key = f"{topic_id}|{book_md5 or 'any'}"
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return MINDMAP_TREES_DIR / f"{digest}.json"


def write_latest_mindmap_tree(record: dict[str, Any]) -> dict[str, Any]:
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    tree = extra.get("currentMindmap") if isinstance(extra.get("currentMindmap"), dict) else {}
    topic_id = str(record.get("topicid") or "")
    book_md5 = str(record.get("bookmd5") or "")
    if not topic_id or not tree:
        return {"ok": False, "reason": "missing-topic-or-tree"}
    payload = {
        "schema": "codex.mn.mindmapTreeCache.v1",
        "sourceEvent": str(record.get("event") or ""),
        "topicid": topic_id,
        "bookmd5": book_md5,
        "updatedAt": str(record.get("ts") or time.strftime("%Y-%m-%dT%H:%M:%S%z")),
        "selectedNoteId": str(extra.get("selectedNoteId") or tree.get("noteId") or ""),
        "selectedNoteTitle": str(extra.get("selectedNoteTitle") or tree.get("title") or ""),
        "rootTitle": str(tree.get("title") or extra.get("selectedNoteTitle") or ""),
        "nodeCount": int(extra.get("nodeCount") or operation_runtime.count_mindmap_nodes(tree)),
        "truncatedCount": int(extra.get("truncatedCount") or 0),
        "currentMindmap": tree,
    }
    write_json_file(mindmap_tree_cache_path(topic_id, book_md5), payload)
    registry_result: dict[str, Any] = {}
    try:
        registry_result = register_mindmap_tree_cache_objects({"topicid": topic_id, "bookmd5": book_md5}, payload)
    except Exception as exc:
        registry_result = {"ok": False, "message": f"MNObject Registry 写入脑图缓存失败：{exc}"}
    return {"ok": True, "cache": payload, "mnObjectRegistry": registry_result}


def read_latest_mindmap_tree(topic_id: str, book_md5: str) -> dict[str, Any]:
    if not topic_id:
        return {}
    payload = read_json_file(mindmap_tree_cache_path(topic_id, book_md5), {})
    return payload if isinstance(payload, dict) else {}


def mindmap_tree_preview(tree: dict[str, Any], max_nodes: int = 24, max_depth: int = 2) -> list[dict[str, Any]]:
    preview: list[dict[str, Any]] = []

    def walk(node: Any, depth: int, path: str) -> None:
        if len(preview) >= max_nodes or depth > max_depth or not isinstance(node, dict):
            return
        children = node.get("children") if isinstance(node.get("children"), list) else []
        preview.append(
            {
                "noteId": str(node.get("noteId") or ""),
                "title": str(node.get("title") or node.get("name") or "未命名节点"),
                "depth": depth,
                "path": path,
                "childCount": len(children),
            }
        )
        for index, child in enumerate(children):
            if len(preview) >= max_nodes:
                break
            walk(child, depth + 1, f"{path}.{index + 1}" if path else str(index + 1))

    walk(tree, 0, "1")
    return preview


def latest_mindmap_tree_cache_status(topic_id: str = "", book_md5: str = "", limit: int = 120) -> dict[str, Any]:
    topic_id = str(topic_id or "")
    book_md5 = str(book_md5 or "")
    for item in reversed(read_recent_events(limit)):
        if str(item.get("event") or "") != "mindmapTreeReadFinished":
            continue
        if topic_id and str(item.get("topicid") or "") != topic_id:
            continue
        if book_md5 and str(item.get("bookmd5") or "") != book_md5:
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        tree = extra.get("currentMindmap") if isinstance(extra.get("currentMindmap"), dict) else {}
        node_count = int(extra.get("nodeCount") or operation_runtime.count_mindmap_nodes(tree) or 0)
        truncated_count = int(extra.get("truncatedCount") or 0)
        root_title = str(tree.get("title") or extra.get("selectedNoteTitle") or "")
        preview = mindmap_tree_preview(tree)
        return {
            "schema": "codex.mn.mindmapTreeCache.v1",
            "available": True,
            "status": "ready",
            "summary": f"当前脑图树缓存：{node_count} 个节点，截断 {truncated_count} 个。",
            "sourceEvent": "mindmapTreeReadFinished",
            "topicid": str(item.get("topicid") or ""),
            "bookmd5": str(item.get("bookmd5") or ""),
            "updatedAt": str(item.get("ts") or ""),
            "selectedNoteId": str(extra.get("selectedNoteId") or tree.get("noteId") or ""),
            "selectedNoteTitle": str(extra.get("selectedNoteTitle") or root_title),
            "rootTitle": root_title,
            "nodeCount": node_count,
            "truncatedCount": truncated_count,
            "treePreview": preview,
            "treePreviewCount": len(preview),
            "treePreviewTruncated": node_count > len(preview),
        }
    return {
        "schema": "codex.mn.mindmapTreeCache.v1",
        "available": False,
        "status": "unknown",
        "summary": "还没有读取当前脑图树。",
        "sourceEvent": "",
        "topicid": topic_id,
        "bookmd5": book_md5,
        "updatedAt": "",
        "selectedNoteId": "",
        "selectedNoteTitle": "",
        "rootTitle": "",
        "nodeCount": 0,
        "truncatedCount": 0,
        "treePreview": [],
        "treePreviewCount": 0,
        "treePreviewTruncated": False,
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
    raw_draft_path = DRAFTS_DIR / f"{clean_id}.json"
    raw_draft = read_json_file(raw_draft_path, {})
    if not isinstance(raw_draft, dict) or not raw_draft:
        raw_draft = draft
    raw_manifest = raw_draft.get("operationManifest") if isinstance(raw_draft.get("operationManifest"), dict) else {}
    if not raw_manifest:
        raw_manifest = draft_operation_manifest(
            raw_draft.get("cards") if isinstance(raw_draft.get("cards"), list) else [],
            raw_draft.get("mindmap") if isinstance(raw_draft.get("mindmap"), dict) else None,
            raw_draft.get("writeTarget") if isinstance(raw_draft.get("writeTarget"), dict) else {},
            topic_id or str(raw_draft.get("topicid") or ""),
            book_md5 or str(raw_draft.get("bookmd5") or ""),
        )
    dry_run = operation_dry_run(raw_manifest, topic_id or str(raw_draft.get("topicid") or ""), book_md5 or str(raw_draft.get("bookmd5") or ""))
    raw_manifest = {**raw_manifest, "dryRun": dry_run}
    raw_draft["operationManifest"] = raw_manifest
    if raw_draft_path.exists():
        write_json_file(raw_draft_path, raw_draft)
    if dry_run.get("status") == "blocked":
        return {
            "ok": False,
            "message": str(dry_run.get("message") or "写入草稿已被 Operation dry-run 阻断。"),
            "reply": (
                "写入草稿已阻断。\n\n"
                f"原因：{dry_run.get('message') or 'Operation dry-run 未通过'}\n"
                "请先按 dry-run 提示调整权限或配置 MN 接口，再重新写入。"
            ),
            "draft": draft_summary(clean_id, raw_draft),
            "dryRun": dry_run,
            "operationManifest": raw_manifest,
        }
    command = {
        "nativeAction": "write_draft",
        "draftId": clean_id,
        "message": "请 MN4 插件写入已确认草稿。",
        "source": str(payload.get("source") or "request_draft_write"),
        "requested_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    mn_object = raw_draft.get("mnObject") if isinstance(raw_draft.get("mnObject"), dict) else {}
    if mn_object:
        source_ref = mn_object.get("sourceRef") if isinstance(mn_object.get("sourceRef"), dict) else {}
        command.update(
            {
                "mnObjectId": str(mn_object.get("objectId") or ""),
                "mnObjectKind": str(mn_object.get("kind") or ""),
                "mnObjectTitle": str(mn_object.get("title") or ""),
                "mnObjectSourceRef": source_ref,
            }
        )
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
        "draft": draft_summary(clean_id, raw_draft),
        "dryRun": dry_run,
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
            "生成/更新 release/CodexCompanion-0.4.28-latest.pkg；随后重新运行 python3 release_acceptance.py --json",
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


def object_ref_from_mapping(data: dict[str, Any], fallback: dict[str, Any] | None = None) -> dict[str, Any]:
    fallback = fallback if isinstance(fallback, dict) else {}
    mn_object = data.get("mnObject") if isinstance(data.get("mnObject"), dict) else {}
    if mn_object:
        object_ref = {
            "objectId": str(mn_object.get("objectId") or fallback.get("objectId") or ""),
            "kind": str(mn_object.get("kind") or fallback.get("kind") or ""),
            "title": str(mn_object.get("title") or fallback.get("title") or ""),
            "sourceRef": transaction_manager.clean_source_ref(
                mn_object.get("sourceRef")
                if isinstance(mn_object.get("sourceRef"), dict)
                else fallback.get("sourceRef")
            ),
        }
        return object_ref if object_ref_has_identity(object_ref) else {}
    object_ref = transaction_manager.clean_object_ref(data, fallback)
    return object_ref if object_ref_has_identity(object_ref) else {}


def object_ref_from_existing_session(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return object_ref_from_mapping(data) if isinstance(data, dict) else {}


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
    object_ref = object_ref_from_mapping(data)
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
        "objectRef": object_ref,
        "mnObjectId": str(object_ref.get("objectId") or ""),
        "mnObjectKind": str(object_ref.get("kind") or ""),
        "mnObjectTitle": str(object_ref.get("title") or ""),
    }


def conversation_matches_payload(item: dict[str, Any], payload: dict[str, Any]) -> bool:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if topic_id and str(item.get("topicid") or "") != topic_id:
        return False
    if book_md5 and str(item.get("bookmd5") or "") != book_md5:
        return False
    requested_object_ref = object_ref_from_mapping(payload)
    requested_object_id = str(requested_object_ref.get("objectId") or "")
    if requested_object_id:
        item_object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
        if str(item_object_ref.get("objectId") or "") != requested_object_id:
            return False
    return True


def conversation_summary(item: dict[str, Any]) -> dict[str, Any]:
    object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
    return {
        "sessionId": item.get("sessionId") or "",
        "conversationId": item.get("conversationId") or "",
        "topicid": item.get("topicid") or "",
        "bookmd5": item.get("bookmd5") or "",
        "title": item.get("title") or "新对话",
        "updatedAt": item.get("updatedAt") or "",
        "messageCount": int(item.get("messageCount") or 0),
        "lastMessage": item.get("lastMessage") or "",
        "objectRef": object_ref if object_ref_has_identity(object_ref) else {},
        "mnObjectId": str(object_ref.get("objectId") or ""),
        "mnObjectKind": str(object_ref.get("kind") or ""),
        "mnObjectTitle": str(object_ref.get("title") or ""),
    }


def conversation_payload_for_new(payload: dict[str, Any]) -> dict[str, Any]:
    conversation_id = str(uuid.uuid4()).upper()
    derived = {**payload, "conversationId": conversation_id}
    object_ref = object_ref_from_mapping(payload)
    return {
        "sessionId": session_key(derived),
        "conversationId": conversation_id,
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "title": "新对话",
        "updatedAt": "",
        "messageCount": 0,
        "lastMessage": "",
        "objectRef": object_ref,
        "mnObjectId": str(object_ref.get("objectId") or ""),
        "mnObjectKind": str(object_ref.get("kind") or ""),
        "mnObjectTitle": str(object_ref.get("title") or ""),
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
        return {"ok": False, "message": "加载历史对话失败：该会话不属于当前文档或当前对象。"}
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
        return {"ok": False, "message": "删除历史对话失败：该会话不属于当前文档或当前对象。"}
    try:
        path.unlink()
    except Exception as exc:
        return {"ok": False, "message": f"删除历史对话失败：{exc}"}
    return {"ok": True, "message": "历史对话已删除。", "deleted": session_id}


def save_history(payload: dict[str, Any], history: list[dict[str, str]]) -> None:
    path = session_path(payload)
    conversation_id = normalize_conversation_id(payload)
    title = conversation_title_from_history(history)
    object_ref = object_ref_from_mapping(payload, object_ref_from_existing_session(path))
    body = {
        "topicid": normalize_topic_id(payload),
        "bookmd5": normalize_book_md5(payload),
        "source": str(payload.get("source") or ""),
        "conversationId": conversation_id,
        "title": title,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "history": history[-16:],
    }
    if object_ref_has_identity(object_ref):
        body["objectRef"] = object_ref
        body["mnObjectId"] = str(object_ref.get("objectId") or "")
        body["mnObjectKind"] = str(object_ref.get("kind") or "")
        body["mnObjectTitle"] = str(object_ref.get("title") or "")
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
    object_ref = object_ref_from_mapping(payload, object_ref_from_existing_session(session_path(payload)))
    return {
        "ok": True,
        "message": f"已读取历史对话：{len(history)} 条。",
        "history": history,
        "history_count": len(history),
        "session": session_key(payload),
        "objectRef": object_ref,
        "mnObjectId": str(object_ref.get("objectId") or ""),
    }


def merge_object_ref(primary: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    primary = primary if isinstance(primary, dict) else {}
    fallback = fallback if isinstance(fallback, dict) else {}
    source_ref = primary.get("sourceRef") if isinstance(primary.get("sourceRef"), dict) else {}
    fallback_source_ref = fallback.get("sourceRef") if isinstance(fallback.get("sourceRef"), dict) else {}
    return {
        "objectId": str(primary.get("objectId") or fallback.get("objectId") or ""),
        "kind": str(primary.get("kind") or fallback.get("kind") or ""),
        "title": str(primary.get("title") or fallback.get("title") or ""),
        "sourceRef": transaction_manager.clean_source_ref(source_ref or fallback_source_ref),
    }


def operation_ledger_id(prefix: str, source_id: Any) -> str:
    clean_prefix = re.sub(r"[^a-z_]", "", str(prefix or "").lower())[:40]
    clean_id = re.sub(r"[^A-Za-z0-9._-]", "", str(source_id or ""))[:140]
    return f"{clean_prefix}:{clean_id}" if clean_prefix and clean_id else ""


def operation_ledger_action(ledger_id: str) -> dict[str, Any]:
    return {
        "schema": "codex.mn.operationLedgerAction.v1",
        "label": "查看账本",
        "action": "operation_ledger_get",
        "payload": {"ledgerId": ledger_id},
    }


def operation_ledger_entry(
    *,
    ledger_id: str,
    entry_type: str,
    source_id: str,
    title: str,
    status: str,
    summary: str,
    topicid: str,
    bookmd5: str,
    object_ref: dict[str, Any],
    created_at: str,
    updated_at: str,
    counts: dict[str, Any] | None = None,
) -> dict[str, Any]:
    object_ref = object_ref if isinstance(object_ref, dict) else {}
    return {
        "schema": "codex.mn.operationLedgerEntry.v1",
        "ledgerId": ledger_id,
        "entryType": entry_type,
        "sourceId": source_id,
        "title": title,
        "status": status,
        "summary": summary,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "objectRef": object_ref,
        "createdAt": created_at,
        "updatedAt": updated_at or created_at,
        "counts": counts or {},
        "ledgerAction": operation_ledger_action(ledger_id),
    }


def operation_ledger_object_filter(payload: dict[str, Any]) -> tuple[dict[str, Any], str]:
    requested_object_ref = object_ref_from_mapping(payload)
    requested_object_id = str(
        payload.get("mnObjectId")
        or payload.get("objectId")
        or requested_object_ref.get("objectId")
        or ""
    ).strip()
    if requested_object_id and not requested_object_ref.get("objectId"):
        requested_object_ref = {"objectId": requested_object_id, "kind": "", "title": "", "sourceRef": {}}
    return requested_object_ref, requested_object_id


def operation_ledger_matches(
    *,
    payload: dict[str, Any],
    topicid: str,
    bookmd5: str,
    object_ref: dict[str, Any],
    requested_object_id: str,
) -> bool:
    requested_topic = normalize_topic_id(payload)
    requested_book = normalize_book_md5(payload)
    if requested_topic and topicid != requested_topic:
        return False
    if requested_book and bookmd5 != requested_book:
        return False
    if requested_object_id and str(object_ref.get("objectId") or "") != requested_object_id:
        return False
    return True


def operation_ledger_filter_payload(payload: dict[str, Any]) -> dict[str, str]:
    return {
        "entryTypeFilter": str(payload.get("entryTypeFilter") or payload.get("entryType") or "").strip(),
        "statusFilter": str(payload.get("statusFilter") or payload.get("status") or "").strip(),
        "query": str(payload.get("query") or payload.get("search") or "").strip(),
    }


def operation_ledger_entry_text(entry: dict[str, Any]) -> str:
    object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
    source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
    fields = [
        entry.get("ledgerId"),
        entry.get("entryType"),
        entry.get("sourceId"),
        entry.get("title"),
        entry.get("status"),
        entry.get("summary"),
        object_ref.get("objectId"),
        object_ref.get("kind"),
        object_ref.get("title"),
        source_ref.get("noteId"),
        source_ref.get("documentTitle"),
        source_ref.get("quote"),
    ]
    return " ".join(str(item) for item in fields if item is not None).lower()


def filter_operation_ledger_entries(entries: list[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    entry_type = filters.get("entryTypeFilter", "").lower()
    status = filters.get("statusFilter", "").lower()
    query = filters.get("query", "").lower()
    out: list[dict[str, Any]] = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        if entry_type and str(entry.get("entryType") or "").lower() != entry_type:
            continue
        if status and str(entry.get("status") or "").lower() != status:
            continue
        if query and query not in operation_ledger_entry_text(entry):
            continue
        out.append(entry)
    return out


def workflow_operation_ledger_entry(run: dict[str, Any]) -> dict[str, Any]:
    summary = workflow_run_summary(run)
    object_ref = run.get("objectRef") if isinstance(run.get("objectRef"), dict) else {}
    ledger_id = operation_ledger_id("workflow", summary.get("id"))
    return operation_ledger_entry(
        ledger_id=ledger_id,
        entry_type="workflow_run",
        source_id=str(summary.get("id") or ""),
        title=str(summary.get("title") or summary.get("workflowId") or "Workflow run"),
        status=str(summary.get("status") or "unknown"),
        summary=(
            f"工作流：{summary.get('workflowId') or ''} / "
            f"队列 {summary.get('queuedCount') or 0} / "
            f"等待确认 {summary.get('waitingConfirmationCount') or 0}"
        ),
        topicid=str(summary.get("topicid") or ""),
        bookmd5=str(summary.get("bookmd5") or ""),
        object_ref=object_ref,
        created_at=str(summary.get("createdAt") or ""),
        updated_at=str(summary.get("updatedAt") or summary.get("createdAt") or ""),
        counts={
            "queued": int(summary.get("queuedCount") or 0),
            "waitingConfirmation": int(summary.get("waitingConfirmationCount") or 0),
            "manual": int(summary.get("manualCount") or 0),
        },
    )


def transaction_operation_ledger_entry(summary: dict[str, Any]) -> dict[str, Any]:
    transaction_id = str(summary.get("transactionId") or "")
    object_ref = summary.get("objectRef") if isinstance(summary.get("objectRef"), dict) else {}
    title = str(summary.get("mindmapTitle") or summary.get("draftId") or transaction_id or "AI 编辑事务")
    return operation_ledger_entry(
        ledger_id=operation_ledger_id("transaction", transaction_id),
        entry_type="ai_edit_transaction",
        source_id=transaction_id,
        title=title,
        status=str(summary.get("status") or "unknown"),
        summary=str(summary.get("message") or "AI 编辑事务记录。"),
        topicid=str(summary.get("topicid") or ""),
        bookmd5=str(summary.get("bookmd5") or ""),
        object_ref=object_ref,
        created_at=str(summary.get("createdAt") or summary.get("updatedAt") or ""),
        updated_at=str(summary.get("updatedAt") or summary.get("createdAt") or ""),
        counts={
            "created": int(summary.get("createdCount") or 0),
            "applied": int(summary.get("appliedCount") or 0),
            "deleted": int(summary.get("deletedCount") or 0),
            "failed": int(summary.get("failedCount") or 0),
            "cards": int(summary.get("cardCount") or 0),
        },
    )


def external_gateway_operation_ledger_entry(record: dict[str, Any]) -> dict[str, Any]:
    request_id = str(record.get("requestId") or "")
    object_ref = record.get("objectRef") if isinstance(record.get("objectRef"), dict) else {}
    result = record.get("result") if isinstance(record.get("result"), dict) else {}
    callback = record.get("callback") if isinstance(record.get("callback"), dict) else {}
    caller = str(record.get("caller") or "external")
    return operation_ledger_entry(
        ledger_id=operation_ledger_id("external", request_id),
        entry_type="external_gateway_request",
        source_id=request_id,
        title=f"外部自动化：{caller}",
        status=str(record.get("stage") or "unknown"),
        summary=str(result.get("message") or f"callback: {callback.get('status') or 'not_configured'}"),
        topicid=str(record.get("topicid") or ""),
        bookmd5=str(record.get("bookmd5") or ""),
        object_ref=object_ref,
        created_at=str(record.get("createdAt") or ""),
        updated_at=str(record.get("updatedAt") or record.get("createdAt") or ""),
        counts={
            "queued": int(result.get("queuedCount") or 0),
            "waitingConfirmation": int(result.get("waitingConfirmationCount") or 0),
            "callbackReceived": int(callback.get("receivedCount") or 0),
        },
    )


def manual_relation_operation_ledger_entry(event: dict[str, Any]) -> dict[str, Any]:
    from_object = event.get("fromObject") if isinstance(event.get("fromObject"), dict) else {}
    to_object = event.get("toObject") if isinstance(event.get("toObject"), dict) else {}
    from_title = str(from_object.get("title") or event.get("fromObjectId") or "")
    to_title = str(to_object.get("title") or event.get("toObjectId") or "")
    relation = str(event.get("relation") or "related_to")
    status = str(event.get("status") or "saved")
    object_ref = from_object if object_ref_has_identity(from_object) else {"objectId": str(event.get("fromObjectId") or "")}
    return operation_ledger_entry(
        ledger_id=operation_ledger_id("manualrel", str(event.get("eventId") or "")),
        entry_type="object_graph_manual_relation",
        source_id=str(event.get("eventId") or event.get("relationId") or ""),
        title=str(event.get("label") or f"{from_title} {relation} {to_title}" or "手工对象关系"),
        status=status,
        summary=f"{from_title} {relation} {to_title}".strip(),
        topicid=str(event.get("topicid") or ""),
        bookmd5=str(event.get("bookmd5") or ""),
        object_ref=object_ref,
        created_at=str(event.get("createdAt") or event.get("updatedAt") or ""),
        updated_at=str(event.get("updatedAt") or event.get("createdAt") or ""),
        counts={"manualRelations": 1},
    )


def manual_relation_events_for_object(payload: dict[str, Any], requested_object_id: str = "") -> list[dict[str, Any]]:
    requested_topic = normalize_topic_id(payload)
    requested_book = normalize_book_md5(payload)
    store = object_graph_relation_store()
    events = store.get("events") if isinstance(store.get("events"), list) else []
    out: list[dict[str, Any]] = []
    for item in events:
        if not isinstance(item, dict):
            continue
        if requested_topic and item.get("topicid") and item.get("topicid") != requested_topic:
            continue
        if requested_book and item.get("bookmd5") and item.get("bookmd5") != requested_book:
            continue
        if requested_object_id and item.get("fromObjectId") != requested_object_id and item.get("toObjectId") != requested_object_id:
            continue
        out.append(item)
    out.sort(key=lambda item: str(item.get("updatedAt") or item.get("createdAt") or ""), reverse=True)
    return out


def manual_relation_event_by_id(event_id: str) -> dict[str, Any]:
    store = object_graph_relation_store()
    for item in store.get("events") if isinstance(store.get("events"), list) else []:
        if isinstance(item, dict) and str(item.get("eventId") or "") == event_id:
            return item
    return {}


def operation_ledger_list(payload: dict[str, Any]) -> dict[str, Any]:
    requested_object_ref, requested_object_id = operation_ledger_object_filter(payload)
    limit = max(1, min(int(payload.get("limit") or 30), 120))
    entries: list[dict[str, Any]] = []
    object_ref = requested_object_ref

    if WORKFLOW_RUNS_DIR.exists():
        for path in sorted(WORKFLOW_RUNS_DIR.glob("*.json"), reverse=True):
            run = read_json_file(path, {})
            if not isinstance(run, dict) or not run:
                continue
            entry = workflow_operation_ledger_entry(run)
            entry_object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
            if not operation_ledger_matches(
                payload=payload,
                topicid=str(entry.get("topicid") or ""),
                bookmd5=str(entry.get("bookmd5") or ""),
                object_ref=entry_object_ref,
                requested_object_id=requested_object_id,
            ):
                continue
            object_ref = merge_object_ref(object_ref, entry_object_ref)
            entries.append(entry)

    transaction_candidates = transaction_manager.latest_summary(
        topicid=normalize_topic_id(payload),
        bookmd5=normalize_book_md5(payload),
        limit=200,
    )
    for summary in transaction_candidates.get("items") if isinstance(transaction_candidates.get("items"), list) else []:
        if not isinstance(summary, dict):
            continue
        entry = transaction_operation_ledger_entry(summary)
        entry_object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
        if not operation_ledger_matches(
            payload=payload,
            topicid=str(entry.get("topicid") or ""),
            bookmd5=str(entry.get("bookmd5") or ""),
            object_ref=entry_object_ref,
            requested_object_id=requested_object_id,
        ):
            continue
        object_ref = merge_object_ref(object_ref, entry_object_ref)
        entries.append(entry)

    if EXTERNAL_GATEWAY_DIR.exists():
        for path in sorted(EXTERNAL_GATEWAY_DIR.glob("*.json"), reverse=True):
            record = read_json_file(path, {})
            if not isinstance(record, dict) or not record:
                continue
            entry = external_gateway_operation_ledger_entry(record)
            entry_object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
            if not operation_ledger_matches(
                payload=payload,
                topicid=str(entry.get("topicid") or ""),
                bookmd5=str(entry.get("bookmd5") or ""),
                object_ref=entry_object_ref,
                requested_object_id=requested_object_id,
            ):
                continue
            object_ref = merge_object_ref(object_ref, entry_object_ref)
            entries.append(entry)

    for event in manual_relation_events_for_object(payload, requested_object_id):
        entry = manual_relation_operation_ledger_entry(event)
        entry_object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
        object_ref = merge_object_ref(object_ref, entry_object_ref)
        entries.append(entry)

    entries.sort(key=lambda item: str(item.get("updatedAt") or item.get("createdAt") or ""), reverse=True)
    filters = operation_ledger_filter_payload(payload)
    unfiltered_total = len(entries)
    filtered_entries = filter_operation_ledger_entries(entries, filters)
    entries = filtered_entries[:limit]
    type_counts: dict[str, int] = {}
    for item in entries:
        entry_type = str(item.get("entryType") or "unknown")
        type_counts[entry_type] = type_counts.get(entry_type, 0) + 1
    filtered_message = (
        f"已读取 Operation Ledger：{len(entries)} / {unfiltered_total} 条。"
        if filtered_entries != entries or any(filters.values())
        else f"已读取 Operation Ledger：{len(entries)} 条。"
    )
    return {
        "ok": True,
        "schema": "codex.mn.operationLedger.v1",
        "message": filtered_message,
        "objectRef": object_ref if object_ref_has_identity(object_ref) else {},
        "filters": filters,
        "counts": {
            "total": len(entries),
            "filteredTotal": len(filtered_entries),
            "unfilteredTotal": unfiltered_total,
            **type_counts,
        },
        "entries": entries,
    }


def transaction_operation_chain_evidence(record: dict[str, Any], verification: dict[str, Any]) -> dict[str, Any]:
    plan = record.get("mindmapDiffOperationPlan") if isinstance(record.get("mindmapDiffOperationPlan"), dict) else {}
    operation_manifest = record.get("operationManifest") if isinstance(record.get("operationManifest"), dict) else {}
    if not plan and isinstance(operation_manifest.get("operationPlan"), dict):
        plan = operation_manifest["operationPlan"]
    dry_run = operation_manifest.get("dryRun") if isinstance(operation_manifest.get("dryRun"), dict) else {}
    apply_boundary = plan.get("applyBoundary") if isinstance(plan.get("applyBoundary"), dict) else {}
    dry_run_status = str(dry_run.get("status") or apply_boundary.get("localApplyStatus") or "")
    mindmap_apply = record.get("mindmapDiffApply") if isinstance(record.get("mindmapDiffApply"), dict) else {}
    applied_operations = mindmap_apply.get("appliedOperations") if isinstance(mindmap_apply.get("appliedOperations"), list) else []
    mindmap_verification = mindmap_apply.get("verification") if isinstance(mindmap_apply.get("verification"), dict) else {}
    created_note_ids = transaction_manager.unique_strings(record.get("createdNoteIds"))
    applied_note_ids = transaction_manager.unique_strings(record.get("appliedNoteIds"))
    raw_events = record.get("events") if isinstance(record.get("events"), list) else []
    timeline: list[dict[str, Any]] = []
    for item in raw_events:
        if not isinstance(item, dict):
            continue
        timeline.append(
            {
                "event": str(item.get("event") or ""),
                "ts": str(item.get("ts") or ""),
                "nativeAction": str(item.get("nativeAction") or ""),
                "queueId": str(item.get("queueId") or ""),
                "source": str(item.get("source") or ""),
                "operationCount": int(item.get("operationCount") or 0),
            }
        )
    native_command_source = next(
        (
            item
            for item in timeline
            if item.get("nativeAction") or item.get("queueId") or item.get("event") == "mindmapDiffApplyRequested"
        ),
        {},
    )
    plan_operation_count = int(plan.get("operationCount") or len(plan.get("operations") if isinstance(plan.get("operations"), list) else []) or 0)
    return {
        "schema": "codex.mn.operationChainEvidence.v1",
        "transactionId": str(record.get("transactionId") or ""),
        "operationPlan": plan,
        "dryRun": {
            "schema": "codex.mn.operationChainDryRunEvidence.v1",
            "status": dry_run_status or "unknown",
            "dryRun": dry_run,
            "applyBoundary": apply_boundary,
        },
        "nativeCommand": {
            "schema": "codex.mn.nativeCommandEvidence.v1",
            "nativeAction": str(native_command_source.get("nativeAction") or ("apply_mindmap_diff_operations" if mindmap_apply else "")),
            "queueId": str(native_command_source.get("queueId") or ""),
            "source": str(native_command_source.get("source") or ""),
            "operationCount": int(native_command_source.get("operationCount") or plan_operation_count),
        },
        "nativeEventTimeline": timeline,
        "nativeApply": {
            "schema": "codex.mn.nativeApplyEvidence.v1",
            "nativeAction": "apply_mindmap_diff_operations" if mindmap_apply else "",
            "status": str(mindmap_verification.get("status") or record.get("status") or "unknown"),
            "appliedCount": int(record.get("appliedCount") or len(applied_operations) or 0),
            "failedCount": int(record.get("failedCount") or 0),
            "createdNoteIds": created_note_ids,
            "appliedNoteIds": applied_note_ids,
            "appliedOperations": applied_operations,
            "verification": mindmap_verification,
        },
        "rollback": {
            "schema": "codex.mn.rollbackEvidence.v1",
            "status": str(record.get("status") or ""),
            "deletedCount": int(record.get("deletedCount") or 0),
            "failedCount": int(record.get("failedCount") or 0),
            "rollbackComplete": bool(verification.get("rollbackComplete")),
            "requiresConfirmation": bool(verification.get("requiresConfirmation")),
            "accepted": bool(verification.get("accepted")),
            "availableActions": verification.get("availableActions") if isinstance(verification.get("availableActions"), list) else [],
            "failures": verification.get("failures") if isinstance(verification.get("failures"), list) else [],
            "undoRollback": verification.get("undoRollback") if isinstance(verification.get("undoRollback"), dict) else {},
        },
        "residual": {
            "schema": "codex.mn.residualObjectEvidence.v1",
            "remainingCount": int(verification.get("remainingCount") or 0),
            "remainingNoteIds": verification.get("remainingNoteIds") if isinstance(verification.get("remainingNoteIds"), list) else [],
            "createdNoteIds": created_note_ids,
            "targetNoteIds": verification.get("targetNoteIds") if isinstance(verification.get("targetNoteIds"), list) else [],
            "residualProof": verification.get("residualProof") if isinstance(verification.get("residualProof"), dict) else {},
        },
    }


def operation_ledger_get(payload: dict[str, Any]) -> dict[str, Any]:
    ledger_id = str(payload.get("ledgerId") or payload.get("id") or "").strip()
    if ":" not in ledger_id:
        return {"ok": False, "message": "读取 Operation Ledger 失败：缺少有效 ledgerId。"}
    prefix, source_id = ledger_id.split(":", 1)
    prefix = prefix.strip()
    source_id = source_id.strip()
    evidence: dict[str, Any] = {
        "schema": "codex.mn.operationLedgerEvidence.v1",
        "ledgerId": ledger_id,
        "entryType": "",
        "status": "unknown",
        "summary": "",
        "verification": {},
        "callback": {},
        "workflow": {},
    }
    if prefix == "workflow":
        loaded = load_workflow_run(source_id)
        if not loaded.get("ok"):
            return loaded
        record = loaded["workflowRun"]
        entry = workflow_operation_ledger_entry(record)
        summary = workflow_run_summary(record)
        waiting = [step for step in record.get("steps") if isinstance(step, dict) and step.get("status") == "waiting_confirmation"] if isinstance(record.get("steps"), list) else []
        blocked = [step for step in record.get("steps") if isinstance(step, dict) and step.get("status") in {"blocked", "failed"}] if isinstance(record.get("steps"), list) else []
        evidence.update(
            {
                "entryType": "workflow_run",
                "status": str(summary.get("status") or "unknown"),
                "summary": (
                    f"workflow {summary.get('workflowId') or ''}: "
                    f"queued={summary.get('queuedCount') or 0}, "
                    f"waiting={summary.get('waitingConfirmationCount') or 0}, "
                    f"blocked={len(blocked)}"
                ),
                "workflow": {
                    "schema": "codex.mn.workflowRunEvidence.v1",
                    "workflowRunId": str(summary.get("id") or ""),
                    "workflowId": str(summary.get("workflowId") or ""),
                    "status": str(summary.get("status") or ""),
                    "queuedCount": int(summary.get("queuedCount") or 0),
                    "waitingConfirmationCount": int(summary.get("waitingConfirmationCount") or 0),
                    "blockedCount": len(blocked),
                    "waitingStepIds": [str(step.get("id") or step.get("action") or "") for step in waiting],
                    "blockedStepIds": [str(step.get("id") or step.get("action") or "") for step in blocked],
                },
            }
        )
    elif prefix == "transaction":
        record = transaction_manager.load_transaction(source_id)
        if not record:
            return {"ok": False, "message": "读取 Operation Ledger 失败：事务不存在。", "ledgerId": ledger_id}
        verification = transaction_manager.verification_report(record)
        entry = transaction_operation_ledger_entry(transaction_manager.transaction_summary(record))
        evidence.update(
            {
                "entryType": "ai_edit_transaction",
                "status": str(verification.get("status") or "unknown"),
                "summary": str(verification.get("summary") or ""),
                "verification": verification,
                "operationChain": transaction_operation_chain_evidence(record, verification),
            }
        )
    elif prefix == "external":
        record = read_json_file(external_gateway_request_path(source_id), {})
        if not isinstance(record, dict) or not record:
            return {"ok": False, "message": "读取 Operation Ledger 失败：外部请求不存在。", "ledgerId": ledger_id}
        entry = external_gateway_operation_ledger_entry(record)
        callback = record.get("callback") if isinstance(record.get("callback"), dict) else {}
        result = record.get("result") if isinstance(record.get("result"), dict) else {}
        evidence.update(
            {
                "entryType": "external_gateway_request",
                "status": str(record.get("stage") or callback.get("status") or "unknown"),
                "summary": str(result.get("message") or f"callback: {callback.get('status') or 'not_configured'}"),
                "callback": {
                    "schema": "codex.mn.externalCallbackEvidence.v1",
                    "status": str(callback.get("status") or "not_configured"),
                    "receivedCount": int(callback.get("receivedCount") or 0),
                    "receivedAt": str(callback.get("receivedAt") or ""),
                    "message": str(callback.get("message") or ""),
                    "payload": callback.get("payload") if isinstance(callback.get("payload"), dict) else {},
                    "history": callback.get("history") if isinstance(callback.get("history"), list) else [],
                },
            }
        )
    elif prefix == "manualrel":
        record = manual_relation_event_by_id(source_id)
        if not record:
            return {"ok": False, "message": "读取 Operation Ledger 失败：手工对象关系事件不存在。", "ledgerId": ledger_id}
        entry = manual_relation_operation_ledger_entry(record)
        evidence.update(
            {
                "entryType": "object_graph_manual_relation",
                "status": str(record.get("status") or "unknown"),
                "summary": str(entry.get("summary") or ""),
                "manualRelation": {
                    "schema": "codex.mn.objectGraphManualRelationEvidence.v1",
                    "eventId": str(record.get("eventId") or ""),
                    "relationId": str(record.get("relationId") or ""),
                    "status": str(record.get("status") or ""),
                    "topicid": str(record.get("topicid") or ""),
                    "bookmd5": str(record.get("bookmd5") or ""),
                    "fromObjectId": str(record.get("fromObjectId") or ""),
                    "toObjectId": str(record.get("toObjectId") or ""),
                    "fromObject": record.get("fromObject") if isinstance(record.get("fromObject"), dict) else {},
                    "toObject": record.get("toObject") if isinstance(record.get("toObject"), dict) else {},
                    "relation": str(record.get("relation") or "related_to"),
                    "label": str(record.get("label") or ""),
                    "note": str(record.get("note") or ""),
                    "evidenceType": "manual_relation",
                    "createdAt": str(record.get("createdAt") or ""),
                    "updatedAt": str(record.get("updatedAt") or ""),
                },
            }
        )
    else:
        return {"ok": False, "message": f"读取 Operation Ledger 失败：未知 ledger 类型 {prefix}。", "ledgerId": ledger_id}
    return {
        "ok": True,
        "schema": "codex.mn.operationLedgerEntryDetail.v1",
        "message": "已读取 Operation Ledger 详情。",
        "entry": entry,
        "record": record,
        "evidence": evidence,
    }


def object_graph_action(label: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "codex.mn.objectGraphAction.v1",
        "label": label,
        "action": action,
        "payload": payload if isinstance(payload, dict) else {},
    }


def object_graph_action_from_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    descriptor = descriptor if isinstance(descriptor, dict) else {}
    return object_graph_action(
        str(descriptor.get("label") or "打开"),
        str(descriptor.get("action") or ""),
        descriptor.get("payload") if isinstance(descriptor.get("payload"), dict) else {},
    )


def object_graph_node(
    *,
    node_id: str,
    node_type: str,
    title: str,
    status: str = "",
    summary: str = "",
    object_ref: dict[str, Any] | None = None,
    source_id: str = "",
    updated_at: str = "",
    graph_action: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    object_ref = object_ref if isinstance(object_ref, dict) else {}
    node: dict[str, Any] = {
        "schema": "codex.mn.objectGraphNode.v1",
        "nodeId": node_id,
        "nodeType": node_type,
        "title": title,
        "status": status,
        "summary": summary,
        "sourceId": source_id,
        "updatedAt": updated_at,
        "objectRef": object_ref if object_ref_has_identity(object_ref) else {},
    }
    if graph_action and graph_action.get("action"):
        node["graphAction"] = graph_action
    if isinstance(extra, dict):
        for key, value in extra.items():
            if key not in node:
                node[key] = value
    return node


def object_graph_edge(
    from_id: str,
    to_id: str,
    relation: str,
    evidence_type: str,
    source_id: str = "",
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    edge = {
        "schema": "codex.mn.objectGraphEdge.v1",
        "edgeId": operation_ledger_id("edge", f"{from_id}:{relation}:{to_id}") or f"{from_id}:{relation}:{to_id}",
        "from": from_id,
        "to": to_id,
        "relation": relation,
        "evidenceType": evidence_type,
        "sourceId": source_id,
    }
    if isinstance(extra, dict):
        for key, value in extra.items():
            if key not in edge:
                edge[key] = value
    return edge


def object_graph_add_node(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    root_id: str,
    node: dict[str, Any],
    relation: str,
    evidence_type: str,
) -> None:
    node_id = str(node.get("nodeId") or "")
    if not node_id or node_id == root_id:
        return
    if node_id not in nodes:
        nodes[node_id] = node
        edges.append(object_graph_edge(root_id, node_id, relation, evidence_type, str(node.get("sourceId") or "")))


def object_graph_relation_store() -> dict[str, Any]:
    store = read_json_file(OBJECT_GRAPH_RELATIONS_PATH, {})
    if not isinstance(store, dict):
        store = {}
    relations = store.get("relations") if isinstance(store.get("relations"), list) else []
    events = store.get("events") if isinstance(store.get("events"), list) else []
    return {"schema": "codex.mn.objectGraphManualRelations.v1", "relations": relations, "events": events}


def write_object_graph_relation_store(relations: list[dict[str, Any]], events: list[dict[str, Any]] | None = None) -> None:
    clean_relations = [item for item in relations if isinstance(item, dict) and item.get("relationId")]
    clean_events = [item for item in (events or []) if isinstance(item, dict) and item.get("eventId")]
    write_json_file(
        OBJECT_GRAPH_RELATIONS_PATH,
        {
            "schema": "codex.mn.objectGraphManualRelations.v1",
            "updatedAt": diagnostic_timestamp(),
            "relations": clean_relations,
            "events": clean_events[-500:],
        },
    )


def clean_object_graph_object_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    source_ref = value.get("sourceRef") if isinstance(value.get("sourceRef"), dict) else {}
    return {
        "objectId": str(value.get("objectId") or "")[:240],
        "kind": str(value.get("kind") or "")[:80],
        "title": str(value.get("title") or value.get("objectId") or "")[:240],
        "sourceRef": transaction_manager.clean_source_ref(source_ref),
    }


def mn_object_registry_store() -> dict[str, Any]:
    store = read_json_file(MN_OBJECT_REGISTRY_PATH, {})
    if not isinstance(store, dict):
        store = {}
    objects = store.get("objects") if isinstance(store.get("objects"), list) else []
    clean_objects = [
        item
        for item in objects
        if isinstance(item, dict)
        and isinstance(item.get("objectRef"), dict)
        and str(item["objectRef"].get("objectId") or "")
    ]
    return {
        "schema": "codex.mn.mnObjectRegistry.v1",
        "updatedAt": str(store.get("updatedAt") or ""),
        "objects": clean_objects,
    }


def write_mn_object_registry_store(objects: list[dict[str, Any]]) -> None:
    clean_objects = [
        item
        for item in objects
        if isinstance(item, dict)
        and isinstance(item.get("objectRef"), dict)
        and str(item["objectRef"].get("objectId") or "")
    ]
    write_json_file(
        MN_OBJECT_REGISTRY_PATH,
        {
            "schema": "codex.mn.mnObjectRegistry.v1",
            "updatedAt": diagnostic_timestamp(),
            "objects": clean_objects[-2000:],
        },
    )


def register_mn_objects(
    object_refs: list[dict[str, Any]],
    payload: dict[str, Any],
    evidence_type: str,
    source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    now = diagnostic_timestamp()
    store = mn_object_registry_store()
    entries = store.get("objects") if isinstance(store.get("objects"), list) else []
    by_id: dict[str, dict[str, Any]] = {
        str(item.get("objectRef", {}).get("objectId") or ""): item
        for item in entries
        if isinstance(item, dict) and isinstance(item.get("objectRef"), dict)
    }
    changed = 0
    for raw_ref in object_refs:
        clean_ref = clean_object_graph_object_ref(raw_ref)
        object_id = str(clean_ref.get("objectId") or "").strip()
        if not object_id:
            continue
        previous = by_id.get(object_id) if isinstance(by_id.get(object_id), dict) else {}
        previous_ref = previous.get("objectRef") if isinstance(previous.get("objectRef"), dict) else {}
        merged_ref = merge_object_ref(clean_ref, previous_ref)
        evidence_types = [
            str(item)
            for item in previous.get("evidenceTypes", [])
            if isinstance(previous.get("evidenceTypes"), list) and str(item)
        ]
        if evidence_type and evidence_type not in evidence_types:
            evidence_types.append(evidence_type)
        entry = {
            "schema": "codex.mn.mnObjectRegistryEntry.v1",
            "objectRef": merged_ref,
            "objectId": object_id,
            "kind": str(merged_ref.get("kind") or ""),
            "title": str(merged_ref.get("title") or object_id),
            "sourceRef": merged_ref.get("sourceRef") if isinstance(merged_ref.get("sourceRef"), dict) else {},
            "topicid": topic_id or str(previous.get("topicid") or ""),
            "bookmd5": book_md5 or str(previous.get("bookmd5") or ""),
            "firstSeenAt": str(previous.get("firstSeenAt") or now),
            "lastSeenAt": now,
            "seenCount": int(previous.get("seenCount") or 0) + 1,
            "evidenceTypes": sorted(set(evidence_types)),
            "source": source if isinstance(source, dict) else {},
        }
        by_id[object_id] = entry
        changed += 1
    if changed:
        ordered = sorted(by_id.values(), key=lambda item: str(item.get("lastSeenAt") or ""), reverse=True)
        write_mn_object_registry_store(ordered)
    return {"ok": True, "schema": "codex.mn.mnObjectRegistry.v1", "registered": changed}


def mn_object_registry(payload: dict[str, Any]) -> dict[str, Any]:
    requested_topic = normalize_topic_id(payload)
    requested_book = normalize_book_md5(payload)
    limit = max(1, min(int(payload.get("limit") or 80), 500))
    store = mn_object_registry_store()
    objects: list[dict[str, Any]] = []
    for item in store.get("objects") if isinstance(store.get("objects"), list) else []:
        if not isinstance(item, dict):
            continue
        if requested_topic and item.get("topicid") and item.get("topicid") != requested_topic:
            continue
        if requested_book and item.get("bookmd5") and item.get("bookmd5") != requested_book:
            continue
        objects.append(item)
    objects.sort(key=lambda item: str(item.get("lastSeenAt") or item.get("firstSeenAt") or ""), reverse=True)
    type_counts: dict[str, int] = {}
    for item in objects:
        kind = str(item.get("kind") or item.get("objectRef", {}).get("kind") or "unknown")
        type_counts[kind] = type_counts.get(kind, 0) + 1
    return {
        "ok": True,
        "schema": "codex.mn.mnObjectRegistry.v1",
        "message": f"已读取 MNObject Registry：{len(objects[:limit])} / {len(objects)} 个对象。",
        "objects": objects[:limit],
        "counts": {"total": len(objects), "returned": len(objects[:limit]), "kinds": type_counts},
        "updatedAt": str(store.get("updatedAt") or ""),
    }


def clean_object_graph_relation_type(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9_:-]", "_", str(value or "").strip().lower())[:64]
    return text or "related_to"


def object_graph_relation_id(from_object_id: str, relation: str, to_object_id: str, topicid: str, bookmd5: str) -> str:
    raw = f"{topicid}|{bookmd5}|{from_object_id}|{relation}|{to_object_id}"
    return operation_ledger_id("manualrel", hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24])


def object_graph_relation_event(relation: dict[str, Any], status: str, event_id: str = "") -> dict[str, Any]:
    now = diagnostic_timestamp()
    relation_id = str(relation.get("relationId") or "")
    event_seed = event_id or hashlib.sha256(f"{relation_id}|{status}|{now}|{uuid.uuid4()}".encode("utf-8")).hexdigest()[:24]
    return {
        "schema": "codex.mn.objectGraphManualRelationEvent.v1",
        "eventId": event_seed,
        "relationId": relation_id,
        "status": str(status or "saved"),
        "topicid": str(relation.get("topicid") or ""),
        "bookmd5": str(relation.get("bookmd5") or ""),
        "fromObjectId": str(relation.get("fromObjectId") or ""),
        "toObjectId": str(relation.get("toObjectId") or ""),
        "fromObject": relation.get("fromObject") if isinstance(relation.get("fromObject"), dict) else {},
        "toObject": relation.get("toObject") if isinstance(relation.get("toObject"), dict) else {},
        "relation": str(relation.get("relation") or "related_to"),
        "label": str(relation.get("label") or ""),
        "note": str(relation.get("note") or ""),
        "evidenceType": "manual_relation",
        "createdAt": now,
        "updatedAt": now,
    }


def object_graph_relation_save(payload: dict[str, Any]) -> dict[str, Any]:
    source_ref, source_id = operation_ledger_object_filter(payload)
    target_ref = clean_object_graph_object_ref(payload.get("targetObject") or payload.get("toObject") or {})
    target_id = str(payload.get("targetObjectId") or payload.get("toObjectId") or target_ref.get("objectId") or "").strip()
    if target_id and not target_ref.get("objectId"):
        target_ref = {"objectId": target_id, "kind": "", "title": target_id, "sourceRef": {}}
    if not source_id:
        return {"ok": False, "message": "保存对象关系失败：缺少来源 MNObject。"}
    if not target_id:
        return {"ok": False, "message": "保存对象关系失败：缺少目标 MNObject。"}
    if source_id == target_id:
        return {"ok": False, "message": "保存对象关系失败：不能把对象关联到自身。"}
    if not source_ref.get("objectId"):
        source_ref = merge_object_ref({"objectId": source_id}, source_ref)
    if not target_ref.get("objectId"):
        target_ref = merge_object_ref({"objectId": target_id}, target_ref)
    relation_type = clean_object_graph_relation_type(payload.get("relation") or payload.get("relationType"))
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    relation_id = object_graph_relation_id(source_id, relation_type, target_id, topic_id, book_md5)
    now = diagnostic_timestamp()
    store = object_graph_relation_store()
    relations = store.get("relations") if isinstance(store.get("relations"), list) else []
    events = store.get("events") if isinstance(store.get("events"), list) else []
    existing_by_id = {str(item.get("relationId") or ""): item for item in relations if isinstance(item, dict)}
    previous = existing_by_id.get(relation_id) if isinstance(existing_by_id.get(relation_id), dict) else {}
    relation = {
        "schema": "codex.mn.objectGraphManualRelation.v1",
        "relationId": relation_id,
        "topicid": topic_id,
        "bookmd5": book_md5,
        "fromObjectId": source_id,
        "toObjectId": target_id,
        "fromObject": source_ref,
        "toObject": target_ref,
        "relation": relation_type,
        "label": str(payload.get("label") or payload.get("relationLabel") or relation_type)[:160],
        "note": str(payload.get("note") or payload.get("comment") or "")[:1200],
        "evidenceType": "manual_relation",
        "createdAt": str(previous.get("createdAt") or now),
        "updatedAt": now,
    }
    updated = [item for item in relations if isinstance(item, dict) and item.get("relationId") != relation_id]
    updated.append(relation)
    event = object_graph_relation_event(relation, "saved")
    write_object_graph_relation_store(updated, [*events, event])
    register_mn_objects(
        [source_ref, target_ref],
        payload,
        "manual_relation",
        source={"relationId": relation_id, "eventId": str(event.get("eventId") or "")},
    )
    append_diagnostic_log(
        "info",
        "objectGraphManualRelationSaved",
        f"{source_id} {relation_type} {target_id}",
        extra={
            "requestId": relation_id,
            "topicid": topic_id,
            "bookmd5": book_md5,
            "targetObjectRef": target_ref,
        },
        object_ref=source_ref,
        request_id=relation_id,
    )
    return {
        "ok": True,
        "schema": "codex.mn.objectGraphManualRelation.v1",
        "message": "已保存对象图谱关系。",
        "relation": relation,
        "event": event,
    }


def object_graph_relation_delete(payload: dict[str, Any]) -> dict[str, Any]:
    relation_id = str(payload.get("relationId") or payload.get("id") or "").strip()
    if not relation_id:
        return {"ok": False, "message": "删除对象关系失败：缺少 relationId。"}
    store = object_graph_relation_store()
    relations = store.get("relations") if isinstance(store.get("relations"), list) else []
    events = store.get("events") if isinstance(store.get("events"), list) else []
    removed_relation = next((item for item in relations if isinstance(item, dict) and item.get("relationId") == relation_id), None)
    remaining = [item for item in relations if not isinstance(item, dict) or item.get("relationId") != relation_id]
    removed = len(relations) - len(remaining)
    event = object_graph_relation_event(removed_relation, "deleted") if isinstance(removed_relation, dict) else {}
    write_object_graph_relation_store(remaining, [*events, event] if event else events)
    if removed:
        append_diagnostic_log(
            "info",
            "objectGraphManualRelationDeleted",
            relation_id,
            request_id=relation_id,
        )
    return {
        "ok": True,
        "schema": "codex.mn.objectGraphManualRelationDelete.v1",
        "message": "已删除对象图谱关系。" if removed else "对象图谱关系已不存在。",
        "relationId": relation_id,
        "removed": removed,
        "event": event,
    }


def object_graph_manual_relation_node_id(object_id: str) -> str:
    return str(object_id or "")


def object_graph_manual_relations_for_object(root_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    store = object_graph_relation_store()
    relations = store.get("relations") if isinstance(store.get("relations"), list) else []
    out: list[dict[str, Any]] = []
    for item in relations:
        if not isinstance(item, dict):
            continue
        if topic_id and item.get("topicid") and item.get("topicid") != topic_id:
            continue
        if book_md5 and item.get("bookmd5") and item.get("bookmd5") != book_md5:
            continue
        if item.get("fromObjectId") == root_id or item.get("toObjectId") == root_id:
            out.append(item)
    return out


def object_graph_add_manual_relations(
    nodes: dict[str, dict[str, Any]],
    edges: list[dict[str, Any]],
    root_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    relations = object_graph_manual_relations_for_object(root_id, payload)
    added_edges = 0
    for relation in relations:
        from_object = clean_object_graph_object_ref(relation.get("fromObject") if isinstance(relation.get("fromObject"), dict) else {})
        to_object = clean_object_graph_object_ref(relation.get("toObject") if isinstance(relation.get("toObject"), dict) else {})
        from_id = str(relation.get("fromObjectId") or from_object.get("objectId") or "")
        to_id = str(relation.get("toObjectId") or to_object.get("objectId") or "")
        if not from_id or not to_id:
            continue
        for object_id, object_ref in [(from_id, from_object), (to_id, to_object)]:
            if object_id == root_id:
                continue
            node_id = object_graph_manual_relation_node_id(object_id)
            if node_id not in nodes:
                title = str(object_ref.get("title") or object_id)
                nodes[node_id] = object_graph_node(
                    node_id=node_id,
                    node_type="manual_mn_object",
                    title=title,
                    status=str(object_ref.get("kind") or "manual"),
                    summary="手工维护的对象关系",
                    object_ref=object_ref if object_ref_has_identity(object_ref) else {"objectId": object_id},
                    source_id=object_id,
                    updated_at=str(relation.get("updatedAt") or ""),
                    graph_action=object_graph_action(
                        "删除关系",
                        "object_graph_relation_delete",
                        {"relationId": str(relation.get("relationId") or "")},
                    ),
                    extra={
                        "relationId": str(relation.get("relationId") or ""),
                        "relationLabel": str(relation.get("label") or ""),
                    },
                )
        edge_from = root_id if from_id == root_id else object_graph_manual_relation_node_id(from_id)
        edge_to = root_id if to_id == root_id else object_graph_manual_relation_node_id(to_id)
        if edge_from == edge_to:
            continue
        edge = object_graph_edge(
            edge_from,
            edge_to,
            str(relation.get("relation") or "related_to"),
            "manual_relation",
            str(relation.get("relationId") or ""),
            {
                "relationId": str(relation.get("relationId") or ""),
                "label": str(relation.get("label") or ""),
                "note": str(relation.get("note") or ""),
                "editable": True,
                "updatedAt": str(relation.get("updatedAt") or ""),
            },
        )
        edges.append(edge)
        added_edges += 1
    return {
        "schema": "codex.mn.objectGraphManualRelations.v1",
        "count": len(relations),
        "edgeCount": added_edges,
        "relations": relations,
    }


def object_graph_knowledge_query(object_ref: dict[str, Any]) -> str:
    source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
    parts = [
        str(object_ref.get("title") or ""),
        str(object_ref.get("kind") or ""),
        str(source_ref.get("quote") or ""),
        str(source_ref.get("documentTitle") or ""),
        str(source_ref.get("path") or ""),
    ]
    return " ".join(part.strip() for part in parts if part and part.strip())[:1200]


def object_graph_knowledge_node_id(match: dict[str, Any]) -> str:
    source_id = str(match.get("noteId") or match.get("id") or match.get("title") or "")
    return operation_ledger_id("knowledge", source_id)


def object_graph_knowledge_node(match: dict[str, Any], object_ref: dict[str, Any]) -> dict[str, Any]:
    note_id = str(match.get("noteId") or "")
    title = str(match.get("title") or note_id or "知识实体")
    query = note_id or title
    return object_graph_node(
        node_id=object_graph_knowledge_node_id(match),
        node_type="knowledge_entity",
        title=title,
        status=str(match.get("entityType") or match.get("kind") or ""),
        summary=str(match.get("snippet") or ""),
        object_ref=object_ref,
        source_id=note_id or str(match.get("id") or ""),
        updated_at=str(match.get("ts") or ""),
        graph_action=object_graph_action(
            "检索知识",
            "knowledge_index_search",
            {"query": query, "limit": 8},
        ),
        extra={
            "knowledgeId": str(match.get("id") or ""),
            "entityType": str(match.get("entityType") or match.get("kind") or ""),
            "noteId": note_id,
            "sourceRef": match.get("sourceRef") if isinstance(match.get("sourceRef"), dict) else {},
            "relations": match.get("relations") if isinstance(match.get("relations"), list) else [],
            "score": int(match.get("score") or 0),
        },
    )


def object_graph_collect_knowledge_matches(
    payload: dict[str, Any],
    object_ref: dict[str, Any],
    limit: int,
) -> list[dict[str, Any]]:
    query = object_graph_knowledge_query(object_ref)
    if not query:
        return []
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    result = knowledge_index.search(query, topicid=topic_id, bookmd5=book_md5, limit=limit)
    raw_matches = result.get("matches") if isinstance(result.get("matches"), list) else []
    by_key: dict[str, dict[str, Any]] = {}
    queue: list[dict[str, Any]] = []
    for item in raw_matches:
        if not isinstance(item, dict):
            continue
        key = str(item.get("noteId") or item.get("id") or item.get("title") or "")
        if key and key not in by_key:
            by_key[key] = item
            queue.append(item)
    for item in list(queue):
        relations = item.get("relations") if isinstance(item.get("relations"), list) else []
        for relation in relations[:12]:
            if not isinstance(relation, dict):
                continue
            target = str(relation.get("targetNoteId") or relation.get("targetId") or "").strip()
            if not target or target in by_key:
                continue
            related = knowledge_index.search(target, topicid=topic_id, bookmd5=book_md5, limit=1)
            related_matches = related.get("matches") if isinstance(related.get("matches"), list) else []
            if related_matches and isinstance(related_matches[0], dict):
                by_key[target] = related_matches[0]
                queue.append(related_matches[0])
            if len(queue) >= limit:
                break
        if len(queue) >= limit:
            break
    return queue[:limit]


def object_graph_mn_note_node_id(note_id: str) -> str:
    return operation_ledger_id("mnnote", note_id)


def object_graph_flatten_mindmap_tree(tree: dict[str, Any], max_nodes: int = 160) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []

    def walk(node: Any, parent_note_id: str, depth: int, path: str) -> None:
        if len(out) >= max_nodes or not isinstance(node, dict):
            return
        children = node.get("children") if isinstance(node.get("children"), list) else []
        note_id = str(node.get("noteId") or node.get("id") or "").strip()
        title = str(node.get("title") or node.get("name") or note_id or "未命名节点")
        out.append(
            {
                "noteId": note_id,
                "title": title,
                "body": str(node.get("body") or node.get("text") or "")[:1200],
                "parentNoteId": parent_note_id,
                "depth": depth,
                "path": path,
                "childCount": len(children),
            }
        )
        for index, child in enumerate(children):
            if len(out) >= max_nodes:
                break
            child_path = f"{path}.{index + 1}" if path else str(index + 1)
            walk(child, note_id, depth + 1, child_path)

    walk(tree, "", 0, "1")
    return out


def mindmap_tree_item_object_ref(item: dict[str, Any], cache: dict[str, Any]) -> dict[str, Any]:
    note_id = str(item.get("noteId") or "").strip()
    title = str(item.get("title") or note_id or "MN 节点")
    return {
        "objectId": f"mnobj:note:{note_id}" if note_id else "",
        "kind": "mindmap_node",
        "title": title[:240],
        "sourceRef": {
            "noteId": note_id,
            "parentNoteId": str(item.get("parentNoteId") or ""),
            "nodePath": str(item.get("path") or ""),
            "documentTitle": str(cache.get("rootTitle") or cache.get("selectedNoteTitle") or ""),
        },
    }


def mindmap_tree_cache_object_refs(cache: dict[str, Any], max_nodes: int = 500) -> list[dict[str, Any]]:
    tree = cache.get("currentMindmap") if isinstance(cache.get("currentMindmap"), dict) else {}
    if not tree:
        return []
    refs: list[dict[str, Any]] = []
    for item in object_graph_flatten_mindmap_tree(tree, max_nodes=max_nodes):
        if not isinstance(item, dict) or not item.get("noteId"):
            continue
        refs.append(mindmap_tree_item_object_ref(item, cache))
    return refs


def register_mindmap_tree_cache_objects(payload: dict[str, Any], cache: dict[str, Any] | None = None) -> dict[str, Any]:
    cache = cache if isinstance(cache, dict) else read_latest_mindmap_tree(normalize_topic_id(payload), normalize_book_md5(payload))
    refs = mindmap_tree_cache_object_refs(cache if isinstance(cache, dict) else {})
    if not refs:
        return {"ok": True, "schema": "codex.mn.mnObjectRegistry.v1", "registered": 0}
    return register_mn_objects(
        refs,
        payload,
        "mindmap_tree_cache",
        source={
            "sourceEvent": str(cache.get("sourceEvent") or "mindmapTreeReadFinished"),
            "updatedAt": str(cache.get("updatedAt") or ""),
            "nodeCount": len(refs),
        },
    )


def native_scan_object_ref(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    source_ref = value.get("sourceRef") if isinstance(value.get("sourceRef"), dict) else {}
    note_id = str(source_ref.get("noteId") or value.get("noteId") or value.get("id") or "").strip()
    raw_object_id = str(value.get("objectId") or value.get("mnObjectId") or "").strip()
    object_id = raw_object_id or (f"mnobj:note:{note_id}" if note_id else "")
    kind = str(value.get("kind") or value.get("objectKind") or ("mindmap_node" if note_id else "mn_object"))[:80]
    title = str(value.get("title") or value.get("noteTitle") or value.get("name") or object_id)[:240]
    merged_source_ref = {
        **source_ref,
        "noteId": str(source_ref.get("noteId") or note_id),
        "parentNoteId": str(source_ref.get("parentNoteId") or value.get("parentNoteId") or ""),
        "nodePath": str(source_ref.get("nodePath") or value.get("nodePath") or value.get("path") or ""),
        "documentTitle": str(source_ref.get("documentTitle") or value.get("documentTitle") or ""),
    }
    return {
        "objectId": object_id,
        "kind": kind,
        "title": title,
        "sourceRef": merged_source_ref,
    }


def register_native_object_scan_event(record: dict[str, Any]) -> dict[str, Any]:
    extra = record.get("extra") if isinstance(record.get("extra"), dict) else {}
    raw_objects = extra.get("objects") if isinstance(extra.get("objects"), list) else extra.get("mnObjects")
    if not isinstance(raw_objects, list):
        raw_objects = []
    refs = [native_scan_object_ref(item) for item in raw_objects]
    refs = [item for item in refs if isinstance(item, dict) and item.get("objectId")]
    if not refs:
        return {"ok": True, "schema": "codex.mn.mnObjectRegistry.v1", "registered": 0}
    return register_mn_objects(
        refs,
        {"topicid": str(record.get("topicid") or ""), "bookmd5": str(record.get("bookmd5") or "")},
        "native_object_scan",
        source={
            "sourceEvent": str(record.get("event") or "mnObjectRegistryScanFinished"),
            "scanId": str(extra.get("scanId") or ""),
            "objectCount": len(refs),
            "truncatedCount": int(extra.get("truncatedCount") or 0),
        },
    )


def object_graph_mn_note_node(item: dict[str, Any], object_ref: dict[str, Any], cache: dict[str, Any]) -> dict[str, Any]:
    note_id = str(item.get("noteId") or "")
    title = str(item.get("title") or note_id or "MN 节点")
    note_ref = mindmap_tree_item_object_ref(item, {**cache, "rootTitle": str(cache.get("rootTitle") or object_ref.get("title") or "")})
    source_ref = note_ref.get("sourceRef") if isinstance(note_ref.get("sourceRef"), dict) else {}
    return object_graph_node(
        node_id=object_graph_mn_note_node_id(note_id),
        node_type="mn_note",
        title=title,
        status=f"depth {int(item.get('depth') or 0)}",
        summary=str(item.get("body") or ""),
        object_ref=note_ref,
        source_id=note_id,
        updated_at=str(cache.get("updatedAt") or ""),
        graph_action=object_graph_action(
            "读取子树",
            "mn_read_tree",
            {"selectedNoteId": note_id, "selectedNoteTitle": title},
        ),
        extra={
            "noteId": note_id,
            "parentNoteId": str(item.get("parentNoteId") or ""),
            "depth": int(item.get("depth") or 0),
            "path": str(item.get("path") or ""),
            "childCount": int(item.get("childCount") or 0),
            "sourceRef": source_ref,
        },
    )


def object_graph_note_id_from_object_id(object_id: str) -> str:
    object_id = str(object_id or "")
    if object_id.startswith("mnobj:note:"):
        return object_id.split("mnobj:note:", 1)[1].strip()
    return ""


def object_graph_registry_scan_items(payload: dict[str, Any], max_nodes: int = 160) -> list[dict[str, Any]]:
    registry = mn_object_registry({**payload, "limit": max_nodes})
    objects = registry.get("objects") if isinstance(registry.get("objects"), list) else []
    items: list[dict[str, Any]] = []
    for entry in objects:
        if not isinstance(entry, dict):
            continue
        evidence_types = [str(item) for item in entry.get("evidenceTypes", []) if isinstance(entry.get("evidenceTypes"), list) and str(item)]
        if "native_object_scan" not in evidence_types:
            continue
        object_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
        source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
        note_id = str(source_ref.get("noteId") or object_graph_note_id_from_object_id(str(object_ref.get("objectId") or ""))).strip()
        if not note_id:
            continue
        node_path = str(source_ref.get("nodePath") or "")
        depth = max(0, len([part for part in node_path.split(".") if part]) - 1) if node_path else 0
        items.append(
            {
                "noteId": note_id,
                "title": str(object_ref.get("title") or entry.get("title") or note_id),
                "body": str(entry.get("summary") or ""),
                "parentNoteId": str(source_ref.get("parentNoteId") or ""),
                "depth": depth,
                "path": node_path,
                "childCount": 0,
                "objectRef": object_ref,
                "sourceRef": source_ref,
                "updatedAt": str(entry.get("lastSeenAt") or entry.get("firstSeenAt") or ""),
                "evidenceTypes": sorted(set(evidence_types)),
            }
        )
    items.sort(key=lambda item: (str(item.get("path") or "zzzz"), str(item.get("noteId") or "")))
    return items[:max_nodes]


def object_graph_registry_scan_node(item: dict[str, Any]) -> dict[str, Any]:
    note_id = str(item.get("noteId") or "")
    object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
    source_ref = item.get("sourceRef") if isinstance(item.get("sourceRef"), dict) else {}
    return object_graph_node(
        node_id=object_graph_mn_note_node_id(note_id),
        node_type="mn_note",
        title=str(item.get("title") or note_id or "MN 节点"),
        status=f"scan depth {int(item.get('depth') or 0)}",
        summary=str(item.get("body") or ""),
        object_ref=object_ref,
        source_id=note_id,
        updated_at=str(item.get("updatedAt") or ""),
        graph_action=object_graph_action(
            "读取子树",
            "mn_read_tree",
            {"selectedNoteId": note_id, "selectedNoteTitle": str(item.get("title") or note_id)},
        ),
        extra={
            "noteId": note_id,
            "parentNoteId": str(item.get("parentNoteId") or ""),
            "depth": int(item.get("depth") or 0),
            "path": str(item.get("path") or ""),
            "childCount": int(item.get("childCount") or 0),
            "sourceRef": source_ref,
            "evidenceTypes": item.get("evidenceTypes") if isinstance(item.get("evidenceTypes"), list) else [],
        },
    )


def object_graph(payload: dict[str, Any]) -> dict[str, Any]:
    requested_object_ref, requested_object_id = operation_ledger_object_filter(payload)
    if not requested_object_id:
        return {
            "ok": False,
            "message": "对象图谱读取失败：缺少当前 MNObject。请先刷新 Agent 计划或选择一个 MarginNote 对象。",
            "schema": "codex.mn.objectGraph.v1",
            "root": {},
            "nodes": [],
            "edges": [],
            "counts": {"nodes": 0, "edges": 0},
        }

    limit = max(1, min(int(payload.get("limit") or 8), 30))
    activity = object_activity({**payload, "mnObjectId": requested_object_id, "limit": limit})
    ledger = operation_ledger_list({**payload, "mnObjectId": requested_object_id, "limit": limit})
    object_ref = merge_object_ref(requested_object_ref, activity.get("objectRef") if isinstance(activity.get("objectRef"), dict) else {})
    object_ref = merge_object_ref(object_ref, ledger.get("objectRef") if isinstance(ledger.get("objectRef"), dict) else {})
    if not object_ref.get("objectId"):
        object_ref = merge_object_ref({"objectId": requested_object_id}, object_ref)
    root_id = str(object_ref.get("objectId") or requested_object_id)
    nodes: dict[str, dict[str, Any]] = {
        root_id: object_graph_node(
            node_id=root_id,
            node_type="mn_object",
            title=str(object_ref.get("title") or root_id),
            status="focused",
            summary=str(object_ref.get("kind") or "MarginNote object"),
            object_ref=object_ref,
            source_id=root_id,
            updated_at="",
        )
    }
    edges: list[dict[str, Any]] = []

    if activity.get("ok"):
        conversations = activity.get("conversations") if isinstance(activity.get("conversations"), list) else []
        for item in conversations[:limit]:
            if not isinstance(item, dict):
                continue
            session_id = str(item.get("sessionId") or item.get("conversationId") or "")
            node_id = operation_ledger_id("conversation", session_id)
            if not node_id:
                continue
            object_graph_add_node(
                nodes,
                edges,
                root_id,
                object_graph_node(
                    node_id=node_id,
                    node_type="conversation",
                    title=str(item.get("title") or "历史对话"),
                    status=str(item.get("updatedAt") or ""),
                    summary=str(item.get("lastMessage") or f"{int(item.get('messageCount') or 0)} 条消息"),
                    object_ref=item.get("objectRef") if isinstance(item.get("objectRef"), dict) else object_ref,
                    source_id=session_id,
                    updated_at=str(item.get("updatedAt") or ""),
                    graph_action=object_graph_action_from_descriptor(item.get("activityAction") if isinstance(item.get("activityAction"), dict) else {}),
                ),
                "has_conversation",
                "object_activity",
            )

        logs = activity.get("logs") if isinstance(activity.get("logs"), list) else []
        for item in logs[:limit]:
            if not isinstance(item, dict):
                continue
            source_id = str(item.get("requestId") or item.get("event") or item.get("ts") or "")
            node_id = operation_ledger_id("log", source_id)
            if not node_id:
                continue
            object_graph_add_node(
                nodes,
                edges,
                root_id,
                object_graph_node(
                    node_id=node_id,
                    node_type="diagnostic_log",
                    title=str(item.get("event") or "诊断日志"),
                    status=str(item.get("level") or ""),
                    summary=str(item.get("message") or ""),
                    object_ref=item.get("objectRef") if isinstance(item.get("objectRef"), dict) else object_ref,
                    source_id=source_id,
                    updated_at=str(item.get("ts") or ""),
                    graph_action=object_graph_action_from_descriptor(item.get("activityAction") if isinstance(item.get("activityAction"), dict) else {}),
                ),
                "has_log",
                "object_activity",
            )

    if ledger.get("ok"):
        entries = ledger.get("entries") if isinstance(ledger.get("entries"), list) else []
        for item in entries[:limit]:
            if not isinstance(item, dict):
                continue
            ledger_id = str(item.get("ledgerId") or "")
            if not ledger_id:
                continue
            object_graph_add_node(
                nodes,
                edges,
                root_id,
                object_graph_node(
                    node_id=ledger_id,
                    node_type=str(item.get("entryType") or "operation"),
                    title=str(item.get("title") or item.get("sourceId") or ledger_id),
                    status=str(item.get("status") or ""),
                    summary=str(item.get("summary") or ""),
                    object_ref=item.get("objectRef") if isinstance(item.get("objectRef"), dict) else object_ref,
                    source_id=str(item.get("sourceId") or ledger_id),
                    updated_at=str(item.get("updatedAt") or item.get("createdAt") or ""),
                    graph_action=object_graph_action_from_descriptor(item.get("ledgerAction") if isinstance(item.get("ledgerAction"), dict) else {}),
                ),
                "has_operation",
                "operation_ledger",
            )

    mindmap_cache = read_latest_mindmap_tree(normalize_topic_id(payload), normalize_book_md5(payload))
    mindmap_evidence: dict[str, Any] = {
        "schema": "codex.mn.nativeMindmapTreeEvidence.v1",
        "available": False,
        "nodeCount": 0,
        "truncatedCount": 0,
        "selectedNoteId": "",
        "rootTitle": "",
    }
    tree = mindmap_cache.get("currentMindmap") if isinstance(mindmap_cache.get("currentMindmap"), dict) else {}
    if tree:
        flattened = object_graph_flatten_mindmap_tree(tree)
        mindmap_evidence = {
            "schema": "codex.mn.nativeMindmapTreeEvidence.v1",
            "available": True,
            "sourceEvent": str(mindmap_cache.get("sourceEvent") or ""),
            "updatedAt": str(mindmap_cache.get("updatedAt") or ""),
            "selectedNoteId": str(mindmap_cache.get("selectedNoteId") or ""),
            "selectedNoteTitle": str(mindmap_cache.get("selectedNoteTitle") or ""),
            "rootTitle": str(mindmap_cache.get("rootTitle") or ""),
            "nodeCount": int(mindmap_cache.get("nodeCount") or len(flattened)),
            "truncatedCount": int(mindmap_cache.get("truncatedCount") or 0),
        }
        note_ids: set[str] = set()
        for item in flattened:
            note_id = str(item.get("noteId") or "")
            if not note_id:
                continue
            note_ids.add(note_id)
            object_graph_add_node(
                nodes,
                edges,
                root_id,
                object_graph_mn_note_node(item, object_ref, mindmap_cache),
                "focuses_mn_note" if int(item.get("depth") or 0) == 0 else "mentions_mn_note",
                "mindmap_tree_cache",
            )
        mn_relation_edges: set[str] = set()
        for item in flattened:
            note_id = str(item.get("noteId") or "")
            parent_note_id = str(item.get("parentNoteId") or "")
            if not note_id or not parent_note_id or parent_note_id not in note_ids:
                continue
            edge = object_graph_edge(
                object_graph_mn_note_node_id(parent_note_id),
                object_graph_mn_note_node_id(note_id),
                "contains",
                "mindmap_tree_cache",
                str(item.get("path") or ""),
            )
            edge_id = str(edge.get("edgeId") or "")
            if edge_id in mn_relation_edges:
                continue
            mn_relation_edges.add(edge_id)
            edges.append(edge)

    native_scan_items = object_graph_registry_scan_items(payload, max_nodes=max(24, limit * 8))
    if native_scan_items:
        source_ref = object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {}
        root_note_id = str(source_ref.get("noteId") or object_graph_note_id_from_object_id(root_id)).strip()
        scan_note_ids = {str(item.get("noteId") or "") for item in native_scan_items if str(item.get("noteId") or "")}
        for item in native_scan_items:
            note_id = str(item.get("noteId") or "")
            if not note_id:
                continue
            object_graph_add_node(
                nodes,
                edges,
                root_id,
                object_graph_registry_scan_node(item),
                "focuses_mn_note" if root_note_id and note_id == root_note_id else "mentions_mn_note",
                "native_object_scan",
            )
        scan_relation_edges: set[str] = set()
        for item in native_scan_items:
            note_id = str(item.get("noteId") or "")
            parent_note_id = str(item.get("parentNoteId") or "")
            if not note_id or not parent_note_id or parent_note_id not in scan_note_ids:
                continue
            edge = object_graph_edge(
                object_graph_mn_note_node_id(parent_note_id),
                object_graph_mn_note_node_id(note_id),
                "contains",
                "native_object_scan",
                str(item.get("path") or ""),
                {"source": "MNObject Registry"},
            )
            edge_id = str(edge.get("edgeId") or "")
            if edge_id in scan_relation_edges:
                continue
            scan_relation_edges.add(edge_id)
            edges.append(edge)

    knowledge_matches = object_graph_collect_knowledge_matches(payload, object_ref, limit)
    note_id_to_node_id: dict[str, str] = {}
    for item in knowledge_matches:
        if not isinstance(item, dict):
            continue
        node_id = object_graph_knowledge_node_id(item)
        if not node_id:
            continue
        note_id = str(item.get("noteId") or "")
        if note_id:
            note_id_to_node_id[note_id] = node_id
        object_graph_add_node(
            nodes,
            edges,
            root_id,
            object_graph_knowledge_node(item, object_ref),
            "mentions_knowledge",
            "knowledge_index",
        )
    relation_edge_ids: set[str] = set()
    for item in knowledge_matches:
        from_id = object_graph_knowledge_node_id(item)
        if not from_id or from_id not in nodes:
            continue
        relations = item.get("relations") if isinstance(item.get("relations"), list) else []
        for relation in relations:
            if not isinstance(relation, dict):
                continue
            target = str(relation.get("targetNoteId") or relation.get("targetId") or "").strip()
            to_id = note_id_to_node_id.get(target, "")
            if not to_id or to_id not in nodes:
                continue
            relation_type = str(relation.get("type") or relation.get("relation") or "related_to") or "related_to"
            edge = object_graph_edge(from_id, to_id, relation_type, "knowledge_relation", str(relation.get("label") or target))
            edge_id = str(edge.get("edgeId") or "")
            if edge_id in relation_edge_ids:
                continue
            relation_edge_ids.add(edge_id)
            edges.append(edge)

    manual_relations = object_graph_add_manual_relations(nodes, edges, root_id, payload)

    type_counts: dict[str, int] = {}
    for node in nodes.values():
        node_type = str(node.get("nodeType") or "unknown")
        type_counts[node_type] = type_counts.get(node_type, 0) + 1
    evidence_counts: dict[str, int] = {}
    for edge in edges:
        evidence_type = str(edge.get("evidenceType") or "")
        if evidence_type:
            evidence_counts[evidence_type] = evidence_counts.get(evidence_type, 0) + 1
    return {
        "ok": True,
        "schema": "codex.mn.objectGraph.v1",
        "message": f"已读取对象图谱：{len(nodes)} 个节点，{len(edges)} 条关系。",
        "root": object_ref if object_ref_has_identity(object_ref) else {"objectId": root_id},
        "nodes": list(nodes.values()),
        "edges": edges,
        "counts": {"nodes": len(nodes), "edges": len(edges), **type_counts, **evidence_counts},
        "mindmapTree": mindmap_evidence,
        "manualRelations": manual_relations,
        "activity": {
            "ok": bool(activity.get("ok")),
            "counts": activity.get("counts") if isinstance(activity.get("counts"), dict) else {},
        },
        "ledger": {
            "ok": bool(ledger.get("ok")),
            "counts": ledger.get("counts") if isinstance(ledger.get("counts"), dict) else {},
        },
    }


def attach_activity_action(kind: str, item: dict[str, Any], object_id: str) -> dict[str, Any]:
    item = dict(item)
    action = ""
    label = "查看"
    payload: dict[str, Any] = {"mnObjectId": object_id}
    if kind == "conversation":
        action = "conversation_load"
        label = "打开对话"
        payload["sessionId"] = str(item.get("sessionId") or "")
    elif kind == "workflow":
        action = "workflow_status"
        label = "查看工作流"
        payload["workflowRunId"] = str(item.get("id") or item.get("workflowRunId") or "")
    elif kind == "transaction":
        action = "ai_edit_transaction_get"
        label = "查看事务"
        payload["transactionId"] = str(item.get("transactionId") or "")
    elif kind == "log":
        action = "log_detail"
        label = "查看日志"
        payload["requestId"] = str(item.get("requestId") or "")
        payload["event"] = str(item.get("event") or "")
    elif kind == "manual_relation":
        action = "operation_ledger_get"
        label = "查看关系"
        payload["ledgerId"] = str(item.get("ledgerId") or operation_ledger_id("manualrel", item.get("eventId") or ""))
    item["activityKind"] = kind
    item["activityAction"] = {
        "schema": "codex.mn.objectActivityAction.v1",
        "label": label,
        "action": action,
        "payload": payload,
    }
    return item


def object_activity(payload: dict[str, Any]) -> dict[str, Any]:
    object_ref = object_ref_from_mapping(payload)
    object_id = str(object_ref.get("objectId") or "")
    if not object_id:
        return {
            "ok": False,
            "message": "对象活动读取失败：缺少当前 MNObject。请先刷新 Agent 计划或选择一个 MarginNote 对象。",
            "schema": "codex.mn.objectActivity.v1",
            "objectRef": {},
        }
    limit = max(1, min(int(payload.get("limit") or 6), 20))
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)

    conversations_result = list_conversations({**payload, "mnObjectId": object_id})
    conversations = conversations_result.get("conversations") if isinstance(conversations_result.get("conversations"), list) else []
    conversations = [attach_activity_action("conversation", item, object_id) for item in conversations[:limit] if isinstance(item, dict)]
    for item in conversations:
        object_ref = merge_object_ref(object_ref, item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {})

    workflows_result = workflow_list({**payload, "mnObjectId": object_id, "limit": limit})
    workflow_runs = workflows_result.get("workflowRuns") if isinstance(workflows_result.get("workflowRuns"), list) else []
    workflow_runs = [attach_activity_action("workflow", item, object_id) for item in workflow_runs if isinstance(item, dict)]

    transaction_candidates = transaction_manager.latest_summary(topicid=topic_id, bookmd5=book_md5, limit=80)
    transactions: list[dict[str, Any]] = []
    for item in transaction_candidates.get("items") if isinstance(transaction_candidates.get("items"), list) else []:
        if not isinstance(item, dict):
            continue
        item_object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
        if str(item_object_ref.get("objectId") or "") != object_id:
            continue
        object_ref = merge_object_ref(object_ref, item_object_ref)
        transactions.append(attach_activity_action("transaction", item, object_id))
        if len(transactions) >= limit:
            break

    logs: list[dict[str, Any]] = []
    for item in reversed(read_recent_diagnostic_logs(160)):
        if not isinstance(item, dict):
            continue
        item_object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
        if str(item_object_ref.get("objectId") or "") != object_id:
            continue
        object_ref = merge_object_ref(object_ref, item_object_ref)
        logs.append(attach_activity_action("log", item, object_id))
        if len(logs) >= limit:
            break

    manual_relations: list[dict[str, Any]] = []
    for item in manual_relation_events_for_object(payload, object_id)[:limit]:
        entry = manual_relation_operation_ledger_entry(item)
        item_with_ledger = {**item, "ledgerId": entry.get("ledgerId")}
        item_object_ref = item.get("fromObject") if isinstance(item.get("fromObject"), dict) else {}
        if str(item.get("fromObjectId") or "") != object_id:
            item_object_ref = item.get("toObject") if isinstance(item.get("toObject"), dict) else {}
        object_ref = merge_object_ref(object_ref, item_object_ref)
        manual_relations.append(attach_activity_action("manual_relation", item_with_ledger, object_id))

    counts = {
        "conversations": len(conversations),
        "workflowRuns": len(workflow_runs),
        "transactions": len(transactions),
        "logs": len(logs),
        "manualRelations": len(manual_relations),
    }
    total = sum(counts.values())
    return {
        "ok": True,
        "schema": "codex.mn.objectActivity.v1",
        "message": f"已读取当前对象活动：{total} 条。",
        "objectRef": object_ref,
        "counts": counts,
        "conversations": conversations,
        "workflowRuns": workflow_runs,
        "transactions": transactions,
        "logs": logs,
        "manualRelations": manual_relations,
    }


def object_browser_action(label: str, action: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema": "codex.mn.objectBrowserAction.v1",
        "label": str(label or "打开"),
        "action": str(action or ""),
        "payload": payload if isinstance(payload, dict) else {},
    }


def object_browser_action_from_descriptor(descriptor: dict[str, Any]) -> dict[str, Any]:
    descriptor = descriptor if isinstance(descriptor, dict) else {}
    return object_browser_action(
        str(descriptor.get("label") or "打开"),
        str(descriptor.get("action") or ""),
        descriptor.get("payload") if isinstance(descriptor.get("payload"), dict) else {},
    )


def object_browser_item(
    *,
    browser_id: str,
    object_type: str,
    kind: str,
    title: str,
    summary: str = "",
    status: str = "",
    object_ref: dict[str, Any] | None = None,
    source_ref: dict[str, Any] | None = None,
    evidence: dict[str, Any] | None = None,
    available_actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    object_ref = object_ref if isinstance(object_ref, dict) else {}
    source_ref = source_ref if isinstance(source_ref, dict) else {}
    evidence = evidence if isinstance(evidence, dict) else {}
    actions = [item for item in (available_actions or []) if isinstance(item, dict) and item.get("action")]
    item: dict[str, Any] = {
        "schema": "codex.mn.objectBrowserItem.v1",
        "browserId": browser_id,
        "objectType": object_type,
        "kind": kind,
        "title": title,
        "summary": summary,
        "status": status,
        "objectRef": object_ref if object_ref_has_identity(object_ref) else {},
        "sourceRef": transaction_manager.clean_source_ref(source_ref),
        "evidence": evidence,
        "availableActions": actions,
    }
    if actions:
        item["browserAction"] = actions[0]
    return item


def object_browser_filter_payload(payload: dict[str, Any]) -> dict[str, str]:
    object_type = str(
        payload.get("objectTypeFilter")
        or payload.get("filterObjectType")
        or payload.get("objectType")
        or ""
    ).strip()
    kind = str(
        payload.get("kindFilter")
        or payload.get("filterKind")
        or payload.get("objectKind")
        or ""
    ).strip()
    query = str(
        payload.get("query")
        or payload.get("search")
        or payload.get("objectQuery")
        or ""
    ).strip()
    if object_type in {"*", "all", "全部"}:
        object_type = ""
    if kind in {"*", "all", "全部"}:
        kind = ""
    return {"objectType": object_type, "kind": kind, "query": query}


def object_browser_item_text(item: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ["browserId", "objectType", "kind", "title", "summary", "status"]:
        value = item.get(key)
        if value:
            parts.append(str(value))
    object_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
    source_ref = item.get("sourceRef") if isinstance(item.get("sourceRef"), dict) else {}
    for mapping in [object_ref, source_ref]:
        for key in ["objectId", "kind", "title", "noteId", "page", "quote", "path", "documentTitle"]:
            value = mapping.get(key)
            if value is not None and value != "":
                parts.append(str(value))
    evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
    for key in ["schema", "relation", "label", "note", "event", "message"]:
        value = evidence.get(key)
        if value:
            parts.append(str(value))
    return "\n".join(parts).lower()


def filter_object_browser_items(objects: list[dict[str, Any]], filters: dict[str, str]) -> list[dict[str, Any]]:
    object_type = str(filters.get("objectType") or "")
    kind = str(filters.get("kind") or "")
    query = str(filters.get("query") or "").lower()
    filtered: list[dict[str, Any]] = []
    for item in objects:
        if object_type and str(item.get("objectType") or "") != object_type:
            continue
        if kind and str(item.get("kind") or "") != kind:
            continue
        if query and query not in object_browser_item_text(item):
            continue
        filtered.append(item)
    return filtered


def object_browser(payload: dict[str, Any]) -> dict[str, Any]:
    requested_object_ref, requested_object_id = operation_ledger_object_filter(payload)
    if not requested_object_id:
        return {
            "ok": False,
            "message": "对象浏览器读取失败：缺少当前 MNObject。请先刷新 Agent 计划或选择一个 MarginNote 对象。",
            "schema": "codex.mn.objectBrowser.v1",
            "rootObject": {},
            "objects": [],
            "groups": [],
            "counts": {"total": 0},
        }

    limit = max(1, min(int(payload.get("limit") or 12), 40))
    scoped_payload = {**payload, "mnObjectId": requested_object_id, "limit": limit}
    graph = object_graph(scoped_payload)
    activity = object_activity(scoped_payload)
    ledger = operation_ledger_list(scoped_payload)
    object_ref = requested_object_ref
    object_ref = merge_object_ref(object_ref, graph.get("root") if isinstance(graph.get("root"), dict) else {})
    object_ref = merge_object_ref(object_ref, activity.get("objectRef") if isinstance(activity.get("objectRef"), dict) else {})
    object_ref = merge_object_ref(object_ref, ledger.get("objectRef") if isinstance(ledger.get("objectRef"), dict) else {})
    if not object_ref.get("objectId"):
        object_ref = merge_object_ref({"objectId": requested_object_id}, object_ref)

    observed_object_refs: list[dict[str, Any]] = [object_ref]
    focus_actions = [
        object_browser_action("打开图谱", "object_graph", {"mnObjectId": requested_object_id, "limit": limit}),
        object_browser_action("查看活动", "object_activity", {"mnObjectId": requested_object_id, "limit": limit}),
        object_browser_action("查看账本", "operation_ledger_list", {"mnObjectId": requested_object_id, "limit": limit}),
    ]
    objects: list[dict[str, Any]] = [
        object_browser_item(
            browser_id=str(object_ref.get("objectId") or requested_object_id),
            object_type="focus",
            kind=str(object_ref.get("kind") or "mn_object"),
            title=str(object_ref.get("title") or requested_object_id),
            summary="当前 MarginNote 焦点对象",
            status="focused",
            object_ref=object_ref,
            source_ref=object_ref.get("sourceRef") if isinstance(object_ref.get("sourceRef"), dict) else {},
            evidence={"schema": "codex.mn.objectBrowserFocusEvidence.v1", "objectRef": object_ref},
            available_actions=focus_actions,
        )
    ]

    graph_objects = 0
    if graph.get("ok"):
        for node in graph.get("nodes") if isinstance(graph.get("nodes"), list) else []:
            if not isinstance(node, dict) or node.get("nodeType") == "mn_object":
                continue
            action = node.get("graphAction") if isinstance(node.get("graphAction"), dict) else {}
            node_ref = node.get("objectRef") if isinstance(node.get("objectRef"), dict) else {}
            node_source_ref = node.get("sourceRef") if isinstance(node.get("sourceRef"), dict) else {}
            if not node_source_ref and isinstance(node_ref.get("sourceRef"), dict):
                node_source_ref = node_ref["sourceRef"]
            if object_ref_has_identity(node_ref):
                observed_object_refs.append(node_ref)
            objects.append(
                object_browser_item(
                    browser_id=str(node.get("nodeId") or node.get("sourceId") or ""),
                    object_type="object_graph",
                    kind=str(node.get("nodeType") or "graph_node"),
                    title=str(node.get("title") or node.get("sourceId") or "图谱对象"),
                    summary=str(node.get("summary") or ""),
                    status=str(node.get("status") or ""),
                    object_ref=node_ref,
                    source_ref=node_source_ref,
                    evidence={"schema": "codex.mn.objectBrowserGraphEvidence.v1", "node": node},
                    available_actions=[object_browser_action_from_descriptor(action)] if action.get("action") else [],
                )
            )
            graph_objects += 1
            if graph_objects >= limit:
                break

    activity_objects = 0
    if activity.get("ok"):
        activity_lists = [
            activity.get("conversations"),
            activity.get("workflowRuns"),
            activity.get("transactions"),
            activity.get("manualRelations"),
            activity.get("logs"),
        ]
        for bucket in activity_lists:
            for item in bucket if isinstance(bucket, list) else []:
                if not isinstance(item, dict):
                    continue
                action = item.get("activityAction") if isinstance(item.get("activityAction"), dict) else {}
                item_ref = item.get("objectRef") if isinstance(item.get("objectRef"), dict) else {}
                item_source_ref = item_ref.get("sourceRef") if isinstance(item_ref.get("sourceRef"), dict) else {}
                if object_ref_has_identity(item_ref):
                    observed_object_refs.append(item_ref)
                browser_id = str(
                    item.get("sessionId")
                    or item.get("id")
                    or item.get("transactionId")
                    or item.get("eventId")
                    or item.get("requestId")
                    or item.get("event")
                    or ""
                )
                objects.append(
                    object_browser_item(
                        browser_id=operation_ledger_id("activity", browser_id) or browser_id,
                        object_type="object_activity",
                        kind=str(item.get("activityKind") or "activity"),
                        title=str(item.get("title") or item.get("event") or item.get("label") or item.get("transactionId") or "对象活动"),
                        summary=str(item.get("message") or item.get("lastMessage") or item.get("status") or item.get("note") or ""),
                        status=str(item.get("status") or item.get("level") or ""),
                        object_ref=item_ref,
                        source_ref=item_source_ref,
                        evidence={"schema": "codex.mn.objectBrowserActivityEvidence.v1", "activity": item},
                        available_actions=[object_browser_action_from_descriptor(action)] if action.get("action") else [],
                    )
                )
                activity_objects += 1
                if activity_objects >= limit:
                    break
            if activity_objects >= limit:
                break

    ledger_objects = 0
    if ledger.get("ok"):
        for entry in ledger.get("entries") if isinstance(ledger.get("entries"), list) else []:
            if not isinstance(entry, dict):
                continue
            action = entry.get("ledgerAction") if isinstance(entry.get("ledgerAction"), dict) else {}
            entry_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
            if object_ref_has_identity(entry_ref):
                observed_object_refs.append(entry_ref)
            evidence: dict[str, Any] = {"schema": "codex.mn.objectBrowserLedgerEvidence.v1", "entry": entry}
            if str(entry.get("entryType") or "") == "object_graph_manual_relation":
                detail = operation_ledger_get({"ledgerId": str(entry.get("ledgerId") or "")})
                if detail.get("ok") and isinstance(detail.get("evidence"), dict):
                    evidence.update(detail["evidence"])
            objects.append(
                object_browser_item(
                    browser_id=str(entry.get("ledgerId") or entry.get("sourceId") or ""),
                    object_type="operation_ledger",
                    kind=str(entry.get("entryType") or "ledger"),
                    title=str(entry.get("title") or entry.get("sourceId") or "账本对象"),
                    summary=str(entry.get("summary") or ""),
                    status=str(entry.get("status") or ""),
                    object_ref=entry_ref,
                    source_ref=entry_ref.get("sourceRef") if isinstance(entry_ref.get("sourceRef"), dict) else {},
                    evidence=evidence,
                    available_actions=[object_browser_action_from_descriptor(action)] if action.get("action") else [],
                )
            )
            ledger_objects += 1
            if ledger_objects >= limit:
                break

    register_mn_objects(
        observed_object_refs,
        payload,
        "object_browser",
        source={"mnObjectId": requested_object_id},
    )
    registry_objects = 0
    registry = mn_object_registry({**payload, "limit": limit})
    if registry.get("ok"):
        for entry in registry.get("objects") if isinstance(registry.get("objects"), list) else []:
            if not isinstance(entry, dict):
                continue
            entry_ref = entry.get("objectRef") if isinstance(entry.get("objectRef"), dict) else {}
            object_id = str(entry_ref.get("objectId") or entry.get("objectId") or "")
            if not object_id:
                continue
            evidence_types = [
                str(item)
                for item in entry.get("evidenceTypes", [])
                if isinstance(entry.get("evidenceTypes"), list) and str(item)
            ]
            action_payload = {
                "mnObjectId": object_id,
                "mnObject": entry_ref,
                "evidenceTypes": sorted(set(evidence_types)),
                "limit": limit,
            }
            objects.append(
                object_browser_item(
                    browser_id=operation_ledger_id("registry", object_id),
                    object_type="registry",
                    kind=str(entry_ref.get("kind") or entry.get("kind") or "mn_object"),
                    title=str(entry_ref.get("title") or entry.get("title") or object_id),
                    summary=f"Registry seen {int(entry.get('seenCount') or 0)} 次",
                    status="registered",
                    object_ref=entry_ref,
                    source_ref=entry_ref.get("sourceRef") if isinstance(entry_ref.get("sourceRef"), dict) else {},
                    evidence={"schema": "codex.mn.objectBrowserRegistryEvidence.v1", "registryEntry": entry},
                    available_actions=[
                        object_browser_action("打开图谱", "object_graph", action_payload),
                        object_browser_action("查看活动", "object_activity", action_payload),
                        object_browser_action("查看账本", "operation_ledger_list", action_payload),
                    ],
                )
            )
            registry_objects += 1
            if registry_objects >= limit:
                break

    filters = object_browser_filter_payload(payload)
    filtered_objects = filter_object_browser_items(objects, filters)
    type_counts: dict[str, int] = {}
    for item in filtered_objects:
        object_type = str(item.get("objectType") or "unknown")
        type_counts[object_type] = type_counts.get(object_type, 0) + 1
    groups = [
        {"schema": "codex.mn.objectBrowserGroup.v1", "groupId": "focus", "label": "当前对象", "count": type_counts.get("focus", 0)},
        {"schema": "codex.mn.objectBrowserGroup.v1", "groupId": "registry", "label": "MNObject Registry", "count": type_counts.get("registry", 0)},
        {"schema": "codex.mn.objectBrowserGroup.v1", "groupId": "object_graph", "label": "Object Graph", "count": type_counts.get("object_graph", 0)},
        {"schema": "codex.mn.objectBrowserGroup.v1", "groupId": "object_activity", "label": "对象活动", "count": type_counts.get("object_activity", 0)},
        {"schema": "codex.mn.objectBrowserGroup.v1", "groupId": "operation_ledger", "label": "Operation Ledger", "count": type_counts.get("operation_ledger", 0)},
    ]
    return {
        "ok": True,
        "schema": "codex.mn.objectBrowser.v1",
        "message": f"已读取对象浏览器：{len(filtered_objects)} / {len(objects)} 个对象。",
        "rootObject": object_ref,
        "filters": filters,
        "groups": groups,
        "counts": {
            "total": len(filtered_objects),
            "filteredTotal": len(filtered_objects),
            "unfilteredTotal": len(objects),
            **type_counts,
        },
        "objects": filtered_objects[: max(limit * 3, limit)],
        "sources": {
            "registry": registry.get("counts") if isinstance(registry.get("counts"), dict) else {},
            "graph": graph.get("counts") if isinstance(graph.get("counts"), dict) else {},
            "activity": activity.get("counts") if isinstance(activity.get("counts"), dict) else {},
            "ledger": ledger.get("counts") if isinstance(ledger.get("counts"), dict) else {},
        },
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
    transaction_result = transaction_manager.apply_native_event(record)
    if transaction_result.get("ok"):
        record["transaction"] = transaction_manager.transaction_summary(transaction_result["transaction"])
    if record["event"] == "mindmapTreeReadFinished":
        cache_result = write_latest_mindmap_tree(record)
        if cache_result.get("ok"):
            record["mindmapTreeCache"] = {
                "schema": cache_result["cache"].get("schema"),
                "nodeCount": cache_result["cache"].get("nodeCount"),
                "updatedAt": cache_result["cache"].get("updatedAt"),
            }
            if isinstance(cache_result.get("mnObjectRegistry"), dict):
                record["mnObjectRegistry"] = cache_result["mnObjectRegistry"]
    if record["event"] == "mnObjectRegistryScanFinished":
        record["mnObjectRegistry"] = register_native_object_scan_event(record)
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


def latest_mindmap_diff_apply_status(topic_id: str = "", book_md5: str = "", limit: int = 120) -> dict[str, Any]:
    def safe_count(value: Any) -> int:
        try:
            return int(value or 0)
        except Exception:
            return 0

    topic_id = str(topic_id or "")
    book_md5 = str(book_md5 or "")
    for item in reversed(read_recent_events(limit)):
        if str(item.get("event") or "") != "mindmapDiffApplyFinished":
            continue
        if topic_id and str(item.get("topicid") or "") != topic_id:
            continue
        if book_md5 and str(item.get("bookmd5") or "") != book_md5:
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        verification = extra.get("verification") if isinstance(extra.get("verification"), dict) else {}
        failed_count = safe_count(extra.get("failedCount"))
        applied_count = safe_count(extra.get("appliedCount"))
        status = str(verification.get("status") or ("block" if failed_count else ("pass" if applied_count else "unknown")))
        summary = str(
            verification.get("summary")
            or f"脑图 Diff 验证：通过 {safe_count(verification.get('verifiedCount')) or applied_count}，失败 {safe_count(verification.get('failedVerificationCount')) or failed_count}。"
        )
        return {
            "schema": "codex.mn.mindmapDiffApplyStatus.v1",
            "available": True,
            "status": status,
            "summary": summary,
            "topicid": str(item.get("topicid") or ""),
            "bookmd5": str(item.get("bookmd5") or ""),
            "updatedAt": str(item.get("ts") or ""),
            "appliedCount": applied_count,
            "failedCount": failed_count,
            "createdNoteIds": extra.get("createdNoteIds") if isinstance(extra.get("createdNoteIds"), list) else [],
            "appliedOperations": extra.get("appliedOperations") if isinstance(extra.get("appliedOperations"), list) else [],
            "verification": verification,
        }
    return {
        "schema": "codex.mn.mindmapDiffApplyStatus.v1",
        "available": False,
        "status": "unknown",
        "summary": "还没有收到脑图 Diff 局部执行验证结果。",
        "topicid": topic_id,
        "bookmd5": book_md5,
        "updatedAt": "",
        "appliedCount": 0,
        "failedCount": 0,
        "createdNoteIds": [],
        "appliedOperations": [],
        "verification": {},
    }


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
    update_mindmap_ready = bool(extra.get("canUpdateMindmapNode") or extra.get("canUpdateMindmap"))
    merge_mindmap_ready = bool(extra.get("canMergeMindmapNode") or extra.get("canMergeMindmap"))
    move_mindmap_ready = bool(extra.get("canMoveMindmapNode") or extra.get("canMoveMindmap"))
    delete_mindmap_ready = bool(extra.get("canDeleteMindmapNode") or extra.get("canDeleteMindmap"))
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
            "nativeMindmapUpdate": {
                "label": "更新 MN 原生脑图节点",
                "available": update_mindmap_ready,
                "ready": update_mindmap_ready,
                "entryAction": "request_mindmap_diff_apply",
                "nativeAction": "apply_mindmap_diff_operations",
                "blockedReason": "" if update_mindmap_ready else "unverified-note-update-api",
                "nextStep": "刷新 MN 原生能力；确认 noteTitle/comment 更新路径可用后再局部更新。",
                "evidence": ["noteTitle", "appendMarkdownComment"] if update_mindmap_ready else [],
            },
            "nativeMindmapMerge": {
                "label": "合并 MN 原生脑图节点",
                "available": merge_mindmap_ready,
                "ready": merge_mindmap_ready,
                "entryAction": "request_mindmap_diff_apply",
                "nativeAction": "apply_mindmap_diff_operations",
                "blockedReason": "" if merge_mindmap_ready else "unverified-note-merge-api",
                "nextStep": "刷新 MN 原生能力；确认合并策略可用后再执行。",
                "evidence": ["appendMarkdownComment"] if merge_mindmap_ready else [],
            },
            "nativeMindmapMove": {
                "label": "移动 MN 原生脑图节点",
                "available": move_mindmap_ready,
                "ready": move_mindmap_ready,
                "entryAction": "request_mindmap_diff_apply",
                "nativeAction": "apply_mindmap_diff_operations",
                "blockedReason": "" if move_mindmap_ready else "unverified-note-move-api",
                "nextStep": "刷新 MN 原生能力；确认 addChild 迁移父节点路径可用后再移动。",
                "evidence": ["addChild"] if move_mindmap_ready else [],
            },
            "nativeMindmapDelete": {
                "label": "删除 MN 原生脑图节点",
                "available": delete_mindmap_ready,
                "ready": delete_mindmap_ready,
                "entryAction": "request_mindmap_diff_apply",
                "nativeAction": "apply_mindmap_diff_operations",
                "blockedReason": "" if delete_mindmap_ready else "unverified-note-delete-api",
                "nextStep": "删除类操作必须显式确认并通过事务验证后才能执行。",
                "evidence": ["deleteNote"] if delete_mindmap_ready else [],
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
    mn_api_status = mn_api_status_fields(settings)
    return {
        "ok": True,
        "message": "Codex MarginNote Companion is running.",
        "pid": os.getpid(),
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        **ai_status,
        **mn_api_status,
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
        "mindmapTreeCache": latest_mindmap_tree_cache_status(),
        "mindmapDiffApply": latest_mindmap_diff_apply_status(),
        "aiEditTransactions": transaction_manager.latest_summary(limit=8),
        "aiEditTransactionStatus": transaction_manager.latest_status(),
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


def should_include_knowledge_index(payload: dict[str, Any], task: str) -> bool:
    if truthy_payload_flag(payload.get("includeKnowledgeIndex")):
        return True
    if str(payload.get("includeKnowledgeIndex") or "").strip().lower() in {"0", "false", "no", "off"}:
        return False
    text = combined_user_request(payload)
    if task == "goal_run" and has_explicit_goal_payload(payload):
        goal = goal_payload_from_request(payload)
        text = "\n".join(part for part in [text, goal.get("title", ""), goal.get("detail", "")] if part)
    return bool(KNOWLEDGE_INDEX_REQUEST_RE.search(text))


def knowledge_index_scope(payload: dict[str, Any]) -> tuple[str, str, str]:
    requested = str(payload.get("knowledgeScope") or payload.get("knowledge_scope") or "").strip().lower()
    text = combined_user_request(payload)
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if requested in {"notebook", "topic"} or re.search(r"跨文档|整个\s*notebook|notebook", text, re.I):
        return topic_id, "", "notebook"
    return topic_id, book_md5, "document"


def knowledge_index_context_for_model(payload: dict[str, Any], query: str, task: str = "chat", max_chars: int = 2400) -> str:
    if not should_include_knowledge_index(payload, task):
        return ""
    topic_id, book_md5, scope_label = knowledge_index_scope(payload)
    search_query = repair_pdf_extracted_math_text(str(query or combined_user_request(payload) or "")).strip()
    result = knowledge_index.search(search_query, topicid=topic_id, bookmd5=book_md5, limit=5)
    if not result.get("ok"):
        if truthy_payload_flag(payload.get("includeKnowledgeIndex")):
            return f"本地知识索引：检索失败：{result.get('message') or '缺少关键词'}"
        return ""
    matches = result.get("matches") if isinstance(result.get("matches"), list) else []
    if not matches:
        if truthy_payload_flag(payload.get("includeKnowledgeIndex")):
            return f"本地知识索引：当前{('notebook' if scope_label == 'notebook' else '文档')}范围未命中。"
        return ""
    lines = [
        "本地知识索引检索片段：",
        f"范围：{scope_label}；说明：以下来自 Companion 本地索引，不代表当前 PDF 原文。",
    ]
    used = len("\n".join(lines))
    for item in matches:
        if not isinstance(item, dict):
            continue
        source_ref = item.get("sourceRef") if isinstance(item.get("sourceRef"), dict) else {}
        source_bits = []
        if item.get("noteId"):
            source_bits.append(f"noteId={item.get('noteId')}")
        if source_ref.get("page"):
            source_bits.append(f"p.{source_ref.get('page')}")
        if source_ref.get("quote"):
            source_bits.append(f"quote={source_ref.get('quote')}")
        source_line = (" / " + " / ".join(source_bits)) if source_bits else ""
        block = (
            f"\n[{item.get('kind') or 'context'}] {item.get('title') or '未命名索引项'}{source_line}\n"
            f"{item.get('snippet') or ''}"
        )
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining <= 160:
                break
            block = block[:remaining].rstrip()
        lines.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n".join(lines).strip()


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
    knowledge_context = knowledge_index_context_for_model(payload, combined_user_request(payload), task=task)
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
    if knowledge_context:
        sections.append(knowledge_context)
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


def is_retryable_codex_cli_startup_error(detail: str) -> bool:
    text = str(detail or "").lower()
    return "timed out waiting for cloud config bundle" in text


def format_codex_cli_failure(detail: str, settings: dict[str, str], retried: bool = False) -> str:
    if len(detail) > 1400:
        detail = detail[:1400] + "..."
    if is_retryable_codex_cli_startup_error(detail):
        proxy_url = sanitize_proxy_url(settings.get("proxyUrl", ""))
        retry_text = "已自动重试一次，仍失败；" if retried else ""
        proxy_text = f"当前代理：{proxy_url}。" if proxy_url else "当前未配置代理。"
        return (
            "Codex CLI 网络/代理初始化超时："
            f"{retry_text}CLI 在 15 秒内没有拿到 cloud config bundle。"
            "这通常是代理链路、网络抖动或 Codex CLI 云端配置初始化失败，不是当前 PDF 或脑图问题。"
            f"{proxy_text}请重试，或检查代理/Codex CLI 登录；也可以在设置中配置 OpenAI Key 作为备用后端。"
            f" 原始错误：{detail}"
        )
    return f"Codex CLI 调用失败或无输出：{detail}"


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
    retried_startup_error = False
    last_detail = "Codex CLI 返回为空。"
    for attempt in range(2):
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
        last_detail = stdout or stderr or "Codex CLI 返回为空。"
        if attempt == 0 and is_retryable_codex_cli_startup_error(last_detail):
            retried_startup_error = True
            continue
        return format_codex_cli_failure(last_detail, settings, retried=retried_startup_error), "codex-cli-error"
    return format_codex_cli_failure(last_detail, settings, retried=retried_startup_error), "codex-cli-error"


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


def card_factory_source_ref(payload: dict[str, Any], source_text: str) -> dict[str, Any]:
    source: dict[str, Any] = {}
    page = payload.get("pageNumber") or payload.get("page") or payload.get("pageLabel")
    if page not in (None, ""):
        source["page"] = page
    note_id = str(payload.get("selectedNoteId") or payload.get("noteId") or payload.get("noteid") or "").strip()
    if note_id:
        source["noteId"] = note_id
    note_title = str(payload.get("selectedNoteTitle") or payload.get("noteTitle") or "").strip()
    if note_title:
        source["noteTitle"] = truncate_text(note_title, 120)
    document_title = str(payload.get("documentTitle") or payload.get("docTitle") or payload.get("bookTitle") or "").strip()
    if document_title:
        source["documentTitle"] = truncate_text(document_title, 180)
    quote = plain_context_excerpt(
        str(payload.get("selectionText") or payload.get("selectedText") or payload.get("sourceExcerpt") or source_text or ""),
        240,
    )
    if quote:
        source["quote"] = quote
    topic_id = normalize_topic_id(payload)
    book_md5 = normalize_book_md5(payload)
    if topic_id:
        source["topicid"] = topic_id
    if book_md5:
        source["bookmd5"] = book_md5
    return source


def infer_card_factory_type(title: str, body: str) -> str:
    title_value = str(title or "").lower()
    if re.search(r"概念|定义|定位|concept", title_value):
        return "concept"
    if re.search(r"公式|符号|notation|equation|变量|计算", title_value):
        return "formula"
    if re.search(r"实验|证据|结果|数据|figure|table|evidence", title_value):
        return "evidence"
    body_without_source = str(body or "").split("## 来源线索", 1)[0]
    value = f"{title}\n{body_without_source}".lower()
    if re.search(r"公式|符号|notation|equation|mask|score|log\s*pi|gradient|坐标|变量", value):
        return "formula"
    if re.search(r"实验|证据|结果|数据|第\s*\d+\s*页|figure|table|real robot|benchmark|ablation", value):
        return "evidence"
    if re.search(r"方法|算法|流程|模型|policy|pipeline|architecture|filter", value):
        return "method"
    if re.search(r"局限|失败|边界|风险|limitation|failure|不能|不保证", value):
        return "limitation"
    if re.search(r"对比|区别|相同|不同|compare|versus|vs\\.", value):
        return "comparison"
    if re.search(r"复习|问题|quiz|review", value):
        return "review"
    return "concept"


def card_factory_learning_goal(card_type: str) -> str:
    goals = {
        "concept": "说清这个概念的定义、作用和边界。",
        "formula": "解释关键符号、变量关系和公式用途。",
        "method": "复述方法流程、输入输出和关键假设。",
        "evidence": "说明这条证据支持了什么结论，以及支持边界。",
        "limitation": "指出失败条件、适用边界和误用风险。",
        "comparison": "比较对象之间的相同点、差异和取舍。",
        "review": "把内容转成可自测的问题和答案线索。",
    }
    return goals.get(card_type, goals["concept"])


def card_factory_review_prompt(title: str, card_type: str) -> str:
    title = clean_mindmap_node_title(title, 60)
    if card_type == "formula":
        return f"不用看原文，解释“{title}”里的符号关系和它解决的问题。"
    if card_type == "evidence":
        return f"“{title}”这条证据具体支持了哪个结论？支持边界是什么？"
    if card_type == "method":
        return f"按输入、步骤、输出复述“{title}”。"
    if card_type == "limitation":
        return f"“{title}”在什么条件下不成立或容易被误用？"
    if card_type == "comparison":
        return f"比较“{title}”涉及对象的关键差异和取舍。"
    return f"用自己的话解释“{title}”的核心含义。"


def card_factory_summary(cards: list[dict[str, Any]], source_ref: dict[str, Any]) -> dict[str, Any]:
    quality = operation_runtime.audit_card_quality(cards)
    return {
        "schema": CARD_FACTORY_SCHEMA,
        "cardCount": len(cards),
        "typeCounts": quality.get("typeCounts", {}),
        "sourceRef": source_ref,
        "reviewPromptCount": len([card for card in cards if card.get("reviewPrompt")]),
        "learningGoalCount": len([card for card in cards if card.get("learningGoal")]),
    }


def enrich_card_factory_cards(cards: list[dict[str, Any]], source_text: str, backend: str, payload: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    source_ref = card_factory_source_ref(payload, source_text)
    enriched: list[dict[str, Any]] = []
    for index, card in enumerate(cards, start=1):
        item = dict(card)
        title = str(item.get("title") or f"Codex短卡 {index:02d}").strip()
        body = str(item.get("body") or "").strip()
        card_type = str(item.get("cardType") or item.get("type") or "").strip() or infer_card_factory_type(title, body)
        item["cardType"] = card_type
        item["source"] = {**source_ref, **(item.get("source") if isinstance(item.get("source"), dict) else {})}
        item["learningGoal"] = str(item.get("learningGoal") or card_factory_learning_goal(card_type))
        item["reviewPrompt"] = str(item.get("reviewPrompt") or card_factory_review_prompt(title, card_type))
        item["factory"] = {
            "schema": CARD_FACTORY_CARD_SCHEMA,
            "index": index,
            "backend": backend,
            "sourceLinked": bool(item["source"]),
        }
        enriched.append(item)
    return enriched, card_factory_summary(enriched, source_ref)


def build_short_cards(text: str, reply: str, backend: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    sections = markdown_heading_sections(reply) or bullet_sections(reply) or fallback_card_sections(reply)
    cards: list[dict[str, Any]] = []
    for index, section in enumerate(sections[:6], 1):
        title = clean_mindmap_node_title(section.get("title") or f"精读笔记 {index}", 34)
        body = build_card_body(section.get("body") or reply, text, backend, payload)
        cards.append({"title": f"Codex短卡 {index:02d}：{title}", "body": body})
    if not cards:
        cards = [{"title": "Codex短卡 01：精读笔记", "body": build_card_body(reply, text, backend, payload)}]
    enriched, _factory = enrich_card_factory_cards(cards, text, backend, payload)
    return enriched


def with_mn_object(payload: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    return {**result, "mnObject": agent_workbench.build_mn_object(payload)}


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
    card_factory = card_factory_summary(cards, card_factory_source_ref(payload, text))
    card_quality = operation_runtime.audit_card_quality(cards)
    append_history(payload, text, reply)
    return with_mn_object(payload, {
        "ok": True,
        "message": f"已返回 {len(cards)} 张可写入 MN4 的短卡片（{backend}）。",
        "reply": reply,
        "backend": backend,
        "cards": cards,
        "cardFactory": card_factory,
        "cardQuality": card_quality,
    })


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
    return with_mn_object(payload, result)


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
    return with_mn_object(payload, {
        "ok": True,
        "message": f"已返回可写入 MN4 的{message_label}（{backend}，{stats.get('nodeCount', 0)} 个节点，{stats.get('maxDepth', 0)} 层）。",
        "reply": reply,
        "backend": backend,
        "mindmap": tree,
        "writeTarget": write_target,
        "mindmapStats": stats,
    })


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
    card_factory = card_factory_summary(cards, card_factory_source_ref(payload, text or "完整精读"))
    card_quality = operation_runtime.audit_card_quality(cards)
    append_history(payload, text or "完整精读", reply)
    result = {
        "ok": True,
        "message": f"已返回完整精读草稿：{len(cards)} 张短卡片 + 1 个脑图分支（{backend}）。",
        "reply": reply,
        "backend": backend,
        "cards": cards,
        "cardFactory": card_factory,
        "cardQuality": card_quality,
        "mindmap": tree,
    }
    if write_target:
        result["writeTarget"] = write_target
    return with_mn_object(payload, result)


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
            **mn_api_status_fields(settings),
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
                f"MN API：{mn_api_status_fields(settings)['mn_api_backend_label']}\n"
                f"代理：{'已配置' if settings.get('proxyUrl') else '未配置'}\n"
                f"OpenAI：{'已配置' if get_setting('OPENAI_API_KEY') else '未配置'}\n"
                f"URL API：{'已配置' if get_setting('MN_URL_API_SECRET') else '未配置'}\n"
                f"文件路径：{len(settings.get('fileSearchRoots') or [])} 个\n"
                f"自定义按钮：{len(settings.get('customButtons') or [])}"
            ),
            "settings": settings,
            **ai_status_fields(settings),
            **mn_api_status_fields(settings),
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
    if action == "mn_api_status":
        settings = runtime_settings()
        return {
            "ok": True,
            "message": "已读取 MarginNote API 适配器状态。",
            **mn_api_status_fields(settings),
        }
    if action == "mn_url_api_build_request":
        try:
            request_preview = marginnote_api_adapter.build_url_api_request(
                action=str(payload.get("urlApiAction") or payload.get("urlAction") or "ping"),
                secret=get_setting("MN_URL_API_SECRET"),
                payload=payload.get("urlPayload") if isinstance(payload.get("urlPayload"), dict) else {},
                callback_base_url=str(
                    payload.get("callbackBaseUrl")
                    or f"http://{HOST}:{PORT}/mn-url-api/callback"
                ),
                request_id=str(payload.get("requestId") or ""),
            )
        except ValueError as exc:
            return {
                "ok": False,
                "message": f"构造 MarginNote URL API 请求失败：{exc}",
                **mn_api_status_fields(runtime_settings()),
            }
        return {
            "ok": True,
            "message": "已构造 MarginNote URL API 请求预览。",
            "request": {
                "requestId": request_preview.request_id,
                "action": request_preview.action,
                "payload": request_preview.payload,
                "redactedUrl": request_preview.redacted_url,
            },
            **mn_api_status_fields(runtime_settings()),
        }
    if action == "agent_plan":
        return agent_plan(payload)
    if action == "operation_plan_preview":
        return operation_plan_preview(payload)
    if action == "mindmap_diff_preview":
        return mindmap_diff_preview(payload)
    if action == "request_mindmap_diff_apply":
        return request_mindmap_diff_apply(payload)
    if action == "workflow_templates":
        return {
            "ok": True,
            "message": "已读取工作流模板。",
            "workflowTemplates": workflow_engine.list_workflow_templates(),
        }
    if action == "workflow_preview":
        return workflow_preview(payload)
    if action == "workflow_start":
        return workflow_start(payload)
    if action == "workflow_status":
        return load_workflow_run(str(payload.get("workflowRunId") or payload.get("id") or ""))
    if action == "workflow_list":
        return workflow_list(payload)
    if action == "workflow_cancel":
        return workflow_cancel(payload)
    if action == "workflow_retry_step":
        return workflow_retry_step(payload)
    if action == "external_gateway_start_workflow":
        return external_gateway_start_workflow(payload)
    if action == "external_gateway_request_status":
        return external_gateway_request_status(payload)
    if action == "external_gateway_callback":
        return external_gateway_callback_update(payload)
    if action == "skill_marketplace_status":
        return skill_marketplace.status()
    if action == "skill_install":
        return skill_marketplace.install(str(payload.get("skillId") or payload.get("id") or ""))
    if action == "skill_uninstall":
        return skill_marketplace.uninstall(str(payload.get("skillId") or payload.get("id") or ""))
    if action == "knowledge_index_status":
        return knowledge_index.status(normalize_topic_id(payload), normalize_book_md5(payload))
    if action == "knowledge_index_search":
        return knowledge_index_search_action(payload)
    if action == "knowledge_index_ingest_context":
        return knowledge_index_ingest_context(payload)
    if action == "knowledge_index_clear":
        return knowledge_index.clear(normalize_topic_id(payload), normalize_book_md5(payload))
    if action == "review_queue_add":
        return review_queue_add(payload)
    if action == "review_queue_list":
        return review_queue_list(payload)
    if action == "mn_object_registry":
        return mn_object_registry(payload)
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
    if action == "mn_read_tree":
        return request_mindmap_tree(payload)
    if action == "request_mn_object_registry_scan":
        return request_mn_object_registry_scan(payload)
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
    if action == "object_browser":
        return object_browser(payload)
    if action == "object_graph":
        return object_graph(payload)
    if action == "object_graph_relation_save":
        return object_graph_relation_save(payload)
    if action == "object_graph_relation_delete":
        return object_graph_relation_delete(payload)
    if action == "object_activity":
        return object_activity(payload)
    if action == "operation_ledger_list":
        return operation_ledger_list(payload)
    if action == "operation_ledger_get":
        return operation_ledger_get(payload)
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
    if action == "ai_edit_transaction_list":
        transactions = transaction_manager.latest_summary(
            topicid=normalize_topic_id(payload),
            bookmd5=normalize_book_md5(payload),
            limit=int(payload.get("limit") or 8),
        )
        return {
            "ok": True,
            "message": f"已读取最近 {transactions['count']} 个 AI 编辑事务。",
            "transactions": transactions,
        }
    if action == "ai_edit_transaction_get":
        transaction_id = str(payload.get("transactionId") or payload.get("id") or "")
        transaction = transaction_manager.load_transaction(transaction_id)
        if not transaction:
            return {
                "ok": False,
                "message": "未找到该 AI 编辑事务。",
                "transactionId": transaction_id,
            }
        return {
            "ok": True,
            "message": "已读取 AI 编辑事务。",
            "transaction": transaction,
        }
    if action == "ai_edit_transaction_verify":
        transaction_id = str(payload.get("transactionId") or payload.get("id") or "")
        transaction = transaction_manager.load_transaction(transaction_id)
        if not transaction:
            return {
                "ok": False,
                "message": "未找到该 AI 编辑事务，无法生成验证报告。",
                "transactionId": transaction_id,
            }
        verification = transaction_manager.verification_report(transaction)
        return {
            "ok": True,
            "message": "已生成 AI 编辑验证报告。",
            "reply": verification.get("summary") or "回滚验证：无报告内容。",
            "transaction": transaction,
            "verification": verification,
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
    if action == "request_mindmap_delete_confirmation":
        return request_mindmap_delete_confirmation(payload)
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
    summary = {
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
    object_ref = object_ref_from_mapping(result)
    if object_ref_has_identity(object_ref):
        summary["objectRef"] = object_ref
        summary["mnObjectId"] = str(object_ref.get("objectId") or "")
    return summary


def handle_action_logged(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        payload = {}
    payload = dict(payload)
    request_id = str(payload.get("_request_id") or payload.get("requestId") or uuid.uuid4().hex[:12])
    payload["_request_id"] = request_id
    action = str(payload.get("action") or "").strip()
    object_ref = object_ref_from_mapping(payload)
    started = time.time()
    append_diagnostic_log(
        "info",
        "action.start",
        f"开始动作：{action or '(empty)'}",
        payload=payload,
        object_ref=object_ref if object_ref_has_identity(object_ref) else None,
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
            object_ref=object_ref if object_ref_has_identity(object_ref) else None,
            request_id=request_id,
        )
        raise
    if not isinstance(result, dict):
        result = {"ok": False, "message": "动作没有返回可用结果。"}
    result["requestId"] = request_id
    result_object_ref = object_ref_from_mapping(result, object_ref)
    append_diagnostic_log(
        "info" if result.get("ok") else "warn",
        "action.end",
        str(result.get("message") or ("动作完成。" if result.get("ok") else "动作失败。")),
        payload=payload,
        extra={
            "durationMs": int((time.time() - started) * 1000),
            "result": action_log_result_summary(result),
        },
        object_ref=result_object_ref if object_ref_has_identity(result_object_ref) else None,
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
        if self.path == "/external/workflow/start":
            external_payload = dict(payload) if isinstance(payload, dict) else {}
            external_payload.update({"action": "external_gateway_start_workflow"})
            try:
                result = handle_action_logged(external_payload)
            except Exception as exc:
                append_diagnostic_log(
                    "error",
                    "external_gateway.http_exception",
                    f"外部 workflow 请求失败：{exc}",
                    payload=external_payload,
                    extra={"path": self.path, "error": repr(exc)},
                )
                result = {"ok": False, "message": f"外部 workflow 请求失败：{exc}"}
            self._send_json(200 if result.get("ok") else 400, result)
            return
        if self.path in {"/external/callback/success", "/external/callback/error"}:
            callback_payload = dict(payload) if isinstance(payload, dict) else {}
            callback_payload.update(
                {
                    "action": "external_gateway_callback",
                    "callbackStatus": "success" if self.path.endswith("/success") else "error",
                }
            )
            try:
                result = handle_action_logged(callback_payload)
            except Exception as exc:
                append_diagnostic_log(
                    "error",
                    "external_gateway.callback_exception",
                    f"外部 callback 请求失败：{exc}",
                    payload=callback_payload,
                    extra={"path": self.path, "error": repr(exc)},
                )
                result = {"ok": False, "message": f"外部 callback 请求失败：{exc}"}
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
    WORKFLOW_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    load_env_file()
    (ROOT / "companion.pid").write_text(str(os.getpid()), encoding="utf-8")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Codex MarginNote Companion listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
