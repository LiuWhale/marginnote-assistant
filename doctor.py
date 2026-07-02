#!/usr/bin/python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib import request


HOME = Path.home()
ROOT = Path(os.environ.get("CODEX_MN_COMPANION_HOME", HOME / ".codex/marginnote-assistant")).expanduser()
EXT_DIR = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
DB_PATH = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/Private Documents/MN4NotebookDatabase/0/MarginNotes.sqlite"
ONEDRIVE_DIR = HOME / "Library/CloudStorage/OneDrive-个人/Codex Companion"
MN4_APP = Path("/Applications/MarginNote 4.app")
EVENTS_PATH = ROOT / "events.jsonl"
CURRENT_PLUGIN_VERSION = "0.4.41"
REQUIRED_NATIVE_HANDLER_FEATURES = [
    "native-highlight-arm-next-selection-default",
    "native-highlight-prefer-next-selection-v1",
    "native-highlight-command-prepared",
    "selection-popup-diagnostics-v1",
    "native-highlight-selection-poll-v1",
    "native-highlight-selection-poll-probe-v1",
    "selection-popup-scene-observer-v1",
    "selection-popup-notebook-rebind-v1",
    "native-highlight-selection-text-resolver-v1",
    "native-pdf-selection-probe-v1",
    "native-pdf-selection-image-probe-v1",
    "context-refresh-clears-stale-selection-v1",
    "ai-edit-transaction-rollback-v1",
    "ai-edit-undo-rollback-v2",
    "native-mn-object-registry-scan-v1",
    "native-mn-object-existence-probe-v1",
    "native-mindmap-diff-apply-create-v1",
    "native-mindmap-delete-suggestion-confirm-v1",
]
CURRENT_RC_VERSION = "0.4.41"
PREFERRED_LAUNCH_LABEL = "com.codex.paper-companion"
LEGACY_LAUNCH_LABEL = "com.liuwhale.codex-marginnote-assistant"
LATEST_PACKAGE = ROOT / f"release/CodexCompanion-{CURRENT_RC_VERSION}-latest-dist.zip"
ONEDRIVE_LATEST_PACKAGE = ONEDRIVE_DIR / f"CodexCompanion-{CURRENT_RC_VERSION}-latest-dist.zip"
LATEST_PKG = ROOT / f"release/CodexCompanion-{CURRENT_RC_VERSION}-latest.pkg"
ONEDRIVE_LATEST_PKG = ONEDRIVE_DIR / f"CodexCompanion-{CURRENT_RC_VERSION}-latest.pkg"
RELEASE_SHA256SUMS = ROOT / "release/SHA256SUMS.txt"
ONEDRIVE_RELEASE_SHA256SUMS = ONEDRIVE_DIR / "SHA256SUMS.txt"
PDF_EXPORT_DIR = ONEDRIVE_DIR / "exports"
NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID = "AAFA4811-8B3A-46AF-8511-6037060FA23B"
NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5 = "253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246"
COMPANION_URL = "http://127.0.0.1:48761"
REQUIRED_WEB_CONTROL_IDS = [
    "aiChatShell",
    "knowledgeOsContractPanel",
    "knowledgeOsContractTitle",
    "knowledgeOsObjectLayer",
    "knowledgeOsOperationLayer",
    "knowledgeOsEvidenceLayer",
    "modeSwitchBar",
    "chatModeButton",
    "agentWorkspaceModeButton",
    "modeIntentLine",
    "workspaceNavigator",
    "workspaceNavigatorSummary",
    "workspaceNavConsoleButton",
    "workspaceNavMindmapStudioButton",
    "workspaceNavCardFactoryButton",
    "workspaceNavLedgerExplorerButton",
    "workspaceNavKnowledgeGraphButton",
    "workspaceNavWorkflowBuilderButton",
    "workspaceNavSkillCenterButton",
    "knowledgeConsolePanel",
    "notebookWorkspacePanel",
    "notebookWorkspaceTitle",
    "notebookWorkspaceSummary",
    "notebookWorkspaceRefreshButton",
    "notebookWorkspaceFocus",
    "notebookWorkspaceObjectCount",
    "notebookWorkspaceMindmap",
    "notebookWorkspaceReview",
    "notebookWorkspaceWorkflow",
    "notebookWorkspaceLedger",
    "notebookWorkspaceSources",
    "notebookWorkspaceActions",
    "notebookObjectIntake",
    "notebookObjectIntakeSummary",
    "notebookObjectIntakeRoutes",
    "notebookObjectTaskComposer",
    "notebookObjectTaskComposerSummary",
    "notebookObjectTaskComposerList",
    "sourceRegistryPanel",
    "notebookWorkspaceSourceRegistry",
    "notebookWorkspaceSourceSummary",
    "notebookWorkspaceSourceList",
    "notebookWorkspaceSourceActionStatus",
    "notebookWorkspaceSourceActions",
    "notebookWorkspaceStudyProgram",
    "notebookWorkspaceStudyCoverage",
    "notebookWorkspaceStudyGaps",
    "notebookWorkspaceStudyRecommendations",
    "notebookWorkspaceRunbook",
    "notebookWorkspaceRunbookSummary",
    "notebookWorkspaceRunbookAutoButton",
    "notebookWorkspaceRunbookAutoStatus",
    "notebookWorkspaceRunbookContinueButton",
    "notebookWorkspaceRunbookList",
    "commandPanePanel",
    "commandPaneHeader",
    "commandPaneStatus",
    "commandPaneToggleButton",
    "commandPaneBody",
    "commandPaneComposer",
    "workbenchTabs",
    "workbenchTabObject",
    "workbenchTabOperation",
    "workbenchTabKnowledge",
    "workbenchTabWorkflow",
    "studioCanvasPanel",
    "workbenchLayout",
    "objectWorkspacePanel",
    "operationWorkspacePanel",
    "knowledgeWorkspacePanel",
    "workflowWorkspacePanel",
    "objectWorkspaceTitle",
    "objectWorkspaceMeta",
    "objectWorkspaceScope",
    "objectGraphPanel",
    "objectGraphRefreshButton",
    "objectGraphRelationAddButton",
    "objectGraphSummary",
    "objectGraphNodes",
    "objectGraphRelationEditor",
    "objectGraphRelationTargetInput",
    "objectGraphRelationTypeInput",
    "objectGraphRelationLabelInput",
    "objectGraphRelationNoteInput",
    "objectGraphRelationSaveButton",
    "objectGraphRelationCancelButton",
    "objectActivityPanel",
    "objectActivityRefreshButton",
    "objectActivitySummary",
    "objectActivityList",
    "operationLedgerDrawer",
    "operationLedgerPanel",
    "operationLedgerRefreshButton",
    "operationLedgerSummary",
    "operationLedgerList",
    "operationLedgerDetailPanel",
    "operationLedgerDetailTitle",
    "operationLedgerDetailMeta",
    "operationLedgerDetailEvidence",
    "operationLedgerDetailCloseButton",
    "operationWorkspaceTitle",
    "operationWorkspaceMeta",
    "verificationReportPanel",
    "realMnAcceptancePanel",
    "realMnAcceptanceStatusLine",
    "realMnAcceptanceChecklist",
    "realMnAcceptanceRunAllButton",
    "singleDocumentAcceptanceLine",
    "singleDocumentAcceptanceDetail",
    "singleDocumentAcceptanceButton",
    "mainUiFunctionalAcceptanceLine",
    "mainUiFunctionalAcceptanceDetail",
    "mainUiFunctionalAcceptanceButton",
    "realMnAcceptanceSafeEvidenceButton",
    "mainNativeHighlightWizardPanel",
    "mainNativeHighlightWizardLine",
    "mainNativeHighlightWizardDetail",
    "mainNativeHighlightWizardActions",
    "nativeHighlightWizardRetryButton",
    "nativeHighlightWizardRefreshButton",
    "operationCompilerPanel",
    "operationCompilerSummary",
    "operationPlanStats",
    "operationCompilerChecks",
    "operationDryRunDetails",
    "operationCompilerRepairActions",
    "operationWorkspaceNextActions",
    "mindmapStudioPanel",
    "mindmapStudioSummary",
    "mindmapStudioCurrentTree",
    "mindmapStudioDiffStage",
    "mindmapStudioApplyStage",
    "mindmapStudioTransactionStage",
    "mindmapStudioReadTreeButton",
    "mindmapStudioPreviewDiffButton",
    "mindmapStudioApplySelectedButton",
    "mindmapStudioVerifyButton",
    "mindmapStudioRollbackButton",
    "mindmapStudioStatusLine",
    "knowledgeWorkspaceTitle",
    "knowledgeWorkspaceSummary",
    "knowledgeWorkspaceScope",
    "knowledgeWorkspaceEntities",
    "knowledgeWorkspaceRelations",
    "knowledgeWorkspaceSearchInput",
    "knowledgeWorkspaceSearchButton",
    "knowledgeWorkspaceResults",
    "knowledgeWorkspaceActions",
    "workflowWorkspaceTitle",
    "workflowWorkspaceSummary",
    "workflowWorkspaceRuns",
    "workflowBuilderBoardPanel",
    "workflowBuilderBoardSummary",
    "workflowBuilderBoardLanes",
    "externalGatewayPanel",
    "workflowWorkspaceGateway",
    "skillCenterPanel",
    "workflowWorkspaceSkills",
    "workflowWorkspaceSkillsList",
    "workflowWorkspaceTemplates",
    "workflowWorkspaceRecentRuns",
    "workflowWorkspaceActions",
    "mindmapTreeCacheStatus",
    "mindmapTreeCacheText",
    "mindmapTreeRefreshButton",
    "mindmapTreePreviewList",
    "mindmapDiffWorkbench",
    "mindmapDiffWorkbenchTitle",
    "mindmapDiffWorkbenchSummary",
    "mindmapDiffWorkbenchPreview",
    "operationWorkspaceVerification",
    "agentWorkbenchBar",
    "agentWorkbenchLight",
    "agentWorkbenchLine",
    "agentWorkbenchDetail",
    "agentPlanRefreshButton",
    "mindmapDiffApplyStatus",
    "mindmapDiffApplyLight",
    "mindmapDiffApplyText",
    "aiEditTransactionCenter",
    "aiEditTransactionTitle",
    "aiEditTransactionSummary",
    "aiEditTransactionNotes",
    "aiEditTransactionResidualProof",
    "promptInput",
    "sendButton",
    "stopButton",
    "contextButton",
    "contextScopeAutoButton",
    "contextScopeSelectionButton",
    "contextScopeDocumentButton",
    "closeButton",
    "liveHistory",
    "contextSourceLine",
    "aiReadinessLine",
    "aiReadinessDetail",
    "selectionPreview",
    "statusPill",
    "pdfCacheBanner",
    "pdfCacheBannerLight",
    "pdfCacheBannerText",
    "pdfCacheFileBannerButton",
    "pdfCacheFileInput",
    "pdfCacheFileButton",
    "mindmapTargetBar",
    "mindmapTargetLight",
    "mindmapTargetSelect",
    "mindmapTargetRefreshButton",
    "contextLine",
    "readinessPanel",
    "mnApiStatusLine",
    "mnApiBackendSelect",
    "mnUrlApiSecretInput",
    "clearMnUrlApiSecretButton",
    "conversationHistoryPage",
    "conversationHistoryList",
    "conversationHistoryCloseButton",
    "fileSearchRootsInput",
    "fileSearchRootsStatusLine",
    "logsStatusLine",
    "logsList",
]


@dataclass
class Check:
    name: str
    status: str
    detail: str
    evidence: dict[str, Any] | None = None


def shell(args: list[str], timeout: float = 8) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True, timeout=timeout)


def http_json(path: str, timeout: float = 5) -> dict[str, Any] | None:
    try:
        with request.urlopen(COMPANION_URL + path, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def http_action_json(payload: dict[str, Any], timeout: float = 8) -> dict[str, Any] | None:
    try:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = request.Request(
            COMPANION_URL + "/marginnote/action",
            data=data,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_sha256_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            entries[parts[-1]] = parts[0]
    return entries


def parse_developer_id_installer_identities(output: str) -> list[str]:
    identities: list[str] = []
    for line in output.splitlines():
        if "Developer ID Installer:" not in line:
            continue
        parts = line.split('"')
        if len(parts) >= 3:
            identity = parts[1].strip()
        else:
            identity = line.strip()
        if identity.startswith("Developer ID Installer:") and identity not in identities:
            identities.append(identity)
    return identities


def notary_credentials_mode(env: dict[str, str] | None = None) -> str:
    env = env if env is not None else os.environ
    profile = (
        env.get("NOTARYTOOL_KEYCHAIN_PROFILE", "")
        or env.get("CODEX_MN_NOTARYTOOL_KEYCHAIN_PROFILE", "")
    ).strip()
    if profile:
        return "keychain-profile"
    if (
        env.get("APPLE_ID", "").strip()
        and env.get("APPLE_TEAM_ID", "").strip()
        and env.get("APPLE_APP_SPECIFIC_PASSWORD", "").strip()
    ):
        return "apple-id"
    return ""


def query_one(sql: str, params: tuple[Any, ...] = ()) -> Any:
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(sql, params).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def check_mn4_app() -> Check:
    if MN4_APP.exists():
        return Check("MarginNote 4 app", "OK", str(MN4_APP))
    return Check("MarginNote 4 app", "FAIL", f"not found: {MN4_APP}")


def check_extension() -> Check:
    required = ["main.js", "CodexPanelController.js", "mnaddon.json", "codex.png"]
    missing = [item for item in required if not (EXT_DIR / item).exists()]
    if missing:
        return Check("MN4 extension files", "FAIL", "missing " + ", ".join(missing), {"path": str(EXT_DIR)})
    try:
        manifest = json.loads((EXT_DIR / "mnaddon.json").read_text(encoding="utf-8"))
    except Exception as exc:
        return Check("MN4 extension manifest", "FAIL", f"cannot read manifest: {exc}")
    title = str(manifest.get("title") or "")
    version = str(manifest.get("version") or "")
    status = "OK" if title == "Codex Companion" and version == CURRENT_PLUGIN_VERSION else "WARN"
    return Check(
        "MN4 extension manifest",
        status,
        f"{title or '(missing title)'} / {version or '(missing version)'}",
        {"path": str(EXT_DIR), "manifest": manifest},
    )


def check_companion() -> Check:
    health = http_json("/health", timeout=2)
    if not health or not health.get("ok"):
        return Check("Companion service", "FAIL", f"not responding at {COMPANION_URL}")
    status = http_json("/status", timeout=3)
    if not status or not status.get("ok"):
        return Check(
            "Companion service",
            "OK",
            "health=ok, status=unavailable",
            {"health": health, "status": status},
        )
    detail = (
        f"pid={status.get('pid')}, model={status.get('model')}, "
        f"backend={status.get('ai_backend')}, "
        f"codex_cli={bool(status.get('codex_cli_available'))}, "
        f"openai_configured={bool(status.get('openai_configured'))}, "
        f"proxy={status.get('proxy_scheme') if status.get('proxy_configured') else 'none'}"
    )
    return Check("Companion service", "OK", detail, status)


def check_launch_agent() -> Check:
    labels = [PREFERRED_LAUNCH_LABEL, LEGACY_LAUNCH_LABEL]
    found: list[str] = []
    for label in labels:
        path = HOME / f"Library/LaunchAgents/{label}.plist"
        if path.exists():
            found.append(str(path))
    if not found:
        return Check("LaunchAgent", "WARN", "no LaunchAgent plist found")
    loaded = []
    domain = f"gui/{os.getuid()}"
    for label in labels:
        proc = shell(["launchctl", "print", f"{domain}/{label}"], timeout=4)
        if proc.returncode == 0:
            loaded.append(label)
    if PREFERRED_LAUNCH_LABEL in loaded and LEGACY_LAUNCH_LABEL not in loaded:
        status = "OK"
        detail = "loaded: " + PREFERRED_LAUNCH_LABEL
    elif PREFERRED_LAUNCH_LABEL in loaded and LEGACY_LAUNCH_LABEL in loaded:
        status = "WARN"
        detail = "preferred label is loaded, but legacy label is also loaded"
    elif loaded:
        status = "WARN"
        detail = "preferred label is not loaded; loaded legacy label: " + ", ".join(loaded)
    else:
        status = "WARN"
        detail = "plist exists but service is not loaded"
    return Check("LaunchAgent", status, detail, {"plists": found, "loaded": loaded})


def check_release_package() -> Check:
    local = LATEST_PACKAGE.exists()
    cloud = ONEDRIVE_LATEST_PACKAGE.exists()
    evidence: dict[str, Any] = {"local": str(LATEST_PACKAGE), "onedrive": str(ONEDRIVE_LATEST_PACKAGE)}
    if not local or not cloud:
        return Check(
            "Latest RC package",
            "WARN",
            f"local={local}, onedrive={cloud}",
            evidence,
        )

    try:
        local_bytes = LATEST_PACKAGE.read_bytes()
        cloud_bytes = ONEDRIVE_LATEST_PACKAGE.read_bytes()
    except PermissionError as exc:
        denied_path = str(getattr(exc, "filename", "") or "")
        if not denied_path:
            message = str(exc)
            if str(ONEDRIVE_LATEST_PACKAGE) in message:
                denied_path = str(ONEDRIVE_LATEST_PACKAGE)
            elif str(LATEST_PACKAGE) in message:
                denied_path = str(LATEST_PACKAGE)
        evidence.update(
            {
                "permissionIssue": True,
                "permissionPath": denied_path or str(ONEDRIVE_LATEST_PACKAGE),
                "permissionError": str(exc),
            }
        )
        return Check(
            "Latest RC package",
            "WARN",
            "permission_denied: grant Full Disk Access to the Companion service/Python and retry",
            evidence,
        )

    local_hash = sha256_bytes(local_bytes)
    cloud_hash = sha256_bytes(cloud_bytes)
    hashes_match = local_hash == cloud_hash
    evidence.update({"localSha256": local_hash, "onedriveSha256": cloud_hash, "hashesMatch": hashes_match})

    required_root_files = [
        "README-FIRST.txt",
        "install.sh",
        "uninstall.sh",
        "Install Codex Companion.command",
        "Uninstall Codex Companion.command",
        "Collect Native Highlight Evidence.command",
        "Collect Single Document Acceptance.command",
        "Collect Cross-Machine Evidence.command",
        "Build Signed Package.command",
        "Notarize Package.command",
        "Prepare Release Handoff.command",
        "release_smoke_test.py",
        "single_document_acceptance.py",
        "ui_functional_acceptance.py",
        "build_pkg.py",
        "notarize_pkg.py",
        "prepare_release_handoff.py",
    ]
    required_payload_files = ["companion/companion.py", "extension/codex.mn.assistant/main.js"]
    private_names = {"companion/.env", "companion/companion_settings.json", "companion/events.jsonl", "companion/goal.json"}
    private_parts = ("companion/uploads/", "companion/queue/", "companion/drafts/", "companion/release/", "companion/logs/")
    try:
        with zipfile.ZipFile(LATEST_PACKAGE) as archive:
            names = archive.namelist()
    except Exception as exc:
        evidence["zipError"] = str(exc)
        return Check("Latest RC package", "WARN", f"cannot inspect zip: {exc}", evidence)

    suffixes = [name.split("/", 1)[1] for name in names if "/" in name]
    missing_root = [name for name in required_root_files if name not in suffixes]
    missing_payload = [name for name in required_payload_files if name not in suffixes]
    bad_entries = [
        name
        for name in suffixes
        if name in private_names or any(part in name for part in private_parts)
    ]
    evidence.update(
        {
            "missingRootFiles": missing_root,
            "missingPayloadFiles": missing_payload,
            "badEntries": bad_entries,
            "fileCount": len(names),
        }
    )

    problems: list[str] = []
    if not hashes_match:
        problems.append("hash_mismatch")
    if missing_root:
        problems.append("missing_root=" + ",".join(missing_root))
    if missing_payload:
        problems.append("missing_payload=" + ",".join(missing_payload))
    if bad_entries:
        problems.append(f"private_entries={len(bad_entries)}")
    if not problems:
        return Check(
            "Latest RC package",
            "OK",
            "installable clean zip; local and OneDrive hashes match",
            evidence,
        )
    return Check(
        "Latest RC package",
        "WARN",
        "; ".join(problems),
        evidence,
    )


def check_release_pkg() -> Check:
    local = LATEST_PKG.exists()
    cloud = ONEDRIVE_LATEST_PKG.exists()
    evidence: dict[str, Any] = {"local": str(LATEST_PKG), "onedrive": str(ONEDRIVE_LATEST_PKG)}
    if not local or not cloud:
        return Check("Latest RC pkg", "WARN", f"local={local}, onedrive={cloud}", evidence)

    try:
        local_bytes = LATEST_PKG.read_bytes()
        cloud_bytes = ONEDRIVE_LATEST_PKG.read_bytes()
    except PermissionError as exc:
        denied_path = str(getattr(exc, "filename", "") or "")
        if not denied_path:
            message = str(exc)
            if str(ONEDRIVE_LATEST_PKG) in message:
                denied_path = str(ONEDRIVE_LATEST_PKG)
            elif str(LATEST_PKG) in message:
                denied_path = str(LATEST_PKG)
        evidence.update(
            {
                "permissionIssue": True,
                "permissionPath": denied_path or str(ONEDRIVE_LATEST_PKG),
                "permissionError": str(exc),
            }
        )
        return Check(
            "Latest RC pkg",
            "WARN",
            "permission_denied: grant Full Disk Access to the Companion service/Python and retry",
            evidence,
        )

    local_hash = sha256_bytes(local_bytes)
    cloud_hash = sha256_bytes(cloud_bytes)
    hashes_match = local_hash == cloud_hash
    signature = shell(["pkgutil", "--check-signature", str(LATEST_PKG)], timeout=8)
    payload = shell(["pkgutil", "--payload-files", str(LATEST_PKG)], timeout=8)
    signature_text = (signature.stdout + signature.stderr).strip()
    payload_lines = [line for line in payload.stdout.splitlines() if line.strip()]
    no_signature = "Status: no signature" in signature_text
    signed = "Status: signed" in signature_text or "Status: signed by" in signature_text
    stapler = shell(["xcrun", "stapler", "validate", str(LATEST_PKG)], timeout=12) if signed else None
    spctl = shell(["spctl", "-a", "-vv", "-t", "install", str(LATEST_PKG)], timeout=12) if signed else None
    stapler_text = ((stapler.stdout + stapler.stderr).strip() if stapler else "")
    spctl_text = ((spctl.stdout + spctl.stderr).strip() if spctl else "")
    notarized = bool(signed and stapler and stapler.returncode == 0)
    gatekeeper_ok = bool(signed and spctl and spctl.returncode == 0)
    evidence.update(
        {
            "localSha256": local_hash,
            "onedriveSha256": cloud_hash,
            "hashesMatch": hashes_match,
            "signature": signature_text,
            "signatureReturnCode": signature.returncode,
            "signed": signed,
            "noSignature": no_signature,
            "payloadFileCount": len(payload_lines),
            "payloadFilesPreview": payload_lines[:20],
            "payloadReturnCode": payload.returncode,
            "stapler": stapler_text,
            "staplerReturnCode": stapler.returncode if stapler else None,
            "spctl": spctl_text,
            "spctlReturnCode": spctl.returncode if spctl else None,
            "notarized": notarized,
            "gatekeeperInstallAccepted": gatekeeper_ok,
        }
    )

    problems: list[str] = []
    if not hashes_match:
        problems.append("hash_mismatch")
    if payload.returncode != 0:
        problems.append(f"payload_check_failed={payload.returncode}")
    elif payload_lines:
        problems.append(f"payload_files={len(payload_lines)}")
    if no_signature:
        problems.append("no signature")
    elif not signed:
        problems.append("signature_unknown")
    elif not notarized:
        problems.append("not notarized")
    if signed and notarized and not gatekeeper_ok:
        problems.append(f"spctl_rejected={spctl.returncode if spctl else 'missing'}")

    if not problems:
        return Check(
            "Latest RC pkg",
            "OK",
            "signed notarized nopayload pkg; local and OneDrive hashes match",
            evidence,
        )
    return Check("Latest RC pkg", "WARN", "; ".join(problems), evidence)


def check_release_sha256_manifest() -> Check:
    local_exists = RELEASE_SHA256SUMS.exists()
    cloud_exists = ONEDRIVE_RELEASE_SHA256SUMS.exists()
    evidence: dict[str, Any] = {
        "localManifest": str(RELEASE_SHA256SUMS),
        "onedriveManifest": str(ONEDRIVE_RELEASE_SHA256SUMS),
        "localExists": local_exists,
        "onedriveExists": cloud_exists,
    }
    if not local_exists or not cloud_exists:
        return Check(
            "Release SHA256 manifest",
            "WARN",
            f"local={local_exists}, onedrive={cloud_exists}",
            evidence,
        )
    try:
        local_text = RELEASE_SHA256SUMS.read_text(encoding="utf-8")
        cloud_text = ONEDRIVE_RELEASE_SHA256SUMS.read_text(encoding="utf-8")
        entries = read_sha256_manifest(RELEASE_SHA256SUMS)
    except PermissionError as exc:
        evidence.update(
            {
                "permissionIssue": True,
                "permissionPath": str(getattr(exc, "filename", "") or ONEDRIVE_RELEASE_SHA256SUMS),
                "permissionError": str(exc),
            }
        )
        return Check(
            "Release SHA256 manifest",
            "WARN",
            "permission_denied: grant Full Disk Access to the Companion service/Python and retry",
            evidence,
        )
    except Exception as exc:
        evidence["error"] = str(exc)
        return Check("Release SHA256 manifest", "WARN", f"cannot read manifest: {exc}", evidence)

    manifests_match = local_text == cloud_text
    evidence["manifestsMatch"] = manifests_match
    evidence["entryCount"] = len(entries)
    artifacts = [
        ("zip", LATEST_PACKAGE),
        ("pkg", LATEST_PKG),
    ]
    problems: list[str] = []
    if not manifests_match:
        problems.append("manifest_mismatch")
    artifact_evidence: dict[str, Any] = {}
    artifacts_match = True
    for label, path in artifacts:
        expected = entries.get(path.name, "")
        actual = ""
        exists = path.exists()
        if exists:
            try:
                actual = sha256_file(path)
            except PermissionError as exc:
                problems.append(f"{label}_permission")
                artifacts_match = False
                artifact_evidence[label] = {
                    "name": path.name,
                    "path": str(path),
                    "exists": True,
                    "expected": expected,
                    "actual": "",
                    "matches": False,
                    "permissionError": str(exc),
                }
                continue
        matches = bool(expected and actual and expected == actual)
        artifacts_match = artifacts_match and matches
        artifact_evidence[label] = {
            "name": path.name,
            "path": str(path),
            "exists": exists,
            "expected": expected,
            "actual": actual,
            "matches": matches,
        }
        if not expected:
            problems.append(f"{label}_missing_entry")
        elif not exists:
            problems.append(f"{label}_missing_file")
        elif not matches:
            problems.append(f"{label}_mismatch")
    evidence["artifacts"] = artifact_evidence
    evidence["artifactsMatch"] = artifacts_match
    if not problems:
        return Check(
            "Release SHA256 manifest",
            "OK",
            "local and OneDrive SHA256SUMS match zip/pkg artifacts",
            evidence,
        )
    return Check("Release SHA256 manifest", "WARN", "; ".join(problems), evidence)


def check_release_maintainer_prerequisites() -> Check:
    identity_result = shell(["security", "find-identity", "-v", "-p", "basic"], timeout=8)
    identity_output = identity_result.stdout + identity_result.stderr
    identities = parse_developer_id_installer_identities(identity_output)
    notary_mode = notary_credentials_mode()
    auto_sign_ready = len(identities) == 1
    manual_sign_possible = len(identities) >= 1
    evidence: dict[str, Any] = {
        "developerIdInstallerIdentities": identities,
        "developerIdInstallerCount": len(identities),
        "securityReturnCode": identity_result.returncode,
        "autoSignReady": auto_sign_ready,
        "manualSignPossible": manual_sign_possible,
        "notaryCredentialsConfigured": bool(notary_mode),
        "notaryCredentialsMode": notary_mode,
    }
    problems: list[str] = []
    if not identities:
        problems.append("missing_developer_id_installer")
    elif len(identities) > 1:
        problems.append("multiple_developer_id_installer_identities")
    if not notary_mode:
        problems.append("missing_notary_credentials")
    if not problems:
        return Check(
            "Release maintainer prerequisites",
            "OK",
            "single Developer ID Installer identity and notarytool credentials are configured",
            evidence,
        )
    return Check("Release maintainer prerequisites", "WARN", "; ".join(problems), evidence)


def check_database() -> Check:
    if not DB_PATH.exists():
        return Check("MN4 database", "WARN", f"not found: {DB_PATH}")
    try:
        conn = sqlite3.connect(DB_PATH)
        try:
            columns = {
                str(row[1])
                for row in conn.execute("pragma table_info(ZBOOKNOTE)").fetchall()
                if len(row) > 1
            }

            def count_where(parts: list[str], params: tuple[Any, ...] = ()) -> int:
                if not parts:
                    return 0
                where = " or ".join(f"({part})" for part in parts)
                return int(conn.execute(f"select count(*) from ZBOOKNOTE where {where}", params).fetchone()[0] or 0)

            title_parts: list[str] = []
            title_params: list[Any] = []
            comment_parts: list[str] = []
            comment_params: list[Any] = []
            if "ZNOTETITLE" in columns:
                title_parts.extend(
                    [
                        "ZNOTETITLE like ?",
                        "ZNOTETITLE like ?",
                        "ZNOTETITLE like ?",
                    ]
                )
                title_params.extend(["Codex短卡 %", "Codex 脑图%", "Codex高亮：%"])
            if "ZCOMMENT" in columns:
                comment_parts.extend(
                    [
                        "ZCOMMENT like ?",
                        "ZCOMMENT like ?",
                        "ZCOMMENT like ?",
                    ]
                )
                comment_params.extend(["%codex-paper-companion:%", "%full-reading:%", "%Codex%"])

            cards = count_where(
                (["ZNOTETITLE like ?"] if "ZNOTETITLE" in columns else [])
                + (["ZCOMMENT like ?"] if "ZCOMMENT" in columns else []),
                tuple((["Codex短卡 %"] if "ZNOTETITLE" in columns else []) + (["%:card:%"] if "ZCOMMENT" in columns else [])),
            )
            mindmap_nodes = count_where(
                (["ZNOTETITLE like ?"] if "ZNOTETITLE" in columns else [])
                + (["ZCOMMENT like ?"] if "ZCOMMENT" in columns else []),
                tuple((["Codex 脑图%"] if "ZNOTETITLE" in columns else []) + (["%:mindmap:%"] if "ZCOMMENT" in columns else [])),
            )
            highlight_nodes = count_where(
                ["ZNOTETITLE like ?"] if "ZNOTETITLE" in columns else [],
                ("Codex高亮：%",) if "ZNOTETITLE" in columns else (),
            )
            codex_notes = count_where(title_parts + comment_parts, tuple(title_params + comment_params))
        finally:
            conn.close()
    except PermissionError as exc:
        return Check("MN4 database", "WARN", f"permission denied: {exc}", {"path": str(DB_PATH)})
    except Exception as exc:
        return Check("MN4 database", "FAIL", f"query failed: {exc}", {"path": str(DB_PATH)})
    status = "OK" if codex_notes > 0 else "WARN"
    detail = (
        f"codex_notes={codex_notes}, cards={cards}, "
        f"mindmap_nodes={mindmap_nodes}, highlight_nodes={highlight_nodes}"
    )
    return Check(
        "MN4 Codex content",
        status,
        detail,
        {
            "codexNotes": codex_notes,
            "cards": cards,
            "mindmapNodes": mindmap_nodes,
            "highlightNodes": highlight_nodes,
            "db": str(DB_PATH),
        },
    )


def check_native_highlights() -> Check:
    if not DB_PATH.exists():
        return Check("Native highlight blobs", "WARN", f"database not found: {DB_PATH}")
    try:
        highlight_blobs = int(
            query_one(
                "select count(*) from ZBOOKNOTE where ZBOOKMD5=? and ZTOPICID=? and ZHIGHLIGHTS is not null",
                (NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5, NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID),
            )
            or 0
        )
    except PermissionError as exc:
        return Check("Native highlight blobs", "WARN", f"permission denied: {exc}", {"path": str(DB_PATH)})
    except Exception as exc:
        return Check("Native highlight blobs", "FAIL", f"query failed: {exc}", {"path": str(DB_PATH)})
    evidence = {
        "native_highlight_blobs": highlight_blobs,
        "topicid": NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID,
        "bookmd5": NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5,
        "db": str(DB_PATH),
    }
    if highlight_blobs > 0:
        return Check("Native highlight blobs", "OK", f"{highlight_blobs} rows have ZHIGHLIGHTS", evidence)
    return Check(
        "Native highlight blobs",
        "WARN",
        "0 rows have ZHIGHLIGHTS in the configured validation scope; visible native highlights are not proven",
        evidence,
    )


def check_webview_gap() -> Check:
    expected = [
        EXT_DIR / "CodexWebPanelController.js",
        EXT_DIR / "web/index.html",
        EXT_DIR / "web/app.css",
        EXT_DIR / "web/app.js",
    ]
    missing = [str(path) for path in expected if not path.exists()]
    if not missing:
        return Check("WebView chat UI", "OK", "WebView panel and web assets exist", {"files": [str(path) for path in expected]})
    return Check(
        "WebView chat UI",
        "WARN",
        "not fully installed; current panel may not have direct text-input chat",
        {"missing": missing},
    )


def read_events(limit: int = 200) -> list[dict[str, Any]]:
    if not EVENTS_PATH.exists():
        return []
    try:
        lines = EVENTS_PATH.read_text(encoding="utf-8").splitlines()[-limit:]
    except Exception:
        return []
    events: list[dict[str, Any]] = []
    for line in lines:
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            events.append(item)
    return events


def runtime_source_files() -> list[Path]:
    return [
        EXT_DIR / "main.js",
        EXT_DIR / "CodexPanelController.js",
        EXT_DIR / "CodexWebPanelController.js",
        EXT_DIR / "web/index.html",
        EXT_DIR / "web/app.js",
        EXT_DIR / "web/app.css",
        EXT_DIR / "web/styles.css",
    ]


def event_epoch(event: dict[str, Any] | None) -> float | None:
    if not isinstance(event, dict):
        return None
    raw = str(event.get("ts") or "")
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%Y-%m-%dT%H:%M:%S%z").timestamp()
    except Exception:
        return None


def runtime_staleness_evidence(reference_event: dict[str, Any] | None = None) -> dict[str, Any]:
    source_mtimes: list[tuple[Path, float]] = []
    for path in runtime_source_files():
        try:
            source_mtimes.append((path, path.stat().st_mtime))
        except OSError:
            continue
    if not source_mtimes:
        return {"staleRuntime": False, "reason": "no-runtime-source-files"}
    latest_source, source_mtime = max(source_mtimes, key=lambda item: item[1])
    try:
        events_mtime = EVENTS_PATH.stat().st_mtime
    except OSError:
        return {
            "staleRuntime": True,
            "reason": "missing-events-file",
            "latestRuntimeSource": str(latest_source),
            "runtimeSourceMtime": source_mtime,
        }
    reference_event_time = event_epoch(reference_event)
    reference_time = reference_event_time if reference_event_time and source_mtime > 1_000_000_000 else events_mtime
    stale = reference_time + 1 < source_mtime
    return {
        "staleRuntime": stale,
        "eventsMtime": events_mtime,
        "referenceEventTs": reference_event.get("ts") if isinstance(reference_event, dict) else "",
        "referenceEventTime": reference_event_time,
        "stalenessReferenceTime": reference_time,
        "latestRuntimeSource": str(latest_source),
        "runtimeSourceMtime": source_mtime,
    }


def runtime_handler_stale_evidence(
    events: list[dict[str, Any]],
    *,
    latest_web: dict[str, Any] | None = None,
    latest_native: dict[str, Any] | None = None,
) -> dict[str, Any]:
    reference_by_action = {
        "probe_native_api_capabilities": latest_native,
        "reload_web_panel": latest_web,
    }
    latest_unknown_epoch: dict[str, float] = {}
    latest_unknown_ts: dict[str, str] = {}
    for item in events:
        if str(item.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(item.get("event") or "") != "nativeQueueCommandUnknown":
            continue
        extra = item.get("extra") if isinstance(item.get("extra"), dict) else {}
        native_action = str(extra.get("nativeAction") or "")
        if native_action not in reference_by_action:
            continue
        unknown_epoch = event_epoch(item) or 0.0
        reference_epoch = event_epoch(reference_by_action[native_action]) or 0.0
        if unknown_epoch > reference_epoch and unknown_epoch >= latest_unknown_epoch.get(native_action, 0.0):
            latest_unknown_epoch[native_action] = unknown_epoch
            latest_unknown_ts[native_action] = str(item.get("ts") or "")
    actions = list(latest_unknown_epoch.keys())
    required_features = installed_required_native_handler_features()
    native_features = native_handler_features_from_event(latest_native)
    missing_features = [
        feature for feature in required_features if feature not in native_features
    ] if latest_native else []
    if missing_features:
        actions.append("native-handler-features")
    return {
        "runtimeHandlerStale": bool(actions),
        "runtimeHandlerStaleActions": actions,
        "runtimeHandlerLatestUnknownTs": latest_unknown_ts,
        "requiredNativeHandlerFeatures": required_features,
        "nativeHandlerFeatures": native_features,
        "missingNativeHandlerFeatures": missing_features,
    }


def installed_required_native_handler_features() -> list[str]:
    try:
        text = (EXT_DIR / "main.js").read_text(encoding="utf-8")
    except Exception:
        return list(REQUIRED_NATIVE_HANDLER_FEATURES)
    features = [feature for feature in REQUIRED_NATIVE_HANDLER_FEATURES if feature in text]
    return features or list(REQUIRED_NATIVE_HANDLER_FEATURES)


def native_handler_features_from_event(event: dict[str, Any] | None) -> list[str]:
    extra = event.get("extra") if isinstance((event or {}).get("extra"), dict) else {}
    features = extra.get("handlerFeatures") if isinstance(extra.get("handlerFeatures"), list) else []
    return [str(item) for item in features if item]


def web_controls_event_details(event: dict[str, Any]) -> dict[str, Any]:
    extra = event.get("extra") if isinstance(event.get("extra"), dict) else {}
    controls = {item for item in str(extra.get("controls") or "").split(",") if item}
    reported_missing = [item for item in str(extra.get("missing") or "").split(",") if item]
    absent = [item for item in REQUIRED_WEB_CONTROL_IDS if item not in controls]
    min_width = str(extra.get("minWidth") or "")
    min_height = str(extra.get("minHeight") or "")
    bad_size = min_width != "390" or min_height != "520"
    return {
        "controls": controls,
        "reported_missing": reported_missing,
        "absent": absent,
        "min_width": min_width,
        "min_height": min_height,
        "bad_size": bad_size,
        "complete": not reported_missing and not absent and not bad_size,
    }


def select_best_web_controls_event(matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in reversed(matches):
        if web_controls_event_details(item)["complete"]:
            return item
    return matches[-1] if matches else None


def select_best_native_api_event(matches: list[dict[str, Any]]) -> dict[str, Any] | None:
    required = installed_required_native_handler_features()
    for item in reversed(matches):
        features = native_handler_features_from_event(item)
        if required and all(feature in features for feature in required):
            return item
    return matches[-1] if matches else None


def check_runtime_webview() -> Check:
    events = read_events()
    if not events:
        return Check("MN4 runtime WebView", "WARN", "no plugin events recorded yet", {"events": str(EVENTS_PATH)})
    web_events = [
        item
        for item in events
        if str(item.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
        and str(item.get("event") or "") in {"webPanelLoaded", "panelShownState", "sceneWillConnect"}
    ]
    loaded = any(str(item.get("event") or "") == "webPanelLoaded" for item in web_events)
    shown = any(
        str(item.get("event") or "") == "panelShownState"
        and isinstance(item.get("extra"), dict)
        and item["extra"].get("panelKind") == "webview"
        for item in web_events
    )
    if loaded and shown:
        return Check("MN4 runtime WebView", "OK", f"MN4 loaded pluginVersion {CURRENT_PLUGIN_VERSION} and WebView panel")
    if web_events:
        return Check("MN4 runtime WebView", "WARN", f"{CURRENT_PLUGIN_VERSION} events exist, but WebView panel load/show is not fully proven")
    return Check("MN4 runtime WebView", "WARN", f"restart MarginNote 4 to load pluginVersion {CURRENT_PLUGIN_VERSION}")


def check_runtime_web_controls() -> Check:
    events = read_events(400)
    matches = [
        item
        for item in events
        if str(item.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
        and str(item.get("event") or "") == "webControlsReady"
    ]
    if not matches:
        return Check(
            "MN4 runtime Web controls",
            "WARN",
            f"no webControlsReady event for pluginVersion {CURRENT_PLUGIN_VERSION}; restart MN4 and open the panel",
            {"events": str(EVENTS_PATH), "required": REQUIRED_WEB_CONTROL_IDS},
        )
    latest = select_best_web_controls_event(matches)
    assert latest is not None
    details = web_controls_event_details(latest)
    controls = details["controls"]
    reported_missing = details["reported_missing"]
    absent = details["absent"]
    min_width = details["min_width"]
    min_height = details["min_height"]
    bad_size = details["bad_size"]
    stale = runtime_staleness_evidence(latest)
    handler_stale = runtime_handler_stale_evidence(events, latest_web=latest)
    evidence = {"event": latest, **stale, **handler_stale}
    if stale.get("staleRuntime") or handler_stale.get("runtimeHandlerStale"):
        reasons: list[str] = []
        if stale.get("staleRuntime"):
            reasons.append("stale runtime event; installed Web assets changed after the last MN4 event")
        if handler_stale.get("runtimeHandlerStale"):
            reasons.append(f"runtime handler does not know {handler_stale.get('runtimeHandlerStaleActions') or []}")
        detail = "; ".join(reasons) + "; restart MarginNote 4 or reopen the Codex panel"
        if reported_missing or absent or bad_size:
            detail += (
                f"; previous reported_missing={reported_missing or []}, "
                f"absent={absent or []}, min={min_width or '?'}x{min_height or '?'}"
            )
        return Check("MN4 runtime Web controls", "WARN", detail, evidence)
    if not reported_missing and not absent and not bad_size:
        return Check(
            "MN4 runtime Web controls",
            "OK",
            f"{len(controls)} controls reported, min={min_width}x{min_height}",
            evidence,
        )
    detail = (
        f"reported_missing={reported_missing or []}, absent={absent or []}, "
        f"min={min_width or '?'}x{min_height or '?'}"
    )
    return Check("MN4 runtime Web controls", "FAIL", detail, evidence)


def check_runtime_native_api_capabilities() -> Check:
    events = read_events(600)
    matches = [
        item
        for item in events
        if str(item.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
        and str(item.get("event") or "") == "nativeApiCapabilities"
    ]
    if not matches:
        return Check(
            "MN4 native API probe",
            "WARN",
            f"no nativeApiCapabilities event for pluginVersion {CURRENT_PLUGIN_VERSION}; open the panel to probe selectors",
            {"events": str(EVENTS_PATH)},
        )
    latest = select_best_native_api_event(matches)
    assert latest is not None
    web_matches = [
        item
        for item in events
        if str(item.get("pluginVersion") or "") == CURRENT_PLUGIN_VERSION
        and str(item.get("event") or "") == "webControlsReady"
    ]
    latest_web = select_best_web_controls_event(web_matches) if web_matches else None
    extra = latest.get("extra") if isinstance(latest.get("extra"), dict) else {}
    methods = extra.get("candidateMethods") if isinstance(extra.get("candidateMethods"), list) else []
    matrix = extra.get("capabilityMatrix") if isinstance(extra.get("capabilityMatrix"), dict) else {}
    matrix_present = bool(matrix)
    ready_actions = [
        str(key)
        for key, value in matrix.items()
        if isinstance(value, dict) and bool(value.get("ready"))
    ]
    blocked_actions = [
        str(key)
        for key, value in matrix.items()
        if isinstance(value, dict) and bool(value.get("available")) and not bool(value.get("ready"))
    ]
    highlight_candidate = bool(extra.get("hasNativeHighlightCandidate"))
    export_candidate = bool(extra.get("hasAnnotatedExportCandidate"))
    stale = runtime_staleness_evidence(latest)
    status = "OK" if matrix_present and (ready_actions or highlight_candidate or export_candidate or methods) else "WARN"
    detail = (
        f"highlight_candidate={highlight_candidate}, "
        f"export_candidate={export_candidate}, candidates={len(methods)}, "
        f"ready_actions={len(ready_actions)}, blocked_actions={len(blocked_actions)}, "
        f"capability_matrix={matrix_present}"
    )
    handler_stale = runtime_handler_stale_evidence(events, latest_web=latest_web, latest_native=latest)
    runtime_handler_stale = bool(handler_stale.get("runtimeHandlerStale"))
    runtime_handler_stale_actions = handler_stale.get("runtimeHandlerStaleActions") or []
    if runtime_handler_stale:
        detail += (
            f"; runtime_handler_stale=True; MN4 runtime treated {runtime_handler_stale_actions} "
            "as unknown; reopen the Codex panel or restart MarginNote 4 to load installed main.js"
        )
        status = "WARN"
    if stale.get("staleRuntime"):
        detail += "; stale runtime event; installed plugin assets changed after the last MN4 probe"
        status = "WARN"
    return Check(
        "MN4 native API probe",
        status,
        detail,
        {
            "event": latest,
            **stale,
            "candidateMethods": methods,
            "readyActions": ready_actions,
            "blockedActions": blocked_actions,
            "capabilityMatrix": matrix,
            **handler_stale,
        },
    )


def pymupdf_python_candidates() -> list[Path]:
    raw_candidates = [
        os.environ.get("CODEX_MN_PYMUPDF_PYTHON"),
        sys.executable,
        str(HOME / "miniforge3/bin/python3"),
        "/opt/homebrew/bin/python3",
        "/opt/homebrew/bin/python3.12",
        "/usr/local/bin/python3",
        str(HOME / ".cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3"),
    ]
    candidates: list[Path] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        if not raw:
            continue
        candidate = Path(raw).expanduser()
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.exists():
            candidates.append(candidate)
    return candidates


def find_pymupdf_python() -> tuple[Path | None, str | None]:
    errors: list[str] = []
    for candidate in pymupdf_python_candidates():
        try:
            proc = shell([str(candidate), "-c", "import fitz"], timeout=8)
        except Exception as exc:
            errors.append(f"{candidate}: {exc}")
            continue
        if proc.returncode == 0:
            return candidate, None
        errors.append(f"{candidate}: {proc.stderr.strip() or proc.returncode}")
    return None, "; ".join(errors[-3:]) if errors else "no python candidates found"


def check_pdf_export_runtime() -> Check:
    python, error = find_pymupdf_python()
    export_dir = ONEDRIVE_DIR / "exports"
    if python is None:
        return Check(
            "PDF highlight-copy export",
            "WARN",
            "PyMuPDF not available; export_annotated_pdf will explain how to configure CODEX_MN_PYMUPDF_PYTHON",
            {"error": error, "exportDir": str(export_dir)},
        )
    status = "OK" if ONEDRIVE_DIR.exists() else "WARN"
    detail = f"PyMuPDF python={python}, exportDir={export_dir}"
    return Check(
        "PDF highlight-copy export",
        status,
        detail,
        {"python": str(python), "exportDir": str(export_dir), "onedriveExists": ONEDRIVE_DIR.exists()},
    )


def check_companion_file_access_permissions() -> Check:
    result = http_action_json(
        {
            "action": "diagnose_permissions",
            "topicid": NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID,
            "bookmd5": NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5,
            "source": "doctor.py",
        }
    )
    if not result or not result.get("ok"):
        return Check(
            "Companion file access",
            "WARN",
            "diagnose_permissions did not return a usable response",
            {"response": result},
        )
    status_value = str(result.get("status") or "WARN")
    file_access = result.get("fileAccess") if isinstance(result.get("fileAccess"), dict) else {}
    source_status = ""
    cache_status = ""
    database_status = ""
    export_status = ""
    if isinstance(file_access.get("sourcePdf"), dict):
        source_status = str(file_access["sourcePdf"].get("status") or "")
    if isinstance(file_access.get("pdfCache"), dict):
        cache_status = str(file_access["pdfCache"].get("status") or "")
    if isinstance(file_access.get("mnDatabase"), dict):
        database_status = str(file_access["mnDatabase"].get("status") or "")
    if isinstance(file_access.get("exportDir"), dict):
        export_status = str(file_access["exportDir"].get("status") or "")
    status = "OK" if status_value == "OK" else "WARN"
    detail = (
        f"{status_value}, sourcePdf={source_status or '?'}, "
        f"pdfCache={cache_status or '?'}, mnDatabase={database_status or '?'}, "
        f"exportDir={export_status or '?'}"
    )
    return Check("Companion file access", status, detail, result)


def check_full_reading_dedupe() -> Check:
    events = read_events(300)
    matches = []
    for item in events:
        if str(item.get("pluginVersion") or "") != CURRENT_PLUGIN_VERSION:
            continue
        if str(item.get("event") or "") != "createCardsFinished":
            continue
        extra = item.get("extra") or {}
        requested = int(extra.get("requested") or 0) if isinstance(extra, dict) else 0
        created = int(extra.get("created") or 0) if isinstance(extra, dict) else 0
        skipped = int(extra.get("skipped") or 0) if isinstance(extra, dict) else 0
        if requested > 0 and created == 0 and skipped >= requested:
            matches.append(item)
    if matches:
        extra = matches[-1].get("extra") or {}
        detail = (
            f"latest duplicate card write requested={extra.get('requested')}, "
            f"skipped={extra.get('skipped')}, created={extra.get('created')}, scanned={extra.get('dedupeScanned')}"
        )
        return Check("Full-reading dedupe", "OK", detail, {"event": matches[-1]})
    return Check(
        "Full-reading dedupe",
        "WARN",
        "no recent createCardsFinished event proving requested>0, created=0, skipped>=requested",
        {"events": str(EVENTS_PATH)},
    )


def check_highlight_policy() -> Check:
    allow = os.environ.get("CODEX_MN_ALLOW_DB_HIGHLIGHT_WRITE", "0") == "1"
    if allow:
        return Check("Highlight DB write policy", "WARN", "experimental DB highlight writes are enabled")
    return Check("Highlight DB write policy", "OK", "direct SQLite highlight writes are disabled by default")


def run_checks() -> list[Check]:
    return [
        check_mn4_app(),
        check_extension(),
        check_companion(),
        check_launch_agent(),
        check_release_package(),
        check_release_pkg(),
        check_release_sha256_manifest(),
        check_release_maintainer_prerequisites(),
        check_database(),
        check_full_reading_dedupe(),
        check_native_highlights(),
        check_webview_gap(),
        check_runtime_webview(),
        check_runtime_web_controls(),
        check_runtime_native_api_capabilities(),
        check_pdf_export_runtime(),
        check_companion_file_access_permissions(),
        check_highlight_policy(),
    ]


def print_text(checks: list[Check]) -> None:
    width = max(len(item.name) for item in checks)
    for item in checks:
        print(f"[{item.status:<4}] {item.name:<{width}}  {item.detail}")
    fails = sum(1 for item in checks if item.status == "FAIL")
    warns = sum(1 for item in checks if item.status == "WARN")
    print()
    print(f"Summary: {fails} fail, {warns} warn, {len(checks) - fails - warns} ok")


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnose Codex Companion installation and release-readiness state.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as failures.")
    args = parser.parse_args()

    checks = run_checks()
    if args.json:
        print(json.dumps([item.__dict__ for item in checks], ensure_ascii=False, indent=2))
    else:
        print_text(checks)
    has_fail = any(item.status == "FAIL" for item in checks)
    has_warn = any(item.status == "WARN" for item in checks)
    if has_fail or (args.strict and has_warn):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
