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
            'id="modeSwitchBar"',
            'id="chatModeButton"',
            'id="agentWorkspaceModeButton"',
            'id="modeIntentLine"',
            'id="workspaceNavigator"',
            'id="workspaceNavigatorSummary"',
            'id="workspaceNavConsoleButton"',
            'id="workspaceNavMindmapStudioButton"',
            'id="workspaceNavCardFactoryButton"',
            'id="workspaceNavLedgerExplorerButton"',
            'id="workspaceNavKnowledgeGraphButton"',
            'id="workspaceNavWorkflowBuilderButton"',
            'id="workspaceNavSkillCenterButton"',
            'id="notebookWorkspacePanel"',
            'id="notebookWorkspaceTitle"',
            'id="notebookWorkspaceSummary"',
            'id="notebookWorkspaceRefreshButton"',
            'id="notebookWorkspaceFocus"',
            'id="notebookWorkspaceObjectCount"',
            'id="notebookWorkspaceMindmap"',
            'id="notebookWorkspaceReview"',
            'id="notebookWorkspaceWorkflow"',
            'id="notebookWorkspaceLedger"',
            'id="notebookWorkspaceActions"',
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
            'id="workflowWorkspaceGateway"',
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
            "Chat Mode",
            "Agent Workspace",
        ]:
            self.assertIn(marker, self.html)

        self.assertIn("activeProductMode: 'workspace'", self.js)
        self.assertIn("commandPaneExpanded: false", self.js)
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
        self.assertIn("function runNotebookWorkspaceAction", self.js)
        self.assertIn("state.notebookWorkspace", self.js)
        self.assertIn("postCompanion('notebook_workspace'", self.js)
        self.assertIn("notebookWorkspaceRefreshButton", self.js)
        self.assertIn("data-notebook-workspace-action", self.js)
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
        self.assertLess(main_html.index('id="workbenchTabs"'), main_html.index('id="commandPanePanel"'))
        self.assertLess(main_html.index('id="commandPanePanel"'), main_html.index('id="workbenchLayout"'))
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
            "高亮",
            "导出",
            "一次性目标",
            "按钮中心",
        ]:
            self.assertNotIn(removed, main_html)

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
        navigator_html = main_html.split('id="workspaceNavigator"', 1)[1].split('id="workbenchTabs"', 1)[0]
        for marker in [
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
            "state.activeWorkspaceSurface",
            "switchWorkbenchPane(workspaceSurfacePane(surface)",
            "workspaceSurfaceAnchor(surface)",
            "focusWorkspaceSurfaceAnchor(anchorId)",
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
            "function workflowRunInspectorStep",
            "function renderWorkflowRunInspector",
            "function openWorkflowRunInspector",
            "function retryWorkflowRunStep",
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
            "postCompanion('knowledge_index_search'",
            "postCompanion('workflow_start'",
            "postCompanion('workflow_status'",
            "postCompanion('workflow_retry_step'",
            "postCompanion('skill_marketplace_status'",
            "postCompanion('skill_install'",
            "workflowTemplates",
            "workflowSkills",
            "knowledgeWorkspaceResults",
            "knowledgeWorkspaceReviewQueue",
            "knowledgeWorkspaceReviewList",
            "workflowWorkspaceTemplates",
            "workflowWorkspaceRecentRuns",
            "workflowWorkspaceSkillsList",
            "runInspector",
            "retryable",
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
            'id="modelInput"',
            'id="speedSelect"',
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
            "renderMnApiStatus",
            "checkForUpdates",
            "installUpdate",
            "renderUpdateStatus",
        ]:
            self.assertIn(marker, self.html + self.js)

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
            'id="singleDocumentAcceptanceButton"',
            'id="releaseAcceptanceButton"',
            '<option value="local">',
            "队列与生成",
            "上下文文件",
            "自定义按钮",
            "诊断与验收",
            "发布验收",
            "高亮采证",
            "本文档验收",
        ]:
            self.assertNotIn(marker, self.html)
        for marker in [
            'id="defaultContextScopeSelect"',
            'id="permissionDiagnoseButton"',
            'id="cacheCurrentPdfButton"',
            'id="nativeCapabilitiesRefreshButton"',
            "defaultContextScope",
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
        save_body = self.js.split("postCompanionPath('/marginnote/draft', 'draft_save'", 1)[1].split(
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
        ]:
            self.assertIn(marker, self.html + self.js + self.css)

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
