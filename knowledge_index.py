from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any


_ROOT = Path.home() / ".codex/marginnote-assistant"
_INDEX_DIR = _ROOT / "indexes"
_INDEX_PATH = _INDEX_DIR / "knowledge.jsonl"


def configure(root: Path | str) -> None:
    global _ROOT, _INDEX_DIR, _INDEX_PATH
    _ROOT = Path(root).expanduser()
    _INDEX_DIR = _ROOT / "indexes"
    _INDEX_PATH = _INDEX_DIR / "knowledge.jsonl"


def _clean(value: Any, limit: int = 5000) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _entry_id(entry: dict[str, Any]) -> str:
    raw = "|".join(
        [
            str(entry.get("topicid") or ""),
            str(entry.get("bookmd5") or ""),
            str(entry.get("kind") or ""),
            str(entry.get("entityType") or ""),
            str(entry.get("noteId") or ""),
            str(entry.get("title") or ""),
            str(entry.get("text") or "")[:500],
        ]
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _read_entries() -> list[dict[str, Any]]:
    if not _INDEX_PATH.exists():
        return []
    entries: list[dict[str, Any]] = []
    try:
        with _INDEX_PATH.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    entries.append(item)
    except OSError:
        return []
    return entries


def _write_entries(entries: list[dict[str, Any]]) -> None:
    _INDEX_DIR.mkdir(parents=True, exist_ok=True)
    with _INDEX_PATH.open("w", encoding="utf-8") as handle:
        for entry in entries[-5000:]:
            handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def ingest_entry(
    *,
    kind: str,
    title: str,
    text: str,
    topicid: str = "",
    bookmd5: str = "",
    source: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "kind": _clean(kind, 80) or "context",
        "title": _clean(title, 200) or "未命名索引项",
        "text": _clean(text, 12000),
        "topicid": _clean(topicid, 120),
        "bookmd5": _clean(bookmd5, 120),
        "source": _clean(source, 120),
        "metadata": metadata if isinstance(metadata, dict) else {},
    }
    clean_entry["id"] = _entry_id(clean_entry)
    if not clean_entry["text"]:
        return {"ok": False, "message": "索引内容为空。"}
    entries = _read_entries()
    entries = [entry for entry in entries if entry.get("id") != clean_entry["id"]]
    entries.append(clean_entry)
    _write_entries(entries)
    return {"ok": True, "message": "已写入知识索引。", "entry": clean_entry, "count": len(entries)}


def _source_ref(entity: dict[str, Any]) -> dict[str, Any]:
    source = entity.get("source") if isinstance(entity.get("source"), dict) else {}
    page = entity.get("page", source.get("page"))
    quote = entity.get("quote", source.get("quote"))
    link = entity.get("link", source.get("link"))
    document_title = entity.get("documentTitle", source.get("documentTitle"))
    ref: dict[str, Any] = {}
    if page not in (None, ""):
        try:
            ref["page"] = int(page)
        except Exception:
            ref["page"] = _clean(page, 40)
    if quote:
        ref["quote"] = _clean(quote, 1000)
    if link:
        ref["link"] = _clean(link, 500)
    if document_title:
        ref["documentTitle"] = _clean(document_title, 240)
    return ref


def _relations(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, str]] = []
    for item in raw[:60]:
        if not isinstance(item, dict):
            continue
        relation = {
            "type": _clean(item.get("type") or item.get("relation") or "", 80),
            "targetNoteId": _clean(item.get("targetNoteId") or item.get("target_note_id") or "", 160),
            "targetId": _clean(item.get("targetId") or item.get("target_id") or "", 160),
            "label": _clean(item.get("label") or item.get("title") or "", 200),
        }
        if any(relation.values()):
            out.append(relation)
    return out


def ingest_entities(
    entities: list[dict[str, Any]],
    *,
    topicid: str = "",
    bookmd5: str = "",
    source: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if not isinstance(entities, list) or not entities:
        return {"ok": False, "message": "实体列表为空。", "entityCount": 0}
    base_metadata = metadata if isinstance(metadata, dict) else {}
    entries = _read_entries()
    by_id = {str(entry.get("id") or ""): entry for entry in entries if isinstance(entry, dict)}
    written: list[dict[str, Any]] = []
    for raw in entities[:500]:
        if not isinstance(raw, dict):
            continue
        entity_type = _clean(raw.get("entityType") or raw.get("entity_type") or raw.get("kind") or raw.get("type"), 80) or "entity"
        title = _clean(raw.get("title") or raw.get("name") or raw.get("noteTitle"), 220) or "未命名实体"
        text = _clean(raw.get("text") or raw.get("body") or raw.get("summary") or raw.get("quote") or title, 12000)
        if not text:
            continue
        source_ref = _source_ref(raw)
        note_id = _clean(raw.get("noteId") or raw.get("note_id") or raw.get("id"), 180)
        entry_metadata = dict(base_metadata)
        for key in ("documentTitle", "contextScope", "selectedNoteId"):
            if raw.get(key) and key not in entry_metadata:
                entry_metadata[key] = _clean(raw.get(key), 500)
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "kind": entity_type,
            "entityType": entity_type,
            "title": title,
            "text": text,
            "topicid": _clean(topicid, 120),
            "bookmd5": _clean(bookmd5, 120),
            "source": _clean(source or raw.get("sourceName") or "marginnote-entity", 120),
            "noteId": note_id,
            "sourceRef": source_ref,
            "relations": _relations(raw.get("relations")),
            "metadata": entry_metadata,
        }
        entry["id"] = _entry_id(entry)
        by_id[entry["id"]] = entry
        written.append(entry)
    if not written:
        return {"ok": False, "message": "没有可写入的结构化实体。", "entityCount": 0}
    _write_entries(list(by_id.values()))
    return {
        "ok": True,
        "message": f"已写入结构化知识实体 {len(written)} 条。",
        "entityCount": len(written),
        "entries": written,
        "count": len(by_id),
    }


def _matches_scope(entry: dict[str, Any], topicid: str = "", bookmd5: str = "") -> bool:
    if topicid and str(entry.get("topicid") or "") != str(topicid):
        return False
    if bookmd5 and str(entry.get("bookmd5") or "") != str(bookmd5):
        return False
    return True


def status(topicid: str = "", bookmd5: str = "") -> dict[str, Any]:
    entries = [entry for entry in _read_entries() if _matches_scope(entry, topicid, bookmd5)]
    kinds: dict[str, int] = {}
    entity_types: dict[str, int] = {}
    for entry in entries:
        kind = str(entry.get("kind") or "unknown")
        kinds[kind] = kinds.get(kind, 0) + 1
        entity_type = str(entry.get("entityType") or "")
        if entity_type:
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
    return {
        "ok": True,
        "message": f"知识索引：{len(entries)} 条。",
        "count": len(entries),
        "kinds": kinds,
        "entityTypes": entity_types,
        "path": str(_INDEX_PATH),
    }


def _tokens(query: str) -> list[str]:
    value = str(query or "").lower()
    tokens = [token for token in re.split(r"[^0-9a-zA-Z\u4e00-\u9fff]+", value) if token]
    return sorted(set(tokens), key=len, reverse=True)[:20]


def search(query: str, *, topicid: str = "", bookmd5: str = "", limit: int = 8) -> dict[str, Any]:
    tokens = _tokens(query)
    if not tokens:
        return {"ok": False, "message": "缺少搜索关键词。", "matches": []}
    phrase = str(query or "").strip().lower()
    scored: list[tuple[int, dict[str, Any]]] = []
    for entry in _read_entries():
        if not _matches_scope(entry, topicid, bookmd5):
            continue
        source_ref = entry.get("sourceRef") if isinstance(entry.get("sourceRef"), dict) else {}
        relations = entry.get("relations") if isinstance(entry.get("relations"), list) else []
        relation_text = " ".join(
            " ".join(str(value or "") for value in relation.values())
            for relation in relations
            if isinstance(relation, dict)
        )
        haystack = (
            f"{entry.get('title') or ''}\n{entry.get('text') or ''}\n"
            f"{entry.get('entityType') or ''}\n{entry.get('noteId') or ''}\n"
            f"{source_ref.get('quote') or ''}\n{relation_text}"
        ).lower()
        score = 0
        if phrase and phrase in haystack:
            score += 12
        if phrase and phrase in str(entry.get("title") or "").lower():
            score += 8
        for token in tokens:
            if token in haystack:
                score += 5 if token in str(entry.get("title") or "").lower() else 2
                score += min(haystack.count(token), 5)
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda item: (item[0], str(item[1].get("ts") or "")), reverse=True)
    matches = []
    for score, entry in scored[: max(1, min(int(limit or 8), 20))]:
        text = str(entry.get("text") or "")
        matches.append(
            {
                "id": entry.get("id"),
                "score": score,
                "kind": entry.get("kind"),
                "title": entry.get("title"),
                "snippet": _clean(text, 420),
                "topicid": entry.get("topicid"),
                "bookmd5": entry.get("bookmd5"),
                "source": entry.get("source"),
                "entityType": entry.get("entityType") or entry.get("kind"),
                "noteId": entry.get("noteId"),
                "sourceRef": entry.get("sourceRef") if isinstance(entry.get("sourceRef"), dict) else {},
                "relations": entry.get("relations") if isinstance(entry.get("relations"), list) else [],
                "ts": entry.get("ts"),
            }
        )
    return {
        "ok": True,
        "message": f"知识索引命中 {len(matches)} 条。",
        "query": query,
        "matches": matches,
    }


def clear(topicid: str = "", bookmd5: str = "") -> dict[str, Any]:
    entries = _read_entries()
    kept = [entry for entry in entries if not _matches_scope(entry, topicid, bookmd5)]
    removed = len(entries) - len(kept)
    _write_entries(kept)
    return {"ok": True, "message": f"已清除知识索引 {removed} 条。", "removed": removed}
