from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseDocsTests(unittest.TestCase):
    def read_doc(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def contract_unit(self, text: str, anchor: str, required: list[str]) -> str | None:
        paragraphs = [item.strip() for item in text.split("\n\n") if item.strip()]
        lines = [item.strip() for item in text.splitlines() if item.strip()]
        for unit in paragraphs + lines:
            if anchor in unit and all(marker in unit for marker in required):
                return unit
        return None

    def assert_contract_unit(self, text: str, anchor: str, required: list[str]) -> None:
        self.assertIsNotNone(
            self.contract_unit(text, anchor, required),
            "expected one paragraph or checklist line to bind "
            + repr(anchor)
            + " to "
            + repr(required),
        )

    def test_user_guides_document_multi_file_source_workspace_contract(self) -> None:
        for name in ["README.md", "README.zh-CN.md", "docs/USER_MANUAL.md"]:
            with self.subTest(name=name):
                text = self.read_doc(name)
                for marker in [
                    "资料",
                    "一次 Codex CLI 调用",
                    "SOURCES.md",
                    "软链接",
                    "OpenAI API",
                    "不会删除原文件",
                ]:
                    self.assertIn(marker, text)

    def test_release_checklist_covers_three_file_live_and_broken_link_preflight(self) -> None:
        text = self.read_doc("docs/RELEASE_CHECKLIST.md")

        for marker in [
            "三个文件",
            "一次 Codex CLI 调用",
            "SOURCES.md",
            "断开的软链接",
            "模型调用前阻止",
            "Codex CLI 调用数仍为 0",
        ]:
            self.assertIn(marker, text)

    def test_release_docs_cover_final_workspace_security_and_fallback_contracts(self) -> None:
        expectations = {
            "README.md": ["0.4.55", "token", "one file", "textReadable=false", "7 days", "no fixed generation timeout"],
            "README.zh-CN.md": ["0.4.55", "token", "一个文件", "textReadable=false", "7 天", "没有固定生成超时"],
            "docs/USER_MANUAL.md": ["0.4.55", "token", "一个文件", "textReadable=false", "7 天", "没有固定生成超时"],
        }
        for name, markers in expectations.items():
            with self.subTest(name=name):
                text = self.read_doc(name)
                for marker in markers:
                    self.assertIn(marker, text)
                source_section = text.partition("资料")[2]
                self.assertNotIn("本地选择与搜索结果", source_section)
                self.assertNotIn("search-root results", source_section)

        checklist = self.read_doc("docs/RELEASE_CHECKLIST.md")
        self.assertIn("source_workspace.py", checklist)
        self.assertIn("web-action-token", checklist)

    def test_release_docs_cover_one_operation_multi_file_upload(self) -> None:
        expectations = {
            "README.md": [
                "Add Files",
                "one picker operation",
                "20 files",
                "20 MB",
                "PDF",
                "DOCX",
                "PPTX",
                "progress",
                "partial failures",
                "automatically selected",
                "repeated batches",
            ],
            "README.zh-CN.md": [
                "Add Files",
                "一次选择操作",
                "20 个文件",
                "20 MB",
                "PDF",
                "DOCX",
                "PPTX",
                "上传进度",
                "部分失败",
                "自动选中",
                "重复批次",
            ],
            "docs/USER_MANUAL.md": [
                "Add Files",
                "一次选择操作",
                "20 个文件",
                "20 MB",
                "PDF",
                "DOCX",
                "PPTX",
                "上传进度",
                "部分失败",
                "自动选中",
                "重复批次",
            ],
            "docs/RELEASE_CHECKLIST.md": [
                "Add Files",
                "一次原生选择操作",
                "至少两个",
                "20 个文件",
                "20 MB",
                "上传进度",
                "部分失败",
                "自动选中",
                "重复批次",
                "source_workspace_lifecycle.js",
            ],
        }
        for name, markers in expectations.items():
            with self.subTest(name=name):
                text = self.read_doc(name)
                for marker in markers:
                    self.assertIn(marker, text)

        changelog = self.read_doc("CHANGELOG.md")
        section = changelog.partition("## 0.4.53")[2].split("\n## ", 1)[0]
        for marker in [
            "Add Files",
            "one picker operation",
            "20 files",
            "20 MB",
            "progress",
            "partial failures",
            "auto-selection",
            "source_workspace_lifecycle.js",
        ]:
            self.assertIn(marker, section)

    def test_release_docs_cover_repair_cycle_safety_contract(self) -> None:
        marker_soup = (
            "token 127.0.0.1:48761 localhost:48761 [::1]:48761 custom URL "
            "session epoch tombstone retryable confirmation rollback not published"
        )
        self.assertIsNone(
            self.contract_unit(
                marker_soup,
                "token",
                ["only to the exact HTTP loopback Companion origins", "custom URLs never receive it"],
            ),
            "same-line marker soup must not satisfy a condition-to-outcome contract",
        )

        readme = self.read_doc("README.md")
        self.assert_contract_unit(
            readme,
            "Token-aware Python clients",
            [
                "only to the exact HTTP loopback Companion origins",
                "http://127.0.0.1:48761",
                "http://localhost:48761",
                "http://[::1]:48761",
                "custom URLs never receive it",
            ],
        )
        self.assert_contract_unit(
            readme,
            "active conversation is durably restored",
            [
                "epoch no longer matches are rejected",
                "tombstone` that rejects late callbacks instead of recreating the conversation",
                "remains visible as retryable work rather than being acknowledged or discarded",
                "saved as a draft and always requires explicit confirmation before the native write bridge",
            ],
        )
        self.assert_contract_unit(
            readme,
            "source-management mode",
            [
                "select and remove only current conversation membership",
                "never delete originals, extracted/cached files, or upload-registry records",
                "followed current document is protected from removal",
                "disable follow-current before selecting it",
                "If either stage fails, Companion restores the previous membership",
                "If rollback fails, the panel shows an explicit warning and does not report the removal as complete",
            ],
        )
        self.assert_contract_unit(readme, "current public release", ["0.4.55", "releases/tag/v0.4.55"])

        readme_zh = self.read_doc("README.zh-CN.md")
        self.assert_contract_unit(
            readme_zh,
            "支持 token 的 Python 客户端",
            [
                "只会向 `http://127.0.0.1:48761`、`http://localhost:48761` 和 `http://[::1]:48761` 这三个精确 HTTP loopback 来源附加隐式 token",
                "自定义 URL 绝不会收到它",
            ],
        )
        self.assert_contract_unit(
            readme_zh,
            "活动对话在面板重新加载后",
            [
                "epoch 不匹配的变更会被拒绝",
                "tombstone`，迟到回调不能重新创建它",
                "失败的队列项会保留为可重试工作，而不是被确认或丢弃",
                "先保存为草稿，必须经过明确确认后才能调用原生写入桥",
            ],
        )
        self.assert_contract_unit(
            readme_zh,
            "需要缩小当前会话",
            [
                "只处理当前会话的成员关系",
                "不会删除原文件、缓存/提取文件，也不会删除上传注册记录",
                "当前跟随文件受保护，不能移除",
                "先关闭跟随才可以选择它",
                "任一步失败都会恢复旧成员关系并验证恢复结果",
                "若回滚失败，面板会给出明确警告，不能把本次移除显示为完成",
            ],
        )
        self.assert_contract_unit(readme_zh, "当前公开版本", ["0.4.55", "releases/tag/v0.4.55"])

        manual = self.read_doc("docs/USER_MANUAL.md")
        self.assert_contract_unit(
            manual,
            "支持 token 的 Python 客户端",
            [
                "只会向 `http://127.0.0.1:48761`、`http://localhost:48761` 和 `http://[::1]:48761` 这三个精确 HTTP loopback 来源附加隐式 token",
                "自定义 URL 绝不会收到它",
            ],
        )
        self.assert_contract_unit(
            manual,
            "活动会话可从持久化",
            ["epoch 不匹配的迟到结果", "tombstone` 回调都会被拒绝", "不能恢复或覆盖已失效会话"],
        )
        self.assert_contract_unit(
            manual,
            "队列失败",
            ["保持未确认并标记为可重试", "只能保存为草稿", "用户明确确认后才会调用原生写入桥", "不能后台自动写入 MarginNote"],
        )
        self.assert_contract_unit(
            manual,
            "要缩小范围",
            ["全选可移除", "取消全选", "移除所选", "只清空当前会话成员关系", "不删除原文件", "上传注册记录"],
        )
        self.assert_contract_unit(
            manual,
            "跟随当前文件` 开启时",
            ["当前跟随文件受保护", "关闭后才允许选择它", "恢复旧成员关系并验证恢复结果", "若回滚失败，会显示明确警告", "不得把这次操作视为成功"],
        )
        self.assert_contract_unit(manual, "当前公开版本", ["0.4.55", "releases/tag/v0.4.55"])

        checklist = self.read_doc("docs/RELEASE_CHECKLIST.md")
        self.assert_contract_unit(
            checklist,
            "支持 token 的 Python 客户端",
            [
                "只向 `http://127.0.0.1:48761`、`http://localhost:48761` 和 `http://[::1]:48761` 三个精确 HTTP loopback 来源附加隐式 token",
                "自定义 URL 不带 token",
                "重定向和日志均不泄露 token",
            ],
        )
        self.assert_contract_unit(
            checklist,
            "新建/重新打开对话",
            ["session epoch` 不匹配", "tombstone` 回调都必须被拒绝", "失败队列项必须保留为可重试工作", "排队写入只能生成草稿", "必须由用户确认", "不能自动调用原生写入"],
        )
        self.assert_contract_unit(
            checklist,
            "打开资料管理模式",
            ["只改变当前会话的成员关系", "原文件、缓存/提取文件和上传注册记录必须保留", "当前跟随文件必须受保护", "关闭后才允许把它加入移除选择"],
        )
        self.assert_contract_unit(
            checklist,
            "对子集移除",
            ["移除后空集", "更新后必须验证新工作区", "更新或验证失败时必须恢复旧成员关系并验证恢复", "若回滚失败，界面必须显示明确警告", "不能报告操作成功"],
        )
        self.assert_contract_unit(checklist, "正式发布版本", ["0.4.55", "v0.4.55"])
        self.assertIn("https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.55", checklist)

        changelog = self.read_doc("CHANGELOG.md").partition("## 0.4.55")[2].split("\n## ", 1)[0]
        self.assert_contract_unit(changelog, "current_document", ["bookmd5", "documentId", "whole-notebook"])
        self.assert_contract_unit(changelog, "first-click", ["native read callback", "continues automatically"])

    def test_release_status_matrix_tracks_knowledge_os_kernels_and_shell(self) -> None:
        text = self.read_doc("docs/RELEASE_STATUS_MATRIX.md")

        for marker in [
            "knowledgeConsolePanel",
            "Knowledge Console Matrix",
            "knowledge_console.py",
            "tests/test_knowledge_console.py",
            "codex.mn.knowledgeConsoleMatrix.v1",
            "studioCanvasPanel",
            "operationLedgerDrawer",
            "sourceRegistryPanel",
            "verificationReportPanel",
            "externalGatewayPanel",
            "skillCenterPanel",
            "Object Intake router",
            "object_intake.py",
            "tests/test_object_intake.py",
            "codex.mn.objectIntake.v1",
            "Notebook Runbook",
            "notebook_runbook.py",
            "tests/test_notebook_runbook.py",
            "codex.mn.notebookRunbook.v1",
            "Object Task Composer",
            "object_task_composer.py",
            "tests/test_object_task_composer.py",
            "codex.mn.objectTaskComposer.v1",
            "codex.mn.objectTaskWorkflowCandidate.v1",
            "Workflow Builder Board",
            "workflow_builder.py",
            "tests/test_workflow_builder.py",
            "codex.mn.workflowBuilderBoard.v1",
            "workflowBuilderBoardPanel",
            "draft_candidates",
            "waiting_confirmation",
            "notebookObjectTaskComposer",
            "route_skill_center",
            "Live MN Object Kernel",
            "Source Registry action evidence",
            "External Automation Gateway v2",
            "Transactional Native Editor",
            "Workflow Runtime v2",
            "Skill Runtime v2",
            "Verification Agent",
            "codex.mn.verificationReport.v1",
            "final/v3 claim",
            "Arbitrary-document UI functional acceptance",
            "ui_functional_acceptance.py",
            "ui_functional_acceptance_summary",
            "uiFunctionalAcceptanceButton",
            "uiFunctionalAcceptanceLine",
            "UI 功能验收：PASS",
            "UI 功能验收",
            "codex-companion-ui-functional-acceptance-v1",
            "webview_static_controls",
            "webview_button_coverage",
            "webview_browser_render",
            "webview_browser_interaction",
            "webview_browser_actions",
            "webview_browser_write_actions",
            "sendButton",
            "Enter key",
            "conversation_new",
            "buttonActionDeltas",
            "conversationHistoryObjectButton",
            "conversationHistoryAllButton",
            "settings_update",
            "update_check",
            "open_url",
            "diagnose_permissions",
            "open_full_disk_access_settings",
            "request_pdf_cache",
            "request_native_capability_probe",
            "--browser-interaction",
            "--browser-actions",
            "--browser-write-actions",
            "request_mn_object_registry_scan",
            "mn_read_tree",
            "object_graph",
            "object_activity",
            "object_graph_relation_save",
            "notebook_runbook_preflight_record",
            "verificationRepairPlanRecommendedButton",
            "mindmapStudioVerifyButton",
            "mindmapStudioRollbackButton",
            "knowledge_index_search",
            "mindmap_target_status",
            "request_mindmap_diff_apply",
            "ai_edit_transaction_verify",
            "request_mn_object_existence_probe",
            "write_draft",
            "accept_ai_edit_transaction",
            "reject_ai_edit_transaction",
            "native_scope_guards",
            "Collect Single Document Acceptance.command",
            "single_document_acceptance.py",
            "single_document_acceptance",
            "singleDocumentAcceptanceButton",
            "realMnAcceptancePanel",
            "mainUiFunctionalAcceptanceButton",
            "realMnAcceptanceSafeEvidenceButton",
            "主工作台 Verification Center",
            "single_document_acceptance_summary",
            "本文档验收",
        ]:
            self.assertIn(marker, text)

        for stale in [
            "toolActionGrid",
            "goalActionStrip",
            "mainActionStack",
            "goalRunPanel",
            "sourceToolPanel",
            "stagedActionLine",
            "workflowActionPanel",
            "mindmapActionGrid",
            "moreToolsPanel",
            "moreToolsSummary",
            "secondaryToolsPanel",
            "secondaryToolsSummary",
            "workflowActionGrid",
            "workflowActionGroups",
            "goalActionPanel",
            "sourceActionGrid",
            "sourceToolGrid",
            "mindmapToolGrid",
            "文档与脑图工具条",
            "aiActionPanel/primaryActionGrid/sourceToolPanel/nodeToolPanel",
            "主操作网格是 5 格",
            "`goalToggleButton` 在 `primaryActionGrid`",
            "`goalActionStrip` 内联在常用任务标题区",
            "空闲为“开始”",
            "常用任务网格是 4+4 两行主操作区",
            "常用任务网格是 3+3 两行生成区",
            "原文工具折叠在 `secondaryToolsPanel`",
        ]:
            self.assertNotIn(stale, text)

    def test_release_docs_describe_goal_run_as_one_shot_not_persisted_context(self) -> None:
        combined = "\n".join(
            self.read_doc(name)
            for name in [
                "docs/PRODUCT_SPEC.md",
                "docs/USER_MANUAL.md",
                "docs/RELEASE_STATUS_MATRIX.md",
                "README.md",
            ]
        )

        self.assertIn("一次性长任务", combined)
        self.assertIn("不会保存成长期当前目标", combined)
        for stale in [
            "会保存当前目标",
            "状态栏显示当前目标摘要",
            "状态栏显示当前目标",
            "目标和上传文件能在",
        ]:
            self.assertNotIn(stale, combined)

    def test_ultimate_design_is_knowledge_agent_os_not_chat_plus_buttons(self) -> None:
        ultimate = self.read_doc("docs/ULTIMATE_PLUGIN_DESIGN.md")
        product_spec = self.read_doc("docs/PRODUCT_SPEC.md")
        manual = self.read_doc("docs/USER_MANUAL.md")
        combined = "\n".join([ultimate, product_spec, manual])

        for marker in [
            "MarginNote Knowledge Agent OS",
            "不是当前聊天插件的增强版",
            "双模式产品",
            "Chat Mode",
            "Agent Workspace Mode",
            "Knowledge OS Contract",
            "对象层",
            "操作层",
            "证据层",
            "聊天区只能作为命令入口",
            "聊天是入口，不是终局",
            "Agent Workspace 才是生产系统",
            "当前 0.4.x 是 Chat Mode + Agent Workspace 雏形",
            "从回答按钮升级到对象操作",
            "真实脑图工作台",
            "对象优先、操作优先、证据优先",
            "不得把现有控件堆叠当作终局",
            "Object Graph",
            "Object Browser",
            "object_browser",
            "mn_object_registry",
            "codex.mn.mnObjectRegistry.v1",
            "mnobj:note:<noteId>",
            "objectRegistryScanButton",
            "request_mn_object_registry_scan",
            "scan_mn_objects",
            "mnObjectRegistryScanFinished",
            "native_object_scan",
            "扫描对象会进入 Object Graph",
            "扫描证据存在后会直接打开 Object Browser",
            "open_source_registry",
            "已有可读材料时会打开 Source Registry",
            "没有原生扫描证据时会请求扫描 MN 对象",
            "open_object_browser",
            "open_mindmap_studio",
            "open_card_factory",
            "open_workflow_builder",
            "已有脑图树缓存后会直接打开 Mindmap Studio",
            "卡片覆盖` 轴会打开 Card Factory",
            "已有 run 后会直接打开 Workflow Builder",
            "Runbook 现在包含确认上下文、核对来源清单、扫描 MN 对象、读取脑图基线、检查卡片覆盖、生成操作计划、检查工作流、核对操作证据八步",
            "不会自动生成卡片",
            "native_object_scan 父子边",
            "点击扫描对象会打开该对象图谱",
            "点击扫描对象会打开该对象活动和账本",
            "扫描 MN",
            "mindmapTreeReadFinished",
            "objectBrowserPanel",
            "browserAction",
            "codex.mn.objectBrowser.v1",
            "Knowledge Index 实体",
            "knowledge_relation",
            "entityType/noteId/sourceRef/relations",
            "mn_note",
            "nativeMindmapTreeEvidence",
            "mindmap_tree_cache",
            "manual_relation",
            "object_graph_relation_save/delete",
            "object_graph_manual_relation",
            "manualRelation",
            "可编辑关系边",
            "Operation Ledger",
            "Knowledge Graph",
            "Workflow Runtime",
            "External Automation Gateway",
            "Skill Marketplace",
            "v3.0",
            "当前 0.4.x 不是终局",
            "AI Copilot 面板",
            "MNObject Registry",
            "Operation Compiler",
            "Object Browser",
            "Mindmap Studio",
            "Card Factory",
            "codex.mn.cardFactory.v1",
            "cardType",
            "reviewPrompt",
            "learningGoal",
            "卡片工厂",
            "Knowledge Graph Studio",
            "Workflow Builder",
            "Skill Center",
            "Operation Ledger Explorer",
            "只要首屏仍然像聊天框加按钮，就不算终极版",
            "v3 产品合约",
            "第一屏合约",
            "对象合约",
            "操作合约",
            "学习合约",
            "证据合约",
            "扩展合约",
            "如果一个版本的主要体验仍然是“问一句、看回答、点生成卡片/脑图、去设置里修问题”",
            "终局必须和当前版本拉开的可见断层",
            "当前 0.4.x 做不到的事",
            "终局验收不按按钮数量算",
            "默认入口必须能在 Chat Mode 和 Agent Workspace Mode 之间切换",
            "modeSwitchBar",
            "chatModeButton",
            "agentWorkspaceModeButton",
            "modeIntentLine",
            "activeProductMode",
            "lastWorkspacePane",
            "Workspace Navigator",
            "workspaceNavigator",
            "Knowledge Console Matrix",
            "knowledge_console.py",
            "codex.mn.knowledgeConsoleMatrix.v1",
            "Object Intake",
            "object_intake.py",
            "codex.mn.objectIntake.v1",
            "Object Task Composer",
            "object_task_composer.py",
            "codex.mn.objectTaskComposer.v1",
            "codex.mn.objectTaskDraft.v1",
            "codex.mn.objectTaskWorkflowCandidate.v1",
            "Workflow Builder Board",
            "workflow_builder.py",
            "codex.mn.workflowBuilderBoard.v1",
            "workflowBuilderBoardPanel",
            "draft_candidates",
            "waiting_confirmation",
            "workflow 候选",
            "启动候选必须继续经过 Workflow Runtime",
            "Object Task Composer`，把对象路线转成任务草案和 workflow 候选",
            "route_source_registry",
            "route_object_browser",
            "route_mindmap_studio",
            "route_card_factory",
            "route_workflow_builder",
            "route_skill_center",
            "route_verification_center",
            "用户不需要先发 prompt 才知道能做什么",
            "Mindmap Studio",
            "Card Factory",
            "Operation Ledger",
            "Workflow Builder",
            "Skill Center",
            "能像 Finder 一样浏览 notebook 对象",
            "能原地编辑真实现有脑图",
            "复习队列和覆盖率是 Card Factory 的必选闭环",
            "外部自动化不能绕过 dry-run、确认、ledger 和回滚",
            "技能包不是自定义 prompt",
            "如果用户的高阶工作仍只能靠输入一句话再点回答下方按钮，就不是终局",
            "跨 notebook 知识层",
            "外部 URL/API 自动化",
        ]:
            self.assertIn(marker, combined)

        for stale in [
            "# Codex Companion Ultimate Design: MN Agent Workbench\n",
            "终极版必须出现的新形态",
            "v2.0 不是“能聊天”就完成",
        ]:
            self.assertNotIn(stale, ultimate)

    def test_ultimate_design_is_not_current_control_inventory(self) -> None:
        ultimate = self.read_doc("docs/ULTIMATE_PLUGIN_DESIGN.md")

        for marker in [
            "终局反证清单",
            "产品断代路线",
            "架构断代",
            "体验断代",
            "数据断代",
            "能力断代",
            "当前预览版 UI 功能验收只证明不退化，不证明 v3 完成",
            "终局验收不按按钮数量算，而按对象覆盖、操作闭环、学习闭环和证据闭环算",
            "如果第一屏仍然需要用户先提问，失败",
            "如果脑图仍然以生成新树为主，失败",
            "如果卡片仍然以回答切块为主，失败",
            "如果拒绝后只能相信日志，失败",
            "如果技能仍然只是 prompt 收藏，失败",
        ]:
            self.assertIn(marker, ultimate)

        for implementation_inventory in [
            "modeSwitchBar",
            "chatModeButton",
            "agentWorkspaceModeButton",
            "modeIntentLine",
            "activeProductMode",
            "lastWorkspacePane",
            "workspaceNavigator",
            "objectBrowserPanel",
            "workflowBuilderBoardPanel",
            "tests/test_knowledge_console.py",
            "tests/test_object_intake.py",
            "tests/test_object_task_composer.py",
            "tests/test_workflow_builder.py",
            "ui_functional_acceptance.py --browser-render --browser-interaction --browser-actions --browser-write-actions",
        ]:
            self.assertNotIn(implementation_inventory, ultimate)

    def test_docs_describe_mindmap_studio_as_operation_workspace(self) -> None:
        combined = "\n".join(
            self.read_doc(name)
            for name in [
                "README.md",
                "README.zh-CN.md",
                "docs/PRODUCT_SPEC.md",
                "docs/USER_MANUAL.md",
                "CHANGELOG.md",
            ]
        )

        for marker in [
            "Mindmap Studio",
            "读取现有脑图",
            "预览 Diff",
            "应用所选",
            "验证事务",
            "回滚事务",
            "不是回答下方按钮的别名",
        ]:
            self.assertIn(marker, combined)


if __name__ == "__main__":
    unittest.main()
