from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path.home() / ".codex/marginnote-assistant"
SOURCE_WORKSPACES_DIR = ROOT / "control" / "source-workspaces"
SOURCE_WORKSPACE_SCHEMA = "codex.mn.sourceWorkspace.v1"
MANIFEST_KEYS = {
    "schema",
    "conversationId",
    "followCurrentDocument",
    "revision",
    "updatedAt",
    "sourcesMdSha256",
    "sources",
}
LEGACY_MANIFEST_KEYS = MANIFEST_KEYS - {"sourcesMdSha256"}
SOURCE_KEYS = {
    "sourceId",
    "displayName",
    "kind",
    "originalPath",
    "textOriginalPath",
    "fileLink",
    "fileLinkName",
    "textLink",
    "textLinkName",
    "sha256",
    "textSha256",
    "readable",
    "textReadable",
    "pageCount",
    "truncated",
    "error",
}
LEGACY_SOURCE_KEYS = SOURCE_KEYS - {"textSha256", "textLinkName"}
MANAGED_TEXT_ARTIFACT_RE = re.compile(r"^managed-[a-f0-9]{16}-([a-f0-9]{64})\.txt$")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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
    digest = hashlib.sha256(str(conversation_id).encode("utf-8")).hexdigest()[:16]
    return SOURCE_WORKSPACES_DIR / f"{safe_id[:96]}--{digest}"


def legacy_workspace_path(conversation_id: str) -> Path:
    safe_id = safe_conversation_id(conversation_id)
    if not safe_id:
        raise ValueError("missing valid conversationId")
    return SOURCE_WORKSPACES_DIR / safe_id


def _legacy_workspace_ownership(path: Path, conversation_id: str) -> tuple[dict[str, Any] | None, str]:
    try:
        path_stat = path.lstat()
    except FileNotFoundError:
        return None, ""
    except OSError as exc:
        return None, f"legacy workspace cannot be inspected: {exc}"
    if not stat.S_ISDIR(path_stat.st_mode):
        return None, "legacy workspace is not a real directory"
    manifest_path = path / "manifest.json"
    try:
        manifest_stat = manifest_path.lstat()
    except OSError as exc:
        return None, f"legacy workspace manifest cannot be inspected: {exc}"
    if not stat.S_ISREG(manifest_stat.st_mode):
        return None, "legacy workspace manifest is not a regular file"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, f"legacy workspace manifest is invalid: {exc}"
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_WORKSPACE_SCHEMA:
        return None, "legacy workspace manifest schema is invalid"
    if str(manifest.get("conversationId") or "") != str(conversation_id):
        return None, "legacy workspace conversation ownership does not match"
    return manifest, ""


def _workspace_path_for_read(conversation_id: str) -> tuple[Path, str]:
    target = workspace_path(conversation_id)
    if target.exists() or target.is_symlink():
        return target, ""
    legacy = legacy_workspace_path(conversation_id)
    if not legacy.exists() and not legacy.is_symlink():
        return target, ""
    _, ownership_error = _legacy_workspace_ownership(legacy, conversation_id)
    if ownership_error:
        return target, ownership_error
    if target.exists() or target.is_symlink():
        return target, "digest workspace appeared during legacy fallback"
    return legacy, ""


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


def _workspace_manifest_contract(
    path: Path,
    conversation_id: str = "",
    *,
    allow_legacy_contract: bool = False,
) -> tuple[dict[str, Any], set[str], set[Path], str]:
    if not path.exists() and not path.is_symlink():
        raise ValueError("workspace root is missing")
    if path.is_symlink() or not path.is_dir():
        raise ValueError("workspace root is not a managed directory")
    manifest_path = path / "manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ValueError("workspace manifest is missing or not a regular file")
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)
    except (OSError, ValueError) as exc:
        raise ValueError(f"workspace manifest is invalid: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_WORKSPACE_SCHEMA:
        raise ValueError("workspace manifest schema is invalid")
    if conversation_id and str(manifest.get("conversationId") or "") != str(conversation_id):
        raise ValueError("workspace conversation ownership does not match")
    manifest_keys = set(manifest)
    if manifest_keys != MANIFEST_KEYS and not (
        allow_legacy_contract and manifest_keys == LEGACY_MANIFEST_KEYS
    ):
        raise ValueError("workspace manifest contains unrecognized fields")
    if not str(manifest.get("conversationId") or ""):
        raise ValueError("workspace manifest conversation ownership is missing")
    if not isinstance(manifest.get("followCurrentDocument"), bool):
        raise ValueError("workspace manifest follow-current value is invalid")
    if not re.fullmatch(r"[a-f0-9]{64}", str(manifest.get("revision") or "")):
        raise ValueError("workspace manifest revision is invalid")
    if manifest_keys == MANIFEST_KEYS and not re.fullmatch(
        r"[a-f0-9]{64}", str(manifest.get("sourcesMdSha256") or "")
    ):
        raise ValueError("workspace manifest SOURCES.md sha256 is invalid")
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("workspace manifest sources are invalid")
    expected_links: set[Path] = set()
    source_ids: set[str] = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("workspace manifest contains an invalid source")
        source_keys = set(source)
        if source_keys != SOURCE_KEYS and not (
            allow_legacy_contract
            and (
                source_keys == LEGACY_SOURCE_KEYS
                or source_keys == LEGACY_SOURCE_KEYS | {"textLinkName"}
            )
        ):
            raise ValueError("workspace manifest source contains unrecognized fields")
        source_id = str(source.get("sourceId") or "")
        if not source_id or source_id in source_ids:
            raise ValueError("workspace manifest source identity is invalid")
        source_ids.add(source_id)
        if source_keys == SOURCE_KEYS:
            for text_field in ("displayName", "kind", "originalPath", "fileLink", "fileLinkName"):
                if not str(source.get(text_field) or ""):
                    raise ValueError(f"workspace manifest source {text_field} is invalid")
            if not Path(str(source.get("originalPath") or "")).is_absolute():
                raise ValueError("workspace manifest source path is not absolute")
            if not re.fullmatch(r"[a-f0-9]{64}", str(source.get("sha256") or "")):
                raise ValueError("workspace manifest source sha256 is invalid")
            if not isinstance(source.get("truncated"), bool) or not isinstance(source.get("error"), str):
                raise ValueError("workspace manifest source diagnostic fields are invalid")
            if source.get("pageCount") is not None and not isinstance(source.get("pageCount"), int):
                raise ValueError("workspace manifest source page count is invalid")
            text_link_present = bool(source.get("textLink"))
            if text_link_present != bool(source.get("textReadable")):
                raise ValueError("workspace manifest text readability is inconsistent")
            if text_link_present:
                if not Path(str(source.get("textOriginalPath") or "")).is_absolute():
                    raise ValueError("workspace manifest text source path is not absolute")
                if not re.fullmatch(r"[a-f0-9]{64}", str(source.get("textSha256") or "")):
                    raise ValueError("workspace manifest text sha256 is invalid")
            elif source.get("textSha256") or source.get("textOriginalPath") or source.get("textLinkName"):
                raise ValueError("workspace manifest contains orphaned text metadata")
            if source.get("readable") is not True:
                raise ValueError("workspace manifest source readability is invalid")
        for field, directory_name in (("fileLink", "files"), ("textLink", "text")):
            relative = str(source.get(field) or "")
            if not relative:
                continue
            relative_path = Path(relative)
            if relative_path.is_absolute() or relative_path.parts[:1] != (directory_name,) or len(relative_path.parts) != 2:
                raise ValueError("workspace manifest contains an invalid managed link")
            name_field = "fileLinkName" if field == "fileLink" else "textLinkName"
            if source.get(name_field) and str(source.get(name_field)) != relative_path.name:
                raise ValueError("workspace manifest link name does not match its path")
            expected_links.add(relative_path)
    if manifest_keys == MANIFEST_KEYS:
        expected_revision = _revision(
            str(manifest.get("conversationId") or ""),
            sources,
            bool(manifest.get("followCurrentDocument", True)),
            str(manifest.get("sourcesMdSha256") or ""),
        )
        if str(manifest.get("revision") or "") != expected_revision:
            raise ValueError("workspace manifest revision does not match its content")
    return manifest, manifest_keys, expected_links, manifest_text


def _validate_sources_file(
    path: Path,
    manifest: dict[str, Any],
    manifest_keys: set[str],
    *,
    required: bool,
) -> None:
    sources_file = path / "SOURCES.md"
    present = sources_file.exists() or sources_file.is_symlink()
    if not present:
        if required:
            raise ValueError("workspace SOURCES.md is missing or not a regular file")
        return
    if sources_file.is_symlink() or not sources_file.is_file():
        raise ValueError("workspace SOURCES.md is missing or not a regular file")
    if manifest_keys != MANIFEST_KEYS:
        return
    try:
        sources_text = sources_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ValueError(f"workspace SOURCES.md is unreadable: {exc}") from exc
    if _sha256_text(sources_text) != str(manifest.get("sourcesMdSha256") or ""):
        raise ValueError("workspace SOURCES.md sha256 does not match the manifest")
    if sources_text != _sources_markdown(manifest):
        raise ValueError("workspace SOURCES.md content does not match the manifest")


def _workspace_owned_entries(
    path: Path,
    conversation_id: str = "",
    *,
    allow_legacy_contract: bool = False,
) -> list[Path]:
    if not path.exists() and not path.is_symlink():
        return []
    manifest, manifest_keys, expected_links, _ = _workspace_manifest_contract(
        path,
        conversation_id,
        allow_legacy_contract=allow_legacy_contract,
    )
    top_entries = {child.name for child in path.iterdir()}
    if top_entries != {"manifest.json", "SOURCES.md", "files", "text"}:
        raise ValueError("workspace contains unrecognized content")
    for directory_name in ("files", "text"):
        directory = path / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"workspace {directory_name} is not a managed directory")
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
    _validate_sources_file(path, manifest, manifest_keys, required=True)
    return [
        path / "manifest.json",
        path / "SOURCES.md",
        path / "files",
        path / "text",
        *[path / relative for relative in sorted(expected_links)],
    ]


def _workspace_cleanup_plan(
    path: Path,
    conversation_id: str = "",
    *,
    allow_legacy_contract: bool = False,
) -> dict[str, Any] | None:
    if not path.exists() and not path.is_symlink():
        return None
    manifest, manifest_keys, expected_links, manifest_text = _workspace_manifest_contract(
        path,
        conversation_id,
        allow_legacy_contract=allow_legacy_contract,
    )
    allowed_top_entries = {"manifest.json", "SOURCES.md", "files", "text"}
    actual_top_entries = {child.name for child in path.iterdir()}
    if actual_top_entries - allowed_top_entries:
        raise ValueError("workspace contains unrecognized content")
    for directory_name in ("files", "text"):
        directory = path / directory_name
        present = directory.exists() or directory.is_symlink()
        if not present:
            continue
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError(f"workspace {directory_name} is not a managed directory")
        expected_names = {
            relative.name for relative in expected_links if relative.parts[:1] == (directory_name,)
        }
        actual_names = {child.name for child in directory.iterdir()}
        if actual_names - expected_names:
            raise ValueError("workspace contains unrecognized content")
        for child in directory.iterdir():
            if not child.is_symlink():
                raise ValueError("workspace contains a non-symlink managed link")
    _validate_sources_file(path, manifest, manifest_keys, required=False)
    return {
        "manifest": manifest,
        "manifestText": manifest_text,
        "expectedLinks": sorted(expected_links),
    }


def _unlink_if_present(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _rmdir_if_present(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    try:
        path.rmdir()
    except FileNotFoundError:
        pass


def _remove_owned_tree(path: Path, conversation_id: str = "", *, allow_legacy_contract: bool = False) -> None:
    plan = _workspace_cleanup_plan(
        path,
        conversation_id,
        allow_legacy_contract=allow_legacy_contract,
    )
    if plan is None:
        return
    for relative in plan["expectedLinks"]:
        _unlink_if_present(path / relative)
    _unlink_if_present(path / "SOURCES.md")
    _rmdir_if_present(path / "files")
    _rmdir_if_present(path / "text")
    manifest_path = path / "manifest.json"
    manifest_path.unlink()
    try:
        path.rmdir()
    except FileNotFoundError:
        return
    except OSError as remove_error:
        try:
            if path.exists() and not path.is_symlink() and path.is_dir():
                with manifest_path.open("x", encoding="utf-8") as handle:
                    handle.write(str(plan["manifestText"]))
        except OSError as restore_error:
            raise OSError(
                f"workspace root cleanup failed ({remove_error}); manifest restore failed ({restore_error})"
            ) from remove_error
        raise


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
    try:
        source_sha256 = _sha256_file(path)
    except OSError as exc:
        return None, [f"source {source_id or index + 1} cannot be hashed: {exc}"]
    claimed_sha256 = str(source.get("sha256") or "").strip().lower()
    if claimed_sha256 and claimed_sha256 != source_sha256:
        return None, [f"source {source_id or index + 1} sha256 changed before workspace build"]
    text_sha256 = ""
    if text_path is not None:
        try:
            text_sha256 = _sha256_file(text_path)
        except OSError as exc:
            return None, [f"source {source_id or index + 1} textPath cannot be hashed: {exc}"]
    display_name = title or path.name
    normalized = {
        "sourceId": source_id,
        "displayName": display_name,
        "kind": kind,
        "originalPath": str(path),
        "textOriginalPath": str(text_path) if text_path else "",
        "sha256": source_sha256,
        "textSha256": text_sha256,
        "pageCount": source.get("pageCount") if source.get("pageCount") is not None else None,
        "truncated": bool(source.get("truncated", False)),
        "error": str(source.get("error") or source.get("textError") or ""),
    }
    return normalized, []


def _revision(
    conversation_id: str,
    records: list[dict[str, Any]],
    follow_current_document: bool,
    sources_md_sha256: str,
) -> str:
    payload = {
        "schema": SOURCE_WORKSPACE_SCHEMA,
        "conversationId": str(conversation_id),
        "followCurrentDocument": bool(follow_current_document),
        "sourcesMdSha256": str(sources_md_sha256),
        "sources": records,
    }
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
            lines.append(f"- Extracted text truncated: `{'true' if source.get('truncated') else 'false'}`")
        elif source.get("error"):
            lines.append(f"- Extracted text unavailable: {source['error']}")
        lines.append("")
    return "\n".join(lines)


def build_workspace(conversation_id: str, sources: list[dict], follow_current_document: bool) -> dict:
    target = workspace_path(conversation_id)
    if not isinstance(sources, list):
        return _result({"schema": SOURCE_WORKSPACE_SCHEMA, "conversationId": str(conversation_id), "sources": []}, False, ["sources must be a list"])
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
        return _result({"schema": SOURCE_WORKSPACE_SCHEMA, "conversationId": str(conversation_id), "sources": []}, False, errors)

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
            "textLinkName": "",
            "sha256": item["sha256"],
            "textSha256": item["textSha256"],
            "readable": True,
            "textReadable": False,
            "pageCount": item["pageCount"],
            "truncated": item["truncated"],
            "error": item["error"],
            "_textOriginalPath": item["textOriginalPath"],
        }
        if item["textOriginalPath"]:
            text_name = f"{index:03d}--{_slug(item['displayName'], 'source')}--{digest}.txt"
            record["textLink"] = f"text/{text_name}"
            record["textLinkName"] = text_name
            record["textReadable"] = True
        manifest_sources.append(record)

    public_sources = [{key: value for key, value in source.items() if not key.startswith("_")} for source in manifest_sources]
    sources_text = _sources_markdown({"sources": public_sources})
    sources_md_sha256 = _sha256_text(sources_text)
    revision = _revision(
        str(conversation_id),
        public_sources,
        follow_current_document,
        sources_md_sha256,
    )
    manifest = {
        "schema": SOURCE_WORKSPACE_SCHEMA,
        "conversationId": str(conversation_id),
        "followCurrentDocument": bool(follow_current_document),
        "revision": revision,
        "updatedAt": _now(),
        "sourcesMdSha256": sources_md_sha256,
        "sources": public_sources,
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
        (staging / "SOURCES.md").write_text(sources_text, encoding="utf-8")
        SOURCE_WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        if target.exists() or target.is_symlink():
            if target.is_symlink() or not target.is_dir():
                raise ValueError("managed workspace path is not a directory")
            os.replace(target, backup)
        os.replace(staging, target)
        if backup.exists():
            _remove_owned_tree(backup, str(conversation_id), allow_legacy_contract=True)
    except Exception as exc:
        if target.exists() and target != staging and backup.exists():
            _remove_owned_tree(target, str(conversation_id), allow_legacy_contract=True)
        if backup.exists() and not target.exists():
            os.replace(backup, target)
        if staging.exists() and (staging / "manifest.json").is_file():
            _remove_owned_tree(staging, str(conversation_id), allow_legacy_contract=True)
        result = _result(manifest, False, [f"workspace build failed: {exc}"])
        result["workspacePath"] = str(target)
        return result
    result = _result(manifest, True)
    result["workspacePath"] = str(target)
    return result


def load_workspace(conversation_id: str) -> dict:
    path, fallback_error = _workspace_path_for_read(conversation_id)
    if fallback_error:
        return {"ok": False, "errors": [fallback_error], "sourceCount": 0}
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return {"ok": False, "errors": ["workspace manifest is missing"], "sourceCount": 0}
    try:
        _workspace_owned_entries(path, str(conversation_id))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [f"workspace manifest is invalid: {exc}"], "sourceCount": 0}
    if not isinstance(manifest, dict) or manifest.get("schema") != SOURCE_WORKSPACE_SCHEMA:
        return {"ok": False, "errors": ["workspace manifest schema is invalid"], "sourceCount": 0}
    result = _result(manifest, True)
    result["workspacePath"] = str(path)
    return result


def validate_workspace(conversation_id: str, expected_revision: str = "") -> dict:
    loaded = load_workspace(conversation_id)
    if not loaded.get("ok"):
        return loaded
    errors: list[str] = []
    if expected_revision and loaded.get("revision") != expected_revision:
        errors.append("workspace revision does not match expected revision")
    workspace = Path(str(loaded.get("workspacePath") or workspace_path(conversation_id)))
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
                elif _sha256_file(target) != str(source.get("sha256") or ""):
                    source_errors.append("file content sha256 does not match the manifest source")
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
                    elif _sha256_file(text_target) != str(source.get("textSha256") or ""):
                        source_errors.append("text content sha256 does not match the manifest source")
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
    digest = workspace_path(conversation_id)
    legacy = legacy_workspace_path(conversation_id)
    paths = [
        path
        for path in (digest, legacy)
        if path.exists() or path.is_symlink()
    ]
    if not paths:
        paths = [digest]
    for path in paths:
        if not path.exists() and not path.is_symlink():
            continue
        _, ownership_error = _legacy_workspace_ownership(path, conversation_id)
        if ownership_error:
            return {"ok": False, "errors": [ownership_error], "sourceCount": 0}
        try:
            _workspace_cleanup_plan(path, str(conversation_id), allow_legacy_contract=True)
        except (OSError, ValueError) as exc:
            return {"ok": False, "errors": [f"workspace cleanup failed: {exc}"], "sourceCount": 0}
    try:
        for path in paths:
            _remove_owned_tree(path, str(conversation_id), allow_legacy_contract=True)
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [f"workspace cleanup failed: {exc}"], "sourceCount": 0}
    return {
        "ok": True,
        "errors": [],
        "sourceCount": 0,
        "workspacePath": str(paths[0]),
        "workspacePaths": [str(path) for path in paths],
        "conversationId": str(conversation_id),
    }


def backup_workspace(conversation_id: str) -> dict[str, Any]:
    digest = workspace_path(conversation_id)
    legacy = legacy_workspace_path(conversation_id)
    paths = [path for path in (digest, legacy) if path.exists() or path.is_symlink()]
    entries: list[dict[str, str]] = []
    try:
        for path in paths:
            _workspace_cleanup_plan(path, str(conversation_id), allow_legacy_contract=True)
        SOURCE_WORKSPACES_DIR.mkdir(parents=True, exist_ok=True)
        for path in paths:
            backup = SOURCE_WORKSPACES_DIR / f".backup-{uuid.uuid4().hex}"
            os.replace(path, backup)
            entries.append({"path": str(path), "backupPath": str(backup)})
    except (OSError, ValueError) as exc:
        for entry in reversed(entries):
            original = Path(entry["path"])
            backup = Path(entry["backupPath"])
            if backup.exists() and not original.exists() and not original.is_symlink():
                os.replace(backup, original)
        return {
            "ok": False,
            "conversationId": str(conversation_id),
            "entries": [],
            "errors": [f"workspace backup failed: {exc}"],
        }
    return {
        "ok": True,
        "conversationId": str(conversation_id),
        "entries": entries,
        "errors": [],
    }


def _workspace_backup_entries(transaction: dict[str, Any], conversation_id: str) -> list[tuple[Path, Path]]:
    if str(transaction.get("conversationId") or "") != str(conversation_id):
        raise ValueError("workspace backup conversation ownership does not match")
    expected_paths = {
        workspace_path(conversation_id),
        legacy_workspace_path(conversation_id),
    }
    entries: list[tuple[Path, Path]] = []
    for raw in transaction.get("entries", []):
        if not isinstance(raw, dict):
            raise ValueError("workspace backup entry is invalid")
        original = Path(str(raw.get("path") or ""))
        backup = Path(str(raw.get("backupPath") or ""))
        if original not in expected_paths:
            raise ValueError("workspace backup target is not owned by this conversation")
        if backup.parent != SOURCE_WORKSPACES_DIR or not backup.name.startswith(".backup-"):
            raise ValueError("workspace backup path is outside the managed root")
        if backup.exists() or backup.is_symlink():
            _workspace_cleanup_plan(backup, str(conversation_id), allow_legacy_contract=True)
        entries.append((original, backup))
    return entries


def restore_workspace_backup(conversation_id: str, transaction: dict[str, Any]) -> dict[str, Any]:
    try:
        entries = _workspace_backup_entries(transaction, conversation_id)
        for _, backup in entries:
            if not backup.exists() or backup.is_symlink():
                raise ValueError("workspace backup is missing or invalid")
        expected_paths = {
            workspace_path(conversation_id),
            legacy_workspace_path(conversation_id),
        }
        for path in expected_paths:
            if path.exists() or path.is_symlink():
                _remove_owned_tree(path, str(conversation_id), allow_legacy_contract=True)
        for original, backup in entries:
            if original.exists() or original.is_symlink():
                raise ValueError("workspace restore target already exists")
            os.replace(backup, original)
    except (OSError, ValueError) as exc:
        return {"ok": False, "errors": [f"workspace restore failed: {exc}"]}
    return {"ok": True, "errors": []}


def discard_workspace_backup(conversation_id: str, transaction: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    try:
        entries = _workspace_backup_entries(transaction, conversation_id)
    except ValueError as exc:
        return {"ok": False, "errors": [f"workspace backup cleanup failed: {exc}"]}
    for _, backup in entries:
        if not backup.exists() and not backup.is_symlink():
            continue
        try:
            _remove_owned_tree(backup, str(conversation_id), allow_legacy_contract=True)
        except (OSError, ValueError) as exc:
            errors.append(f"workspace backup cleanup failed: {exc}")
    return {"ok": not errors, "errors": errors}


def cleanup_orphans(
    active_conversation_ids: set[str] | list[str] | tuple[str, ...],
    *,
    text_artifacts_dir: Path | str | None = None,
    now: float | None = None,
) -> dict[str, Any]:
    active_ids = {str(item) for item in active_conversation_ids if str(item)}
    current_time = float(now if now is not None else time.time())
    workspace_cutoff = current_time - 7 * 24 * 60 * 60
    transient_cutoff = current_time - 24 * 60 * 60
    removed_workspaces: list[str] = []
    removed_transients: list[str] = []
    removed_text_artifacts: list[str] = []
    skipped: list[str] = []
    referenced_text_paths: set[str] = set()

    if SOURCE_WORKSPACES_DIR.exists() and not SOURCE_WORKSPACES_DIR.is_symlink():
        for path in sorted(SOURCE_WORKSPACES_DIR.iterdir(), key=lambda item: item.name):
            try:
                path_stat = path.lstat()
                if not stat.S_ISDIR(path_stat.st_mode):
                    skipped.append(str(path))
                    continue
                manifest_path = path / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                conversation_id = str(manifest.get("conversationId") or "") if isinstance(manifest, dict) else ""
                if not conversation_id:
                    raise ValueError("missing conversation ownership")
                _workspace_owned_entries(
                    path,
                    conversation_id,
                    allow_legacy_contract=True,
                )
                modified_at = max(path_stat.st_mtime, manifest_path.lstat().st_mtime)
                transient = path.name.startswith(".staging-") or path.name.startswith(".backup-")
                if transient:
                    remove = modified_at < transient_cutoff
                else:
                    expected_names = {
                        workspace_path(conversation_id).name,
                        legacy_workspace_path(conversation_id).name,
                    }
                    if path.name not in expected_names:
                        raise ValueError("workspace path does not match its owner")
                    remove = conversation_id not in active_ids and modified_at < workspace_cutoff
                if remove:
                    _remove_owned_tree(
                        path,
                        conversation_id,
                        allow_legacy_contract=True,
                    )
                    (removed_transients if transient else removed_workspaces).append(str(path))
                    continue
                for source in manifest.get("sources", []):
                    if not isinstance(source, dict):
                        continue
                    text_path = str(source.get("textOriginalPath") or "")
                    if text_path:
                        referenced_text_paths.add(str(Path(text_path).expanduser().resolve(strict=False)))
            except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
                skipped.append(str(path))

    artifact_root = Path(text_artifacts_dir) if text_artifacts_dir is not None else ROOT / "control" / "source-text"
    if artifact_root.exists() and not artifact_root.is_symlink() and artifact_root.is_dir():
        for path in sorted(artifact_root.iterdir(), key=lambda item: item.name):
            try:
                path_stat = path.lstat()
                match = MANAGED_TEXT_ARTIFACT_RE.fullmatch(path.name)
                if not stat.S_ISREG(path_stat.st_mode) or path.is_symlink() or match is None:
                    continue
                if _sha256_file(path) != match.group(1):
                    continue
                canonical = str(path.resolve(strict=False))
                if canonical in referenced_text_paths or path_stat.st_mtime >= workspace_cutoff:
                    continue
                path.unlink()
                removed_text_artifacts.append(str(path))
            except OSError:
                skipped.append(str(path))

    return {
        "ok": True,
        "removedWorkspaceCount": len(removed_workspaces),
        "removedTransientCount": len(removed_transients),
        "removedTextArtifactCount": len(removed_text_artifacts),
        "removedWorkspaces": removed_workspaces,
        "removedTransients": removed_transients,
        "removedTextArtifacts": removed_text_artifacts,
        "skipped": skipped,
    }
