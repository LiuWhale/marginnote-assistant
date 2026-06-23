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

    def test_visible_surface_is_ai_chat_only(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]
        for marker in [
            'id="aiChatShell"',
            'id="statusPill"',
            'id="settingsButton"',
            'id="contextButton"',
            'id="stopButton"',
            'id="contextSourceLine"',
            'id="selectionPreview"',
            'id="liveHistory"',
            'id="promptInput"',
            'id="sendButton"',
        ]:
            self.assertIn(marker, self.html)

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
            "historyButton",
            "制卡",
            "脑图",
            "高亮",
            "导出",
            "一次性目标",
            "按钮中心",
        ]:
            self.assertNotIn(removed, main_html)

    def test_formal_config_page_owns_runtime_context_and_ai_status(self) -> None:
        for marker in [
            'id="configPage"',
            'id="configBackButton"',
            'id="settingsNotebookLine"',
            'id="settingsDocumentLine"',
            'id="settingsContextScopeLine"',
            'id="readinessPanel"',
            'id="aiBackendSelect"',
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
            "checkForUpdates",
            "installUpdate",
            "renderUpdateStatus",
        ]:
            self.assertIn(marker, self.html + self.js)

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

    def test_main_surface_has_update_notice_but_no_update_install_controls(self) -> None:
        main_html = self.html.split('<main id="aiChatShell"', 1)[1].split("</main>", 1)[0]

        self.assertIn('id="updateNotice"', main_html)
        self.assertIn('id="updateNoticeText"', main_html)
        self.assertIn('id="updateNoticeOpenSettingsButton"', main_html)
        self.assertNotIn('id="updateInstallButton"', main_html)
        self.assertNotIn('id="githubRepoInput"', main_html)

    def test_ai_chat_exposes_context_scope_like_builtin_ai(self) -> None:
        for marker in [
            'id="contextScopeAutoButton"',
            'id="contextScopeSelectionButton"',
            'id="contextScopeDocumentButton"',
            'data-context-scope="auto"',
            'data-context-scope="selection"',
            'data-context-scope="document"',
            'id="contextSourceLine"',
            'data-context-state="empty"',
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

    def test_send_action_always_uses_chat(self) -> None:
        send_body = self.js.split("function sendAction", 1)[1].split("\n  function renderControls", 1)[0]
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

    def test_latest_reply_exposes_mindmap_action_menu(self) -> None:
        for marker in [
            "addAssistantReplyWithActions",
            "reply-mindmap-trigger",
            "reply-mindmap-menu",
            "回答添加到脑图",
            "对话添加到脑图（双向同步）",
            "在脑图中创建卡片树",
            "runReplyMindmapAction",
        ]:
            self.assertIn(marker, self.js + self.css)

    def test_reply_card_tree_prompt_uses_explicit_create_card_tree_command(self) -> None:
        for marker in [
            "[create_card_tree]",
            "根据上面的回答创建一个结构化的卡片树（使用markdown大纲格式）",
            "buildReplyMindmapPrompt",
            "latestChatTranscript",
        ]:
            self.assertIn(marker, self.js)

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
            "ai-edit-accept",
            "ai-edit-reject",
            "postCompanionPath('/marginnote/draft', 'draft_save'",
            "bridge('write_draft'",
        ]:
            self.assertIn(marker, self.js + self.css)
        self.assertNotIn("全部接受", self.js + self.html)
        self.assertNotIn("全部拒绝", self.js + self.html)

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

    def test_progress_copy_matches_ai_chat_only_surface(self) -> None:
        self.assertIn("可继续输入；运行中可点停止。", self.js)
        self.assertNotIn("可继续输入或点击按钮；忙碌时会在消息里给出后续引导。", self.js)

    def test_required_controls_match_minimal_ai_chat_surface(self) -> None:
        required_body = self.js.split("var requiredControlIds = [", 1)[1].split("];", 1)[0]
        for marker in [
            "'aiChatShell'",
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
        self.assertIn(".reply-mindmap-menu", self.css)
        self.assertIn(".ai-edit-operation", self.css)

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
