#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DEFAULT_PACKAGE_ZIP = ROOT / "release/CodexCompanion-0.4.20-latest-dist.zip"
DEFAULT_PACKAGE_PKG = ROOT / "release/CodexCompanion-0.4.20-latest.pkg"
DEFAULT_OUTPUT_PARENT = ROOT / "release/handoff"
DEFAULT_ONEDRIVE_PARENT = Path.home() / "Library/CloudStorage/OneDrive-个人/Codex Companion/Release Handoff"
LIVE_EXTENSION = Path.home() / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
CURRENT_PLUGIN_VERSION = "0.4.20"
CROSS_MACHINE_EVIDENCE_SCHEMA = "codex-companion-cross-machine-install-v1"
NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA = "codex-companion-native-highlight-v1"
MN_RUNTIME_EVIDENCE_SCHEMA = "codex-companion-mn-runtime-v1"
SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA = "codex-companion-single-document-acceptance-v1"
RUNTIME_SOURCE_RELATIVE_FILES = [
    "main.js",
    "CodexPanelController.js",
    "CodexWebPanelController.js",
    "web/index.html",
    "web/app.js",
    "web/app.css",
    "web/styles.css",
]
CROSS_MACHINE_EVIDENCE_PATTERNS = [
    "codex-companion-cross-machine-evidence-*.json",
    "CodexCompanion-cross-machine-evidence-*.json",
    "cross-machine-evidence*.json",
]
INSTALL_EVIDENCE_CHECKS = [
    "MN4 extension manifest",
    "Companion service",
    "LaunchAgent",
]
NATIVE_HIGHLIGHT_EVIDENCE_PATTERNS = [
    "codex-companion-native-highlight-evidence-*.json",
    "CodexCompanion-native-highlight-evidence-*.json",
    "native-highlight-evidence*.json",
]
MN_RUNTIME_EVIDENCE_PATTERNS = [
    "CodexCompanion-MNRuntimeEvidence-*.json",
    "codex-companion-mn-runtime-evidence-*.json",
    "mn-runtime-evidence*.json",
]
SINGLE_DOCUMENT_ACCEPTANCE_PATTERNS = [
    "codex-companion-single-document-acceptance-*.json",
    "CodexCompanion-single-document-acceptance-*.json",
    "single-document-acceptance*.json",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def timestamp_now() -> str:
    return time.strftime("%Y%m%d-%H%M%S")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.expanduser().read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON is not an object: {path}")
    return data


def unique_existing_dirs(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        candidate = path.expanduser()
        try:
            key = str(candidate.resolve())
        except Exception:
            key = str(candidate)
        if key in seen or not candidate.exists() or not candidate.is_dir():
            continue
        seen.add(key)
        result.append(candidate)
    return result


def default_evidence_search_dirs(package_zip: Path | None = None) -> list[Path]:
    dirs = [
        Path.cwd(),
        ROOT / "release/evidence",
        ROOT / "release/diagnostics/evidence",
        ROOT / "release",
        ROOT,
    ]
    if package_zip:
        package_zip = package_zip.expanduser()
        dirs.extend([package_zip.parent, package_zip.parent / "evidence", package_zip.parent / "diagnostics/evidence"])
    dirs.append(Path.home() / "Desktop")
    return unique_existing_dirs(dirs)


def json_file_matches_schema(path: Path, schema: str) -> bool:
    if "template" in path.name.lower():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return isinstance(data, dict) and data.get("schema") == schema


def discover_evidence_candidates(schema: str, patterns: list[str], search_dirs: list[Path] | None = None) -> list[Path]:
    candidates: list[Path] = []
    for directory in unique_existing_dirs(search_dirs or default_evidence_search_dirs()):
        for pattern in patterns:
            for path in directory.glob(pattern):
                if path.is_file() and json_file_matches_schema(path, schema):
                    candidates.append(path)
    return sorted(candidates, key=lambda path: (path.stat().st_mtime_ns, path.name), reverse=True)


def discover_evidence_file(schema: str, patterns: list[str], search_dirs: list[Path] | None = None) -> Path | None:
    candidates = discover_evidence_candidates(schema, patterns, search_dirs)
    return candidates[0] if candidates else None


def discover_evidence_files(search_dirs: list[Path] | None = None, expected_package_sha256: str = "") -> list[Path]:
    files: list[Path] = []
    for schema, patterns in [
        (MN_RUNTIME_EVIDENCE_SCHEMA, MN_RUNTIME_EVIDENCE_PATTERNS),
        (NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA, NATIVE_HIGHLIGHT_EVIDENCE_PATTERNS),
        (SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA, SINGLE_DOCUMENT_ACCEPTANCE_PATTERNS),
        (CROSS_MACHINE_EVIDENCE_SCHEMA, CROSS_MACHINE_EVIDENCE_PATTERNS),
    ]:
        release_path: Path | None = None
        diagnostic_path: Path | None = None
        for path in discover_evidence_candidates(schema, patterns, search_dirs):
            if evidence_file_is_release_proof(path, expected_package_sha256):
                if release_path is None:
                    release_path = path
            elif diagnostic_path is None:
                diagnostic_path = path
            if release_path and diagnostic_path:
                break
        for path in [release_path, diagnostic_path]:
            if path and path not in files:
                files.append(path)
    return files


def mn_runtime_evidence_is_release_proof(data: dict[str, Any]) -> bool:
    runtime = data.get("mnRuntime") if isinstance(data.get("mnRuntime"), dict) else {}
    status_after = data.get("statusAfter") if isinstance(data.get("statusAfter"), dict) else {}
    status_runtime = status_after.get("mnRuntime") if isinstance(status_after.get("mnRuntime"), dict) else {}
    runtime = runtime or status_runtime
    base_ok = bool(
        data.get("ok")
        and runtime.get("ready")
        and not runtime.get("staleRuntime")
        and not runtime.get("runtimeHandlerStale")
    )
    if not base_ok:
        return False
    current_source = latest_runtime_source()
    reference_time = mn_runtime_evidence_reference_time(data, runtime)
    if current_source and reference_time is not None and float(current_source.get("mtime") or 0) > reference_time + 1:
        return False
    return True


def numeric_time(value: Any) -> float | None:
    if isinstance(value, (int, float)) and float(value) > 0:
        return float(value)
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            parsed = float(value)
            if parsed > 0:
                return parsed
        except ValueError:
            pass
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            pass
        try:
            return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").timestamp()
        except ValueError:
            return None
    return None


def mn_runtime_evidence_reference_time(data: dict[str, Any], runtime: dict[str, Any]) -> float | None:
    for key in ["sourceMtime", "runtimeSourceMtime", "stalenessReferenceTime"]:
        parsed = numeric_time(runtime.get(key))
        if parsed is not None:
            return parsed
        parsed = numeric_time(data.get(key))
        if parsed is not None:
            return parsed
    for key in ["latestEventTs", "latestNativeEventTs", "latestWebEventTs"]:
        parsed = numeric_time(runtime.get(key))
        if parsed is not None:
            return parsed
    return numeric_time(data.get("generatedAt"))


def latest_runtime_source(extension_dir: Path | None = None) -> dict[str, Any] | None:
    extension_dir = extension_dir or LIVE_EXTENSION
    latest_path: Path | None = None
    latest_mtime = 0.0
    for relative in RUNTIME_SOURCE_RELATIVE_FILES:
        path = extension_dir / relative
        try:
            mtime = path.stat().st_mtime
        except OSError:
            continue
        if mtime > latest_mtime:
            latest_path = path
            latest_mtime = mtime
    if latest_path is None:
        return None
    return {"path": str(latest_path), "mtime": latest_mtime}


def native_highlight_event_scope(event: dict[str, Any] | None) -> dict[str, str]:
    event = event or {}
    return {
        "topicid": str(event.get("topicid") or event.get("notebookid") or ""),
        "bookmd5": str(event.get("bookmd5") or event.get("docmd5") or ""),
    }


def native_highlight_evidence_is_release_proof(data: dict[str, Any]) -> bool:
    events = data.get("events") if isinstance(data.get("events"), dict) else {}
    latest_posted = events.get("latestPosted") if isinstance(events.get("latestPosted"), dict) else None
    if not data.get("ok") or not latest_posted:
        return False
    if str(latest_posted.get("event") or "") != "nativeHighlightSelectionPosted":
        return False
    if str(latest_posted.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
        return False
    event_scope = native_highlight_event_scope(latest_posted)
    if not event_scope["topicid"] or not event_scope["bookmd5"]:
        return False
    blob_check = data.get("highlightBlobCheck") if isinstance(data.get("highlightBlobCheck"), dict) else {}
    blob_scope = {
        "topicid": str(blob_check.get("topicid") or ""),
        "bookmd5": str(blob_check.get("bookmd5") or ""),
    }
    return bool(
        str(blob_check.get("status") or "") == "OK"
        and int(blob_check.get("native_highlight_blobs") or 0) > 0
        and blob_scope == event_scope
    )


def cross_machine_evidence_is_release_proof(data: dict[str, Any], expected_package_sha256: str = "") -> bool:
    package = data.get("package") if isinstance(data.get("package"), dict) else {}
    observed_sha = str(package.get("sha256") or "")
    install_checks = data.get("installChecks") if isinstance(data.get("installChecks"), dict) else {}
    checks_ok = all(bool(install_checks.get(name)) for name in INSTALL_EVIDENCE_CHECKS)
    return bool(
        data.get("ok")
        and checks_ok
        and (not expected_package_sha256 or observed_sha == expected_package_sha256)
    )


def single_document_acceptance_is_release_proof(data: dict[str, Any]) -> bool:
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    checks = data.get("checks") if isinstance(data.get("checks"), list) else []
    return bool(
        data.get("ok")
        and str(data.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
        and str(data.get("topicid") or "")
        and str(data.get("bookmd5") or "")
        and str(summary.get("singleDocumentAcceptance") or "") == "PASS"
        and int(summary.get("blocked") or 0) == 0
        and checks
        and all(isinstance(item, dict) and str(item.get("status") or "") == "PASS" for item in checks)
    )


def evidence_file_is_release_proof(path: Path, expected_package_sha256: str = "") -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    schema = data.get("schema")
    if schema == MN_RUNTIME_EVIDENCE_SCHEMA:
        return mn_runtime_evidence_is_release_proof(data)
    if schema == NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA:
        return native_highlight_evidence_is_release_proof(data)
    if schema == SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA:
        return single_document_acceptance_is_release_proof(data)
    if schema == CROSS_MACHINE_EVIDENCE_SCHEMA:
        return cross_machine_evidence_is_release_proof(data, expected_package_sha256)
    return False


def release_proof_runtime_evidence(search_dirs: list[Path] | None = None) -> Path | None:
    for path in discover_evidence_candidates(
        MN_RUNTIME_EVIDENCE_SCHEMA,
        MN_RUNTIME_EVIDENCE_PATTERNS,
        search_dirs,
    ):
        if evidence_file_is_release_proof(path):
            return path
    return None


def collect_acceptance_report(package_zip: Path, evidence_search_dirs: list[Path] | None = None) -> dict[str, Any]:
    script = ROOT / "release_acceptance.py"
    command = [sys.executable, str(script), str(package_zip), "--json"]
    runtime_evidence = release_proof_runtime_evidence(evidence_search_dirs or default_evidence_search_dirs(package_zip))
    if runtime_evidence:
        command.extend(["--mn-runtime-evidence", str(runtime_evidence)])
    result = subprocess.run(
        command,
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=False,
        timeout=180,
    )
    try:
        report = json.loads(result.stdout or "{}")
    except Exception:
        report = {}
    if not isinstance(report, dict):
        report = {}
    report.setdefault("releasable", False)
    report.setdefault("handoffCollection", {})
    report["handoffCollection"].update(
        {
            "command": command,
            "mnRuntimeEvidence": str(runtime_evidence) if runtime_evidence else "",
            "returncode": result.returncode,
            "stderrTail": (result.stderr or "")[-2000:],
            "stdoutLength": len(result.stdout or ""),
        }
    )
    return report


def native_highlight_template() -> dict[str, Any]:
    return {
        "schema": NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
        "generatedAt": "",
        "environment": {"host": "", "user": "", "platform": ""},
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "highlightScope": {"topicid": "", "bookmd5": ""},
        "events": {"latestPosted": None, "latestFailed": None},
        "highlightBlobCheck": {
            "status": "WARN",
            "topicid": "",
            "bookmd5": "",
            "native_highlight_blobs": 0,
            "db": "",
            "detail": "Fill by running Collect Native Highlight Evidence.command with an active MN4 PDF text selection, or run it first and reselect a short PDF text span within the 90-second wait window.",
        },
        "doctor": {"checks": [], "run": {}},
        "doctorHighlightCheck": None,
        "highlightAttempt": {
            "requested": False,
            "request": {},
            "wait": {},
            "cleanup": {},
            "event": None,
            "ok": False,
            "reason": "",
        },
        "ok": False,
        "problems": ["template-only"],
    }


def mn_runtime_template() -> dict[str, Any]:
    return {
        "schema": MN_RUNTIME_EVIDENCE_SCHEMA,
        "generatedAt": "",
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "ok": False,
        "message": "Fill by running Refresh MN Runtime.command after reopening the Codex panel.",
        "nextStep": "Reopen the Codex panel, click Refresh MN ability, then collect runtime evidence.",
        "statusBefore": {},
        "addonReloadAttempts": [],
        "probeResult": {},
        "statusAfter": {
            "mnRuntime": {
                "ready": False,
                "webControlsReady": False,
                "nativeApiReady": False,
                "staleRuntime": True,
                "runtimeHandlerStale": True,
                "pluginVersion": CURRENT_PLUGIN_VERSION,
            },
            "nativeApiCapabilities": {
                "available": False,
                "pluginVersion": CURRENT_PLUGIN_VERSION,
                "capabilityMatrix": {},
            },
        },
        "mnRuntime": {},
        "nativeApiCapabilities": {},
        "doctor": {},
    }


def cross_machine_template() -> dict[str, Any]:
    return {
        "schema": CROSS_MACHINE_EVIDENCE_SCHEMA,
        "generatedAt": "",
        "environment": {"host": "", "user": "", "platform": ""},
        "package": {"path": "", "exists": False, "sha256": ""},
        "doctor": {"checks": [], "run": {}},
        "installChecks": {
            "MN4 extension manifest": False,
            "Companion service": False,
            "LaunchAgent": False,
        },
        "ok": False,
        "problems": ["template-only"],
    }


def single_document_template() -> dict[str, Any]:
    return {
        "schema": SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
        "generatedAt": "",
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "topicid": "",
        "bookmd5": "",
        "ok": False,
        "summary": {
            "singleDocumentAcceptance": "BLOCK",
            "total": 0,
            "passed": 0,
            "blocked": 0,
        },
        "checks": [],
        "nextActions": [
            "Fill by running single_document_acceptance.py after testing all core workflows in the same MarginNote document."
        ],
    }


def gate_lines(title: str, items: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", ""]
    if not items:
        lines.extend(["None.", ""])
        return lines
    for item in items:
        name = str(item.get("name") or "unknown")
        detail = str(item.get("detail") or "")
        lines.append(f"### {name}")
        if detail:
            lines.append(detail)
        actions = item.get("nextActions") if isinstance(item.get("nextActions"), list) else []
        if actions:
            lines.append("")
            lines.append("Next actions:")
            for action in actions:
                lines.append(f"- {action}")
        lines.append("")
    return lines


def write_sha256_manifest(paths: list[Path], target: Path) -> None:
    lines = []
    for path in paths:
        if path.exists() and path.is_file():
            try:
                display_name = str(path.relative_to(target.parent))
            except ValueError:
                display_name = path.name
            lines.append(f"{sha256_file(path)}  {display_name}")
    target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def write_handoff_markdown(
    target: Path,
    *,
    package_zip: Path,
    package_pkg: Path | None,
    acceptance_report: dict[str, Any],
    included_files: list[str],
    diagnostic_files: list[str] | None = None,
) -> None:
    blockers = acceptance_report.get("blockers") if isinstance(acceptance_report.get("blockers"), list) else []
    warnings = acceptance_report.get("warnings") if isinstance(acceptance_report.get("warnings"), list) else []
    diagnostic_files = diagnostic_files or []
    lines = [
        "# Codex Companion Release Handoff",
        "",
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"Plugin version: {CURRENT_PLUGIN_VERSION}",
        f"Releasable: {bool(acceptance_report.get('releasable'))}",
        "",
        "## Included Artifacts",
        "",
    ]
    for name in included_files:
        lines.append(f"- {name}")
    lines.extend(
        [
            "",
            "## Diagnostic Evidence",
            "",
        ]
    )
    if diagnostic_files:
        lines.append("These files are included for debugging only; they are not release proof.")
        lines.append("")
        for name in diagnostic_files:
            lines.append(f"- {name}")
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Latest Package Hashes",
            "",
            f"- {package_zip.name}: `{sha256_file(package_zip) if package_zip.exists() else 'missing'}`",
        ]
    )
    if package_pkg and package_pkg.exists():
        lines.append(f"- {package_pkg.name}: `{sha256_file(package_pkg)}`")
    lines.extend(["", "Use `release_acceptance.json` as the exact machine-readable gate report."])
    lines.extend([""])
    lines.extend(gate_lines("Blocking Gates", [item for item in blockers if isinstance(item, dict)]))
    lines.extend(gate_lines("Warnings", [item for item in warnings if isinstance(item, dict)]))
    lines.extend(
        [
            "## Evidence Commands",
            "",
            "MN runtime evidence:",
            "",
            "```bash",
            "python3 refresh_mn_runtime.py --try-addon-url-reload --output ./mn-runtime-evidence.json",
            "python3 release_acceptance.py --mn-runtime-evidence ./mn-runtime-evidence.json",
            "```",
            "",
            "Native highlight evidence:",
            "",
            "```bash",
            "# First select text in an open MarginNote PDF.",
            "python3 release_acceptance.py --collect-native-highlight-evidence ./native-highlight-evidence.json --try-native-highlight",
            "python3 release_acceptance.py --native-highlight-evidence ./native-highlight-evidence.json",
            "```",
            "",
            "This waits for nativeHighlightSelectionPosted/nativeHighlightSelectionFailed and validates ZHIGHLIGHTS in the same topic/book scope.",
            "",
            "Single-document acceptance:",
            "",
            "```bash",
            "# During programmatic testing, add --record to send_action.py calls.",
            "python3 single_document_acceptance.py --topicid <topicid> --bookmd5 <bookmd5> --events events.jsonl --action-results release/evidence/action-results.jsonl --native-highlight-evidence native-highlight-evidence.json --output ./codex-companion-single-document-acceptance.json",
            "python3 release_acceptance.py --single-document-evidence ./codex-companion-single-document-acceptance.json",
            "```",
            "",
            "Double-click alternative: Collect Single Document Acceptance.command.",
            "",
            "This proves send/explain, cards, mindmaps, append-to-current-mindmap, settings, file upload, one-shot goal, queue/history, PDF cache, native highlight, and annotated PDF export were exercised in one topic/book scope.",
            "",
            "Cross-machine install evidence:",
            "",
            "```bash",
            "python3 release_acceptance.py ./CodexCompanion-0.4.20-latest-dist.zip --collect-cross-machine-evidence ./cross-machine-evidence.json",
            "python3 release_acceptance.py --cross-machine-evidence ./cross-machine-evidence.json",
            "```",
            "",
            "Signing and notarization:",
            "",
            "```bash",
            "python3 build_pkg.py release/CodexCompanion-0.4.20-latest-dist.zip --auto-sign --json",
            "python3 notarize_pkg.py release/CodexCompanion-0.4.20-latest.pkg --keychain-profile <profile> --json",
            "```",
            "",
        ]
    )
    target.write_text("\n".join(lines), encoding="utf-8")


def make_zip_from_dir(source_dir: Path, target_zip: Path) -> None:
    if target_zip.exists():
        target_zip.unlink()
    with zipfile.ZipFile(target_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_dir() or path.name.startswith("._"):
                continue
            archive.write(path, path.relative_to(source_dir.parent))


def copy_file_if_present(source: Path | None, target_dir: Path) -> list[str]:
    if not source:
        return []
    source = source.expanduser()
    if not source.exists() or not source.is_file():
        return []
    shutil.copy2(source, target_dir / source.name)
    return [source.name]


def copy_evidence_files(sources: list[Path], bundle_dir: Path) -> list[str]:
    if not sources:
        return []
    evidence_dir = bundle_dir / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    seen: set[str] = set()
    for source in sources:
        source = source.expanduser()
        if not source.exists() or not source.is_file() or source.name in seen:
            continue
        target = evidence_dir / source.name
        shutil.copy2(source, target)
        copied.append(f"evidence/{source.name}")
        seen.add(source.name)
    return copied


def copy_evidence_files_by_release_status(
    sources: list[Path],
    bundle_dir: Path,
    expected_package_sha256: str = "",
) -> tuple[list[str], list[str]]:
    if not sources:
        return [], []
    release_dir = bundle_dir / "evidence"
    diagnostic_dir = bundle_dir / "diagnostics" / "evidence"
    copied_release: list[str] = []
    copied_diagnostic: list[str] = []
    seen: set[str] = set()
    for source in sources:
        source = source.expanduser()
        if not source.exists() or not source.is_file() or source.name in seen:
            continue
        if evidence_file_is_release_proof(source, expected_package_sha256):
            release_dir.mkdir(parents=True, exist_ok=True)
            target = release_dir / source.name
            shutil.copy2(source, target)
            copied_release.append(f"evidence/{source.name}")
        else:
            diagnostic_dir.mkdir(parents=True, exist_ok=True)
            target = diagnostic_dir / source.name
            shutil.copy2(source, target)
            copied_diagnostic.append(f"diagnostics/evidence/{source.name}")
        seen.add(source.name)
    return copied_release, copied_diagnostic


def build_handoff_bundle(
    *,
    package_zip: Path,
    package_pkg: Path | None,
    acceptance_report: dict[str, Any],
    output_parent: Path,
    onedrive_parent: Path | None = DEFAULT_ONEDRIVE_PARENT,
    timestamp: str | None = None,
    evidence_search_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    timestamp = timestamp or timestamp_now()
    output_parent = output_parent.expanduser()
    output_parent.mkdir(parents=True, exist_ok=True)
    bundle_dir = output_parent / f"CodexCompanion-release-handoff-{timestamp}"
    if bundle_dir.exists():
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)

    included_files: list[str] = []
    included_files.extend(copy_file_if_present(package_zip, bundle_dir))
    included_files.extend(copy_file_if_present(package_pkg, bundle_dir))
    (bundle_dir / "release_acceptance.json").write_text(
        json.dumps(acceptance_report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    included_files.append("release_acceptance.json")
    (bundle_dir / "mn-runtime-evidence-template.json").write_text(
        json.dumps(mn_runtime_template(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    included_files.append("mn-runtime-evidence-template.json")
    (bundle_dir / "native-highlight-evidence-template.json").write_text(
        json.dumps(native_highlight_template(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    included_files.append("native-highlight-evidence-template.json")
    (bundle_dir / "cross-machine-evidence-template.json").write_text(
        json.dumps(cross_machine_template(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    included_files.append("cross-machine-evidence-template.json")
    (bundle_dir / "single-document-acceptance-template.json").write_text(
        json.dumps(single_document_template(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    included_files.append("single-document-acceptance-template.json")
    evidence_dirs = evidence_search_dirs or default_evidence_search_dirs(package_zip)
    expected_package_sha256 = sha256_file(package_zip) if package_zip.exists() else ""
    release_evidence_files, diagnostic_evidence_files = copy_evidence_files_by_release_status(
        discover_evidence_files(evidence_dirs, expected_package_sha256),
        bundle_dir,
        expected_package_sha256,
    )
    included_files.extend(release_evidence_files)
    included_files.extend(diagnostic_evidence_files)

    handoff_md = bundle_dir / "RELEASE_HANDOFF.md"
    final_file_list = included_files + ["RELEASE_HANDOFF.md", "SHA256SUMS.txt"]
    write_handoff_markdown(
        handoff_md,
        package_zip=package_zip,
        package_pkg=package_pkg,
        acceptance_report=acceptance_report,
        included_files=final_file_list,
        diagnostic_files=diagnostic_evidence_files,
    )
    included_files.append("RELEASE_HANDOFF.md")
    write_sha256_manifest([bundle_dir / name for name in included_files], bundle_dir / "SHA256SUMS.txt")
    included_files.append("SHA256SUMS.txt")

    bundle_zip = output_parent / f"{bundle_dir.name}.zip"
    make_zip_from_dir(bundle_dir, bundle_zip)

    onedrive_bundle_dir = ""
    onedrive_bundle_zip = ""
    if onedrive_parent:
        onedrive_parent = onedrive_parent.expanduser()
        onedrive_parent.mkdir(parents=True, exist_ok=True)
        target_dir = onedrive_parent / bundle_dir.name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        shutil.copytree(bundle_dir, target_dir)
        target_zip = onedrive_parent / bundle_zip.name
        shutil.copy2(bundle_zip, target_zip)
        onedrive_bundle_dir = str(target_dir)
        onedrive_bundle_zip = str(target_zip)

    return {
        "ok": bool(package_zip.exists() and (bundle_dir / "RELEASE_HANDOFF.md").exists() and bundle_zip.exists()),
        "bundleDir": str(bundle_dir),
        "bundleZip": str(bundle_zip),
        "onedriveBundleDir": onedrive_bundle_dir,
        "onedriveBundleZip": onedrive_bundle_zip,
        "includedFiles": included_files,
        "releasable": bool(acceptance_report.get("releasable")),
        "blockerCount": len(acceptance_report.get("blockers") or []),
        "warningCount": len(acceptance_report.get("warnings") or []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare a Codex Companion release handoff bundle.")
    parser.add_argument("package", nargs="?", default=str(DEFAULT_PACKAGE_ZIP), help="Latest release zip.")
    parser.add_argument("--pkg", default=str(DEFAULT_PACKAGE_PKG), help="Latest pkg wrapper, if available.")
    parser.add_argument("--acceptance-json", help="Existing release_acceptance.py --json report.")
    parser.add_argument("--output-parent", default=str(DEFAULT_OUTPUT_PARENT), help="Directory for handoff bundles.")
    parser.add_argument("--onedrive-parent", default=str(DEFAULT_ONEDRIVE_PARENT), help="OneDrive mirror directory.")
    parser.add_argument("--no-onedrive", action="store_true", help="Do not mirror the bundle to OneDrive.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    package_zip = Path(args.package).expanduser()
    package_pkg = Path(args.pkg).expanduser() if args.pkg else None
    if args.acceptance_json:
        acceptance_report = load_json(Path(args.acceptance_json))
    else:
        acceptance_report = collect_acceptance_report(package_zip)

    result = build_handoff_bundle(
        package_zip=package_zip,
        package_pkg=package_pkg,
        acceptance_report=acceptance_report,
        output_parent=Path(args.output_parent),
        onedrive_parent=None if args.no_onedrive else Path(args.onedrive_parent),
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Handoff bundle: {result['bundleDir']}")
        print(f"Handoff zip: {result['bundleZip']}")
        if result.get("onedriveBundleZip"):
            print(f"OneDrive zip: {result['onedriveBundleZip']}")
        print(f"Release gate: {'PASS' if result.get('releasable') else 'BLOCKED'}")
        print(f"Blockers: {result.get('blockerCount', 0)} / Warnings: {result.get('warningCount', 0)}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
