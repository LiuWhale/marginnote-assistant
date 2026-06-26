from __future__ import annotations

import json
import re
import subprocess
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import quote, urlencode


URL_API_PREFIX = "marginnote4app://addon/api"
URL_API_ACTIONS = {"ping", "read", "ls", "find", "tree", "write", "delete"}
MN_API_BACKENDS = {"auto", "native", "url_api"}
MN_API_BACKEND_LABELS = {
    "auto": "自动",
    "native": "MN4 原生",
    "url_api": "URL API Gateway",
}


@dataclass(frozen=True)
class URLApiRequest:
    url: str
    redacted_url: str
    request_id: str
    action: str
    payload: dict[str, Any]


def sanitize_mn_api_backend(value: Any) -> str:
    text = str(value or "").strip()
    if text in MN_API_BACKENDS:
        return text
    return "auto"


def mn_api_backend_label(value: Any) -> str:
    return MN_API_BACKEND_LABELS.get(sanitize_mn_api_backend(value), MN_API_BACKEND_LABELS["auto"])


def sanitize_url_api_secret(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    if len(text) > 300 or any(char in text for char in "\r\n\t "):
        return ""
    if not re.match(r"^[A-Za-z0-9._:-]{8,300}$", text):
        return ""
    return text


def generate_request_id(prefix: str = "req_codex") -> str:
    return f"{prefix}_{int(time.time() * 1000)}_{uuid.uuid4().hex[:10]}"


def normalize_callback_base_url(callback_base_url: str) -> str:
    text = str(callback_base_url or "").strip().rstrip("/")
    if not text:
        return ""
    if not re.match(r"^https?://", text, re.IGNORECASE):
        raise ValueError("callback_base_url must be http or https")
    return text


def redact_secret_from_url(url: str) -> str:
    return re.sub(r"([?&]secret=)([^&#]*)", r"\1[REDACTED]", url)


def build_url_api_request(
    action: str,
    secret: str,
    payload: dict[str, Any] | None = None,
    callback_base_url: str = "",
    request_id: str = "",
) -> URLApiRequest:
    action = str(action or "").strip()
    if action not in URL_API_ACTIONS:
        raise ValueError(f"Unsupported MarginNote URL API action: {action}")
    secret = sanitize_url_api_secret(secret)
    if not secret:
        raise ValueError("Missing MarginNote URL API secret")
    clean_payload = payload if isinstance(payload, dict) else {}
    request_id = str(request_id or "").strip() or generate_request_id()
    params: list[tuple[str, str]] = [
        ("requestId", request_id),
        ("action", action),
        ("secret", secret),
    ]
    callback_base = normalize_callback_base_url(callback_base_url)
    if callback_base:
        params.append(("x-success", f"{callback_base}/success"))
        params.append(("x-error", f"{callback_base}/error"))
    if clean_payload:
        params.append(("payload", quote(json.dumps(clean_payload, ensure_ascii=False, separators=(",", ":")))))
    query = urlencode(params, safe="%:/")
    url = f"{URL_API_PREFIX}?{query}"
    return URLApiRequest(
        url=url,
        redacted_url=redact_secret_from_url(url),
        request_id=request_id,
        action=action,
        payload=clean_payload,
    )


def adapter_status(settings: dict[str, Any] | None = None, url_api_secret: str = "") -> dict[str, Any]:
    settings = settings if isinstance(settings, dict) else {}
    backend = sanitize_mn_api_backend(settings.get("mnApiBackend"))
    configured = bool(sanitize_url_api_secret(url_api_secret))
    native_available = True
    url_api_available = configured
    available = bool(native_available if backend in {"auto", "native"} else url_api_available)
    return {
        "backend": backend,
        "backendLabel": mn_api_backend_label(backend),
        "available": available,
        "nativeAvailable": native_available,
        "urlApiConfigured": configured,
        "urlApiAvailable": url_api_available,
        "actions": sorted(URL_API_ACTIONS),
    }


def open_url(url: str, opener: Callable[[list[str]], Any] | None = None) -> dict[str, Any]:
    if not str(url or "").startswith(URL_API_PREFIX):
        return {"ok": False, "message": "只允许打开 MarginNote URL API 请求。"}
    runner = opener or subprocess.run
    result = runner(["/usr/bin/open", url])
    return {
        "ok": True,
        "message": "已打开 MarginNote URL API 请求。",
        "returncode": getattr(result, "returncode", 0),
        "redactedUrl": redact_secret_from_url(url),
    }
