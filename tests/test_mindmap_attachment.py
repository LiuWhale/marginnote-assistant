#!/usr/bin/env python3
from __future__ import annotations

import unittest

import mindmap_attachment


def current_mindmap() -> dict:
    return {
        "noteId": "notebook-root",
        "title": "Paper.pdf",
        "body": "",
        "children": [
            {
                "noteId": "document-root",
                "title": "Paper · Codex 脑图",
                "body": "",
                "children": [
                    {
                        "noteId": "intro-node",
                        "title": "研究背景与问题",
                        "body": "机器人安全研究的背景、任务定义与主要挑战。",
                        "children": [],
                    },
                    {
                        "noteId": "attention-node",
                        "title": "注意力引导安全过滤",
                        "body": "attention map、patch mask 与危险动作识别。",
                        "children": [],
                    },
                ],
            }
        ],
    }


def document_root_target() -> dict:
    return {
        "mode": "document_root",
        "operation": "append_to_document_mindmap_root",
        "label": "文档脑图：Paper · Codex 脑图",
        "rootTitle": "Paper · Codex 脑图",
        "codexId": "mindmap-target:paper",
        "documentKey": "topic:book",
    }


class MindmapAttachmentTests(unittest.TestCase):
    def test_compatible_selected_node_wins(self) -> None:
        proposed = {
            "title": "回答脑图",
            "body": "",
            "children": [
                {
                    "title": "Patch Mask",
                    "body": "attention patch mask 如何定位危险区域。",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "attention-node",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "verified_parent_node")
        self.assertEqual(result["writeTarget"]["parentNoteId"], "attention-node")
        self.assertEqual(result["writeTarget"]["parentNoteTitle"], "注意力引导安全过滤")
        self.assertEqual(result["routing"]["reason"], "compatible-selected-node")
        self.assertFalse(result["routing"]["fallback"])

    def test_stronger_candidate_beats_incompatible_selection(self) -> None:
        proposed = {
            "title": "回答脑图",
            "body": "attention filtering",
            "children": [
                {
                    "title": "注意力掩码",
                    "body": "patch mask 和 attention map 的联系。",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "intro-node",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["parentNoteId"], "attention-node")
        self.assertEqual(result["routing"]["reason"], "best-semantic-match")
        self.assertGreaterEqual(result["routing"]["confidence"], 0.34)

    def test_low_confidence_falls_back_to_document_root(self) -> None:
        proposed = {
            "title": "训练时间调度",
            "body": "学习率 warmup 与 optimizer step。",
            "children": [],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")
        self.assertEqual(result["writeTarget"]["codexId"], "mindmap-target:paper")
        self.assertEqual(result["routing"]["reason"], "low-confidence-document-root-fallback")
        self.assertTrue(result["routing"]["fallback"])

    def test_existing_and_repeated_titles_are_removed_from_proposed_tree(self) -> None:
        proposed = {
            "title": "回答脑图",
            "body": "",
            "children": [
                {"title": "注意力引导安全过滤", "body": "重复已有节点。", "children": []},
                {"title": "验证边界", "body": "只说明证据边界。", "children": []},
                {"title": "验证边界", "body": "重复建议。", "children": []},
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "",
            document_root_target(),
        )

        self.assertEqual(result["duplicateCount"], 2)
        self.assertEqual(
            [child["title"] for child in result["tree"]["children"]],
            ["验证边界"],
        )
        self.assertEqual(
            {item["reason"] for item in result["duplicates"]},
            {"existing-title", "repeated-proposed-title"},
        )

    def test_synthetic_notebook_root_is_never_selected_as_parent(self) -> None:
        proposed = {
            "title": "Paper",
            "body": "document overview",
            "children": [],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "",
            document_root_target(),
        )

        self.assertNotEqual(result["writeTarget"].get("parentNoteId"), "notebook-root")


if __name__ == "__main__":
    unittest.main()
