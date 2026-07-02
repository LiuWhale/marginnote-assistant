#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import importlib.util
import json
import os
import re
import socket
import subprocess
import struct
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SCHEMA = "codex-companion-ui-functional-acceptance-v1"
ROOT = Path(__file__).resolve().parent

REQUIRED_CONTROL_IDS = [
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
    "workspaceSurfaceSelect",
    "workspaceNavigatorToggleButton",
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
    "notebookWorkspaceDetailsToggleButton",
    "notebookWorkspaceRefreshButton",
    "notebookWorkspaceDetails",
    "notebookWorkspaceGrid",
    "notebookKnowledgeMatrix",
    "notebookKnowledgeMatrixSummary",
    "notebookKnowledgeMatrixList",
    "notebookObjectIntake",
    "notebookObjectIntakeSummary",
    "notebookObjectIntakeRoutes",
    "notebookObjectTaskComposer",
    "notebookObjectTaskComposerSummary",
    "notebookObjectTaskComposerList",
    "notebookWorkspaceRunbook",
    "notebookWorkspaceRunbookSummary",
    "notebookWorkspaceRunbookAutoButton",
    "notebookWorkspaceRunbookAutoStatus",
    "notebookWorkspaceRunbookContinueButton",
    "notebookWorkspaceRunbookList",
    "notebookWorkspaceActions",
    "sourceRegistryPanel",
    "objectBrowserPanel",
    "objectRegistryScanButton",
    "mindmapTreeCacheStatus",
    "mindmapTreeRefreshButton",
    "mindmapStudioPanel",
    "mindmapStudioReadTreeButton",
    "knowledgeWorkspaceReviewQueue",
    "knowledgeWorkspaceReviewList",
    "operationLedgerDrawer",
    "operationLedgerPanel",
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
    "workflowBuilderBoardPanel",
    "workflowBuilderBoardLanes",
    "skillCenterPanel",
    "externalGatewayPanel",
    "commandPanePanel",
    "promptInput",
    "sendButton",
    "conversationHistoryPage",
    "conversationHistoryButton",
    "conversationHistoryCloseButton",
    "configPage",
    "settingsButton",
    "configBackButton",
]

REQUIRED_JS_MARKERS = [
    "function renderNotebookWorkspace",
    "function renderNotebookKnowledgeMatrix",
    "function renderNotebookObjectIntake",
    "function renderNotebookObjectTaskComposer",
    "function renderNotebookWorkspaceRunbook",
    "function currentNotebookScopePayload",
    "function runNotebookWorkspaceAction",
    "function switchWorkspaceSurface",
    "function renderObjectBrowser",
    "function requestObjectRegistryScan",
    "function requestMindmapTreeRead",
    "function openConfigPage",
    "function openConversationHistory",
    "function renderRealMnAcceptancePanel",
    "item.disabled",
    "disabledReason",
    "data-notebook-workspace-action",
    "data-notebook-runbook-step",
    "postCompanion('notebook_workspace'",
    "postCompanion('single_document_acceptance_summary'",
]

REQUIRED_WORKSPACE_SURFACES = [
    "console",
    "object_browser",
    "source_registry",
    "mindmap_studio",
    "verification_center",
    "card_factory",
    "ledger_explorer",
    "knowledge_graph",
    "workflow_builder",
    "skill_center",
]

BROWSER_RENDER_MARKERS = [
    'id="aiChatShell"',
    'data-product-mode="chat"',
    'id="knowledgeOsContractPanel"',
    'id="workspaceNavigator"',
    'id="notebookWorkspacePanel"',
    'id="notebookKnowledgeMatrix"',
    'id="notebookObjectIntake"',
    'id="notebookObjectTaskComposer"',
    'id="notebookWorkspaceRunbook"',
    'id="workflowBuilderBoardPanel"',
    'id="realMnAcceptancePanel"',
    'id="sendButton"',
]

BROWSER_NATIVE_DISABLED_IDS = [
    "objectRegistryScanButton",
    "mindmapTreeRefreshButton",
]

BROWSER_INTERACTION_EXPECTED = {
    "initialMode": "chat",
    "chatMode": "chat",
    "workspaceMode": "workspace",
    "mindmapSurface": "mindmap_studio",
    "mindmapPane": "operation",
    "cardSurface": "card_factory",
    "cardPane": "knowledge",
    "workflowSurface": "workflow_builder",
    "workflowPane": "workflow",
}

BROWSER_INTERACTION_EXPECTED_SURFACES = {
    "workspaceNavConsoleButton": ("console", "object"),
    "workspaceNavMindmapStudioButton": ("mindmap_studio", "operation"),
    "workspaceNavCardFactoryButton": ("card_factory", "knowledge"),
    "workspaceNavLedgerExplorerButton": ("ledger_explorer", "object"),
    "workspaceNavKnowledgeGraphButton": ("knowledge_graph", "knowledge"),
    "workspaceNavWorkflowBuilderButton": ("workflow_builder", "workflow"),
    "workspaceNavSkillCenterButton": ("skill_center", "workflow"),
}

BROWSER_INTERACTION_EXPECTED_TABS = {
    "workbenchTabObject": "object",
    "workbenchTabOperation": "operation",
    "workbenchTabKnowledge": "knowledge",
    "workbenchTabWorkflow": "workflow",
}

BROWSER_INTERACTION_EXPECTED_SELECT_SURFACES = {
    "object_browser": {
        "pane": "object",
        "visible": ["objectWorkspacePanel", "objectBrowserPanel"],
        "hidden": ["knowledgeConsolePanel", "operationWorkspacePanel", "knowledgeWorkspacePanel", "workflowWorkspacePanel"],
    },
    "source_registry": {
        "pane": "object",
        "visible": ["knowledgeConsolePanel", "notebookWorkspacePanel", "sourceRegistryPanel"],
        "hidden": ["workbenchTabs", "workbenchLayout"],
    },
    "verification_center": {
        "pane": "operation",
        "visible": ["operationWorkspacePanel", "verificationReportPanel"],
        "hidden": ["knowledgeConsolePanel", "mindmapStudioPanel", "knowledgeWorkspacePanel", "workflowWorkspacePanel"],
    },
}

BROWSER_INTERACTION_EXPECTED_LAYOUT = {
    "workspaceNavConsoleButton": {
        "visible": ["knowledgeConsolePanel", "notebookWorkspacePanel"],
        "hidden": [
            "workbenchTabs",
            "workbenchLayout",
            "objectWorkspacePanel",
            "operationWorkspacePanel",
            "knowledgeWorkspacePanel",
            "workflowWorkspacePanel",
            "objectBrowserPanel",
            "objectGraphPanel",
            "objectActivityPanel",
            "operationLedgerDrawer",
            "notebookWorkspaceDetails",
            "notebookWorkspaceGrid",
            "notebookObjectIntake",
            "notebookObjectTaskComposer",
            "sourceRegistryPanel",
            "notebookWorkspaceStudyProgram",
            "notebookWorkspaceRunbook",
            "notebookWorkspaceActions",
        ],
    },
    "workspaceNavMindmapStudioButton": {
        "visible": ["operationWorkspacePanel", "mindmapStudioPanel", "mindmapDiffWorkbench"],
        "hidden": ["knowledgeConsolePanel", "verificationReportPanel", "knowledgeWorkspacePanel", "workflowWorkspacePanel"],
    },
    "workspaceNavCardFactoryButton": {
        "visible": ["knowledgeWorkspacePanel", "knowledgeWorkspaceReviewQueue", "knowledgeWorkspaceReviewList"],
        "hidden": ["knowledgeConsolePanel", "objectWorkspacePanel", "operationWorkspacePanel", "workflowWorkspacePanel", "knowledgeWorkspaceResults"],
    },
    "workspaceNavLedgerExplorerButton": {
        "visible": ["objectWorkspacePanel", "operationLedgerDrawer"],
        "hidden": ["knowledgeConsolePanel", "objectBrowserPanel", "objectGraphPanel", "objectActivityPanel", "operationWorkspacePanel", "knowledgeWorkspacePanel", "workflowWorkspacePanel"],
    },
    "workspaceNavKnowledgeGraphButton": {
        "visible": ["knowledgeWorkspacePanel", "knowledgeWorkspaceResults"],
        "hidden": ["knowledgeConsolePanel", "knowledgeWorkspaceReviewQueue", "knowledgeWorkspaceReviewList", "objectWorkspacePanel", "operationWorkspacePanel", "workflowWorkspacePanel"],
    },
    "workspaceNavWorkflowBuilderButton": {
        "visible": ["workflowWorkspacePanel", "workflowBuilderBoardPanel", "workflowWorkspaceTemplates"],
        "hidden": ["knowledgeConsolePanel", "objectWorkspacePanel", "operationWorkspacePanel", "knowledgeWorkspacePanel", "skillCenterPanel"],
    },
    "workspaceNavSkillCenterButton": {
        "visible": ["workflowWorkspacePanel", "skillCenterPanel", "workflowWorkspaceSkills"],
        "hidden": ["knowledgeConsolePanel", "workflowBuilderBoardPanel", "workflowWorkspaceTemplates", "objectWorkspacePanel", "operationWorkspacePanel", "knowledgeWorkspacePanel"],
    },
}

BROWSER_ACTION_REQUIRED_BUTTONS = [
    "sendButton",
    "newConversationButton",
    "conversationHistoryAllButton",
    "conversationHistoryObjectButton",
    "agentPlanRefreshButton",
    "contextScopeSelectionButton",
    "contextScopeDocumentButton",
    "objectRegistryScanButton",
    "objectBrowserFilterButton",
    "objectGraphRefreshButton",
    "objectActivityRefreshButton",
    "mindmapTreeRefreshButton",
    "mindmapStudioReadTreeButton",
    "mindmapTargetRefreshButton",
    "notebookWorkspaceRefreshButton",
    "notebookWorkspaceRunbookAutoButton",
    "notebookWorkspaceRunbookContinueButton",
    "objectBrowserRefreshButton",
    "operationLedgerRefreshButton",
    "operationLedgerFilterButton",
    "verificationReportRefreshButton",
    "verificationRepairPlanRecommendedButton",
    "realMnAcceptanceRunAllButton",
    "singleDocumentAcceptanceButton",
    "mainUiFunctionalAcceptanceButton",
    "realMnAcceptanceSafeEvidenceButton",
    "nativeHighlightWizardRetryButton",
    "nativeHighlightWizardRefreshButton",
    "knowledgeWorkspaceSearchButton",
    "objectGraphRelationAddButton",
    "objectGraphRelationSaveButton",
    "objectGraphRelationCancelButton",
    "settingsButton",
    "contextButton",
    "saveFileSearchRootsButton",
    "updateCheckButton",
    "updateInstallButton",
    "permissionDiagnoseButton",
    "openPermissionSettingsButton",
    "cacheCurrentPdfButton",
    "nativeCapabilitiesRefreshButton",
    "healthCheckButton",
    "aiBackendProbeButton",
    "uiFunctionalAcceptanceButton",
    "logsRefreshButton",
    "conversationHistoryButton",
]

BROWSER_ACTION_REQUIRED_ACTIONS = [
    "chat",
    "conversation_new",
    "agent_plan",
    "request_mn_object_registry_scan",
    "mn_read_tree",
    "notebook_workspace",
    "object_browser",
    "object_graph",
    "object_activity",
    "operation_ledger_list",
    "verification_report_list",
    "knowledge_index_search",
    "mindmap_target_status",
    "notebook_runbook_preflight_record",
    "object_graph_relation_save",
    "request_mn_object_existence_probe",
    "single_document_acceptance_summary",
    "settings_update",
    "update_check",
    "open_url",
    "diagnose_permissions",
    "open_full_disk_access_settings",
    "request_pdf_cache",
    "request_native_capability_probe",
    "request_pdf_selection_probe",
    "native_highlight_wizard_start",
    "native_highlight_wizard_status",
    "health",
    "ai_backend_probe",
    "ui_functional_acceptance_summary",
    "logs_recent",
    "conversation_list",
]

BROWSER_ACTION_BUTTON_ACTIONS = {
    "sendButton": "chat",
    "newConversationButton": "conversation_new",
    "conversationHistoryAllButton": "conversation_list",
    "conversationHistoryObjectButton": "conversation_list",
    "agentPlanRefreshButton": "agent_plan",
    "objectRegistryScanButton": "request_mn_object_registry_scan",
    "mindmapTreeRefreshButton": "mn_read_tree",
    "mindmapStudioReadTreeButton": "mn_read_tree",
    "notebookWorkspaceRefreshButton": "notebook_workspace",
    "notebookWorkspaceRunbookAutoButton": "notebook_runbook_preflight_record",
    "notebookWorkspaceRunbookContinueButton": "object_browser",
    "objectBrowserRefreshButton": "object_browser",
    "objectBrowserFilterButton": "object_browser",
    "objectGraphRefreshButton": "object_graph",
    "objectActivityRefreshButton": "object_activity",
    "operationLedgerRefreshButton": "operation_ledger_list",
    "operationLedgerFilterButton": "operation_ledger_list",
    "verificationReportRefreshButton": "verification_report_list",
    "knowledgeWorkspaceSearchButton": "knowledge_index_search",
    "mindmapTargetRefreshButton": "mindmap_target_status",
    "objectGraphRelationSaveButton": "object_graph_relation_save",
    "verificationRepairPlanRecommendedButton": "request_mn_object_existence_probe",
    "realMnAcceptanceRunAllButton": "single_document_acceptance_summary",
    "singleDocumentAcceptanceButton": "single_document_acceptance_summary",
    "mainUiFunctionalAcceptanceButton": "ui_functional_acceptance_summary",
    "realMnAcceptanceSafeEvidenceButton": "request_native_capability_probe",
    "nativeHighlightWizardRetryButton": "native_highlight_wizard_start",
    "nativeHighlightWizardRefreshButton": "request_pdf_selection_probe",
    "saveFileSearchRootsButton": "settings_update",
    "updateCheckButton": "update_check",
    "updateInstallButton": "open_url",
    "permissionDiagnoseButton": "diagnose_permissions",
    "openPermissionSettingsButton": "open_full_disk_access_settings",
    "cacheCurrentPdfButton": "request_pdf_cache",
    "nativeCapabilitiesRefreshButton": "request_native_capability_probe",
    "healthCheckButton": "health",
    "aiBackendProbeButton": "ai_backend_probe",
    "uiFunctionalAcceptanceButton": "ui_functional_acceptance_summary",
    "logsRefreshButton": "logs_recent",
    "conversationHistoryButton": "conversation_list",
}

BROWSER_ACTION_REQUIRED_BRIDGE_ACTIONS = [
    "context",
]

BROWSER_WRITE_REQUIRED_CLICK_TARGETS = [
    "replyMindmapTreeButton",
    "aiEditRejectButton",
    "aiEditAcceptButton",
    "aiEditReviewQueueButton",
    "mindmapStudioPreviewDiffButton",
    "mindmapStudioApplySelectedButton",
    "mindmapStudioVerifyButton",
    "mindmapStudioRollbackButton",
    "transactionVerifyButton",
    "transactionEvidenceButton",
    "transactionProbeButton",
]

BROWSER_WRITE_REQUIRED_COMPANION_ACTIONS = [
    "generate_mindmap",
    "draft_save",
    "mindmap_diff_preview",
    "request_mindmap_diff_apply",
    "ai_edit_transaction_get",
    "ai_edit_transaction_verify",
    "request_mn_object_existence_probe",
    "review_queue_add",
]

BROWSER_WRITE_REQUIRED_BRIDGE_ACTIONS = [
    "write_draft",
    "accept_ai_edit_transaction",
    "reject_ai_edit_transaction",
]

BUTTON_COVERAGE_INTERACTION_BUTTONS = [
    "chatModeButton",
    "agentWorkspaceModeButton",
    "advancedReadButton",
    "advancedMindmapButton",
    "advancedCardsButton",
    "advancedNextStepButton",
    "expertModeToggleButton",
    "expertModeBackButton",
    "commandPaneToggleButton",
    "configBackButton",
    "contextScopeAutoButton",
    "conversationHistoryAllButton",
    "conversationHistoryCloseButton",
    "conversationHistoryObjectButton",
    "workspaceNavigatorToggleButton",
    "notebookWorkspaceDetailsToggleButton",
    "notebookKnowledgeMatrixToggleButton",
    "workbenchTabObject",
    "workbenchTabOperation",
    "workbenchTabKnowledge",
    "workbenchTabWorkflow",
    "workspaceNavConsoleButton",
    "workspaceNavMindmapStudioButton",
    "workspaceNavCardFactoryButton",
    "workspaceNavLedgerExplorerButton",
    "workspaceNavKnowledgeGraphButton",
    "workspaceNavWorkflowBuilderButton",
    "workspaceNavSkillCenterButton",
]

BUTTON_COVERAGE_WRITE_BUTTONS = [
    "mindmapStudioPreviewDiffButton",
    "mindmapStudioApplySelectedButton",
    "mindmapStudioVerifyButton",
    "mindmapStudioRollbackButton",
]

BUTTON_COVERAGE_PANEL_CONTROL_BUTTONS = [
    "advancedVerifyButton",
    "knowledgeWorkspaceSearchButton",
    "mindmapStudioReadTreeButton",
    "mindmapTargetRefreshButton",
    "objectActivityRefreshButton",
    "objectBrowserFilterButton",
    "objectGraphRefreshButton",
    "operationLedgerFilterButton",
]

BUTTON_COVERAGE_DYNAMIC_BUTTONS = [
]

BUTTON_COVERAGE_FORM_OR_DESTRUCTIVE_BUTTONS = [
    "clearMnUrlApiSecretButton",
    "clearOpenAIKeyButton",
    "logsClearButton",
    "saveSettingsButton",
]

BUTTON_COVERAGE_FILE_PICKER_BUTTONS = [
    "pdfCacheFileBannerButton",
    "pdfCacheFileButton",
]

BUTTON_COVERAGE_CLOSE_ONLY_BUTTONS = [
    "closeButton",
    "operationLedgerDetailCloseButton",
    "workflowRunInspectorCloseButton",
]

BUTTON_COVERAGE_HIDDEN_RUNTIME_BUTTONS = [
    "stopButton",
    "updateNoticeOpenSettingsButton",
]

BROWSER_CANDIDATE_PATHS = [
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/常用/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]


class IdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key == "id" and value:
                self.ids.add(value)


class ButtonIdCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.button_ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "button":
            return
        for key, value in attrs:
            if key == "id" and value:
                self.button_ids.add(value)


def pass_check(check_id: str, label: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"id": check_id, "label": label, "status": "PASS", "evidence": evidence or {}, "problems": []}


def fail_check(check_id: str, label: str, problems: list[str], evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"id": check_id, "label": label, "status": "FAIL", "evidence": evidence or {}, "problems": problems}


def check_from_problems(check_id: str, label: str, problems: list[str], evidence: dict[str, Any]) -> dict[str, Any]:
    return fail_check(check_id, label, problems, evidence) if problems else pass_check(check_id, label, evidence)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def collect_html_ids(index_html: Path) -> set[str]:
    parser = IdCollector()
    parser.feed(read_text(index_html))
    return parser.ids


def collect_html_button_ids(index_html: Path) -> set[str]:
    parser = ButtonIdCollector()
    parser.feed(read_text(index_html))
    return parser.button_ids


def load_companion_module(root: Path, workspace_home: Path):
    old_home = os.environ.get("CODEX_MN_COMPANION_HOME")
    os.environ["CODEX_MN_COMPANION_HOME"] = str(workspace_home)
    try:
        spec = importlib.util.spec_from_file_location("codex_mn_companion_ui_acceptance", root / "companion.py")
        if not spec or not spec.loader:
            raise RuntimeError("cannot load companion.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old_home is None:
            os.environ.pop("CODEX_MN_COMPANION_HOME", None)
        else:
            os.environ["CODEX_MN_COMPANION_HOME"] = old_home


def default_document_payload(topicid: str, bookmd5: str, document_title: str) -> dict[str, Any]:
    return {
        "action": "notebook_workspace",
        "topicid": topicid,
        "bookmd5": bookmd5,
        "docmd5": bookmd5,
        "documentTitle": document_title,
        "mnObject": {
            "objectId": f"mnobj:doc:{bookmd5 or 'arbitrary'}",
            "kind": "document",
            "title": document_title,
            "sourceRef": {
                "documentTitle": document_title,
                "bookmd5": bookmd5,
                "topicid": topicid,
            },
        },
    }


def check_static_controls(root: Path) -> dict[str, Any]:
    index_html = root / "extension/codex.mn.assistant/web/index.html"
    ids = collect_html_ids(index_html)
    missing = [control_id for control_id in REQUIRED_CONTROL_IDS if control_id not in ids]
    return check_from_problems(
        "webview_static_controls",
        "WebView static controls",
        [f"missing control #{item}" for item in missing],
        {"controlCount": len(ids), "missing": missing},
    )


def check_behavior_markers(root: Path) -> dict[str, Any]:
    app_js = read_text(root / "extension/codex.mn.assistant/web/app.js")
    app_css = read_text(root / "extension/codex.mn.assistant/web/app.css")
    missing = [marker for marker in REQUIRED_JS_MARKERS if marker not in app_js]
    css_markers = [
        ".notebook-runbook",
        ".notebook-knowledge-matrix",
        ".notebook-object-intake",
        ".notebook-object-task-composer",
        ".workflow-builder-board",
    ]
    missing.extend([marker for marker in css_markers if marker not in app_css])
    return check_from_problems(
        "webview_behavior_markers",
        "WebView behavior markers",
        [f"missing marker {item}" for item in missing],
        {"markerCount": len(REQUIRED_JS_MARKERS) + len(css_markers), "missing": missing},
    )


def check_button_coverage(root: Path) -> dict[str, Any]:
    index_html = root / "extension/codex.mn.assistant/web/index.html"
    button_ids = collect_html_button_ids(index_html)
    categories: dict[str, list[str]] = {
        "actualBrowserButtons": sorted(set(BROWSER_ACTION_REQUIRED_BUTTONS)),
        "interactionButtons": sorted(set(BUTTON_COVERAGE_INTERACTION_BUTTONS)),
        "writeButtons": sorted(set(BUTTON_COVERAGE_WRITE_BUTTONS)),
        "panelControlButtons": sorted(set(BUTTON_COVERAGE_PANEL_CONTROL_BUTTONS)),
        "dynamicButtons": sorted(set(BUTTON_COVERAGE_DYNAMIC_BUTTONS)),
        "formOrDestructiveButtons": sorted(set(BUTTON_COVERAGE_FORM_OR_DESTRUCTIVE_BUTTONS)),
        "filePickerButtons": sorted(set(BUTTON_COVERAGE_FILE_PICKER_BUTTONS)),
        "closeOnlyButtons": sorted(set(BUTTON_COVERAGE_CLOSE_ONLY_BUTTONS)),
        "hiddenRuntimeButtons": sorted(set(BUTTON_COVERAGE_HIDDEN_RUNTIME_BUTTONS)),
    }
    classified: set[str] = set()
    for values in categories.values():
        classified.update(values)
    unclassified = sorted(button_ids - classified)
    stale_classified = sorted(classified - button_ids - {"replyMindmapTreeButton", "aiEditRejectButton", "aiEditAcceptButton", "aiEditReviewQueueButton", "transactionVerifyButton", "transactionEvidenceButton", "transactionProbeButton"})
    problems = [f"unclassified button #{item}" for item in unclassified]
    if stale_classified:
        problems.append("button coverage lists reference missing static buttons: " + ", ".join(stale_classified))
    return check_from_problems(
        "webview_button_coverage",
        "WebView button coverage",
        problems,
        {
            "buttonCount": len(button_ids),
            "unclassifiedButtons": unclassified,
            "staleClassifiedButtons": stale_classified,
            **categories,
        },
    )


def rendered_tag_for_id(dom: str, element_id: str) -> str:
    match = re.search(r"<[^>]*\bid=[\"']" + re.escape(element_id) + r"[\"'][^>]*>", dom)
    return match.group(0) if match else ""


def check_browser_render_output(dom: str, *, timed_out: bool, return_code: int | None) -> dict[str, Any]:
    missing = [marker for marker in BROWSER_RENDER_MARKERS if marker not in dom]
    problems = [f"missing rendered marker {marker}" for marker in missing]
    disabled: dict[str, bool] = {}
    for element_id in BROWSER_NATIVE_DISABLED_IDS:
        tag = rendered_tag_for_id(dom, element_id)
        is_disabled = bool(tag and re.search(r"\sdisabled(?:[=\s>]|$)", tag))
        disabled[element_id] = is_disabled
        if not is_disabled:
            problems.append(f"rendered native action #{element_id} is not disabled without topicid")
    if not dom.strip():
        problems.append("browser produced no rendered DOM")
    if return_code not in (0, None) and missing:
        problems.append(f"browser exited {return_code} before rendering required controls")
    return check_from_problems(
        "webview_browser_render",
        "WebView browser render",
        problems,
        {
            "domLength": len(dom),
            "timedOut": timed_out,
            "returnCode": return_code,
            "missing": missing,
            "disabled": disabled,
        },
    )


def check_browser_interaction_result(result: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    after_chat = result.get("afterChat") if isinstance(result.get("afterChat"), dict) else {}
    after_workspace = result.get("afterWorkspace") if isinstance(result.get("afterWorkspace"), dict) else {}
    mindmap = result.get("mindmapStudio") if isinstance(result.get("mindmapStudio"), dict) else {}
    card_factory = result.get("cardFactory") if isinstance(result.get("cardFactory"), dict) else {}
    workflow_builder = result.get("workflowBuilder") if isinstance(result.get("workflowBuilder"), dict) else {}
    workspace_surfaces = result.get("workspaceSurfaces") if isinstance(result.get("workspaceSurfaces"), dict) else {}
    workspace_select_surfaces = (
        result.get("workspaceSelectSurfaces") if isinstance(result.get("workspaceSelectSurfaces"), dict) else {}
    )
    workbench_tabs = result.get("workbenchTabs") if isinstance(result.get("workbenchTabs"), dict) else {}
    command_pane = result.get("commandPane") if isinstance(result.get("commandPane"), dict) else {}
    console_layout = result.get("consoleLayout") if isinstance(result.get("consoleLayout"), dict) else {}
    settings = result.get("settings") if isinstance(result.get("settings"), dict) else {}
    history = result.get("history") if isinstance(result.get("history"), dict) else {}
    select_focus = (
        result.get("workspaceSurfaceSelectFocus")
        if isinstance(result.get("workspaceSurfaceSelectFocus"), dict)
        else {}
    )

    if result.get("initialMode") != BROWSER_INTERACTION_EXPECTED["initialMode"]:
        problems.append(f"initial product mode is not chat: {result.get('initialMode')}")
    if after_chat.get("mode") != BROWSER_INTERACTION_EXPECTED["chatMode"]:
        problems.append("chat mode click did not switch product mode")
    if after_chat.get("chatSelected") is not True:
        problems.append("chat mode button is not selected after click")
    if after_chat.get("workspaceNavigatorVisible") is not False:
        problems.append("workspace navigator remains visible in chat mode")
    chat_layout = after_chat.get("layout") if isinstance(after_chat.get("layout"), dict) else {}
    if chat_layout.get("commandPaneVisible") is not True or chat_layout.get("bodyVisible") is not True:
        problems.append("chat mode command pane did not render as the primary surface")
    if chat_layout.get("historyVisible") is not True or int(chat_layout.get("historyHeight") or 0) < 220:
        problems.append(f"chat history did not fill available height: {chat_layout}")
    if chat_layout.get("historyFillsBody") is not True:
        problems.append(f"chat history did not fill command pane body: {chat_layout}")
    if chat_layout.get("composerVisible") is not True or chat_layout.get("composerNearViewportBottom") is not True:
        problems.append(f"chat composer was not anchored near viewport bottom: {chat_layout}")
    if after_workspace.get("mode") != BROWSER_INTERACTION_EXPECTED["workspaceMode"]:
        problems.append("workspace mode click did not switch product mode back")
    if after_workspace.get("workspaceSelected") is not True:
        problems.append("workspace mode button is not selected after click")
    if after_workspace.get("workspaceNavigatorVisible") is not False:
        problems.append("workspace navigator should stay hidden in simple tool mode")
    if after_workspace.get("advancedToolCenterVisible") is not True:
        problems.append("simple tool center did not render in workspace mode")
    after_expert = result.get("afterExpertMode") if isinstance(result.get("afterExpertMode"), dict) else {}
    if after_expert.get("expertModeExpanded") != "true":
        problems.append(f"expert mode did not expand: {after_expert.get('expertModeExpanded')}")
    if after_expert.get("workspaceNavigatorVisible") is not True:
        problems.append("workspace navigator is not visible after opening expert mode")
    if after_expert.get("expertBackVisible") is not True:
        problems.append("expert mode return button is not visible after opening expert mode")
    if console_layout.get("knowledgeConsoleVisible") is not True:
        problems.append("console workspace did not render Knowledge Console")
    if int(console_layout.get("panelHeight") or 0) < 210:
        problems.append(f"console workspace panel is too short for practical use: {console_layout}")
    if console_layout.get("fillsAboveCommand") is not True or int(console_layout.get("blankGapAboveCommand") or 0) > 32:
        problems.append(f"console workspace leaves a blank gap above Command Pane: {console_layout}")
    if int(console_layout.get("trailingBlankAboveCommand") or 0) > 80:
        problems.append(f"console workspace has excessive trailing blank space: {console_layout}")
    if console_layout.get("detailsNestedScrollTrap") is True:
        problems.append(f"notebook details became a nested scroll trap: {console_layout}")
    responsive_layout = result.get("responsiveLayout") if isinstance(result.get("responsiveLayout"), dict) else {}
    if int(responsive_layout.get("badCount") or 0) > 0:
        problems.append(f"workspace narrow layout text overflow: {responsive_layout}")
    if int(responsive_layout.get("buttonIssueCount") or 0) > 0:
        problems.append(f"workspace narrow button layout issue: {responsive_layout}")
    if int(responsive_layout.get("cardIssueCount") or 0) > 0:
        problems.append(f"workspace narrow card layout issue: {responsive_layout}")
    medium_layout = result.get("mediumLayout") if isinstance(result.get("mediumLayout"), dict) else {}
    if int(medium_layout.get("badCount") or 0) > 0:
        problems.append(f"workspace medium layout text overflow: {medium_layout}")
    if int(medium_layout.get("buttonIssueCount") or 0) > 0:
        problems.append(f"workspace medium button layout issue: {medium_layout}")
    if int(medium_layout.get("cardIssueCount") or 0) > 0:
        problems.append(f"workspace medium card layout issue: {medium_layout}")
    wide_layout = result.get("wideLayout") if isinstance(result.get("wideLayout"), dict) else {}
    if int(wide_layout.get("buttonIssueCount") or 0) > 0:
        problems.append(f"workspace wide button layout issue: {wide_layout}")
    if int(wide_layout.get("cardIssueCount") or 0) > 0:
        problems.append(f"workspace wide card layout issue: {wide_layout}")
    if select_focus.get("exists") is not True:
        problems.append("workspace surface select focus probe did not find the select")
    if select_focus.get("focusedBeforeMousedown") is not True:
        problems.append("workspace surface select did not accept focus before mousedown probe")
    if select_focus.get("blurredOnFocusedMousedown") is not True:
        problems.append("workspace surface select kept focus on focused mousedown")
    if select_focus.get("activeSurfaceAfterChange") != BROWSER_INTERACTION_EXPECTED["mindmapSurface"]:
        problems.append(
            "workspace surface select change did not switch to mindmap surface: "
            f"{select_focus.get('activeSurfaceAfterChange')}"
        )
    if select_focus.get("blurredAfterChange") is not True:
        problems.append("workspace surface select kept focus after change")
    if mindmap.get("activeSurface") != BROWSER_INTERACTION_EXPECTED["mindmapSurface"]:
        problems.append(f"mindmap nav did not select mindmap surface: {mindmap.get('activeSurface')}")
    if mindmap.get("activePane") != BROWSER_INTERACTION_EXPECTED["mindmapPane"]:
        problems.append(f"mindmap nav did not activate operation pane: {mindmap.get('activePane')}")
    if card_factory.get("activeSurface") != BROWSER_INTERACTION_EXPECTED["cardSurface"]:
        problems.append(f"card factory nav did not select card factory surface: {card_factory.get('activeSurface')}")
    if card_factory.get("activePane") != BROWSER_INTERACTION_EXPECTED["cardPane"]:
        problems.append(f"card factory nav did not activate knowledge pane: {card_factory.get('activePane')}")
    if workflow_builder.get("activeSurface") != BROWSER_INTERACTION_EXPECTED["workflowSurface"]:
        problems.append(f"workflow builder nav did not select workflow builder surface: {workflow_builder.get('activeSurface')}")
    if workflow_builder.get("activePane") != BROWSER_INTERACTION_EXPECTED["workflowPane"]:
        problems.append(f"workflow builder nav did not activate workflow pane: {workflow_builder.get('activePane')}")
    for button_id, (expected_surface, expected_pane) in BROWSER_INTERACTION_EXPECTED_SURFACES.items():
        item = workspace_surfaces.get(button_id) if isinstance(workspace_surfaces.get(button_id), dict) else {}
        if item.get("activeSurface") != expected_surface:
            problems.append(f"workspace nav did not select {expected_surface}: {button_id} -> {item.get('activeSurface')}")
        if item.get("activePane") != expected_pane:
            problems.append(f"workspace nav did not activate {expected_pane}: {button_id} -> {item.get('activePane')}")
        layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
        visible = layout.get("visible") if isinstance(layout.get("visible"), dict) else {}
        if layout.get("shellSurface") != expected_surface:
            problems.append(
                f"workspace surface layout did not stamp shell surface {expected_surface}: "
                f"{button_id} -> {layout.get('shellSurface')}"
            )
        expected_layout = BROWSER_INTERACTION_EXPECTED_LAYOUT.get(button_id, {})
        for element_id in expected_layout.get("visible", []):
            if visible.get(element_id) is not True:
                problems.append(f"workspace surface layout should show #{element_id} on {expected_surface}")
        for element_id in expected_layout.get("hidden", []):
            if visible.get(element_id) is not False:
                problems.append(f"workspace surface layout should hide #{element_id} on {expected_surface}")
    for surface, expected_layout in BROWSER_INTERACTION_EXPECTED_SELECT_SURFACES.items():
        item = workspace_select_surfaces.get(surface) if isinstance(workspace_select_surfaces.get(surface), dict) else {}
        if item.get("activeSurface") != surface:
            problems.append(f"workspace select did not select {surface}: {item.get('activeSurface')}")
        if item.get("activePane") != expected_layout.get("pane"):
            problems.append(f"workspace select did not activate {expected_layout.get('pane')} for {surface}: {item.get('activePane')}")
        layout = item.get("layout") if isinstance(item.get("layout"), dict) else {}
        visible = layout.get("visible") if isinstance(layout.get("visible"), dict) else {}
        if layout.get("shellSurface") != surface:
            problems.append(f"workspace select layout did not stamp shell surface {surface}: {layout.get('shellSurface')}")
        for element_id in expected_layout.get("visible", []):
            if visible.get(element_id) is not True:
                problems.append(f"workspace select surface layout should show #{element_id} on {surface}")
        for element_id in expected_layout.get("hidden", []):
            if visible.get(element_id) is not False:
                problems.append(f"workspace select surface layout should hide #{element_id} on {surface}")
    for button_id, expected_pane in BROWSER_INTERACTION_EXPECTED_TABS.items():
        item = workbench_tabs.get(button_id) if isinstance(workbench_tabs.get(button_id), dict) else {}
        if item.get("activePane") != expected_pane:
            problems.append(f"workbench tab did not activate {expected_pane}: {button_id} -> {item.get('activePane')}")
    if command_pane.get("expandedAfterToggle") != "true":
        problems.append(f"command pane toggle did not expand pane: {command_pane.get('expandedAfterToggle')}")
    if command_pane.get("navigatorExpandedAfterToggle") != "false":
        problems.append(
            "command pane expansion did not auto-collapse Workspace Navigator: "
            f"{command_pane.get('navigatorExpandedAfterToggle')}"
        )
    if command_pane.get("navigatorVisibleAfterToggle") is not False:
        problems.append("Workspace Navigator remained visible while Command Pane was expanded")
    if int(command_pane.get("panelHeightAfterToggle") or 0) < 320:
        problems.append(f"expanded Command Pane is too short: {command_pane}")
    if int(command_pane.get("bodyHeightAfterToggle") or 0) < 140:
        problems.append(f"expanded Command Pane body is too short: {command_pane}")
    if int(command_pane.get("historyHeightAfterToggle") or 0) < 110:
        problems.append(f"expanded conversation history is too short: {command_pane}")
    workspace_details = result.get("notebookWorkspaceDetails") if isinstance(result.get("notebookWorkspaceDetails"), dict) else {}
    if workspace_details.get("expandedAfterToggle") != "true":
        problems.append(
            f"notebook workspace details toggle did not expand details: "
            f"{workspace_details.get('expandedAfterToggle')}"
        )
    if workspace_details.get("detailsVisibleAfterToggle") is not True:
        problems.append("notebook workspace details drawer was not visible after expansion")
    if int(workspace_details.get("detailsHeightAfterToggle") or 0) <= 0:
        problems.append("notebook workspace details drawer had no measured height after expansion")
    header_spacing = result.get("notebookHeaderSpacing") if isinstance(result.get("notebookHeaderSpacing"), dict) else {}
    if int(header_spacing.get("topGapDelta") or 0) > 4 or int(header_spacing.get("rightGapDelta") or 0) > 4:
        problems.append(f"notebook workspace header spacing changed after expand: {header_spacing}")
    wide_header_spacing = result.get("wideHeaderSpacing") if isinstance(result.get("wideHeaderSpacing"), dict) else {}
    if int(wide_header_spacing.get("topGapDelta") or 0) > 4 or int(wide_header_spacing.get("rightGapDelta") or 0) > 4:
        problems.append(f"notebook workspace wide header spacing changed after expand: {wide_header_spacing}")
    composer = result.get("composerVisibility") if isinstance(result.get("composerVisibility"), dict) else {}
    if composer.get("sendButtonVisibleInStress") is not True:
        problems.append("send button was not visible in the small-window expanded workspace stress case")
    if composer.get("sendButtonWithinViewportInStress") is not True:
        problems.append(
            "send button was outside the viewport in the small-window expanded workspace stress case: "
            f"{composer.get('sendButtonRect')}"
        )
    if composer.get("composerWithinViewportInStress") is not True:
        problems.append(
            "command composer was outside the viewport in the small-window expanded workspace stress case: "
            f"{composer.get('composerRect')}"
        )
    scroll = result.get("workbenchScroll") if isinstance(result.get("workbenchScroll"), dict) else {}
    for key, panel_id in {
        "operation": "operationWorkspacePanel",
        "knowledge": "knowledgeWorkspacePanel",
        "workflow": "workflowWorkspacePanel",
    }.items():
        probe = scroll.get(key) if isinstance(scroll.get(key), dict) else {}
        if probe.get("exists") is not True:
            problems.append(f"{panel_id} scroll container was missing")
            continue
        if probe.get("visible") is not True:
            problems.append(f"{panel_id} was not visible during scroll probe")
        if str(probe.get("overflowY") or "") not in {"auto", "scroll", "overlay"}:
            problems.append(f"{panel_id} is not user-scrollable: overflow-y={probe.get('overflowY')}")
        if int(probe.get("clientHeight") or 0) <= 0:
            problems.append(f"{panel_id} had no usable height for scrolling")
        if int(probe.get("clientHeight") or 0) < 120:
            problems.append(f"{panel_id} scroll area is too short for practical use: {probe.get('clientHeight')}px")
        clearance = probe.get("viewportClearance") if isinstance(probe.get("viewportClearance"), dict) else {}
        if int(clearance.get("topAfterTabs") or 0) < 8:
            problems.append(f"{panel_id} top is too close to workbench tabs: {clearance.get('topAfterTabs')}px")
        boundary = probe.get("contentBoundary") if isinstance(probe.get("contentBoundary"), dict) else {}
        if boundary.get("firstFullyBelowHeader") is not True:
            problems.append(
                f"{panel_id} top content is clipped by sticky header: "
                f"{boundary.get('firstId')} top={boundary.get('firstTop')} limit={boundary.get('topVisibleLimit')}"
            )
        if boundary.get("lastFullyAboveCommandPane") is not True:
            problems.append(
                f"{panel_id} bottom content cannot scroll above Command Pane: "
                f"{boundary.get('lastId')} bottom={boundary.get('lastBottom')} limit={boundary.get('bottomVisibleLimit')}"
            )
    navigator = result.get("workspaceNavigator") if isinstance(result.get("workspaceNavigator"), dict) else {}
    if navigator.get("toggleVisible") is not False:
        problems.append("workspace navigator expand button should be hidden when select navigation is primary")
    if navigator.get("gridVisible") is not False:
        problems.append("workspace navigator card grid should stay hidden when select navigation is primary")
    if navigator.get("expandedState") != "false":
        problems.append(f"workspace navigator expanded state should remain collapsed: {navigator.get('expandedState')}")
    if navigator.get("expandedAfterSurfaceSelection") != "false":
        problems.append(
            "workspace navigator should stay collapsed after selecting a workspace surface: "
            f"{navigator.get('expandedAfterSurfaceSelection')}"
        )
    if settings.get("opened") is not True or settings.get("closed") is not True:
        problems.append("settings page did not open and close through buttons")
    if settings.get("contextScopeAutoPressed") is not True:
        problems.append("context scope auto button was not selected in settings")
    if history.get("opened") is not True or history.get("closed") is not True:
        problems.append("conversation history page did not open and close through buttons")
    for label, page_id, data in [
        ("settings", "configPage", settings.get("layout") if isinstance(settings.get("layout"), dict) else {}),
        ("history", "conversationHistoryPage", history.get("layout") if isinstance(history.get("layout"), dict) else {}),
    ]:
        if data.get("exists") is not True:
            problems.append(f"{label} page layout probe did not find {page_id}")
            continue
        if data.get("visible") is not True:
            problems.append(f"{label} page was not visible during layout probe")
        if data.get("headerVisible") is not True:
            problems.append(f"{label} page header was not visible")
        if data.get("returnButtonVisible") is not True:
            problems.append(f"{label} page return button was not visible")
        if data.get("returnButtonWithinViewport") is not True:
            problems.append(f"{label} page return button was outside viewport: {data.get('pageRect')}")
        if str(data.get("bodyOverflowY") or "") not in {"auto", "scroll", "overlay"}:
            problems.append(f"{label} page body is not scrollable: overflow-y={data.get('bodyOverflowY')}")
        if int(data.get("bodyClientHeight") or 0) < 120:
            problems.append(f"{label} page body is too short for practical use: {data.get('bodyClientHeight')}px")
        top_boundary = data.get("topBoundary") if isinstance(data.get("topBoundary"), dict) else {}
        if top_boundary.get("firstVisibleAtTop") is not True:
            problems.append(
                f"{label} page top content is clipped: "
                f"{top_boundary.get('firstId')} top={top_boundary.get('firstTop')} bodyTop={top_boundary.get('bodyTop')}"
            )
        boundary = data.get("lastBoundary") if isinstance(data.get("lastBoundary"), dict) else {}
        if boundary.get("lastVisibleAtBottom") is not True:
            problems.append(
                f"{label} page bottom content is clipped: "
                f"{boundary.get('lastId')} bottom={boundary.get('lastBottom')} bodyBottom={boundary.get('bodyBottom')}"
            )
    matrix = result.get("knowledgeMatrix") if isinstance(result.get("knowledgeMatrix"), dict) else {}
    matrix_toggle_disabled = matrix.get("toggleDisabled") is True
    if matrix.get("expandedAfterToggle") != "true" and not matrix_toggle_disabled:
        problems.append(f"knowledge matrix toggle did not expand details: {matrix.get('expandedAfterToggle')}")

    return check_from_problems(
        "webview_browser_interaction",
        "WebView browser interaction",
        problems,
        {"result": result},
    )


def check_browser_action_stub_result(result: dict[str, Any]) -> dict[str, Any]:
    clicked = result.get("clicked") if isinstance(result.get("clicked"), dict) else {}
    actions = result.get("actions") if isinstance(result.get("actions"), list) else []
    bridge_actions = result.get("bridgeActions") if isinstance(result.get("bridgeActions"), list) else []
    button_action_deltas = result.get("buttonActionDeltas") if isinstance(result.get("buttonActionDeltas"), dict) else {}
    final_ui = result.get("finalUiState") if isinstance(result.get("finalUiState"), dict) else {}
    action_set = {str(item) for item in actions}
    bridge_action_set = {str(item) for item in bridge_actions}
    problems: list[str] = []
    for button_id in BROWSER_ACTION_REQUIRED_BUTTONS:
        if clicked.get(button_id) is not True:
            problems.append(f"button was not clicked: {button_id}")
    for action in BROWSER_ACTION_REQUIRED_ACTIONS:
        if action not in action_set:
            problems.append(f"missing backend action: {action}")
    for button_id, action in BROWSER_ACTION_BUTTON_ACTIONS.items():
        delta = int(button_action_deltas.get(button_id) or 0)
        if delta < 1:
            problems.append(f"button did not trigger expected backend action: {button_id} -> {action}")
    for action in BROWSER_ACTION_REQUIRED_BRIDGE_ACTIONS:
        if action not in bridge_action_set:
            problems.append(f"missing native bridge action: {action}")
    if result.get("connectionFailureVisible") is True:
        problems.append("connection failure message appeared while using stub backend")
    if int(result.get("requestCount") or len(actions)) < len(BROWSER_ACTION_REQUIRED_ACTIONS):
        problems.append(f"too few companion requests: {result.get('requestCount')}")
    if result.get("promptClearedAfterSend") is not True:
        problems.append("prompt input did not clear after send")
    if result.get("enterSubmitted") is not True:
        problems.append("Enter key did not submit chat")
    if result.get("contextScopeAfterClicks") != "document":
        problems.append(f"context scope did not switch to document: {result.get('contextScopeAfterClicks')}")
    if result.get("relationEditorOpened") is not True:
        problems.append("object relation editor did not open")
    if result.get("relationEditorClosedAfterCancel") is not True:
        problems.append("object relation editor did not close after cancel")
    ui_line = str(result.get("uiFunctionalLineText") or "")
    ui_detail = str(result.get("uiFunctionalDetailText") or "")
    if "PASS" not in ui_line or "11/11" not in ui_line:
        problems.append(f"UI functional acceptance result was not rendered as PASS: {ui_line}")
    if "webview_browser_actions" not in ui_detail:
        problems.append("UI functional acceptance detail did not render checks")
    if "真实 MN4 运行态验收" not in ui_detail:
        problems.append("real MN4 runtime boundary was not rendered")
    if "MN native API matrix" not in ui_detail or "下一步：" not in ui_detail:
        problems.append("real MN4 runtime blockers were not rendered")
    if "推荐修复：" not in ui_detail:
        problems.append("real MN4 recommended repairs were not rendered")
    safe_evidence_id = "realMnRuntimeSafeEvidenceButton"
    if clicked.get(safe_evidence_id) is not True:
        problems.append("real MN4 safe evidence button was not clicked")
    if int(button_action_deltas.get(safe_evidence_id) or 0) < 1:
        problems.append("real MN4 safe evidence button did not trigger native capability probe")
    repair_id = "realMnRepair-refresh_native_capabilities"
    if clicked.get(repair_id) is not True:
        problems.append("real MN4 recommended repair button was not clicked")
    if int(button_action_deltas.get(repair_id) or 0) < 1:
        problems.append("real MN4 recommended repair did not trigger native capability probe")
    highlight_repair_id = "realMnRepair-run_native_highlight_wizard"
    if clicked.get(highlight_repair_id) is not True:
        problems.append("real MN4 highlight repair button was not clicked")
    if int(button_action_deltas.get(highlight_repair_id) or 0) < 1:
        problems.append("real MN4 highlight repair did not start highlight wizard")
    if not final_ui:
        problems.append("final UI state was not captured after action sweep")
    if final_ui.get("settingsHidden") is not True:
        problems.append("settings page remained open after action sweep")
    if final_ui.get("historyHidden") is not True:
        problems.append("history page remained open after action sweep")
    if final_ui.get("activeProductMode") != "workspace":
        problems.append(f"product mode was not workspace after action sweep: {final_ui.get('activeProductMode')}")
    if final_ui.get("commandPaneVisible") is not True:
        problems.append("command pane was not visible after action sweep")
    if final_ui.get("composerVisible") is not True or final_ui.get("composerWithinViewport") is not True:
        problems.append(f"command composer was not usable after action sweep: {final_ui}")
    if final_ui.get("sendButtonVisible") is not True or final_ui.get("sendButtonWithinViewport") is not True:
        problems.append(f"send button was not usable after action sweep: {final_ui}")
    if final_ui.get("promptUsable") is not True:
        problems.append("prompt input was not usable after action sweep")
    if final_ui.get("activeElementRepeatBlocking") is True:
        problems.append(f"focus remained on a repeat-blocking control: {final_ui.get('activeElementId')}")
    return check_from_problems(
        "webview_browser_actions",
        "WebView browser actions",
        problems,
        {"result": result},
    )


def check_browser_write_action_stub_result(result: dict[str, Any]) -> dict[str, Any]:
    clicked = result.get("clicked") if isinstance(result.get("clicked"), dict) else {}
    actions = result.get("actions") if isinstance(result.get("actions"), list) else []
    bridge_actions = result.get("bridgeActions") if isinstance(result.get("bridgeActions"), list) else []
    final_ui = result.get("finalUiState") if isinstance(result.get("finalUiState"), dict) else {}
    action_set = {str(item) for item in actions}
    bridge_action_set = {str(item) for item in bridge_actions}
    problems: list[str] = []
    for target in BROWSER_WRITE_REQUIRED_CLICK_TARGETS:
        if clicked.get(target) is not True:
            problems.append(f"write target was not clicked: {target}")
    for action in BROWSER_WRITE_REQUIRED_COMPANION_ACTIONS:
        if action not in action_set:
            problems.append(f"missing write backend action: {action}")
    for action in BROWSER_WRITE_REQUIRED_BRIDGE_ACTIONS:
        if action not in bridge_action_set:
            problems.append(f"missing native bridge action: {action}")
    if result.get("connectionFailureVisible") is True:
        problems.append("connection failure message appeared while using write stub backend")
    if not final_ui:
        problems.append("final UI state was not captured after write action sweep")
    if final_ui.get("settingsHidden") is not True:
        problems.append("settings page remained open after write action sweep")
    if final_ui.get("historyHidden") is not True:
        problems.append("history page remained open after write action sweep")
    if final_ui.get("activeProductMode") != "workspace":
        problems.append(f"product mode was not workspace after write action sweep: {final_ui.get('activeProductMode')}")
    if final_ui.get("commandPaneVisible") is not True:
        problems.append("command pane was not visible after write action sweep")
    if final_ui.get("composerVisible") is not True or final_ui.get("composerWithinViewport") is not True:
        problems.append(f"command composer was not usable after write action sweep: {final_ui}")
    if final_ui.get("sendButtonVisible") is not True or final_ui.get("sendButtonWithinViewport") is not True:
        problems.append(f"send button was not usable after write action sweep: {final_ui}")
    if final_ui.get("promptUsable") is not True:
        problems.append("prompt input was not usable after write action sweep")
    if final_ui.get("activeElementRepeatBlocking") is True:
        problems.append(f"focus remained on a repeat-blocking write control: {final_ui.get('activeElementId')}")
    return check_from_problems(
        "webview_browser_write_actions",
        "WebView browser write actions",
        problems,
        {"result": result},
    )


def find_browser_executable(explicit_path: str = "") -> str:
    if explicit_path and Path(explicit_path).exists():
        return explicit_path
    for candidate in BROWSER_CANDIDATE_PATHS:
        if Path(candidate).exists():
            return candidate
    return ""


def free_local_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def wait_for_static_server(port: int, timeout_seconds: float = 3.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.25):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"static server did not start on 127.0.0.1:{port}")


def read_http_json(url: str, timeout_seconds: float = 5.0) -> Any:
    with urllib.request.urlopen(url, timeout=timeout_seconds) as response:
        return json.loads(response.read().decode("utf-8"))


def wait_for_devtools_page_ws(port: int, timeout_seconds: float = 6.0) -> str:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            targets = read_http_json(f"http://127.0.0.1:{port}/json/list", timeout_seconds=0.5)
            if isinstance(targets, list):
                for target in targets:
                    if isinstance(target, dict) and target.get("type") == "page" and target.get("webSocketDebuggerUrl"):
                        return str(target["webSocketDebuggerUrl"])
        except Exception as exc:
            last_error = str(exc)
        time.sleep(0.05)
    raise RuntimeError(f"DevTools page websocket not available on port {port}: {last_error}")


def websocket_read_exact(sock: socket.socket, size: int) -> bytes:
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("websocket connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def websocket_send_frame(sock: socket.socket, opcode: int, payload: bytes) -> None:
    first = 0x80 | (opcode & 0x0F)
    length = len(payload)
    mask_bit = 0x80
    if length < 126:
        header = bytes([first, mask_bit | length])
    elif length < 65536:
        header = bytes([first, mask_bit | 126]) + struct.pack("!H", length)
    else:
        header = bytes([first, mask_bit | 127]) + struct.pack("!Q", length)
    mask = os.urandom(4)
    masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
    sock.sendall(header + mask + masked)


def websocket_receive_text(sock: socket.socket) -> str:
    while True:
        first, second = websocket_read_exact(sock, 2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", websocket_read_exact(sock, 2))[0]
        elif length == 127:
            length = struct.unpack("!Q", websocket_read_exact(sock, 8))[0]
        mask = websocket_read_exact(sock, 4) if masked else b""
        payload = websocket_read_exact(sock, length) if length else b""
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        if opcode == 0x1:
            return payload.decode("utf-8", errors="replace")
        if opcode == 0x8:
            raise RuntimeError("websocket closed by peer")
        if opcode == 0x9:
            websocket_send_frame(sock, 0xA, payload)


class DevToolsSession:
    def __init__(self, websocket_url: str, timeout_seconds: float = 8.0) -> None:
        self.websocket_url = websocket_url
        self.timeout_seconds = timeout_seconds
        self.next_id = 0
        self.sock = self._connect(websocket_url)

    def _connect(self, websocket_url: str) -> socket.socket:
        parsed = urllib.parse.urlparse(websocket_url)
        host = parsed.hostname or "127.0.0.1"
        port = int(parsed.port or 80)
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        sock = socket.create_connection((host, port), timeout=self.timeout_seconds)
        sock.settimeout(self.timeout_seconds)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(4096)
            if not chunk:
                raise RuntimeError("websocket handshake closed")
            response += chunk
        if b" 101 " not in response.split(b"\r\n", 1)[0]:
            raise RuntimeError(response.decode("utf-8", errors="replace").splitlines()[0])
        expected_accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()).decode("ascii")
        if expected_accept not in response.decode("utf-8", errors="replace"):
            raise RuntimeError("websocket accept hash mismatch")
        return sock

    def close(self) -> None:
        try:
            websocket_send_frame(self.sock, 0x8, b"")
        except Exception:
            pass
        self.sock.close()

    def command(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.next_id += 1
        ident = self.next_id
        websocket_send_frame(self.sock, 0x1, json.dumps({"id": ident, "method": method, "params": params or {}}).encode("utf-8"))
        deadline = time.time() + self.timeout_seconds
        while time.time() < deadline:
            message = json.loads(websocket_receive_text(self.sock))
            if message.get("id") != ident:
                continue
            if "error" in message:
                raise RuntimeError(str(message["error"]))
            return message
        raise RuntimeError(f"timed out waiting for CDP response: {method}")

    def evaluate(self, expression: str) -> Any:
        response = self.command(
            "Runtime.evaluate",
            {
                "expression": expression,
                "awaitPromise": True,
                "returnByValue": True,
            },
        )
        result = response.get("result") if isinstance(response.get("result"), dict) else {}
        if response.get("exceptionDetails"):
            raise RuntimeError(str(response["exceptionDetails"]))
        value = result.get("result") if isinstance(result.get("result"), dict) else {}
        return value.get("value")


def run_browser_render_check(root: Path, *, browser_path: str = "", timeout_seconds: float = 12.0) -> dict[str, Any]:
    browser = find_browser_executable(browser_path)
    if not browser:
        return fail_check(
            "webview_browser_render",
            "WebView browser render",
            ["no supported headless browser found"],
            {"candidatePaths": BROWSER_CANDIDATE_PATHS},
        )
    web_root = root / "extension/codex.mn.assistant/web"
    if not web_root.is_dir():
        return fail_check(
            "webview_browser_render",
            "WebView browser render",
            [f"missing web root: {web_root}"],
            {"webRoot": str(web_root)},
        )
    port = free_local_port()
    with tempfile.TemporaryDirectory() as profile:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
            cwd=str(web_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_for_static_server(port)
            command = [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                "--disable-background-networking",
                "--disable-component-update",
                f"--user-data-dir={profile}",
                "--dump-dom",
                f"http://127.0.0.1:{port}/index.html",
            ]
            proc = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            timed_out = False
            try:
                output, _ = proc.communicate(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                output, _ = proc.communicate()
            check = check_browser_render_output(output or "", timed_out=timed_out, return_code=proc.returncode)
            check["evidence"]["browser"] = browser
            check["evidence"]["url"] = f"http://127.0.0.1:{port}/index.html"
            return check
        except Exception as exc:
            return fail_check(
                "webview_browser_render",
                "WebView browser render",
                [str(exc)],
                {"browser": browser, "port": port},
            )
        finally:
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)


BROWSER_INTERACTION_SCRIPT = r"""
(async function() {
  const delay = () => new Promise(resolve => window.setTimeout(resolve, 80));
  const byId = id => document.getElementById(id);
  const shell = byId('aiChatShell');
  const visible = id => {
    const el = byId(id);
    if (!el) return false;
    const style = window.getComputedStyle(el);
    const hasBox = Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    return hasBox && !el.classList.contains('hidden') && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const activePane = () => {
    const panel = document.querySelector('.workbench-panel.active');
    return panel ? panel.getAttribute('data-workbench-pane') : '';
  };
  const activeSurface = () => {
    if (shell && shell.getAttribute('data-workspace-surface')) return shell.getAttribute('data-workspace-surface');
    const card = document.querySelector('.workspace-nav-card.active');
    return card ? card.getAttribute('data-workspace-surface') : '';
  };
  const click = async id => {
    const el = byId(id);
    if (!el) return false;
    el.click();
    await delay();
    return true;
  };
  const classHidden = id => {
    const el = byId(id);
    return !el || el.classList.contains('hidden');
  };
  const rectOf = id => {
    const el = byId(id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      top: Math.round(r.top),
      right: Math.round(r.right),
      bottom: Math.round(r.bottom),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height)
    };
  };
  const rectWithinViewport = rect => {
    if (!rect || rect.width <= 0 || rect.height <= 0) return false;
    return rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth;
  };
  const visibleNode = el => {
    if (!el) return false;
    const style = window.getComputedStyle(el);
    const rect = el.getBoundingClientRect();
    return style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      !el.classList.contains('hidden') &&
      rect.width > 0 &&
      rect.height > 0;
  };
  const responsiveOverflowProbe = () => {
    const selectors = [
      '.topbar',
      '.topbar-identity',
      '.topbar-actions',
      '.topbar-workspace-rail',
      '.mode-switch-bar',
      '.mode-switch-button',
      '.mode-intent-line',
      '.workspace-navigator',
      '.workspace-navigator-header',
      '.workspace-navigator-controls',
      '.workspace-surface-select',
      '.notebook-workspace-panel',
      '.notebook-workspace-header',
      '.notebook-workspace-header-actions',
      '.notebook-workspace-card',
      '.notebook-workspace-action',
      '.notebook-object-intake-route',
      '.notebook-object-task',
      '.notebook-object-task-action',
      '.notebook-source-item',
      '.notebook-source-action',
      '.notebook-study-program',
      '.notebook-study-gap',
      '.notebook-study-recommendation',
      '.notebook-runbook',
      '.notebook-runbook-header',
      '.notebook-runbook-header-actions',
      '.notebook-runbook-step',
      '.notebook-runbook-action',
      '.workbench-panel',
      '.object-browser-panel',
      '.object-graph-panel',
      '.object-activity-panel',
      '.operation-ledger-panel',
      '.operation-compiler-panel',
      '.operation-compiler-card',
      '.mindmap-studio-panel',
      '.mindmap-studio-summary',
      '.mindmap-studio-actions',
      '.mindmap-diff-workbench',
      '.mindmap-target-bar',
      '.verification-report-panel',
      '.real-mn-acceptance-panel',
      '.knowledge-workspace-panel',
      '.knowledge-workspace-card',
      '.workflow-workspace-panel',
      '.workflow-builder-board-panel',
      '.skill-center-panel'
    ];
    const seen = new Set();
    const badItems = [];
    const buttonIssues = [];
    const cardIssues = [];
    const buttonSelectors = [
      '.topbar-actions .small-button',
      '.topbar-actions .icon-button',
      '.workspace-surface-select',
      '.workspace-navigator-controls button',
      '.notebook-workspace-header-actions button',
      '.notebook-workspace-details-toggle',
      '.notebook-object-intake-action',
      '.notebook-object-task-action',
      '.notebook-knowledge-axis-action',
      '.notebook-source-action',
      '.notebook-study-recommendation',
      '.notebook-runbook-action',
      '.notebook-runbook-auto',
      '.notebook-runbook-continue',
      '.mindmap-studio-actions button',
      '.operation-compiler-actions button',
      '.operation-ledger-panel button',
      '.verification-report-panel button',
      '.real-mn-acceptance-panel button',
      '.object-browser-panel button',
      '.object-graph-panel button',
      '.object-activity-panel button',
      '.knowledge-workspace-panel button',
      '.workflow-workspace-panel button',
      '.workflow-builder-board-panel button',
      '.skill-center-panel button',
      '.workbench-panel button',
      '.command-pane-toggle',
      '.pdf-cache-action',
      '.send-button',
      'button',
      'select'
    ];
    const parentSelectors = [
      '.topbar',
      '.workspace-navigator-controls',
      '.notebook-workspace-header',
      '.notebook-object-intake-route',
      '.notebook-object-task',
      '.notebook-knowledge-axis',
      '.notebook-source-item',
      '.notebook-study-gap',
      '.notebook-runbook-step',
      '.notebook-runbook-header',
      '.mindmap-studio-panel',
      '.mindmap-studio-actions',
      '.operation-compiler-panel',
      '.operation-ledger-panel',
      '.verification-report-panel',
      '.real-mn-acceptance-panel',
      '.object-browser-panel',
      '.object-graph-panel',
      '.object-activity-panel',
      '.knowledge-workspace-panel',
      '.workflow-workspace-panel',
      '.workflow-builder-board-panel',
      '.skill-center-panel',
      '.workbench-panel',
      '.command-pane-header',
      '.pdf-cache-banner',
      '.composer-input-row'
    ].join(',');
    const issueKey = item => [
      item.type,
      item.selector,
      item.id || '',
      item.text || '',
      item.parent || ''
    ].join('|');
    const issueSeen = new Set();
    const addButtonIssue = item => {
      const key = issueKey(item);
      if (issueSeen.has(key)) return;
      issueSeen.add(key);
      buttonIssues.push(item);
    };
    const addCardIssue = item => {
      cardIssues.push(item);
    };
    selectors.forEach(selector => {
      document.querySelectorAll(selector).forEach((el, index) => {
        if (!visibleNode(el)) return;
        const key = selector + ':' + (el.id || index);
        if (seen.has(key)) return;
        seen.add(key);
        const style = window.getComputedStyle(el);
        if (["auto", "scroll", "overlay"].includes(style.overflowX)) return;
        const clientWidth = Math.round(el.clientWidth);
        const scrollWidth = Math.round(el.scrollWidth);
        if (scrollWidth > clientWidth + 3) {
          badItems.push({
            selector,
            id: el.id || '',
            className: String(el.className || ''),
            clientWidth,
            scrollWidth,
            text: (el.textContent || '').trim().slice(0, 80)
          });
        }
      });
    });
    buttonSelectors.forEach(selector => {
      document.querySelectorAll(selector).forEach((el, index) => {
        if (!visibleNode(el)) return;
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        const clientWidth = Math.round(el.clientWidth);
        const scrollWidth = Math.round(el.scrollWidth);
        const clientHeight = Math.round(el.clientHeight);
        const scrollHeight = Math.round(el.scrollHeight);
        const text = (el.textContent || el.getAttribute('aria-label') || '').trim();
        if (scrollWidth > clientWidth + 3 || scrollHeight > clientHeight + 3) {
          addButtonIssue({
            type: 'clipped',
            selector,
            id: el.id || '',
            className: String(el.className || ''),
            overflowX: style.overflowX,
            overflowY: style.overflowY,
            clientWidth,
            scrollWidth,
            clientHeight,
            scrollHeight,
            text: text.slice(0, 80),
            index
          });
        }
        const parent = el.closest(parentSelectors) || el.parentElement;
        if (parent) {
          const parentRect = parent.getBoundingClientRect();
          if (
            rect.left < parentRect.left - 2 ||
            rect.right > parentRect.right + 2 ||
            rect.top < parentRect.top - 2 ||
            rect.bottom > parentRect.bottom + 2
          ) {
            addButtonIssue({
              type: 'outside-parent',
              selector,
              id: el.id || '',
              className: String(el.className || ''),
              parent: parent.id ? ('#' + parent.id) : (parent.className ? ('.' + String(parent.className).trim().split(/\s+/).join('.')) : parent.tagName),
              rect: {
                left: Math.round(rect.left),
                right: Math.round(rect.right),
                top: Math.round(rect.top),
                bottom: Math.round(rect.bottom)
              },
              parentRect: {
                left: Math.round(parentRect.left),
                right: Math.round(parentRect.right),
                top: Math.round(parentRect.top),
                bottom: Math.round(parentRect.bottom)
              },
              text: text.slice(0, 80),
              index
            });
          }
        }
      });
    });
    [
      { name: 'topbarActions', selector: '.topbar-actions .small-button', checkWidth: true },
      { name: 'workspaceHeaderActions', selector: '.notebook-workspace-header-actions button', checkWidth: false },
      { name: 'runbookHeaderActions', selector: '.notebook-runbook-header-actions button', checkWidth: false }
    ].forEach(group => {
      const nodes = Array.from(document.querySelectorAll(group.selector)).filter(visibleNode);
      if (nodes.length < 2) return;
      const rects = nodes.map(el => el.getBoundingClientRect());
      const heights = rects.map(rect => Math.round(rect.height));
      const widths = rects.map(rect => Math.round(rect.width));
      if (Math.max(...heights) - Math.min(...heights) > 3) {
        addButtonIssue({
          type: 'inconsistent-height',
          selector: group.selector,
          group: group.name,
          heights,
          texts: nodes.map(el => (el.textContent || '').trim()).slice(0, 8)
        });
      }
      if (group.checkWidth && Math.max(...widths) - Math.min(...widths) > 8) {
        addButtonIssue({
          type: 'inconsistent-width',
          selector: group.selector,
          group: group.name,
          widths,
          texts: nodes.map(el => (el.textContent || '').trim()).slice(0, 8)
        });
      }
    });
    if (window.innerWidth >= 761) {
      [
        {
          name: 'notebookObjectIntakeRoutes',
          container: '.notebook-object-intake-routes',
          selector: '.notebook-object-intake-route'
        },
        {
          name: 'notebookObjectTaskList',
          container: '.notebook-object-task-list',
          selector: '.notebook-object-task'
        }
      ].forEach(group => {
        document.querySelectorAll(group.container).forEach(container => {
          const cards = Array.from(container.querySelectorAll(group.selector)).filter(card =>
            visibleNode(card) && !card.classList.contains('empty')
          );
          if (cards.length < 2) return;
          const heights = cards.map(card => Math.round(card.getBoundingClientRect().height));
          const maxHeight = Math.max(...heights);
          const minHeight = Math.min(...heights);
          if (maxHeight - minHeight > 4) {
            addCardIssue({
              type: 'inconsistent-card-height',
              selector: group.selector,
              group: group.name,
              heights,
              delta: maxHeight - minHeight,
              texts: cards.map(card => (card.textContent || '').trim().slice(0, 80)).slice(0, 8)
            });
          }
        });
      });
      document.querySelectorAll('.notebook-object-intake-route, .notebook-object-task').forEach((card, index) => {
        if (!visibleNode(card) || card.classList.contains('empty')) return;
        const actions = Array.from(card.querySelectorAll('.notebook-object-intake-action, .notebook-object-task-action')).filter(visibleNode);
        if (!actions.length) return;
        const cardRect = card.getBoundingClientRect();
        const actionRects = actions.map(action => action.getBoundingClientRect());
        const widestAction = Math.max(...actionRects.map(rect => rect.width));
        const lastActionBottom = Math.max(...actionRects.map(rect => rect.bottom));
        const bottomGap = Math.round(cardRect.bottom - lastActionBottom);
        const cardWidth = Math.round(cardRect.width);
        if (widestAction > Math.min(cardRect.width * 0.72, 420)) {
          addButtonIssue({
            type: 'wide-stretched-action',
            selector: card.classList.contains('notebook-object-task') ? '.notebook-object-task' : '.notebook-object-intake-route',
            className: String(card.className || ''),
            cardWidth,
            actionWidth: Math.round(widestAction),
            text: actions.map(action => (action.textContent || '').trim()).join(' / ').slice(0, 80),
            index
          });
        }
        if (bottomGap > 34) {
          addButtonIssue({
            type: 'excessive-bottom-gap',
            selector: card.classList.contains('notebook-object-task') ? '.notebook-object-task' : '.notebook-object-intake-route',
            className: String(card.className || ''),
            cardHeight: Math.round(cardRect.height),
            bottomGap,
            text: actions.map(action => (action.textContent || '').trim()).join(' / ').slice(0, 80),
            index
          });
        }
      });
    }
    return {
      viewportWidth: window.innerWidth,
      viewportHeight: window.innerHeight,
      badCount: badItems.length,
      badItems: badItems.slice(0, 12),
      buttonIssueCount: buttonIssues.length,
      buttonIssues: buttonIssues.slice(0, 16),
      cardIssueCount: cardIssues.length,
      cardIssues: cardIssues.slice(0, 12)
    };
  };
  const chatLayoutProbe = () => {
    const pane = byId('commandPanePanel');
    const body = byId('commandPaneBody');
    const history = byId('liveHistory');
    const composer = byId('commandPaneComposer');
    const paneRect = pane ? pane.getBoundingClientRect() : null;
    const bodyRect = body ? body.getBoundingClientRect() : null;
    const historyRect = history ? history.getBoundingClientRect() : null;
    const composerRect = composer ? composer.getBoundingClientRect() : null;
    const historyHeight = historyRect ? Math.round(historyRect.height) : 0;
    const bodyHeight = bodyRect ? Math.round(bodyRect.height) : 0;
    const composerBottomGap = composerRect ? Math.round(window.innerHeight - composerRect.bottom) : null;
    return {
      commandPaneVisible: visible('commandPanePanel'),
      bodyVisible: visible('commandPaneBody'),
      historyVisible: visible('liveHistory'),
      composerVisible: visible('commandPaneComposer'),
      paneHeight: paneRect ? Math.round(paneRect.height) : 0,
      bodyHeight,
      historyHeight,
      composerBottomGap,
      historyFillsBody: historyHeight >= Math.max(220, bodyHeight - 96),
      composerNearViewportBottom: composerBottomGap !== null && composerBottomGap <= 24
    };
  };
  const consoleLayoutProbe = () => {
    const panel = byId('knowledgeConsolePanel');
    const details = byId('notebookWorkspaceDetails');
    const command = byId('commandPanePanel');
    const panelRect = panel ? panel.getBoundingClientRect() : null;
    const detailsStyle = details ? window.getComputedStyle(details) : null;
    const detailsRect = details ? details.getBoundingClientRect() : null;
    const commandRect = command ? command.getBoundingClientRect() : null;
    const blankGapAboveCommand = panelRect && commandRect ? Math.max(0, Math.round(commandRect.top - panelRect.bottom)) : null;
    const detailsScrollHeight = details ? Math.round(details.scrollHeight) : 0;
    const detailsClientHeight = details ? Math.round(details.clientHeight) : 0;
    const detailsOverflowY = detailsStyle ? detailsStyle.overflowY : '';
    const originalScrollTop = panel ? panel.scrollTop : 0;
    let trailingBlankAboveCommand = null;
    let lastContentBottomAtBottom = null;
    if (panel && commandRect) {
      panel.scrollTop = panel.scrollHeight;
      const contentNodes = [
        byId('notebookWorkspaceDetails'),
        byId('notebookKnowledgeMatrix')
      ].filter(node => {
        if (!node) return false;
        const nodeStyle = window.getComputedStyle(node);
        const nodeRect = node.getBoundingClientRect();
        return nodeStyle.display !== 'none' &&
          nodeStyle.visibility !== 'hidden' &&
          !node.classList.contains('hidden') &&
          nodeRect.width > 0 &&
          nodeRect.height > 0;
      });
      if (contentNodes.length) {
        lastContentBottomAtBottom = Math.round(Math.max.apply(null, contentNodes.map(node => node.getBoundingClientRect().bottom)));
        trailingBlankAboveCommand = Math.max(0, Math.round(commandRect.top - lastContentBottomAtBottom));
      }
      panel.scrollTop = originalScrollTop;
    }
    return {
      mode: shell ? shell.getAttribute('data-product-mode') : '',
      surface: shell ? shell.getAttribute('data-workspace-surface') : '',
      knowledgeConsoleVisible: visible('knowledgeConsolePanel'),
      notebookWorkspaceVisible: visible('notebookWorkspacePanel'),
      commandPaneVisible: visible('commandPanePanel'),
      panelHeight: panelRect ? Math.round(panelRect.height) : 0,
      panelBottom: panelRect ? Math.round(panelRect.bottom) : null,
      commandTop: commandRect ? Math.round(commandRect.top) : null,
      blankGapAboveCommand,
      lastContentBottomAtBottom,
      trailingBlankAboveCommand,
      fillsAboveCommand: blankGapAboveCommand !== null && blankGapAboveCommand <= 32,
      detailsVisible: visible('notebookWorkspaceDetails'),
      detailsHeight: detailsRect ? Math.round(detailsRect.height) : 0,
      detailsOverflowY,
      detailsScrollHeight,
      detailsClientHeight,
      detailsNestedScrollTrap: ["auto", "scroll", "overlay"].includes(detailsOverflowY) &&
        detailsScrollHeight > detailsClientHeight + 12
    };
  };
  const commandPaneLayoutProbe = () => {
    const pane = byId('commandPanePanel');
    const body = byId('commandPaneBody');
    const history = byId('liveHistory');
    const paneRect = pane ? pane.getBoundingClientRect() : null;
    const bodyRect = body ? body.getBoundingClientRect() : null;
    const historyRect = history ? history.getBoundingClientRect() : null;
    return {
      panelHeight: paneRect ? Math.round(paneRect.height) : 0,
      bodyHeight: bodyRect ? Math.round(bodyRect.height) : 0,
      historyHeight: historyRect ? Math.round(historyRect.height) : 0,
      panelTop: paneRect ? Math.round(paneRect.top) : null,
      panelBottom: paneRect ? Math.round(paneRect.bottom) : null
    };
  };
  const panelScrollProbe = id => {
    const el = byId(id);
    if (!el) return {exists: false};
    const style = window.getComputedStyle(el);
    const ancestor = ancestorId => {
      const node = byId(ancestorId);
      if (!node) return null;
      const nodeStyle = window.getComputedStyle(node);
      return {
        rect: rectOf(ancestorId),
        clientHeight: Math.round(node.clientHeight),
        scrollHeight: Math.round(node.scrollHeight),
        overflowY: nodeStyle.overflowY,
        display: nodeStyle.display,
        flex: nodeStyle.flex
      };
    };
    const visibleDirectChildren = () => Array.from(el.children).filter(child => {
      const childStyle = window.getComputedStyle(child);
      const rect = child.getBoundingClientRect();
      return child.tagName.toLowerCase() !== 'header' &&
        childStyle.display !== 'none' &&
        childStyle.visibility !== 'hidden' &&
        !child.classList.contains('hidden') &&
        rect.width > 0 &&
        rect.height > 0;
    });
    const contentBoundary = () => {
      const originalScrollTop = el.scrollTop;
      const panelRect = el.getBoundingClientRect();
      const header = el.querySelector(':scope > .workbench-panel-header');
      const headerRect = header ? header.getBoundingClientRect() : panelRect;
      const command = byId('commandPanePanel');
      const commandRect = command ? command.getBoundingClientRect() : null;
      el.scrollTop = 0;
      const topChildren = visibleDirectChildren();
      const first = topChildren.length ? topChildren[0] : null;
      const firstRect = first ? first.getBoundingClientRect() : null;
      el.scrollTop = el.scrollHeight;
      const bottomChildren = visibleDirectChildren();
      const last = bottomChildren.length ? bottomChildren[bottomChildren.length - 1] : null;
      const lastRect = last ? last.getBoundingClientRect() : null;
      const bottomVisibleLimit = Math.min(panelRect.bottom, commandRect ? commandRect.top : window.innerHeight) - 8;
      const topVisibleLimit = Math.max(panelRect.top, headerRect.bottom) + 4;
      const snapshot = {
        firstId: first ? (first.id || first.className || first.tagName) : '',
        firstTop: firstRect ? Math.round(firstRect.top) : null,
        topVisibleLimit: Math.round(topVisibleLimit),
        firstFullyBelowHeader: firstRect ? firstRect.top >= topVisibleLimit : false,
        lastId: last ? (last.id || last.className || last.tagName) : '',
        lastBottom: lastRect ? Math.round(lastRect.bottom) : null,
        bottomVisibleLimit: Math.round(bottomVisibleLimit),
        lastFullyAboveCommandPane: lastRect ? lastRect.bottom <= bottomVisibleLimit : false,
        finalScrollTop: Math.round(el.scrollTop),
        maxScrollTop: Math.round(Math.max(0, el.scrollHeight - el.clientHeight))
      };
      el.scrollTop = originalScrollTop;
      return snapshot;
    };
    return {
      exists: true,
      visible: visible(id),
      overflowY: style.overflowY,
      paddingBottom: style.paddingBottom,
      clientHeight: Math.round(el.clientHeight),
      scrollHeight: Math.round(el.scrollHeight),
      rect: rectOf(id),
      viewportClearance: {
        topAfterTabs: (() => {
          const panelRect = el.getBoundingClientRect();
          const tabs = byId('workbenchTabs');
          if (!tabs) return null;
          const tabRect = tabs.getBoundingClientRect();
          return Math.round(panelRect.top - tabRect.bottom);
        })(),
        bottomBeforeCommandPane: (() => {
          const panelRect = el.getBoundingClientRect();
          const command = byId('commandPanePanel');
          if (!command) return null;
          const commandRect = command.getBoundingClientRect();
          return Math.round(commandRect.top - panelRect.bottom);
        })()
      },
      contentBoundary: contentBoundary(),
      ancestors: {
        studioCanvasPanel: ancestor('studioCanvasPanel'),
        workbenchTabs: ancestor('workbenchTabs'),
        workbenchLayout: ancestor('workbenchLayout'),
        commandPanePanel: ancestor('commandPanePanel')
      }
    };
  };
  const pageLayoutProbe = (pageId, returnButtonId) => {
    const page = byId(pageId);
    if (!page) return {exists: false};
    const body = page.querySelector('.config-body');
    const header = page.querySelector('.config-header');
    const button = byId(returnButtonId);
    const bodyStyle = body ? window.getComputedStyle(body) : null;
    const originalScrollTop = body ? body.scrollTop : 0;
    let topBoundary = null;
    let lastBoundary = null;
    if (body) {
      const visibleChildren = () => Array.from(body.children).filter(child => {
        const childStyle = window.getComputedStyle(child);
        const rect = child.getBoundingClientRect();
        return childStyle.display !== 'none' &&
          childStyle.visibility !== 'hidden' &&
          !child.classList.contains('hidden') &&
          rect.width > 0 &&
          rect.height > 0;
      });
      body.scrollTop = 0;
      const topChildren = visibleChildren();
      const first = topChildren.length ? topChildren[0] : null;
      const firstRect = first ? first.getBoundingClientRect() : null;
      const topBodyRect = body.getBoundingClientRect();
      topBoundary = {
        firstId: first ? (first.id || first.className || first.tagName) : '',
        firstTop: firstRect ? Math.round(firstRect.top) : null,
        bodyTop: Math.round(topBodyRect.top),
        firstVisibleAtTop: firstRect ? firstRect.top >= topBodyRect.top + 6 : true
      };
      body.scrollTop = body.scrollHeight;
      const children = visibleChildren();
      const last = children.length ? children[children.length - 1] : null;
      const lastRect = last ? last.getBoundingClientRect() : null;
      const bodyRect = body.getBoundingClientRect();
      lastBoundary = {
        lastId: last ? (last.id || last.className || last.tagName) : '',
        lastBottom: lastRect ? Math.round(lastRect.bottom) : null,
        bodyBottom: Math.round(bodyRect.bottom),
        lastVisibleAtBottom: lastRect ? lastRect.bottom <= bodyRect.bottom - 8 : true,
        finalScrollTop: Math.round(body.scrollTop),
        maxScrollTop: Math.round(Math.max(0, body.scrollHeight - body.clientHeight))
      };
      body.scrollTop = originalScrollTop;
    }
    return {
      exists: true,
      visible: visible(pageId),
      headerVisible: !!(header && header.getClientRects().length),
      returnButtonVisible: visible(returnButtonId),
      returnButtonWithinViewport: rectWithinViewport(rectOf(returnButtonId)),
      bodyOverflowY: bodyStyle ? bodyStyle.overflowY : '',
      bodyClientHeight: body ? Math.round(body.clientHeight) : 0,
      bodyScrollHeight: body ? Math.round(body.scrollHeight) : 0,
      bodyRect: body ? rectOfElement(body) : null,
      pageRect: rectOf(pageId),
      topBoundary,
      lastBoundary
    };
  };
  const notebookHeaderSpacingProbe = async () => {
    const container = byId('knowledgeConsolePanel') || byId('notebookWorkspacePanel');
    const toggle = byId('notebookWorkspaceDetailsToggleButton');
    const header = document.querySelector('.notebook-workspace-header');
    if (!container || !toggle || !header) return {exists: false};
    const measure = () => {
      const containerRect = container.getBoundingClientRect();
      const toggleRect = toggle.getBoundingClientRect();
      const headerRect = header.getBoundingClientRect();
      return {
        headerTopGap: Math.round(headerRect.top - containerRect.top),
        topGap: Math.round(toggleRect.top - containerRect.top),
        rightGap: Math.round(containerRect.right - toggleRect.right),
        toggleTop: Math.round(toggleRect.top),
        toggleRight: Math.round(toggleRect.right),
        containerTop: Math.round(containerRect.top),
        containerRight: Math.round(containerRect.right),
        containerScrollTop: Math.round(container.scrollTop || 0),
        expanded: toggle.getAttribute('aria-expanded') === 'true'
      };
    };
    if (toggle.getAttribute('aria-expanded') === 'true') {
      toggle.click();
      await delay();
    }
    container.scrollTop = 0;
    await delay();
    const collapsed = measure();
    toggle.click();
    await delay();
    container.scrollTop = 120;
    await delay();
    const expandedScrolled = measure();
    container.scrollTop = 0;
    toggle.click();
    await delay();
    return {
      exists: true,
      collapsed,
      expandedScrolled,
      topGapDelta: Math.abs((collapsed.topGap || 0) - (expandedScrolled.topGap || 0)),
      rightGapDelta: Math.abs((collapsed.rightGap || 0) - (expandedScrolled.rightGap || 0))
    };
  };
  const rectOfElement = el => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      top: Math.round(r.top),
      right: Math.round(r.right),
      bottom: Math.round(r.bottom),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height)
    };
  };
  const surfaceLayout = () => ({
    shellSurface: shell ? shell.getAttribute('data-workspace-surface') : '',
    visible: {
      knowledgeConsolePanel: visible('knowledgeConsolePanel'),
      workbenchTabs: visible('workbenchTabs'),
      workbenchLayout: visible('workbenchLayout'),
      notebookWorkspacePanel: visible('notebookWorkspacePanel'),
      notebookWorkspaceDetails: visible('notebookWorkspaceDetails'),
      notebookWorkspaceGrid: visible('notebookWorkspaceGrid'),
      notebookObjectIntake: visible('notebookObjectIntake'),
      notebookObjectTaskComposer: visible('notebookObjectTaskComposer'),
      sourceRegistryPanel: visible('sourceRegistryPanel'),
      notebookWorkspaceStudyProgram: visible('notebookWorkspaceStudyProgram'),
      notebookWorkspaceRunbook: visible('notebookWorkspaceRunbook'),
      notebookWorkspaceActions: visible('notebookWorkspaceActions'),
      objectWorkspacePanel: visible('objectWorkspacePanel'),
      operationWorkspacePanel: visible('operationWorkspacePanel'),
      knowledgeWorkspacePanel: visible('knowledgeWorkspacePanel'),
      workflowWorkspacePanel: visible('workflowWorkspacePanel'),
      mindmapStudioPanel: visible('mindmapStudioPanel'),
      verificationReportPanel: visible('verificationReportPanel'),
      mindmapDiffWorkbench: visible('mindmapDiffWorkbench'),
      operationLedgerDrawer: visible('operationLedgerDrawer'),
      objectBrowserPanel: visible('objectBrowserPanel'),
      objectGraphPanel: visible('objectGraphPanel'),
      objectActivityPanel: visible('objectActivityPanel'),
      knowledgeWorkspaceReviewQueue: visible('knowledgeWorkspaceReviewQueue'),
      knowledgeWorkspaceReviewList: visible('knowledgeWorkspaceReviewList'),
      knowledgeWorkspaceResults: visible('knowledgeWorkspaceResults'),
      workflowBuilderBoardPanel: visible('workflowBuilderBoardPanel'),
      workflowWorkspaceTemplates: visible('workflowWorkspaceTemplates'),
      skillCenterPanel: visible('skillCenterPanel'),
      workflowWorkspaceSkills: visible('workflowWorkspaceSkills')
    }
  });
  const result = {
    initialMode: shell ? shell.getAttribute('data-product-mode') : ''
  };
  await click('chatModeButton');
  result.afterChat = {
    mode: shell ? shell.getAttribute('data-product-mode') : '',
    chatSelected: byId('chatModeButton') ? byId('chatModeButton').getAttribute('aria-selected') === 'true' : false,
    workspaceNavigatorVisible: visible('workspaceNavigator'),
    commandPaneBodyVisible: visible('commandPaneBody'),
    layout: chatLayoutProbe()
  };
  await click('agentWorkspaceModeButton');
  result.afterWorkspace = {
    mode: shell ? shell.getAttribute('data-product-mode') : '',
    workspaceSelected: byId('agentWorkspaceModeButton') ? byId('agentWorkspaceModeButton').getAttribute('aria-selected') === 'true' : false,
    workspaceNavigatorVisible: visible('workspaceNavigator'),
    advancedToolCenterVisible: visible('advancedToolCenterPanel'),
    expertModeExpanded: shell ? shell.getAttribute('data-expert-mode') : '',
    commandPaneExpanded: shell ? shell.getAttribute('data-command-pane-expanded') : ''
  };
  await click('expertModeToggleButton');
  result.afterExpertMode = {
    expertModeExpanded: shell ? shell.getAttribute('data-expert-mode') : '',
    workspaceNavigatorVisible: visible('workspaceNavigator'),
    expertBackVisible: visible('expertModeBackButton'),
    advancedToolCenterVisible: visible('advancedToolCenterPanel')
  };
  const detailsButton = byId('notebookWorkspaceDetailsToggleButton');
  const detailsWasExpanded = detailsButton ? detailsButton.getAttribute('aria-expanded') === 'true' : false;
  if (!detailsWasExpanded) await click('notebookWorkspaceDetailsToggleButton');
  result.consoleLayout = consoleLayoutProbe();
  result.responsiveLayout = responsiveOverflowProbe();
  if (!detailsWasExpanded) await click('notebookWorkspaceDetailsToggleButton');
  result.notebookHeaderSpacing = await notebookHeaderSpacingProbe();
  result.notebookWorkspaceDetails = {};
  if (byId('notebookWorkspaceDetailsToggleButton') &&
      byId('notebookWorkspaceDetailsToggleButton').getAttribute('aria-expanded') === 'true') {
    await click('notebookWorkspaceDetailsToggleButton');
  }
  await click('notebookWorkspaceDetailsToggleButton');
  result.notebookWorkspaceDetails.expandedAfterToggle = byId('notebookWorkspaceDetailsToggleButton') ? byId('notebookWorkspaceDetailsToggleButton').getAttribute('aria-expanded') : '';
  result.notebookWorkspaceDetails.detailsVisibleAfterToggle = visible('notebookWorkspaceDetails');
  result.notebookWorkspaceDetails.detailsHeightAfterToggle = byId('notebookWorkspaceDetails') ? Math.round(byId('notebookWorkspaceDetails').getBoundingClientRect().height) : 0;
  result.notebookWorkspaceDetails.detailsScrollHeightAfterToggle = byId('notebookWorkspaceDetails') ? Math.round(byId('notebookWorkspaceDetails').scrollHeight) : 0;
  await click('notebookWorkspaceDetailsToggleButton');
  result.commandPane = {};
  result.commandPane.navigatorExpandedBeforeCommand = shell ? shell.getAttribute('data-workspace-navigator-expanded') : '';
  await click('commandPaneToggleButton');
  result.commandPane.expandedAfterToggle = shell ? shell.getAttribute('data-command-pane-expanded') : '';
  result.commandPane.navigatorExpandedAfterToggle = shell ? shell.getAttribute('data-workspace-navigator-expanded') : '';
  result.commandPane.navigatorVisibleAfterToggle = visible('workspaceNavigator');
  const commandPaneLayout = commandPaneLayoutProbe();
  result.commandPane.panelHeightAfterToggle = commandPaneLayout.panelHeight;
  result.commandPane.bodyHeightAfterToggle = commandPaneLayout.bodyHeight;
  result.commandPane.historyHeightAfterToggle = commandPaneLayout.historyHeight;
  const sendButtonRect = rectOf('sendButton');
  const composerRect = rectOf('commandPaneComposer');
  result.composerVisibility = {
    viewportWidth: window.innerWidth,
    viewportHeight: window.innerHeight,
    sendButtonVisibleInStress: visible('sendButton'),
    sendButtonWithinViewportInStress: rectWithinViewport(sendButtonRect),
    composerWithinViewportInStress: rectWithinViewport(composerRect),
    sendButtonRect,
    composerRect
  };
  await click('commandPaneToggleButton');
  result.workspaceNavigator = {};
  result.workspaceNavigator.expandedState = shell ? shell.getAttribute('data-workspace-navigator-expanded') : '';
  result.workspaceNavigator.toggleVisible = visible('workspaceNavigatorToggleButton');
  result.workspaceNavigator.gridVisible = !!document.querySelector('.workspace-nav-grid') &&
    Array.from(document.querySelectorAll('.workspace-nav-grid')).some(node => {
      const rect = node.getBoundingClientRect();
      const style = window.getComputedStyle(node);
      return style.display !== 'none' && style.visibility !== 'hidden' && rect.width > 0 && rect.height > 0;
    });
  result.workspaceSurfaceSelectFocus = {};
  const workspaceSelect = byId('workspaceSurfaceSelect');
  const switchViaSelect = async surface => {
    if (!workspaceSelect) return false;
    workspaceSelect.value = surface;
    workspaceSelect.dispatchEvent(new Event('change', {bubbles: true}));
    await delay();
    return true;
  };
  if (workspaceSelect) {
    result.workspaceSurfaceSelectFocus.exists = true;
    workspaceSelect.focus();
    result.workspaceSurfaceSelectFocus.focusedBeforeMousedown = document.activeElement === workspaceSelect;
    workspaceSelect.dispatchEvent(new MouseEvent('mousedown', {bubbles: true, cancelable: true}));
    await delay();
    result.workspaceSurfaceSelectFocus.blurredOnFocusedMousedown = document.activeElement !== workspaceSelect;
    workspaceSelect.focus();
    await switchViaSelect('mindmap_studio');
    result.workspaceSurfaceSelectFocus.activeSurfaceAfterChange = activeSurface();
    result.workspaceSurfaceSelectFocus.blurredAfterChange = document.activeElement !== workspaceSelect;
  } else {
    result.workspaceSurfaceSelectFocus.exists = false;
  }
  result.knowledgeMatrix = {};
  await click('notebookKnowledgeMatrixToggleButton');
  result.knowledgeMatrix.expandedAfterToggle = byId('notebookKnowledgeMatrixToggleButton') ? byId('notebookKnowledgeMatrixToggleButton').getAttribute('aria-expanded') : '';
  result.knowledgeMatrix.toggleDisabled = byId('notebookKnowledgeMatrixToggleButton') ? !!byId('notebookKnowledgeMatrixToggleButton').disabled : false;
  await click('notebookKnowledgeMatrixToggleButton');
  result.workspaceSurfaces = {};
  const surfaceEntries = [
    ['workspaceNavConsoleButton', 'console'],
    ['workspaceNavMindmapStudioButton', 'mindmap_studio'],
    ['workspaceNavCardFactoryButton', 'card_factory'],
    ['workspaceNavLedgerExplorerButton', 'ledger_explorer'],
    ['workspaceNavKnowledgeGraphButton', 'knowledge_graph'],
    ['workspaceNavWorkflowBuilderButton', 'workflow_builder'],
    ['workspaceNavSkillCenterButton', 'skill_center']
  ];
  for (const [id, surface] of surfaceEntries) {
    await switchViaSelect(surface);
    result.workspaceSurfaces[id] = {activeSurface: activeSurface(), activePane: activePane(), layout: surfaceLayout()};
  }
  result.workspaceSelectSurfaces = {};
  const selectOnlySurfaces = ['object_browser', 'source_registry', 'verification_center'];
  for (const surface of selectOnlySurfaces) {
    await switchViaSelect(surface);
    result.workspaceSelectSurfaces[surface] = {activeSurface: activeSurface(), activePane: activePane(), layout: surfaceLayout()};
  }
  result.workspaceNavigator.expandedAfterSurfaceSelection = shell ? shell.getAttribute('data-workspace-navigator-expanded') : '';
  result.workbenchTabs = {};
  const tabButtons = ['workbenchTabObject', 'workbenchTabOperation', 'workbenchTabKnowledge', 'workbenchTabWorkflow'];
  for (const id of tabButtons) {
    await click(id);
    result.workbenchTabs[id] = {activeSurface: activeSurface(), activePane: activePane()};
  }
  result.workbenchScroll = {};
  await switchViaSelect('mindmap_studio');
  result.mindmapStudio = {activeSurface: activeSurface(), activePane: activePane(), panelVisible: visible('operationWorkspacePanel')};
  result.workbenchScroll.operation = panelScrollProbe('operationWorkspacePanel');
  await switchViaSelect('card_factory');
  result.cardFactory = {activeSurface: activeSurface(), activePane: activePane(), panelVisible: visible('knowledgeWorkspacePanel')};
  result.workbenchScroll.knowledge = panelScrollProbe('knowledgeWorkspacePanel');
  await switchViaSelect('workflow_builder');
  result.workflowBuilder = {activeSurface: activeSurface(), activePane: activePane(), panelVisible: visible('workflowWorkspacePanel')};
  result.workbenchScroll.workflow = panelScrollProbe('workflowWorkspacePanel');
  await click('settingsButton');
  result.settings = {opened: !classHidden('configPage'), historyHiddenWhileOpen: classHidden('conversationHistoryPage')};
  result.settings.layout = pageLayoutProbe('configPage', 'configBackButton');
  await click('contextScopeAutoButton');
  result.settings.contextScopeAutoPressed = byId('contextScopeAutoButton') ? byId('contextScopeAutoButton').getAttribute('aria-pressed') === 'true' : false;
  await click('configBackButton');
  result.settings.closed = classHidden('configPage');
  await click('conversationHistoryButton');
  result.history = {opened: !classHidden('conversationHistoryPage'), settingsHiddenWhileOpen: classHidden('configPage')};
  result.history.layout = pageLayoutProbe('conversationHistoryPage', 'conversationHistoryCloseButton');
  await click('conversationHistoryCloseButton');
  result.history.closed = classHidden('conversationHistoryPage');
  return result;
})()
"""


def browser_base_response_for_action(action: str) -> dict[str, Any]:
    stub_mn_object = {
        "objectId": "mnobj:doc:ui-actions",
        "kind": "document",
        "title": "任意文档 Stub UI 验收.pdf",
        "sourceRef": {
            "topicid": "stub-topic",
            "bookmd5": "stub-book",
            "documentTitle": "任意文档 Stub UI 验收.pdf",
        },
    }
    stub_agent_operation = {
        "schema": "codex.mn.agentOperation.v1",
        "mnObject": stub_mn_object,
        "object": {
            "mnObjectId": stub_mn_object["objectId"],
            "kind": stub_mn_object["kind"],
            "title": stub_mn_object["title"],
            "sourceRef": stub_mn_object["sourceRef"],
        },
        "intent": {"kind": "inspect_document", "summary": "UI action wiring acceptance"},
        "workflow": {"id": "ui_action_acceptance", "title": "任意文档 UI 动作验收"},
        "contextPolicy": {"visibleScope": "current_document"},
        "knowledge": {"enabled": True, "count": 1},
        "operationPolicy": {
            "risk": {
                "status": "read_only",
                "dryRunStatus": "not_required",
                "confirmationPoints": [],
            }
        },
        "nextActions": [
            {"id": "open_object_browser", "label": "浏览对象"},
            {"id": "open_operation_ledger", "label": "查看账本"},
            {"id": "open_verification_center", "label": "验证证据"},
        ],
    }
    if action == "chat":
        return {
            "ok": True,
            "message": "stub chat completed",
            "reply": "任意文档 UI 主输入验收已完成。",
            "queue": {"pending": 0},
        }
    if action == "conversation_new":
        return {
            "ok": True,
            "message": "stub new conversation",
            "conversation": {
                "conversationId": "UI-ACTION-CONVERSATION",
                "title": "任意文档 UI 验收会话",
                "history": [],
            },
        }
    if action == "settings_update":
        return {
            "ok": True,
            "message": "stub settings saved",
            "settings": {
                "fileSearchRoots": ["/tmp/codex-ui-action-root"],
                "defaultContextScope": "document",
                "aiBackend": "auto",
                "speed": "fast",
                "model": "gpt-5.5",
            },
        }
    if action == "update_check":
        return {
            "ok": True,
            "message": "stub update check",
            "update": {
                "repo": "LiuWhale/marginnote-assistant",
                "currentVersion": "0.4.41",
                "latestVersion": "0.4.41",
                "hasUpdate": False,
                "releaseUrl": "https://github.com/LiuWhale/marginnote-assistant/releases",
            },
        }
    if action == "open_url":
        return {
            "ok": True,
            "message": "stub opened download page",
            "url": "https://github.com/LiuWhale/marginnote-assistant/releases",
        }
    if action == "diagnose_permissions":
        return {
            "ok": True,
            "message": "stub permission diagnosis",
            "status": "OK",
            "fileAccess": {"ok": True, "summary": "stub file access ok"},
        }
    if action == "open_full_disk_access_settings":
        return {
            "ok": True,
            "message": "stub opened Full Disk Access settings",
            "reply": "已打开权限设置。",
        }
    if action == "request_pdf_cache":
        return {
            "ok": True,
            "message": "stub PDF cache requested",
            "reply": "已请求缓存当前 PDF。",
            "pdfCache": {
                "state": "waiting_native",
                "label": "PDF缓存：等待 MN4 缓存",
                "detail": "stub PDF cache request",
                "pending": True,
            },
        }
    if action == "request_native_capability_probe":
        return {
            "ok": True,
            "message": "stub native capability probe requested",
            "nativeApiCapabilities": {
                "available": True,
                "features": ["native-mn-object-registry-scan-v1"],
            },
        }
    if action == "native_highlight_wizard_start":
        return {
            "ok": True,
            "message": "stub native highlight wizard started",
            "nativeHighlightWizard": {
                "stage": "waiting_selection",
                "summary": "stub waiting for a PDF selection",
                "blockedChecks": ["native_highlight_visible"],
                "nextActions": ["回到 PDF 重新选中一小段文字。"],
                "secondsRemaining": 88,
                "elapsedSeconds": 2,
                "latestEventName": "nativeHighlightNextSelectionPollStarted",
                "latestEventReason": "stub-selection-required",
                "recoverable": True,
                "retryAction": "native_highlight_wizard_start",
                "retryLabel": "重新高亮采证",
            },
        }
    if action == "request_pdf_selection_probe":
        return {
            "ok": True,
            "message": "stub PDF selection probe requested",
            "selectionProbe": {
                "schema": "codex.mn.pdfSelectionProbe.v1",
                "ready": False,
                "hasSelectionText": False,
                "selectionLength": 0,
                "hasDocumentController": True,
                "selectedDocumentControllerLabel": "stub.reader.currentDocumentController",
                "candidateCount": 1,
                "candidateLabels": ["stub.reader.currentDocumentController"],
                "ageSeconds": 0,
                "error": "",
            },
            "nativeHighlightWizard": {
                "stage": "waiting_selection",
                "summary": "stub waiting after PDF selection probe",
                "blockedChecks": ["native_highlight_visible", "selection_popup_highlight"],
                "secondsRemaining": None,
                "elapsedSeconds": 0,
                "latestEventName": "nativeHighlightSelectionProbe",
                "latestEventReason": "",
                "selectionProbe": {
                    "schema": "codex.mn.pdfSelectionProbe.v1",
                    "ready": False,
                    "hasSelectionText": False,
                    "selectionLength": 0,
                    "hasDocumentController": True,
                    "selectedDocumentControllerLabel": "stub.reader.currentDocumentController",
                    "candidateCount": 1,
                    "candidateLabels": ["stub.reader.currentDocumentController"],
                    "ageSeconds": 0,
                    "error": "",
                },
                "recoverable": True,
                "retryAction": "native_highlight_wizard_start",
                "retryLabel": "重新高亮采证",
            },
        }
    if action == "native_highlight_wizard_status":
        return {
            "ok": True,
            "message": "stub native highlight wizard status",
            "nativeHighlightWizard": {
                "stage": "expired",
                "summary": "stub expired waiting for a PDF selection",
                "blockedChecks": ["native_highlight_visible", "selection_popup_highlight"],
                "secondsRemaining": 0,
                "elapsedSeconds": 91,
                "latestEventName": "nativeHighlightNextSelectionPollExpired",
                "latestEventReason": "stub-selection-required",
                "recoverable": True,
                "retryAction": "native_highlight_wizard_start",
                "retryLabel": "重新高亮采证",
            },
        }
    if action == "agent_plan":
        return {
            "ok": True,
            "message": "stub agent plan",
            "agentOperation": stub_agent_operation,
        }
    if action == "request_mn_object_registry_scan":
        return {
            "ok": True,
            "message": "stub MN object registry scan requested",
            "schema": "codex.mn.nativeObjectScanRequest.v1",
            "requestId": "ui-actions-native-scan",
            "status": "submitted",
        }
    if action == "mn_read_tree":
        return {
            "ok": True,
            "message": "stub mindmap tree read requested",
            "mindmapTreeCache": {
                "schema": "codex.mn.mindmapTreeCache.v1",
                "available": True,
                "status": "ready",
                "nodeCount": 1,
                "rootTitle": "任意文档 Stub 脑图",
                "treePreview": [{"title": "任意文档 Stub 脑图", "depth": 0, "childCount": 0}],
            },
        }
    if action == "notebook_workspace":
        return {
            "ok": True,
            "message": "stub notebook workspace",
            "notebookWorkspace": {
                "schema": "codex.mn.notebookWorkspace.v1",
                "topicid": "stub-topic",
                "bookmd5": "stub-book",
                "documentTitle": "任意文档 Stub UI 验收.pdf",
                "focusObject": stub_mn_object,
                "primaryActions": [],
                "objects": {},
                "mindmap": {},
                "reviewQueue": {},
                "workflows": {},
                "ledger": {},
                "readiness": {},
                "knowledgeMatrix": {"schema": "codex.mn.knowledgeConsoleMatrix.v1", "axes": []},
                "objectIntake": {"schema": "codex.mn.objectIntake.v1", "routes": []},
                "objectTaskComposer": {"schema": "codex.mn.objectTaskComposer.v1", "tasks": []},
                "runbook": {
                    "schema": "codex.mn.notebookRunbook.v1",
                    "status": "action_required",
                    "summary": {"ready": 1, "actionRequired": 1, "blocked": 0, "pending": 0},
                    "steps": [
                        {"id": "context", "label": "确认上下文", "status": "ready", "evidence": ["stub context"]},
                        {
                            "id": "object_browser",
                            "label": "读取对象浏览器",
                            "status": "action_required",
                            "evidence": ["stub object"],
                            "action": {
                                "id": "open_object_browser",
                                "label": "打开 Object Browser",
                                "action": "object_browser",
                                "surface": "object_browser",
                                "payload": {"mnObjectId": "mnobj:doc:ui-actions"},
                            },
                        },
                    ],
                    "continueAction": {
                        "id": "open_object_browser",
                        "label": "继续下一步",
                        "action": "object_browser",
                        "surface": "object_browser",
                        "payload": {"mnObjectId": "mnobj:doc:ui-actions"},
                    },
                    "autoPlan": {
                        "schema": "codex.mn.notebookRunbookAutoPlan.v1",
                        "canRun": True,
                        "label": "自动准备",
                        "detail": "stub safe preflight",
                        "actions": [
                            {
                                "id": "open_object_browser",
                                "label": "打开 Object Browser",
                                "action": "object_browser",
                                "surface": "object_browser",
                                "payload": {"mnObjectId": "mnobj:doc:ui-actions"},
                            }
                        ],
                    },
                },
                "sourceRegistry": {"schema": "codex.mn.sourceRegistry.v1", "sources": []},
            },
            "objectBrowser": {"ok": True, "schema": "codex.mn.objectBrowser.v1", "items": [], "counts": {}, "sources": {}},
            "operationLedger": {"ok": True, "schema": "codex.mn.operationLedger.v1", "entries": [], "counts": {}},
            "reviewQueue": {"schema": "codex.mn.reviewQueue.v1", "items": [], "summary": {}},
            "workflowWorkspace": {
                "schema": "codex.mn.workflowWorkspace.v1",
                "workflowRuns": [],
                "workflowTemplates": [],
                "workflowBuilderBoard": {"schema": "codex.mn.workflowBuilderBoard.v1", "lanes": []},
            },
            "mindmapTreeCache": {"available": False, "nodeCount": 0},
        }
    if action == "object_browser":
        return {"ok": True, "message": "stub object browser", "schema": "codex.mn.objectBrowser.v1", "items": [], "counts": {}, "sources": {}}
    if action == "object_graph":
        return {
            "ok": True,
            "message": "stub object graph",
            "schema": "codex.mn.objectGraph.v1",
            "nodes": [],
            "edges": [],
            "counts": {},
        }
    if action == "object_activity":
        return {
            "ok": True,
            "message": "stub object activity",
            "schema": "codex.mn.objectActivity.v1",
            "conversations": [],
            "workflowRuns": [],
            "transactions": [],
            "manualRelations": [],
            "logs": [],
            "counts": {},
        }
    if action == "operation_ledger_list":
        return {"ok": True, "message": "stub ledger", "schema": "codex.mn.operationLedger.v1", "entries": [], "counts": {"total": 0}}
    if action == "verification_report_list":
        return {
            "ok": True,
            "message": "stub verification",
            "schema": "codex.mn.verificationReportList.v1",
            "reports": [],
            "counts": {"PASS": 0, "FAIL": 0, "UNKNOWN": 1},
            "repairPlan": {
                "schema": "codex.mn.verificationRepairPlan.v1",
                "status": "action_required",
                "detail": "stub repair plan",
                "recommendedActionId": "request_object_existence_probe",
                "recommendedAction": {
                    "id": "request_object_existence_probe",
                    "label": "检查真实对象",
                    "action": "request_mn_object_existence_probe",
                    "payload": {"transactionId": "tx-ui-actions", "noteIds": ["N-ui-actions"]},
                },
                "actions": [
                    {
                        "id": "request_object_existence_probe",
                        "label": "检查真实对象",
                        "action": "request_mn_object_existence_probe",
                        "payload": {"transactionId": "tx-ui-actions", "noteIds": ["N-ui-actions"]},
                    }
                ],
            },
        }
    if action == "knowledge_index_search":
        return {
            "ok": True,
            "message": "stub knowledge search",
            "schema": "codex.mn.knowledgeIndexSearch.v1",
            "matches": [],
        }
    if action == "mindmap_target_status":
        return {
            "ok": True,
            "message": "stub mindmap target status",
            "mindmapTarget": {
                "state": "ready",
                "label": "目标脑图：stub",
                "detail": "stub target status",
                "target": {"mode": "document"},
                "options": [],
            },
        }
    if action == "notebook_runbook_preflight_record":
        return {
            "ok": True,
            "message": "stub runbook preflight recorded",
            "preflightRun": {
                "schema": "codex.mn.notebookRunbookPreflightRun.v1",
                "runId": "preflight-ui-actions",
                "status": "running",
                "actionCount": 1,
                "completedCount": 0,
                "failedCount": 0,
            },
        }
    if action == "object_graph_relation_save":
        return {
            "ok": True,
            "message": "stub object graph relation saved",
            "relation": {
                "relationId": "relation-ui-actions",
                "fromObjectId": "mnobj:doc:ui-actions",
                "toObjectId": "mnobj:doc:ui-related",
                "relation": "related_to",
                "label": "UI relation",
            },
        }
    if action == "health":
        return {"ok": True, "message": "stub health", "status": "ok", "ready": True}
    if action == "ai_backend_probe":
        return {"ok": True, "message": "stub ai probe", "backend": "stub", "available": True}
    if action == "single_document_acceptance_summary":
        return {
            "ok": True,
            "message": "stub single document acceptance",
            "singleDocumentReady": False,
            "singleDocumentPassedCount": 6,
            "singleDocumentTotalCount": 8,
            "singleDocumentBlockerCount": 2,
            "singleDocumentAcceptance": {
                "schema": "codex-companion-single-document-acceptance-v1",
                "topicid": "UI-ACTIONS-TOPIC",
                "bookmd5": "ui-actions-book",
                "summary": {
                    "singleDocumentAcceptance": "BLOCK",
                    "passed": 6,
                    "total": 8,
                    "blocked": 2,
                },
                "checks": [
                    {
                        "id": "native_api_matrix",
                        "label": "MN native API matrix",
                        "status": "BLOCK",
                        "detail": "Missing nativeApiCapabilities event.",
                        "nextActions": ["刷新 MN 能力。"],
                    },
                    {
                        "id": "native_highlight_visible",
                        "label": "MN native visible highlight",
                        "status": "BLOCK",
                        "detail": "Missing native visible highlight proof.",
                        "nextActions": ["运行高亮采证。"],
                    },
                ],
            },
            "reply": "本文档验收：BLOCK，阻塞项 2。",
        }
    if action == "ui_functional_acceptance_summary":
        return {
            "ok": True,
            "message": "stub UI functional acceptance",
            "uiFunctionalReady": True,
            "uiFunctionalPassedCount": 11,
            "uiFunctionalTotalCount": 11,
            "uiFunctionalBlockerCount": 0,
            "uiFunctionalAcceptance": {
                "schema": SCHEMA,
                "ok": True,
                "checks": [
                    {
                        "id": "webview_browser_actions",
                        "label": "WebView browser actions",
                        "status": "PASS",
                        "problems": [],
                    }
                ],
                "problems": [],
            },
            "realMnRuntimeReady": False,
            "realMnRuntimeBlockerCount": 2,
            "realMnRuntimeAcceptance": {
                "schema": "codex-companion-real-mn-runtime-boundary-v1",
                "status": "BLOCK",
                "ready": False,
                "passedCount": 6,
                "totalCount": 8,
                "blockerCount": 2,
                "topicid": "UI-ACTIONS-TOPIC",
                "bookmd5": "ui-actions-book",
                "message": "stub real MN4 runtime evidence is not proved",
                "nextActions": ["刷新 MN 能力。", "运行高亮采证。"],
                "recommendedActions": [
                    {
                        "id": "refresh_native_capabilities",
                        "label": "刷新 MN 能力",
                        "kind": "button",
                        "handler": "refreshNativeCapabilities",
                        "action": "request_native_capability_probe",
                        "checkId": "native_api_matrix",
                        "writeRisk": False,
                    },
                    {
                        "id": "run_native_highlight_wizard",
                        "label": "运行高亮采证",
                        "kind": "button",
                        "handler": "startNativeHighlightWizard",
                        "action": "native_highlight_wizard_start",
                        "checkId": "native_highlight_visible",
                        "writeRisk": False,
                    },
                ],
                "singleDocumentAcceptance": {
                    "schema": "codex-companion-single-document-acceptance-v1",
                    "topicid": "UI-ACTIONS-TOPIC",
                    "bookmd5": "ui-actions-book",
                    "checks": [
                        {
                            "id": "native_api_matrix",
                            "label": "MN native API matrix",
                            "status": "BLOCK",
                            "detail": "Missing nativeApiCapabilities event.",
                            "nextActions": ["刷新 MN 能力。"],
                        },
                        {
                            "id": "native_highlight_visible",
                            "label": "MN native visible highlight",
                            "status": "BLOCK",
                            "detail": "Missing native visible highlight proof.",
                            "nextActions": ["运行高亮采证。"],
                        },
                    ],
                    "nextActions": ["刷新 MN 能力。", "运行高亮采证。"],
                },
            },
            "reply": "任意文档 UI 功能验收：PASS",
        }
    if action == "logs_recent":
        return {"ok": True, "message": "stub logs", "logs": [], "entries": []}
    if action == "conversation_list":
        return {"ok": True, "message": "stub conversations", "conversations": [], "items": []}
    if action == "generate_mindmap":
        return {
            "ok": True,
            "message": "stub generated mindmap draft",
            "reply": "stub mindmap draft generated",
            "mindmap": {
                "title": "任意文档 Stub 脑图",
                "nodes": [{"title": "核心问题", "children": [{"title": "方法路线"}]}],
                "writeTarget": {"mode": "selected_or_document_root", "label": "任意文档 Stub 脑图"},
            },
            "cards": [],
            "writeTarget": {"mode": "selected_or_document_root", "label": "任意文档 Stub 脑图"},
        }
    if action == "draft_save":
        return {
            "ok": True,
            "message": "stub draft saved",
            "draft": {
                "id": "draft-ui-write",
                "original_action": "generate_mindmap",
                "has_mindmap": True,
                "mindmap_title": "任意文档 Stub 脑图",
                "card_count": 0,
                "createdCount": 1,
                "operation_manifest": {
                    "operationCount": 1,
                    "createMindmapNodes": 1,
                    "dryRun": {"status": "ready", "operationCount": 1, "blockedCount": 0},
                },
            },
        }
    if action == "mindmap_diff_preview":
        operation = {
            "opId": "op-create-ui-write",
            "op": "create_mindmap_node",
            "mutation": "create",
            "title": "核心问题",
            "bodyPreview": "任意文档 UI 写入验收节点",
            "targetParent": "任意文档 Stub 脑图",
            "proposedPath": "0.1",
            "requires": ["nativeMindmap"],
            "reason": "UI write action acceptance",
        }
        return {
            "ok": True,
            "message": "stub mindmap diff preview",
            "draftId": "draft-ui-write",
            "mindmapDiff": {
                "schema": "codex.mn.mindmapDiff.v1",
                "summary": {
                    "proposedCount": 1,
                    "currentCount": 1,
                    "createCount": 1,
                    "updateCount": 0,
                    "mergeCount": 0,
                    "duplicateCount": 0,
                },
                "operations": [operation],
            },
            "mindmapDiffOperationPlan": {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 1,
                "skippedCount": 0,
                "requiredCapabilities": ["nativeMindmap"],
                "operations": [operation],
                "applyBoundary": {
                    "localApplyStatus": "all_local",
                    "currentApplyPath": "local_operation_queue",
                    "acceptButtonBehavior": "applies_local_operations",
                    "directlyExecutableMutations": ["create"],
                    "blockedLocalMutations": [],
                },
            },
        }
    if action == "request_mindmap_diff_apply":
        return {
            "ok": True,
            "message": "stub mindmap diff apply queued",
            "applyPlan": {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "transactionId": "tx-ui-write",
                "operationCount": 1,
                "operations": [],
            },
            "queue": {"pending": 0},
        }
    if action == "ai_edit_transaction_get":
        return {
            "ok": True,
            "message": "stub transaction",
            "transaction": {
                "schema": "codex.mn.aiEditTransaction.v1",
                "transactionId": "tx-ui-write",
                "status": "created_pending_user_decision",
                "createdNoteIds": ["N-ui-write"],
                "createdCardIds": [],
                "objectRef": stub_mn_object,
                "topicid": "stub-topic",
                "bookmd5": "stub-book",
                "draftId": "draft-ui-write",
            },
        }
    if action == "ai_edit_transaction_verify":
        return {
            "ok": True,
            "message": "stub transaction verification",
            "reply": "stub transaction verification",
            "transaction": {
                "schema": "codex.mn.aiEditTransaction.v1",
                "transactionId": "tx-ui-write",
                "status": "created_pending_user_decision",
                "createdNoteIds": ["N-ui-write"],
                "objectRef": stub_mn_object,
            },
            "verification": {
                "schema": "codex.mn.aiEditTransactionVerification.v1",
                "transactionId": "tx-ui-write",
                "status": "pending",
                "summary": "stub verification pending native probe",
                "createdCount": 1,
                "remainingCount": 1,
                "createdNoteIds": ["N-ui-write"],
                "remainingNoteIds": ["N-ui-write"],
                "nextActions": [
                    {
                        "id": "request_object_existence_probe",
                        "action": "request_mn_object_existence_probe",
                        "noteIds": ["N-ui-write"],
                    }
                ],
                "residualProof": {
                    "schema": "codex.mn.residualProof.v1",
                    "status": "pending",
                    "remainingCount": 1,
                    "objects": [
                        {
                            "noteId": "N-ui-write",
                            "expectedState": "created_pending_user_decision",
                            "actualState": "unknown",
                            "residual": True,
                            "verificationLevel": "native_probe_missing",
                        }
                    ],
                },
            },
        }
    if action == "request_mn_object_existence_probe":
        return {
            "ok": True,
            "message": "stub object existence probe requested",
            "probe": {
                "schema": "codex.mn.objectExistenceProbeRequest.v1",
                "probeId": "probe-ui-write",
                "transactionId": "tx-ui-write",
                "noteIds": ["N-ui-write"],
            },
            "queue": {"pending": 0},
        }
    if action == "review_queue_add":
        return {
            "ok": True,
            "message": "stub review queue add",
            "reviewQueue": {"schema": "codex.mn.reviewQueue.v1", "items": [], "summary": {"total": 0}},
            "summary": {"total": 0},
        }
    return {"ok": True, "message": f"stub {action}"}


def browser_action_stub_script(responses: dict[str, dict[str, Any]]) -> str:
    responses_json = json.dumps(responses, ensure_ascii=False)
    return (
        r"""
(function() {
  const responses = RESPONSES_JSON;
  window.__codexActionCalls = [];
  window.__codexBridgeCalls = [];
  const OriginalXHR = window.XMLHttpRequest;
  function StubXHR() {
    this.headers = {};
    this.readyState = 0;
    this.status = 0;
    this.responseText = '';
    this.onreadystatechange = null;
    this.onerror = null;
    this.method = '';
    this.url = '';
  }
  StubXHR.prototype.open = function(method, url) {
    this.method = method;
    this.url = url;
    this.readyState = 1;
  };
  StubXHR.prototype.setRequestHeader = function(key, value) {
    this.headers[key] = value;
  };
  StubXHR.prototype.send = function(body) {
    const xhr = this;
    let payload = {};
    try { payload = JSON.parse(body || '{}'); } catch (err) { payload = {}; }
    const action = payload.action || (String(xhr.url || '').indexOf('/status') >= 0 ? 'status' : '');
    window.__codexActionCalls.push({method: xhr.method, url: xhr.url, action: action, payload: payload});
    const response = responses[action] || {ok: true, message: 'stub ' + action};
    window.setTimeout(function() {
      xhr.status = 200;
      xhr.readyState = 4;
      xhr.responseText = JSON.stringify(response);
      if (typeof xhr.onreadystatechange === 'function') xhr.onreadystatechange();
    }, 20);
  };
  window.XMLHttpRequest = StubXHR;
  window.__codexRestoreXHR = function() { window.XMLHttpRequest = OriginalXHR; };
  return true;
})()
"""
    ).replace("RESPONSES_JSON", responses_json)


BROWSER_ACTION_STUB_CLICK_SCRIPT = r"""
(async function() {
  const delay = () => new Promise(resolve => window.setTimeout(resolve, 120));
  const byId = id => document.getElementById(id);
  const shell = byId('aiChatShell');
  const clicked = {};
  const buttonActionDeltas = {};
  window.__codexBridgeCalls = [];
  const actionCount = action => (window.__codexActionCalls || []).filter(call => call.action === action).length;
  const visible = id => {
    const el = byId(id);
    if (!el) return false;
    const style = window.getComputedStyle(el);
    const hasBox = Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    return hasBox && !el.classList.contains('hidden') && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const rectOf = id => {
    const el = byId(id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      top: Math.round(r.top),
      right: Math.round(r.right),
      bottom: Math.round(r.bottom),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height)
    };
  };
  const rectWithinViewport = rect => {
    if (!rect || rect.width <= 0 || rect.height <= 0) return false;
    return rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth;
  };
  const classHidden = id => {
    const el = byId(id);
    return !el || el.classList.contains('hidden');
  };
  const waitFor = async predicate => {
    for (let i = 0; i < 15; i++) {
      if (predicate()) return true;
      await delay();
    }
    return false;
  };
  const waitForAction = async action => waitFor(() => actionCount(action) > 0);
  const waitForActionCount = async (action, count) => waitFor(() => actionCount(action) >= count);
  const click = async id => {
    const el = byId(id);
    clicked[id] = !!(el && !el.disabled);
    if (el && !el.disabled) {
      el.click();
      await delay();
      return true;
    }
    await delay();
    return false;
  };
  const clickAndWaitAction = async (id, action) => {
    const before = actionCount(action);
    const didClick = await click(id);
    if (didClick) await waitForActionCount(action, before + 1);
    buttonActionDeltas[id] = actionCount(action) - before;
    return buttonActionDeltas[id] > 0;
  };
  const editorVisible = id => {
    const el = byId(id);
    return !!(el && !el.classList.contains('hidden'));
  };
  const setInput = async (id, value) => {
    const el = byId(id);
    if (!el) return false;
    el.value = value;
    el.dispatchEvent(new Event('input', {bubbles: true}));
    await delay();
    return true;
  };
  const enterInput = async id => {
    const el = byId(id);
    if (!el) return false;
    const before = actionCount('chat');
    el.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true}));
    return await waitForActionCount('chat', before + 1);
  };
  if (window.CodexPanel && typeof window.CodexPanel.setContext === 'function') {
    window.CodexPanel.setContext({
      topicid: 'stub-topic',
      notebookid: 'stub-topic',
      bookmd5: 'stub-book',
      docmd5: 'stub-book',
      documentTitle: '任意文档 Stub UI 验收.pdf'
    });
    await delay();
  }
  await setInput('promptInput', '解释这份任意文档的核心内容');
  await clickAndWaitAction('sendButton', 'chat');
  await delay();
  const promptClearedAfterSend = byId('promptInput') ? byId('promptInput').value === '' : false;
  await setInput('promptInput', '用 Enter 再提交一次');
  const enterSubmitted = await enterInput('promptInput');
  await delay();
  await clickAndWaitAction('newConversationButton', 'conversation_new');
  await clickAndWaitAction('agentPlanRefreshButton', 'agent_plan');
  await clickAndWaitAction('objectRegistryScanButton', 'request_mn_object_registry_scan');
  await clickAndWaitAction('mindmapTreeRefreshButton', 'mn_read_tree');
  await clickAndWaitAction('mindmapStudioReadTreeButton', 'mn_read_tree');
  for (let i = 0; i < 5 && actionCount('notebook_workspace') === 0; i++) {
    await clickAndWaitAction('notebookWorkspaceRefreshButton', 'notebook_workspace');
    await delay();
  }
  if (!buttonActionDeltas.notebookWorkspaceRefreshButton) {
    buttonActionDeltas.notebookWorkspaceRefreshButton = actionCount('notebook_workspace') > 0 ? 1 : 0;
  }
  await clickAndWaitAction('notebookWorkspaceRunbookContinueButton', 'object_browser');
  await clickAndWaitAction('notebookWorkspaceRunbookAutoButton', 'notebook_runbook_preflight_record');
  await clickAndWaitAction('objectBrowserRefreshButton', 'object_browser');
  await setInput('objectBrowserSearchInput', '任意文档');
  await clickAndWaitAction('objectBrowserFilterButton', 'object_browser');
  await clickAndWaitAction('objectGraphRefreshButton', 'object_graph');
  await click('objectGraphRelationAddButton');
  const relationEditorOpened = editorVisible('objectGraphRelationEditor');
  await setInput('objectGraphRelationTargetInput', 'mnobj:doc:ui-related');
  await setInput('objectGraphRelationLabelInput', 'UI relation');
  await clickAndWaitAction('objectGraphRelationSaveButton', 'object_graph_relation_save');
  await click('objectGraphRelationAddButton');
  await click('objectGraphRelationCancelButton');
  const relationEditorClosedAfterCancel = !editorVisible('objectGraphRelationEditor');
  await clickAndWaitAction('objectActivityRefreshButton', 'object_activity');
  await clickAndWaitAction('operationLedgerRefreshButton', 'operation_ledger_list');
  await clickAndWaitAction('operationLedgerFilterButton', 'operation_ledger_list');
  await clickAndWaitAction('verificationReportRefreshButton', 'verification_report_list');
  await clickAndWaitAction('verificationRepairPlanRecommendedButton', 'request_mn_object_existence_probe');
  await clickAndWaitAction('realMnAcceptanceRunAllButton', 'single_document_acceptance_summary');
  await clickAndWaitAction('singleDocumentAcceptanceButton', 'single_document_acceptance_summary');
  await clickAndWaitAction('mainUiFunctionalAcceptanceButton', 'ui_functional_acceptance_summary');
  await clickAndWaitAction('realMnAcceptanceSafeEvidenceButton', 'request_native_capability_probe');
  await clickAndWaitAction('nativeHighlightWizardRetryButton', 'native_highlight_wizard_start');
  await clickAndWaitAction('nativeHighlightWizardRefreshButton', 'request_pdf_selection_probe');
  await setInput('knowledgeWorkspaceSearchInput', '任意文档');
  await clickAndWaitAction('knowledgeWorkspaceSearchButton', 'knowledge_index_search');
  await clickAndWaitAction('mindmapTargetRefreshButton', 'mindmap_target_status');
  await click('settingsButton');
  await click('contextButton');
  await delay();
  await click('contextScopeSelectionButton');
  await click('contextScopeDocumentButton');
  const documentScopeButton = byId('contextScopeDocumentButton');
  const contextScopeAfterClicks = documentScopeButton && documentScopeButton.getAttribute('aria-pressed') === 'true' ? 'document' : '';
  await setInput('fileSearchRootsInput', '/tmp/codex-ui-action-root');
  await clickAndWaitAction('saveFileSearchRootsButton', 'settings_update');
  await clickAndWaitAction('updateCheckButton', 'update_check');
  await clickAndWaitAction('updateInstallButton', 'open_url');
  await clickAndWaitAction('permissionDiagnoseButton', 'diagnose_permissions');
  await clickAndWaitAction('openPermissionSettingsButton', 'open_full_disk_access_settings');
  await clickAndWaitAction('cacheCurrentPdfButton', 'request_pdf_cache');
  await clickAndWaitAction('nativeCapabilitiesRefreshButton', 'request_native_capability_probe');
  await clickAndWaitAction('healthCheckButton', 'health');
  await clickAndWaitAction('aiBackendProbeButton', 'ai_backend_probe');
  await clickAndWaitAction('uiFunctionalAcceptanceButton', 'ui_functional_acceptance_summary');
  await clickAndWaitAction('realMnRuntimeSafeEvidenceButton', 'request_native_capability_probe');
  await clickAndWaitAction('realMnRepair-refresh_native_capabilities', 'request_native_capability_probe');
  await clickAndWaitAction('realMnRepair-run_native_highlight_wizard', 'native_highlight_wizard_start');
  const uiFunctionalLineText = byId('uiFunctionalAcceptanceLine') ? byId('uiFunctionalAcceptanceLine').textContent : '';
  const uiFunctionalDetailText = byId('uiFunctionalAcceptanceDetail') ? byId('uiFunctionalAcceptanceDetail').textContent : '';
  await clickAndWaitAction('logsRefreshButton', 'logs_recent');
  await click('configBackButton');
  await clickAndWaitAction('conversationHistoryButton', 'conversation_list');
  await clickAndWaitAction('conversationHistoryObjectButton', 'conversation_list');
  await clickAndWaitAction('conversationHistoryAllButton', 'conversation_list');
  await click('conversationHistoryCloseButton');
  const prompt = byId('promptInput');
  if (prompt && !prompt.disabled && typeof prompt.focus === 'function') prompt.focus();
  await delay();
  const activeElement = document.activeElement;
  const activeTag = activeElement ? String(activeElement.tagName || '').toLowerCase() : '';
  const activeElementRepeatBlocking =
    !!activeElement &&
    activeElement !== document.body &&
    activeTag !== 'textarea' &&
    activeTag !== 'input' &&
    activeElement.isContentEditable !== true;
  const sendButtonRect = rectOf('sendButton');
  const composerRect = rectOf('commandPaneComposer');
  const finalUiState = {
    settingsHidden: classHidden('configPage'),
    historyHidden: classHidden('conversationHistoryPage'),
    activeProductMode: shell ? shell.getAttribute('data-product-mode') : '',
    commandPaneVisible: visible('commandPanePanel'),
    composerVisible: visible('commandPaneComposer'),
    composerWithinViewport: rectWithinViewport(composerRect),
    sendButtonVisible: visible('sendButton'),
    sendButtonWithinViewport: rectWithinViewport(sendButtonRect),
    promptUsable: !!(prompt && !prompt.disabled && visible('promptInput')),
    activeElementRepeatBlocking: activeElementRepeatBlocking,
    activeElementId: activeElement ? (activeElement.id || activeElement.tagName || '') : ''
  };
  const historyText = byId('liveHistory') ? byId('liveHistory').textContent : '';
  const statusText = byId('statusPill') ? byId('statusPill').textContent : '';
  const calls = window.__codexActionCalls || [];
  const bridgeCalls = window.__codexBridgeCalls || [];
  return {
    clicked: clicked,
    actions: calls.map(call => call.action),
    bridgeActions: bridgeCalls.map(call => call.path),
    requestCount: calls.length,
    connectionFailureVisible: /Companion 未运行|无法连接 127\.0\.0\.1:48761/.test(historyText + '\n' + statusText),
    statusText: statusText,
    promptClearedAfterSend: promptClearedAfterSend,
    enterSubmitted: enterSubmitted,
    contextScopeAfterClicks: contextScopeAfterClicks,
    buttonActionDeltas: buttonActionDeltas,
    relationEditorOpened: relationEditorOpened,
    relationEditorClosedAfterCancel: relationEditorClosedAfterCancel,
    uiFunctionalLineText: uiFunctionalLineText,
    uiFunctionalDetailText: uiFunctionalDetailText,
    finalUiState: finalUiState
  };
})()
"""

BROWSER_WRITE_ACTION_STUB_CLICK_SCRIPT = r"""
(async function() {
  const delay = () => new Promise(resolve => window.setTimeout(resolve, 140));
  const byId = id => document.getElementById(id);
  const shell = byId('aiChatShell');
  const clicked = {};
  const calls = () => window.__codexActionCalls || [];
  const bridgeCalls = () => window.__codexBridgeCalls || [];
  const actionCount = action => calls().filter(call => call.action === action).length;
  const bridgeCount = action => bridgeCalls().filter(call => call.path === action).length;
  const visible = id => {
    const el = byId(id);
    if (!el) return false;
    const style = window.getComputedStyle(el);
    const hasBox = Boolean(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
    return hasBox && !el.classList.contains('hidden') && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const rectOf = id => {
    const el = byId(id);
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return {
      top: Math.round(r.top),
      right: Math.round(r.right),
      bottom: Math.round(r.bottom),
      left: Math.round(r.left),
      width: Math.round(r.width),
      height: Math.round(r.height)
    };
  };
  const rectWithinViewport = rect => {
    if (!rect || rect.width <= 0 || rect.height <= 0) return false;
    return rect.top >= 0 && rect.left >= 0 && rect.bottom <= window.innerHeight && rect.right <= window.innerWidth;
  };
  const classHidden = id => {
    const el = byId(id);
    return !el || el.classList.contains('hidden');
  };
  const waitFor = async predicate => {
    for (let i = 0; i < 25; i++) {
      if (predicate()) return true;
      await delay();
    }
    return false;
  };
  const waitForAction = action => waitFor(() => actionCount(action) > 0);
  const waitForBridge = action => waitFor(() => bridgeCount(action) > 0);
  const waitForBridgeCount = (action, count) => waitFor(() => bridgeCount(action) >= count);
  const waitForSelector = selector => waitFor(() => !!document.querySelector(selector));
  const clickElement = async (key, el) => {
    clicked[key] = !!(el && !el.disabled);
    if (el && !el.disabled) {
      el.click();
      await delay();
      return true;
    }
    await delay();
    return false;
  };
  const click = (key, id) => clickElement(key, byId(id || key));
  const clickSelector = (key, selector) => clickElement(key, document.querySelector(selector));
  if (window.CodexPanel && typeof window.CodexPanel.setContext === 'function') {
    window.CodexPanel.setContext({
      topicid: 'stub-topic',
      notebookid: 'stub-topic',
      bookmd5: 'stub-book',
      docmd5: 'stub-book',
      documentTitle: '任意文档 Stub UI 验收.pdf'
    });
  }
  if (window.CodexPanel && typeof window.CodexPanel.setReply === 'function') {
    window.CodexPanel.setReply({text: '任意文档回答：核心问题、方法路线、验证证据。'});
  }
  await waitForSelector('.reply-mindmap-tree-button');
  await clickSelector('replyMindmapTreeButton', '.reply-mindmap-tree-button');
  await waitForAction('generate_mindmap');
  await waitForAction('draft_save');
  await waitForBridge('write_draft');

  if (window.CodexPanel && typeof window.CodexPanel.setAiEditOperationReady === 'function') {
    window.CodexPanel.setAiEditOperationReady({
      id: 'draft-ui-reject',
      transactionId: 'tx-ui-reject',
      original_action: 'generate_mindmap',
      has_mindmap: true,
      createdCount: 1,
      createdNoteIds: ['N-ui-reject'],
      operation_manifest: {operationCount: 1, dryRun: {status: 'ready'}}
    });
  }
  await waitForSelector('.ai-edit-operation[data-transaction-id="tx-ui-reject"] .ai-edit-review-queue');
  await clickSelector('aiEditReviewQueueButton', '.ai-edit-operation[data-transaction-id="tx-ui-reject"] .ai-edit-review-queue');
  await waitForAction('review_queue_add');
  await clickSelector('aiEditRejectButton', '.ai-edit-operation[data-transaction-id="tx-ui-reject"] .ai-edit-reject');
  await waitForBridge('reject_ai_edit_transaction');

  if (window.CodexPanel && typeof window.CodexPanel.setAiEditOperationReady === 'function') {
    window.CodexPanel.setAiEditOperationReady({
      id: 'draft-ui-accept',
      transactionId: 'tx-ui-accept',
      original_action: 'generate_mindmap',
      has_mindmap: true,
      createdCount: 1,
      createdNoteIds: ['N-ui-accept'],
      operation_manifest: {operationCount: 1, dryRun: {status: 'ready'}}
    });
  }
  await waitForSelector('.ai-edit-operation[data-transaction-id="tx-ui-accept"] .ai-edit-accept');
  await clickSelector('aiEditAcceptButton', '.ai-edit-operation[data-transaction-id="tx-ui-accept"] .ai-edit-accept');
  await waitForBridge('accept_ai_edit_transaction');

  await click('mindmapStudioPreviewDiffButton');
  await waitForAction('mindmap_diff_preview');
  await waitForSelector('.mindmap-diff-operation');
  await click('mindmapStudioApplySelectedButton');
  await waitForAction('request_mindmap_diff_apply');

  if (window.CodexPanel && typeof window.CodexPanel.setAiEditTransactionStatus === 'function') {
    window.CodexPanel.setAiEditTransactionStatus({
      schema: 'codex.mn.aiEditTransactionStatus.v1',
      available: true,
      summary: 'stub transaction center',
      latest: {
        transactionId: 'tx-ui-write',
        status: 'created_pending_user_decision',
        createdNoteIds: ['N-ui-write'],
        createdCount: 1,
        objectRef: {
          objectId: 'mnobj:doc:ui-actions',
          kind: 'document',
          title: '任意文档 Stub UI 验收.pdf'
        }
      },
      verification: {
        transactionId: 'tx-ui-write',
        status: 'pending',
        summary: 'stub verification pending native probe',
        createdNoteIds: ['N-ui-write'],
        remainingNoteIds: ['N-ui-write'],
        createdCount: 1,
        remainingCount: 1,
        nextActions: [
          {
            id: 'request_object_existence_probe',
            action: 'request_mn_object_existence_probe',
            noteIds: ['N-ui-write']
          }
        ],
        residualProof: {
          schema: 'codex.mn.residualProof.v1',
          status: 'pending',
          remainingCount: 1,
          objects: [
            {
              noteId: 'N-ui-write',
              expectedState: 'created_pending_user_decision',
              actualState: 'unknown',
              residual: true,
              verificationLevel: 'native_probe_missing'
            }
          ]
        }
      }
    });
  }
  await click('mindmapStudioVerifyButton');
  await waitForAction('ai_edit_transaction_verify');
  const rejectBridgeBeforeStudioRollback = bridgeCount('reject_ai_edit_transaction');
  await click('mindmapStudioRollbackButton');
  await waitForBridgeCount('reject_ai_edit_transaction', rejectBridgeBeforeStudioRollback + 1);
  await waitForSelector('.ai-edit-transaction-verify');
  await clickSelector('transactionVerifyButton', '.ai-edit-transaction-verify');
  await waitForAction('ai_edit_transaction_verify');
  await clickSelector('transactionEvidenceButton', '.ai-edit-transaction-evidence');
  await waitForAction('ai_edit_transaction_get');
  await clickSelector('transactionProbeButton', '.ai-edit-transaction-probe');
  await waitForAction('request_mn_object_existence_probe');
  const prompt = byId('promptInput');
  if (prompt && !prompt.disabled && typeof prompt.focus === 'function') prompt.focus();
  await delay();
  const activeElement = document.activeElement;
  const activeTag = activeElement ? String(activeElement.tagName || '').toLowerCase() : '';
  const activeElementRepeatBlocking =
    !!activeElement &&
    activeElement !== document.body &&
    activeTag !== 'textarea' &&
    activeTag !== 'input' &&
    activeElement.isContentEditable !== true;
  const sendButtonRect = rectOf('sendButton');
  const composerRect = rectOf('commandPaneComposer');
  const finalUiState = {
    settingsHidden: classHidden('configPage'),
    historyHidden: classHidden('conversationHistoryPage'),
    activeProductMode: shell ? shell.getAttribute('data-product-mode') : '',
    commandPaneVisible: visible('commandPanePanel'),
    composerVisible: visible('commandPaneComposer'),
    composerWithinViewport: rectWithinViewport(composerRect),
    sendButtonVisible: visible('sendButton'),
    sendButtonWithinViewport: rectWithinViewport(sendButtonRect),
    promptUsable: !!(prompt && !prompt.disabled && visible('promptInput')),
    activeElementRepeatBlocking: activeElementRepeatBlocking,
    activeElementId: activeElement ? (activeElement.id || activeElement.tagName || '') : ''
  };
  const historyText = byId('liveHistory') ? byId('liveHistory').textContent : '';
  const statusText = byId('statusPill') ? byId('statusPill').textContent : '';
  return {
    clicked: clicked,
    actions: calls().map(call => call.action),
    bridgeActions: bridgeCalls().map(call => call.path),
    requestCount: calls().length,
    bridgeRequestCount: bridgeCalls().length,
    connectionFailureVisible: /Companion 未运行|无法连接 127\.0\.0\.1:48761/.test(historyText + '\n' + statusText),
    statusText: statusText,
    finalUiState: finalUiState
  };
})()
"""


def run_browser_interaction_check(root: Path, *, browser_path: str = "", timeout_seconds: float = 12.0) -> dict[str, Any]:
    browser = find_browser_executable(browser_path)
    if not browser:
        return fail_check(
            "webview_browser_interaction",
            "WebView browser interaction",
            ["no supported headless browser found"],
            {"candidatePaths": BROWSER_CANDIDATE_PATHS},
        )
    web_root = root / "extension/codex.mn.assistant/web"
    if not web_root.is_dir():
        return fail_check(
            "webview_browser_interaction",
            "WebView browser interaction",
            [f"missing web root: {web_root}"],
            {"webRoot": str(web_root)},
        )
    http_port = free_local_port()
    debug_port = free_local_port()
    with tempfile.TemporaryDirectory() as profile:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(http_port), "--bind", "127.0.0.1"],
            cwd=str(web_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        browser_proc: subprocess.Popen[str] | None = None
        session: DevToolsSession | None = None
        try:
            wait_for_static_server(http_port)
            browser_proc = subprocess.Popen(
                [
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-background-networking",
                    "--disable-component-update",
                    f"--remote-debugging-port={debug_port}",
                    f"--user-data-dir={profile}",
                    "about:blank",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ws_url = wait_for_devtools_page_ws(debug_port, timeout_seconds=timeout_seconds)
            session = DevToolsSession(ws_url, timeout_seconds=timeout_seconds)
            session.command("Page.enable")
            session.command("Runtime.enable")
            url = f"http://127.0.0.1:{http_port}/index.html"

            def navigate_and_wait(width: int, height: int) -> str:
                session.command(
                    "Emulation.setDeviceMetricsOverride",
                    {"width": width, "height": height, "deviceScaleFactor": 1, "mobile": False},
                )
                session.command("Page.navigate", {"url": url})
                deadline = time.time() + timeout_seconds
                state = ""
                while time.time() < deadline:
                    state = str(session.evaluate("document.readyState") or "")
                    if state == "complete":
                        break
                    time.sleep(0.1)
                return state

            wide_ready_state = navigate_and_wait(1280, 720)
            wide_result = session.evaluate(BROWSER_INTERACTION_SCRIPT)
            wide_layout = wide_result.get("responsiveLayout") if isinstance(wide_result, dict) else {}
            wide_header_spacing = wide_result.get("notebookHeaderSpacing") if isinstance(wide_result, dict) else {}
            session.command(
                "Page.navigate",
                {"url": "about:blank"},
            )
            medium_ready_state = navigate_and_wait(840, 640)
            medium_result = session.evaluate(BROWSER_INTERACTION_SCRIPT)
            medium_layout = medium_result.get("responsiveLayout") if isinstance(medium_result, dict) else {}
            session.command(
                "Page.navigate",
                {"url": "about:blank"},
            )
            ready_state = navigate_and_wait(430, 560)
            result = session.evaluate(BROWSER_INTERACTION_SCRIPT)
            if not isinstance(result, dict):
                return fail_check(
                    "webview_browser_interaction",
                    "WebView browser interaction",
                    [f"interaction script returned non-object: {type(result).__name__}"],
                    {"browser": browser, "url": url, "readyState": ready_state},
                )
            result["wideLayout"] = wide_layout
            result["wideHeaderSpacing"] = wide_header_spacing
            result["mediumLayout"] = medium_layout
            check = check_browser_interaction_result(result)
            check["evidence"]["browser"] = browser
            check["evidence"]["url"] = url
            check["evidence"]["readyState"] = ready_state
            check["evidence"]["wideReadyState"] = wide_ready_state
            check["evidence"]["mediumReadyState"] = medium_ready_state
            return check
        except Exception as exc:
            return fail_check(
                "webview_browser_interaction",
                "WebView browser interaction",
                [str(exc)],
                {"browser": browser, "httpPort": http_port, "debugPort": debug_port},
            )
        finally:
            if session is not None:
                session.close()
            if browser_proc is not None:
                browser_proc.terminate()
                try:
                    browser_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    browser_proc.kill()
                    browser_proc.wait(timeout=2)
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)


def run_browser_action_stub_check(root: Path, *, browser_path: str = "", timeout_seconds: float = 12.0) -> dict[str, Any]:
    browser = find_browser_executable(browser_path)
    if not browser:
        return fail_check(
            "webview_browser_actions",
            "WebView browser actions",
            ["no supported headless browser found"],
            {"candidatePaths": BROWSER_CANDIDATE_PATHS},
        )
    web_root = root / "extension/codex.mn.assistant/web"
    if not web_root.is_dir():
        return fail_check(
            "webview_browser_actions",
            "WebView browser actions",
            [f"missing web root: {web_root}"],
            {"webRoot": str(web_root)},
        )
    http_port = free_local_port()
    debug_port = free_local_port()
    responses = {action: browser_base_response_for_action(action) for action in BROWSER_ACTION_REQUIRED_ACTIONS}
    with tempfile.TemporaryDirectory() as profile:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(http_port), "--bind", "127.0.0.1"],
            cwd=str(web_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        browser_proc: subprocess.Popen[str] | None = None
        session: DevToolsSession | None = None
        try:
            wait_for_static_server(http_port)
            browser_proc = subprocess.Popen(
                [
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-background-networking",
                    "--disable-component-update",
                    f"--remote-debugging-port={debug_port}",
                    f"--user-data-dir={profile}",
                    "about:blank",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ws_url = wait_for_devtools_page_ws(debug_port, timeout_seconds=timeout_seconds)
            session = DevToolsSession(ws_url, timeout_seconds=timeout_seconds)
            session.command("Page.enable")
            session.command("Runtime.enable")
            session.command("Page.addScriptToEvaluateOnNewDocument", {"source": browser_action_stub_script(responses)})
            url = f"http://127.0.0.1:{http_port}/index.html"
            session.command("Page.navigate", {"url": url})
            deadline = time.time() + timeout_seconds
            ready_state = ""
            while time.time() < deadline:
                ready_state = str(session.evaluate("document.readyState") or "")
                if ready_state == "complete":
                    break
                time.sleep(0.1)
            session.evaluate(browser_action_stub_script(responses))
            time.sleep(1.0)
            result = session.evaluate(BROWSER_ACTION_STUB_CLICK_SCRIPT)
            if not isinstance(result, dict):
                return fail_check(
                    "webview_browser_actions",
                    "WebView browser actions",
                    [f"action stub script returned non-object: {type(result).__name__}"],
                    {"browser": browser, "url": url, "readyState": ready_state},
                )
            check = check_browser_action_stub_result(result)
            check["evidence"]["browser"] = browser
            check["evidence"]["url"] = url
            check["evidence"]["readyState"] = ready_state
            return check
        except Exception as exc:
            return fail_check(
                "webview_browser_actions",
                "WebView browser actions",
                [str(exc)],
                {"browser": browser, "httpPort": http_port, "debugPort": debug_port},
            )
        finally:
            if session is not None:
                session.close()
            if browser_proc is not None:
                browser_proc.terminate()
                try:
                    browser_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    browser_proc.kill()
                    browser_proc.wait(timeout=2)
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)


def run_browser_write_action_stub_check(root: Path, *, browser_path: str = "", timeout_seconds: float = 12.0) -> dict[str, Any]:
    browser = find_browser_executable(browser_path)
    if not browser:
        return fail_check(
            "webview_browser_write_actions",
            "WebView browser write actions",
            ["no supported headless browser found"],
            {"candidatePaths": BROWSER_CANDIDATE_PATHS},
        )
    web_root = root / "extension/codex.mn.assistant/web"
    if not web_root.is_dir():
        return fail_check(
            "webview_browser_write_actions",
            "WebView browser write actions",
            [f"missing web root: {web_root}"],
            {"webRoot": str(web_root)},
        )
    http_port = free_local_port()
    debug_port = free_local_port()
    response_actions = sorted(
        set(BROWSER_ACTION_REQUIRED_ACTIONS)
        | set(BROWSER_WRITE_REQUIRED_COMPANION_ACTIONS)
        | {"request_pdf_cache", "mindmap_target_status", "queue_status", "web_busy_update"}
    )
    responses = {action: browser_base_response_for_action(action) for action in response_actions}
    with tempfile.TemporaryDirectory() as profile:
        server = subprocess.Popen(
            [sys.executable, "-m", "http.server", str(http_port), "--bind", "127.0.0.1"],
            cwd=str(web_root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        browser_proc: subprocess.Popen[str] | None = None
        session: DevToolsSession | None = None
        try:
            wait_for_static_server(http_port)
            browser_proc = subprocess.Popen(
                [
                    browser,
                    "--headless=new",
                    "--disable-gpu",
                    "--no-first-run",
                    "--disable-background-networking",
                    "--disable-component-update",
                    f"--remote-debugging-port={debug_port}",
                    f"--user-data-dir={profile}",
                    "about:blank",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ws_url = wait_for_devtools_page_ws(debug_port, timeout_seconds=timeout_seconds)
            session = DevToolsSession(ws_url, timeout_seconds=timeout_seconds)
            session.command("Page.enable")
            session.command("Runtime.enable")
            session.command("Page.addScriptToEvaluateOnNewDocument", {"source": browser_action_stub_script(responses)})
            url = f"http://127.0.0.1:{http_port}/index.html"
            session.command("Page.navigate", {"url": url})
            deadline = time.time() + timeout_seconds
            ready_state = ""
            while time.time() < deadline:
                ready_state = str(session.evaluate("document.readyState") or "")
                if ready_state == "complete":
                    break
                time.sleep(0.1)
            session.evaluate(browser_action_stub_script(responses))
            time.sleep(1.0)
            result = session.evaluate(BROWSER_WRITE_ACTION_STUB_CLICK_SCRIPT)
            if not isinstance(result, dict):
                return fail_check(
                    "webview_browser_write_actions",
                    "WebView browser write actions",
                    [f"write action stub script returned non-object: {type(result).__name__}"],
                    {"browser": browser, "url": url, "readyState": ready_state},
                )
            check = check_browser_write_action_stub_result(result)
            check["evidence"]["browser"] = browser
            check["evidence"]["url"] = url
            check["evidence"]["readyState"] = ready_state
            return check
        except Exception as exc:
            return fail_check(
                "webview_browser_write_actions",
                "WebView browser write actions",
                [str(exc)],
                {"browser": browser, "httpPort": http_port, "debugPort": debug_port},
            )
        finally:
            if session is not None:
                session.close()
            if browser_proc is not None:
                browser_proc.terminate()
                try:
                    browser_proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    browser_proc.kill()
                    browser_proc.wait(timeout=2)
            server.terminate()
            try:
                server.wait(timeout=2)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=2)


def safe_action_names(actions: list[dict[str, Any]]) -> list[str]:
    return [str(item.get("action") or "") for item in actions if isinstance(item, dict)]


def check_arbitrary_document_workspace(workspace: dict[str, Any], expected_title: str) -> dict[str, Any]:
    data = workspace.get("notebookWorkspace") if isinstance(workspace.get("notebookWorkspace"), dict) else {}
    primary_actions = data.get("primaryActions") if isinstance(data.get("primaryActions"), list) else []
    actions_by_id = {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}
    problems: list[str] = []
    if not workspace.get("ok"):
        problems.append("notebook_workspace returned ok=false")
    if data.get("schema") != "codex.mn.notebookWorkspace.v1":
        problems.append("missing notebook workspace schema")
    if str(data.get("documentTitle") or "") != expected_title:
        problems.append("document title did not survive arbitrary-document payload")
    for action_id in ["scan_mn_objects", "read_mindmap_tree", "open_source_registry", "open_card_factory", "open_workflow_builder"]:
        if action_id not in actions_by_id:
            problems.append(f"missing primary action {action_id}")
    if actions_by_id.get("scan_mn_objects", {}).get("disabled"):
        problems.append("scan_mn_objects is disabled despite explicit arbitrary topicid")
    if actions_by_id.get("read_mindmap_tree", {}).get("disabled"):
        problems.append("read_mindmap_tree is disabled despite explicit arbitrary topicid")
    return check_from_problems(
        "arbitrary_document_workspace",
        "Arbitrary document workspace",
        problems,
        {
            "documentTitle": data.get("documentTitle"),
            "primaryActionIds": [str(item.get("id") or "") for item in primary_actions],
        },
    )


def check_notebook_workspace_kernels(workspace: dict[str, Any]) -> dict[str, Any]:
    data = workspace.get("notebookWorkspace") if isinstance(workspace.get("notebookWorkspace"), dict) else {}
    workflow_workspace = workspace.get("workflowWorkspace") if isinstance(workspace.get("workflowWorkspace"), dict) else {}
    matrix = data.get("knowledgeMatrix") if isinstance(data.get("knowledgeMatrix"), dict) else {}
    intake = data.get("objectIntake") if isinstance(data.get("objectIntake"), dict) else {}
    composer = data.get("objectTaskComposer") if isinstance(data.get("objectTaskComposer"), dict) else {}
    runbook = data.get("runbook") if isinstance(data.get("runbook"), dict) else {}
    workflow = workflow_workspace.get("workflowBuilderBoard") if isinstance(workflow_workspace.get("workflowBuilderBoard"), dict) else {}
    axes = matrix.get("axes") if isinstance(matrix.get("axes"), list) else []
    routes = intake.get("routes") if isinstance(intake.get("routes"), list) else []
    tasks = composer.get("tasks") if isinstance(composer.get("tasks"), list) else []
    steps = runbook.get("steps") if isinstance(runbook.get("steps"), list) else []
    lanes = workflow.get("lanes") if isinstance(workflow.get("lanes"), list) else []
    problems: list[str] = []
    expected = {
        "knowledgeMatrix": (matrix.get("schema"), "codex.mn.knowledgeConsoleMatrix.v1"),
        "objectIntake": (intake.get("schema"), "codex.mn.objectIntake.v1"),
        "objectTaskComposer": (composer.get("schema"), "codex.mn.objectTaskComposer.v1"),
        "runbook": (runbook.get("schema"), "codex.mn.notebookRunbook.v1"),
        "workflowBuilderBoard": (workflow.get("schema"), "codex.mn.workflowBuilderBoard.v1"),
    }
    for name, (actual, schema) in expected.items():
        if actual != schema:
            problems.append(f"{name} schema mismatch: {actual}")
    if len(axes) != 7:
        problems.append(f"expected 7 matrix axes, got {len(axes)}")
    if len(routes) != 7:
        problems.append(f"expected 7 intake routes, got {len(routes)}")
    if len(tasks) != 7:
        problems.append(f"expected 7 task drafts, got {len(tasks)}")
    if len(steps) != 8:
        problems.append(f"expected 8 runbook steps, got {len(steps)}")
    if len(lanes) < 4:
        problems.append(f"expected at least 4 workflow board lanes, got {len(lanes)}")
    auto_actions = safe_action_names(runbook.get("autoPlan", {}).get("actions") if isinstance(runbook.get("autoPlan"), dict) else [])
    forbidden = {"draft_accept", "acceptMindmapDiff", "request_mindmap_diff_apply"}
    unsafe = sorted(set(auto_actions) & forbidden)
    if unsafe:
        problems.append(f"autoPlan contains write-like actions: {unsafe}")
    return check_from_problems(
        "notebook_workspace_kernels",
        "Notebook Workspace kernels",
        problems,
        {
            "matrixAxisCount": len(axes),
            "intakeRouteCount": len(routes),
            "taskDraftCount": len(tasks),
            "runbookStepCount": len(steps),
            "workflowLaneCount": len(lanes),
            "autoPlanActions": auto_actions,
        },
    )


def check_workspace_surface_actions(workspace: dict[str, Any]) -> dict[str, Any]:
    data = workspace.get("notebookWorkspace") if isinstance(workspace.get("notebookWorkspace"), dict) else {}
    primary_actions = data.get("primaryActions") if isinstance(data.get("primaryActions"), list) else []
    surfaces = {str(item.get("surface") or "") for item in primary_actions if isinstance(item, dict)}
    missing_surfaces = [surface for surface in REQUIRED_WORKSPACE_SURFACES if surface not in surfaces and surface not in {"knowledge_graph"}]
    # Knowledge Graph is reached through the navigator and object graph rather than a primary notebook action.
    return check_from_problems(
        "workspace_surface_actions",
        "Workspace surface actions",
        [f"missing workspace action surface {item}" for item in missing_surfaces],
        {"surfaces": sorted(surfaces), "missing": missing_surfaces},
    )


def check_native_scope_guards(companion: Any) -> dict[str, Any]:
    companion.read_defaults = lambda key: ""
    workspace = companion.handle_action({"action": "notebook_workspace"})
    data = workspace.get("notebookWorkspace") if isinstance(workspace.get("notebookWorkspace"), dict) else {}
    primary_actions = data.get("primaryActions") if isinstance(data.get("primaryActions"), list) else []
    actions_by_id = {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}
    matrix = data.get("knowledgeMatrix") if isinstance(data.get("knowledgeMatrix"), dict) else {}
    axes = {str(item.get("id") or ""): item for item in (matrix.get("axes") if isinstance(matrix.get("axes"), list) else []) if isinstance(item, dict)}
    runbook = data.get("runbook") if isinstance(data.get("runbook"), dict) else {}
    problems: list[str] = []
    for action_id in ["scan_mn_objects", "read_mindmap_tree"]:
        if not actions_by_id.get(action_id, {}).get("disabled"):
            problems.append(f"{action_id} is not disabled without topicid")
    for axis_id in ["mn_objects", "mindmap_baseline"]:
        if axes.get(axis_id, {}).get("status") != "blocked":
            problems.append(f"{axis_id} axis is not blocked without topicid")
    auto_plan = runbook.get("autoPlan") if isinstance(runbook.get("autoPlan"), dict) else {}
    if auto_plan.get("canRun"):
        problems.append("runbook autoPlan can run without topicid")
    return check_from_problems(
        "native_scope_guards",
        "Native scope guards",
        problems,
        {
            "scanDisabled": bool(actions_by_id.get("scan_mn_objects", {}).get("disabled")),
            "readTreeDisabled": bool(actions_by_id.get("read_mindmap_tree", {}).get("disabled")),
            "noScopeAutoPlanCanRun": bool(auto_plan.get("canRun")),
            "axisStatuses": {axis_id: axes.get(axis_id, {}).get("status") for axis_id in ["mn_objects", "mindmap_baseline"]},
        },
    )


def evaluate_ui_functional_acceptance(
    *,
    root: Path = ROOT,
    workspace_home: Path | None = None,
    document_payload: dict[str, Any] | None = None,
    browser_render: bool = False,
    browser_interaction: bool = False,
    browser_actions: bool = False,
    browser_write_actions: bool = False,
    browser_path: str = "",
    browser_timeout: float = 12.0,
) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    own_temp: tempfile.TemporaryDirectory[str] | None = None
    if workspace_home is None:
        own_temp = tempfile.TemporaryDirectory()
        workspace_home = Path(own_temp.name)
    workspace_home = Path(workspace_home).expanduser()
    workspace_home.mkdir(parents=True, exist_ok=True)

    try:
        companion = load_companion_module(root, workspace_home)
        companion.read_defaults = lambda key: ""
        payload = document_payload or default_document_payload(
            "UI-ACCEPTANCE-TOPIC",
            "ui-acceptance-book",
            "任意文档 UI 功能验收.pdf",
        )
        workspace = companion.handle_action({**payload, "action": "notebook_workspace"})
        checks = [
            check_static_controls(root),
            check_behavior_markers(root),
            check_button_coverage(root),
            check_arbitrary_document_workspace(workspace, str(payload.get("documentTitle") or "")),
            check_notebook_workspace_kernels(workspace),
            check_workspace_surface_actions(workspace),
            check_native_scope_guards(companion),
        ]
        if browser_render:
            checks.append(run_browser_render_check(root, browser_path=browser_path, timeout_seconds=browser_timeout))
        if browser_interaction:
            checks.append(run_browser_interaction_check(root, browser_path=browser_path, timeout_seconds=browser_timeout))
        if browser_actions:
            checks.append(run_browser_action_stub_check(root, browser_path=browser_path, timeout_seconds=browser_timeout))
        if browser_write_actions:
            checks.append(run_browser_write_action_stub_check(root, browser_path=browser_path, timeout_seconds=browser_timeout))
        ok = all(item.get("status") == "PASS" for item in checks)
        return {
            "schema": SCHEMA,
            "ok": ok,
            "root": str(root),
            "documentTitle": str(payload.get("documentTitle") or ""),
            "topicid": str(payload.get("topicid") or ""),
            "bookmd5": str(payload.get("bookmd5") or ""),
            "checks": checks,
            "problems": [
                problem
                for check in checks
                for problem in (check.get("problems") if isinstance(check.get("problems"), list) else [])
            ],
        }
    finally:
        if own_temp is not None:
            own_temp.cleanup()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run arbitrary-document UI functional acceptance for Codex Companion.")
    parser.add_argument("--root", default=str(ROOT), help="Companion source root.")
    parser.add_argument("--workspace-home", default="", help="Temporary CODEX_MN_COMPANION_HOME for deterministic module checks.")
    parser.add_argument("--topicid", default="UI-ACCEPTANCE-TOPIC")
    parser.add_argument("--bookmd5", default="ui-acceptance-book")
    parser.add_argument("--document-title", default="任意文档 UI 功能验收.pdf")
    parser.add_argument("--output", default="", help="Optional JSON report output path.")
    parser.add_argument("--browser-render", action="store_true", help="Render the WebView with a local headless browser and inspect the rendered DOM.")
    parser.add_argument("--browser-interaction", action="store_true", help="Drive local WebView clicks with the browser DevTools protocol.")
    parser.add_argument("--browser-actions", action="store_true", help="Stub Companion XHR and click UI action buttons to verify backend action wiring.")
    parser.add_argument("--browser-write-actions", action="store_true", help="Stub write/transaction paths and verify draft, mind-map Diff, transaction, and native bridge wiring.")
    parser.add_argument("--browser-path", default="", help="Optional Microsoft Edge/Chrome executable for browser checks.")
    parser.add_argument("--browser-timeout", type=float, default=12.0, help="Seconds to wait for headless browser DOM output.")
    args = parser.parse_args(argv)

    workspace_home = Path(args.workspace_home).expanduser() if args.workspace_home else None
    payload = default_document_payload(args.topicid, args.bookmd5, args.document_title)
    report = evaluate_ui_functional_acceptance(
        root=Path(args.root).expanduser(),
        workspace_home=workspace_home,
        document_payload=payload,
        browser_render=bool(args.browser_render),
        browser_interaction=bool(args.browser_interaction),
        browser_actions=bool(args.browser_actions),
        browser_write_actions=bool(args.browser_write_actions),
        browser_path=str(args.browser_path or ""),
        browser_timeout=float(args.browser_timeout),
    )
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
    if args.output:
        output = Path(args.output).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
