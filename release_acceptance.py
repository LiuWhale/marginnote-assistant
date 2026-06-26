#!/usr/bin/env python3
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request


ROOT = Path(__file__).resolve().parent
DEFAULT_PACKAGE = ROOT / "release/CodexCompanion-0.4.29-latest-dist.zip"
LIVE_EXTENSION = Path.home() / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
MN_DATABASE = Path.home() / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
CURRENT_PLUGIN_VERSION = "0.4.29"
EVIDENCE_SCHEMA = "codex-companion-cross-machine-install-v1"
NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA = "codex-companion-native-highlight-v1"
MN_RUNTIME_EVIDENCE_SCHEMA = "codex-companion-mn-runtime-v1"
SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA = "codex-companion-single-document-acceptance-v1"
DEFAULT_COMPANION_URL = "http://127.0.0.1:48761"
CROSS_MACHINE_EVIDENCE_PATTERNS = [
    "codex-companion-cross-machine-evidence-*.json",
    "CodexCompanion-cross-machine-evidence-*.json",
    "cross-machine-evidence*.json",
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
RUNTIME_SOURCE_RELATIVE_FILES = [
    "main.js",
    "CodexPanelController.js",
    "CodexWebPanelController.js",
    "web/index.html",
    "web/app.js",
    "web/app.css",
    "web/styles.css",
]
REQUIRED_NATIVE_HANDLER_FEATURES = [
    "native-highlight-arm-next-selection-default",
    "native-highlight-prefer-next-selection-v1",
    "native-highlight-command-prepared",
    "selection-popup-diagnostics-v1",
    "native-highlight-selection-poll-v1",
    "selection-popup-scene-observer-v1",
    "selection-popup-notebook-rebind-v1",
    "native-highlight-selection-text-resolver-v1",
    "context-refresh-clears-stale-selection-v1",
    "ai-edit-transaction-rollback-v1",
    "ai-edit-undo-rollback-v2",
    "native-mn-object-registry-scan-v1",
    "native-mn-object-existence-probe-v1",
    "native-mindmap-diff-apply-create-v1",
    "native-mindmap-delete-suggestion-confirm-v1",
]
INSTALL_EVIDENCE_CHECKS = [
    "MN4 extension manifest",
    "Companion service",
    "LaunchAgent",
]


@dataclass
class Gate:
    name: str
    status: str
    detail: str
    evidence: dict[str, Any] | None = None
    nextActions: list[str] = field(default_factory=list)


def resolve_layout(root: Path) -> dict[str, Path]:
    root = root.resolve()
    if (root / "doctor.py").exists() and (root / "tests").is_dir():
        project_root = root
    elif (root / "companion/doctor.py").exists() and (root / "companion/tests").is_dir():
        project_root = root / "companion"
    else:
        project_root = root
    return {
        "packageRoot": root,
        "projectRoot": project_root,
        "doctor": project_root / "doctor.py",
        "tests": project_root / "tests",
        "acceptance": root / "release_acceptance.py",
    }


LAYOUT = resolve_layout(ROOT)


def run(
    args: list[str],
    timeout: float = 60,
    stdout_limit: int | None = 4000,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> dict[str, Any]:
    completed = subprocess.run(
        args,
        cwd=str(cwd or LAYOUT["projectRoot"]),
        text=True,
        capture_output=True,
        timeout=timeout,
        check=False,
        env=env,
    )
    stdout = completed.stdout if stdout_limit is None else completed.stdout[-stdout_limit:]
    stderr = completed.stderr if stdout_limit is None else completed.stderr[-stdout_limit:]
    return {
        "args": args,
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "ok": completed.returncode == 0,
    }


def compact_command_result(result: dict[str, Any], parsed_items: int | None = None) -> dict[str, Any]:
    compact = dict(result)
    stdout = str(compact.get("stdout") or "")
    compact["stdoutLength"] = len(stdout)
    if parsed_items is not None:
        compact["stdout"] = f"<parsed {parsed_items} JSON items>"
    elif len(stdout) > 1200:
        compact["stdout"] = stdout[-1200:]
    return compact


def command_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = dict(os.environ)
    path_parts = [
        "/opt/homebrew/bin",
        "/opt/homebrew/sbin",
        "/usr/local/bin",
        "/usr/bin",
        "/bin",
        "/usr/sbin",
        "/sbin",
        str(Path.home() / ".npm-global/bin"),
    ]
    existing = env.get("PATH", "")
    if existing:
        path_parts.append(existing)
    env["PATH"] = ":".join(path_parts)
    if extra:
        env.update({str(key): str(value) for key, value in extra.items()})
    return env


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_default(key: str) -> str:
    try:
        result = subprocess.run(
            ["/usr/bin/defaults", "read", "QReader.MarginStudy.easy", key],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip().strip('"')


def companion_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def post_json(base_url: str, path: str, payload: dict[str, Any], timeout: int = 30) -> dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        companion_url(base_url, path),
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


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


def default_evidence_search_dirs(package: Path | None = None) -> list[Path]:
    dirs = [
        Path.cwd(),
        LAYOUT["packageRoot"] / "release/evidence",
        LAYOUT["packageRoot"] / "release",
        LAYOUT["packageRoot"],
        LAYOUT["projectRoot"],
    ]
    if package:
        package = package.expanduser()
        dirs.extend([package.parent, package.parent / "evidence"])
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


def auto_discovered_evidence_result(
    schema: str,
    patterns: list[str],
    evaluator: Any,
    search_dirs: list[Path] | None = None,
) -> dict[str, Any] | None:
    latest_invalid: dict[str, Any] | None = None
    for candidate in discover_evidence_candidates(schema, patterns, search_dirs):
        result = evaluator(candidate)
        result["autoDiscovered"] = True
        if result.get("ok"):
            return result
        if latest_invalid is None:
            latest_invalid = result
    return latest_invalid


def extract_release_extension(package: Path, target_dir: Path) -> Path | None:
    package = package.expanduser()
    if not package.exists():
        return None
    try:
        with zipfile.ZipFile(package) as archive:
            names = [
                name
                for name in archive.namelist()
                if "/extension/codex.mn.assistant/" in name and not name.endswith("/")
            ]
            if not names:
                return None
            archive.extractall(target_dir, names)
    except Exception:
        return None
    candidates = sorted(target_dir.glob("*/extension/codex.mn.assistant"))
    if candidates:
        return candidates[0].resolve()
    return None


def machine_identity() -> dict[str, str]:
    return {
        "host": platform.node() or "",
        "user": getpass.getuser() or "",
        "platform": platform.platform() or "",
    }


def check_by_name(checks: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for item in checks:
        if str(item.get("name") or "") == name:
            return item
    return None


def required_install_checks(checks: list[dict[str, Any]]) -> dict[str, bool]:
    return {
        name: bool((check_by_name(checks, name) or {}).get("status") == "OK")
        for name in INSTALL_EVIDENCE_CHECKS
    }


def check_gate(
    name: str,
    checks: list[dict[str, Any]],
    check_name: str,
    success_detail: str,
    missing_detail: str,
) -> Gate:
    item = check_by_name(checks, check_name)
    if not item:
        return Gate(name, "BLOCK", missing_detail, {"check": check_name})
    status = str(item.get("status") or "")
    detail = str(item.get("detail") or "")
    if status == "OK":
        return Gate(name, "PASS", success_detail or detail, {"check": item})
    return Gate(name, "BLOCK", detail or f"{check_name} is {status}", {"check": item})


def next_actions_for_gate(name: str, detail: str = "") -> list[str]:
    detail_lower = detail.lower()
    if name == "unit_tests":
        return ["Run python3 -m unittest discover -s tests and fix the failing test output."]
    if name == "syntax_checks":
        return ["Run python3 release_acceptance.py release/CodexCompanion-0.4.29-latest-dist.zip --skip-tests to see the exact syntax command failure."]
    if name == "release_zip_smoke":
        return ["Run python3 package_release.py 0.4.29, then rerun release_smoke_test.py on the latest dist zip."]
    if name == "install_dry_run":
        return ["Run python3 release_smoke_test.py release/CodexCompanion-0.4.29-latest-dist.zip --install-dry-run and fix the install/uninstall script failure."]
    if name == "runtime_web_controls":
        if "reload_web_panel" in detail_lower:
            return [
                "在 MarginNote 4 里关闭再重新打开 Codex 面板；当前运行态不认识 reload_web_panel，说明刷新命令无法让旧 handler 自己热更新。",
                "重新打开面板后点击“刷新MN能力”，或双击 Refresh MN Runtime.command 采集新的 MN runtime evidence。",
                "若重新打开面板后仍显示旧 handler，到设置页点击“发布验收”，在发布验收结果里的“重启MN4”恢复动作中确认后再发送 restart_marginnote4。",
                "随后 rerun release_acceptance.py，或带 --mn-runtime-evidence <json> 验证 ready=True 且 runtimeHandlerStale=False。",
            ]
        actions = [
            "Open the Codex Companion Settings tab, run Release Acceptance, then use the 重启MN4 recovery action shown in the release result if the runtime is still stale; it asks for confirmation before sending restart_marginnote4.",
            "After MarginNote 4 reloads, reopen the Codex panel and click Refresh MN ability, then rerun release_acceptance.py.",
            "Optional evidence path: run Refresh MN Runtime.command and rerun release_acceptance.py with --mn-runtime-evidence <json> once it reports ready=True, webPanelReloadResult.ok=True, and runtimeHandlerStale=False.",
        ]
        if "stale" not in detail_lower:
            actions.insert(0, "Open a notebook in MarginNote 4 and open the Codex Companion panel so the Web controls can report readiness.")
        return actions
    if name == "native_api_matrix":
        if "reload_web_panel" in detail_lower:
            return [
                "先在 MarginNote 4 里关闭再重新打开 Codex 面板；当前运行态把 reload_web_panel 当作 unknown，native probe 结果来自旧 handler。",
                "面板重新打开后点击“刷新MN能力”，确认 nativeApiCapabilities 重新上报 capabilityMatrix。",
                "再运行 Refresh MN Runtime.command 或 release_acceptance.py，确认 runtimeHandlerStale=False。",
            ]
        actions = [
            "Click Refresh MN ability in the Codex Companion panel to rerun the native API probe from the current MarginNote runtime.",
            "If runtime_handler_stale=True or probe_native_api_capabilities is unknown, open Settings, run Release Acceptance, use the 重启MN4 recovery action shown there, then reopen the panel.",
        ]
        return actions
    if name == "native_visible_highlight":
        return [
            "Open a PDF in MarginNote 4, select a short text span, click 高亮选区, and confirm the highlight is visible in the document.",
            "Run Collect Native Highlight Evidence.command, or use --collect-native-highlight-evidence, then rerun release_acceptance.py with --native-highlight-evidence <json>.",
            "Run python3 doctor.py --json and rerun release_acceptance.py after the Native highlight blobs check reports rows with ZHIGHLIGHTS.",
        ]
    if name == "release_sha256_manifest":
        if "permission" in detail.lower() or "Full Disk Access" in detail:
            return [
                "Give the Companion service/Python/Terminal Full Disk Access so it can read OneDrive SHA256SUMS.txt.",
                "Then rerun release_acceptance.py or click 发布验收 in the Codex Companion panel.",
            ]
        return [
            "Run python3 package_release.py, then python3 build_pkg.py release/CodexCompanion-0.4.29-latest-dist.zip --json.",
            "Copy release/SHA256SUMS.txt to the OneDrive Codex Companion folder and rerun release_acceptance.py.",
        ]
    if name == "release_maintainer_prerequisites":
        return [
            "Install exactly one Developer ID Installer certificate for one-click Build Signed Package.command, or pass --sign-identity explicitly.",
            "Configure notarytool credentials with xcrun notarytool store-credentials, NOTARYTOOL_KEYCHAIN_PROFILE, or Apple ID environment variables.",
        ]
    if name == "signed_pkg":
        return [
            "Install a Developer ID Installer certificate in Keychain, then run Build Signed Package.command.",
            "CLI alternative: python3 build_pkg.py release/CodexCompanion-0.4.29-latest-dist.zip --auto-sign --json.",
        ]
    if name == "notarized_pkg":
        return [
            "Store Apple notarization credentials with xcrun notarytool store-credentials, then run Notarize Package.command.",
            "CLI alternative: python3 notarize_pkg.py release/CodexCompanion-0.4.29-latest.pkg --keychain-profile <profile> --json.",
        ]
    if name == "cross_machine_install":
        return [
            "On a different macOS user or machine, install the latest release zip and run Collect Cross-Machine Evidence.command.",
            "Bring the generated JSON back and rerun release_acceptance.py with --cross-machine-evidence <json>.",
        ]
    if name == "single_document_acceptance":
        return [
            "在同一个打开的 MarginNote 文档里依次跑发送/解释、制卡、脑图、补脑图、设置保存、上传文件、一次性目标、队列/历史、缓存 PDF、高亮和导出。",
            "用 send_action.py 做程序化验收时加 --record，action result 会追加到 release/evidence/action-results.jsonl。",
            "完成同一文档测试和 native highlight evidence 后，双击 Collect Single Document Acceptance.command 生成桌面 JSON；脚本会自动发现 release/evidence 或桌面上的高亮证据。",
            "CLI 示例：python3 single_document_acceptance.py --topicid <topicid> --bookmd5 <bookmd5> --events events.jsonl --action-results release/evidence/action-results.jsonl --output release/evidence/codex-companion-single-document-acceptance-$(date +%Y%m%d-%H%M%S).json",
        ]
    return ["Inspect the gate evidence above, fix the blocker, and rerun release_acceptance.py."]


def gate_payload(gate: Gate) -> dict[str, Any]:
    payload = gate.__dict__.copy()
    if gate.status in {"BLOCK", "WARN"} and not payload.get("nextActions"):
        payload["nextActions"] = next_actions_for_gate(gate.name, gate.detail)
    return payload


def native_highlight_evidence_blocker_detail(
    native_highlight_evidence: dict[str, Any],
    fallback_detail: str,
) -> str:
    parts: list[str] = []
    problems = native_highlight_evidence.get("problems") if isinstance(native_highlight_evidence.get("problems"), list) else []
    if problems:
        parts.append("native highlight evidence incomplete: " + ", ".join(str(item) for item in problems[:6]))
    attempt_reason = str(native_highlight_evidence.get("highlightAttemptReason") or "").strip()
    if not attempt_reason:
        attempt_reason = native_highlight_attempt_reason(native_highlight_evidence)
    if attempt_reason:
        parts.append(f"active attempt reason: {attempt_reason}")
    blob_check = (
        native_highlight_evidence.get("highlightBlobCheck")
        if isinstance(native_highlight_evidence.get("highlightBlobCheck"), dict)
        else {}
    )
    blob_detail = str(blob_check.get("detail") or "").strip()
    if blob_detail:
        parts.append(blob_detail)
    if fallback_detail and fallback_detail not in parts:
        parts.append(fallback_detail)
    return "; ".join(parts) or "visible native highlight evidence is not proven"


def validate_mn_runtime_evidence(data: dict[str, Any] | None) -> dict[str, Any]:
    data = data if isinstance(data, dict) else {}
    prevalidated = (
        isinstance(data.get("mnRuntime"), dict)
        and isinstance(data.get("nativeApiCapabilities"), dict)
        and "ok" in data
        and "problems" in data
        and "schema" not in data
    )
    problems: list[str] = list(data.get("problems") or []) if prevalidated and isinstance(data.get("problems"), list) else []
    current_runtime_source: dict[str, Any] | None = None
    evidence_reference_time: float | None = None
    if prevalidated:
        runtime = data["mnRuntime"]
        caps = data["nativeApiCapabilities"]
    else:
        if data.get("schema") != MN_RUNTIME_EVIDENCE_SCHEMA:
            problems.append("schema-mismatch")

        status_after = data.get("statusAfter") if isinstance(data.get("statusAfter"), dict) else {}
        runtime = status_after.get("mnRuntime") if isinstance(status_after.get("mnRuntime"), dict) else None
        if runtime is None and isinstance(data.get("mnRuntime"), dict):
            runtime = data["mnRuntime"]
        caps = status_after.get("nativeApiCapabilities") if isinstance(status_after.get("nativeApiCapabilities"), dict) else None
        if caps is None and isinstance(data.get("nativeApiCapabilities"), dict):
            caps = data["nativeApiCapabilities"]

    if not isinstance(runtime, dict):
        runtime = {}
        problems.append("missing-mn-runtime")
    if not isinstance(caps, dict):
        caps = {}
        problems.append("missing-native-api-capabilities")

    plugin_version = str(data.get("pluginVersion") or runtime.get("pluginVersion") or caps.get("pluginVersion") or "")
    if not plugin_version:
        problems.append("missing-plugin-version")
    elif plugin_version != CURRENT_PLUGIN_VERSION:
        problems.append("plugin-version-mismatch")

    if not bool(runtime.get("ready")):
        problems.append("runtime-not-ready")
    if not bool(runtime.get("webControlsReady")):
        problems.append("web-controls-not-ready")
    if not bool(runtime.get("nativeApiReady")):
        problems.append("native-api-not-ready")
    if bool(runtime.get("staleRuntime")):
        problems.append("runtime-stale")
    if bool(runtime.get("runtimeHandlerStale")):
        problems.append("runtime-handler-stale")

    matrix = caps.get("capabilityMatrix") if isinstance(caps.get("capabilityMatrix"), dict) else {}
    if not bool(caps.get("available")):
        problems.append("native-api-unavailable")
    if not matrix:
        problems.append("missing-capability-matrix")
    required_handler_features = installed_required_native_handler_features()
    native_handler_features = [
        str(item)
        for item in caps.get("handlerFeatures", [])
        if item
    ] if isinstance(caps.get("handlerFeatures"), list) else []
    missing_handler_features = [
        feature for feature in required_handler_features if feature not in native_handler_features
    ]
    for feature in missing_handler_features:
        problems.append(f"missing-native-handler-feature:{feature}")

    current_runtime_source = latest_runtime_source()
    evidence_reference_time = mn_runtime_evidence_reference_time(data, runtime)
    if (
        current_runtime_source
        and evidence_reference_time is not None
        and float(current_runtime_source.get("mtime") or 0) > evidence_reference_time + 1
    ):
        problems.append("runtime-evidence-stale-against-current-source")

    # Keep ordering stable while avoiding duplicate problems when prevalidated data already contains one.
    problems = list(dict.fromkeys(problems))

    result = {
        "ok": not problems,
        "problems": problems,
        "pluginVersion": plugin_version,
        "mnRuntime": runtime,
        "nativeApiCapabilities": caps,
        "requiredNativeHandlerFeatures": required_handler_features,
        "nativeHandlerFeatures": native_handler_features,
        "missingNativeHandlerFeatures": missing_handler_features,
    }
    if current_runtime_source:
        result["currentRuntimeSource"] = current_runtime_source
    if evidence_reference_time is not None:
        result["evidenceReferenceTime"] = evidence_reference_time
    if data.get("path"):
        result["path"] = data.get("path")
    return result


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


def installed_required_native_handler_features(extension_dir: Path | None = None) -> list[str]:
    extension_dir = extension_dir or LIVE_EXTENSION
    try:
        text = (extension_dir / "main.js").read_text(encoding="utf-8")
    except Exception:
        return list(REQUIRED_NATIVE_HANDLER_FEATURES)
    features = [feature for feature in REQUIRED_NATIVE_HANDLER_FEATURES if feature in text]
    return features or list(REQUIRED_NATIVE_HANDLER_FEATURES)


def warning_gate(
    name: str,
    doctor_checks: list[dict[str, Any]],
    check_name: str,
    success_detail: str,
) -> Gate | None:
    item = check_by_name(doctor_checks, check_name)
    if not item:
        return None
    status = str(item.get("status") or "")
    detail = str(item.get("detail") or "")
    if status == "OK":
        return Gate(name, "PASS", success_detail or detail, {"check": item})
    return Gate(name, "WARN", detail or f"{check_name} is {status}", {"check": item})


def evaluate_acceptance(
    *,
    unit_tests_ok: bool,
    syntax_ok: bool,
    smoke: dict[str, Any],
    doctor_checks: list[dict[str, Any]],
    cross_machine_verified: bool,
    native_highlight_evidence: dict[str, Any] | None = None,
    mn_runtime_evidence: dict[str, Any] | None = None,
    single_document_acceptance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gates: list[Gate] = []
    mn_runtime_validation = validate_mn_runtime_evidence(mn_runtime_evidence) if mn_runtime_evidence else None
    gates.append(
        Gate(
            "unit_tests",
            "PASS" if unit_tests_ok else "BLOCK",
            "unit test suite passed" if unit_tests_ok else "unit test suite failed",
        )
    )
    gates.append(
        Gate(
            "syntax_checks",
            "PASS" if syntax_ok else "BLOCK",
            "Python/JS/shell syntax checks passed" if syntax_ok else "syntax checks failed",
        )
    )

    smoke_ok = bool(smoke.get("ok"))
    gates.append(
        Gate(
            "release_zip_smoke",
            "PASS" if smoke_ok else "BLOCK",
            "release zip passed smoke checks" if smoke_ok else "release zip smoke failed",
            {"smoke": smoke},
        )
    )
    dry_run = smoke.get("installDryRun") if isinstance(smoke.get("installDryRun"), dict) else {}
    dry_run_ok = bool(dry_run.get("ok"))
    gates.append(
        Gate(
            "install_dry_run",
            "PASS" if dry_run_ok else "BLOCK",
            "install/uninstall dry-run passed" if dry_run_ok else "install/uninstall dry-run missing or failed",
            {"installDryRun": dry_run},
        )
    )

    runtime_gate = check_gate(
        "runtime_web_controls",
        doctor_checks,
        "MN4 runtime Web controls",
        "current MN4 runtime reported all required Web controls",
        "missing doctor check: MN4 runtime Web controls",
    )
    native_api_gate = check_gate(
        "native_api_matrix",
        doctor_checks,
        "MN4 native API probe",
        "current MN4 runtime reported native capability matrix",
        "missing doctor check: MN4 native API probe",
    )
    if mn_runtime_validation and mn_runtime_validation.get("ok"):
        runtime_gate = Gate(
            "runtime_web_controls",
            "PASS",
            "structured MN4 runtime evidence proves current Web controls and runtime readiness",
            {"mnRuntimeEvidence": mn_runtime_validation},
        )
        native_api_gate = Gate(
            "native_api_matrix",
            "PASS",
            "structured MN4 runtime evidence proves current native capability matrix",
            {"mnRuntimeEvidence": mn_runtime_validation},
        )
    gates.append(runtime_gate)
    gates.append(native_api_gate)
    native_highlight_gate = check_gate(
        "native_visible_highlight",
        doctor_checks,
        "Native highlight blobs",
        "MN4 database contains visible native highlight evidence",
        "missing doctor check: Native highlight blobs",
    )
    if native_highlight_gate.status != "PASS" and native_highlight_evidence and native_highlight_evidence.get("ok"):
        native_highlight_gate = Gate(
            "native_visible_highlight",
            "PASS",
            "structured native highlight evidence proves visible MN4 highlight",
            {"nativeHighlightEvidence": native_highlight_evidence},
        )
    elif native_highlight_gate.status != "PASS" and native_highlight_evidence:
        native_highlight_gate = Gate(
            "native_visible_highlight",
            "BLOCK",
            native_highlight_evidence_blocker_detail(native_highlight_evidence, native_highlight_gate.detail),
            {
                "nativeHighlightEvidence": native_highlight_evidence,
                "doctorGate": native_highlight_gate.evidence,
            },
        )
    gates.append(native_highlight_gate)
    gates.append(
        check_gate(
            "release_sha256_manifest",
            doctor_checks,
            "Release SHA256 manifest",
            "SHA256SUMS covers the latest zip/pkg and matches OneDrive",
            "missing doctor check: Release SHA256 manifest",
        )
    )
    prerequisites_gate = warning_gate(
        "release_maintainer_prerequisites",
        doctor_checks,
        "Release maintainer prerequisites",
        "local maintainer machine has signing and notarytool prerequisites",
    )
    if prerequisites_gate:
        gates.append(prerequisites_gate)

    pkg_check = check_by_name(doctor_checks, "Latest RC pkg")
    if not pkg_check:
        gates.append(Gate("signed_pkg", "BLOCK", "missing doctor check: Latest RC pkg"))
        gates.append(Gate("notarized_pkg", "BLOCK", "missing doctor check: Latest RC pkg"))
    else:
        pkg_status = str(pkg_check.get("status") or "")
        pkg_detail = str(pkg_check.get("detail") or "")
        pkg_evidence = pkg_check.get("evidence") if isinstance(pkg_check.get("evidence"), dict) else {}
        signed = bool(pkg_evidence.get("signed")) or (
            pkg_status == "OK" and "no signature" not in pkg_detail.lower()
        )
        notarized = bool(pkg_evidence.get("notarized")) or (
            pkg_status == "OK" and "notarized" in pkg_detail.lower()
        )
        gates.append(
            Gate(
                "signed_pkg",
                "PASS" if signed else "BLOCK",
                "latest pkg is signed" if signed else (pkg_detail or f"Latest RC pkg is {pkg_status}"),
                {"check": pkg_check},
            )
        )
        gates.append(
            Gate(
                "notarized_pkg",
                "PASS" if notarized else "BLOCK",
                "latest pkg is notarized and stapled"
                if notarized
                else (pkg_detail or f"Latest RC pkg is {pkg_status}"),
                {"check": pkg_check},
            )
        )

    gates.append(
        Gate(
            "cross_machine_install",
            "PASS" if cross_machine_verified else "BLOCK",
            "cross-machine install evidence is present"
            if cross_machine_verified
            else "missing cross-machine install evidence",
        )
    )
    if single_document_acceptance is not None:
        single_doc_ok = bool(single_document_acceptance.get("ok"))
        problems = single_document_acceptance.get("problems")
        blocked_checks = single_document_acceptance.get("blockedChecks")
        detail = (
            "all core button workflows passed in one MarginNote document"
            if single_doc_ok
            else "single-document acceptance is missing or incomplete"
        )
        if not single_doc_ok:
            parts = []
            if isinstance(problems, list) and problems:
                parts.append(", ".join(str(item) for item in problems[:8]))
            if isinstance(blocked_checks, list) and blocked_checks:
                parts.append("blocked checks: " + ", ".join(str(item) for item in blocked_checks[:8]))
            detail = "; ".join(parts) or detail
        gates.append(
            Gate(
                "single_document_acceptance",
                "PASS" if single_doc_ok else "BLOCK",
                detail,
                {"singleDocumentAcceptance": single_document_acceptance},
            )
        )

    payload = {
        "releasable": not any(gate.status == "BLOCK" for gate in gates),
        "blockers": [gate_payload(gate) for gate in gates if gate.status == "BLOCK"],
        "warnings": [gate_payload(gate) for gate in gates if gate.status == "WARN"],
        "gates": [gate_payload(gate) for gate in gates],
    }
    return payload


def run_unit_tests(package: Path | None = None) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="codex-companion-acceptance-") as tmp:
        extra_env: dict[str, str] = {}
        if package:
            extension_dir = extract_release_extension(package, Path(tmp))
            if extension_dir:
                extra_env["CODEX_MN_TEST_EXTENSION_DIR"] = str(extension_dir)
        return run(
            [sys.executable, "-m", "unittest", "discover", "-s", str(LAYOUT["tests"])],
            timeout=120,
            cwd=LAYOUT["projectRoot"],
            env=command_env(extra_env),
        )


def run_syntax_checks() -> dict[str, Any]:
    commands = [
        [
            sys.executable,
            "-m",
            "py_compile",
            str(LAYOUT["projectRoot"] / "companion.py"),
            str(LAYOUT["projectRoot"] / "doctor.py"),
            str(LAYOUT["projectRoot"] / "package_release.py"),
            str(LAYOUT["projectRoot"] / "send_action.py"),
            str(LAYOUT["projectRoot"] / "audit_highlights.py"),
            str(LAYOUT["projectRoot"] / "verify_after_unlock.py"),
            str(LAYOUT["packageRoot"] / "release_smoke_test.py"),
            str(LAYOUT["packageRoot"] / "single_document_acceptance.py"),
            str(LAYOUT["packageRoot"] / "build_pkg.py"),
            str(LAYOUT["packageRoot"] / "notarize_pkg.py"),
            str(LAYOUT["packageRoot"] / "prepare_release_handoff.py"),
            str(LAYOUT["acceptance"]),
        ],
        ["node", "--check", str(LIVE_EXTENSION / "web/app.js")],
        ["node", "--check", str(LIVE_EXTENSION / "main.js")],
        ["node", "--check", str(LIVE_EXTENSION / "CodexWebPanelController.js")],
        ["node", "--check", str(LIVE_EXTENSION / "CodexPanelController.js")],
        [
            "zsh",
            "-n",
            str(LAYOUT["packageRoot"] / "install.sh"),
            str(LAYOUT["packageRoot"] / "uninstall.sh"),
            str(LAYOUT["packageRoot"] / "Install Codex Companion.command"),
            str(LAYOUT["packageRoot"] / "Uninstall Codex Companion.command"),
            str(LAYOUT["packageRoot"] / "Collect Native Highlight Evidence.command"),
            str(LAYOUT["packageRoot"] / "Collect Single Document Acceptance.command"),
            str(LAYOUT["packageRoot"] / "Collect Cross-Machine Evidence.command"),
            str(LAYOUT["packageRoot"] / "Build Signed Package.command"),
            str(LAYOUT["packageRoot"] / "Notarize Package.command"),
            str(LAYOUT["packageRoot"] / "Prepare Release Handoff.command"),
            str(LAYOUT["projectRoot"] / "install_companion.sh"),
            str(LAYOUT["projectRoot"] / "install_extension.sh"),
            str(LAYOUT["projectRoot"] / "uninstall_companion.sh"),
            str(LAYOUT["projectRoot"] / "start_companion.sh"),
            str(LAYOUT["projectRoot"] / "stop_companion.sh"),
            str(LAYOUT["projectRoot"] / "package_release.sh"),
            str(LAYOUT["projectRoot"] / "verify_when_unlocked.sh"),
            str(LAYOUT["projectRoot"] / "run_companion_foreground.sh"),
        ],
    ]
    results = [run(command, timeout=60, cwd=LAYOUT["packageRoot"]) for command in commands]
    return {"ok": all(item["ok"] for item in results), "results": results}


def run_smoke(package: Path) -> dict[str, Any]:
    import release_smoke_test

    result = release_smoke_test.inspect_package(package)
    payload = result.__dict__.copy()
    if result.ok:
        payload["installDryRun"] = release_smoke_test.run_install_dry_run(package)
        payload["ok"] = bool(payload["installDryRun"].get("ok"))
    else:
        payload["ok"] = False
    return payload


def run_doctor_json() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    completed = run(
        [sys.executable, str(LAYOUT["doctor"]), "--json"],
        timeout=30,
        stdout_limit=None,
        cwd=LAYOUT["projectRoot"],
    )
    try:
        data = json.loads(str(completed.get("stdout") or "[]"))
    except Exception:
        data = []
    checks = data if isinstance(data, list) else []
    return checks, compact_command_result(completed, parsed_items=len(checks))


def collect_cross_machine_evidence(package: Path) -> dict[str, Any]:
    package = package.expanduser()
    checks, doctor_run = run_doctor_json()
    install_checks = required_install_checks(checks)
    package_exists = package.exists()
    evidence = {
        "schema": EVIDENCE_SCHEMA,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "environment": machine_identity(),
        "package": {
            "path": str(package),
            "exists": package_exists,
            "sha256": sha256_file(package) if package_exists else "",
        },
        "doctor": {
            "checks": checks,
            "run": doctor_run,
        },
        "installChecks": install_checks,
    }
    evidence["ok"] = bool(package_exists and all(install_checks.values()))
    return evidence


def validate_cross_machine_evidence(
    data: dict[str, Any],
    expected_package_sha256: str = "",
    current_identity: dict[str, str] | None = None,
) -> dict[str, Any]:
    problems: list[str] = []
    if data.get("schema") != EVIDENCE_SCHEMA:
        problems.append("schema-mismatch")

    environment = data.get("environment") if isinstance(data.get("environment"), dict) else {}
    current = current_identity or machine_identity()
    host = str(environment.get("host") or "")
    user = str(environment.get("user") or "")
    if not host:
        problems.append("missing-host")
    if not user:
        problems.append("missing-user")
    if host and user and host == str(current.get("host") or "") and user == str(current.get("user") or ""):
        problems.append("same-host-and-user")

    package = data.get("package") if isinstance(data.get("package"), dict) else {}
    observed_sha = str(package.get("sha256") or "")
    if expected_package_sha256 and observed_sha != expected_package_sha256:
        problems.append("package-sha256-mismatch")

    doctor = data.get("doctor") if isinstance(data.get("doctor"), dict) else {}
    checks = doctor.get("checks") if isinstance(doctor.get("checks"), list) else []
    install_checks = required_install_checks([item for item in checks if isinstance(item, dict)])
    for name, ok in install_checks.items():
        if not ok:
            problems.append(f"missing-ok-check:{name}")

    return {
        "ok": not problems,
        "problems": problems,
        "environment": environment,
        "packageSha256": observed_sha,
        "installChecks": install_checks,
    }


def cross_machine_evidence_result(
    path: Path | None,
    expected_package_sha256: str = "",
    search_dirs: list[Path] | None = None,
) -> dict[str, Any]:
    auto_discovered = False
    if not path:
        discovered = auto_discovered_evidence_result(
            EVIDENCE_SCHEMA,
            CROSS_MACHINE_EVIDENCE_PATTERNS,
            lambda candidate: cross_machine_evidence_result(
                candidate,
                expected_package_sha256=expected_package_sha256,
                search_dirs=search_dirs,
            ),
            search_dirs,
        )
        if discovered:
            return discovered
    if not path:
        payload = {"ok": False, "problems": ["missing-evidence-path"]}
        if search_dirs:
            payload["searchDirs"] = [str(item) for item in search_dirs]
        return payload
    path = path.expanduser()
    if not path.exists():
        return {"ok": False, "problems": ["evidence-file-not-found"], "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "problems": ["evidence-json-parse-failed"], "path": str(path)}
    if not isinstance(data, dict):
        return {"ok": False, "problems": ["evidence-json-not-object"], "path": str(path)}
    result = validate_cross_machine_evidence(data, expected_package_sha256=expected_package_sha256)
    result["path"] = str(path)
    result["autoDiscovered"] = auto_discovered
    return result


def cross_machine_evidence_ok(
    path: Path | None,
    expected_package_sha256: str = "",
    current_identity: dict[str, str] | None = None,
) -> bool:
    if not path:
        return False
    path = path.expanduser()
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    return bool(
        validate_cross_machine_evidence(
            data,
            expected_package_sha256=expected_package_sha256,
            current_identity=current_identity,
        ).get("ok")
    )


def latest_event_by_name(checks: list[dict[str, Any]], event_name: str) -> dict[str, Any] | None:
    for check in checks:
        if not isinstance(check, dict):
            continue
        evidence = check.get("evidence") if isinstance(check.get("evidence"), dict) else {}
        event = evidence.get("event") if isinstance(evidence.get("event"), dict) else None
        if event and str(event.get("event") or "") == event_name:
            return event
    return None


def read_recent_plugin_events(limit: int = 1000) -> list[dict[str, Any]]:
    candidates: list[Path] = [LAYOUT["projectRoot"] / "events.jsonl"]
    installed_root = Path(
        os.environ.get("CODEX_MN_COMPANION_HOME", str(Path.home() / ".codex/marginnote-assistant"))
    ).expanduser()
    candidates.append(installed_root / "events.jsonl")
    try:
        import companion
        candidates.append(Path(getattr(companion, "EVENTS_PATH", LAYOUT["projectRoot"] / "events.jsonl")))
    except Exception:
        pass
    events_path = None
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.expanduser())
        if key in seen:
            continue
        seen.add(key)
        if candidate.expanduser().exists():
            events_path = candidate.expanduser()
            break
    if events_path is None or not events_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = events_path.read_text(encoding="utf-8").splitlines()[-limit:]
    except Exception:
        return []
    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def latest_plugin_event(events: list[dict[str, Any]], event_name: str) -> dict[str, Any] | None:
    for item in reversed(events):
        if str(item.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(item.get("event") or "") == event_name:
            return item
    return None


def native_highlight_event_scope(event: dict[str, Any] | None) -> dict[str, str]:
    event = event or {}
    return {
        "topicid": str(event.get("topicid") or event.get("notebookid") or ""),
        "bookmd5": str(event.get("bookmd5") or event.get("docmd5") or ""),
    }


def check_native_highlight_blobs_for_event(event: dict[str, Any] | None) -> dict[str, Any]:
    scope = native_highlight_event_scope(event)
    topicid = scope["topicid"]
    bookmd5 = scope["bookmd5"]
    payload: dict[str, Any] = {
        "status": "WARN",
        "topicid": topicid,
        "bookmd5": bookmd5,
        "native_highlight_blobs": 0,
        "db": str(MN_DATABASE),
    }
    if not topicid or not bookmd5:
        payload["detail"] = "latest nativeHighlightSelectionPosted event lacks topicid/bookmd5"
        return payload
    if not MN_DATABASE.exists():
        payload["detail"] = f"database not found: {MN_DATABASE}"
        return payload
    try:
        import sqlite3

        conn = sqlite3.connect(MN_DATABASE)
        try:
            row = conn.execute(
                "select count(*) from ZBOOKNOTE where ZBOOKMD5=? and ZTOPICID=? and ZHIGHLIGHTS is not null",
                (bookmd5, topicid),
            ).fetchone()
        finally:
            conn.close()
    except PermissionError as exc:
        payload["detail"] = f"permission denied: {exc}"
        return payload
    except Exception as exc:
        payload["status"] = "FAIL"
        payload["detail"] = f"query failed: {exc}"
        return payload
    count = int(row[0] if row else 0)
    payload["native_highlight_blobs"] = count
    if count > 0:
        payload["status"] = "OK"
        payload["detail"] = f"{count} rows have ZHIGHLIGHTS for latest native highlight event scope"
    else:
        payload["detail"] = "0 rows have ZHIGHLIGHTS for latest native highlight event scope"
    return payload


def post_native_highlight_request(
    base_url: str,
    topicid: str,
    bookmd5: str,
    selection_text: str = "",
    *,
    post=post_json,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "action": "request_native_highlight_selection",
        "topicid": topicid,
        "notebookid": topicid,
        "bookmd5": bookmd5,
        "docmd5": bookmd5,
        "selectionText": selection_text,
        "source": "release_acceptance.py",
    }
    try:
        return post(base_url, "/marginnote/action", payload)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "payload": payload}


def queued_command_id(result: dict[str, Any]) -> str:
    queued = result.get("queued") if isinstance(result.get("queued"), dict) else {}
    return str(queued.get("id") or "").strip()


def cleanup_queued_command(
    base_url: str,
    topicid: str,
    bookmd5: str,
    command_id: str,
    *,
    post=post_json,
) -> dict[str, Any]:
    command_id = str(command_id or "").strip()
    if not topicid or not command_id:
        return {"ok": True, "skipped": True, "reason": "missing-topicid-or-command-id"}
    payload = {
        "topicid": topicid,
        "notebookid": topicid,
        "bookmd5": bookmd5,
        "docmd5": bookmd5,
        "ids": [command_id],
        "source": "release_acceptance.py",
    }
    try:
        return post(base_url, "/marginnote/ack", payload)
    except Exception as exc:
        return {"ok": False, "error": str(exc), "payload": payload}


def native_highlight_attempt_event_result(event: dict[str, Any] | None) -> dict[str, Any]:
    if not event:
        return {"ok": False, "reason": "missing-event", "event": None}
    event_name = str(event.get("event") or "")
    if event_name == "nativeHighlightSelectionPosted":
        return {"ok": True, "reason": "", "event": event}
    if event_name == "nativeHighlightNextSelectionArmed":
        return {"ok": False, "reason": "armed-next-selection", "event": event}
    if event_name == "nativeHighlightSelectionFailed":
        extra = event.get("extra") if isinstance(event.get("extra"), dict) else {}
        reason = str(extra.get("reason") or event.get("reason") or "native-highlight-failed")
        return {"ok": False, "reason": reason, "event": event}
    return {"ok": False, "reason": f"unexpected-event:{event_name or '(empty)'}", "event": event}


def native_highlight_attempt_reason(data: dict[str, Any]) -> str:
    attempt = data.get("highlightAttempt") if isinstance(data.get("highlightAttempt"), dict) else {}
    if not attempt or not attempt.get("requested"):
        return ""
    reason = str(attempt.get("reason") or "").strip()
    if reason:
        return reason
    wait = attempt.get("wait") if isinstance(attempt.get("wait"), dict) else {}
    reason = str(wait.get("reason") or "").strip()
    if reason:
        return reason
    request_result = attempt.get("request") if isinstance(attempt.get("request"), dict) else {}
    if request_result and not request_result.get("ok"):
        return str(request_result.get("message") or request_result.get("error") or "request-failed").strip()
    return ""


def find_native_highlight_attempt_event(events: list[dict[str, Any]], previous_event_count: int = 0) -> dict[str, Any] | None:
    start = max(0, min(previous_event_count, len(events)))
    for event in reversed(events[start:]):
        if str(event.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(event.get("event") or "") in {
            "nativeHighlightSelectionPosted",
            "nativeHighlightSelectionFailed",
            "nativeHighlightNextSelectionArmed",
        }:
            return event
    return None


def event_marker(event: dict[str, Any] | None) -> tuple[str, str, str, str, str]:
    event = event or {}
    return (
        str(event.get("ts") or ""),
        str(event.get("event") or ""),
        str(event.get("pluginVersion") or ""),
        str(event.get("topicid") or event.get("notebookid") or ""),
        str(event.get("bookmd5") or event.get("docmd5") or ""),
    )


def event_timestamp(event: dict[str, Any] | None) -> float | None:
    value = str((event or {}).get("ts") or "").strip()
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except ValueError:
        return None


def events_after_marker(events: list[dict[str, Any]], previous_latest_event: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not previous_latest_event:
        return events
    marker = event_marker(previous_latest_event)
    for index, event in enumerate(events):
        if event_marker(event) == marker:
            return events[index + 1 :]
    marker_ts = event_timestamp(previous_latest_event)
    if marker_ts is None:
        return events
    return [event for event in events if (event_timestamp(event) or 0) > marker_ts]


def find_native_highlight_attempt_event_after_marker(
    events: list[dict[str, Any]],
    previous_latest_event: dict[str, Any] | None,
) -> dict[str, Any] | None:
    for event in reversed(events_after_marker(events, previous_latest_event)):
        if str(event.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(event.get("event") or "") in {
            "nativeHighlightSelectionPosted",
            "nativeHighlightSelectionFailed",
            "nativeHighlightNextSelectionArmed",
        }:
            return event
    return None


def wait_for_native_highlight_result(
    previous_event_count: int,
    timeout_seconds: float,
    interval_seconds: float,
    previous_latest_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    deadline = time.time() + max(timeout_seconds, 0)
    last_seen = previous_event_count
    armed_result: dict[str, Any] | None = None
    while True:
        events = read_recent_plugin_events()
        last_seen = len(events)
        event = (
            find_native_highlight_attempt_event_after_marker(events, previous_latest_event)
            if previous_latest_event
            else find_native_highlight_attempt_event(events, previous_event_count)
        )
        if event:
            result = native_highlight_attempt_event_result(event)
            result["eventsSeen"] = len(events)
            if str(event.get("event") or "") != "nativeHighlightNextSelectionArmed":
                return result
            armed_result = result
        if time.time() >= deadline:
            if armed_result:
                return armed_result
            return {
                "ok": False,
                "reason": "timeout",
                "event": None,
                "eventsSeen": last_seen,
            }
        time.sleep(max(interval_seconds, 0.05))


def collect_native_highlight_evidence(
    *,
    try_native_highlight: bool = False,
    base_url: str = DEFAULT_COMPANION_URL,
    topicid: str = "",
    bookmd5: str = "",
    selection_text: str = "",
    timeout_seconds: float = 20,
    interval_seconds: float = 1,
    post=post_json,
) -> dict[str, Any]:
    highlight_attempt: dict[str, Any] = {"requested": False}
    if try_native_highlight:
        topicid = topicid or read_default("mindbooks_lasttopicid")
        bookmd5 = bookmd5 or read_default("mindbooks_lastbookmd5")
        events_before = read_recent_plugin_events()
        request_result = post_native_highlight_request(
            base_url,
            topicid,
            bookmd5,
            selection_text,
            post=post,
        )
        wait_result = (
            wait_for_native_highlight_result(
                previous_event_count=len(events_before),
                timeout_seconds=timeout_seconds,
                interval_seconds=interval_seconds,
                previous_latest_event=events_before[-1] if events_before else None,
            )
            if request_result.get("ok")
            else {"ok": False, "reason": "request-failed", "event": None}
        )
        cleanup_result: dict[str, Any] = {"ok": True, "skipped": True, "reason": "native-highlight-attempt-finished"}
        if str(wait_result.get("reason") or "") == "timeout":
            cleanup_result = cleanup_queued_command(
                base_url,
                topicid,
                bookmd5,
                queued_command_id(request_result),
                post=post,
            )
        highlight_attempt = {
            "requested": True,
            "topicid": topicid,
            "bookmd5": bookmd5,
            "request": request_result,
            "wait": wait_result,
            "cleanup": cleanup_result,
            "event": wait_result.get("event"),
            "ok": bool(wait_result.get("ok")),
            "reason": str(wait_result.get("reason") or ""),
        }
    checks, doctor_run = run_doctor_json()
    events = read_recent_plugin_events()
    latest_posted = latest_plugin_event(events, "nativeHighlightSelectionPosted")
    latest_failed = latest_plugin_event(events, "nativeHighlightSelectionFailed")
    latest_armed = latest_plugin_event(events, "nativeHighlightNextSelectionArmed")
    highlight_check = check_by_name(checks, "Native highlight blobs")
    highlight_blob_check = check_native_highlight_blobs_for_event(latest_posted)
    evidence = {
        "schema": NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
        "generatedAt": datetime.now().astimezone().isoformat(timespec="seconds"),
        "environment": machine_identity(),
        "pluginVersion": CURRENT_PLUGIN_VERSION,
        "highlightScope": native_highlight_event_scope(latest_posted),
        "events": {
            "latestPosted": latest_posted,
            "latestFailed": latest_failed,
            "latestArmed": latest_armed,
        },
        "highlightBlobCheck": highlight_blob_check,
        "doctor": {
            "checks": checks,
            "run": doctor_run,
        },
        "doctorHighlightCheck": highlight_check,
        "highlightAttempt": highlight_attempt,
    }
    validation = validate_native_highlight_evidence(evidence)
    evidence["ok"] = bool(validation.get("ok"))
    evidence["problems"] = validation.get("problems", [])
    return evidence


def validate_native_highlight_evidence(data: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    if data.get("schema") != NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA:
        problems.append("schema-mismatch")
    attempt_reason = native_highlight_attempt_reason(data)
    if attempt_reason:
        if attempt_reason == "timeout":
            problems.append("native-highlight-attempt-timeout")
        elif attempt_reason == "armed-next-selection":
            problems.append("native-highlight-attempt-armed-next-selection")
        else:
            problems.append(f"native-highlight-attempt-failed:{attempt_reason}")
    events = data.get("events") if isinstance(data.get("events"), dict) else {}
    latest_posted = events.get("latestPosted") if isinstance(events.get("latestPosted"), dict) else None
    if not latest_posted or str(latest_posted.get("event") or "") != "nativeHighlightSelectionPosted":
        problems.append("missing-nativeHighlightSelectionPosted")
    elif str(latest_posted.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
        problems.append("plugin-version-mismatch")
    event_scope = native_highlight_event_scope(latest_posted)
    if latest_posted and (not event_scope["topicid"] or not event_scope["bookmd5"]):
        problems.append("missing-native-highlight-scope")

    doctor = data.get("doctor") if isinstance(data.get("doctor"), dict) else {}
    checks = doctor.get("checks") if isinstance(doctor.get("checks"), list) else []
    highlight_check = check_by_name([item for item in checks if isinstance(item, dict)], "Native highlight blobs")
    if not highlight_check and isinstance(data.get("doctorHighlightCheck"), dict):
        highlight_check = data["doctorHighlightCheck"]
    blob_check = data.get("highlightBlobCheck") if isinstance(data.get("highlightBlobCheck"), dict) else None
    if blob_check:
        blob_status = str(blob_check.get("status") or "")
        blob_scope = {
            "topicid": str(blob_check.get("topicid") or ""),
            "bookmd5": str(blob_check.get("bookmd5") or ""),
        }
        if blob_status != "OK" or int(blob_check.get("native_highlight_blobs") or 0) <= 0:
            problems.append("native-highlight-blobs-not-ok")
        if event_scope["topicid"] and event_scope["bookmd5"] and blob_scope != event_scope:
            problems.append("native-highlight-scope-mismatch")
    elif not highlight_check:
        problems.append("missing-native-highlight-blob-check")
    elif str(highlight_check.get("status") or "") != "OK":
        problems.append("native-highlight-blobs-not-ok")

    return {
        "ok": not problems,
        "problems": problems,
        "event": latest_posted,
        "highlightScope": event_scope,
        "highlightBlobCheck": blob_check,
        "doctorHighlightCheck": highlight_check,
        "highlightAttemptReason": attempt_reason,
    }


def native_highlight_evidence_result(path: Path | None, search_dirs: list[Path] | None = None) -> dict[str, Any]:
    auto_discovered = False
    if not path:
        discovered = auto_discovered_evidence_result(
            NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
            NATIVE_HIGHLIGHT_EVIDENCE_PATTERNS,
            lambda candidate: native_highlight_evidence_result(candidate, search_dirs=search_dirs),
            search_dirs,
        )
        if discovered:
            return discovered
    if not path:
        payload = {"ok": False, "problems": ["missing-evidence-path"]}
        if search_dirs:
            payload["searchDirs"] = [str(item) for item in search_dirs]
        return payload
    path = path.expanduser()
    if not path.exists():
        return {"ok": False, "problems": ["evidence-file-not-found"], "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "problems": ["evidence-json-parse-failed"], "path": str(path)}
    if not isinstance(data, dict):
        return {"ok": False, "problems": ["evidence-json-not-object"], "path": str(path)}
    result = validate_native_highlight_evidence(data)
    result["path"] = str(path)
    result["autoDiscovered"] = auto_discovered
    return result


def mn_runtime_evidence_result(path: Path | None, search_dirs: list[Path] | None = None) -> dict[str, Any]:
    auto_discovered = False
    if not path:
        discovered = auto_discovered_evidence_result(
            MN_RUNTIME_EVIDENCE_SCHEMA,
            MN_RUNTIME_EVIDENCE_PATTERNS,
            lambda candidate: mn_runtime_evidence_result(candidate, search_dirs=search_dirs),
            search_dirs,
        )
        if discovered:
            return discovered
    if not path:
        payload = {"ok": False, "problems": ["missing-evidence-path"]}
        if search_dirs:
            payload["searchDirs"] = [str(item) for item in search_dirs]
        return payload
    path = path.expanduser()
    if not path.exists():
        return {"ok": False, "problems": ["evidence-file-not-found"], "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "problems": ["evidence-json-parse-failed"], "path": str(path)}
    if not isinstance(data, dict):
        return {"ok": False, "problems": ["evidence-json-not-object"], "path": str(path)}
    result = validate_mn_runtime_evidence(data)
    result["path"] = str(path)
    result["autoDiscovered"] = auto_discovered
    return result


def validate_single_document_acceptance_evidence(data: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    if data.get("schema") != SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA:
        problems.append("schema-mismatch")
    if str(data.get("pluginVersion") or "") not in {"", CURRENT_PLUGIN_VERSION}:
        problems.append("plugin-version-mismatch")
    if not str(data.get("topicid") or ""):
        problems.append("missing-topicid")
    if not str(data.get("bookmd5") or ""):
        problems.append("missing-bookmd5")
    if data.get("ok") is not True:
        problems.append("single-document-not-ok")
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    if str(summary.get("singleDocumentAcceptance") or "") != "PASS":
        problems.append("summary-not-pass")
    if int(summary.get("blocked") or 0) != 0:
        problems.append("summary-has-blocked")
    checks = data.get("checks") if isinstance(data.get("checks"), list) else []
    if not checks:
        problems.append("missing-checks")
    blocked_checks = [
        str(item.get("id") or item.get("label") or "unknown")
        for item in checks
        if isinstance(item, dict) and str(item.get("status") or "") != "PASS"
    ]
    for check_id in blocked_checks:
        problems.append(f"check-blocked:{check_id}")
    problems = list(dict.fromkeys(problems))
    return {
        "ok": not problems,
        "problems": problems,
        "topicid": str(data.get("topicid") or ""),
        "bookmd5": str(data.get("bookmd5") or ""),
        "blockedChecks": blocked_checks,
        "summary": summary,
    }


def single_document_acceptance_result(path: Path | None, search_dirs: list[Path] | None = None) -> dict[str, Any]:
    auto_discovered = False
    if not path:
        discovered = auto_discovered_evidence_result(
            SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
            SINGLE_DOCUMENT_ACCEPTANCE_PATTERNS,
            lambda candidate: single_document_acceptance_result(candidate, search_dirs=search_dirs),
            search_dirs,
        )
        if discovered:
            return discovered
    if not path:
        payload = {"ok": False, "problems": ["missing-evidence-path"]}
        if search_dirs:
            payload["searchDirs"] = [str(item) for item in search_dirs]
        return payload
    path = path.expanduser()
    if not path.exists():
        return {"ok": False, "problems": ["evidence-file-not-found"], "path": str(path)}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"ok": False, "problems": ["evidence-json-parse-failed"], "path": str(path)}
    if not isinstance(data, dict):
        return {"ok": False, "problems": ["evidence-json-not-object"], "path": str(path)}
    result = validate_single_document_acceptance_evidence(data)
    result["path"] = str(path)
    result["autoDiscovered"] = auto_discovered
    return result


def print_text(report: dict[str, Any]) -> None:
    print("Release acceptance:", "PASS" if report.get("releasable") else "BLOCKED")
    for gate in report.get("gates", []):
        print(f"[{gate['status']:<5}] {gate['name']}: {gate['detail']}")
        next_actions = gate.get("nextActions") if isinstance(gate.get("nextActions"), list) else []
        if gate.get("status") == "BLOCK" and next_actions:
            print("  Next actions:")
            for action in next_actions:
                print(f"  - {action}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final release acceptance gates for Codex Companion.")
    parser.add_argument("package", nargs="?", default=str(DEFAULT_PACKAGE), help="Release zip to inspect.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--skip-tests", action="store_true", help="Do not run unit tests; mark the unit-test gate blocked.")
    parser.add_argument("--skip-syntax", action="store_true", help="Do not run syntax checks; mark the syntax gate blocked.")
    parser.add_argument("--cross-machine-evidence", help="JSON/text evidence file from a different macOS user or machine.")
    parser.add_argument("--mn-runtime-evidence", help="JSON evidence from Refresh MN Runtime.command proving current MN4 runtime readiness.")
    parser.add_argument("--native-highlight-evidence", help="JSON evidence proving a visible native MN4 highlight.")
    parser.add_argument("--single-document-evidence", help="JSON evidence from single_document_acceptance.py proving all core workflows passed in one MN document.")
    parser.add_argument("--url", default=DEFAULT_COMPANION_URL, help="Companion base URL for active evidence collection.")
    parser.add_argument("--topicid", default="", help="MarginNote notebook/topic id for active native highlight collection.")
    parser.add_argument("--bookmd5", default="", help="MarginNote document md5 for active native highlight collection.")
    parser.add_argument("--selection-text", default="", help="Optional selected text hint for active native highlight collection.")
    parser.add_argument(
        "--try-native-highlight",
        action="store_true",
        help="When collecting native highlight evidence, first ask the MN4 plugin to highlight the current PDF selection; if it arms the next selection, keep waiting for a posted/failed event.",
    )
    parser.add_argument(
        "--native-highlight-timeout",
        type=float,
        default=90,
        help="Seconds to wait for nativeHighlightSelectionPosted/nativeHighlightSelectionFailed after --try-native-highlight; an armed-next-selection event keeps waiting until this timeout.",
    )
    parser.add_argument(
        "--native-highlight-interval",
        type=float,
        default=1,
        help="Polling interval while waiting for native highlight attempt evidence.",
    )
    parser.add_argument(
        "--collect-cross-machine-evidence",
        metavar="OUTPUT",
        help="Write install evidence JSON on a different macOS user or machine after installing this package.",
    )
    parser.add_argument(
        "--collect-native-highlight-evidence",
        metavar="OUTPUT",
        help="Write native highlight evidence JSON after triggering 高亮选区; the command can wait for a reselected MN4 PDF text span.",
    )
    args = parser.parse_args()

    if args.collect_cross_machine_evidence:
        evidence = collect_cross_machine_evidence(Path(args.package))
        output = Path(args.collect_cross_machine_evidence).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.json:
            print(json.dumps(evidence, ensure_ascii=False, indent=2))
        else:
            print(f"Wrote cross-machine evidence: {output}")
            print("Evidence:", "OK" if evidence.get("ok") else "INCOMPLETE")
        return 0 if evidence.get("ok") else 1

    if args.collect_native_highlight_evidence:
        evidence = collect_native_highlight_evidence(
            try_native_highlight=args.try_native_highlight,
            base_url=args.url,
            topicid=args.topicid,
            bookmd5=args.bookmd5,
            selection_text=args.selection_text,
            timeout_seconds=args.native_highlight_timeout,
            interval_seconds=args.native_highlight_interval,
        )
        output = Path(args.collect_native_highlight_evidence).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2), encoding="utf-8")
        if args.json:
            print(json.dumps(evidence, ensure_ascii=False, indent=2))
        else:
            print(f"Wrote native highlight evidence: {output}")
            print("Evidence:", "OK" if evidence.get("ok") else "INCOMPLETE")
            if evidence.get("problems"):
                print("Problems:", ", ".join(str(item) for item in evidence.get("problems", [])))
        return 0 if evidence.get("ok") else 1

    package_path = Path(args.package)
    tests = {"ok": False, "skipped": True} if args.skip_tests else run_unit_tests(package_path)
    syntax = {"ok": False, "skipped": True} if args.skip_syntax else run_syntax_checks()
    smoke = run_smoke(package_path)
    doctor_checks, doctor_run = run_doctor_json()
    evidence_search_dirs = default_evidence_search_dirs(package_path)
    cross_machine = cross_machine_evidence_result(
        Path(args.cross_machine_evidence) if args.cross_machine_evidence else None,
        expected_package_sha256=str(smoke.get("sha256") or ""),
        search_dirs=evidence_search_dirs,
    )
    native_highlight = native_highlight_evidence_result(
        Path(args.native_highlight_evidence) if args.native_highlight_evidence else None,
        search_dirs=evidence_search_dirs,
    )
    mn_runtime = mn_runtime_evidence_result(
        Path(args.mn_runtime_evidence) if args.mn_runtime_evidence else None,
        search_dirs=evidence_search_dirs,
    )
    single_document = single_document_acceptance_result(
        Path(args.single_document_evidence) if args.single_document_evidence else None,
        search_dirs=evidence_search_dirs,
    )
    report = evaluate_acceptance(
        unit_tests_ok=bool(tests.get("ok")),
        syntax_ok=bool(syntax.get("ok")),
        smoke=smoke,
        doctor_checks=doctor_checks,
        cross_machine_verified=bool(cross_machine.get("ok")),
        native_highlight_evidence=native_highlight,
        mn_runtime_evidence=mn_runtime,
        single_document_acceptance=single_document,
    )
    report["evidence"] = {
        "unitTests": tests,
        "syntax": syntax,
        "smoke": smoke,
        "doctor": doctor_run,
        "crossMachine": cross_machine,
        "mnRuntime": mn_runtime,
        "nativeHighlight": native_highlight,
        "singleDocument": single_document,
    }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print_text(report)
    return 0 if report.get("releasable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
