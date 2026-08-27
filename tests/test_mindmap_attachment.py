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
    def test_current_candidates_are_deduplicated_by_note_id_across_repeated_views(self) -> None:
        current = {
            "noteId": "notebook-root",
            "children": [
                {
                    "noteId": "branch-a",
                    "children": [
                        {
                            "noteId": "shared-note",
                            "title": "共享节点",
                            "body": "同一个原生节点。",
                            "children": [],
                        }
                    ],
                },
                {
                    "noteId": "shared-note",
                    "title": "共享节点",
                    "body": "同一个原生节点。",
                    "children": [],
                },
            ],
        }

        candidates = mindmap_attachment.flatten_current_nodes(current)

        self.assertEqual(
            [item["noteId"] for item in candidates].count("shared-note"),
            1,
        )

    def test_one_short_chinese_phrase_cannot_count_as_three_independent_signals(self) -> None:
        proposed = {
            "title": "回答脑图",
            "body": "这里只是顺带提到优化器，并不讨论该节点。",
            "children": [{"title": "一般结论", "body": "优化器不是本段主题。", "children": []}],
        }
        current = {
            "noteId": "notebook-root",
            "children": [
                {
                    "noteId": "optimizer",
                    "title": "优化器",
                    "body": "",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")

    def test_tree_fingerprint_changes_when_title_changes_without_node_count_change(self) -> None:
        before = {
            "noteId": "root",
            "title": "Root",
            "body": "",
            "documentId": "B1",
            "children": [{"noteId": "N1", "title": "Old Name", "body": "", "children": []}],
        }
        after = {
            "noteId": "root",
            "title": "Root",
            "body": "",
            "documentId": "B1",
            "children": [{"noteId": "N1", "title": "New Name", "body": "", "children": []}],
        }

        self.assertNotEqual(
            mindmap_attachment.tree_fingerprint(before),
            mindmap_attachment.tree_fingerprint(after),
        )

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
        self.assertEqual(result["routing"]["decision"], "existing_parent")
        self.assertFalse(result["routing"]["requiresParentConfirmation"])
        self.assertGreaterEqual(result["routing"]["confidence"], 0.34)

    def test_close_existing_parent_candidates_require_confirmation_instead_of_auto_routing(self) -> None:
        proposed = {
            "title": "SimbaV2 缩放稳定性",
            "body": "超球归一化控制特征范数、参数范数和梯度稳定性。",
            "children": [
                {
                    "title": "高 UTD 稳定训练",
                    "body": "强化学习模型扩展与有效学习率。",
                    "children": [],
                }
            ],
        }
        current = {
            "noteId": "notebook-root",
            "children": [
                {
                    "noteId": "doc-root",
                    "title": "Scale RL · Codex 脑图",
                    "documentId": "B1",
                    "children": [
                        {
                            "noteId": "candidate-a",
                            "title": "SimbaV2 超球归一化",
                            "body": "强化学习特征范数、参数范数、梯度稳定性与高 UTD 扩展。",
                            "documentId": "B1",
                            "children": [],
                        },
                        {
                            "noteId": "candidate-b",
                            "title": "SimbaV2 超球归一化",
                            "body": "强化学习特征范数、参数范数、梯度稳定性与高 UTD 扩展。",
                            "documentId": "B1",
                            "children": [],
                        },
                    ],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
            expected_document_id="B1",
        )

        self.assertEqual(result["routing"]["decision"], "ambiguous")
        self.assertEqual(result["routing"]["reason"], "ambiguous-existing-parent")
        self.assertTrue(result["routing"]["requiresParentConfirmation"])
        self.assertEqual(
            {item["noteId"] for item in result["routing"]["parentCandidates"]},
            {"candidate-a", "candidate-b"},
        )

    def test_low_confidence_creates_semantic_parent_under_document_root(self) -> None:
        proposed = {
            "title": "训练时间调度",
            "body": "本节讨论训练调度。",
            "children": [
                {
                    "title": "学习率 Warmup",
                    "body": "逐步提高学习率。",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")
        self.assertEqual(result["routing"]["decision"], "new_parent")
        self.assertEqual(result["routing"]["reason"], "new-semantic-parent")
        self.assertEqual(result["routing"]["newParentTitle"], "训练时间调度")
        self.assertEqual(result["tree"]["children"][0]["title"], "训练时间调度")
        self.assertEqual(
            result["tree"]["children"][0]["children"][0]["title"],
            "学习率 Warmup",
        )

    def test_document_root_container_title_is_not_reused_as_semantic_parent(self) -> None:
        proposed = {
            "title": "Paper · Codex 脑图",
            "body": "本次回答解释 SimbaV2。",
            "children": [
                {
                    "title": "SimbaV2 超球归一化",
                    "body": "控制特征和参数范数。",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current_mindmap(),
            "",
            document_root_target(),
        )

        self.assertEqual(result["routing"]["decision"], "new_parent")
        self.assertEqual(result["routing"]["newParentTitle"], "SimbaV2 超球归一化")
        self.assertNotEqual(result["routing"]["newParentTitle"], "Paper")

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
        self.assertEqual(result["routing"]["decision"], "new_parent")
        self.assertEqual(result["routing"]["reason"], "new-semantic-parent")
        self.assertEqual(result["routing"]["newParentTitle"], "训练时间调度")
        self.assertTrue(result["routing"]["fallback"])

    def test_low_confidence_uses_unique_current_document_root_in_open_mindmap(self) -> None:
        proposed = {
            "title": "回答脑图",
            "body": "与现有节点没有足够语义重合。",
            "children": [{"title": "新主题", "body": "新增内容。", "children": []}],
        }
        current = {
            "noteId": "notebook-root",
            "title": "I-JEPA",
            "body": "",
            "documentId": "",
            "children": [
                {
                    "noteId": "study-set-root",
                    "title": "StudySet",
                    "body": "",
                    "documentId": "B1_StudySet",
                    "children": [],
                },
                {
                    "noteId": "ijepa-root",
                    "title": "I-JEPA",
                    "body": "I-JEPA\n\n",
                    "documentId": "B1",
                    "children": [],
                },
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
            expected_document_id="B1",
        )

        self.assertEqual(result["writeTarget"]["mode"], "verified_parent_node")
        self.assertEqual(result["writeTarget"]["parentNoteId"], "ijepa-root")
        self.assertEqual(result["writeTarget"]["parentNoteTitle"], "I-JEPA")
        self.assertEqual(result["routing"]["decision"], "new_parent")
        self.assertEqual(result["routing"]["reason"], "new-semantic-parent")
        self.assertEqual(result["routing"]["newParentTitle"], "新主题")
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

    def test_single_shared_word_is_not_enough_for_automatic_parent(self) -> None:
        current = current_mindmap()
        current["children"][0]["children"].append(
            {
                "noteId": "safety-node",
                "title": "Safety",
                "body": "",
                "children": [],
            }
        )
        proposed = {
            "title": "实验配置",
            "body": "Safety appears once in a long unrelated answer about optimizer schedules.",
            "children": [
                {
                    "title": "学习率设置",
                    "body": "warmup、batch size 和训练轮数。",
                    "children": [],
                }
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")
        self.assertTrue(result["routing"]["fallback"])

    def test_one_long_chinese_phrase_still_counts_as_one_signal(self) -> None:
        current = current_mindmap()
        current["children"][0]["children"].append(
            {
                "noteId": "filter-node",
                "title": "注意力过滤器",
                "body": "",
                "children": [],
            }
        )
        proposed = {
            "title": "补充说明",
            "body": "注意力过滤器",
            "children": [],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")
        self.assertTrue(result["routing"]["fallback"])

    def test_exact_duplicate_matching_preserves_meaningful_punctuation(self) -> None:
        current = current_mindmap()
        current["children"][0]["children"].append(
            {
                "noteId": "c-node",
                "title": "C",
                "body": "language label",
                "children": [],
            }
        )
        proposed = {
            "title": "回答脑图",
            "body": "",
            "children": [
                {"title": "C++", "body": "distinct title", "children": []},
                {"title": "A/B", "body": "ratio", "children": []},
                {"title": "AB", "body": "letters", "children": []},
            ],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["duplicateCount"], 0)
        self.assertEqual(result["tree"]["children"][0]["title"], "C++等主题")
        self.assertEqual(
            [child["title"] for child in result["tree"]["children"][0]["children"]],
            ["C++", "A/B", "AB"],
        )

    def test_verified_parent_carries_the_body_evidence_used_for_routing(self) -> None:
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
            "attention-node",
            document_root_target(),
        )

        self.assertEqual(
            result["writeTarget"]["parentEvidenceBody"],
            "attention map、patch mask 与危险动作识别。",
        )

    def test_two_generic_shared_words_are_not_strong_enough_to_route(self) -> None:
        current = {
            "noteId": "notebook-root",
            "title": "Paper.pdf",
            "children": [
                {
                    "noteId": "generic",
                    "title": "Model Results",
                    "body": "",
                    "children": [],
                }
            ],
        }
        proposed = {
            "title": "Unrelated optimizer notes",
            "body": "A long discussion mentions model and results only in passing.",
            "children": [{"title": "Schedule", "body": "warmup and epochs", "children": []}],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")

    def test_one_cjk_phrase_cannot_count_as_three_independent_parent_signals(self) -> None:
        current = {
            "noteId": "notebook-root",
            "title": "Paper.pdf",
            "children": [
                {
                    "noteId": "attention-filter",
                    "title": "注意力过滤器",
                    "body": "注意力；过滤器",
                    "children": [],
                }
            ],
        }
        proposed = {
            "title": "回答脑图",
            "body": "注意力过滤器",
            "children": [{"title": "补充说明", "body": "注意力过滤器", "children": []}],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")

    def test_exact_duplicate_matching_preserves_case(self) -> None:
        current = {
            "noteId": "notebook-root",
            "title": "Paper.pdf",
            "children": [{"noteId": "upper", "title": "US", "body": "", "children": []}],
        }
        proposed = {
            "title": "回答脑图",
            "children": [{"title": "us", "body": "pronoun", "children": []}],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "",
            document_root_target(),
        )

        self.assertEqual(result["duplicateCount"], 0)
        self.assertEqual(result["tree"]["children"][0]["title"], "us")

    def test_candidates_are_limited_to_the_current_document(self) -> None:
        current = current_mindmap()
        current["children"][0]["documentId"] = "OTHER"
        current["children"][0]["children"][1]["documentId"] = "OTHER"
        proposed = {
            "title": "回答脑图",
            "body": "attention filtering patch mask",
            "children": [{"title": "注意力掩码", "body": "attention map", "children": []}],
        }

        result = mindmap_attachment.plan_reply_attachment(
            proposed,
            current,
            "attention-node",
            document_root_target(),
            expected_document_id="CURRENT",
        )

        self.assertEqual(result["writeTarget"]["mode"], "document_root")


if __name__ == "__main__":
    unittest.main()
