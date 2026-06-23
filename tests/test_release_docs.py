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


if __name__ == "__main__":
    unittest.main()
