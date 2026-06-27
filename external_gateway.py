from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path.home() / ".codex/marginnote-assistant"
REQUESTS_DIR = ROOT / "external-gateway"

EXTERNAL_REQUEST_SCHEMA = "codex.mn.externalGatewayRequest.v1"
AGENT_OPERATION_SCHEMA = "codex.mn.agentOperation.v1"

ALLOWED_ACTIONS = {
    "ping",
    "read",
    "ls",
    "find",
    "tree",
    "workflow_start",
    "agent_operation",
}
DIRECT_WRITE_ACTIONS = {"write", "delete", "patch", "create_note", "create_card", "mindmap_write"}
SECRET_QUERY_KEYS = {"secret", "token", "api_key", "apikey", "key", "authorization", "auth"}


def configure(root: Path | str) -> None:
    global ROOT, REQUESTS_DIR
    ROOT = Path(root).expanduser()
    REQUESTS_DIR = ROOT / "external-gateway"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _clean_id(value: Any) -> str:
    text = str(value or "").strip()
    clean = re.sub(r"[^A-Za-z0-9._-]", "", text)[:120]
    return clean or f"ext_{uuid.uuid4().hex[:16]}"


def _clean_text(value: Any, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _request_path(request_id: str) -> Path:
    return REQUESTS_DIR / f"{_clean_id(request_id)}.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _sanitize_url(value: Any) -> str:
    text = _clean_text(value, 2000)
    if not text:
        return ""
    try:
        parts = urlsplit(text)
    except Exception:
        return ""
    query = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in SECRET_QUERY_KEYS]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def _callback(payload: dict[str, Any]) -> dict[str, Any]:
    success = _sanitize_url(payload.get("x-success") or payload.get("xSuccess") or payload.get("successCallback"))
    error_url = _sanitize_url(payload.get("x-error") or payload.get("xError") or payload.get("errorCallback"))
    callback = payload.get("callback") if isinstance(payload.get("callback"), dict) else {}
    success = success or _sanitize_url(callback.get("success"))
    error_url = error_url or _sanitize_url(callback.get("error"))
    return {
        "success": success,
        "error": error_url,
        "status": "pending" if (success or error_url) else "not_configured",
    }


def _payload(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("payload")
    if isinstance(value, dict):
        return dict(value)
    return {}


def _object_ref(payload: dict[str, Any], body: dict[str, Any]) -> dict[str, Any]:
    ref = payload.get("objectRef") if isinstance(payload.get("objectRef"), dict) else body.get("objectRef")
    if not isinstance(ref, dict):
        return {}
    return {
        "objectId": _clean_text(ref.get("objectId"), 240),
        "kind": _clean_text(ref.get("kind"), 80),
        "title": _clean_text(ref.get("title"), 240),
        "sourceRef": ref.get("sourceRef") if isinstance(ref.get("sourceRef"), dict) else {},
    }


def _normalized_request(payload: dict[str, Any], action: str, body: dict[str, Any]) -> dict[str, Any]:
    now = _now()
    request_id = _clean_id(payload.get("requestId") or payload.get("_request_id") or payload.get("id"))
    caller = _clean_text(payload.get("caller") or payload.get("source") or "external", 120)
    workflow_id = _clean_text(payload.get("workflowId") or body.get("workflowId"), 120)
    object_ref = _object_ref(payload, body)
    return {
        "schema": EXTERNAL_REQUEST_SCHEMA,
        "requestId": request_id,
        "caller": caller or "external",
        "action": action,
        "requestedAction": action,
        "workflowId": workflow_id,
        "topicid": _clean_text(payload.get("topicid"), 160),
        "bookmd5": _clean_text(payload.get("bookmd5"), 160),
        "objectRef": object_ref,
        "payload": body,
        "callback": _callback(payload),
        "stage": "received",
        "result": {},
        "createdAt": now,
        "updatedAt": now,
    }


def _agent_operation(request_record: dict[str, Any]) -> dict[str, Any]:
    request_id = str(request_record.get("requestId") or "")
    operation_type = str(request_record.get("action") or "agent_operation")
    payload = request_record.get("payload") if isinstance(request_record.get("payload"), dict) else {}
    return {
        "schema": AGENT_OPERATION_SCHEMA,
        "operationId": f"agentop:{request_id}",
        "type": operation_type,
        "status": "accepted",
        "external": {
            "requestId": request_id,
            "caller": str(request_record.get("caller") or "external"),
            "action": operation_type,
            "callback": request_record.get("callback") if isinstance(request_record.get("callback"), dict) else {},
        },
        "objectRef": request_record.get("objectRef") if isinstance(request_record.get("objectRef"), dict) else {},
        "payload": payload,
        "createdAt": str(request_record.get("createdAt") or ""),
    }


def normalize_request(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload) if isinstance(payload, dict) else {}
    action = _clean_text(payload.get("action") or payload.get("requestedAction") or "workflow_start", 80).lower()
    if action in DIRECT_WRITE_ACTIONS:
        return {
            "ok": False,
            "code": "DIRECT_WRITE_FORBIDDEN",
            "message": "外部自动化不能直接写入或删除 MarginNote 内容；请启动需要确认的 workflow 或 agent_operation。",
            "requestId": _clean_id(payload.get("requestId") or payload.get("_request_id") or payload.get("id")),
        }
    if action not in ALLOWED_ACTIONS:
        return {
            "ok": False,
            "code": "UNSUPPORTED_EXTERNAL_ACTION",
            "message": f"不支持的外部自动化动作：{action or 'unknown'}。",
            "requestId": _clean_id(payload.get("requestId") or payload.get("_request_id") or payload.get("id")),
        }
    body = _payload(payload)
    request_record = _normalized_request(payload, action, body)
    return {
        "ok": True,
        "code": "OK",
        "message": "外部自动化请求已规范化。",
        "externalGatewayRequest": request_record,
        "agentOperation": _agent_operation(request_record),
    }


def _sanitize_record(record: dict[str, Any]) -> dict[str, Any]:
    record = dict(record) if isinstance(record, dict) else {}
    record.pop("secret", None)
    record["schema"] = str(record.get("schema") or EXTERNAL_REQUEST_SCHEMA)
    record["requestId"] = _clean_id(record.get("requestId") or record.get("_request_id") or record.get("id"))
    record["caller"] = _clean_text(record.get("caller") or record.get("source") or "external", 120)
    if isinstance(record.get("callback"), dict):
        callback = dict(record["callback"])
        callback["success"] = _sanitize_url(callback.get("success"))
        callback["error"] = _sanitize_url(callback.get("error"))
        callback["status"] = _clean_text(callback.get("status") or ("pending" if callback.get("success") or callback.get("error") else "not_configured"), 80)
        record["callback"] = callback
    else:
        record["callback"] = {"success": "", "error": "", "status": "not_configured"}
    record["updatedAt"] = _now()
    if not record.get("createdAt"):
        record["createdAt"] = record["updatedAt"]
    return record


def record_request(record: dict[str, Any]) -> dict[str, Any]:
    stored = _sanitize_record(record)
    _write_json(_request_path(str(stored.get("requestId") or "")), stored)
    return {"ok": True, "message": "已记录外部自动化请求。", "externalGateway": stored}


def request_status(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload) if isinstance(payload, dict) else {}
    request_id = _clean_id(payload.get("requestId") or payload.get("id") or "")
    record = _read_json(_request_path(request_id), {})
    if not isinstance(record, dict) or not record:
        return {"ok": False, "message": "未找到外部自动化请求。", "requestId": request_id}
    return {"ok": True, "message": "已读取外部自动化请求。", "externalGateway": _sanitize_record(record)}


def update_callback(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload) if isinstance(payload, dict) else {}
    request_id = _clean_id(payload.get("requestId") or payload.get("id") or "")
    path = _request_path(request_id)
    record = _read_json(path, {})
    if not isinstance(record, dict) or not record:
        return {"ok": False, "message": "未找到外部自动化请求，无法记录回调。", "requestId": request_id}

    raw_status = _clean_text(payload.get("callbackStatus") or payload.get("status"), 80).lower()
    if raw_status in {"ok", "done", "complete", "completed", "success"}:
        callback_status = "success"
    elif raw_status in {"fail", "failed", "failure", "error"}:
        callback_status = "error"
    else:
        callback_status = "unknown"

    callback_payload = payload.get("payload")
    if callback_payload is None:
        callback_payload = payload.get("result") if "result" in payload else {}
    if not isinstance(callback_payload, dict):
        callback_payload = {"value": callback_payload}

    callback = record.get("callback") if isinstance(record.get("callback"), dict) else {}
    history = callback.get("history") if isinstance(callback.get("history"), list) else []
    now = _now()
    event = {
        "status": callback_status,
        "message": _clean_text(payload.get("message"), 500),
        "payload": callback_payload,
        "receivedAt": now,
    }
    record["callback"] = {
        **callback,
        "success": _sanitize_url(callback.get("success")),
        "error": _sanitize_url(callback.get("error")),
        "status": callback_status,
        "message": event["message"],
        "payload": callback_payload,
        "receivedAt": now,
        "receivedCount": len(history) + 1,
        "history": [*history, event],
    }
    record["stage"] = f"callback_{callback_status}" if callback_status in {"success", "error"} else "callback_received"
    result = record.get("result") if isinstance(record.get("result"), dict) else {}
    record["result"] = {**result, "callbackStatus": callback_status, "callbackMessage": event["message"]}
    return record_request(record)
