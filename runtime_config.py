from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


DEFAULT_MODEL = "gpt-5.6-sol"
MODEL_PRESETS = [
    {"id": "gpt-5.6-sol", "label": "GPT-5.6 SOL", "note": "frontier capability"},
    {"id": "gpt-5.6-terra", "label": "GPT-5.6 Terra", "note": "balanced capability and cost"},
    {"id": "gpt-5.6-luna", "label": "GPT-5.6 Luna", "note": "efficient high-volume work"},
    {"id": "gpt-5.5", "label": "GPT-5.5", "note": "previous default"},
    {"id": "gpt-5.4", "label": "GPT-5.4", "note": "stable fallback"},
    {"id": "gpt-5.4-mini", "label": "GPT-5.4 mini", "note": "fast fallback"},
]
MODEL_ALIASES = {
    "gpt-5.6": DEFAULT_MODEL,
}
DEFAULT_RUNTIME_SETTINGS = {
    "permission": "notes",
    "model": DEFAULT_MODEL,
    "speed": "codex_config",
    "reasoningEffort": "codex_config",
    "proxyUrl": "",
    "aiBackend": "auto",
    "mnApiBackend": "auto",
    "codexCliPath": "",
    "defaultContextScope": "auto",
    "githubRepo": "LiuWhale/marginnote-assistant",
    "customButtons": [],
    "fileSearchRoots": [],
}
AI_BACKENDS = {"auto", "codex_cli", "openai_api", "local"}
MN_API_BACKENDS = {"auto", "native", "url_api"}
AI_BACKEND_LABELS = {
    "auto": "自动",
    "codex_cli": "Codex CLI",
    "openai_api": "OpenAI API",
    "local": "本地工具/诊断",
}
SPEED_MAX_OUTPUT_TOKENS = {
    "codex_config": 1200,
    "priority": 1200,
}
CODEX_CLI_TIMEOUTS = {
    "codex_config": None,
    "priority": None,
}
CODEX_CLI_LONG_TASK_TIMEOUT = None
CODEX_CLI_SERVICE_TIERS = {
    "codex_config": "",
    "priority": "priority",
}
REASONING_EFFORTS = {"codex_config", "low", "medium", "high", "xhigh", "max", "ultra"}
LEGACY_REASONING_ALIASES = {
    "fast": "medium",
    "balanced": "medium",
    "deep": "high",
}
CONTEXT_SCOPE_ALIASES = {
    "auto": "auto",
    "自动": "auto",
    "selection": "selection",
    "selected": "selection",
    "selected_only": "selection",
    "选区": "selection",
    "只看选区": "selection",
    "document": "document",
    "full": "document",
    "fulltext": "document",
    "full_text": "document",
    "全文": "document",
    "全文检索": "document",
    "当前文档": "document",
}
CUSTOM_BUTTON_ACTIONS = {
    "chat",
    "explain_selection",
    "generate_card",
    "generate_mindmap",
    "generate_full_reading",
    "expand_node",
    "reorganize_mindmap",
    "request_native_highlight_selection",
}


def sanitize_permission(value: Any) -> str:
    text = str(value or "").strip()
    if text in {"read_only", "notes", "full"}:
        return text
    return DEFAULT_RUNTIME_SETTINGS["permission"]


def sanitize_speed(value: Any) -> str:
    text = str(value or "").strip()
    if text == "fast":
        return "priority"
    if text in SPEED_MAX_OUTPUT_TOKENS:
        return text
    return DEFAULT_RUNTIME_SETTINGS["speed"]


def sanitize_reasoning_effort(value: Any) -> str:
    text = str(value or "").strip()
    if text in LEGACY_REASONING_ALIASES:
        return LEGACY_REASONING_ALIASES[text]
    if text in REASONING_EFFORTS:
        return text
    return DEFAULT_RUNTIME_SETTINGS["reasoningEffort"]


def sanitize_model(value: Any, fallback_model: str = DEFAULT_MODEL) -> str:
    text = str(value or "").strip()
    if text in MODEL_ALIASES:
        return MODEL_ALIASES[text]
    if not text:
        return fallback_model
    if not re.match(r"^[A-Za-z0-9._:-]{2,80}$", text):
        return fallback_model
    return text


def sanitize_proxy_url(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > 300 or any(char in text for char in "\r\n\t"):
        return ""
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        return ""
    if not parsed.netloc:
        return ""
    return text


def sanitize_github_repo(value: Any) -> str:
    fallback = DEFAULT_RUNTIME_SETTINGS["githubRepo"]
    text = str(value or "").strip()
    if not text:
        return fallback
    text = re.sub(r"^https?://github\.com/", "", text, flags=re.IGNORECASE)
    text = text.removeprefix("git@github.com:")
    text = text.removesuffix(".git")
    text = text.strip("/")
    parts = text.split("/")
    if len(parts) != 2:
        return fallback
    owner, repo = parts
    if not re.match(r"^[A-Za-z0-9][A-Za-z0-9-]{0,38}$", owner):
        return fallback
    if not re.match(r"^[A-Za-z0-9._-]{1,100}$", repo):
        return fallback
    return f"{owner}/{repo}"


def sanitize_ai_backend(value: Any) -> str:
    text = str(value or "").strip()
    if text in AI_BACKENDS:
        return text
    return DEFAULT_RUNTIME_SETTINGS["aiBackend"]


def sanitize_mn_api_backend(value: Any) -> str:
    text = str(value or "").strip()
    if text in MN_API_BACKENDS:
        return text
    return DEFAULT_RUNTIME_SETTINGS["mnApiBackend"]


def sanitize_default_context_scope(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return DEFAULT_RUNTIME_SETTINGS["defaultContextScope"]
    return CONTEXT_SCOPE_ALIASES.get(text, CONTEXT_SCOPE_ALIASES.get(text.lower(), "auto"))


def sanitize_codex_cli_path(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > 500 or any(char in text for char in "\r\n\t"):
        return ""
    return str(Path(text).expanduser())


def ai_backend_label(value: Any) -> str:
    return AI_BACKEND_LABELS.get(sanitize_ai_backend(value), AI_BACKEND_LABELS["auto"])


def sanitize_custom_buttons(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    buttons: list[dict[str, Any]] = []
    pinned_count = 0
    for item in value[:40]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()[:48]
        action = str(item.get("action") or "").strip()
        prompt = str(item.get("prompt") or "").strip()[:3000]
        if not title or not prompt or action not in CUSTOM_BUTTON_ACTIONS:
            continue
        show_on_main = bool(item.get("showOnMain")) and pinned_count < 6
        if show_on_main:
            pinned_count += 1
        buttons.append({"title": title, "action": action, "prompt": prompt, "showOnMain": show_on_main})
        if len(buttons) >= 20:
            break
    return buttons


def sanitize_file_search_roots(value: Any) -> list[str]:
    if isinstance(value, str):
        candidates = re.split(r"[\r\n]+", value)
    elif isinstance(value, list):
        candidates = value
    else:
        return []
    roots: list[str] = []
    seen: set[str] = set()
    for item in candidates[:80]:
        text = str(item or "").strip()
        if not text or any(char in text for char in "\r\n\t"):
            continue
        if len(text) > 1000:
            continue
        path = str(Path(text).expanduser())
        if path in seen:
            continue
        seen.add(path)
        roots.append(path)
        if len(roots) >= 40:
            break
    return roots


def sanitize_openai_api_key(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > 300 or any(char in text for char in "\r\n\t "):
        return ""
    if not re.match(r"^[A-Za-z0-9._:-]{12,300}$", text):
        return ""
    return text


def sanitize_mn_url_api_secret(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > 300 or any(char in text for char in "\r\n\t "):
        return ""
    if not re.match(r"^[A-Za-z0-9._:-]{8,300}$", text):
        return ""
    return text
