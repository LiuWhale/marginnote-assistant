from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "extension/codex.mn.assistant"
LIVE_ROOT = Path.home() / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
ROOT = SOURCE_ROOT if SOURCE_ROOT.exists() else LIVE_ROOT


class WebControlsStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "web/index.html").read_text(encoding="utf-8")
        self.js = (ROOT / "web/app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "web/app.css").read_text(encoding="utf-8")

    def test_visible_surface_is_object_operation_workbench(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="aiChatShell"',
            'id="knowledgeOsContractPanel"',
            'id="knowledgeOsContractTitle"',
            'id="knowledgeOsObjectLayer"',
            'id="knowledgeOsOperationLayer"',
            'id="knowledgeOsEvidenceLayer"',
            'id="modeSwitchBar"',
            'id="chatModeButton"',
            'id="agentWorkspaceModeButton"',
            'id="modeIntentLine"',
            'id="workspaceNavigator"',
            'id="workspaceNavigatorSummary"',
            'id="workspaceSurfaceSelect"',
            'id="workspaceNavigatorToggleButton"',
            'id="workspaceNavConsoleButton"',
            'id="workspaceNavMindmapStudioButton"',
            'id="workspaceNavCardFactoryButton"',
            'id="workspaceNavLedgerExplorerButton"',
            'id="workspaceNavKnowledgeGraphButton"',
            'id="workspaceNavWorkflowBuilderButton"',
            'id="workspaceNavSkillCenterButton"',
            'id="knowledgeConsolePanel"',
            'id="notebookWorkspacePanel"',
            'id="notebookWorkspaceTitle"',
            'id="notebookWorkspaceSummary"',
            'id="notebookWorkspaceRefreshButton"',
            'id="notebookWorkspaceDetails"',
            'id="notebookWorkspaceFocus"',
            'id="notebookWorkspaceObjectCount"',
            'id="notebookWorkspaceMindmap"',
            'id="notebookWorkspaceReview"',
            'id="notebookWorkspaceWorkflow"',
            'id="notebookWorkspaceLedger"',
            'id="notebookWorkspaceActions"',
            'id="notebookKnowledgeMatrix"',
            'id="notebookKnowledgeMatrixSummary"',
            'id="notebookKnowledgeMatrixList"',
            'id="notebookObjectIntake"',
            'id="notebookObjectIntakeSummary"',
            'id="notebookObjectIntakeRoutes"',
            'id="notebookObjectTaskComposer"',
            'id="notebookObjectTaskComposerSummary"',
            'id="notebookObjectTaskComposerList"',
            'id="sourceRegistryPanel"',
            'id="notebookWorkspaceRunbook"',
            'id="notebookWorkspaceRunbookSummary"',
            'id="notebookWorkspaceRunbookAutoButton"',
            'id="notebookWorkspaceRunbookContinueButton"',
            'id="notebookWorkspaceRunbookList"',
            'id="commandPanePanel"',
            'id="commandPaneHeader"',
            'id="commandPaneStatus"',
            'id="commandPaneToggleButton"',
            'id="commandPaneBody"',
            'id="commandPaneComposer"',
            'id="workbenchTabs"',
            'id="workbenchTabObject"',
            'id="workbenchTabOperation"',
            'id="workbenchTabKnowledge"',
            'id="workbenchTabWorkflow"',
            'id="studioCanvasPanel"',
            'id="workbenchLayout"',
            'id="objectWorkspacePanel"',
            'id="operationWorkspacePanel"',
            'id="knowledgeWorkspacePanel"',
            'id="workflowWorkspacePanel"',
            'id="objectWorkspaceTitle"',
            'id="objectWorkspaceMeta"',
            'id="objectWorkspaceScope"',
            'id="objectWorkspaceObjectId"',
            'id="objectWorkspaceSourceRef"',
            'id="objectRiskPanel"',
            'id="objectRiskSummary"',
            'id="objectRiskList"',
            'id="objectWorkspaceActions"',
            'id="objectWorkspaceEvidence"',
            'id="objectGraphPanel"',
            'id="objectGraphRefreshButton"',
            'id="objectGraphRelationAddButton"',
            'id="objectGraphSummary"',
            'id="objectGraphNodes"',
            'id="objectGraphRelationEditor"',
            'id="objectGraphRelationTargetInput"',
            'id="objectGraphRelationTypeInput"',
            'id="objectGraphRelationLabelInput"',
            'id="objectGraphRelationNoteInput"',
            'id="objectGraphRelationSaveButton"',
            'id="objectGraphRelationCancelButton"',
            'id="objectActivityPanel"',
            'id="objectActivityRefreshButton"',
            'id="objectActivitySummary"',
            'id="objectActivityList"',
            'id="operationLedgerDrawer"',
            'id="operationLedgerPanel"',
            'id="operationLedgerRefreshButton"',
            'id="operationLedgerSummary"',
            'id="operationLedgerTypeFilterSelect"',
            'id="operationLedgerStatusFilterInput"',
            'id="operationLedgerSearchInput"',
            'id="operationLedgerFilterButton"',
            'id="operationLedgerList"',
            'id="operationLedgerDetailPanel"',
            'id="operationLedgerDetailTitle"',
            'id="operationLedgerDetailMeta"',
            'id="operationLedgerDetailEvidence"',
            'id="operationLedgerDetailCloseButton"',
            'id="operationWorkspaceTitle"',
            'id="operationWorkspaceMeta"',
            'id="verificationReportPanel"',
            'id="verificationReportRefreshButton"',
            'id="verificationReportSummary"',
            'id="verificationReportCounts"',
            'id="verificationReportList"',
            'id="operationCompilerPanel"',
            'id="operationCompilerSummary"',
            'id="operationPlanStats"',
            'id="operationCompilerChecks"',
            'id="operationDryRunDetails"',
            'id="operationWorkspaceNextActions"',
            'id="mindmapStudioPanel"',
            'id="mindmapStudioSummary"',
            'id="mindmapStudioCurrentTree"',
            'id="mindmapStudioDiffStage"',
            'id="mindmapStudioApplyStage"',
            'id="mindmapStudioTransactionStage"',
            'id="mindmapStudioReadTreeButton"',
            'id="mindmapStudioPreviewDiffButton"',
            'id="mindmapStudioApplySelectedButton"',
            'id="mindmapStudioVerifyButton"',
            'id="mindmapStudioRollbackButton"',
            'id="mindmapStudioStatusLine"',
            'id="knowledgeWorkspaceTitle"',
            'id="knowledgeWorkspaceSummary"',
            'id="knowledgeWorkspaceScope"',
            'id="knowledgeWorkspaceEntities"',
            'id="knowledgeWorkspaceRelations"',
            'id="knowledgeWorkspaceActions"',
            'id="workflowWorkspaceTitle"',
            'id="workflowWorkspaceSummary"',
            'id="workflowWorkspaceRuns"',
            'id="workflowBuilderBoardPanel"',
            'id="workflowBuilderBoardSummary"',
            'id="workflowBuilderBoardLanes"',
            'id="externalGatewayPanel"',
            'id="workflowWorkspaceGateway"',
            'id="skillCenterPanel"',
            'id="workflowWorkspaceSkills"',
            'id="workflowWorkspaceActions"',
            'id="mindmapTreeCacheStatus"',
            'id="mindmapTreeCacheText"',
            'id="mindmapTreeRefreshButton"',
            'id="mindmapTreePreviewList"',
            'id="operationWorkspaceVerification"',
            'id="statusPill"',
            'id="settingsButton"',
            'id="newConversationButton"',
            'id="conversationHistoryButton"',
            'id="stopButton"',
            'id="pdfCacheBanner"',
            'id="pdfCacheBannerText"',
            'id="liveHistory"',
            'id="promptInput"',
            'id="sendButton"',
            'id="agentWorkbenchBar"',
            'id="agentWorkbenchLine"',
            'id="agentPlanRefreshButton"',
            "对象",
            "对话",
            "操作",
            "知识",
            "工作流",
            "Knowledge Console",
            "对话",
            "高级",
        ]:
            self.assertIn(marker, self.html)

        self.assertIn("activeProductMode: 'chat'", self.js)
        self.assertIn("commandPaneExpanded: true", self.js)
        self.assertIn("lastWorkspacePane: 'object'", self.js)
        self.assertIn("activeWorkspaceSurface: 'console'", self.js)
        self.assertIn("function switchProductMode", self.js)
        self.assertIn("function renderProductMode", self.js)
        self.assertIn("function renderCommandPane", self.js)
        self.assertIn("function toggleCommandPane", self.js)
        self.assertIn("function switchWorkspaceSurface", self.js)
        self.assertIn("function renderWorkspaceNavigator", self.js)
        self.assertIn("function refreshNotebookWorkspace", self.js)
        self.assertIn("function renderNotebookWorkspace", self.js)
        self.assertIn("function renderNotebookKnowledgeMatrix", self.js)
        self.assertIn("codex.mn.knowledgeConsoleMatrix.v1", self.js)
        self.assertIn("data-notebook-knowledge-axis", self.js)
        for runtime_marker in [
            "'notebookWorkspaceRunbook'",
            "'notebookWorkspaceRunbookSummary'",
            "'notebookWorkspaceRunbookAutoButton'",
            "'notebookWorkspaceRunbookAutoStatus'",
            "'notebookWorkspaceRunbookContinueButton'",
            "'notebookWorkspaceRunbookList'",
        ]:
            self.assertIn(runtime_marker, self.js)
        self.assertIn("knowledgeMatrix", self.js)
        self.assertIn("function renderNotebookObjectIntake", self.js)
        self.assertIn("codex.mn.objectIntake.v1", self.js)
        self.assertIn("data-object-intake-route", self.js)
        self.assertIn("data.objectIntake", self.js)
        self.assertIn("notebookObjectIntake", self.html)
        self.assertIn("notebookObjectIntakeSummary", self.html)
        self.assertIn("notebookObjectIntakeRoutes", self.html)
        self.assertIn("function renderNotebookObjectTaskComposer", self.js)
        self.assertIn("codex.mn.objectTaskComposer.v1", self.js)
        self.assertIn("data-object-task-id", self.js)
        self.assertIn("data.objectTaskComposer", self.js)
        self.assertIn("codex.mn.objectTaskWorkflowCandidate.v1", self.js)
        self.assertIn("notebook-object-task-workflow", self.js)
        self.assertIn("startAction = task.startAction", self.js)
        self.assertIn("action === 'workflow_start'", self.js)
        self.assertIn("postCompanion('workflow_start'", self.js)
        self.assertIn("function renderWorkflowBuilderBoard", self.js)
        self.assertIn("codex.mn.workflowBuilderBoard.v1", self.js)
        self.assertIn("data-workflow-builder-lane", self.js)
        self.assertIn("data-workflow-builder-card", self.js)
        self.assertIn("renderWorkflowBuilderBoard(data.workflowBuilderBoard || {})", self.js)
        self.assertIn("workflowBuilderBoard", self.js)
        self.assertIn("workflowBuilderBoardPanel", self.html)
        self.assertIn("workflowBuilderBoardSummary", self.html)
        self.assertIn("workflowBuilderBoardLanes", self.html)
        self.assertIn("notebookObjectTaskComposer", self.html)
        self.assertIn("notebookObjectTaskComposerSummary", self.html)
        self.assertIn("notebookObjectTaskComposerList", self.html)
        self.assertIn("refreshAgentPlan(true, payload)", self.js)
        self.assertIn("Object.assign({}, overridePayload, {prompt: prompt})", self.js)
        self.assertIn("object_browser: 'object'", self.js)
        self.assertIn("object_browser: 'objectBrowserPanel'", self.js)
        self.assertIn("object_browser: true", self.js)
        self.assertIn("action === 'object_browser'", self.js)
        self.assertIn("refreshObjectBrowser(true, payload)", self.js)
        self.assertIn("source_registry: 'object'", self.js)
        self.assertIn("source_registry: 'sourceRegistryPanel'", self.js)
        self.assertIn("source_registry: true", self.js)
        self.assertIn("action === 'open_source_registry'", self.js)
        self.assertIn("refreshNotebookWorkspace(false)", self.js)
        self.assertIn("mindmap_studio: 'mindmapStudioPanel'", self.js)
        self.assertIn("action === 'open_mindmap_studio'", self.js)
        self.assertIn("renderMindmapStudioPanel()", self.js)
        self.assertIn("action === 'open_card_factory'", self.js)
        self.assertIn("refreshKnowledgeWorkspace(true, payload)", self.js)
        self.assertIn("action === 'open_workflow_builder'", self.js)
        self.assertIn("refreshWorkflowWorkspace(true, payload)", self.js)
        self.assertIn("skill_center: 'workflow'", self.js)
        self.assertIn("skill_center: 'skillCenterPanel'", self.js)
        self.assertIn("action === 'open_skill_center'", self.js)
        self.assertIn("verification_center: 'operation'", self.js)
        self.assertIn("verification_center: 'verificationReportPanel'", self.js)
        self.assertIn("action === 'verification_report_list'", self.js)
        self.assertIn("refreshVerificationCenter(true, payload)", self.js)
        self.assertIn("function runNotebookWorkspaceAction", self.js)
        self.assertIn("state.notebookWorkspace", self.js)
        self.assertIn("postCompanion('notebook_workspace'", self.js)
        self.assertIn("notebookWorkspaceRefreshButton", self.js)
        self.assertIn("data-notebook-workspace-action", self.js)
        self.assertIn("notebookWorkspaceSources", self.html)
        self.assertIn("notebookWorkspaceSourceRegistry", self.html)
        self.assertIn("notebookWorkspaceSourceSummary", self.html)
        self.assertIn("notebookWorkspaceSourceList", self.html)
        self.assertIn("notebookWorkspaceSourceActionStatus", self.html)
        self.assertIn("notebookWorkspaceSourceActions", self.html)
        self.assertIn("function renderNotebookSourceRegistry", self.js)
        self.assertIn("function renderNotebookSourceActions", self.js)
        self.assertIn("function sourceRegistryActionStatusText", self.js)
        self.assertIn("function renderNotebookSourceActionStatus", self.js)
        self.assertIn("function recordSourceRegistryActionRun", self.js)
        self.assertIn("function runSourceRegistryTrackedAction", self.js)
        self.assertIn("source_registry_action_record", self.js)
        self.assertIn("data-source-registry-kind", self.js)
        self.assertIn("data-source-registry-action", self.js)
        self.assertIn("data.sourceRegistry", self.js)
        self.assertIn("choose_pdf_cache_file", self.js)
        self.assertIn("open_config_page", self.js)
        self.assertIn("refresh_context", self.js)
        self.assertIn("notebookWorkspaceStudyProgram", self.html)
        self.assertIn("notebookWorkspaceStudyCoverage", self.html)
        self.assertIn("notebookWorkspaceStudyGaps", self.html)
        self.assertIn("notebookWorkspaceStudyRecommendations", self.html)
        self.assertIn("function renderNotebookStudyProgram", self.js)
        self.assertIn("data-study-program-gap", self.js)
        self.assertIn("data-study-workflow-id", self.js)
        self.assertIn("data.studyProgram", self.js)
        self.assertIn("renderNotebookWorkspaceRunbook", self.js)
        self.assertIn("data-notebook-runbook-step", self.js)
        self.assertIn("data.runbook", self.js)
        self.assertIn("runNotebookWorkspaceAutoPlan", self.js)
        self.assertIn("notebookWorkspaceRunbookAutoButton", self.js)
        self.assertIn("notebookWorkspaceRunbookAutoStatus", self.html)
        self.assertIn("recordNotebookRunbookPreflight", self.js)
        self.assertIn("notebook_runbook_preflight_record", self.js)
        self.assertIn("runbook.autoPlan", self.js)
        self.assertIn("autoPlan.latestRun", self.js)
        self.assertIn("runNotebookWorkspaceContinue", self.js)
        self.assertIn("notebookWorkspaceRunbookContinueButton", self.js)
        self.assertIn("runbook.continueAction", self.js)
        self.assertIn("data-product-mode", self.js)
        self.assertIn("data-workspace-surface", self.js)
        self.assertIn("modeSwitchBar", self.js)
        self.assertIn("chatModeButton", self.js)
        self.assertIn("agentWorkspaceModeButton", self.js)
        self.assertIn("modeIntentLine", self.js)
        self.assertIn("workspaceNavigator", self.js)
        self.assertIn("workspaceNavMindmapStudioButton", self.js)
        self.assertIn("workspaceNavLedgerExplorerButton", self.js)
        self.assertIn("switchProductMode('chat')", self.js)
        self.assertIn("switchProductMode('workspace')", self.js)
        self.assertIn(".mode-switch-bar", self.css)
        self.assertIn(".mode-switch-button", self.css)
        self.assertIn(".mode-intent-line", self.css)
        self.assertIn(".workspace-navigator", self.css)
        self.assertIn(".workspace-nav-card", self.css)
        self.assertIn(".workspace-nav-card.active", self.css)
        self.assertIn(".notebook-workspace-panel", self.css)
        self.assertIn(".notebook-workspace-card", self.css)
        self.assertIn(".notebook-workspace-action", self.css)
        self.assertIn(".notebook-source-registry", self.css)
        self.assertIn(".notebook-source-item", self.css)
        self.assertIn(".notebook-study-program", self.css)
        self.assertIn(".notebook-study-gap", self.css)
        self.assertIn(".notebook-study-recommendation", self.css)
        self.assertIn(".notebook-runbook", self.css)
        self.assertIn(".notebook-runbook-step", self.css)
        self.assertIn(".notebook-knowledge-matrix", self.css)
        self.assertIn(".notebook-knowledge-axis", self.css)
        self.assertIn(".workflow-builder-board-panel", self.css)
        self.assertIn(".workflow-builder-lane", self.css)
        self.assertIn(".workflow-builder-card", self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] #workbenchTabs', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] .workbench-panel', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] #workspaceNavigator', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] #commandPaneBody', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="workspace"] #workspaceNavigator', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="workspace"] #workbenchTabs', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="workspace"][data-command-pane-expanded="false"] #commandPaneBody', self.css)
        self.assertIn('.command-pane-panel', self.css)
        self.assertIn('.command-pane-header', self.css)
        self.assertIn('.command-pane-composer', self.css)
        self.assertIn("function switchWorkbenchPane", self.js)
        self.assertIn("activeWorkbenchPane: 'object'", self.js)
        self.assertIn("pane = String(pane || 'object')", self.js)
        self.assertIn("pane = 'object'", self.js)
        self.assertNotIn("activeWorkbenchPane: 'dialog'", self.js)
        self.assertNotIn('id="workbenchTabDialog"', self.html)
        self.assertIn("对象、关系、活动、账本", self.html)
        self.assertIn("Notebook Workspace", self.html)
        self.assertIn("Command Pane", self.html)
        self.assertIn("当前 notebook 的对象、脑图、复习、workflow 和账本总览", self.html)
        self.assertIn("function renderWorkbenchPanels", self.js)
        self.assertIn("function renderObjectWorkspaceMnObject", self.js)
        self.assertIn("function renderObjectRiskPanel", self.js)
        self.assertIn("function objectRiskItem", self.js)
        self.assertIn("riskRegister", self.js)
        self.assertIn("function renderObjectWorkspaceActions", self.js)
        self.assertIn('id="objectBrowserPanel"', self.html)
        self.assertIn('id="objectBrowserSummary"', self.html)
        self.assertIn('id="objectBrowserTypeFilterSelect"', self.html)
        self.assertIn('id="objectBrowserKindFilterInput"', self.html)
        self.assertIn('id="objectBrowserSearchInput"', self.html)
        self.assertIn('id="objectBrowserFilterButton"', self.html)
        self.assertIn('id="objectBrowserList"', self.html)
        self.assertIn('id="objectRegistryScanButton"', self.html)
        self.assertIn("function refreshObjectBrowser", self.js)
        self.assertIn("function objectBrowserFilterPayload", self.js)
        self.assertIn("function requestObjectRegistryScan", self.js)
        self.assertIn("function renderObjectBrowser", self.js)
        self.assertIn("function openObjectBrowserItem", self.js)
        self.assertIn("object_browser", self.js)
        self.assertIn("objectTypeFilter", self.js)
        self.assertIn("kindFilter", self.js)
        self.assertIn("query: objectBrowserSearchQuery", self.js)
        self.assertIn("objectBrowserFilterButton", self.js)
        self.assertIn("request_mn_object_registry_scan", self.js)
        self.assertIn("browserAction", self.js)
        self.assertIn("data-browser-action", self.js)
        self.assertIn("Object Browser", self.html)
        self.assertIn("type === 'registry'", self.js)
        self.assertIn("Registry", self.js)
        self.assertIn("function refreshObjectGraph", self.js)
        self.assertIn("function renderObjectGraph", self.js)
        self.assertIn("function openObjectGraphNode", self.js)
        self.assertIn("knowledge_entity", self.js)
        self.assertIn("return '知识'", self.js)
        self.assertIn("mn_note", self.js)
        self.assertIn("return 'MN节点'", self.js)
        self.assertIn("function refreshObjectActivity", self.js)
        self.assertIn("function renderObjectActivity", self.js)
        self.assertIn("function openObjectActivityItem", self.js)
        self.assertIn("function refreshOperationLedger", self.js)
        self.assertIn("function operationLedgerFilterPayload", self.js)
        self.assertIn("function renderOperationLedger", self.js)
        self.assertIn("function renderOperationLedgerDetail", self.js)
        self.assertIn("function closeOperationLedgerDetail", self.js)
        self.assertIn("function openOperationLedgerEntry", self.js)
        self.assertIn("activityAction", self.js)
        self.assertIn("data-activity-action", self.js)
        self.assertIn("graphAction", self.js)
        self.assertIn("data-graph-action", self.js)
        self.assertIn("ledgerAction", self.js)
        self.assertIn("data-ledger-action", self.js)
        self.assertIn("result.evidence", self.js)
        self.assertIn("evidence.verification", self.js)
        self.assertIn("evidence.callback", self.js)
        self.assertIn("evidence.operationChain", self.js)
        self.assertIn("evidence.manualRelation", self.js)
        self.assertIn("manualRelations", self.js)
        self.assertIn("object_graph_manual_relation", self.js)
        self.assertIn("manualRelation.fromObjectId", self.js)
        self.assertIn("manualRelation.toObjectId", self.js)
        self.assertIn("关系对象", self.js)
        self.assertIn("手工关系", self.js)
        self.assertIn("验证：", self.js)
        self.assertIn("操作链", self.js)
        self.assertIn("nativeApply", self.js)
        self.assertIn("nativeCommand", self.js)
        self.assertIn("nativeEventTimeline", self.js)
        self.assertIn("原生命令", self.js)
        self.assertIn("事件线", self.js)
        self.assertIn("residual", self.js)
        self.assertIn("renderOperationLedgerDetail(result)", self.js)
        self.assertIn("operationLedgerDetail", self.js)
        self.assertIn("conversation_load", self.js)
        self.assertIn("workflow_status", self.js)
        self.assertIn("ai_edit_transaction_get", self.js)
        self.assertIn("operation_ledger_list", self.js)
        self.assertIn("operation_ledger_get", self.js)
        self.assertIn("entryTypeFilter", self.js)
        self.assertIn("statusFilter", self.js)
        self.assertIn("query: operationLedgerSearchQuery", self.js)
        self.assertIn("operationLedgerFilterButton", self.js)
        self.assertIn("log_detail", self.js)
        self.assertIn("state.objectActivity", self.js)
        self.assertIn("state.objectGraph", self.js)
        self.assertIn("state.operationLedger", self.js)
        self.assertIn("postCompanion('object_graph'", self.js)
        self.assertIn("postCompanion('object_activity'", self.js)
        self.assertIn("postCompanion('operation_ledger_list'", self.js)
        self.assertIn("postCompanion('operation_ledger_get'", self.js)
        object_browser_open_body = self.js.split("function openObjectBrowserItem", 1)[1].split("\n  function renderObjectBrowser", 1)[0]
        object_graph_refresh_body = self.js.split("function refreshObjectGraph", 1)[1].split("\n  function openObjectGraphRelationEditor", 1)[0]
        object_activity_refresh_body = self.js.split("function refreshObjectActivity", 1)[1].split("\n  function operationLedgerKindLabel", 1)[0]
        operation_ledger_refresh_body = self.js.split("function refreshOperationLedger", 1)[1].split("\n  function renderOperationWorkspaceActions", 1)[0]
        self.assertIn("refreshObjectGraph(true, descriptor.payload || {})", object_browser_open_body)
        self.assertIn("refreshObjectActivity(true, descriptor.payload || {})", object_browser_open_body)
        self.assertIn("refreshOperationLedger(true, descriptor.payload || {})", object_browser_open_body)
        self.assertIn("overridePayload", object_graph_refresh_body)
        self.assertIn("objectPayload.mnObjectId || objectRef.objectId", object_graph_refresh_body)
        self.assertIn("Object.assign({}, objectPayload", object_graph_refresh_body)
        self.assertIn("mnObject: objectPayload.mnObject || objectRef", object_graph_refresh_body)
        self.assertIn("overridePayload", object_activity_refresh_body)
        self.assertIn("Object.assign({}, objectPayload", object_activity_refresh_body)
        self.assertIn("mnObject: objectPayload.mnObject || objectRef", object_activity_refresh_body)
        self.assertIn("overridePayload", operation_ledger_refresh_body)
        self.assertIn("Object.assign({}, objectPayload", operation_ledger_refresh_body)
        self.assertIn("mnObject: objectPayload.mnObject || objectRef", operation_ledger_refresh_body)
        self.assertIn("object-graph-panel", self.css)
        self.assertIn("object-risk-panel", self.css)
        self.assertIn("object-risk-row", self.css)
        self.assertIn("object-risk-summary", self.css)
        self.assertIn("object-graph-node", self.css)
        self.assertIn("object-graph-open", self.css)
        self.assertIn("object-activity-panel", self.css)
        self.assertIn("object-activity-row", self.css)
        self.assertIn("object-activity-open", self.css)
        self.assertIn("operation-ledger-panel", self.css)
        self.assertIn("operation-ledger-filters", self.css)
        self.assertIn("operation-ledger-filter-field", self.css)
        self.assertIn("operation-ledger-search", self.css)
        self.assertIn("operation-ledger-row", self.css)
        self.assertIn("operation-ledger-open", self.css)
        self.assertIn("operation-ledger-detail-panel", self.css)
        self.assertIn("operation-ledger-evidence-row", self.css)
        self.assertIn(".object-browser-filters", self.css)
        self.assertIn(".object-browser-filter-field", self.css)
        self.assertIn(".object-browser-search", self.css)
        self.assertIn("function renderOperationWorkspaceActions", self.js)
        self.assertIn("function renderMindmapTreeCacheStatus", self.js)
        self.assertIn("function requestMindmapTreeRead", self.js)
        self.assertIn("function renderMindmapTreePreview", self.js)
        self.assertIn("function renderKnowledgeWorkspace", self.js)
        self.assertIn("function renderWorkflowWorkspace", self.js)
        self.assertIn("function refreshKnowledgeWorkspace", self.js)
        self.assertIn("function refreshWorkflowWorkspace", self.js)
        self.assertIn("state.mindmapTreeCache", self.js)
        self.assertIn("state.knowledgeWorkspace", self.js)
        self.assertIn("state.workflowWorkspace", self.js)
        self.assertIn("knowledge_index_status", self.js)
        self.assertIn("workflow_list", self.js)
        self.assertIn("mn_api_status", self.js)
        self.assertIn("result.mindmapTreeCache", self.js)
        self.assertIn("postCompanion('mn_read_tree'", self.js)
        self.assertIn("treePreview", self.js)
        self.assertIn("data-object-workbench-action", self.js)
        self.assertIn("operation.mnObject", self.js)
        self.assertIn("availableActionCount", self.js)
        self.assertIn("sourceRef.quote", self.js)
        self.assertIn("data-operation-workbench-action", self.js)
        self.assertIn("runAgentNextAction(item", self.js)
        self.assertIn(".workbench-layout", self.css)
        self.assertIn(".workbench-panel", self.css)
        self.assertIn(".workbench-action-list", self.css)
        self.assertIn(".workbench-action-button", self.css)
        self.assertIn(".knowledge-workspace-panel", self.css)
        self.assertIn(".workflow-workspace-panel", self.css)
        self.assertIn(".knowledge-workspace-card", self.css)
        self.assertIn(".workflow-workspace-card", self.css)
        self.assertIn(".mindmap-tree-cache-status", self.css)
        self.assertIn(".mindmap-tree-preview-list", self.css)
        self.assertIn(".mindmap-tree-preview-node", self.css)
        topbar_html = main_html.split('<section class="topbar">', 1)[1].split('<section id="workspaceNavigator"', 1)[0]
        topbar_rail = topbar_html.split('<div class="topbar-workspace-rail">', 1)[1].split('<div class="topbar-actions">', 1)[0]
        self.assertIn('id="knowledgeOsContractPanel"', topbar_rail)
        self.assertIn('id="modeSwitchBar"', topbar_rail)
        self.assertLess(topbar_html.index('class="topbar-identity"'), topbar_html.index('class="topbar-workspace-rail"'))
        self.assertLess(topbar_html.index('class="topbar-workspace-rail"'), topbar_html.index('class="topbar-actions"'))
        self.assertLess(main_html.index('id="workbenchTabs"'), main_html.index('id="commandPanePanel"'))
        self.assertLess(main_html.index('id="commandPanePanel"'), main_html.index('id="workbenchLayout"'))
        self.assertLess(main_html.index('id="knowledgeOsContractPanel"'), main_html.index('id="modeSwitchBar"'))
        self.assertLess(main_html.index('id="knowledgeOsContractPanel"'), main_html.index('id="commandPanePanel"'))
        self.assertIn(".topbar .knowledge-os-contract-panel {\n  display: none;", self.css)
        for marker in [
            "MarginNote Knowledge OS",
            "对象层",
            "操作层",
            "证据层",
            "高级模式用于对象、操作、证据和 workflow 诊断",
        ]:
            self.assertIn(marker, main_html)
        self.assertLess(main_html.index('id="objectWorkspacePanel"'), main_html.index('id="operationWorkspacePanel"'))
        self.assertLess(main_html.index('id="operationWorkspacePanel"'), main_html.index('id="knowledgeWorkspacePanel"'))
        self.assertLess(main_html.index('id="knowledgeWorkspacePanel"'), main_html.index('id="workflowWorkspacePanel"'))

        for removed in [
            "tabButtonButtons",
            "tabButtonSettings",
            "tabButtonFiles",
            "tabButtonHistory",
            "buttonCenterLayout",
            "goalRunPanel",
            "primaryActionGrid",
            "workflowActionPanel",
            "mainPinnedButtonsPanel",
            "draftPanel",
            "releaseAcceptanceActions",
            "runToggleButton",
            "queueBadge",
            "fileInput",
            "制卡",
            "导出",
            "一次性目标",
            "按钮中心",
        ]:
            self.assertNotIn(removed, main_html)
        self.assertNotIn('id="nativeHighlightWizardButton"', main_html)
        self.assertNotIn('data-action="request_native_highlight_selection"', main_html)

    def test_mindmap_studio_is_a_first_class_operation_workspace(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        for marker in [
            'id="mindmapStudioPanel"',
            'id="mindmapStudioSummary"',
            'id="mindmapStudioCurrentTree"',
            'id="mindmapStudioDiffStage"',
            'id="mindmapStudioApplyStage"',
            'id="mindmapStudioTransactionStage"',
            'id="mindmapStudioReadTreeButton"',
            'id="mindmapStudioPreviewDiffButton"',
            'id="mindmapStudioApplySelectedButton"',
            'id="mindmapStudioVerifyButton"',
            'id="mindmapStudioRollbackButton"',
            'id="mindmapStudioStatusLine"',
            "Mindmap Studio",
            "读取现有脑图",
            "预览 Diff",
            "应用所选",
            "验证事务",
            "回滚事务",
        ]:
            self.assertIn(marker, operation_html)
        self.assertLess(operation_html.index('id="mindmapStudioPanel"'), operation_html.index('id="mindmapTreeCacheStatus"'))

        for marker in [
            "function renderMindmapStudioPanel",
            "function mindmapStudioStatusLine",
            "function latestMindmapDiffOperationPanel",
            "function previewMindmapDiffFromStudio",
            "function applyMindmapStudioSelectedDiff",
            "function verifyMindmapStudioTransaction",
            "function rollbackMindmapStudioTransaction",
            "renderMindmapStudioPanel()",
            "requestMindmapTreeRead()",
            "runAgentNextAction({action: 'mindmap_diff_preview'",
            "acceptMindmapDiff(panel)",
            "refreshAiEditTransactionVerification(transactionId)",
            "rollbackAiEditTransaction(transactionId)",
            "mindmap-studio-panel",
            "mindmap-studio-stage",
            "mindmap-studio-actions",
            "mindmap-studio-status-line",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_agent_workspace_navigator_routes_to_first_class_surfaces(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        self.assertIn('id="workspaceNavigator"', main_html)
        self.assertIn('data-workspace-surface="console"', main_html)
        self.assertIn('data-workspace-navigator-expanded="false"', main_html)
        navigator_html = main_html.split('id="workspaceNavigator"', 1)[1].split('id="workbenchTabs"', 1)[0]
        for marker in [
            'id="workspaceSurfaceSelect"',
            '<option value="object_browser">Object Browser</option>',
            '<option value="source_registry">Source Registry</option>',
            '<option value="verification_center">Verification Center</option>',
            'id="workspaceNavigatorToggleButton"',
            "Knowledge Console",
            "Mindmap Studio",
            "Card Factory",
            "Operation Ledger",
            "Knowledge Graph",
            "Workflow Builder",
            "Skill Center",
            'data-workspace-surface="console"',
            'data-workspace-surface="mindmap_studio"',
            'data-workspace-surface="card_factory"',
            'data-workspace-surface="ledger_explorer"',
            'data-workspace-surface="knowledge_graph"',
            'data-workspace-surface="workflow_builder"',
            'data-workspace-surface="skill_center"',
        ]:
            self.assertIn(marker, navigator_html)

        for marker in [
            "function workspaceSurfacePane",
            "function workspaceSurfaceAnchor",
            "function workspaceSurfaceSummary",
            "function focusWorkspaceSurfaceAnchor",
            "function switchWorkspaceSurface",
            "function renderWorkspaceNavigator",
            "function releaseSelectFocusBeforeNativeMenu",
            "workspaceNavigatorExpanded",
            "workspaceSurfaceSelect",
            "workspaceNavigatorToggleButton",
            "function renderNotebookWorkspaceShell",
            "notebookWorkspaceDetailsVisible",
            "state.notebookWorkspaceExpanded",
            "notebookWorkspaceExpanded: false",
            "notebookWorkspaceDetailsToggleButton",
            "notebookWorkspaceDetails",
            "state.activeWorkspaceSurface",
            "notebookKnowledgeMatrixToggleButton",
            "state.knowledgeMatrixExpanded",
            "notebookKnowledgeAxisPriority",
            "switchWorkbenchPane(workspaceSurfacePane(surface)",
            "if (state.workspaceNavigatorExpanded) state.workspaceNavigatorExpanded = false;",
            "workspaceSurfaceAnchor(surface)",
            "focusWorkspaceSurfaceAnchor(anchorId)",
            "releaseSelectFocusBeforeNativeMenu(workspaceSurfaceSelect)",
            "releaseTextInputFocus('workspaceSurfaceSelect')",
            "workspaceNavMindmapStudioButton",
            "workspaceNavCardFactoryButton",
            "workspaceNavLedgerExplorerButton",
            "workspaceNavWorkflowBuilderButton",
            "workspaceNavSkillCenterButton",
            "mindmapDiffWorkbench",
            "knowledgeWorkspaceReviewQueue",
            "operationLedgerPanel",
            "workflowWorkspaceTemplates",
            "workflowWorkspaceSkills",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_workspace_surface_layout_is_page_level_not_crowded_grid(self) -> None:
        for marker in [
            'shell.setAttribute(\'data-workspace-surface\', surface)',
            '.ai-chat-shell[data-product-mode="workspace"][data-workspace-surface="console"] #knowledgeConsolePanel',
            '.ai-chat-shell[data-product-mode="workspace"][data-workspace-surface="source_registry"] #knowledgeConsolePanel',
            '.ai-chat-shell[data-product-mode="workspace"][data-workspace-surface="console"] .notebook-workspace-details',
            '.ai-chat-shell[data-product-mode="workspace"][data-workspace-surface="source_registry"] .notebook-workspace-details',
            '.ai-chat-shell[data-workspace-surface="console"] #objectBrowserPanel',
            '.ai-chat-shell[data-workspace-surface="console"] #objectGraphPanel',
            '.ai-chat-shell[data-workspace-surface="console"] #objectActivityPanel',
            '.ai-chat-shell[data-workspace-surface="console"] #operationLedgerDrawer',
            '.ai-chat-shell[data-workspace-surface="console"] #workbenchTabs',
            '.ai-chat-shell[data-workspace-surface="console"] #workbenchLayout',
            '.ai-chat-shell[data-workspace-surface="source_registry"] #workbenchTabs',
            '.ai-chat-shell[data-workspace-surface="source_registry"] #workbenchLayout',
            ".notebook-workspace-panel.compact #notebookWorkspaceDetails",
            ".notebook-workspace-panel.compact #notebookWorkspaceGrid",
            ".notebook-workspace-panel.compact #notebookObjectIntake",
            ".notebook-workspace-panel.compact #notebookObjectTaskComposer",
            ".notebook-workspace-panel.compact #sourceRegistryPanel",
            ".notebook-workspace-panel.compact #notebookWorkspaceRunbook",
            '.ai-chat-shell[data-workspace-surface="source_registry"] #notebookKnowledgeMatrix',
            '.ai-chat-shell[data-workspace-surface="mindmap_studio"] #verificationReportPanel',
            '.ai-chat-shell[data-workspace-surface="verification_center"] #mindmapStudioPanel',
            '.ai-chat-shell[data-workspace-surface="ledger_explorer"] #objectBrowserPanel',
            '.ai-chat-shell[data-workspace-surface="card_factory"] #knowledgeWorkspaceResults',
            '.ai-chat-shell[data-workspace-surface="knowledge_graph"] #knowledgeWorkspaceReviewQueue',
            '.ai-chat-shell[data-workspace-surface="workflow_builder"] #skillCenterPanel',
            '.ai-chat-shell[data-workspace-surface="skill_center"] #workflowBuilderBoardPanel',
            '.workbench-panel.active',
            '.ai-chat-shell[data-product-mode="workspace"][data-command-pane-expanded="true"] #workspaceNavigator',
            '.ai-chat-shell[data-product-mode="workspace"][data-command-pane-expanded="true"] #commandPanePanel',
            '.ai-chat-shell[data-product-mode="workspace"][data-command-pane-expanded="true"] .command-pane-body .ai-chat-history',
            "overflow-x: hidden;",
            "overflow-y: auto;",
            "padding-bottom: 96px;",
            "scroll-padding-bottom: 104px;",
            ".workbench-panel-header {\n  position: sticky;",
        ]:
            self.assertIn(marker, self.js + self.css)

        self.assertIn("grid-template-columns: minmax(0, 1fr)", self.css)
        self.assertIn("margin-bottom: 206px;", self.css)
        self.assertIn("scroll-padding-bottom: 18px;", self.css)
        self.assertIn("max-height: none;", self.css)
        self.assertIn(".notebook-knowledge-matrix.collapsed .notebook-knowledge-axis.secondary", self.css)
        self.assertIn(".workspace-nav-grid {\n  display: none;", self.css)
        self.assertIn(".workspace-navigator-toggle {\n  display: none;", self.css)
        self.assertIn('.ai-chat-shell[data-workspace-navigator-expanded="true"] .workspace-nav-grid', self.css)
        self.assertIn("grid-template-columns: repeat(2, minmax(0, 1fr));", self.css)
        self.assertIn(".workspace-nav-card {\n  min-width: 0;", self.css)
        self.assertIn("border-radius: 8px;", self.css)

    def test_advanced_mode_defaults_to_simple_tool_center(self) -> None:
        for marker in [
            'id="advancedToolCenterPanel"',
            'id="advancedStatusPdf"',
            'id="advancedStatusMindmap"',
            'id="advancedStatusWrite"',
            'id="advancedNextStepText"',
            'id="advancedNextStepButton"',
            'id="advancedReadButton"',
            'id="advancedMindmapButton"',
            'id="advancedCardsButton"',
            'id="advancedVerifyButton"',
            'id="expertModePanel"',
            'id="expertModeToggleButton"',
            'id="expertModeBackButton"',
            'id="expertModeHint"',
            "工具",
            "当前状态",
            "你想做什么",
            "下一步建议",
            "专家模式",
        ]:
            self.assertIn(marker, self.html)

        for marker in [
            "expertModeExpanded: false",
            "function renderAdvancedToolCenter",
            "function renderExpertMode",
            "function runAdvancedPrimaryAction",
            "function toggleExpertMode",
            "function exitExpertMode",
            "shell.setAttribute('data-expert-mode'",
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="false"] #workspaceNavigator',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="false"] #knowledgeConsolePanel',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="false"] #workbenchTabs',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="false"] #commandPanePanel',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="false"] #commandPaneHeader',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="true"] #workspaceNavigator',
            '.ai-chat-shell[data-product-mode="workspace"][data-expert-mode="true"] #expertModeBackButton',
            '.advanced-tool-center-panel',
            '.advanced-task-grid',
            '.expert-mode-back-button',
            '.expert-mode-panel',
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertNotIn("grid-template-columns:\n    minmax(150px, 0.82fr)", self.css)
        self.assertNotIn("grid-template-columns: repeat(7, minmax(116px, 1fr))", self.css)
        self.assertNotIn("max-height: min(310px, 38vh)", self.css)
        self.assertNotIn("scroll-padding-bottom: 226px", self.css)
        self.assertNotIn("@media (min-width: 761px) {\n  .workbench-panel {\n    display: flex;", self.css)

    def test_staged_prompt_actions_stay_in_command_pane(self) -> None:
        stage_body = self.js.split("function stagePromptAction", 1)[1].split(
            "\n  function stageOrExplainPromptAction", 1
        )[0]

        self.assertIn("renderCommandPane()", stage_body)
        self.assertNotIn("switchProductMode('chat')", stage_body)
        self.assertNotIn("switchTab('chat')", stage_body)

    def test_top_mindmap_target_selector_controls_generation_destination(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="mindmapTargetBar"',
            'id="mindmapTargetLight"',
            'id="mindmapTargetSelect"',
            'id="mindmapTargetRefreshButton"',
            "目标脑图",
        ]:
            self.assertIn(marker, main_html)
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        self.assertIn('id="mindmapTargetBar"', operation_html)
        self.assertLess(operation_html.index('id="mindmapTargetBar"'), operation_html.index('id="agentWorkbenchBar"'))

        for marker in [
            "state.mindmapTarget",
            "function refreshMindmapTarget",
            "function renderMindmapTargetBar",
            "function ensureMindmapTargetReady",
            "mindmap_target_status",
            "mindmap_target_update",
            "payload.mindmapTarget = state.mindmapTarget.target",
            "writeTarget: result.writeTarget ||",
        ]:
            self.assertIn(marker, self.js)
        ensure_body = self.js.split("function ensureMindmapTargetReady", 1)[1].split(
            "\n  function renderControls", 1
        )[0]
        self.assertIn("state.context.mindmapVisible", ensure_body)
        self.assertIn("当前没有打开脑图", ensure_body)

    def test_knowledge_and_workflow_workspaces_are_executable_not_status_only(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="knowledgeWorkspaceSearchInput"',
            'id="knowledgeWorkspaceSearchButton"',
            'id="knowledgeWorkspaceResults"',
            'id="knowledgeWorkspaceReviewQueue"',
            'id="knowledgeWorkspaceReviewList"',
            'id="workflowWorkspaceTemplates"',
            'id="workflowWorkspaceRecentRuns"',
            'id="workflowWorkspaceSkillsList"',
            'id="workflowRunInspectorPanel"',
            'id="workflowRunInspectorTitle"',
            'id="workflowRunInspectorSummary"',
            'id="workflowRunInspectorSteps"',
            'id="workflowRunInspectorCloseButton"',
        ]:
            self.assertIn(marker, main_html)

        for marker in [
            "function renderKnowledgeSearchResults",
            "function searchKnowledgeWorkspace",
            "function renderKnowledgeReviewQueue",
            "function addDraftToReviewQueue",
            "function renderWorkflowTemplates",
            "function renderWorkflowRuns",
            "function renderWorkflowSkills",
            "function renderWorkflowSkillBadges",
            "function previewWorkflowSkillPlan",
            "function workflowRunInspectorStep",
            "function renderWorkflowRunInspector",
            "function openWorkflowRunInspector",
            "function retryWorkflowRunStep",
            "function workflowRunNextStep",
            "function resumeWorkflowRun",
            "function closeWorkflowRunInspector",
            "function startWorkflowTemplate",
            "function installWorkflowSkill",
            "postCompanion('review_queue_list'",
            "postCompanion('review_queue_add'",
            "data-workflow-template-id",
            "data-workflow-run-id",
            "data-workflow-step-id",
            "data-workflow-step-action",
            "data-workflow-skill-id",
            "data-workflow-skill-risk",
            "postCompanion('knowledge_index_search'",
            "postCompanion('workflow_start'",
            "postCompanion('workflow_status'",
            "postCompanion('workflow_next_step'",
            "postCompanion('workflow_resume'",
            "postCompanion('workflow_retry_step'",
            "postCompanion('skill_marketplace_status'",
            "postCompanion('skill_install'",
            "postCompanion('skill_operation_plan'",
            "postCompanion('skill_run_latest'",
            "workflowTemplates",
            "workflowSkills",
            "skillRuns",
            "knowledgeWorkspaceResults",
            "knowledgeWorkspaceReviewQueue",
            "knowledgeWorkspaceReviewList",
            "workflowWorkspaceTemplates",
            "workflowWorkspaceRecentRuns",
            "workflowWorkspaceSkillsList",
            "runInspector",
            "retryable",
            "workflow-run-inspector-next",
            "workflow-run-inspector-resume",
            "重试",
            "加入复习队列",
        ]:
            self.assertIn(marker, self.js)

        for marker in [
            ".knowledge-workspace-search",
            ".knowledge-workspace-result",
            ".knowledge-review-queue",
            ".knowledge-review-item",
            ".ai-edit-review-queue",
            ".workflow-workspace-template",
            ".workflow-workspace-run",
            ".workflow-workspace-skill",
            ".workflow-workspace-skill.invalid",
            ".workflow-workspace-skill-badges",
            ".workflow-workspace-skill-badge",
            ".workflow-run-inspector-panel",
            ".workflow-run-inspector-step",
            ".workflow-run-inspector-step-status",
            ".workflow-run-inspector-step-actions",
            ".workflow-run-inspector-retry",
        ]:
            self.assertIn(marker, self.css)

    def test_main_surface_exposes_compact_agent_workbench_plan(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="agentWorkbenchBar"',
            'id="agentWorkbenchLight"',
            'id="agentWorkbenchLine"',
            'id="agentWorkbenchDetail"',
            'id="agentPlanRefreshButton"',
            "Agent 操作计划",
        ]:
            self.assertIn(marker, main_html + self.js)
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        self.assertIn('id="agentWorkbenchBar"', operation_html)
        self.assertIn('id="operationWorkspaceMeta"', operation_html)
        self.assertIn('id="operationCompilerPanel"', operation_html)
        self.assertIn('id="operationPlanStats"', operation_html)
        self.assertIn('id="operationCompilerChecks"', operation_html)
        self.assertIn('id="operationDryRunDetails"', operation_html)
        self.assertIn('id="operationCompilerRepairActions"', operation_html)
        for marker in [
            "state.agentOperation",
            "function renderAgentWorkbench",
            "function renderOperationCompilerPanel",
            "function renderOperationDryRunDetails",
            "function renderOperationCompilerRepairActions",
            "function runOperationCompilerRepairAction",
            "function refreshAgentPlan",
            "function scheduleAgentPlanRefresh",
            "postCompanionAgentPlan",
            "companionPayload('agent_plan'",
            "operation.nextActions",
            "operation.operationPlan",
            "operation.verificationPlan",
            "operation.operationCompiler",
            "function operationActionGate",
            "data-operation-gate-status",
            "data-operation-repair-action",
            "codex.mn.perOperationDryRun.v1",
            "operation-dry-run-details",
            "operation-dry-run-row",
            "verificationLevel",
            "Operation Compiler 阻断",
            "写入需确认",
            "Dry-run",
        ]:
            self.assertIn(marker, self.js)
        for removed in [
            "primaryActionGrid",
            "workflowActionPanel",
            "mainPinnedButtonsPanel",
        ]:
            self.assertNotIn(removed, main_html)
        self.assertIn(".agent-workbench-bar", self.css)
        self.assertIn(".agent-workbench-light", self.css)
        self.assertIn(".operation-compiler-panel", self.css)
        self.assertIn(".operation-plan-stat", self.css)
        self.assertIn(".operation-compiler-check", self.css)
        self.assertIn(".operation-compiler-repair-actions", self.css)
        self.assertIn(".workbench-action-button:disabled", self.css)
        self.assertIn(".workbench-action-button.blocked", self.css)

    def test_object_graph_exposes_manual_relation_editor(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        object_html = main_html.split('id="objectWorkspacePanel"', 1)[1].split('id="operationWorkspacePanel"', 1)[0]
        for marker in [
            'id="objectGraphRelationAddButton"',
            'id="objectGraphRelationEditor"',
            'id="objectGraphRelationTargetInput"',
            'id="objectGraphRelationTypeInput"',
            'id="objectGraphRelationLabelInput"',
            'id="objectGraphRelationNoteInput"',
            'id="objectGraphRelationSaveButton"',
            'id="objectGraphRelationCancelButton"',
            "添加关系",
            "目标对象 ID",
            "关系类型",
        ]:
            self.assertIn(marker, object_html)
        for marker in [
            "function openObjectGraphRelationEditor",
            "function closeObjectGraphRelationEditor",
            "function saveObjectGraphRelation",
            "object_graph_relation_save",
            "object_graph_relation_delete",
            "manual_relation",
            "manual_mn_object",
            "object-graph-relation-editor",
            "object-graph-relation-actions",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_main_surface_exposes_mindmap_diff_apply_verification_status(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="mindmapDiffApplyStatus"',
            'id="mindmapDiffApplyLight"',
            'id="mindmapDiffApplyText"',
            "function renderMindmapDiffApplyStatus",
            "state.mindmapDiffApply",
            "result.mindmapDiffApply",
            "codex.mn.mindmapDiffApplyStatus.v1",
            "failedVerificationCount",
            "operationVerification",
            "脑图验证",
            ".mindmap-diff-apply-status",
        ]:
            self.assertIn(marker, main_html + self.js + self.css)

    def test_operation_workspace_exposes_verification_center(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        for marker in [
            'id="verificationReportPanel"',
            'id="realMnAcceptancePanel"',
            'id="realMnAcceptanceStatusLine"',
            'id="realMnAcceptanceChecklist"',
            'id="realMnAcceptanceRunAllButton"',
            'id="singleDocumentAcceptanceLine"',
            'id="singleDocumentAcceptanceDetail"',
            'id="singleDocumentAcceptanceButton"',
            'id="mainUiFunctionalAcceptanceLine"',
            'id="mainUiFunctionalAcceptanceDetail"',
            'id="mainUiFunctionalAcceptanceButton"',
            'id="realMnAcceptanceSafeEvidenceButton"',
            'id="mainNativeHighlightWizardPanel"',
            'id="mainNativeHighlightWizardLine"',
            'id="mainNativeHighlightWizardDetail"',
            'id="mainNativeHighlightWizardActions"',
            'id="nativeHighlightWizardRetryButton"',
            'id="nativeHighlightWizardRefreshButton"',
            'id="verificationReportRefreshButton"',
            'id="verificationReportSummary"',
            'id="verificationReportCounts"',
            'id="verificationReportList"',
            'id="verificationReportActionStatus"',
            'id="verificationRepairPlanPanel"',
            'id="verificationRepairPlanSummary"',
            'id="verificationRepairPlanRecommendedButton"',
            'id="verificationRepairPlanActions"',
            "Verification Center",
            "真实 MN4 验收",
            "运行验收流程",
            "当前文档验收",
            "任意文档 UI 验收",
            "安全采证",
            "原生高亮恢复",
            "启动采证",
            "function renderNativeHighlightWizard",
            "nativeHighlightWizardRetryButton",
            "nativeHighlightWizardRefreshButton",
            "secondsRemaining",
            "latestEventReason",
            "recoverable",
            "function refreshVerificationCenter",
            "function renderVerificationCenter",
            "function renderRealMnAcceptancePanel",
            "function renderRealMnAcceptanceOverview",
            "function runRealMnAcceptanceSequence",
            "function setVerificationCenterActionStatus",
            "function renderVerificationRepairPlan",
            "function runVerificationRepairRecommended",
            "postCompanion('verification_report_list'",
            "postCompanion('single_document_acceptance_summary'",
            "postCompanion('ui_functional_acceptance_summary'",
            "function runVerificationCenterAction",
            "data-verification-center-action",
            "data-verification-repair-action",
            "data-verification-recommended-action",
            "postCompanion(action.action",
            "state.verificationCenter",
            "state.verificationCenterActionStatus",
            "state.verificationCenter.repairPlan",
            "verification-center-row",
            "verification-center-action",
            "verification-center-action-status",
            "verification-repair-plan",
            "verification-repair-recommended",
            "verification-center-counts",
            "real-mn-acceptance-panel",
            "real-mn-acceptance-actions",
        ]:
            self.assertIn(marker, operation_html + self.js + self.css)

    def test_ui_functional_acceptance_webview_entry_avoids_self_recursive_gate(self) -> None:
        marker = "postCompanion('ui_functional_acceptance_summary', {"
        self.assertIn(marker, self.js)
        call_start = self.js.index(marker)
        call_body = self.js[call_start:self.js.index("}, function(result)", call_start)]
        self.assertIn("browserRender: true", call_body)
        self.assertIn("browserInteraction: true", call_body)
        self.assertIn("browserActions: false", call_body)
        self.assertIn("browserWriteActions: false", call_body)
        self.assertIn("invocationSurface: 'marginnote-webview'", call_body)
        self.assertNotIn("fullBrowser: true", call_body)

    def test_operation_workspace_exposes_ai_edit_transaction_center(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        for marker in [
            'id="aiEditTransactionCenter"',
            'id="aiEditTransactionTitle"',
            'id="aiEditTransactionSummary"',
            'id="aiEditTransactionNotes"',
            'id="aiEditTransactionResidualProof"',
            'id="aiEditTransactionActions"',
            "事务中心",
        ]:
            self.assertIn(marker, operation_html)
        self.assertLess(operation_html.index('id="mindmapDiffApplyStatus"'), operation_html.index('id="aiEditTransactionCenter"'))

        for marker in [
            "state.aiEditTransactionStatus",
            "result.aiEditTransactionStatus",
            "'aiEditTransactionResidualProof'",
            "function renderAiEditTransactionCenter",
            "codex.mn.aiEditTransactionStatus.v1",
            "remainingNoteIds",
            "createdNoteIds",
            "residualProof",
            "codex.mn.residualProof.v1",
            "function renderAiEditTransactionResidualProof",
            "ai-edit-residual-proof",
            "ai-edit-residual-object",
            "verificationLevel",
            "actualState",
            "expectedState",
            "逐对象残留证明",
            "验证：残留 cardId",
            "remainingCardIds",
            "failedCardIds",
            "创建卡片",
            "objectRef",
            "mnObjectId",
            "事务对象",
            "data-transaction-state",
            "data-transaction-id",
            "function renderAiEditTransactionActions",
            "function retainAiEditTransaction",
            "function rollbackAiEditTransaction",
            "function confirmMindmapDeleteTransaction",
            "function dismissMindmapDeleteTransaction",
            "function refreshAiEditTransactionVerification",
            "function requestAiEditObjectExistenceProbe",
            "function showAiEditTransactionEvidence",
            "function bridgeAiEditTransactionWithEvidence",
            "createdNoteIds: (tx.createdNoteIds || []).join('|')",
            "createdCardIds: (tx.createdCardIds || []).join('|')",
            "targetNoteIds: (tx.targetNoteIds || []).join('|')",
            "bridge(path, payload)",
            "bridgeAiEditTransactionWithEvidence('accept_ai_edit_transaction'",
            "bridgeAiEditTransactionWithEvidence('reject_ai_edit_transaction'",
            "bridgeAiEditTransactionWithEvidence('confirm_mindmap_delete_transaction'",
            "bridgeAiEditTransactionWithEvidence('dismiss_mindmap_delete_transaction'",
            "delete_pending_confirmation",
            "confirm_delete",
            "删除",
            "忽略",
            "postCompanion('ai_edit_transaction_verify'",
            "postCompanion('request_mn_object_existence_probe'",
            "postCompanion('ai_edit_transaction_get'",
            "ai-edit-transaction-actions",
            "ai-edit-transaction-retain",
            "ai-edit-transaction-rollback",
            "ai-edit-transaction-verify",
            "ai-edit-transaction-evidence",
            "ai-edit-transaction-probe",
            "保留",
            "回滚",
            "验证",
            "检查真实对象",
            "证据",
            "ai-edit-transaction-center",
            "ai-edit-transaction-note",
            "回滚",
            "残留",
            "noteId",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_operation_workspace_keeps_latest_mindmap_diff_bench_visible(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        operation_html = main_html.split('id="operationWorkspacePanel"', 1)[1].split("</aside>", 1)[0]
        for marker in [
            'id="mindmapDiffWorkbench"',
            'id="mindmapDiffWorkbenchTitle"',
            'id="mindmapDiffWorkbenchSummary"',
            'id="mindmapDiffWorkbenchPreview"',
            "脑图 Diff 编辑台",
        ]:
            self.assertIn(marker, operation_html)
        self.assertLess(operation_html.index('id="mindmapTreePreviewList"'), operation_html.index('id="mindmapDiffWorkbench"'))
        self.assertLess(operation_html.index('id="mindmapDiffWorkbench"'), operation_html.index('id="operationWorkspaceVerification"'))

        for marker in [
            "state.latestMindmapDiff",
            "function renderMindmapDiffWorkbench",
            "result.mindmapDiff",
            "result.mindmapDiffOperationPlan",
            "mindmapDiffOperationCanApplyLocally(operation)",
            "renderMindmapDiffWorkbench(result)",
            "mindmap-diff-workbench",
            "mindmap-diff-workbench-row",
            "data-mutation",
            "新增",
            "更新",
            "合并",
            "移动",
            "建议删除",
            "局部执行",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_formal_config_page_owns_runtime_context_and_ai_status(self) -> None:
        for marker in [
            'id="configPage"',
            'id="configBackButton"',
            'id="settingsNotebookLine"',
            'id="settingsDocumentLine"',
            'id="settingsContextScopeLine"',
            'id="contextButton"',
            'id="contextScopeAutoButton"',
            'id="contextScopeSelectionButton"',
            'id="contextScopeDocumentButton"',
            'id="contextSourceLine"',
            'id="selectionPreview"',
            'id="readinessPanel"',
            'id="aiBackendSelect"',
            'id="mnApiStatusLine"',
            'id="mnApiBackendSelect"',
            'id="mnUrlApiSecretInput"',
            'id="clearMnUrlApiSecretButton"',
            'id="codexCliPathInput"',
            'id="openaiApiKeyInput"',
            'id="modelPresetSelect"',
            'id="modelPresetButtonGroup"',
            'id="modelInput"',
            'id="applyModelInputButton"',
            'id="aiProfileStatusLine"',
            'id="speedSelect"',
            'id="speedChoiceGroup"',
            'id="speedCodexConfigButton"',
            'id="speedPriorityButton"',
            'id="reasoningEffortSelect"',
            'id="reasoningEffortChoiceGroup"',
            'id="reasoningEffortCodexConfigButton"',
            'id="reasoningEffortXhighButton"',
            'id="reasoningEffortUltraButton"',
            'id="proxyUrlInput"',
            'id="defaultContextScopeSelect"',
            'id="permissionSelect"',
            'id="saveSettingsButton"',
            'id="aiBackendProbeButton"',
            'id="nativeCapabilitiesRefreshButton"',
            'id="githubRepoInput"',
            'id="updateCheckButton"',
            'id="updateInstallButton"',
            'id="updateNotice"',
            "openConfigPage",
            "closeConfigPage",
            "renderSettingsContextMeta",
            "renderSpeedSelector",
            "updateSpeedChoice",
            "renderReasoningEffortSelector",
            "updateReasoningEffortChoice",
            "renderModelSelector",
            "updateModelInputFromPreset",
            "syncModelPresetFromInput",
            "saveAiProfilePatch",
            "applyModelInput",
            "choice-button-grid",
            "模型会自动读取 Codex CLI 当前可用列表",
            "gpt-5.6-sol",
            "gpt-5.6-terra",
            "gpt-5.6-luna",
            "renderMnApiStatus",
            "checkForUpdates",
            "installUpdate",
            "renderUpdateStatus",
            ".config-page",
            "position: fixed;",
            "display: flex;",
            "flex-direction: column;",
            ".config-body",
            "overflow: auto;",
        ]:
            self.assertIn(marker, self.html + self.js + self.css)

        self.assertIn("saveAiProfilePatch({speed: value}", self.js)
        self.assertIn("saveAiProfilePatch({reasoningEffort: value}", self.js)
        self.assertIn("saveAiProfilePatch({model: preset}", self.js)
        self.assertIn("saveAiProfilePatch({model: model}", self.js)
        self.assertIn("postCompanion('settings_update'", self.js)

        config_html = self.html.split('<section id="configPage"', 1)[1]
        for marker in [
            'id="contextButton"',
            'id="contextScopeAutoButton"',
            'id="contextScopeSelectionButton"',
            'id="contextScopeDocumentButton"',
            'id="contextSourceLine"',
            'id="selectionPreview"',
            "当前内容 / 节点",
        ]:
            self.assertIn(marker, config_html)

        topbar = self.html.split('<section class="topbar">', 1)[1].split("</section>", 1)[0]
        self.assertNotIn('id="readinessPanel"', topbar)
        self.assertNotIn("Notebook:", topbar)
        render_context_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]
        self.assertNotIn("'Notebook: '", render_context_body)
        self.assertIn("renderSettingsContextMeta", render_context_body)

    def test_config_page_hides_unused_queue_files_custom_buttons_and_release_tools(self) -> None:
        for marker in [
            'id="queueBadge"',
            'id="runToggleButton"',
            'id="historyButton"',
            'id="clearHistoryButton"',
            'id="fileInput"',
            'id="filePathInput"',
            'id="uploadButton"',
            'id="presetButtonsList"',
            'id="customButtonsList"',
            'id="mainPinnedButtonsPanel"',
            'id="mainPinnedButtonsList"',
            'id="mainPinnedManagerList"',
            'id="customButtonIndexInput"',
            'id="customButtonTitleInput"',
            'id="customButtonActionSelect"',
            'id="customButtonPromptInput"',
            'id="customButtonShowOnMainInput"',
            'id="newCustomButtonButton"',
            'id="saveCustomButtonButton"',
            'id="deleteCustomButtonButton"',
            'id="runtimeEvidenceButton"',
            'id="settingsHighlightStatusButton"',
            'id="nativeHighlightWizardButton"',
            'id="releaseAcceptanceButton"',
            '<option value="local">',
            "队列与生成",
            "上下文文件",
            "自定义按钮",
            "诊断与验收",
            "发布验收",
            "高亮采证",
        ]:
            self.assertNotIn(marker, self.html)
        config_html = self.html.split('<section id="configPage"', 1)[1]
        self.assertNotIn('id="singleDocumentAcceptanceButton"', config_html)
        self.assertNotIn("本文档验收", config_html)
        for marker in [
            'id="defaultContextScopeSelect"',
            'id="permissionDiagnoseButton"',
            'id="cacheCurrentPdfButton"',
            'id="nativeCapabilitiesRefreshButton"',
            'id="uiFunctionalAcceptanceLine"',
            'id="uiFunctionalAcceptanceDetail"',
            'id="uiFunctionalAcceptanceButton"',
            "defaultContextScope",
            "UI 功能验收",
            "真实 MN4 运行态",
            "不等于真实 MN4 当前文档验收通过",
            "realMnRuntimeSafeEvidenceButton",
            "一键安全采证",
            "function renderUiFunctionalAcceptance",
            "function runRealMnRuntimeSafeEvidence",
            "function checkUiFunctionalAcceptance",
            "ui_functional_acceptance_summary",
            "bindButton('uiFunctionalAcceptanceButton', checkUiFunctionalAcceptance)",
        ]:
            self.assertIn(marker, self.html + self.js)
        self.assertEqual(self.html.count('id="permissionDiagnoseButton"'), 1)
        save_body = self.js.split("function saveSettings()", 1)[1].split("\n  function clearOpenAIKey", 1)[0]
        self.assertIn("defaultContextScope: getValue('defaultContextScopeSelect')", save_body)
        self.assertIn("githubRepo: getValue('githubRepoInput')", save_body)
        self.assertIn("mnApiBackend: getValue('mnApiBackendSelect')", save_body)
        self.assertIn("mnUrlApiSecret: mnUrlApiSecret", save_body)
        self.assertIn("setValue('mnUrlApiSecretInput', '')", save_body)
        self.assertIn("clearMnUrlApiSecret", self.js)

    def test_main_surface_has_update_notice_but_no_update_install_controls(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]

        self.assertIn('id="updateNotice"', main_html)
        self.assertIn('id="updateNoticeText"', main_html)
        self.assertIn('id="updateNoticeOpenSettingsButton"', main_html)
        self.assertNotIn('id="updateInstallButton"', main_html)
        self.assertNotIn('id="githubRepoInput"', main_html)

    def test_main_surface_exposes_bottom_pdf_cache_status_light(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        composer = main_html.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]

        self.assertIn('id="pdfCacheBanner"', composer)
        self.assertIn('id="pdfCacheBannerLight"', composer)
        self.assertIn('id="pdfCacheBannerText"', composer)
        self.assertIn('id="pdfCacheFileBannerButton"', composer)
        self.assertLess(composer.index('id="promptInput"'), composer.index('id="pdfCacheBanner"'))
        self.assertIn("renderPdfCacheBanner", self.js)
        self.assertIn("waiting_native", self.js)
        self.assertIn("pdfState === 'cached'", self.js)
        self.assertIn("pdfState === 'permission'", self.js)
        self.assertIn("pdfState === 'error'", self.js)
        self.assertIn("PDF缓存", self.js)
        self.assertIn(".pdf-cache-banner", self.css)
        self.assertIn(".pdf-cache-light", self.css)
        self.assertIn(".pdf-cache-banner.cached .pdf-cache-light", self.css)
        self.assertIn(".pdf-cache-banner.waiting .pdf-cache-light", self.css)
        self.assertIn(".pdf-cache-banner.error .pdf-cache-light", self.css)

    def test_pdf_cache_has_manual_file_picker_fallback(self) -> None:
        config_html = self.html.split('<section id="configPage"', 1)[1]
        composer = self.html.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]

        for marker in [
            'id="pdfCacheFileInput"',
            'type="file"',
            'accept="application/pdf,.pdf"',
            'id="pdfCacheFileButton"',
            'id="pdfCacheFileBannerButton"',
            "choosePdfCacheFile",
            "uploadSelectedPdfCacheFile",
            "readAsDataURL(file)",
            "cache_pdf_from_marginnote",
            "pdfBase64",
            "browser_pdf_file_upload",
        ]:
            self.assertIn(marker, self.html + self.js)
        self.assertIn('id="pdfCacheFileButton"', config_html)
        self.assertIn('id="pdfCacheFileBannerButton"', composer)
        self.assertIn(".pdf-cache-action", self.css)

    def test_pdf_cache_status_light_follows_native_status_text(self) -> None:
        set_status_body = self.js.split("setStatus: function(payload)", 1)[1].split(
            "\n    setReply:", 1
        )[0]

        self.assertIn("renderPdfCacheStatusFromText", self.js)
        self.assertIn("renderPdfCacheStatusFromText(text)", set_status_body)
        self.assertIn("PDF 缓存完成", self.js)
        self.assertIn("PDF 缓存失败", self.js)
        self.assertIn("正在上传当前 PDF 缓存", self.js)

    def test_pdf_cache_status_light_stays_visible_when_state_is_unknown(self) -> None:
        composer = self.html.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]
        render_body = self.js.split("function renderPdfCacheBanner", 1)[1].split(
            "\n  function renderControls", 1
        )[0]

        self.assertIn('id="pdfCacheBanner" class="pdf-cache-banner idle"', composer)
        self.assertIn("PDF缓存：等待当前文档", composer)
        self.assertIn("pdfState === 'unknown' || pdfState === 'missing'", render_body)
        self.assertIn("className = 'pdf-cache-banner idle'", render_body)
        self.assertNotIn("pdf-cache-banner hidden", render_body)

    def test_context_ready_auto_requests_pdf_cache_once_per_document(self) -> None:
        state_header = self.js.split("var state = {", 1)[1].split("\n  };", 1)[0]
        render_context_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]

        self.assertIn("autoPdfCacheRequestedKey", state_header)
        self.assertIn("function autoRequestPdfCacheForCurrentContext", self.js)
        auto_cache_body = self.js.split("function autoRequestPdfCacheForCurrentContext", 1)[1].split(
            "\n  function renderContext", 1
        )[0]
        self.assertIn("autoRequestPdfCacheForCurrentContext()", render_context_body)
        self.assertIn("request_pdf_cache", auto_cache_body)
        self.assertIn("state.autoPdfCacheRequestedKey = docKey", auto_cache_body)
        self.assertIn("normalizePdfCacheState(state.pdfCache)", auto_cache_body)
        self.assertIn("cached", auto_cache_body)
        self.assertIn("waiting_native", auto_cache_body)
        self.assertIn("topicid", auto_cache_body)
        self.assertIn("bookmd5", auto_cache_body)

    def test_document_switch_starts_a_fresh_document_conversation(self) -> None:
        render_context_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]
        post_body = self.js.split("function postCompanion(action", 1)[1].split(
            "\n  function postCompanionPath", 1
        )[0]
        complete_switch_body = self.js.split("function completeAutomaticDocumentSwitch", 1)[1].split(
            "\n  function renderContext", 1
        )[0]

        self.assertIn("state.context.contextDocumentKey", render_context_body)
        self.assertIn("scheduleAutomaticDocumentSwitch", render_context_body)
        self.assertNotIn("resetConversationForDocumentChange", render_context_body)
        self.assertIn("resetConversationForDocumentChange", complete_switch_body)
        self.assertIn("state.conversationId = ''", self.js)
        self.assertIn("state.sessionId = ''", self.js)
        self.assertIn("state.autoPdfCacheRequestedKey = ''", self.js)
        self.assertIn("requestDocumentKey", post_body)
        self.assertIn("staleDocument", post_body)
        self.assertIn("staleBinding", post_body)
        self.assertIn("requestBindingMatchesActiveSession", post_body)
        queued_body = self.js.split("function runQueuedCommand(command, options)", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        self.assertIn("queuedDocumentKey", queued_body)
        self.assertIn("任务属于另一个文件", queued_body)

    def test_context_source_explains_selected_mindmap_node_document_fallback(self) -> None:
        source_line_body = self.js.split("function renderContextSourceLine(ctx)", 1)[1].split(
            "\n  window.CodexPanel", 1
        )[0]

        self.assertIn("selected_mindmap_node", source_line_body)
        self.assertIn("当前节点关联文件", source_line_body)

    def test_update_button_opens_release_page_without_installing(self) -> None:
        install_body = self.js.split("function installUpdate()", 1)[1].split("\n  function trimText", 1)[0]

        self.assertNotIn("window.confirm", install_body)
        self.assertNotIn("postCompanion('update_install'", install_body)
        self.assertIn("postCompanion('open_url'", install_body)
        self.assertIn("bridge('open_url'", install_body)
        self.assertIn("releaseUrl", install_body)
        self.assertIn("downloadUrl", install_body)
        self.assertIn("正在打开下载页面", install_body)
        self.assertIn("打开下载页", self.html + self.js)

    def test_update_check_shows_in_progress_feedback(self) -> None:
        check_body = self.js.split("function checkForUpdates", 1)[1].split("\n  function installUpdate", 1)[0]

        self.assertIn("updateCheckButton", check_body)
        self.assertIn("检查中...", check_body)
        self.assertIn("正在检查 GitHub Release", check_body)
        self.assertIn("button.disabled = true", check_body)
        self.assertIn("button.disabled = false", check_body)

    def test_main_update_notice_only_shows_successful_available_release(self) -> None:
        update_body = self.js.split("function renderUpdateStatus", 1)[1].split("\n  function openUpdateSettings", 1)[0]

        self.assertIn("showNotice", update_body)
        self.assertIn("update.available", update_body)
        self.assertIn("update.ok !== false", update_body)
        self.assertIn("status !== 'error'", update_body)
        self.assertIn("showNotice ? 'update-notice' : 'update-notice hidden'", update_body)

    def test_config_page_exposes_context_scope_like_builtin_ai(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        config_html = self.html.split('<section id="configPage"', 1)[1]

        for marker in [
            'id="contextScopeAutoButton"',
            'id="contextScopeSelectionButton"',
            'id="contextScopeDocumentButton"',
            'data-context-scope="auto"',
            'data-context-scope="selection"',
            'data-context-scope="document"',
            'id="contextSourceLine"',
            'id="selectionPreview"',
            'data-context-state="empty"',
        ]:
            self.assertIn(marker, config_html)

        for marker in [
            'id="contextButton"',
            'id="contextScopeAutoButton"',
            'id="contextSourceLine"',
            'id="selectionPreview"',
            "当前内容 / 节点",
        ]:
            self.assertNotIn(marker, main_html)

        for marker in [
            "AI 可见：未选择上下文",
            "setContextScope",
            "payload.contextScope = currentContextScope()",
            "renderContextSourceLine",
            "PDF 选区",
            "脑图节点",
            "当前文档",
            "当前文档全文检索",
        ]:
            self.assertIn(marker, self.html + self.js)

    def test_config_page_exposes_file_path_management_and_diagnostic_logs(self) -> None:
        config_html = self.html.split('<section id="configPage"', 1)[1]

        for marker in [
            "文件路径管理",
            'id="fileSearchRootsInput"',
            'id="fileSearchRootsStatusLine"',
            'id="saveFileSearchRootsButton"',
            "parseFileSearchRootsInput",
            "renderFileSearchRoots",
            "fileSearchRoots: parseFileSearchRootsInput()",
            "保存文件路径",
            "日志与诊断",
            'id="logsStatusLine"',
            'id="logsList"',
            'id="logsRefreshButton"',
            'id="logsClearButton"',
            "refreshDiagnosticLogs",
            "renderDiagnosticLogs",
            "postCompanion('logs_recent'",
            "postCompanion('logs_clear'",
        ]:
            self.assertIn(marker, config_html + self.js)

        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        self.assertNotIn("文件路径管理", main_html)
        self.assertNotIn("日志与诊断", main_html)

    def test_pdf_math_unicode_repair_is_applied_to_visible_context(self) -> None:
        main_js = (ROOT / "main.js").read_text(encoding="utf-8")
        for marker in [
            "repairPdfExtractedMathText",
            "looksLikePdfMathUnicodeLoss",
            "0x10000",
            "selectionTextFromDocumentController",
        ]:
            self.assertIn(marker, main_js + self.js)
        self.assertIn("repairContextPayload", self.js)
        self.assertIn("repairPdfExtractedMathText(text)", self.js)

    def test_native_context_exports_document_title_for_file_root_resolution(self) -> None:
        main_js = (ROOT / "main.js").read_text(encoding="utf-8")
        for marker in [
            "documentTitleFromDocumentObject",
            "documentTitleFromNotebookController",
            "documentFileName",
            "sourceFileName",
            "documentTitle: documentTitle",
            "documentFileName: documentTitle",
        ]:
            self.assertIn(marker, main_js)

    def test_empty_selection_update_clears_stale_web_context(self) -> None:
        set_prompt_body = self.js.split("setPrompt: function(payload)", 1)[1].split("\n    setStatus:", 1)[0]

        self.assertIn("state.lastPromptFromSelection = text", set_prompt_body)
        self.assertIn("delete state.context.selectionText", set_prompt_body)
        self.assertIn("delete state.context.selectedText", set_prompt_body)
        self.assertIn("renderContextPreview()", set_prompt_body)

    def test_web_panel_polls_context_to_notice_selection_clear(self) -> None:
        self.assertIn("startContextAutoRefresh", self.js)
        self.assertIn("bridge('context', {reason: 'auto-refresh'})", self.js)
        self.assertIn("state.contextAutoRefreshTimer", self.js)

    def test_background_context_refresh_does_not_mutate_prompt_text(self) -> None:
        main_js = (ROOT / "main.js").read_text(encoding="utf-8")
        context_branch = main_js.split("} else if (action === 'context') {", 1)[1].split(
            "\n    }", 1
        )[0]

        self.assertIn("this.lastSelectionText = ''", context_branch)
        self.assertNotIn("setPromptText('')", context_branch)
        self.assertNotIn('setPromptText("")', context_branch)

    def test_background_refresh_pauses_while_text_input_is_active(self) -> None:
        auto_refresh_body = self.js.split("function startContextAutoRefresh", 1)[1].split(
            "\n  function refreshHistory", 1
        )[0]
        clear_prompt_body = self.js.split("function clearPromptInputAfterSend", 1)[1].split(
            "\n  function actionLabel", 1
        )[0]

        self.assertIn("function isTextInputActive", self.js)
        self.assertIn("isTextInputActive()", auto_refresh_body)
        self.assertIn("return", auto_refresh_body)
        self.assertIn("5000", auto_refresh_body)
        self.assertIn("releaseTextInputFocus", clear_prompt_body)

    def test_ai_chat_has_stop_generation_control_but_no_queue_control(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        self.assertIn('id="stopButton"', self.html)
        self.assertIn("bindButton('stopButton', stopCurrent)", self.js)
        self.assertIn("renderStopButton", self.js)
        self.assertNotIn('id="runToggleButton"', main_html)
        self.assertNotIn('id="queueBadge"', main_html)

    def test_send_button_stays_in_bottom_composer(self) -> None:
        composer = self.html.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]
        self.assertIn('id="promptInput"', composer)
        self.assertIn('id="sendButton"', composer)
        self.assertIn('data-action="chat"', composer)
        self.assertLess(composer.index('id="promptInput"'), composer.index('id="sendButton"'))
        for marker in [
            '.ai-chat-shell[data-product-mode="workspace"] #commandPanePanel',
            "position: fixed;",
            "bottom: 0;",
            "z-index: 20;",
            ".ai-chat-shell[data-product-mode=\"workspace\"] .workbench-layout",
            "padding-bottom: 132px;",
        ]:
            self.assertIn(marker, self.css)

    def test_send_button_label_is_two_centered_lines(self) -> None:
        composer = self.html.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]
        for marker in [
            'class="send-button-main">发送</span>',
            'class="send-button-sub">可排队</span>',
            "flex-direction: column",
            "align-items: center",
            "justify-content: center",
            ".send-button-sub",
        ]:
            self.assertIn(marker, composer + self.css)

    def test_send_button_is_excluded_from_busy_queue_pseudo_label(self) -> None:
        self.assertIn('button[data-busy="queue-available"][data-action-state="ready"]:not(#sendButton)', self.css)
        self.assertIn('button[data-busy="queue-available"][data-action-state="ready"]:not(#sendButton)::after', self.css)
        self.assertNotIn('button[data-busy="queue-available"][data-action-state="ready"]::after {\n  content: "可排队";', self.css)

    def test_send_action_always_uses_chat(self) -> None:
        send_body = self.js.split("function sendAction", 1)[1].split("\n  function normalizePdfCacheState", 1)[0]
        self.assertIn("executeAction('chat'", send_body)
        self.assertIn("currentContextScope() !== 'document'", send_body)
        self.assertNotIn("routeNaturalLanguageAction", send_body)
        self.assertNotIn("generate_card", send_body)
        self.assertNotIn("generate_mindmap", send_body)
        self.assertNotIn("request_native_highlight_selection", send_body)

    def test_enter_sends_and_shift_enter_keeps_newline(self) -> None:
        keydown_body = self.js.split("byId('promptInput').addEventListener('keydown'", 1)[1].split(
            "\n    byId('promptInput').addEventListener('input'", 1
        )[0]

        self.assertIn("ev.keyCode === 13", keydown_body)
        self.assertIn("ev.isComposing", keydown_body)
        self.assertIn("!ev.shiftKey", keydown_body)
        self.assertIn("ev.preventDefault()", keydown_body)
        self.assertIn("sendAction('chat')", keydown_body)

    def test_chat_reply_does_not_offer_follow_up_tool_buttons(self) -> None:
        request_body = self.js.split("function requestTextAction", 1)[1].split("\n  function promptValue", 1)[0]
        self.assertNotIn("showFollowUpGuides(action, prompt)", request_body)
        self.assertIn("reportActionResponse(action, result || {})", request_body)

    def test_latest_reply_exposes_agent_next_actions(self) -> None:
        controls_body = self.js.split("function buildReplyAgentActions", 1)[1].split(
            "\n  function runGuideItem", 1
        )[0]
        for marker in [
            "addAssistantReplyWithActions",
            "buildReplyAgentActions",
            "runAgentNextAction",
            "state.agentOperation.nextActions",
            "data-agent-next-action",
            "reply-mindmap-tree-button",
            "生成脑图树",
            "预览写入计划",
            "预览脑图 Diff",
            "检索相关知识",
            "operation_plan_preview",
            "mindmap_diff_preview",
            "knowledge_index_search",
        ]:
            self.assertIn(marker, self.js + self.css)
        for removed in [
            "reply-mindmap-menu",
            "reply-mindmap-menu-item",
            "回答添加到脑图",
            "对话添加到脑图（双向同步）",
            "在脑图中创建卡片树",
            "aria-expanded",
        ]:
            self.assertNotIn(removed, controls_body + self.css)
        self.assertNotIn("buildReplyMindmapControls", self.js)

    def test_reply_card_tree_prompt_uses_explicit_create_card_tree_command(self) -> None:
        for marker in [
            "[create_card_tree]",
            "根据上面的回答创建一个结构化的脑图树（使用markdown大纲格式）",
            "buildReplyMindmapPrompt",
        ]:
            self.assertIn(marker, self.js)
        self.assertNotIn("[answer_to_mindmap]", self.js)
        self.assertNotIn("[conversation_to_mindmap]", self.js)

    def test_mindmap_prompts_request_complete_multi_level_outline(self) -> None:
        for marker in [
            "覆盖全文章节",
            "二级主题",
            "三级细节点",
            "Markdown 层级",
            "覆盖统计",
            "## 一级主题",
            "### 二级主题",
            "#### 三级细节点",
        ]:
            self.assertIn(marker, self.js)

    def test_ai_edit_operation_confirmation_replaces_hidden_draft_panel(self) -> None:
        for marker in [
            "renderAiEditOperation",
            "AI 编辑操作",
            "Created ",
            " card(s)",
            "操作计划：",
            "Dry-run：",
            "ai-edit-accept",
            "ai-edit-reject",
            "postCompanionPath('/marginnote/draft', 'draft_save'",
            "bridge('write_draft'",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertNotIn("全部接受", self.js + self.html)
        self.assertNotIn("全部拒绝", self.js + self.html)

    def test_ai_edit_operation_surfaces_card_factory_quality_summary(self) -> None:
        for marker in [
            "function cardFactoryQualityLines",
            "cardQuality",
            "cardFactory",
            "typeCounts",
            "missingSourceCount",
            "longCardCount",
            "duplicateTitleCount",
            "卡片工厂：",
            "卡型：",
            "缺来源：",
            "长卡：",
            "重复标题：",
            "ai-edit-card-quality",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_ai_edit_operation_is_shown_after_native_write_and_can_reject_transaction(self) -> None:
        main_js = (ROOT / "main.js").read_text(encoding="utf-8")
        for marker in [
            "writeDraftForAiEditOperation",
            "state.pendingAiEditDrafts",
            "CodexPanel.setAiEditOperationReady",
            "reject_ai_edit_transaction",
            "accept_ai_edit_transaction",
            "draftId: draftId",
            "transactionId",
        ]:
            self.assertIn(marker, self.js + main_js)
        draft_body = self.js.split("function requestDraftAction", 1)[1].split(
            "\n  function stagePromptAction", 1
        )[0]
        save_body = draft_body.split("postCompanionPath('/marginnote/draft', 'draft_save'", 1)[1].split(
            "\n        } else {", 1
        )[0]
        self.assertIn("writeDraftForAiEditOperation(saved.draft)", save_body)
        self.assertNotIn("renderAiEditOperation(saved.draft)", save_body)
        self.assertIn("等待确认", self.js)

    def test_ai_edit_result_fetches_verification_report(self) -> None:
        result_body = self.js.split("setAiEditOperationResult: function(payload)", 1)[1].split(
            "\n    setBusy:", 1
        )[0]
        for marker in [
            "function refreshAiEditVerification",
            "function renderAiEditVerification",
            "ai_edit_transaction_verify",
            "transactionId: transactionId",
            "verification.summary",
            "回滚验证",
        ]:
            self.assertIn(marker, self.js)
        self.assertIn("refreshAiEditVerification(transactionId", result_body)
        self.assertIn("ai-edit-verification", self.css)

    def test_mindmap_diff_preview_renders_accept_reject_operation_panel(self) -> None:
        agent_body = self.js.split("function runAgentNextAction", 1)[1].split(
            "\n  function buildReplyAgentActions", 1
        )[0]
        for marker in [
            "function renderMindmapDiffOperation",
            "function buildMindmapDiffOperationPanel",
            "function acceptMindmapDiff",
            "function rejectMindmapDiff",
            "脑图 Diff 预览",
            "新增 ",
            "更新 ",
            "合并 ",
            "重复 ",
            "mindmap-diff-operation",
            "mindmap-diff-accept",
            "mindmap-diff-reject",
            "writeAcceptedDraft(draftId",
            "postCompanion('draft_delete'",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertIn("renderMindmapDiffOperation(result)", agent_body)
        self.assertNotIn("addMessage('assistant', formatMindmapDiffResult(result))", agent_body)

    def test_mindmap_diff_panel_supports_per_node_exclusion_before_write(self) -> None:
        accept_body = self.js.split("function acceptMindmapDiff", 1)[1].split(
            "\n  function rejectMindmapDiff", 1
        )[0]
        for marker in [
            "function renderMindmapDiffRows",
            "function selectedMindmapDiffExclusions",
            "function updateMindmapDiffSelectionSummary",
            "function applyMindmapDiffExclusions",
            "mindmap-diff-row",
            "mindmap-diff-checkbox",
            "mindmap-diff-selection-summary",
            "data-selection-state",
            "mindmap-diff-row-title",
            "mindmap-diff-row-body",
            "data-proposed-path",
            "excludedMindmapPaths: exclusions",
            "postCompanion('draft_update'",
            "applyMindmapDiffExclusions(draftId, panel",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertIn("writeAcceptedDraft(draftId, panel)", accept_body)
        self.assertNotIn("writeAcceptedDraft(draftId, panel);\n  }", accept_body)

    def test_mindmap_diff_panel_supports_per_node_edit_before_write(self) -> None:
        accept_body = self.js.split("function acceptMindmapDiff", 1)[1].split(
            "\n  function rejectMindmapDiff", 1
        )[0]
        for marker in [
            "function mindmapDiffNodeEdits",
            "function applyMindmapDiffDraftEdits",
            "function mindmapDiffPlanAfterUserEdits",
            "mindmap-diff-title-input",
            "mindmap-diff-body-input",
            "data-original-title",
            "data-original-body",
            "mindmapNodeEdits: nodeEdits",
            "applyMindmapDiffDraftEdits(draftId, panel",
            "mindmapDiffPlanAfterUserEdits(panel",
            "bodyPreview = edit.body",
            "operation.title = edit.title",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertIn("applyMindmapDiffDraftEdits(draftId, panel", accept_body)

    def test_mindmap_diff_panel_displays_local_operation_plan(self) -> None:
        for marker in [
            "function mindmapDiffPlanText",
            "function mindmapDiffApplyBoundaryText",
            "function canApplyMindmapDiffLocally",
            "function mindmapDiffOperationCanApplyLocally",
            "function mindmapDiffOperationRequirementsReady",
            "function applyMindmapDiffLocalOperations",
            "function mindmapDiffDeleteSuggestionOperations",
            "function isMindmapDiffDeleteSuggestionOperation",
            "function mindmapDiffApplyOperations",
            "function mindmapDiffApplyPlan",
            "function requestMindmapDeleteConfirmation",
            "mindmapDiffOperationPlan",
            "applyBoundary",
            "_mindmapDiffOperationPlan",
            "request_mindmap_diff_apply",
            "request_mindmap_delete_confirmation",
            "局部操作",
            "局部执行",
            "接受按钮",
            "能力",
            "mindmap-diff-plan",
            "mindmap-diff-boundary",
            "requiredCapabilities",
            "blockedLocalMutations",
            "skippedCount",
            "nativeCapabilityReady(requirement)",
            "update_mindmap_node",
            "merge_mindmap_node",
            "move_mindmap_node",
            "suggest_delete_mindmap_node",
        ]:
            self.assertIn(marker, self.js + self.css)
        accept_body = self.js.split("function acceptMindmapDiff", 1)[1].split(
            "\n  function rejectMindmapDiff", 1
        )[0]
        self.assertIn("canApplyMindmapDiffLocally(panel)", accept_body)
        self.assertIn("applyMindmapDiffLocalOperations(panel)", accept_body)
        self.assertIn("writeAcceptedDraft(draftId, panel)", accept_body)
        self.assertIn("requestMindmapDeleteConfirmation(panel)", accept_body)
        local_apply_body = self.js.split("function applyMindmapDiffLocalOperations", 1)[1].split(
            "\n  function acceptMindmapDiff", 1
        )[0]
        self.assertIn("mindmapDiffApplyPlan(panel)", local_apply_body)
        self.assertNotIn("mindmapDiffPlanAfterUserEdits(panel)", local_apply_body)
        self.assertIn("requestMindmapDeleteConfirmation(panel)", local_apply_body)

    def test_operation_plan_preview_renders_structured_dry_run_panel(self) -> None:
        agent_body = self.js.split("function runAgentNextAction", 1)[1].split(
            "\n  function buildReplyAgentActions", 1
        )[0]
        for marker in [
            "function renderOperationPlanPreview",
            "function buildOperationPlanPanel",
            "function acceptOperationPlan",
            "function rejectOperationPlan",
            "写入计划预览",
            "Dry-run",
            "操作数",
            "阻断",
            "未确认",
            "operation-plan-panel",
            "operation-plan-accept",
            "operation-plan-reject",
            "writeAcceptedDraft(draftId",
            "postCompanion('draft_delete'",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertIn("renderOperationPlanPreview(result)", agent_body)
        self.assertNotIn("addMessage('assistant', result.reply || result.message || '已生成写入计划预览。')", agent_body)

    def test_progress_copy_matches_ai_chat_only_surface(self) -> None:
        self.assertIn("progressActiveHint", self.js)
        self.assertIn("progressFinishedHint", self.js)
        self.assertIn("formatProgressText(elapsed, active)", self.js)
        self.assertIn("finishProgressStage('失败'", self.js)
        self.assertIn("finishProgressStage('未生成脑图'", self.js)
        self.assertIn("可继续输入；运行中可点停止。", self.js)
        self.assertIn("可继续输入。", self.js)
        self.assertNotIn("可继续输入或点击按钮；忙碌时会在消息里给出后续引导。", self.js)

    def test_progress_polling_is_scoped_to_current_request_id(self) -> None:
        request_body = self.js.split("function requestTextAction", 1)[1].split("\n  function promptValue", 1)[0]
        progress_body = self.js.split("function refreshProgressRunState", 1)[1].split(
            "\n  function startProgressStatusPolling", 1
        )[0]

        self.assertIn("newRequestId()", self.js)
        self.assertIn("startProgress(action", request_body)
        self.assertIn("requestId", request_body)
        self.assertIn("_request_id: requestId", request_body)
        self.assertIn("state.progressRequestId", progress_body)
        self.assertIn("run.requestId", progress_body)
        self.assertIn("return;", progress_body.split("run.requestId", 1)[1])

    def test_stop_button_cancels_current_queue_item_and_busy_state(self) -> None:
        self.assertIn("currentQueueId", self.js)
        for function_name in ["requestTextAction", "requestGoalAction", "requestDraftAction"]:
            body = self.js.split("function " + function_name, 1)[1].split("\n  function ", 1)[0]
            self.assertIn("state.currentQueueId = queueId || ''", body)
        stop_body = self.js.split("function stopCurrent", 1)[1].split("\n  function writeAcceptedDraft", 1)[0]
        self.assertIn("var queueId = state.currentQueueId || ''", stop_body)
        self.assertIn("finishProgressStage('已停止'", stop_body)
        self.assertIn("queue_id: queueId", stop_body)
        self.assertIn("state.currentQueueId = ''", stop_body)
        self.assertIn("setWebRunLock(false)", stop_body)

    def test_required_controls_match_minimal_ai_chat_surface(self) -> None:
        required_body = self.js.split("var requiredControlIds = [", 1)[1].split("];", 1)[0]
        for marker in [
            "'aiChatShell'",
            "'commandPanePanel'",
            "'commandPaneHeader'",
            "'commandPaneStatus'",
            "'commandPaneToggleButton'",
            "'commandPaneBody'",
            "'commandPaneComposer'",
            "'settingsButton'",
            "'promptInput'",
            "'sendButton'",
            "'stopButton'",
            "'contextButton'",
            "'contextScopeAutoButton'",
            "'contextScopeSelectionButton'",
            "'contextScopeDocumentButton'",
            "'closeButton'",
            "'liveHistory'",
            "'contextSourceLine'",
            "'aiReadinessLine'",
            "'aiReadinessDetail'",
            "'selectionPreview'",
            "'statusPill'",
            "'agentWorkbenchBar'",
            "'agentWorkbenchLine'",
            "'agentPlanRefreshButton'",
            "'objectRegistryScanButton'",
            "'contextLine'",
            "'readinessPanel'",
        ]:
            self.assertIn(marker, required_body)
        for removed in [
            "goalRunPanel",
            "primaryActionGrid",
            "workflowActionPanel",
            "buttonCenterLayout",
            "runToggleButton",
            "draftPanel",
            "releaseAcceptanceButton",
        ]:
            self.assertNotIn(removed, required_body)

    def test_ai_chat_css_keeps_history_flexible_and_composer_sticky(self) -> None:
        self.assertIn(".ai-chat-history", self.css)
        self.assertIn("min-height: 0;", self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] #studioCanvasPanel', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] #commandPaneBody', self.css)
        self.assertIn('.ai-chat-shell[data-product-mode="chat"] .command-pane-body .ai-chat-history', self.css)
        self.assertIn("max-height: none;", self.css)
        self.assertIn(".ai-chat-composer", self.css)
        self.assertIn("margin-top: auto;", self.css)
        self.assertIn(".ai-chat-status-row", self.css)
        self.assertIn(".context-scope-control", self.css)
        self.assertIn(".scope-button.active", self.css)
        self.assertIn(".reply-mindmap-tree-button", self.css)
        self.assertIn(".agent-workbench-bar", self.css)
        self.assertNotIn(".reply-mindmap-menu", self.css)
        self.assertIn(".ai-edit-operation", self.css)

    def test_ai_chat_has_new_conversation_and_history_panel(self) -> None:
        for marker in [
            'id="newConversationButton"',
            'id="conversationHistoryButton"',
            'id="conversationHistoryPage"',
            'id="conversationHistoryList"',
            'id="conversationHistoryScopeLine"',
            'id="conversationHistoryAllButton"',
            'id="conversationHistoryObjectButton"',
            'id="conversationHistoryCloseButton"',
            '<section id="conversationHistoryPage" class="config-page hidden"',
            "function newConversation",
            "function openConversationHistory",
            "function closeConversationHistory",
            "function refreshConversationHistory",
            "function conversationHistoryPayload",
            "function renderConversationHistoryScope",
            "function currentMnObjectRef",
            "function renderConversationList",
            "function loadConversation",
            "function deleteConversation",
            "conversation_new",
            "conversation_list",
            "conversation_load",
            "conversation_delete",
            "state.conversationHistoryScope",
            "payload.mnObject = mnObject",
            "payload.mnObjectId = objectRef.objectId",
            "conversation-list-object",
            "data-mn-object-id",
            "payload.conversationId",
            "payload.sessionId",
            ".conversation-list-item",
            ".conversation-history-scope",
            ".conversation-history-list",
            ".config-page",
            ".config-body",
            "overflow: auto;",
        ]:
            self.assertIn(marker, self.html + self.js + self.css)

    def test_chat_header_has_multi_file_source_control_and_page(self) -> None:
        for marker in [
            'id="sourceWorkspaceButton"',
            'id="sourceWorkspaceCount"',
            'id="sourceWorkspacePage"',
            'id="sourceWorkspaceBackButton"',
            'id="sourceWorkspaceFollowCurrentDocument"',
            'id="sourceWorkspaceCurrentDocumentList"',
            'id="sourceWorkspaceNotebookList"',
            'id="sourceWorkspaceUploadList"',
            'id="sourceWorkspaceValidationStatus"',
            'id="sourceWorkspaceManageRemovalButton"',
            'id="sourceWorkspaceSelectAllRemovableButton"',
            'id="sourceWorkspaceCancelRemovalSelectionButton"',
            'id="sourceWorkspaceRemoveSelectedButton"',
            'id="sourceWorkspaceValidateButton"',
            'id="sourceWorkspaceDoneButton"',
            'id="sourceWorkspaceDiagnostics"',
            '>资料 <span id="sourceWorkspaceCount"',
            '返回对话',
            '跟随当前文件',
            '全选可移除',
            '取消全选',
            '移除所选',
            '验证资料',
            '完成',
        ]:
            self.assertIn(marker, self.html)
        self.assertNotIn('id="sourceWorkspaceLocalList"', self.html)
        self.assertNotIn('本地选择与搜索结果', self.html)

        for marker in [
            "sourceWorkspace: {schema: 'codex.mn.sourceWorkspace.v1', sourceCount: 0, sources: [], revision: ''}",
            "sourceWorkspaceCandidates: []",
            "sourceWorkspaceSelection: {}",
            "sourceWorkspaceRemovalSelection: {}",
            "sourceWorkspaceRemovalManagementActive: false",
            "sourceWorkspaceBulkInFlight: false",
            "followCurrentDocument: true",
            "function openSourceWorkspacePage",
            "function renderSourceWorkspacePage",
            "function saveSourceWorkspaceSelection",
            "source_workspace_get",
            "source_workspace_update",
            "source_workspace_validate",
            "source_workspace_clear",
            "candidate.path",
            "sourceWorkspaceDiagnostics",
        ]:
            self.assertIn(marker, self.js)

        row_body = self.js.split("function buildSourceWorkspaceRow", 1)[1].split(
            "\n  function renderSourceWorkspaceDiagnostics", 1
        )[0]
        self.assertNotIn("candidate.path", row_body)
        self.assertIn("candidate.title", row_body)
        self.assertIn("row.title =", row_body)
        self.assertIn("type = 'checkbox'", row_body)
        self.assertIn("document.createElement('div')", row_body)
        self.assertNotIn("document.createElement('label')", row_body)
        self.assertIn("sourceWorkspaceControlsLocked()", row_body)
        self.assertIn("isCurrentDocumentCandidate(candidate)", row_body)
        self.assertIn("checkbox.setAttribute('aria-label'", row_body)
        membership_change_body = row_body.split("checkbox.addEventListener('change'", 1)[1].split(
            "\n    var body", 1
        )[0]
        self.assertIn("sourceWorkspaceControlsLocked()", membership_change_body)
        removal_change_body = row_body.split("remove.addEventListener('change'", 1)[1]
        self.assertIn("sourceWorkspaceControlsLocked()", removal_change_body)

        required_controls = self.js.split("var requiredControlIds = [", 1)[1].split("];", 1)[0]
        self.assertNotIn("'sourceWorkspaceClearButton'", required_controls)
        for control_id in [
            "sourceWorkspaceBulkRemoval",
            "sourceWorkspaceManageRemovalButton",
            "sourceWorkspaceBulkControls",
            "sourceWorkspaceSelectAllRemovableButton",
            "sourceWorkspaceCancelRemovalSelectionButton",
            "sourceWorkspaceRemoveSelectedButton",
        ]:
            self.assertIn("'" + control_id + "'", required_controls)

        save_body = self.js.split("function saveSourceWorkspaceSelection", 1)[1].split(
            "\n  function newConversationRequestIsCurrent", 1
        )[0]
        self.assertIn("clearSourceWorkspace", save_body)

        follow_change_body = self.js.split("sourceWorkspaceFollow.addEventListener('change'", 1)[1].split(
            "\n    var sourceWorkspaceDiagnostics", 1
        )[0]
        self.assertIn("sourceWorkspaceControlsLocked()", follow_change_body)

    def test_source_workspace_bulk_removal_is_membership_only_and_transactional(self) -> None:
        removal_body = self.js.split("function applyBulkSourceWorkspaceRemoval", 1)[1].split(
            "\n  function clearSourceWorkspace", 1
        )[0]
        for marker in [
            "source_workspace_update",
            "source_workspace_validate",
            "原始文件和上传记录会保留",
            "sourceWorkspaceRemovalSelection",
            "sourceWorkspaceResultRevision",
            "回滚",
        ]:
            self.assertIn(marker, removal_body)
        self.assertIn("source_workspace_clear", removal_body)
        for forbidden in ["delete_file", "upload_delete", "removeUpload"]:
            self.assertNotIn(forbidden, removal_body)

    def test_generation_payload_and_source_coverage_are_fail_closed(self) -> None:
        payload_body = self.js.split("function companionPayload", 1)[1].split(
            "\n  function parseCompanionResult", 1
        )[0]
        queued_body = self.js.split("function runQueuedCommand", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        completed_body = self.js.split("function addCompletedAssistantReply", 1)[1].split(
            "\n  function addAssistantReplyWithActions", 1
        )[0]

        for marker in [
            "payload.sourceIds",
            "payload.followCurrentDocument",
            "payload.sourceWorkspaceRevision",
            "payload.conversationId",
            "payload.sessionEpoch",
        ]:
            self.assertIn(marker, payload_body)
        for marker in [
            "command.sourceIds",
            "command.followCurrentDocument",
            "command.sourceWorkspaceRevision",
            "command.conversationId",
            "command.sessionEpoch",
        ]:
            self.assertIn(marker, queued_body)
        for marker in [
            "sourceUsage",
            "sourceUsage.complete",
            "answerDerivedWritesEligible",
            "已读取 ",
            "source-usage-unread",
            "unreadIds",
            "missingIds",
        ]:
            self.assertIn(marker, self.js)
        self.assertIn("本次资料：", self.js)
        self.assertIn("个文件，均可读", self.js)
        self.assertIn("replyText", completed_body)
        self.assertIn("buildReplyCopyButton(replyText)", completed_body)
        self.assertIn("allowAnswerDerivedWrites", completed_body)
        self.assertIn("if (allowAnswerDerivedWrites)", completed_body)

    def test_follow_current_document_preserves_explicit_selection(self) -> None:
        context_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]
        follow_body = self.js.split("function completeAutomaticDocumentSwitch", 1)[1].split(
            "\n  function renderContext", 1
        )[0]
        conversation_body = self.js.split("function setCurrentConversation", 1)[1].split(
            "\n  function currentMnObjectRef", 1
        )[0]

        for marker in [
            "scheduleAutomaticDocumentSwitch",
            "stableContextDocumentKey",
            "docKey !== state.stableContextDocumentKey",
        ]:
            self.assertIn(marker, context_body)
        self.assertIn("pending.followCurrentDocument", follow_body)
        self.assertIn("reboundSelection", follow_body)
        for marker in [
            "conversation.sourceIds",
            "conversation.followCurrentDocument",
            "conversation.sourceWorkspaceRevision",
            "conversation.sessionEpoch",
        ]:
            self.assertIn(marker, conversation_body)

    def test_session_epoch_propagates_through_web_lifecycle_and_queue_binding(self) -> None:
        payload_body = self.js.split("function companionPayload", 1)[1].split(
            "\n  function parseCompanionResult", 1
        )[0]
        source_identity_body = self.js.split("function beginSourceWorkspaceRequest", 1)[1].split(
            "\n  function postSourceWorkspace", 1
        )[0]
        queued_body = self.js.split("function runQueuedCommand", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        clear_body = self.js.split("function clearHistory", 1)[1].split(
            "\n  function stopCurrent", 1
        )[0]
        delete_body = self.js.split("function deleteConversation", 1)[1].split(
            "\n  function isBrowserPreview", 1
        )[0]
        execute_body = self.js.split("function executeAction", 1)[1].split(
            "\n  function sendAction", 1
        )[0]
        goal_body = self.js.split("function runGoalWithValue", 1)[1].split(
            "\n  function runGoal", 1
        )[0]

        self.assertIn("sessionEpoch: ''", self.js)
        self.assertIn("state.sessionEpoch = String(conversation.sessionEpoch || '')", self.js)
        self.assertIn("delete payload.sessionEpoch", payload_body)
        self.assertIn("payload.sessionEpoch = state.sessionEpoch", payload_body)
        self.assertIn("sessionEpoch: String(state.sessionEpoch || '')", source_identity_body)
        self.assertIn("identity.sessionEpoch === String(state.sessionEpoch || '')", source_identity_body)
        self.assertIn("sessionEpoch: command.sessionEpoch || ''", queued_body)
        self.assertIn("command.sessionEpoch", queued_body)
        self.assertIn("state.sessionEpoch", queued_body)
        self.assertIn("payload.sessionEpoch = item.sessionEpoch", delete_body)
        self.assertIn("state.sessionEpoch = String(result.sessionEpoch || '')", clear_body)
        self.assertIn("state.sessionEpoch = ''", self.js)
        self.assertIn("!state.sessionEpoch", execute_body)
        self.assertIn("ensureSourceWorkspaceConversation", execute_body)
        self.assertIn("!state.sessionEpoch", goal_body)
        self.assertIn("ensureSourceWorkspaceConversation", goal_body)

    def test_new_conversation_payload_is_source_clean_and_failure_preserves_state(self) -> None:
        payload_body = self.js.split("function companionPayload", 1)[1].split(
            "\n  function parseCompanionResult", 1
        )[0]
        self.assertIn("if (action === 'conversation_new')", payload_body)
        clean_branch = payload_body.partition("if (action === 'conversation_new')")[2].split(
            "\n    } else {", 1
        )[0]
        new_body = self.js.split("function newConversation()", 1)[1].split(
            "\n  function loadConversation", 1
        )[0]
        failure_branch = new_body.split("if (!result || !result.ok)", 1)[1].split("return;", 1)[0]

        for marker in [
            "delete payload.conversationId",
            "delete payload.sessionId",
            "delete payload.sourceIds",
            "delete payload.sourceWorkspaceRevision",
            "payload.followCurrentDocument = true",
        ]:
            self.assertIn(marker, clean_branch)
        self.assertIn("initializeNewConversationState(result.conversation || {})", new_body)
        self.assertIn("refreshSourceWorkspace(true)", new_body)
        self.assertNotIn("saveSourceWorkspaceSelection", new_body)
        self.assertNotIn("setCurrentConversation", failure_branch)
        self.assertNotIn("state.sourceWorkspace", failure_branch)
        self.assertNotIn("state.sourceWorkspaceSelection", failure_branch)

    def test_source_workspace_callbacks_ignore_stale_conversation_or_document(self) -> None:
        self.assertIn("function postSourceWorkspace", self.js)
        guard_body = self.js.partition("function postSourceWorkspace")[2].split(
            "\n  function saveSourceWorkspaceSelection", 1
        )[0]
        self.assertIn("beginSourceWorkspaceRequest", guard_body)
        self.assertIn("sourceWorkspaceRequestIsCurrent(requestIdentity)", guard_body)
        self.assertIn("if (!sourceWorkspaceRequestIsCurrent(requestIdentity)) return;", guard_body)

        self.assertIn("function beginSourceWorkspaceRequest", self.js)
        identity_body = self.js.partition("function beginSourceWorkspaceRequest")[2].split(
            "\n  function postSourceWorkspace", 1
        )[0]
        for marker in [
            "conversationId: String(state.conversationId || '')",
            "contextDocumentKey: String(state.contextDocumentKey || '')",
            "token: state.sourceWorkspaceRequestToken",
            "identity.conversationId === String(state.conversationId || '')",
            "identity.contextDocumentKey === String(state.contextDocumentKey || '')",
        ]:
            self.assertIn(marker, identity_body)

        for action in [
            "source_workspace_get",
            "source_workspace_update",
            "source_workspace_validate",
            "source_workspace_clear",
        ]:
            self.assertIn("postSourceWorkspace('" + action + "'", self.js)

    def test_automatic_document_switch_waits_for_stable_identity_and_rebinds_sources(self) -> None:
        state_body = self.js.split("var state = {", 1)[1].split("};", 1)[0]
        render_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]
        self.assertIn("function scheduleAutomaticDocumentSwitch", self.js)
        schedule_body = self.js.partition("function scheduleAutomaticDocumentSwitch")[2].split(
            "\n  function completeAutomaticDocumentSwitch", 1
        )[0]
        self.assertIn("function completeAutomaticDocumentSwitch", self.js)
        complete_body = self.js.partition("function completeAutomaticDocumentSwitch")[2].split(
            "\n  function renderContext", 1
        )[0]
        unavailable_body = self.js.split("function sourceWorkspaceGenerationUnavailableReason", 1)[1].split(
            "\n  function addSourceRequestStatus", 1
        )[0]
        ensure_body = self.js.split("function ensureSourceWorkspaceConversation", 1)[1].split(
            "\n  function refreshSourceWorkspace", 1
        )[0]
        payload_body = self.js.split("function companionPayload", 1)[1].split(
            "\n  function parseCompanionResult", 1
        )[0]

        for marker in [
            "stableContextDocumentKey",
            "documentSwitchPending",
            "documentSwitchDebounceTimer",
            "pendingDocumentSwitch",
        ]:
            self.assertIn(marker, state_body)
        for marker in [
            "DOCUMENT_SWITCH_DEBOUNCE_MS",
            "window.clearTimeout",
            "window.setTimeout",
            "documentContextReadyForAutomaticSwitch",
            "syncSourceWorkspaceLifecycleFlags",
            "sourceIds: sourceWorkspaceSelectionIds()",
            "followCurrentDocument: state.followCurrentDocument",
        ]:
            self.assertIn(marker, schedule_body)
        self.assertNotIn("requestNewConversation", schedule_body)
        self.assertIn("scheduleAutomaticDocumentSwitch", render_body)
        self.assertNotIn("resetConversationForDocumentChange(state.context)", render_body)
        self.assertNotIn("syncFollowCurrentDocumentMembership(previousDocumentKey, docKey)", render_body)
        for marker in [
            "automaticDocumentSwitch: true",
            "sourceIds: pending.sourceIds",
            "followCurrentDocument: pending.followCurrentDocument",
            "requestNewConversation",
            "saveSourceWorkspaceSelection(false",
            "validateSavedSourceWorkspace",
            "pending.contextDocumentKey === state.contextDocumentKey",
        ]:
            self.assertIn(marker, complete_body)
        self.assertIn("generationLifecycleUnavailableReason", unavailable_body)
        self.assertIn("payload.automaticDocumentSwitch === true", payload_body)
        self.assertIn("delete payload.sourceIds", payload_body)
        self.assertIn("sourceWorkspaceLifecycle.beginMigration", schedule_body)
        self.assertIn("sourceWorkspaceLifecycle.isMigrationCurrent", complete_body)
        self.assertIn("cleanupStaleConversation", complete_body)
        for marker in [
            "state.sourceWorkspaceConversationCreateInFlight",
            "state.sourceWorkspaceConversationCreateCallbacks.push(done)",
            "state.sourceWorkspaceConversationCreateCallbacks.slice()",
        ]:
            self.assertIn(marker, ensure_body)

    def test_lifecycle_helper_is_loaded_and_centrally_gates_queue_execution(self) -> None:
        self.assertIn('<script src="source_workspace_lifecycle.js', self.html)
        self.assertLess(
            self.html.index('source_workspace_lifecycle.js'),
            self.html.index('app.js'),
        )
        for marker in [
            "window.SourceWorkspaceLifecycle.createController()",
            "sourceWorkspaceLifecycle.isGenerationBlocked()",
            "sourceWorkspaceLifecycle.beginUpload",
            "sourceWorkspaceLifecycle.cancelUpload",
            "sourceWorkspaceLifecycle.finishUpload",
            "cleanupStaleConversation",
            "onStaleResponse",
        ]:
            self.assertIn(marker, self.js)
        queued_body = self.js.split("function runQueuedCommand", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]
        self.assertIn("generationLifecycleUnavailableReason", queued_body)
        self.assertIn("deferQueuedGenerationForLifecycle", queued_body)
        self.assertIn("generationLifecycleUnavailableReason", drain_body)

    def test_shared_queue_result_policy_defers_failures_and_stale_sessions_without_ack(self) -> None:
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")
        policy_body = self.js.split("function applyQueuedResultPolicy", 1)[1].split(
            "\n  function saveQueuedWriteForConfirmation", 1
        )[0]
        defer_body = self.js.split("function deferQueuedResult", 1)[1].split(
            "\n  function applyQueuedResultPolicy", 1
        )[0]

        self.assertIn("function handleQueuedResult(options)", lifecycle_js)
        self.assertIn("handleQueuedResult: handleQueuedResult", lifecycle_js)
        self.assertIn("result_failed", lifecycle_js)
        self.assertIn("session_tombstoned", lifecycle_js)
        self.assertIn("session_binding_mismatch", lifecycle_js)
        self.assertIn("retryable: true", lifecycle_js)
        self.assertIn("window.SourceWorkspaceLifecycle.handleQueuedResult", policy_body)
        self.assertIn("onDeferred", policy_body)
        self.assertIn("deferQueuedResult", policy_body)
        self.assertNotIn("ackQueueAndContinue", defer_body)
        self.assertNotIn("drainNextQueuedAction", defer_body)

    def test_queued_chat_renders_only_for_the_bound_active_session_then_acks(self) -> None:
        queued_body = self.js.split("function runQueuedCommand", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        text_body = self.js.split("function requestTextAction", 1)[1].split(
            "\n  function promptValue", 1
        )[0]

        self.assertIn("postCompanionExactPayload", queued_body)
        self.assertIn("applyQueuedResultPolicy", queued_body)
        self.assertIn("onInactiveChat", queued_body)
        self.assertIn("showReply: !queueId", text_body)
        self.assertIn("onActiveChat", text_body)
        self.assertIn("displayCompanionResult", text_body)
        self.assertIn("applyQueuedResultPolicy", text_body)

    def test_inactive_queued_writes_defer_and_active_writes_render_confirmation_without_native_write(self) -> None:
        queued_body = self.js.split("function runQueuedCommand", 1)[1].split(
            "\n  function drainNextQueuedAction", 1
        )[0]
        save_body = self.js.split("function saveQueuedWriteForConfirmation", 1)[1].split(
            "\n  function runQueuedCommand", 1
        )[0]
        draft_body = self.js.split("function requestDraftAction", 1)[1].split(
            "\n  function stagePromptAction", 1
        )[0]

        self.assertIn("inactive_write", (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8"))
        self.assertIn("applyQueuedResultPolicy", queued_body)
        self.assertIn("isWriteAction(rawAction)", queued_body)
        self.assertIn("saveQueuedWriteForConfirmation", draft_body)
        for marker in ["renderControls", "renderDraft", "renderAiEditOperation"]:
            self.assertIn(marker, save_body)
        self.assertNotIn("writeDraftForAiEditOperation", save_body)
        self.assertNotIn("bridge('write_draft'", save_body)

    def test_deferred_queue_items_require_an_explicit_retry_instead_of_immediate_pumping(self) -> None:
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]
        toggle_body = self.js.split("function runToggle", 1)[1].split(
            "\n  function uploadFromInputs", 1
        )[0]

        self.assertIn("state.deferredQueueResults", self.js)
        self.assertIn("retryDeferred", drain_body)
        self.assertIn("deferredQueueResults", drain_body)
        self.assertIn("drainNextQueuedAction({retryDeferred: true})", toggle_body)

    def test_completed_queue_execution_is_persisted_before_ack_and_retried_as_ack_only(self) -> None:
        policy_body = self.js.split("function applyQueuedResultPolicy", 1)[1].split(
            "\n  function saveQueuedWriteForConfirmation", 1
        )[0]
        persist_body = self.js.split("function persistCompletedQueuedResult", 1)[1].split(
            "\n  function applyQueuedResultPolicy", 1
        )[0]
        ack_body = self.js.split("function ackQueueAndContinue", 1)[1].split(
            "\n  function ackAndSkipQueuedCommand", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]

        self.assertIn("completedAckPendingQueueIds", self.js)
        self.assertIn("postCompanionPath('/marginnote/queue-complete'", persist_body)
        self.assertIn("persistCompletedQueuedResult", policy_body)
        self.assertLess(policy_body.index("persistCompletedQueuedResult"), policy_body.index("ackQueueAndContinue"))
        self.assertIn("if (!result || !result.ok)", ack_body)
        self.assertIn("completedAckPendingQueueIds[queueId]", ack_body)
        self.assertIn("delete state.completedAckPendingQueueIds[queueId]", ack_body)
        self.assertIn("queuedExecutionDisposition", drain_body)
        self.assertIn("ack_only", drain_body)
        self.assertIn("ackQueueAndContinue(queueId)", drain_body)

    def test_queued_write_confirmation_blocks_drain_and_binds_draft_transaction_to_queue(self) -> None:
        save_body = self.js.split("function saveQueuedWriteForConfirmation", 1)[1].split(
            "\n  function runQueuedCommand", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]
        render_body = self.js.split("function buildAiEditOperationPanel", 1)[1].split(
            "\n  function renderAiEditOperation", 1
        )[0]
        ready_body = self.js.split("setAiEditOperationReady: function(payload)", 1)[1].split(
            "\n    setAiEditOperationResult:", 1
        )[0]
        result_body = self.js.split("setAiEditOperationResult: function(payload)", 1)[1].split(
            "\n    setAiEditTransactionStatus:", 1
        )[0]

        self.assertIn("pendingQueuedWriteConfirmation", self.js)
        self.assertIn("queueId: command._queue_id", save_body)
        self.assertIn("queueCommand: command", save_body)
        self.assertIn("state.pendingQueuedWriteConfirmation", save_body)
        self.assertIn("confirmation_pending", drain_body)
        self.assertIn("data-queue-id", render_body)
        self.assertIn("queueId", ready_body)
        self.assertIn("transactionId", ready_body)
        self.assertIn("resolveQueuedWriteConfirmation", result_body)
        self.assertIn("resolveQueuedWriteConfirmation", self.js)

    def test_queued_confirmation_guard_is_exact_session_scoped_and_restored_before_pump(self) -> None:
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")
        state_body = self.js.split("var state = {", 1)[1].split("};", 1)[0]
        restore_body = self.js.split("function restoreQueuedWriteConfirmationGuard", 1)[1].split(
            "\n  function persistQueuedWriteConfirmationState", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]
        set_conversation_body = self.js.split("function setCurrentConversation", 1)[1].split(
            "\n  function currentMnObjectRef", 1
        )[0]
        render_context_body = self.js.split("function renderContext(ctx)", 1)[1].split(
            "\n  function renderContextSourceLine", 1
        )[0]
        bind_body = self.js.split("function bind()", 1)[1].split(
            "\n  if (document.readyState", 1
        )[0]

        self.assertIn("function queuedConfirmationMatchesActiveSession", lifecycle_js)
        for marker in ["sessionId", "sessionEpoch", "contextDocumentKey"]:
            self.assertIn(marker, lifecycle_js)
        for marker in [
            "queueGuardRestoreInFlight",
            "queueGuardRestoreToken",
            "queueGuardRestoredIdentityKey",
        ]:
            self.assertIn(marker, state_body)
        self.assertIn("queued_write_confirmation_get", restore_body)
        self.assertIn("pendingQueuedWriteConfirmation", restore_body)
        self.assertIn("renderDraft", restore_body)
        self.assertIn("renderAiEditOperation", restore_body)
        self.assertIn("queueGuardRestoreInFlight", drain_body)
        self.assertIn("resetQueueRuntimeForConversationSwitch", set_conversation_body)
        self.assertIn("prepareQueueRuntimeForActiveSession", set_conversation_body)
        self.assertIn("prepareQueueRuntimeForActiveSession", render_context_body)
        self.assertNotIn("!state.queueGuardRestoreInFlight", render_context_body)
        self.assertNotIn("\n    startQueuePump();", bind_body)
        self.assertNotIn("restoreQueuedWriteConfirmationGuard(startQueuePump)", bind_body)

    def test_queue_runtime_ready_gates_pump_tick_drain_and_timer_start(self) -> None:
        state_body = self.js.split("var state = {", 1)[1].split("};", 1)[0]
        tick_body = self.js.split("function queuePumpTick", 1)[1].split(
            "\n  function startQueuePump", 1
        )[0]
        start_body = self.js.split("function startQueuePump", 1)[1].split(
            "\n  function stopQueuePump", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]

        self.assertIn("queueRuntimeReady: false", state_body)
        self.assertIn("if (!state.queueRuntimeReady) return;", tick_body)
        self.assertIn("if (!state.queueRuntimeReady) return;", start_body)
        self.assertIn("if (!state.queueRuntimeReady) return;", drain_body)
        self.assertIn("queuePumpStartTimer", state_body)

    def test_cold_restore_callback_switch_and_mixed_queue_wiring_are_exactly_scoped(self) -> None:
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")
        restore_body = self.js.split("function restoreQueueRuntimeSessionForContext", 1)[1].split(
            "\n  function queuedSessionIdentity", 1
        )[0]
        persist_body = self.js.split("function persistQueuedWriteConfirmationState", 1)[1].split(
            "\n  function applyQueuedResultPolicy", 1
        )[0]
        schedule_body = self.js.split("function scheduleAutomaticDocumentSwitch", 1)[1].split(
            "\n  function completeAutomaticDocumentSwitch", 1
        )[0]
        drain_body = self.js.split("function drainNextQueuedAction", 1)[1].split(
            "\n  function requestTextAction", 1
        )[0]

        self.assertIn("conversation_active_restore", restore_body)
        self.assertIn("queueSessionRestoreComplete", restore_body)
        self.assertLess(
            restore_body.index("setCurrentConversation"),
            restore_body.index("prepareQueueRuntimeForActiveSession"),
        )
        self.assertNotIn("state.sessionId", persist_body)
        self.assertNotIn("state.sessionEpoch", persist_body)
        self.assertNotIn("state.contextDocumentKey", persist_body)
        self.assertLess(
            schedule_body.index("resetQueueRuntimeForConversationSwitch"),
            schedule_body.index("beginMigration"),
        )
        self.assertIn("firstRunnableQueuedCommand", drain_body)
        self.assertIn("Object.assign({}, options, {isWriteAction: isWriteAction})", drain_body)
        self.assertIn("function firstRunnableQueuedCommand", lifecycle_js)
        self.assertIn("blockedOwners", lifecycle_js)

    def test_conversation_switch_removes_old_confirmation_controls_before_restore(self) -> None:
        switch_body = self.js.split("function setCurrentConversation", 1)[1].split(
            "\n  function currentMnObjectRef", 1
        )[0]
        clear_body = self.js.split("function clearQueuedWriteConfirmationUi", 1)[1].split(
            "\n  function resetQueueRuntimeForConversationSwitch", 1
        )[0]
        accept_body = self.js.split("function acceptDraft", 1)[1].split(
            "\n  function rejectDraft", 1
        )[0]
        reject_body = self.js.split("function rejectDraft", 1)[1].split(
            "\n  function runToggle", 1
        )[0]
        ready_body = self.js.split("setAiEditOperationReady: function(payload)", 1)[1].split(
            "\n    setAiEditOperationResult:", 1
        )[0]
        result_body = self.js.split("setAiEditOperationResult: function(payload)", 1)[1].split(
            "\n    setAiEditTransactionStatus:", 1
        )[0]

        self.assertLess(
            switch_body.index("resetQueueRuntimeForConversationSwitch"),
            switch_body.index("state.sessionId ="),
        )
        for marker in [
            "renderDraft(null)",
            "pendingAiEditDrafts",
            ".ai-edit-operation",
            ".mindmap-diff-operation",
            ".operation-plan-panel",
            "aiEditTransactionStatus",
            "renderAiEditTransactionCenter",
        ]:
            self.assertIn(marker, clear_body)
        self.assertIn("captureQueuedDraftOperationBinding", accept_body)
        self.assertIn("queuedDraftOperationBindingMatchesActiveSession", accept_body)
        self.assertIn("captureQueuedDraftOperationBinding", reject_body)
        self.assertIn("queuedDraftOperationBindingMatchesActiveSession", reject_body)
        self.assertIn("queuedConfirmationMatchesActiveSession", ready_body)
        self.assertLess(
            ready_body.index("queuedConfirmationMatchesActiveSession"),
            ready_body.index("renderAiEditOperation"),
        )
        self.assertLess(
            result_body.index("queuedConfirmationMatchesActiveSession"),
            result_body.index("querySelectorAll('.ai-edit-operation')"),
        )

    def test_guard_blocks_only_same_session_owned_write_commands(self) -> None:
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")

        self.assertIn("function queuedWriteCommandMatchesConfirmation", lifecycle_js)
        self.assertIn("queuedWriteCommandMatchesConfirmation(command", lifecycle_js)
        for action in [
            "generate_card",
            "generate_mindmap",
            "generate_full_reading",
            "expand_node",
            "reorganize_mindmap",
        ]:
            self.assertIn(action, lifecycle_js)

    def test_confirmation_resolution_requires_all_ids_and_exact_active_session(self) -> None:
        resolve_body = self.js.split("function resolveQueuedWriteConfirmation", 1)[1].split(
            "\n  function writeAcceptedDraft", 1
        )[0]

        for marker in [
            "pending.sessionId",
            "state.sessionId",
            "pending.sessionEpoch",
            "state.sessionEpoch",
            "pending.contextDocumentKey",
            "state.contextDocumentKey",
            "providedCount",
            "matchedCount",
            "providedCount !== matchedCount",
        ]:
            self.assertIn(marker, resolve_body)

    def test_confirmation_transitions_are_persisted_before_local_resolution(self) -> None:
        persist_body = self.js.split("function persistQueuedWriteConfirmationState", 1)[1].split(
            "\n  function applyQueuedResultPolicy", 1
        )[0]
        write_body = self.js.split("function writeAcceptedDraft", 1)[1].split(
            "\n  function currentAiEditTransactionId", 1
        )[0]
        result_body = self.js.split("setAiEditOperationResult: function(payload)", 1)[1].split(
            "\n    setAiEditTransactionStatus:", 1
        )[0]

        self.assertIn("queued_write_confirmation_update", persist_body)
        self.assertIn("native_write", write_body)
        self.assertIn("persistQueuedWriteConfirmationState", write_body)
        self.assertIn("persistQueuedWriteConfirmationState", result_body)
        self.assertLess(
            result_body.index("persistQueuedWriteConfirmationState"),
            result_body.index("resolveQueuedWriteConfirmation"),
        )

    def test_empty_queued_goal_and_draft_failure_use_shared_failure_policy(self) -> None:
        goal_body = self.js.split("function requestGoalAction", 1)[1].split(
            "\n  function requestDraftAction", 1
        )[0]
        empty_branch = goal_body.split("if (!goal.title && !goal.detail)", 1)[1].split("return;", 1)[0]
        policy_body = self.js.split("function applyQueuedResultPolicy", 1)[1].split(
            "\n  function saveQueuedWriteForConfirmation", 1
        )[0]

        self.assertIn("applyQueuedResultPolicy", empty_branch)
        self.assertIn("empty_queued_goal", empty_branch)
        self.assertNotIn("ackQueueAndContinue", empty_branch)
        self.assertIn("detail.result || result", policy_body)

    def test_automatic_switch_readiness_uses_exported_lifecycle_predicate(self) -> None:
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")

        self.assertIn("function documentContextReadyForAutomaticSwitch(ctx, docKey)", lifecycle_js)
        self.assertIn(
            "documentContextReadyForAutomaticSwitch: documentContextReadyForAutomaticSwitch",
            lifecycle_js,
        )
        self.assertIn(
            "window.SourceWorkspaceLifecycle.documentContextReadyForAutomaticSwitch",
            self.js,
        )
        self.assertNotIn(
            "function documentContextReadyForAutomaticSwitch(ctx, docKey)",
            self.js,
        )

    def test_document_scoped_payloads_use_exported_implicit_object_policy(self) -> None:
        payload_body = self.js.split("function companionPayload", 1)[1].split(
            "\n  function parseCompanionResult", 1
        )[0]
        lifecycle_js = (ROOT / "web/source_workspace_lifecycle.js").read_text(encoding="utf-8")

        self.assertIn("function shouldAttachImplicitMnObject(action)", lifecycle_js)
        self.assertIn("shouldAttachImplicitMnObject: shouldAttachImplicitMnObject", lifecycle_js)
        self.assertIn(
            "window.SourceWorkspaceLifecycle.shouldAttachImplicitMnObject(action)",
            payload_body,
        )
        self.assertNotIn(
            "if (mnObject && mnObject.objectId && !payload.mnObject && !payload.mnObjectId) payload.mnObject = mnObject;",
            payload_body,
        )

    def test_source_workspace_page_supports_ordered_multi_file_binary_uploads(self) -> None:
        for marker in [
            'id="sourceWorkspaceAddFilesButton"',
            'id="sourceWorkspaceFileInput"',
            'type="file"',
            'multiple',
            'id="sourceWorkspaceUploadProgress"',
            'id="sourceWorkspaceUploadErrors"',
        ]:
            self.assertIn(marker, self.html)
        for marker in [
            "MAX_SOURCE_WORKSPACE_UPLOAD_FILES = 20",
            "MAX_SOURCE_WORKSPACE_UPLOAD_BYTES = 20000000",
            "function uploadSourceWorkspaceFiles",
            "readAsArrayBuffer",
            "fileContentBase64",
            "upload_file",
            "正在上传 ",
            "sourceWorkspaceUploadProgress",
            "sourceWorkspaceUploadErrors",
            "successfulUploadIds",
            "metadata.uploadId",
            "refreshSourceWorkspace(false",
            "saveSourceWorkspaceSelection(false",
            "validateSavedSourceWorkspace",
        ]:
            self.assertIn(marker, self.js)

    def test_parity_matrix_document_tracks_builtin_ai_chat_requirements(self) -> None:
        doc = (Path(__file__).resolve().parents[1] / "docs/MN4_AI_CHAT_PARITY.md").read_text(encoding="utf-8")
        for marker in [
            "MarginNote 自带 AI 对话对标矩阵",
            "显式上下文授权",
            "选区 / 节点 / 文档上下文",
            "多模型档位",
            "生成中停止",
            "非目标",
            "https://forum.marginnote.com/t/questions-about-the-new-ai-assistant/11047",
            "https://apps.apple.com/us/app/marginnote-4-ai-notes-mindmap/id1531657269",
        ]:
            self.assertIn(marker, doc)


if __name__ == "__main__":
    unittest.main()
