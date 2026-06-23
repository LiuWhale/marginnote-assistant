#!/usr/bin/env python3
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path


HOME = Path.home()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_EXT_DIR = PROJECT_ROOT / "extension/codex.mn.assistant"
LIVE_EXT_DIR = HOME / "Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant"
DEFAULT_EXT_DIR = SOURCE_EXT_DIR if SOURCE_EXT_DIR.exists() else LIVE_EXT_DIR


def resolve_extension_dir() -> Path:
    override = os.environ.get("CODEX_MN_TEST_EXTENSION_DIR", "").strip()
    return Path(override).expanduser() if override else DEFAULT_EXT_DIR


class ResizablePanelPathTest(unittest.TestCase):
    def test_extension_dir_can_be_overridden_for_release_acceptance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            old_value = os.environ.get("CODEX_MN_TEST_EXTENSION_DIR")
            os.environ["CODEX_MN_TEST_EXTENSION_DIR"] = tmp
            try:
                self.assertEqual(resolve_extension_dir(), Path(tmp))
            finally:
                if old_value is None:
                    os.environ.pop("CODEX_MN_TEST_EXTENSION_DIR", None)
                else:
                    os.environ["CODEX_MN_TEST_EXTENSION_DIR"] = old_value


class ResizablePanelContractTest(unittest.TestCase):
    def setUp(self) -> None:
        ext_dir = resolve_extension_dir()
        self.controller = (ext_dir / "CodexWebPanelController.js").read_text(encoding="utf-8")
        self.main = (ext_dir / "main.js").read_text(encoding="utf-8")
        self.index = (ext_dir / "web/index.html").read_text(encoding="utf-8")
        self.app = (ext_dir / "web/app.js").read_text(encoding="utf-8")
        self.css = (ext_dir / "web/app.css").read_text(encoding="utf-8")

    def test_web_panel_has_minimum_size_and_persistent_user_size(self) -> None:
        self.assertIn("CodexPanelMinWidth = 390", self.controller)
        self.assertIn("CodexPanelMinHeight = 520", self.controller)
        self.assertIn("codex_mn_assistant_panel_width", self.controller)
        self.assertIn("codex_mn_assistant_panel_height", self.controller)
        self.assertIn("savePanelSize", self.controller)
        self.assertIn("panelPreferredSize", self.controller)
        self.assertIn("panelMinimumSize", self.controller)

    def test_web_panel_can_be_moved_and_zoomed_with_buttons(self) -> None:
        self.assertIn("CodexPanelXKey", self.controller)
        self.assertIn("CodexPanelYKey", self.controller)
        self.assertIn("handleMove:", self.controller)
        self.assertIn("panelMoveFinished", self.controller)
        self.assertIn("shrinkButton", self.controller)
        self.assertIn("expandButton", self.controller)
        self.assertIn("zoomOut:", self.controller)
        self.assertIn("zoomIn:", self.controller)
        self.assertIn("resizePanelBy", self.controller)
        self.assertIn("panelPreferredOrigin", self.controller)
        self.assertIn("isMovingPanel", self.controller)

    def test_web_panel_load_ignores_stale_local_cache(self) -> None:
        load_body = self.controller.split("CodexWebPanelController.prototype.loadInitialPage", 1)[1].split(
            "\nCodexWebPanelController.prototype.loadErrorPage", 1
        )[0]

        self.assertIn("web/index.html", load_body)
        self.assertIn("NSMutableURLRequest.requestWithURL", load_body)
        self.assertIn("setCachePolicy(1)", load_body)
        self.assertIn("loadRequest(request)", load_body)

    def test_main_layout_respects_web_panel_preferred_size(self) -> None:
        self.assertIn("panelPreferredSize", self.main)
        self.assertIn("panelMinimumSize", self.main)
        self.assertIn("panelPreferredOrigin", self.main)
        self.assertIn("isMovingPanel", self.main)
        self.assertIn("preferredSize.width", self.main)
        self.assertIn("minimumSize.height", self.main)

    def test_web_panel_can_confirm_and_write_staged_drafts(self) -> None:
        self.assertIn("codexpaper://write_draft", self.controller)
        self.assertIn("writeDraft", self.controller)
        self.assertIn("writeDraft", self.main)
        self.assertIn("/marginnote/draft?id=", self.main)
        self.assertIn("draftWriteFailed", self.main)
        self.assertIn("draftWritten", self.main)

    def test_ai_edit_reject_removes_only_nodes_from_the_recent_write_transaction(self) -> None:
        for marker in [
            "beginAiEditTransaction",
            "recordAiEditCreatedNote",
            "finishAiEditTransaction",
            "rejectAiEditTransaction",
            "deleteNoteForAiEdit",
            "aiEditOperationReady",
            "aiEditTransactionRejected",
            "aiEditTransactionAccepted",
            "createdNoteIds",
        ]:
            self.assertIn(marker, self.main)
        create_cards_body = self.main.split("CodexAssistantAddon.prototype.createCards", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.createMindmap", 1
        )[0]
        create_mindmap_body = self.main.split("CodexAssistantAddon.prototype.createMindmap", 1)[1].split(
            "\n\n  return CodexAssistantAddon;", 1
        )[0]
        self.assertIn("recordAiEditCreatedNote(note)", create_cards_body)
        self.assertIn("recordAiEditCreatedNote(note)", create_mindmap_body)
        reject_body = self.main.split("CodexAssistantAddon.prototype.rejectAiEditTransaction", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.handleCompanionResponse", 1
        )[0]
        self.assertIn("deleteNoteForAiEdit(note, ctx)", reject_body)
        self.assertIn("Application.sharedInstance().refreshAfterDBChanged", reject_body)

    def test_visible_ui_is_margin_note_style_ai_chat_only(self) -> None:
        for required in [
            'id="aiChatShell"',
            'id="sendButton"',
            'id="promptInput"',
            'id="selectionPreview"',
            'id="liveHistory"',
        ]:
            self.assertIn(required, self.index)

        expected_order = ['id="selectionPreview"', 'id="liveHistory"', 'id="promptInput"', 'id="sendButton"']
        positions = [self.index.index(marker) for marker in expected_order]
        self.assertEqual(positions, sorted(positions))

        main_html = self.index.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for removed in [
            'tabButtonButtons',
            'tabButtonSettings',
            'tabButtonFiles',
            'tabButtonHistory',
            'commandBar',
            'stagedActionLine',
            'goalRunPanel',
            'primaryActionGrid',
            'workflowActionPanel',
            'mainPinnedButtonsPanel',
            'draftPanel',
            '制卡',
            '脑图',
            '高亮',
            '导出',
            '按钮中心',
            '一次性目标',
        ]:
            self.assertNotIn(removed, main_html)

        send_body = self.app.split("function sendAction", 1)[1].split("\n  function renderControls", 1)[0]
        self.assertNotIn("routeNaturalLanguageAction", send_body)
        self.assertIn("executeAction('chat'", send_body)

    def test_merge_mindmap_appends_children_to_selected_node_without_wrapper(self) -> None:
        self.assertIn("mergeIntoSelected", self.main)
        self.assertIn("mergeChildrenIntoSelected", self.main)
        merge_body = self.main.split("function mergeChildrenIntoSelected", 1)[1].split(
            "\n    UndoManager.sharedInstance().undoGrouping", 1
        )[0]

        self.assertIn("makeNode(children[i], selected)", merge_body)
        self.assertNotIn("makeNode(tree, selected)", merge_body)
        self.assertIn("createMindmapFinished", self.main)
        self.assertIn("mode: mergeIntoSelected", self.main)

    def test_merge_mindmap_requires_selected_node_and_never_falls_back_to_new_root(self) -> None:
        self.assertIn("wantsMergeIntoSelected", self.main)
        self.assertIn("missing-selected-node-for-merge", self.main)
        self.assertIn("请先在脑图中选中一个节点", self.main)
        self.assertIn("createMindmapFailed", self.main)
        guard_body = self.main.split("if (wantsMergeIntoSelected && !selected) {", 1)[1].split(
            "\n    var mergeIntoSelected", 1
        )[0]

        self.assertIn("missing-selected-node-for-merge", guard_body)
        self.assertIn("return;", guard_body)
        self.assertNotIn("makeNode(tree, selected)", guard_body)

    def test_companion_action_errors_distinguish_timeout_from_service_down(self) -> None:
        self.assertIn("CompanionActionTimeout = 900", self.main)
        self.assertIn("companionErrorDescription", self.main)
        self.assertIn("companionRequestErrorMessage", self.main)
        self.assertIn("请求超时", self.main)
        self.assertIn("未运行或端口不可达", self.main)
        self.assertIn("127.0.0.1:48761", self.main)
        self.assertIn("设置页的“运行态采证”", self.main)
        self.assertIn("callCompanionRequestFailed", self.main)
        self.assertIn("request.setTimeoutInterval(CompanionActionTimeout)", self.main)
        self.assertNotIn("setTimeoutInterval(120)", self.main)
        self.assertNotIn("未知网络错误", self.main)
        error_branch = self.main.split("if (error) {", 1)[1].split("return;", 1)[0]
        self.assertIn("companionRequestErrorMessage(error, CompanionActionTimeout)", error_branch)
        self.assertNotIn("Codex Companion 未运行：请先启动本地 Companion 服务。", error_branch)

    def test_native_poll_defers_raw_queue_commands_to_webview(self) -> None:
        self.assertIn("callCompanion = function(action, prompt, ackIds)", self.main)
        self.assertIn("if (ackIds && ackIds.length) addon.ackCommands(ackIds);", self.main)
        single_branch = self.main.split("if (rawActionSingle) {", 1)[1].split("return;", 1)[0]
        self.assertIn("rawQueueDeferredToWebView", single_branch)
        self.assertNotIn("addon.callCompanion", single_branch)
        self.assertNotIn("ackCommands([String(queueIdSingle)])", single_branch)
        array_branch = self.main.split("if (rawAction) {", 1)[1].split("break;", 1)[0]
        self.assertIn("rawQueueDeferredToWebView", array_branch)
        self.assertNotIn("addon.callCompanion", array_branch)
        self.assertNotIn("ackIds.push(String(queueId))", array_branch)

    def test_runtime_probes_native_highlight_and_export_api_candidates(self) -> None:
        self.assertIn("probeNativeApiCapabilities", self.main)
        self.assertIn("nativeApiCapabilities", self.main)
        self.assertIn("respondsToSelector", self.main)
        self.assertIn("AppendHighlight", self.main)
        self.assertIn("importPdfAnnotations", self.main)
        self.assertIn("ExportHighlightedPages", self.main)
        self.assertIn("hasNativeHighlightCandidate", self.main)
        self.assertIn("hasAnnotatedExportCandidate", self.main)
        self.assertIn("lastDocumentController", self.main)
        self.assertIn("selectionDocumentController", self.main)
        self.assertIn("nativeCapabilityMatrix", self.main)
        self.assertIn("capabilityMatrix", self.main)
        self.assertIn("activeSelectionLength", self.main)
        self.assertIn("canCreateNote", self.main)
        self.assertIn("Note.createWithTitleNotebookDocument", self.main)
        self.assertIn("UndoManager.sharedInstance().undoGrouping", self.main)
        self.assertIn("Application.sharedInstance().refreshAfterDBChanged", self.main)
        self.assertIn("canInstallSelectionPopupMenu", self.main)

    def test_native_poll_can_highlight_current_pdf_selection_with_mn4_api(self) -> None:
        self.assertIn("highlight_current_selection", self.main)
        self.assertIn("highlightFromSelection", self.main)
        self.assertIn("nativeHighlightSelectionPosted", self.main)
        self.assertIn("nativeHighlightSelectionFailed", self.main)

        handler_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("this.highlightCurrentSelection", handler_body)

    def test_chat_buttons_are_clear_groups_without_collapsed_tool_drawer(self) -> None:
        self.assertIn('id="aiChatShell"', self.index)
        for removed in [
            'id="primaryTaskPanel"',
            'id="goalRunPanel"',
            'id="workflowActionPanel"',
            'id="mindmapToolPanel"',
            'id="sourceToolPanel"',
            'id="secondaryToolsPanel"',
            'id="secondaryToolsSummary"',
            "goalToggleButton",
            "mindmapActionGrid",
            "toolActionGrid",
        ]:
            self.assertNotIn(removed, self.index)

    def test_run_toggle_controls_queue_and_stop_not_prompt_sending(self) -> None:
        main_html = self.index.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        self.assertNotIn('id="runToggleButton"', main_html)
        self.assertNotIn('id="queueBadge"', main_html)
        self.assertNotIn("队列</button>", main_html)
        self.assertIn('id="sendButton"', self.index)

    def test_actions_queue_when_backend_run_is_active_even_without_web_busy(self) -> None:
        self.assertIn("runActive: false", self.app)
        self.assertIn("state.runActive = !!run.active", self.app)
        execute_body = self.app.split("function executeAction", 1)[1].split(
            "\n  function sendAction", 1
        )[0]
        self.assertIn("if (isActiveRun())", execute_body)
        self.assertIn("enqueueAction(action, prompt)", execute_body)

    def test_goal_control_is_first_action_group_not_mixed_with_tools(self) -> None:
        for removed in [
            'id="goalRunPanel"',
            'class="action-panel goal-run-panel goal-entry-panel"',
            'id="mainActionStack"',
            'id="primaryTaskPanel"',
            'id="workflowActionPanel"',
        ]:
            self.assertNotIn(removed, self.index)

    def test_goal_editor_is_adjacent_to_goal_button_inside_composer(self) -> None:
        composer = self.index.split('<section class="composer ai-chat-composer">', 1)[1].split("</section>", 1)[0]
        self.assertIn('id="promptInput"', composer)
        self.assertIn('id="sendButton"', composer)
        self.assertNotIn('id="goalRunPanel"', composer)
        self.assertNotIn('id="goalPanel"', composer)

    def test_highlight_next_selection_button_does_not_require_existing_selection(self) -> None:
        main_html = self.index.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        self.assertNotIn('data-action="request_native_highlight_selection"', main_html)
        self.assertNotIn("高亮", main_html)

    def test_native_poll_can_refresh_native_api_capability_probe(self) -> None:
        self.assertIn("probe_native_api_capabilities", self.main)
        self.assertIn("nativeApiCapabilityProbeRequested", self.main)

        handler_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("this.probeNativeApiCapabilities()", handler_body)
        self.assertIn("nativeAction === 'probe_native_api_capabilities'", handler_body)

    def test_native_poll_can_reload_web_panel_without_restarting_mn4(self) -> None:
        self.assertIn("reload_web_panel", self.main)
        self.assertIn("reloadWebPanel", self.main)
        self.assertIn("webPanelReloadRequested", self.main)
        self.assertIn("webPanelReloadFinished", self.main)

        handler_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("nativeAction === 'reload_web_panel'", handler_body)
        self.assertIn("this.reloadWebPanel()", handler_body)

        show_body = self.main.split("CodexAssistantAddon.prototype.showPanel = function()", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.hidePanel", 1
        )[0]
        reload_body = self.main.split("CodexAssistantAddon.prototype.reloadWebPanel = function()", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.layoutPanel", 1
        )[0]
        self.assertIn("this.panel = createPanelController(this)", show_body)
        self.assertIn("addon.panel = null", reload_body)
        self.assertNotIn("addon.panel.loadInitialPage", reload_body)

    def test_native_document_controller_resolution_uses_shared_candidates_and_diagnostics(self) -> None:
        self.assertIn("function documentControllerCandidates", self.main)
        self.assertIn("function resolveDocumentController", self.main)
        for label in [
            "lastDocumentController",
            "studyController.currentDocumentController",
            "studyController.readerController",
            "studyController.pdfController",
            "studyController.pdfViewController",
            "notebookController.currentDocumentController",
            "notebookController.readerController",
            "notebookController.pdfController",
            "notebookController.pdfViewController",
        ]:
            self.assertIn(label, self.main)

    def test_native_document_controller_resolution_covers_reader_pdf_aliases_and_nested_controllers(self) -> None:
        candidate_body = self.main.split("function documentControllerCandidates", 1)[1].split(
            "\n  function resolveDocumentController", 1
        )[0]
        for marker in [
            "reader",
            "readerView",
            "readerVC",
            "pdfReader",
            "pdfReaderController",
            "pdfDocumentController",
            "documentViewController",
            "docViewController",
            "pdfView",
            "readerController.documentController",
            "readerController.docController",
            "readerController.currentDocumentController",
            "readerViewController.documentController",
            "pdfController.documentController",
            "pdfViewController.documentController",
        ]:
            self.assertIn(marker, candidate_body)

        probe_body = self.main.split("CodexAssistantAddon.prototype.probeNativeApiCapabilities", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.resolveContext", 1
        )[0]
        self.assertIn("resolveDocumentController(this, controller, nc)", probe_body)
        self.assertIn("probeTargetObject(candidate.label, candidate.object", probe_body)
        self.assertIn("documentControllerCandidates: docResolution.labels", probe_body)
        self.assertIn("selectedDocumentControllerLabel: docResolution.label", probe_body)

        highlight_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.startCommandPolling", 1
        )[0]
        self.assertIn("resolveDocumentController(this, controller, nc)", highlight_body)
        self.assertIn("candidateLabels: docResolution.labels", highlight_body)
        self.assertIn("candidateCount: docResolution.labels.length", highlight_body)
        self.assertIn("selectedDocumentControllerLabel: docResolution.label", highlight_body)

    def test_selection_popup_menu_exposes_native_highlight_action(self) -> None:
        self.assertIn("appendSelectionPopupMenuActions", self.main)
        self.assertIn("PopupMenu.currentMenu", self.main)
        self.assertIn("PopupMenuItem", self.main)
        self.assertIn("Codex 高亮选区", self.main)
        self.assertIn("highlightCurrentSelectionFromMenu:", self.main)
        self.assertIn("selectionPopupHighlightMenuInstalled", self.main)

        selection_body = self.main.split("onPopupMenuOnSelection: function(sender)", 1)[1].split(
            "\n    togglePanel:", 1
        )[0]
        self.assertIn("self.appendSelectionPopupMenuActions(sender, documentController)", selection_body)

    def test_selection_popup_notification_records_entry_and_window_filter_diagnostics(self) -> None:
        selection_body = self.main.split("onPopupMenuOnSelection: function(sender)", 1)[1].split(
            "\n    togglePanel:", 1
        )[0]

        self.assertIn("selectionPopupHighlightNotificationObserved", selection_body)
        self.assertIn("selectionPopupHighlightNotificationSkipped", selection_body)
        self.assertIn("reason: 'outside-window'", selection_body)
        self.assertLess(
            selection_body.index("selectionPopupHighlightNotificationObserved"),
            selection_body.index("checkNotifySenderInWindow"),
        )

    def test_selection_popup_observer_registers_when_scene_connects(self) -> None:
        scene_body = self.main.split("sceneWillConnect: function()", 1)[1].split(
            "\n    sceneDidDisconnect", 1
        )[0]

        self.assertIn("registerSelectionPopupObserver", self.main)
        self.assertIn("self.registerSelectionPopupObserver('sceneWillConnect')", scene_body)
        self.assertIn("selectionPopupHighlightObserverRegistered", self.main)
        self.assertIn("PopupMenuOnSelection", self.main)

    def test_selection_popup_observer_rebinds_when_notebook_opens(self) -> None:
        notebook_body = self.main.split("notebookWillOpen: function(notebookid)", 1)[1].split(
            "\n    notebookWillClose", 1
        )[0]
        observer_body = self.main.split("CodexAssistantAddon.prototype.registerSelectionPopupObserver", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.unregisterSelectionPopupObserver", 1
        )[0]

        self.assertIn("self.registerSelectionPopupObserver('notebookWillOpen', true)", notebook_body)
        self.assertIn("force", observer_body)
        self.assertIn("selectionPopupHighlightObserverRebinding", observer_body)
        self.assertIn("selection-popup-notebook-rebind-v1", self.main)

    def test_selection_popup_observer_uses_marginnote_self_registration_pattern(self) -> None:
        observer_body = self.main.split("CodexAssistantAddon.prototype.registerSelectionPopupObserver", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.unregisterSelectionPopupObserver", 1
        )[0]
        unregister_body = self.main.split("CodexAssistantAddon.prototype.unregisterSelectionPopupObserver", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.showPanel", 1
        )[0]

        self.assertIn(
            "NSNotificationCenter.defaultCenter().addObserverSelectorName(self, 'onPopupMenuOnSelection:', 'PopupMenuOnSelection')",
            observer_body,
        )
        self.assertIn(
            "NSNotificationCenter.defaultCenter().removeObserverName(self, 'PopupMenuOnSelection')",
            unregister_body,
        )
        self.assertNotIn("addObserverSelectorName(this,", observer_body)
        self.assertNotIn("removeObserverName(this,", unregister_body)

    def test_selection_popup_menu_reports_missing_selection_text(self) -> None:
        menu_body = self.main.split("CodexAssistantAddon.prototype.appendSelectionPopupMenuActions", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.createSelectionPopupHighlightItem", 1
        )[0]

        self.assertIn("selectionPopupHighlightMenuSkipped", menu_body)
        self.assertIn("reason: 'missing-selection-text'", menu_body)
        self.assertIn("hasDocumentController", menu_body)
        self.assertIn("hasLastSelectionText", menu_body)

    def test_selection_popup_highlight_uses_cached_selection_without_early_reject(self) -> None:
        menu_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelectionFromMenu", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.highlightCurrentSelection", 1
        )[0]
        self.assertIn("source: 'selection-popup-menu'", menu_body)
        self.assertIn("allowCachedSelectionText: true", menu_body)

        highlight_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.startCommandPolling", 1
        )[0]
        self.assertIn("allowCachedSelectionText", highlight_body)
        self.assertIn("usedCachedSelectionText", highlight_body)
        self.assertIn("selectionTextSource", highlight_body)
        self.assertIn("cached-selection", highlight_body)

    def test_native_highlight_uses_shared_selection_text_resolver_with_aliases(self) -> None:
        resolver_body = self.main.split("function selectionTextFromDocumentController", 1)[1].split(
            "\n  function firstStringValue", 1
        )[0]
        highlight_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.startCommandPolling", 1
        )[0]

        for key in [
            "selectionText",
            "selectedText",
            "selectionString",
            "selectedString",
            "selectedTextString",
            "currentSelectionText",
        ]:
            self.assertIn(key, resolver_body)
        self.assertIn("selectionTextFromDocumentController(docController)", highlight_body)
        direct_selection_block = highlight_body.split("var selectionText = '';", 1)[1].split(
            "var allowCachedSelectionText", 1
        )[0]
        self.assertNotIn("valueOf(docController, 'selectionText')", direct_selection_block)
        self.assertIn("native-highlight-selection-text-resolver-v1", self.main)
        self.assertIn("context-refresh-clears-stale-selection-v1", self.main)

    def test_context_refresh_clears_stale_cached_selection_when_no_active_selection(self) -> None:
        self.assertIn("CodexAssistantAddon.prototype.currentSelectionText", self.main)
        resolve_body = self.main.split("CodexAssistantAddon.prototype.resolveContext", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.callCompanion", 1
        )[0]

        self.assertIn("var liveSelectionText = this.currentSelectionText();", resolve_body)
        self.assertIn("if (liveSelectionText)", resolve_body)
        self.assertIn("action === 'context'", resolve_body)
        self.assertIn("this.lastSelectionText = ''", resolve_body)
        self.assertIn("selectionText: selectionText", resolve_body)

    def test_native_highlight_attempts_official_selector_even_when_bridge_does_not_advertise_it(self) -> None:
        self.assertIn("function invokeHighlightFromSelection", self.main)
        self.assertIn("attemptedUnverifiedSelector", self.main)
        self.assertIn("selectorVerified", self.main)
        self.assertIn("unverified-highlightFromSelection-call", self.main)

        highlight_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.startCommandPolling", 1
        )[0]
        self.assertIn("invokeHighlightFromSelection(docController)", highlight_body)
        self.assertNotIn("reason: 'missing-highlightFromSelection'", highlight_body)

        matrix_body = self.main.split("function nativeCapabilityMatrix", 1)[1].split(
            "\n      selectionPopupHighlight:", 1
        )[0]
        self.assertIn("targetLabelIndicatesDocumentController", matrix_body)
        self.assertIn("studyController.readerController", self.main)
        self.assertIn("unverified-highlightFromSelection-call", matrix_body)
        self.assertIn("canAttemptUnverifiedHighlightCall", matrix_body)

    def test_native_highlight_queue_command_preserves_cached_selection_for_web_button(self) -> None:
        handler_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        highlight_branch = handler_body.split("nativeAction === 'highlight_current_selection'", 1)[1].split(
            "return true;", 1
        )[0]
        self.assertIn("highlightCommand.allowCachedSelectionText = true", highlight_branch)
        self.assertIn("this.lastSelectionText", highlight_branch)
        self.assertIn("highlightCommand.selectionText", highlight_branch)

    def test_native_highlight_can_arm_next_pdf_selection_when_web_button_loses_selection(self) -> None:
        self.assertIn("nativeHighlightNextSelectionArmed", self.main)
        self.assertIn("armNativeHighlightNextSelection", self.main)
        self.assertIn("consumeArmedNativeHighlightSelection", self.main)
        self.assertIn("nativeHighlightNextSelectionConsumed", self.main)
        self.assertIn("selection-popup-diagnostics-v1", self.main)

        scene_body = self.main.split("sceneWillConnect: function()", 1)[1].split(
            "\n    sceneDidDisconnect", 1
        )[0]
        selection_body = self.main.split("onPopupMenuOnSelection: function(sender)", 1)[1].split(
            "\n    togglePanel:", 1
        )[0]
        highlight_body = self.main.split("CodexAssistantAddon.prototype.highlightCurrentSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.startCommandPolling", 1
        )[0]
        handler_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]

        self.assertIn("self.nativeHighlightNextSelectionArmed = false", scene_body)
        self.assertIn("self.consumeArmedNativeHighlightSelection(documentController, text)", selection_body)
        self.assertIn("armIfMissingSelection", highlight_body)
        self.assertIn("shouldArmNextSelection", highlight_body)
        self.assertIn("this.armNativeHighlightNextSelection('missing-selection', requestedText)", highlight_body)
        self.assertIn("highlightCommand.armIfMissingSelection = true", handler_body)
        self.assertIn("nativeHighlightCommandPrepared", handler_body)

    def test_native_highlight_armed_selection_polls_pdf_selection_without_popup_event(self) -> None:
        self.assertIn("startNativeHighlightSelectionPoll", self.main)
        self.assertIn("stopNativeHighlightSelectionPoll", self.main)
        self.assertIn("nativeHighlightNextSelectionPollStarted", self.main)
        self.assertIn("nativeHighlightNextSelectionPollObserved", self.main)
        self.assertIn("nativeHighlightNextSelectionPollExpired", self.main)
        self.assertIn("native-highlight-selection-poll-v1", self.main)
        self.assertIn("native-highlight-prefer-next-selection-v1", self.main)

        scene_body = self.main.split("sceneWillConnect: function()", 1)[1].split(
            "\n    sceneDidDisconnect", 1
        )[0]
        arm_body = self.main.split("CodexAssistantAddon.prototype.armNativeHighlightNextSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.consumeArmedNativeHighlightSelection", 1
        )[0]
        poll_body = self.main.split("CodexAssistantAddon.prototype.startNativeHighlightSelectionPoll", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.stopNativeHighlightSelectionPoll", 1
        )[0]
        consume_body = self.main.split("CodexAssistantAddon.prototype.consumeArmedNativeHighlightSelection", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.highlightCurrentSelection", 1
        )[0]

        self.assertIn("self.nativeHighlightNextSelectionPollTimer = null", scene_body)
        self.assertIn("this.startNativeHighlightSelectionPoll()", arm_body)
        self.assertIn("NSTimer.scheduledTimerWithTimeInterval", poll_body)
        self.assertIn("resolveDocumentController(addon, controller, nc)", poll_body)
        self.assertIn("selectionTextFromDocumentController(docController)", poll_body)
        self.assertIn("addon.consumeArmedNativeHighlightSelection(docController, text)", poll_body)
        self.assertIn("this.stopNativeHighlightSelectionPoll()", consume_body)

    def test_context_payload_includes_best_effort_pdf_path(self) -> None:
        self.assertIn("pdfPathFromNotebookController", self.main)
        self.assertIn("pdfPathFromDocumentObject", self.main)
        self.assertIn("'pdfPath'", self.main)
        resolve_body = self.main.split("CodexAssistantAddon.prototype.resolveContext", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.callCompanion", 1
        )[0]
        self.assertIn("var pdfPath = pdfPathFromNotebookController(nc)", resolve_body)
        self.assertIn("pdfPath: pdfPath", resolve_body)
        self.assertIn("documentPath: pdfPath", resolve_body)

    def test_native_bridge_can_upload_current_pdf_cache(self) -> None:
        self.assertIn("codexpaper://upload_pdf", self.controller)
        self.assertIn("uploadPdfToCompanion", self.main)
        self.assertIn("NSData.dataWithContentsOfFile", self.main)
        self.assertIn("cache_pdf_from_marginnote", self.main)
        self.assertIn("pdfBase64", self.main)

    def test_native_bridge_can_open_external_update_url(self) -> None:
        self.assertIn("codexpaper://open_url", self.controller)
        self.assertIn("UIApplication.sharedApplication().openURL", self.controller)
        self.assertIn("NSURL.URLWithString", self.controller)

    def test_native_poll_can_execute_pdf_cache_command_without_system_click(self) -> None:
        self.assertIn("nativeAction", self.main)
        self.assertIn("cache_pdf_from_current_document", self.main)
        self.assertIn("pdfCacheCommandReceived", self.main)
        self.assertIn("pdfPathCandidates", self.main)
        self.assertIn("pdfCacheUploadCandidateFailed", self.main)

        single_branch = self.main.split("if (singleCommand) {", 1)[1].split(
            "addon.postEvent('commandsReceived'", 1
        )[0]
        self.assertIn("addon.handleNativeQueueCommand(singleCommand)", single_branch)
        self.assertIn("addon.ackCommands([String(queueIdSingle)])", single_branch)
        self.assertNotIn("addon.handleCompanionResponse(singleCommand", single_branch)

        native_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("uploadPdfToCompanion", native_body)
        self.assertIn("cache_pdf_from_current_document", native_body)

    def test_native_poll_can_execute_draft_write_command_without_webview_click(self) -> None:
        native_body = self.main.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "\n  CodexAssistantAddon.prototype.ackCommands", 1
        )[0]

        self.assertIn("write_draft", native_body)
        self.assertIn("nativeDraftWriteCommandPrepared", native_body)
        self.assertIn("var draftId = safeString(valueOf(command, 'draftId')", native_body)
        self.assertIn("this.writeDraft(draftId)", native_body)
        self.assertIn("toArray(valueOf(command, 'pdfPathCandidates'))", native_body)

    def test_pdf_cache_upload_callback_does_not_treat_nil_error_as_failure(self) -> None:
        upload_callback = self.main.split("postJSON(CompanionURL, ctx, 30", 1)[1].split(
            "var json = parseJSONData(responseData)", 1
        )[0]

        self.assertIn("!isNil(error)", upload_callback)
        self.assertNotIn("if (error)", upload_callback)


if __name__ == "__main__":
    unittest.main()
