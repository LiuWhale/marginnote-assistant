from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ReleaseDocsTests(unittest.TestCase):
    def read_doc(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_release_status_matrix_names_current_button_layout_controls(self) -> None:
        text = self.read_doc("docs/RELEASE_STATUS_MATRIX.md")

        for marker in [
            "toolActionGrid",
            "goalActionStrip",
            "mainActionStack",
            "goalRunPanel",
            "sourceToolPanel",
            "healthCheckButton",
            "Collect Single Document Acceptance.command",
            "single_document_acceptance.py",
            "single_document_acceptance",
            "singleDocumentAcceptanceButton",
            "single_document_acceptance_summary",
            "本文档验收",
            "常用网格是 2x2",
            "`mainActionStack` 按一次性目标、常用任务、工具区顺序排列",
            "`goalRunPanel` 是独立的一次性目标区",
            "stagedActionLine",
            "`workflowActionPanel` 常驻显示",
            "mindmapActionGrid",
            "sourceToolPanel",
            "可排队",
            "空闲时显示 `队列`",
        ]:
            self.assertIn(marker, text)

        for stale in [
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
