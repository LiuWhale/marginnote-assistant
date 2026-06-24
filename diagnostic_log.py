from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any


DEFAULT_MAX_LINES = 1000
_LOG_PATH = Path(os.environ.get("CODEX_MN_COMPANION_HOME", Path.home() / ".codex/marginnote-assistant")).expanduser() / "logs/diagnostics.jsonl"
_MAX_LINES = DEFAULT_MAX_LINES

SENSITIVE_LOG_KEYS = {
    "apikey",
    "api_key",
    "authorization",
    "filecontent",
    "openaiapikey",
    "password",
    "pdfbase64",
    "secret",
    "token",
}
LARGE_LOG_KEYS = {"cards", "content", "edittext", "history", "messages", "mindmap", "reply"}


def configure(path: Path, *, max_lines: int = DEFAULT_MAX_LINES) -> None:
    global _LOG_PATH, _MAX_LINES
    _LOG_PATH = Path(path).expanduser()
    _MAX_LINES = max(1, int(max_lines or DEFAULT_MAX_LINES))


def log_path() -> Path:
    return _LOG_PATH


def diagnostic_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def sanitize_diagnostic_value(key: str, value: Any, depth: int = 0) -> Any:
    key_lower = str(key or "").replace("_", "").lower()
    if any(sensitive in key_lower for sensitive in SENSITIVE_LOG_KEYS):
        return "[redacted]"
    if key_lower in LARGE_LOG_KEYS:
        if isinstance(value, str):
            return {"chars": len(value), "preview": value[:160]}
        if isinstance(value, list):
            return {"items": len(value)}
        if isinstance(value, dict):
            return {"keys": sorted(str(item) for item in value.keys())[:16]}
        return "[omitted]"
    if depth >= 3:
        return "[max-depth]"
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for index, (child_key, child_value) in enumerate(value.items()):
            if index >= 50:
                output["..."] = f"{len(value) - index} more keys"
                break
            output[str(child_key)] = sanitize_diagnostic_value(str(child_key), child_value, depth + 1)
        return output
    if isinstance(value, list):
        output_list = [sanitize_diagnostic_value(key, item, depth + 1) for item in value[:20]]
        if len(value) > 20:
            output_list.append(f"... {len(value) - 20} more items")
        return output_list
    if isinstance(value, str):
        if len(value) > 500:
            return value[:500] + f"... [{len(value)} chars]"
        return value
    if isinstance(value, (bool, int, float)) or value is None:
        return value
    return str(value)[:500]


def sanitize_diagnostic_payload(payload: Any) -> Any:
    return sanitize_diagnostic_value("payload", payload)


def prune_diagnostic_log() -> None:
    try:
        if not _LOG_PATH.exists():
            return
        lines = _LOG_PATH.read_text(encoding="utf-8").splitlines()
        if len(lines) <= _MAX_LINES:
            return
        _LOG_PATH.write_text(
            "\n".join(lines[-_MAX_LINES:]) + "\n",
            encoding="utf-8",
        )
    except Exception:
        return


def append_diagnostic_log(
    level: str,
    event: str,
    message: str = "",
    *,
    payload: Any | None = None,
    extra: Any | None = None,
    request_id: str = "",
) -> dict[str, Any]:
    record = {
        "ts": diagnostic_timestamp(),
        "pid": os.getpid(),
        "level": str(level or "info"),
        "event": str(event or ""),
        "requestId": str(request_id or ""),
        "message": str(message or "")[:800],
    }
    if payload is not None:
        record["payload"] = sanitize_diagnostic_payload(payload)
    if extra is not None:
        record["extra"] = sanitize_diagnostic_payload(extra)
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    prune_diagnostic_log()
    return record


def read_recent_diagnostic_logs(limit: int = 80) -> list[dict[str, Any]]:
    safe_limit = max(1, min(int(limit or 80), 300))
    if not _LOG_PATH.exists():
        return []
    try:
        lines = _LOG_PATH.read_text(encoding="utf-8").splitlines()[-safe_limit:]
    except Exception:
        return []
    logs: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            logs.append(item)
    return logs


def clear_diagnostic_logs() -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LOG_PATH.write_text("", encoding="utf-8")
