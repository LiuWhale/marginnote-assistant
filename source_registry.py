from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".codex/marginnote-assistant"
ACTION_RUNS_DIR = ROOT / "source-registry-runs"

SOURCE_REGISTRY_SCHEMA = "codex.mn.sourceRegistry.v1"
SOURCE_SOURCE_SCHEMA = "codex.mn.sourceRegistrySource.v1"
SOURCE_ACTION_PLAN_SCHEMA = "codex.mn.sourceRegistryActionPlan.v1"
SOURCE_ACTION_RUN_SCHEMA = "codex.mn.sourceRegistryActionRun.v1"


def configure(root: Path | str) -> None:
    global ROOT, ACTION_RUNS_DIR
    ROOT = Path(root).expanduser()
    ACTION_RUNS_DIR = ROOT / "source-registry-runs"


def _clean(value: Any, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _scope_key(topicid: str, bookmd5: str) -> str:
    raw = f"{topicid}|{bookmd5}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def _runs_path(topicid: str, bookmd5: str) -> Path:
    return ACTION_RUNS_DIR / f"{_scope_key(topicid, bookmd5)}.json"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


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


def _source(
    source_id: str,
    kind: str,
    title: str,
    *,
    path: str = "",
    readable: bool = False,
    status: str = "",
    detail: str = "",
    evidence: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema": SOURCE_SOURCE_SCHEMA,
        "id": source_id,
        "kind": kind,
        "title": title,
        "path": path,
        "readable": bool(readable),
        "status": status or ("ready" if readable else "missing"),
        "detail": detail,
        "evidence": [str(item) for item in (evidence or []) if str(item)],
        "metadata": metadata if isinstance(metadata, dict) else {},
    }


def _path_title(path: Any, fallback: str) -> str:
    text = _clean(path, 900)
    if not text:
        return fallback
    return Path(text).name or text


def _source_from_cache(item: dict[str, Any], index: int) -> dict[str, Any]:
    path = _clean(item.get("path") or item.get("cachePath") or item.get("pdfPath"), 900)
    readable = bool(item.get("readable") or item.get("ok"))
    return _source(
        f"pdf-cache:{index}",
        "pdf_cache",
        _path_title(path, "缓存 PDF"),
        path=path,
        readable=readable,
        status="ready" if readable else _clean(item.get("status"), 80) or "missing",
        detail=_clean(item.get("message") or item.get("detail"), 240),
        evidence=["pdf_cache_index"],
        metadata={
            "sha256": _clean(item.get("sha256"), 160),
            "size": int(item.get("size") or 0),
            "cached_at": _clean(item.get("cached_at") or item.get("cachedAt"), 120),
        },
    )


def _source_from_path(item: Any, index: int, kind: str, evidence: str) -> dict[str, Any]:
    if isinstance(item, dict):
        path = _clean(item.get("path") or item.get("pdfPath") or item.get("root"), 900)
        readable = bool(item.get("readable") or item.get("ok"))
        status = _clean(item.get("status"), 80) or ("ready" if readable else "missing")
        detail = _clean(item.get("message") or item.get("detail"), 240)
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
    else:
        path = _clean(item, 900)
        readable = Path(path).is_file() if path else False
        status = "ready" if readable else "missing"
        detail = ""
        metadata = {}
    return _source(
        f"{kind}:{index}",
        kind,
        _path_title(path, kind),
        path=path,
        readable=readable,
        status=status,
        detail=detail,
        evidence=[evidence],
        metadata=metadata,
    )


def build_action_plan(payload: dict[str, Any], registry: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    topicid = _clean(payload.get("topicid") or payload.get("topicId"), 200)
    bookmd5 = _clean(payload.get("bookmd5") or payload.get("bookMd5"), 200)
    document_title = _clean(payload.get("documentTitle") or payload.get("title"), 260)
    base_payload = {
        "topicid": topicid,
        "bookmd5": bookmd5,
        "documentTitle": document_title,
        "source": "source-registry",
    }
    actions = [
        {
            "id": "cache_current_pdf",
            "label": "缓存当前 PDF",
            "action": "request_pdf_cache",
            "payload": base_payload,
            "surface": "console",
            "tone": "primary" if registry.get("status") != "ready" else "secondary",
        },
        {
            "id": "choose_pdf_file",
            "label": "选择 PDF 文件",
            "action": "choose_pdf_cache_file",
            "payload": {**base_payload, "clientOnly": True},
            "surface": "source_registry",
            "tone": "secondary",
        },
        {
            "id": "manage_file_paths",
            "label": "管理文件路径",
            "action": "open_config_page",
            "payload": {**base_payload, "section": "file_paths", "clientOnly": True},
            "surface": "settings",
            "tone": "secondary",
        },
        {
            "id": "refresh_context",
            "label": "刷新上下文",
            "action": "refresh_context",
            "payload": {**base_payload, "clientOnly": True},
            "surface": "console",
            "tone": "secondary",
        },
    ]
    latest = latest_action_run(topicid, bookmd5)
    status = "ready" if registry.get("status") == "ready" else "action_required"
    recommended = actions[3] if status == "ready" else actions[0]
    return {
        "schema": SOURCE_ACTION_PLAN_SCHEMA,
        "status": status,
        "detail": "已有可读资料来源。" if status == "ready" else "缺少可读全文来源；建议先缓存当前 PDF 或选择本机文件。",
        "recommendedActionId": recommended["id"],
        "recommendedAction": recommended,
        "actionCount": len(actions),
        "actions": actions,
        "latestRun": latest,
    }


def build_registry(
    payload: dict[str, Any],
    *,
    caches: list[dict[str, Any]] | None = None,
    explicit_paths: list[Any] | None = None,
    uploads: list[Any] | None = None,
    roots: list[Any] | None = None,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    topicid = _clean(payload.get("topicid") or payload.get("topicId"), 200)
    bookmd5 = _clean(payload.get("bookmd5") or payload.get("bookMd5"), 200)
    document_title = _clean(payload.get("documentTitle") or payload.get("title"), 260)
    sources: list[dict[str, Any]] = []
    mn_document_source: dict[str, Any] = {}
    if topicid or bookmd5 or document_title:
        mn_document_source = _source(
            f"mn-document:{topicid or 'topic'}:{bookmd5 or 'book'}",
            "mn_document",
            document_title or bookmd5 or topicid or "当前 MN 文档",
            readable=False,
            status="ready",
            detail="MarginNote 当前文档元信息；全文可读性由 PDF 缓存、显式路径或上传材料证明。",
            evidence=[item for item in ["topicid" if topicid else "", "bookmd5" if bookmd5 else "", "documentTitle" if document_title else ""] if item],
            metadata={"topicid": topicid, "bookmd5": bookmd5, "documentTitle": document_title},
        )
    for index, item in enumerate(caches or [], start=1):
        if isinstance(item, dict):
            sources.append(_source_from_cache(item, index))
    for index, item in enumerate(explicit_paths or [], start=1):
        sources.append(_source_from_path(item, index, "explicit_pdf", "payload.pdfPath"))
    for index, item in enumerate(uploads or [], start=1):
        sources.append(_source_from_path(item, index, "upload", "upload_index"))
    for index, item in enumerate(roots or [], start=1):
        sources.append(_source_from_path(item, index, "file_search_root", "settings.fileSearchRoots"))
    if mn_document_source:
        sources.append(mn_document_source)
    readable_count = sum(1 for item in sources if item.get("readable"))
    status = "ready" if readable_count else "missing"
    gaps = []
    if not readable_count:
        gaps.append(
            {
                "id": "source_registry",
                "title": "缺少可读资料来源",
                "detail": "当前 MN 文档只有元信息；需要 PDF 缓存、显式路径、上传文件或可读搜索根。",
                "severity": "blocked",
            }
        )
    registry = {
        "schema": SOURCE_REGISTRY_SCHEMA,
        "status": status,
        "scope": {"topicid": topicid, "bookmd5": bookmd5, "documentTitle": document_title},
        "readableCount": readable_count,
        "sourceCount": len(sources),
        "summary": {
            "total": len(sources),
            "readable": readable_count,
            "cachedPdf": sum(1 for item in sources if item.get("kind") == "pdf_cache" and item.get("readable")),
            "uploads": sum(1 for item in sources if item.get("kind") == "upload"),
            "readableUploads": sum(1 for item in sources if item.get("kind") == "upload" and item.get("readable")),
            "searchRoots": sum(1 for item in sources if item.get("kind") == "file_search_root"),
            "explicitPdf": sum(1 for item in sources if item.get("kind") == "explicit_pdf" and item.get("readable")),
        },
        "sources": sources,
        "gaps": gaps,
        "latestRun": latest_action_run(topicid, bookmd5),
    }
    registry["actionPlan"] = build_action_plan(payload, registry)
    registry["sourceActions"] = registry["actionPlan"].get("actions", [])
    registry["primaryAction"] = registry["actionPlan"].get("recommendedAction") or {}
    return registry


def _run_store(topicid: str, bookmd5: str) -> dict[str, Any]:
    path = _runs_path(topicid, bookmd5)
    raw = _read_json(path, {})
    if not isinstance(raw, dict):
        raw = {}
    runs = raw.get("runs") if isinstance(raw.get("runs"), list) else []
    return {"schema": "codex.mn.sourceRegistryActionRuns.v1", "runs": [item for item in runs if isinstance(item, dict)]}


def _write_run_store(topicid: str, bookmd5: str, runs: list[dict[str, Any]]) -> None:
    _write_json(
        _runs_path(topicid, bookmd5),
        {
            "schema": "codex.mn.sourceRegistryActionRuns.v1",
            "topicid": topicid,
            "bookmd5": bookmd5,
            "updatedAt": _now(),
            "runs": runs[-200:],
        },
    )


def record_action_run(payload: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    topicid = _clean(payload.get("topicid") or payload.get("topicId"), 200)
    bookmd5 = _clean(payload.get("bookmd5") or payload.get("bookMd5"), 200)
    now = _now()
    run_id = _clean(payload.get("runId"), 120) or f"src_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    status = _clean(payload.get("status"), 80) or "running"
    store = _run_store(topicid, bookmd5)
    by_id = {str(item.get("runId") or ""): dict(item) for item in store["runs"]}
    previous = by_id.get(run_id, {})
    result = payload.get("result") if isinstance(payload.get("result"), dict) else {}
    run = {
        "schema": SOURCE_ACTION_RUN_SCHEMA,
        "runId": run_id,
        "status": status,
        "actionId": _clean(payload.get("actionId") or payload.get("id"), 120),
        "actionLabel": _clean(payload.get("actionLabel") or payload.get("label"), 160),
        "action": _clean(payload.get("action"), 120),
        "topicid": topicid,
        "bookmd5": bookmd5,
        "documentTitle": _clean(payload.get("documentTitle"), 260),
        "startedAt": _clean(payload.get("startedAt"), 120) or _clean(previous.get("startedAt"), 120) or now,
        "updatedAt": now,
        "event": _clean(payload.get("event"), 120) or status,
        "message": _clean(payload.get("message"), 500),
        "result": result,
    }
    by_id[run_id] = run
    runs = sorted(by_id.values(), key=lambda item: str(item.get("updatedAt") or ""), reverse=False)
    _write_run_store(topicid, bookmd5, runs)
    return {"ok": True, "sourceActionRun": run}


def latest_action_run(topicid: str, bookmd5: str) -> dict[str, Any]:
    runs = _run_store(_clean(topicid, 200), _clean(bookmd5, 200))["runs"]
    if not runs:
        return {}
    runs.sort(key=lambda item: str(item.get("updatedAt") or item.get("startedAt") or ""), reverse=True)
    return runs[0]
