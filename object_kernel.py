from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".codex/marginnote-assistant"
REGISTRY_DIR = ROOT / "mn-object-registry"

MN_OBJECT_SCHEMA = "codex.mn.mnObject.v1"
MN_OBJECT_REGISTRY_SCHEMA = "codex.mn.mnObjectRegistry.v1"
MN_OBJECT_REGISTRY_SCAN_SCHEMA = "codex.mn.mnObjectRegistryScan.v1"


def configure(root: Path | str) -> None:
    global ROOT, REGISTRY_DIR
    ROOT = Path(root).expanduser()
    REGISTRY_DIR = ROOT / "mn-object-registry"


def _clean_text(value: Any, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _first_text(payload: dict[str, Any], keys: list[str], limit: int = 500) -> str:
    for key in keys:
        text = _clean_text(payload.get(key), limit)
        if text:
            return text
    return ""


def _first_int(payload: dict[str, Any], keys: list[str]) -> int | None:
    for key in keys:
        value = payload.get(key)
        if value is None or value == "":
            continue
        try:
            return int(value)
        except (TypeError, ValueError):
            continue
    return None


def _digest(parts: list[Any], length: int = 16) -> str:
    raw = "|".join(str(part or "") for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:length]


def _scope_value(value: Any) -> str:
    text = _clean_text(value, 200)
    if not text:
        return "none"
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text)[:120] or "none"


def object_scope_key(topicid: str, bookmd5: str) -> str:
    return f"{_scope_value(topicid)}__{_scope_value(bookmd5)}"


def _registry_path(topicid: str, bookmd5: str) -> Path:
    return REGISTRY_DIR / f"{object_scope_key(topicid, bookmd5)}.json"


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


def _kind_from_payload(payload: dict[str, Any]) -> str:
    note_id = _first_text(payload, ["noteId", "noteid", "selectedNoteId"], 160)
    selection = _first_text(payload, ["selectionText", "selectedText", "activeSelectionText", "text"], 700)
    document_title = _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260)
    book_md5 = _first_text(payload, ["bookmd5", "bookMd5", "docmd5", "docMd5"], 200)
    if note_id:
        return "note"
    if selection:
        return "selection"
    if document_title or book_md5:
        return "document"
    return "unknown"


def _object_id(kind: str, identifiers: dict[str, Any], source_ref: dict[str, Any]) -> str:
    note_id = _clean_text(identifiers.get("noteId"), 160)
    if kind == "note" and note_id:
        return f"mnobj:note:{note_id}"
    topicid = _clean_text(identifiers.get("topicid"), 200)
    bookmd5 = _clean_text(identifiers.get("bookmd5"), 200)
    if kind == "document":
        digest = _digest([topicid, bookmd5, source_ref.get("documentTitle")])
        return f"mnobj:document:{digest}"
    if kind == "selection":
        digest = _digest([topicid, bookmd5, source_ref.get("page"), source_ref.get("quote")])
        return f"mnobj:selection:{digest}"
    return f"mnobj:unknown:{_digest([identifiers, source_ref])}"


def _relations(kind: str, identifiers: dict[str, Any], source_ref: dict[str, Any]) -> list[dict[str, str]]:
    relations: list[dict[str, str]] = []
    topicid = _clean_text(identifiers.get("topicid"), 200)
    bookmd5 = _clean_text(identifiers.get("bookmd5"), 200)
    parent_note_id = _clean_text(source_ref.get("parentNoteId"), 160)
    if topicid:
        relations.append({"type": "belongs_to", "targetKind": "notebook", "targetId": topicid})
    if bookmd5:
        relations.append({"type": "belongs_to", "targetKind": "document", "targetId": bookmd5})
    if kind == "note" and parent_note_id:
        relations.append({"type": "contains", "direction": "parent", "targetKind": "note", "targetId": parent_note_id})
    return relations


def build_object(payload: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    kind = _kind_from_payload(payload)
    identifiers = {
        "topicid": _first_text(payload, ["topicid", "topicId", "notebookid", "notebookId"], 200),
        "bookmd5": _first_text(payload, ["bookmd5", "bookMd5", "docmd5", "docMd5"], 200),
        "noteId": _first_text(payload, ["noteId", "noteid", "selectedNoteId"], 160),
    }
    source_ref = {
        "documentTitle": _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260),
        "quote": _first_text(payload, ["quote", "selectionText", "selectedText", "activeSelectionText", "text"], 900),
        "page": _first_int(payload, ["page", "pageNumber", "pageIndex"]),
        "path": _first_text(payload, ["pdfPath", "documentPath", "sourcePath", "filePath"], 900),
    }
    parent_note_id = _first_text(payload, ["parentNoteId", "parentId"], 160)
    if parent_note_id:
        source_ref["parentNoteId"] = parent_note_id
    node_path = _first_text(payload, ["path", "nodePath"], 400)
    if node_path:
        source_ref["nodePath"] = node_path
    title = (
        _first_text(payload, ["title", "selectedNoteTitle", "noteTitle", "documentTitle", "bookTitle"], 260)
        or source_ref.get("quote")
        or kind
    )
    obj = {
        "schema": MN_OBJECT_SCHEMA,
        "objectId": _object_id(kind, identifiers, source_ref),
        "kind": kind,
        "title": title,
        "identifiers": {key: value for key, value in identifiers.items() if value},
        "sourceRef": {key: value for key, value in source_ref.items() if value not in (None, "")},
        "relations": [],
        "permissionBoundary": "notes" if kind in {"note", "selection", "document"} else "read_only",
        "availableActions": [],
        "evidenceTypes": [],
    }
    obj["relations"] = _relations(kind, obj["identifiers"], obj["sourceRef"])
    return obj


def _registry_store(topicid: str, bookmd5: str) -> dict[str, Any]:
    path = _registry_path(topicid, bookmd5)
    raw = _read_json(path, {})
    if not isinstance(raw, dict):
        raw = {}
    objects = raw.get("objects") if isinstance(raw.get("objects"), list) else []
    return {
        "schema": MN_OBJECT_REGISTRY_SCHEMA,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "objects": [item for item in objects if isinstance(item, dict)],
    }


def _write_registry_store(topicid: str, bookmd5: str, objects: list[dict[str, Any]]) -> None:
    payload = {
        "schema": MN_OBJECT_REGISTRY_SCHEMA,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "updatedAt": _now(),
        "objects": objects,
    }
    _write_json(_registry_path(topicid, bookmd5), payload)


def register_object(obj: dict[str, Any], evidence_type: str = "observed") -> dict[str, Any]:
    obj = obj if isinstance(obj, dict) else {}
    identifiers = obj.get("identifiers") if isinstance(obj.get("identifiers"), dict) else {}
    topicid = _clean_text(identifiers.get("topicid"), 200)
    bookmd5 = _clean_text(identifiers.get("bookmd5"), 200)
    object_id = _clean_text(obj.get("objectId"), 240)
    if not object_id:
        obj = build_object(obj)
        identifiers = obj.get("identifiers") if isinstance(obj.get("identifiers"), dict) else {}
        topicid = _clean_text(identifiers.get("topicid"), 200)
        bookmd5 = _clean_text(identifiers.get("bookmd5"), 200)
        object_id = _clean_text(obj.get("objectId"), 240)
    store = _registry_store(topicid, bookmd5)
    now = _now()
    evidence = _clean_text(evidence_type, 120) or "observed"
    existing_by_id = {str(item.get("objectId") or ""): dict(item) for item in store["objects"]}
    current = existing_by_id.get(object_id, {})
    first_seen = _clean_text(current.get("firstSeen"), 80) or now
    evidence_types = set(current.get("evidenceTypes") if isinstance(current.get("evidenceTypes"), list) else [])
    evidence_types.update(obj.get("evidenceTypes") if isinstance(obj.get("evidenceTypes"), list) else [])
    evidence_types.add(evidence)
    seen_count = int(current.get("seenCount") or 0) + 1
    record = {
        **obj,
        "firstSeen": first_seen,
        "lastSeen": now,
        "seenCount": seen_count,
        "evidenceTypes": sorted(str(item) for item in evidence_types if str(item)),
    }
    existing_by_id[object_id] = record
    objects = sorted(existing_by_id.values(), key=lambda item: str(item.get("lastSeen") or ""), reverse=True)
    _write_registry_store(topicid, bookmd5, objects)
    return {"ok": True, "schema": MN_OBJECT_REGISTRY_SCHEMA, "object": record}


def ingest_native_scan(payload: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    topicid = _first_text(payload, ["topicid", "topicId", "notebookid", "notebookId"], 200)
    bookmd5 = _first_text(payload, ["bookmd5", "bookMd5", "docmd5", "docMd5"], 200)
    document_title = _first_text(payload, ["documentTitle", "docTitle", "bookTitle", "title"], 260)
    nodes = payload.get("nodes") if isinstance(payload.get("nodes"), list) else []
    ingested: list[dict[str, Any]] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        note_id = _first_text(node, ["noteId", "noteid", "id"], 160)
        if not note_id:
            continue
        obj = build_object(
            {
                "topicid": topicid,
                "bookmd5": bookmd5,
                "documentTitle": document_title,
                "noteId": note_id,
                "title": _first_text(node, ["title", "name"], 260) or note_id,
                "parentNoteId": _first_text(node, ["parentNoteId", "parentId"], 160),
                "path": _first_text(node, ["path", "nodePath"], 400),
            }
        )
        registered = register_object(obj, evidence_type="native_object_scan")
        ingested.append(registered["object"])
    return {
        "ok": True,
        "schema": MN_OBJECT_REGISTRY_SCAN_SCHEMA,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "ingestedCount": len(ingested),
        "objects": ingested,
    }


def registry_list(payload: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    topicid = _first_text(payload, ["topicid", "topicId", "notebookid", "notebookId"], 200)
    bookmd5 = _first_text(payload, ["bookmd5", "bookMd5", "docmd5", "docMd5"], 200)
    limit = 200
    try:
        limit = max(1, min(1000, int(payload.get("limit") or limit)))
    except (TypeError, ValueError):
        limit = 200
    store = _registry_store(topicid, bookmd5)
    objects = store["objects"][:limit]
    return {
        "ok": True,
        "schema": MN_OBJECT_REGISTRY_SCHEMA,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "total": len(store["objects"]),
        "objects": objects,
        "path": str(_registry_path(topicid, bookmd5)),
    }
