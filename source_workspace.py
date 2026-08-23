from __future__ import annotations

import hashlib
import json
import os
import re
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".codex/marginnote-assistant"
SOURCE_WORKSPACES_DIR = ROOT / "control" / "source-workspaces"
SOURCE_WORKSPACE_SCHEMA = "codex.mn.sourceWorkspace.v1"


def configure(root: Path | str) -> None:
    global ROOT, SOURCE_WORKSPACES_DIR
    ROOT = Path(root).expanduser()
    SOURCE_WORKSPACES_DIR = ROOT / "control" / "source-workspaces"


def safe_conversation_id(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return text[:120]


def workspace_path(conversation_id: str) -> Path:
    safe_id = safe_conversation_id(conversation_id)
    if not safe_id:
        raise ValueError("missing valid conversationId")
    return SOURCE_WORKSPACES_DIR / safe_id


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _canonical_file(value: object, label: str) -> tuple[Path | None, str]:
    raw = str(value or "").strip()
    if not raw:
        return None, f"{label} is missing"
    path = Path(raw).expanduser()
    try:
        canonical = path.resolve(strict=False)
        stat = canonical.stat()
    except OSError as exc:
        return None, f"{label} cannot be inspected: {exc}"
    if not canonical.is_file() or not os.path.isfile(canonical):
        return None, f"{label} is not a regular file"
    if not os.access(canonical, os.R_OK):
        return None, f"{label} is not readable"
    if stat.st_size < 0:
        return None, f"{label} is invalid"
    return canonical, ""


def _slug(value: object, fallback: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return (text[:80] or fallback)[:80]


def _json_write(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _workspace_owned_entries(path: Path) -> list[Path]:
    if not path.exists() and not path.is_symlink():
        return []
    if path.is_symlink() or not path.is_dir():
        raise ValueError("workspace root is not a managed directory")
    manifest_path = path / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("workspace manifest is missing or not a regular file")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError(f"workspace manifest is invalid: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_WORKSPACE_SCHEMA:
        raise ValueError("workspace manifest schema is invalid")

    top_entries = {child.name for child in path.iterdir()}
    if top_entries != {"manifest.json", "SOURCES.md", "files", "text"}:
        raise ValueError("workspace contains unrecognized content")
    for directory_name in ("files", "text"):
        directory = path / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"workspace {directory_name} is not a managed directory")

    expected_links: set[Path] = set()
    for source in manifest.get("sources", []):
        if not isinstance(source, dict):
            raise ValueError("workspace manifest contains an invalid source")
        for field, directory_name in (("fileLink", "files"), ("textLink", "text")):
            relative = str(source.get(field) or "")
            if not relative:
                continue
            relative_path = Path(relative)
            if relative_path.is_absolute() or relative_path.parts[:1] != (directory_name,) or len(relative_path.parts) != 2:
                raise ValueError("workspace manifest contains an invalid managed link")
            expected_links.add(relative_path)
    actual_links = {
        Path(directory_name) / child.name
        for directory_name in ("files", "text")
        for child in (path / directory_name).iterdir()
    }
    if actual_links != expected_links:
        raise ValueError("workspace contains unrecognized content")
    for relative in expected_links:
        if not (path / relative).is_symlink():
            raise ValueError("workspace contains a non-symlink managed link")
    sources_file = path / "SOURCES.md"
    if sources_file.is_symlink() or not sources_file.is_file():
        raise ValueError("workspace SOURCES.md is missing or not a regular file")
    return [manifest_path, sources_file, path / "files", path / "text", *[path / relative for relative in sorted(expected_links)]]


def _remove_owned_tree(path: Path) -> None:
    entries = _workspace_owned_entries(path)
    if not entries:
        return
    for entry in entries:
        if entry.is_symlink() or entry.is_file():
            entry.unlink()
    (path / "files").rmdir()
    (path / "text").rmdir()
    path.rmdir()


def _normal_source(source: dict[str, Any], index: int) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    if not isinstance(source, dict):
        return None, [f"source {index + 1} is not an object"]
    source_id = str(source.get("id") or "").strip()
    if not source_id:
        errors.append(f"source {index + 1} has no id")
    title = str(source.get("title") or "").strip()
    kind = str(source.get("kind") or "").strip()
    path, path_error = _canonical_file(source.get("path"), f"source {source_id or index + 1} path")
    if path_error:
        errors.append(path_error)
    text_path: Path | None = None
    if source.get("textPath"):
        text_path, text_error = _canonical_file(source.get("textPath"), f"source {source_id or index + 1} textPath")
        if text_error:
            errors.append(text_error)
    if errors or path is None:
        return None, errors
    display_name = title or path.name
    normalized = {
        "sourceId": source_id,
        "displayName": display_name,
        "kind": kind,
        "originalPath": str(path),
        "textOriginalPath": str(text_path) if text_path else "",
        "sha256": str(source.get("sha256") or ""),
        "pageCount": source.get("pageCount") if source.get("pageCount") is not None else None,
        "truncated": bool(source.get("truncated", False)),
    }
    return normalized, []


def _revision(records: list[dict[str, Any]], follow_current_document: bool) -> str:
    payload = {"followCurrentDocument": bool(follow_current_document), "sources": records}
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _result(manifest: dict[str, Any], ok: bool, errors: list[str] | None = None) -> dict[str, Any]:
    result = dict(manifest)
    result.update({"ok": ok, "errors": list(errors or []), "sourceCount": len(manifest.get("sources", []))})
    return result


def _sources_markdown(manifest: dict[str, Any]) -> str:
    lines = [
        "# Managed Source Workspace",
        "",
        "Inspect every listed source before answering.",
        "Prefer `text/` for extracted semantic content and `files/` for originals.",
        "State which sources were successfully read.",
        "Explicitly list unreadable or unsupported sources.",
        "Cite the display name and page number or local section when making source-specific claims.",
        "Do not modify any file.",
        "",
        f"Selected sources: {len(manifest.get('sources', []))}",
        "",
    ]
    for index, source in enumerate(manifest.get("sources", []), 1):
        lines.append(f"## {index}. {source['displayName']}")
        lines.append(f"- Kind: `{source['kind']}`")
        lines.append(f"- Original: `{source['fileLink']}`")
        if source.get("textLink"):
            lines.append(f"- Extracted text: `{source['textLink']}`")
        lines.append("")
    return "\n".join(lines)


def build_workspace(conversation_id: str, sources: list[dict], follow_current_document: bool) -> dict:
    target = workspace_path(conversation_id)
    if not isinstance(sources, list):
        return _result({"schema": SOURCE_WORKSPACE_SCHEMA, "conversationId": safe_conversation_id(conversation_id), "sources": []}, False, ["sources must be a list"])
    normalized: list[dict[str, Any]] = []
    errors: list[str] = []
    seen: set[str] = set()
    for index, source in enumerate(sources):
        item, item_errors = _normal_source(source, index)
        errors.extend(item_errors)
        if item is not None:
            if item["sourceId"] in seen:
                errors.append(f"duplicate source id: {item['sourceId']}")
            seen.add(item["sourceId"])
            normalized.append(item)
    if errors:
        return _result({"schema": SOURCE_WORKSPACE_SCHEMA, "conversationId": safe_conversation_id(conversation_id), "sources": []}, False, errors)

    revision = _revision(normalized, follow_current_document)
    manifest_sources: list[dict[str, Any]] = []
    for index, item in enumerate(normalized, 1):
        digest = hashlib.sha256(f"{item['sourceId']}|{item['originalPath']}".encode("utf-8")).hexdigest()[:8]
        suffix = Path(item["originalPath"]).suffix.lower()
        file_name = f"{index:03d}--{_slug(item['displayName'], 'source')}--{digest}{suffix}"
        record = {
            "sourceId": item["sourceId"],
            "displayName": item["displayName"],
            "kind": item["kind"],
            "originalPath": item["originalPath"],
            "textOriginalPath": item["textOriginalPath"],
            "fileLink": f"files/{file_name}",
            "fileLinkName": file_name,
            "textLink": "",
            "sha256": item["sha256"],
            "readable": True,
            "textReadable": False,
            "pageCount": item["pageCount"],
            "truncated": item["truncated"],
            "error": "",
            "_textOriginalPath": item["textOriginalPath"],
        }
        if item["textOriginalPath"]:
            text_name = f"{index:03d}--{_slug(item['displayName'], 'source')}--{digest}.txt"
            record["textLink"] = f"text/{text_name}"
            record["textLinkName"] = text_name
            record["textReadable"] = True
        manifest_sources.append(record)

    manifest = {
        "schema": SOURCE_WORKSPACE_SCHEMA,
        "conversationId": safe_conversation_id(conversation_id),
        "followCurrentDocument": bool(follow_current_document),
        "revision": revision,
        "updatedAt": _now(),
        "sources": [{key: value for key, value in source.items() if not key.startswith("_")} for source in manifest_sources],
    }
    staging = SOURCE_WORKSPACES_DIR / f".staging-{uuid.uuid4().hex}"
    backup = SOURCE_WORKSPACES_DIR / f".backup-{uuid.uuid4().hex}"
    try:
        (staging / "files").mkdir(parents=True, exist_ok=False)
        (staging / "text").mkdir()
        for source, item in zip(manifest_sources, normalized):
            os.symlink(item["originalPath"], staging / source["fileLink"])
            if source.get("textLink"):
                os.symlink(item["textOriginalPath"], staging / source["textLink"])
        _json_write(staging / "manifest.json", manifest)
        (staging / "SOURCES.md").write_text(_sources_markdown(manifest), encoding="utf-8")
        SOURCE_WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_dir():
                raise ValueError("managed workspace path is not a directory")
            os.replace(target, backup)
        os.replace(staging, target)
        if backup.exists():
            _remove_owned_tree(backup)
    except Exception as exc:
        if target.exists() and target != staging and backup.exists():
            _remove_owned_tree(target)
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        if staging.exists() and (staging / "manifest.json").is_file():
            _remove_owned_tree(staging)
        result = _result(manifest, False, [f"workspace build failed: {exc}"])
        result["workspacePath"] = str(target)
        return result
    result = _result(manifest, True)
    result["workspacePath"] = str(target)
    return result


def load_workspace(conversation_id: str) -> dict:
    path = workspace_path(conversation_id)
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "errors": ["workspace manifest is missing"], "sourceCount": 0}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [f"workspace manifest is invalid: {exc}"], "sourceCount": 0}
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_WORKSPACE_SCHEMA:
        return {"ok": False, "errors": ["workspace manifest schema is invalid"], "sourceCount": 0}
    return _result(manifest, True)


def validate_workspace(conversation_id: str, expected_revision: str = "") -> dict:
    loaded = load_workspace(conversation_id)
    if not loaded.get("ok"):
        return loaded
    errors: list[str] = []
    if expected_revision and loaded.get("revision") != expected_revision:
        errors.append("workspace revision does not match expected revision")
    workspace = workspace_path(conversation_id)
    checked_sources: list[dict[str, Any]] = []
    for source in loaded.get("sources", []):
        item = dict(source)
        source_errors: list[str] = []
        file_link = workspace / str(source.get("fileLink") or "")
        try:
            file_link.lstat()
            if not file_link.is_symlink():
                source_errors.append("file link is not a symlink")
            else:
                target = file_link.resolve(strict=True)
                expected_target = Path(str(source.get("originalPath") or "")).expanduser().resolve(strict=False)
                if target != expected_target:
                    source_errors.append("file link target does not match the manifest source")
                elif not target.is_file() or not os.access(target, os.R_OK):
                    source_errors.append("file link target is not a readable regular file")
        except (OSError, RuntimeError):
            source_errors.append("file link is missing or invalid")
        if source.get("textLink"):
            text_link = workspace / str(source["textLink"])
            try:
                text_link.lstat()
                if not text_link.is_symlink():
                    source_errors.append("text link is not a symlink")
                else:
                    text_target = text_link.resolve(strict=True)
                    expected_text_target = Path(str(source.get("textOriginalPath") or "")).expanduser().resolve(strict=False)
                    if not source.get("textOriginalPath") or text_target != expected_text_target:
                        source_errors.append("text link target does not match the manifest source")
                    elif not text_target.is_file() or not os.access(text_target, os.R_OK):
                        source_errors.append("text link target is not a readable regular file")
            except (OSError, RuntimeError):
                source_errors.append("text link is missing or invalid")
        item["valid"] = not source_errors
        item["errors"] = source_errors
        checked_sources.append(item)
        errors.extend(f"{source.get('displayName', source.get('sourceId', 'source'))}: {error}" for error in source_errors)
    result = dict(loaded)
    result["sources"] = checked_sources
    result["errors"] = errors
    result["ok"] = not errors
    return result


def clear_workspace(conversation_id: str) -> dict:
    path = workspace_path(conversation_id)
    try:
        _remove_owned_tree(path)
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [f"workspace cleanup failed: {exc}"], "sourceCount": 0}
    return {"ok": True, "errors": [], "sourceCount": 0, "workspacePath": str(path), "conversationId": safe_conversation_id(conversation_id)}
