from __future__ import annotations

import base64
import importlib.util
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Any


COMPANION_PATH = Path(__file__).resolve().parents[1] / "companion.py"


def load_companion(root: Path) -> Any:
    old_root = os.environ.get("CODEX_MN_COMPANION_HOME")
    os.environ["CODEX_MN_COMPANION_HOME"] = str(root)
    try:
        spec = importlib.util.spec_from_file_location("codex_mn_companion_controls", COMPANION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old_root is None:
            os.environ.pop("CODEX_MN_COMPANION_HOME", None)
        else:
            os.environ["CODEX_MN_COMPANION_HOME"] = old_root


class CompanionControlsTests(unittest.TestCase):
    def test_default_ai_profile_is_gpt55_fast_with_medium_reasoning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            settings = companion.runtime_settings()
            status = companion.status_payload()

            self.assertEqual(settings["model"], "gpt-5.5")
            self.assertEqual(settings["speed"], "fast")
            self.assertEqual(status["model"], "gpt-5.5")
            self.assertEqual(status["speed"], "fast")
            self.assertEqual(companion.CODEX_CLI_REASONING["fast"], "medium")
            self.assertEqual(companion.CODEX_CLI_TIMEOUTS["fast"], 75)

    def test_chat_prompt_does_not_inherit_saved_goal_or_defense_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_goal(
                {
                    "title": "精读当前材料",
                    "detail": "生成 defense 讲稿、短卡片、脑图，并检查高亮。",
                }
            )

            prompt = companion.build_model_input({"prompt": "Figure 2 做什么"}, "chat")

            self.assertIn("Figure 2 做什么", prompt)
            self.assertNotIn("当前目标：", prompt)
            self.assertNotIn("生成 defense 讲稿", prompt)
            self.assertNotIn("答辩准备", prompt)
            self.assertNotIn("defense 说法", prompt)

    def test_repairs_pdf_math_unicode_low_plane_selection_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            raw = "̂ 흉a푖−1= ̂ 흉a푖+ 훿 ⋅ ∇̂ 흉a푖log 휋휙(̂ 흉a푖∣ ̂ 흉푠0) +√훽푖풛,"

            repaired = companion.repair_pdf_extracted_math_text(raw)
            context = companion.selected_context({"prompt": "解释公式", "selectionText": raw})

            self.assertIn("𝝉̂a𝑖−1", repaired)
            self.assertIn("𝛿", repaired)
            self.assertIn("𝜋𝜙", repaired)
            self.assertIn("𝛽𝑖𝒛", repaired)
            self.assertNotIn("흉", repaired)
            self.assertNotIn("훿", repaired)
            self.assertIn(repaired, context)

    def test_context_scope_aliases_are_normalized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            self.assertEqual(companion.normalize_context_scope({"contextScope": "selection"}), "selection")
            self.assertEqual(companion.normalize_context_scope({"contextScope": "全文"}), "document")
            self.assertEqual(companion.normalize_context_scope({"contextScope": "full"}), "document")
            self.assertEqual(companion.normalize_context_scope({"contextScope": "unknown"}), "auto")

    def test_selection_scope_does_not_request_document_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_document_context(payload: dict[str, Any], query: str, max_chars: int = 7000) -> dict[str, Any]:
                calls.append(query)
                return {"ok": True, "text": "全文检索片段：不应该出现"}

            old = companion.document_context_for_model
            companion.document_context_for_model = fake_document_context
            try:
                prompt = companion.build_model_input(
                    {
                        "contextScope": "selection",
                        "prompt": "解释这个公式",
                        "selectionText": "selected equation",
                    },
                    "chat",
                )
            finally:
                companion.document_context_for_model = old

            self.assertEqual(calls, [])
            self.assertIn("PDF 选中文本：\nselected equation", prompt)
            self.assertNotIn("全文检索片段", prompt)

    def test_document_scope_uses_retrieved_document_context_not_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_document_context(payload: dict[str, Any], query: str, max_chars: int = 7000) -> dict[str, Any]:
                calls.append(query)
                return {"ok": True, "text": "当前文档全文检索片段：\n[第2页] retrieved document chunk"}

            old = companion.document_context_for_model
            companion.document_context_for_model = fake_document_context
            try:
                prompt = companion.build_model_input(
                    {
                        "contextScope": "document",
                        "prompt": "解释整篇材料",
                        "selectionText": "accidental small selection",
                    },
                    "chat",
                )
            finally:
                companion.document_context_for_model = old

            self.assertEqual(len(calls), 1)
            self.assertIn("用户输入：\n解释整篇材料", prompt)
            self.assertIn("[第2页] retrieved document chunk", prompt)
            self.assertNotIn("accidental small selection", prompt)

    def test_document_scope_ignores_old_uploaded_files_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            upload_path = Path(tmp) / "uploads" / "old-note.md"
            upload_path.parent.mkdir(parents=True, exist_ok=True)
            upload_path.write_text("old uploaded note should not override current PDF", encoding="utf-8")
            companion.save_uploaded_files(
                [
                    {
                        "id": "old-note",
                        "name": "old-note.md",
                        "path": str(upload_path),
                        "size": upload_path.stat().st_size,
                        "uploaded_at": "2026-06-23T00:00:00+0800",
                    }
                ]
            )

            def fake_document_context(payload: dict[str, Any], query: str, max_chars: int = 7000) -> dict[str, Any]:
                return {"ok": True, "text": "当前文档全文检索片段：\n[第5页] Figure 2 evidence"}

            old = companion.document_context_for_model
            companion.document_context_for_model = fake_document_context
            try:
                prompt = companion.build_model_input(
                    {"contextScope": "document", "prompt": "Figure 2 做什么"},
                    "chat",
                )
            finally:
                companion.document_context_for_model = old

            self.assertIn("Figure 2 evidence", prompt)
            self.assertNotIn("old uploaded note should not override", prompt)
            self.assertIn("已忽略历史上传文件", prompt)

    def test_model_history_drops_stale_missing_pdf_replies_when_document_context_is_available(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            payload = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            companion.append_history(
                payload,
                "详细解释这篇论文",
                "我现在无法详细解释这篇论文，因为本次插件没有传入可解析的本地 PDF 路径，全文内容没有被读取到。",
            )
            companion.append_history(payload, "那之前怎么解读的其他论文", "正常历史回答")
            model_input = "当前文档全文检索片段：\n[第1页] Abstract and evidence are available now."

            history = companion.history_for_model(payload, model_input)

            contents = "\n".join(item["content"] for item in history)
            self.assertIn("正常历史回答", contents)
            self.assertNotIn("全文内容没有被读取到", contents)
            self.assertNotIn("没有传入可解析的本地 PDF 路径", contents)

    def test_conversation_actions_create_list_load_and_delete_document_scoped_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            first = companion.handle_action({**base, "action": "conversation_new"})
            second = companion.handle_action({**base, "action": "conversation_new"})

            self.assertTrue(first["ok"])
            self.assertTrue(second["ok"])
            self.assertNotEqual(first["conversation"]["conversationId"], second["conversation"]["conversationId"])

            companion.append_history(
                {**base, "conversationId": first["conversation"]["conversationId"]},
                "第一轮问题",
                "第一轮回答",
            )
            companion.append_history(
                {**base, "conversationId": second["conversation"]["conversationId"]},
                "第二轮问题",
                "第二轮回答",
            )

            listed = companion.handle_action({**base, "action": "conversation_list"})

            self.assertTrue(listed["ok"])
            self.assertEqual(listed["conversation_count"], 2)
            titles = [item["title"] for item in listed["conversations"]]
            self.assertIn("第一轮问题", titles)
            self.assertIn("第二轮问题", titles)
            for item in listed["conversations"]:
                self.assertEqual(item["topicid"], "T1")
                self.assertEqual(item["bookmd5"], "B1")
                self.assertEqual(item["messageCount"], 2)
                self.assertRegex(item["sessionId"], r"^[a-f0-9]{24}$")

            first_item = next(item for item in listed["conversations"] if item["title"] == "第一轮问题")
            loaded = companion.handle_action({**base, "action": "conversation_load", "sessionId": first_item["sessionId"]})

            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["conversation"]["sessionId"], first_item["sessionId"])
            self.assertEqual([item["content"] for item in loaded["history"]], ["第一轮问题", "第一轮回答"])

            deleted = companion.handle_action({**base, "action": "conversation_delete", "sessionId": first_item["sessionId"]})
            self.assertTrue(deleted["ok"])
            relisted = companion.handle_action({**base, "action": "conversation_list"})
            self.assertEqual(relisted["conversation_count"], 1)
            self.assertEqual(relisted["conversations"][0]["title"], "第二轮问题")

    def test_conversation_history_is_filterable_by_mn_object(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            selection_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:history1",
                "kind": "selection",
                "title": "PDF 选区",
                "sourceRef": {"page": 3, "quote": "selection source"},
            }
            note_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:history2",
                "kind": "note",
                "title": "已有卡片",
                "sourceRef": {"page": 4, "quote": "note source"},
            }

            first = companion.handle_action({**base, "mnObject": selection_object, "action": "conversation_new"})
            second = companion.handle_action({**base, "mnObject": note_object, "action": "conversation_new"})

            self.assertEqual(first["conversation"]["objectRef"]["objectId"], "mnobj:selection:history1")
            self.assertEqual(second["conversation"]["objectRef"]["kind"], "note")

            companion.append_history(
                {
                    **base,
                    "mnObject": selection_object,
                    "conversationId": first["conversation"]["conversationId"],
                },
                "解释这个选区",
                "选区回答",
            )
            companion.append_history(
                {
                    **base,
                    "mnObject": note_object,
                    "conversationId": second["conversation"]["conversationId"],
                },
                "解释这张卡片",
                "卡片回答",
            )

            all_conversations = companion.handle_action({**base, "action": "conversation_list"})
            self.assertEqual(all_conversations["conversation_count"], 2)
            self.assertEqual(
                sorted(item["objectRef"]["objectId"] for item in all_conversations["conversations"]),
                ["mnobj:note:history2", "mnobj:selection:history1"],
            )

            filtered = companion.handle_action(
                {**base, "action": "conversation_list", "mnObjectId": "mnobj:selection:history1"}
            )
            self.assertEqual(filtered["conversation_count"], 1)
            self.assertEqual(filtered["conversations"][0]["title"], "解释这个选区")
            self.assertEqual(filtered["conversations"][0]["objectRef"]["sourceRef"]["quote"], "selection source")

            blocked = companion.handle_action(
                {
                    **base,
                    "action": "conversation_load",
                    "sessionId": filtered["conversations"][0]["sessionId"],
                    "mnObjectId": "mnobj:note:history2",
                }
            )
            self.assertFalse(blocked["ok"])
            self.assertIn("当前对象", blocked["message"])

    def test_diagnostic_logs_record_action_lifecycle_without_secrets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action_logged(
                {
                    "action": "settings_update",
                    "source": "unittest",
                    "settings": {
                        "model": "gpt-5.5",
                        "openaiApiKey": "sk-test-secret-value-1234567890",
                    },
                }
            )

            self.assertTrue(result["ok"])
            self.assertRegex(result["requestId"], r"^[a-f0-9]{12}$")
            logs = companion.read_recent_diagnostic_logs(20)
            events = [item.get("event") for item in logs]
            self.assertIn("action.start", events)
            self.assertIn("action.end", events)
            blob = json.dumps(logs, ensure_ascii=False)
            self.assertIn(result["requestId"], blob)
            self.assertIn("settings_update", blob)
            self.assertIn("[redacted]", blob)
            self.assertNotIn("sk-test-secret-value", blob)

    def test_diagnostic_action_logs_promote_mn_object_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:log123",
                "kind": "selection",
                "title": "PDF 选区",
                "sourceRef": {"page": 9, "quote": "log source"},
            }

            result = companion.handle_action_logged(
                {
                    "action": "settings_update",
                    "source": "unittest",
                    "mnObject": mn_object,
                    "settings": {"model": "gpt-5.5"},
                }
            )

            self.assertTrue(result["ok"])
            logs = [
                item
                for item in companion.read_recent_diagnostic_logs(20)
                if item.get("requestId") == result["requestId"]
            ]
            self.assertEqual([item.get("event") for item in logs], ["action.start", "action.end"])
            for item in logs:
                self.assertEqual(item["objectRef"]["objectId"], "mnobj:selection:log123")
                self.assertEqual(item["objectRef"]["kind"], "selection")
                self.assertEqual(item["objectRef"]["sourceRef"]["quote"], "log source")

    def test_object_activity_aggregates_history_workflows_transactions_and_logs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:activity1",
                "kind": "selection",
                "title": "PDF 选区",
                "sourceRef": {"page": 7, "quote": "activity source"},
            }
            other_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:activity2",
                "kind": "note",
                "title": "其他卡片",
                "sourceRef": {"page": 8, "quote": "other source"},
            }

            conversation = companion.handle_action({**base, "mnObject": mn_object, "action": "conversation_new"})["conversation"]
            companion.append_history(
                {**base, "mnObject": mn_object, "conversationId": conversation["conversationId"]},
                "对象问题",
                "对象回答",
            )
            other_conversation = companion.handle_action(
                {**base, "mnObject": other_object, "action": "conversation_new"}
            )["conversation"]
            companion.append_history(
                {**base, "mnObject": other_object, "conversationId": other_conversation["conversationId"]},
                "其他问题",
                "其他回答",
            )

            workflow = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "workflow_start",
                    "prompt": "解释并制卡",
                    "workflowId": "selection_to_cards",
                    "selectionText": "activity source",
                }
            )
            self.assertTrue(workflow["ok"])

            companion.append_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "activity-tx",
                        "draftId": "activity-draft",
                        "createdNoteIds": ["N-ACT"],
                        "createdCount": 1,
                        "mnObjectId": "mnobj:selection:activity1",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "PDF 选区",
                        "mnObjectSourceRef": {"page": 7, "quote": "activity source"},
                    },
                }
            )
            companion.handle_action_logged(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "settings_update",
                    "settings": {"model": "gpt-5.5"},
                }
            )
            companion.handle_action_logged(
                {
                    **base,
                    "mnObject": other_object,
                    "action": "settings_update",
                    "settings": {"model": "gpt-5.5"},
                }
            )

            activity = companion.handle_action({**base, "action": "object_activity", "mnObjectId": "mnobj:selection:activity1"})

            self.assertTrue(activity["ok"])
            self.assertEqual(activity["objectRef"]["objectId"], "mnobj:selection:activity1")
            self.assertEqual(activity["counts"]["conversations"], 1)
            self.assertEqual(activity["counts"]["workflowRuns"], 1)
            self.assertEqual(activity["counts"]["transactions"], 1)
            self.assertGreaterEqual(activity["counts"]["logs"], 2)
            self.assertEqual(activity["conversations"][0]["title"], "对象问题")
            self.assertEqual(activity["workflowRuns"][0]["mnObjectId"], "mnobj:selection:activity1")
            self.assertEqual(activity["transactions"][0]["transactionId"], "activity-tx")
            self.assertEqual(activity["conversations"][0]["activityAction"]["action"], "conversation_load")
            self.assertEqual(activity["conversations"][0]["activityAction"]["payload"]["sessionId"], conversation["sessionId"])
            self.assertEqual(activity["workflowRuns"][0]["activityAction"]["action"], "workflow_status")
            self.assertEqual(activity["workflowRuns"][0]["activityAction"]["payload"]["workflowRunId"], workflow["summary"]["id"])
            self.assertEqual(activity["transactions"][0]["activityAction"]["action"], "ai_edit_transaction_get")
            self.assertEqual(activity["transactions"][0]["activityAction"]["payload"]["transactionId"], "activity-tx")
            self.assertTrue(all(item["activityAction"]["action"] == "log_detail" for item in activity["logs"]))
            self.assertTrue(all(item["objectRef"]["objectId"] == "mnobj:selection:activity1" for item in activity["logs"]))
            blob = json.dumps(activity, ensure_ascii=False)
            self.assertIn("activity source", blob)
            self.assertNotIn("其他问题", blob)
            self.assertNotIn("mnobj:note:activity2", blob)

    def test_diagnostic_logs_recent_and_clear_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_diagnostic_log("warn", "unit.example", "测试日志", extra={"detail": "可分析"})

            recent = companion.handle_action({"action": "logs_recent", "limit": 5})
            self.assertTrue(recent["ok"])
            self.assertEqual(recent["logs"][-1]["event"], "unit.example")
            self.assertIn("diagnostics.jsonl", recent["logPath"])
            self.assertIn("events.jsonl", recent["eventsPath"])

            cleared = companion.handle_action({"action": "logs_clear"})
            self.assertTrue(cleared["ok"])
            self.assertEqual(companion.read_recent_diagnostic_logs(5), [])

    def test_auto_scope_prefers_selection_unless_prompt_requests_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_document_context(payload: dict[str, Any], query: str, max_chars: int = 7000) -> dict[str, Any]:
                calls.append(query)
                return {"ok": True, "text": "当前文档全文检索片段：\n[第1页] full document chunk"}

            old = companion.document_context_for_model
            companion.document_context_for_model = fake_document_context
            try:
                selected_prompt = companion.build_model_input(
                    {
                        "contextScope": "auto",
                        "prompt": "解释这个位置",
                        "selectionText": "selected passage",
                    },
                    "chat",
                )
                document_prompt = companion.build_model_input(
                    {
                        "contextScope": "auto",
                        "prompt": "全文解释一下",
                        "selectionText": "selected passage",
                    },
                    "chat",
                )
            finally:
                companion.document_context_for_model = old

            self.assertEqual(len(calls), 1)
            self.assertIn("PDF 选中文本：\nselected passage", selected_prompt)
            self.assertNotIn("full document chunk", selected_prompt)
            self.assertIn("full document chunk", document_prompt)
            self.assertNotIn("selected passage", document_prompt)

    def test_document_retrieval_ranks_relevant_chunks_with_page_labels(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            record = {
                "chunks": [
                    {"page": 1, "start": 0, "text": "Abstract and unrelated setup."},
                    {
                        "page": 5,
                        "start": 0,
                        "text": "Attention guided safety filter uses robot attention maps to detect unsafe actions.",
                    },
                    {"page": 8, "start": 0, "text": "Appendix details unrelated baselines."},
                ]
            }

            context = companion.retrieved_document_context_from_cache(record, "attention safety filter", max_chars=500)

            self.assertIn("[第5页]", context)
            self.assertIn("Attention guided safety filter", context)
            self.assertNotIn("Appendix details unrelated", context)

    def test_document_retrieval_boosts_figure_number_queries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            record = {
                "chunks": [
                    {"page": 1, "start": 0, "text": "Figure 1: model overview and abstract context."},
                    {"page": 4, "start": 0, "text": "Figure 2: pipeline for attention heatmap mask generation."},
                    {"page": 9, "start": 0, "text": "Figure 3: ablation summary."},
                ]
            }

            context = companion.retrieved_document_context_from_cache(record, "Figure 2 做什么", max_chars=320)

            self.assertIn("[第4页]", context)
            self.assertIn("Figure 2", context)
            self.assertNotIn("Figure 1", context)

    def test_generate_card_prompt_is_neutral_without_defense_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_goal(
                {
                    "title": "精读当前材料",
                    "detail": "生成 defense 讲稿、短卡片、脑图，并检查高亮。",
                }
            )

            prompt = companion.build_model_input({"prompt": "请生成卡片"}, "generate_card")

            self.assertIn("请生成卡片", prompt)
            self.assertNotIn("当前目标：", prompt)
            self.assertNotIn("生成 defense 讲稿", prompt)
            self.assertNotIn("答辩准备", prompt)
            self.assertNotIn("defense 说法", prompt)

    def test_generate_mindmap_prompt_is_neutral_without_defense_request(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            prompt = companion.build_model_input({"prompt": "生成一个当前材料脑图"}, "generate_mindmap")

            self.assertIn("生成一个当前材料脑图", prompt)
            self.assertNotIn("Defense", prompt)
            self.assertNotIn("答辩准备", prompt)

    def test_goal_run_prompt_keeps_explicit_goal_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_goal(
                {
                    "title": "精读当前材料",
                    "detail": "生成 defense 讲稿、短卡片、脑图，并检查高亮。",
                }
            )

            prompt = companion.build_model_input({"prompt": "请开始执行"}, "goal_run")

            self.assertIn("当前目标：精读当前材料", prompt)
            self.assertIn("生成 defense 讲稿", prompt)

    def test_legacy_goal_file_without_saved_mode_is_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.write_json_file(
                companion.GOAL_PATH,
                {
                    "title": "精读当前材料",
                    "detail": "生成 defense 讲稿、短卡片、脑图，并检查高亮。",
                    "updated_at": "2026-06-11T16:56:55+0800",
                },
            )

            goal = companion.active_goal()

            self.assertEqual(goal["title"], "")
            self.assertEqual(goal["detail"], "")

    def test_openai_key_is_persisted_to_env_but_never_echoed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            updated = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "openaiApiKey": "sk-test-1234567890abcdef",
                        "model": "gpt-5.2",
                    },
                }
            )

            self.assertTrue(updated["ok"])
            self.assertTrue(updated["openai_configured"])
            self.assertNotIn("openaiApiKey", updated["settings"])
            self.assertNotIn("sk-test", updated["reply"])
            self.assertIn("OPENAI_API_KEY=", companion.CONFIG_PATH.read_text(encoding="utf-8"))
            self.assertNotIn("openaiApiKey", companion.SETTINGS_PATH.read_text(encoding="utf-8"))
            self.assertTrue(companion.status_payload()["openai_configured"])

            cleared = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "clearOpenAIKey": True,
                    },
                }
            )
            self.assertTrue(cleared["ok"])
            self.assertFalse(cleared["openai_configured"])
            self.assertNotIn("sk-test", cleared["reply"])
            self.assertNotIn("OPENAI_API_KEY=", companion.CONFIG_PATH.read_text(encoding="utf-8"))
            self.assertFalse(companion.status_payload()["openai_configured"])

    def test_drafts_are_stored_for_explicit_write_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            draft_payload = {
                "ok": True,
                "message": "ready",
                "reply": "preview text",
                "cards": [{"title": "T", "body": "B"}],
                "mindmap": {"title": "Root", "children": [{"title": "Child", "children": []}]},
            }

            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_card",
                    "draft": draft_payload,
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(saved["ok"])
            self.assertEqual(saved["draft"]["card_count"], 1)
            self.assertTrue(saved["draft"]["has_mindmap"])
            self.assertEqual(saved["draft"]["operation_manifest"]["operationCount"], 3)
            self.assertEqual(saved["draft"]["operation_manifest"]["createCards"], 1)
            self.assertEqual(saved["draft"]["operation_manifest"]["createMindmapNodes"], 2)
            self.assertIn(saved["draft"]["operation_manifest"]["dryRun"]["status"], {"ready", "unknown"})
            self.assertEqual(
                saved["draft"]["operation_manifest"]["operationPlan"]["schema"],
                "codex.mn.operationPlan.v1",
            )
            self.assertEqual(
                [item["op"] for item in saved["draft"]["operation_manifest"]["operationPlan"]["operations"]],
                ["create_note", "create_mindmap_node", "create_mindmap_node"],
            )
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["cards"][0]["title"], "T")
            self.assertEqual(loaded["mindmap"]["title"], "Root")
            self.assertEqual(loaded["operationManifest"]["operationCount"], 3)

            preview = companion.handle_action(
                {
                    "action": "operation_plan_preview",
                    "draftId": saved["draft"]["id"],
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )
            self.assertTrue(preview["ok"], preview)
            self.assertEqual(preview["operationPlan"]["operationCount"], 3)
            self.assertIn(preview["dryRun"]["status"], {"ready", "unknown"})
            self.assertIn("Operation dry-run", preview["reply"])

    def test_draft_summary_exposes_card_factory_quality(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_card",
                    "draft": {
                        "ok": True,
                        "message": "ready",
                        "reply": "preview text",
                        "cards": [
                            {"title": "Same", "body": "长正文。" * 260, "type": "concept"},
                            {"title": "Same", "body": "有来源。\nSource: p.4 quote", "cardType": "evidence"},
                        ],
                    },
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(saved["ok"])
            quality = saved["draft"]["card_quality"]
            self.assertEqual(quality["schema"], "codex.mn.cardQuality.v1")
            self.assertEqual(quality["cardCount"], 2)
            self.assertEqual(quality["longCardCount"], 1)
            self.assertEqual(quality["duplicateTitleCount"], 1)
            self.assertEqual(quality["missingSourceCount"], 1)
            self.assertEqual(quality["status"], "warn")

    def test_draft_update_rewrites_cards_from_editable_text_before_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_card",
                    "draft": {
                        "ok": True,
                        "message": "ready",
                        "reply": "preview text",
                        "cards": [{"title": "Old", "body": "Old body"}],
                    },
                }
            )

            updated = companion.update_draft(
                {
                    "id": saved["draft"]["id"],
                    "editText": "## New card\nNew body line 1\nNew body line 2\n\n## Second\nBody",
                }
            )

            self.assertTrue(updated["ok"], updated)
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertEqual(loaded["cards"][0]["title"], "New card")
            self.assertIn("New body line 2", loaded["cards"][0]["body"])
            self.assertEqual(loaded["cards"][1]["title"], "Second")
            self.assertIn("## New card", loaded["draft"]["edit_text"])

    def test_draft_update_can_exclude_selected_mindmap_diff_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_mindmap",
                    "draft": {
                        "ok": True,
                        "message": "ready",
                        "mindmap": {
                            "title": "Root",
                            "children": [
                                {"title": "Keep A", "children": []},
                                {"title": "Drop B", "children": []},
                                {
                                    "title": "Keep C",
                                    "children": [
                                        {"title": "Drop C child", "children": []},
                                        {"title": "Keep C child", "children": []},
                                    ],
                                },
                            ],
                        },
                    },
                }
            )

            updated = companion.update_draft(
                {
                    "id": saved["draft"]["id"],
                    "excludedMindmapPaths": ["0.2", "0.3.1"],
                }
            )

            self.assertTrue(updated["ok"], updated)
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertEqual([child["title"] for child in loaded["mindmap"]["children"]], ["Keep A", "Keep C"])
            self.assertEqual([child["title"] for child in loaded["mindmap"]["children"][1]["children"]], ["Keep C child"])
            self.assertEqual(loaded["operationManifest"]["createMindmapNodes"], 4)
            self.assertEqual(loaded["excludedMindmapPaths"], ["0.2", "0.3.1"])

    def test_draft_update_can_edit_selected_mindmap_diff_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_mindmap",
                    "draft": {
                        "ok": True,
                        "message": "ready",
                        "mindmap": {
                            "title": "Root",
                            "children": [
                                {"title": "Keep A", "body": "A body", "children": []},
                                {"title": "Old B", "body": "B body", "children": []},
                                {"title": "Keep C", "children": [{"title": "Old child", "children": []}]},
                            ],
                        },
                    },
                }
            )

            updated = companion.update_draft(
                {
                    "id": saved["draft"]["id"],
                    "mindmapNodeEdits": [
                        {"proposedPath": "0.2", "title": "Edited B", "body": "Edited B body"},
                        {"path": "0.3.1", "body": "Edited child body"},
                    ],
                }
            )

            self.assertTrue(updated["ok"], updated)
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertEqual(loaded["mindmap"]["children"][1]["title"], "Edited B")
            self.assertEqual(loaded["mindmap"]["children"][1]["body"], "Edited B body")
            self.assertEqual(loaded["mindmap"]["children"][2]["children"][0]["title"], "Old child")
            self.assertEqual(loaded["mindmap"]["children"][2]["children"][0]["body"], "Edited child body")
            self.assertEqual(loaded["operationManifest"]["createMindmapNodes"], 5)
            self.assertEqual(loaded["mindmapNodeEdits"][0]["proposedPath"], "0.2")

    def test_run_state_is_visible_in_queue_status_and_expires(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            started = companion.update_run_state(
                True,
                action="chat",
                stage="正在询问 Codex",
                detail="模型正在生成回答",
                topicid="T1",
                bookmd5="B1",
                queue_id="Q1",
                request_id="REQ1",
            )

            self.assertTrue(started["active"])
            self.assertEqual(started["requestId"], "REQ1")
            queue = companion.queue_status_payload("T1", "B1")
            self.assertTrue(queue["run"]["active"])
            self.assertEqual(queue["run"]["action"], "chat")
            self.assertEqual(queue["run"]["stage"], "正在询问 Codex")
            self.assertEqual(queue["run"]["detail"], "模型正在生成回答")
            self.assertEqual(queue["run"]["queue_id"], "Q1")
            self.assertEqual(queue["run"]["requestId"], "REQ1")
            self.assertGreaterEqual(queue["run"]["elapsed_seconds"], 0)
            self.assertEqual(companion.status_payload()["run"]["action"], "chat")
            self.assertEqual(companion.status_payload()["run"]["requestId"], "REQ1")
            queue_reply = companion.handle_action({"action": "queue_status", "topicid": "T1", "bookmd5": "B1"})
            self.assertIn("运行状态", queue_reply["reply"])
            self.assertIn("正在询问 Codex", queue_reply["reply"])
            self.assertIn("模型正在生成回答", queue_reply["reply"])
            self.assertNotIn("排队引导", queue_reply["reply"])
            self.assertNotIn("排队用途", queue_reply["reply"])

            stale = dict(started)
            stale["updated_epoch"] = 1
            companion.write_json_file(companion.RUN_STATE_PATH, stale)

            expired = companion.active_run_status(max_age_seconds=1)

            self.assertFalse(expired["active"])
            self.assertTrue(expired["expired"])
            self.assertIn("stale", expired["detail"])

    def test_status_payload_exposes_mn4_runtime_stale_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            root = Path(tmp)
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            (extension / "main.js").write_text("new runtime\n", encoding="utf-8")
            (extension / "web/app.js").write_text("new web\n", encoding="utf-8")
            companion.MN_EXTENSION_DIR = extension
            events = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"controls": "promptInput", "missing": ""},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "candidateMethods": [],
                        "capabilityMatrix": {},
                        "handlerFeatures": [
                            "native-highlight-arm-next-selection-default",
                            "native-highlight-prefer-next-selection-v1",
                            "native-highlight-command-prepared",
                            "selection-popup-diagnostics-v1",
                            "native-highlight-selection-poll-v1",
                            "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                        ],
                    },
                },
                {
                    "ts": "2026-06-11T10:24:40+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
            ]
            companion.EVENTS_PATH.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in events) + "\n",
                encoding="utf-8",
            )
            future = 4_000_000_000
            os.utime(extension / "main.js", (future, future))
            os.utime(extension / "web/app.js", (future, future))

            status = companion.status_payload()

            self.assertIn("mnRuntime", status)
            runtime = status["mnRuntime"]
            self.assertFalse(runtime["ready"])
            self.assertTrue(runtime["staleRuntime"])
            self.assertTrue(runtime["runtimeHandlerStale"])
            self.assertIn("probe_native_api_capabilities", runtime["runtimeHandlerStaleActions"])
            self.assertIn("重新打开", runtime["nextStep"])
            self.assertIn("MN4 运行态未刷新", runtime["summary"])

    def test_status_payload_reports_reload_panel_unknown_as_handler_stale_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            root = Path(tmp)
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            for relative in ("main.js", "CodexWebPanelController.js", "web/app.js", "web/index.html", "web/app.css"):
                path = extension / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("current runtime\n", encoding="utf-8")
                os.utime(path, (1_000, 1_000))
            companion.MN_EXTENSION_DIR = extension
            events = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"controls": "promptInput", "missing": ""},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "candidateMethods": [],
                        "capabilityMatrix": {},
                        "handlerFeatures": [
                            "native-highlight-arm-next-selection-default",
                            "native-highlight-prefer-next-selection-v1",
                            "native-highlight-command-prepared",
                            "selection-popup-diagnostics-v1",
                            "native-highlight-selection-poll-v1",
                            "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                        ],
                    },
                },
                {
                    "ts": "2026-06-11T13:10:08+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "reload_web_panel"},
                },
            ]
            companion.EVENTS_PATH.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in events) + "\n",
                encoding="utf-8",
            )

            runtime = companion.status_payload()["mnRuntime"]

            self.assertTrue(runtime["runtimeHandlerStale"])
            self.assertEqual(runtime["runtimeHandlerStaleActions"], ["reload_web_panel"])
            self.assertIn("reload_web_panel", runtime["summary"])

    def test_status_payload_does_not_keep_runtime_handler_stale_after_later_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            root = Path(tmp)
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            for relative in ("main.js", "CodexWebPanelController.js", "web/app.js", "web/index.html", "web/app.css"):
                path = extension / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("current runtime\n", encoding="utf-8")
                os.utime(path, (1_000, 1_000))
            companion.MN_EXTENSION_DIR = extension
            events = [
                {
                    "ts": "2026-06-11T08:48:23+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"controls": "promptInput,primaryTaskPanel,toolActionGrid", "missing": ""},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "candidateMethods": [],
                        "capabilityMatrix": {},
                        "handlerFeatures": [
                            "native-highlight-arm-next-selection-default",
                            "native-highlight-prefer-next-selection-v1",
                            "native-highlight-command-prepared",
                            "selection-popup-diagnostics-v1",
                            "native-highlight-selection-poll-v1",
                            "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                        ],
                    },
                },
            ]
            companion.EVENTS_PATH.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in events) + "\n",
                encoding="utf-8",
            )

            runtime = companion.status_payload()["mnRuntime"]

            self.assertTrue(runtime["nativeApiReady"])
            self.assertFalse(runtime["staleRuntime"])
            self.assertFalse(runtime["runtimeHandlerStale"])
            self.assertEqual(runtime["runtimeHandlerStaleActions"], [])
            self.assertTrue(runtime["ready"])

    def test_status_payload_marks_native_handler_stale_when_required_features_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            root = Path(tmp)
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            main_js = extension / "main.js"
            main_js.write_text(
                "native-highlight-arm-next-selection-default\nnative-highlight-prefer-next-selection-v1\nnative-highlight-command-prepared\nselection-popup-diagnostics-v1\nnative-highlight-selection-poll-v1\nselection-popup-scene-observer-v1\nselection-popup-notebook-rebind-v1\nnative-highlight-selection-text-resolver-v1\ncontext-refresh-clears-stale-selection-v1\nai-edit-transaction-rollback-v1\nai-edit-undo-rollback-v2\n",
                encoding="utf-8",
            )
            for relative in ("CodexWebPanelController.js", "web/app.js", "web/index.html", "web/app.css"):
                path = extension / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("current runtime\n", encoding="utf-8")
                os.utime(path, (1_000, 1_000))
            os.utime(main_js, (1_000, 1_000))
            companion.MN_EXTENSION_DIR = extension
            events = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"controls": "promptInput,primaryTaskPanel,toolActionGrid", "missing": ""},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"candidateMethods": [], "capabilityMatrix": {"nativeCards": {"ready": True}}},
                },
            ]
            companion.EVENTS_PATH.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in events) + "\n",
                encoding="utf-8",
            )

            runtime = companion.status_payload()["mnRuntime"]

            self.assertFalse(runtime["ready"])
            self.assertTrue(runtime["runtimeHandlerStale"])
            self.assertIn("native-handler-features", runtime["runtimeHandlerStaleActions"])
            self.assertEqual(
                runtime["missingNativeHandlerFeatures"],
                [
                    "native-highlight-arm-next-selection-default",
                    "native-highlight-prefer-next-selection-v1",
                    "native-highlight-command-prepared",
                    "selection-popup-diagnostics-v1",
                    "native-highlight-selection-poll-v1",
                    "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                ],
            )

    def test_status_payload_fails_closed_when_installed_handler_feature_source_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            root = Path(tmp)
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            for relative in ("CodexWebPanelController.js", "web/app.js", "web/index.html", "web/app.css"):
                path = extension / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("current runtime\n", encoding="utf-8")
                os.utime(path, (1_000, 1_000))
            companion.MN_EXTENSION_DIR = extension
            events = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"controls": "promptInput,primaryTaskPanel,toolActionGrid", "missing": ""},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                    "extra": {"candidateMethods": [], "capabilityMatrix": {"nativeCards": {"ready": True}}},
                },
            ]
            companion.EVENTS_PATH.write_text(
                "\n".join(json.dumps(item, ensure_ascii=False) for item in events) + "\n",
                encoding="utf-8",
            )

            runtime = companion.status_payload()["mnRuntime"]

            self.assertFalse(runtime["ready"])
            self.assertEqual(
                runtime["requiredNativeHandlerFeatures"],
                [
                    "native-highlight-arm-next-selection-default",
                    "native-highlight-prefer-next-selection-v1",
                    "native-highlight-command-prepared",
                    "selection-popup-diagnostics-v1",
                    "native-highlight-selection-poll-v1",
                    "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                ],
            )
            self.assertEqual(
                runtime["missingNativeHandlerFeatures"],
                [
                    "native-highlight-arm-next-selection-default",
                    "native-highlight-prefer-next-selection-v1",
                    "native-highlight-command-prepared",
                    "selection-popup-diagnostics-v1",
                    "native-highlight-selection-poll-v1",
                    "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                            "ai-edit-transaction-rollback-v1",
                            "ai-edit-undo-rollback-v2",
                ],
            )
            self.assertIn("native-handler-features", runtime["runtimeHandlerStaleActions"])

    def test_restart_marginnote4_action_is_user_triggered_and_reopens_app(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[list[str]] = []

            class FakeCompleted:
                def __init__(self, returncode: int = 0, stdout: str = "", stderr: str = "") -> None:
                    self.returncode = returncode
                    self.stdout = stdout
                    self.stderr = stderr

            def fake_run(args: list[str], **kwargs: Any) -> FakeCompleted:
                calls.append(args)
                return FakeCompleted()

            old_run = companion.subprocess.run
            old_sleep = companion.time.sleep
            companion.subprocess.run = fake_run
            companion.time.sleep = lambda seconds: None
            try:
                result = companion.handle_action({"action": "restart_marginnote4", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run
                companion.time.sleep = old_sleep

            self.assertTrue(result["ok"])
            self.assertEqual(result["message"], "已请求重启 MarginNote 4。")
            self.assertIn("重新打开 Codex 面板", result["reply"])
            self.assertEqual(calls[0][0], "/usr/bin/osascript")
            self.assertIn('tell application id "QReader.MarginStudy.easy" to quit', calls[0])
            self.assertEqual(calls[1], ["/usr/bin/open", "-b", "QReader.MarginStudy.easy"])

    def test_release_acceptance_summary_action_surfaces_blockers_and_next_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[list[str]] = []
            envs: list[dict[str, str]] = []

            class FakeCompleted:
                returncode = 1
                stdout = json.dumps(
                    {
                        "releasable": False,
                        "blockers": [
                            {
                                "name": "native_visible_highlight",
                                "status": "BLOCK",
                                "detail": "0 rows have ZHIGHLIGHTS",
                                "nextActions": ["Click 高亮选区 on selected PDF text."],
                            }
                        ],
                        "gates": [],
                    },
                    ensure_ascii=False,
                )
                stderr = ""

            def fake_run(args: list[str], **kwargs: Any) -> FakeCompleted:
                calls.append(args)
                envs.append(kwargs.get("env") or {})
                return FakeCompleted()

            old_run = companion.subprocess.run
            companion.subprocess.run = fake_run
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            self.assertTrue(result["ok"])
            self.assertFalse(result["releasable"])
            self.assertEqual(result["blockerCount"], 1)
            self.assertEqual(result["blockers"][0]["name"], "native_visible_highlight")
            self.assertIn("native_visible_highlight", result["reply"])
            self.assertIn("高亮选区", result["reply"])
            self.assertIn("releaseAcceptance", result)
            self.assertIn("release_acceptance.py", calls[0][1])
            self.assertIn("--json", calls[0])
            self.assertIn("/opt/homebrew/bin", envs[0]["PATH"])
            self.assertIn("/usr/local/bin", envs[0]["PATH"])

    def test_single_document_acceptance_summary_action_surfaces_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            companion = load_companion(root)
            root.joinpath("events.jsonl").write_text(
                json.dumps(
                    {
                        "event": "webControlsReady",
                        "topicid": "T1",
                        "bookmd5": "B1",
                        "extra": {
                            "controls": (
                                "promptInput,sendButton,stagedActionLine,clearStagedActionButton,"
                                "goalActionStrip,mainActionStack,goalRunPanel,primaryActionGrid,workflowActionPanel,"
                                "mindmapToolPanel,mindmapActionGrid,sourceToolPanel,toolActionGrid"
                            ),
                            "missing": "",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {"action": "single_document_acceptance_summary", "topicid": "T1", "bookmd5": "B1"}
            )

            self.assertTrue(result["ok"])
            self.assertFalse(result["singleDocumentReady"])
            self.assertGreater(result["singleDocumentBlockerCount"], 0)
            self.assertIn("本文档验收", result["reply"])
            self.assertIn("singleDocumentAcceptance", result)
            self.assertEqual(result["singleDocumentAcceptance"]["topicid"], "T1")
            self.assertEqual(result["singleDocumentAcceptance"]["bookmd5"], "B1")
            self.assertIn("Web controls loaded", result["reply"])
            self.assertIn("MN native API matrix", result["reply"])

    def test_release_acceptance_summary_groups_blockers_by_user_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeCompleted:
                returncode = 1
                stdout = json.dumps(
                    {
                        "releasable": False,
                        "blockers": [
                            {
                                "name": "runtime_web_controls",
                                "status": "BLOCK",
                                "detail": "stale runtime",
                                "nextActions": ["重新打开 Codex 面板。"],
                            },
                            {
                                "name": "native_api_matrix",
                                "status": "BLOCK",
                                "detail": "old native handler",
                                "nextActions": ["刷新MN能力。"],
                            },
                            {
                                "name": "native_visible_highlight",
                                "status": "BLOCK",
                                "detail": "no visible highlight",
                                "nextActions": ["选中文本后点高亮选区。"],
                            },
                            {
                                "name": "signed_pkg",
                                "status": "BLOCK",
                                "detail": "no signature",
                                "nextActions": ["运行 Build Signed Package.command。"],
                            },
                            {
                                "name": "notarized_pkg",
                                "status": "BLOCK",
                                "detail": "not notarized",
                                "nextActions": ["运行 Notarize Package.command。"],
                            },
                            {
                                "name": "cross_machine_install",
                                "status": "BLOCK",
                                "detail": "missing cross-machine install evidence",
                                "nextActions": ["运行 Collect Cross-Machine Evidence.command。"],
                            },
                        ],
                    },
                    ensure_ascii=False,
                )
                stderr = ""

            old_run = companion.subprocess.run
            companion.subprocess.run = lambda *args, **kwargs: FakeCompleted()
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            self.assertTrue(result["ok"])
            group_titles = [group["title"] for group in result["blockerGroups"]]
            self.assertEqual(
                group_titles,
                ["MN4 运行态", "真实功能证据", "签名与公证", "跨机器安装"],
            )
            reply = result["reply"]
            for title in group_titles:
                self.assertIn(title, reply)
            self.assertIn("runtime_web_controls", result["blockerGroups"][0]["items"][0]["name"])
            self.assertIn("native_api_matrix", json.dumps(result["blockerGroups"][0], ensure_ascii=False))
            self.assertIn("signed_pkg", json.dumps(result["blockerGroups"][2], ensure_ascii=False))
            self.assertIn("notarized_pkg", json.dumps(result["blockerGroups"][2], ensure_ascii=False))
            self.assertIn("Collect Cross-Machine Evidence.command", reply)

    def test_release_acceptance_summary_returns_direct_recovery_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeCompleted:
                returncode = 1
                stdout = json.dumps(
                    {
                        "releasable": False,
                        "blockers": [
                            {
                                "name": "release_sha256_manifest",
                                "status": "BLOCK",
                                "detail": "permission_denied: grant Full Disk Access",
                            },
                            {
                                "name": "runtime_web_controls",
                                "status": "BLOCK",
                                "detail": "runtime handler does not know reload_web_panel",
                            },
                            {
                                "name": "native_visible_highlight",
                                "status": "BLOCK",
                                "detail": "no visible highlight",
                            },
                        ],
                    },
                    ensure_ascii=False,
                )
                stderr = ""

            old_run = companion.subprocess.run
            companion.subprocess.run = lambda *args, **kwargs: FakeCompleted()
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            action_ids = [item["id"] for item in result["recoveryActions"]]
            self.assertEqual(
                action_ids,
                [
                    "open_full_disk_access_settings",
                    "refresh_native_capabilities",
                    "collect_mn_runtime_evidence",
                    "restart_marginnote4",
                    "diagnose_highlights",
                    "request_native_highlight_selection",
                    "rerun_release_acceptance",
                ],
            )
            self.assertTrue(result["permissionLimited"])
            self.assertEqual(result["recoveryActions"][0]["title"], "打开权限设置")
            self.assertEqual(result["recoveryActions"][3]["title"], "重启MN4")
            self.assertEqual(result["recoveryActions"][3]["handler"], "restartMarginNote4")

    def test_release_acceptance_summary_returns_external_evidence_guide(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeCompleted:
                returncode = 1
                stdout = json.dumps(
                    {
                        "releasable": False,
                        "blockers": [
                            {"name": "runtime_web_controls", "status": "BLOCK", "detail": "stale panel"},
                            {"name": "native_visible_highlight", "status": "BLOCK", "detail": "missing highlight"},
                            {"name": "signed_pkg", "status": "BLOCK", "detail": "no signature"},
                            {"name": "notarized_pkg", "status": "BLOCK", "detail": "not notarized"},
                            {"name": "cross_machine_install", "status": "BLOCK", "detail": "missing evidence"},
                        ],
                    },
                    ensure_ascii=False,
                )
                stderr = ""

            old_run = companion.subprocess.run
            companion.subprocess.run = lambda *args, **kwargs: FakeCompleted()
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            guide = result["evidenceGuide"]
            guide_ids = [item["id"] for item in guide]
            self.assertEqual(
                guide_ids,
                [
                    "collect_mn_runtime_evidence",
                    "collect_native_highlight_evidence",
                    "build_signed_package",
                    "notarize_package",
                    "collect_cross_machine_evidence",
                ],
            )
            self.assertTrue(all(item.get("title") for item in guide))
            self.assertTrue(all(item.get("command") for item in guide))
            self.assertTrue(all(item.get("outputHint") for item in guide))
            self.assertIn("Refresh MN Runtime.command", guide[0]["command"])
            self.assertIn("Collect Native Highlight Evidence.command", guide[1]["command"])
            self.assertIn("Build Signed Package.command", guide[2]["command"])
            self.assertIn("Notarize Package.command", guide[3]["command"])
            self.assertIn("Collect Cross-Machine Evidence.command", guide[4]["command"])
            self.assertIn("--native-highlight-evidence", guide[1]["outputHint"])
            self.assertIn("--cross-machine-evidence", guide[4]["outputHint"])

    def test_release_acceptance_summary_reports_parse_failure_instead_of_zero_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeCompleted:
                returncode = 1
                stdout = ""
                stderr = "Traceback: FileNotFoundError: node"

            old_run = companion.subprocess.run
            companion.subprocess.run = lambda *args, **kwargs: FakeCompleted()
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            self.assertFalse(result["ok"])
            self.assertEqual(result["blockerCount"], 0)
            self.assertIn("发布验收报告解析失败", result["message"])
            self.assertIn("FileNotFoundError", result["reply"])

    def test_release_acceptance_summary_prioritizes_full_disk_access_when_service_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeCompleted:
                returncode = 1
                stdout = json.dumps(
                    {
                        "releasable": False,
                        "blockers": [
                            {
                                "name": "signed_pkg",
                                "status": "BLOCK",
                                "detail": "permission_denied: grant Full Disk Access to the Companion service/Python and retry",
                                "nextActions": ["Install a Developer ID Installer certificate in Keychain."],
                            }
                        ],
                        "evidence": {
                            "unitTests": {
                                "stderr": "PermissionError: Operation not permitted: web/index.html",
                            }
                        },
                    },
                    ensure_ascii=False,
                )
                stderr = ""

            old_run = companion.subprocess.run
            companion.subprocess.run = lambda *args, **kwargs: FakeCompleted()
            try:
                result = companion.handle_action({"action": "release_acceptance_summary", "source": "unittest"})
            finally:
                companion.subprocess.run = old_run

            self.assertTrue(result["ok"])
            self.assertTrue(result["permissionLimited"])
            self.assertIn("Full Disk Access", result["reply"])
            self.assertIn("permissionSubjects", result)
            subjects = result["permissionSubjects"]
            self.assertGreaterEqual(len(subjects), 2)
            self.assertIn("当前 Companion 进程", [item["label"] for item in subjects])
            self.assertIn("Python 可执行文件", [item["label"] for item in subjects])
            self.assertTrue(any(str(item.get("path") or "").endswith("python3") or "Python" in str(item.get("path") or "") for item in subjects))
            self.assertTrue(any(item.get("pid") == companion.os.getpid() for item in subjects))
            first_next_step = result["reply"].split("下一步：", 1)[1]
            self.assertIn("Full Disk Access", first_next_step)

    def test_generation_action_records_finished_run_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_chat(payload: dict[str, Any]) -> dict[str, Any]:
                status = companion.active_run_status()
                self.assertTrue(status["active"])
                self.assertEqual(status["action"], "chat")
                self.assertEqual(status["stage"], "正在执行")
                return {"ok": True, "message": "done", "reply": "hello"}

            companion.chat = fake_chat

            result = companion.handle_action(
                {
                    "action": "chat",
                    "prompt": "hi",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "marginnote4-web-panel",
                }
            )

            self.assertTrue(result["ok"])
            run = companion.active_run_status()
            self.assertFalse(run["active"])
            self.assertEqual(run["action"], "chat")
            self.assertEqual(run["stage"], "已完成")
            self.assertEqual(run["detail"], "done")
            self.assertEqual(run["topicid"], "T1")
            self.assertEqual(run["bookmd5"], "B1")

    def test_draft_summary_exposes_write_target_for_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "expand_node",
                    "draft": {
                        "ok": True,
                        "message": "ready",
                        "reply": "preview text",
                        "mindmap": {"title": "展开当前节点：Safety Gate", "mergeIntoSelected": True, "children": []},
                        "writeTarget": {
                            "mode": "merge_children_into_selected_node",
                            "label": "当前选中节点：Safety Gate",
                            "selectedNoteTitle": "Safety Gate",
                        },
                    },
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(saved["ok"])
            self.assertEqual(saved["draft"]["write_target"], "当前选中节点：Safety Gate")
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["draft"]["write_target"], "当前选中节点：Safety Gate")

    def test_highlight_diagnosis_includes_latest_native_api_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            db_path = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    "create table ZBOOKNOTE (ZBOOKMD5 text, ZTOPICID text, ZHIGHLIGHTS blob, ZAUTHOR text)"
                )
                conn.execute(
                    "insert into ZBOOKNOTE (ZBOOKMD5, ZTOPICID, ZHIGHLIGHTS, ZAUTHOR) values (?, ?, null, '')",
                    ("B1", "T1"),
                )
                conn.commit()
            finally:
                conn.close()
            companion.DB_PATH = db_path
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "pluginVersion": "0.4.11",
                    "extra": {
                        "hasNativeHighlightCandidate": True,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": ["studyController.AppendHighlight"],
                    },
                }
            )

            result = companion.diagnose_highlights({"topicid": "T1", "bookmd5": "B1"})

            self.assertTrue(result["ok"])
            self.assertEqual(result["nativeApiCapabilities"]["candidateMethods"], ["studyController.AppendHighlight"])
            self.assertIn("MN4 原生 API 探测", result["reply"])
            self.assertIn("studyController.AppendHighlight", result["reply"])

    def test_highlight_permission_error_still_reports_native_api_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            db_path = Path(tmp) / "MarginNotes.sqlite"
            db_path.write_text("", encoding="utf-8")
            companion.DB_PATH = db_path
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "pluginVersion": "0.4.11",
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": True,
                        "candidateMethods": ["studyController.ExportHighlightedPages"],
                    },
                }
            )
            old_connect = companion.sqlite3.connect

            def denied_connect(*args: Any, **kwargs: Any) -> Any:
                raise PermissionError("authorization denied")

            companion.sqlite3.connect = denied_connect
            try:
                result = companion.diagnose_highlights({"topicid": "T1", "bookmd5": "B1"})
            finally:
                companion.sqlite3.connect = old_connect

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "PERMISSION")
            self.assertEqual(result["nativeApiCapabilities"]["candidateMethods"], ["studyController.ExportHighlightedPages"])
            self.assertIn("MN4 原生 API 探测", result["reply"])

    def test_native_api_capability_matrix_marks_selection_highlight_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "pluginVersion": "0.4.11",
                    "extra": {
                        "activeSelectionLength": 26,
                        "candidateMethods": ["selectionDocumentController.highlightFromSelection"],
                        "targets": [
                            {
                                "label": "selectionDocumentController",
                                "exists": True,
                                "highlightMethods": ["selectionDocumentController.highlightFromSelection"],
                                "exportMethods": [],
                            }
                        ],
                    },
                }
            )

            caps = companion.latest_native_api_capabilities("T1", "B1")

            matrix = caps["capabilityMatrix"]
            self.assertTrue(matrix["nativeHighlightSelection"]["available"])
            self.assertTrue(matrix["nativeHighlightSelection"]["ready"])
            self.assertEqual(matrix["nativeHighlightSelection"]["nativeAction"], "highlight_current_selection")
            self.assertEqual(matrix["nativeHighlightSelection"]["entryAction"], "request_native_highlight_selection")
            self.assertIn("selectionDocumentController.highlightFromSelection", matrix["nativeHighlightSelection"]["evidence"])

    def test_native_api_capability_matrix_explains_missing_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "pluginVersion": "0.4.11",
                    "extra": {
                        "activeSelectionLength": 0,
                        "candidateMethods": ["documentController.highlightFromSelection"],
                        "targets": [
                            {
                                "label": "documentController",
                                "exists": True,
                                "highlightMethods": ["documentController.highlightFromSelection"],
                                "exportMethods": [],
                            }
                        ],
                    },
                }
            )

            caps = companion.latest_native_api_capabilities("T1", "B1")

            highlight = caps["capabilityMatrix"]["nativeHighlightSelection"]
            self.assertTrue(highlight["available"])
            self.assertFalse(highlight["ready"])
            self.assertEqual(highlight["blockedReason"], "missing-active-pdf-selection")
            self.assertIn("先在 PDF 里选中文本", highlight["nextStep"])

    def test_native_api_capability_matrix_allows_unverified_document_controller_highlight_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "pluginVersion": "0.4.11",
                    "extra": {
                        "activeSelectionLength": 18,
                        "candidateMethods": [],
                        "targets": [
                            {
                                "label": "studyController.readerController",
                                "exists": True,
                                "highlightMethods": [],
                                "exportMethods": [],
                            }
                        ],
                    },
                }
            )

            caps = companion.latest_native_api_capabilities("T1", "B1")

            self.assertTrue(caps["hasNativeHighlightCandidate"])
            highlight = caps["capabilityMatrix"]["nativeHighlightSelection"]
            self.assertTrue(highlight["available"])
            self.assertTrue(highlight["ready"])
            self.assertIn("unverified-highlightFromSelection-call", highlight["evidence"])
            self.assertIn("尝试官方", highlight["nextStep"])

    def test_native_api_reply_block_lists_ready_and_blocked_mn_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            caps = {
                "available": True,
                "event_ts": "2026-06-11T03:00:00+0800",
                "candidateMethods": ["selectionDocumentController.highlightFromSelection"],
                "hasNativeHighlightCandidate": True,
                "hasAnnotatedExportCandidate": False,
                "capabilityMatrix": {
                    "nativeHighlightSelection": {
                        "label": "原生高亮当前 PDF 选区",
                        "ready": True,
                        "available": True,
                        "entryAction": "request_native_highlight_selection",
                        "nextStep": "点击高亮选区。",
                    },
                    "annotatedPdfExport": {
                        "label": "导出带标注 PDF 副本",
                        "ready": False,
                        "available": True,
                        "entryAction": "export_annotated_pdf",
                        "blockedReason": "needs-pdf-cache-or-path",
                        "nextStep": "先缓存 PDF。",
                    },
                },
            }

            reply = companion.native_api_capabilities_reply_block(caps)

            self.assertIn("MN 原生动作矩阵", reply)
            self.assertIn("可执行：原生高亮当前 PDF 选区", reply)
            self.assertIn("受阻：导出带标注 PDF 副本", reply)
            self.assertIn("request_native_highlight_selection", reply)

    def test_selected_context_does_not_inject_paper_specific_background_from_book_md5(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            context = companion.selected_context(
                {
                    "prompt": "解释当前材料",
                    "bookmd5": "253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246",
                }
            )

            self.assertIn("解释当前材料", context)
            self.assertNotIn("当前论文上下文", context)
            self.assertNotIn("Park et al.", context)
            self.assertNotIn("KNOWS", context)

    def test_legacy_database_highlight_repair_action_is_not_executable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action({"action": "repair_knows_highlights", "topicid": "T1", "bookmd5": "B1"})

            self.assertFalse(result["ok"])
            self.assertIn("不再支持", result["message"])
            self.assertNotIn("Park", result["message"])
            self.assertNotIn("KNOWS", result["message"])

    def test_full_reading_uses_model_output_not_builtin_knows_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return (
                    "## 主线\n模型生成的完整精读主线。\n\n"
                    "## 方法\n模型生成的注意力和安全过滤器解释。\n\n"
                    "## Defense\n模型生成的答辩讲稿。"
                ), "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_full_reading(
                {"prompt": "KNOWS full reading", "bookmd5": "generic-book"}
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_full_reading"])
            self.assertEqual(result["backend"], "codex-cli")
            self.assertIn("cards", result)
            self.assertGreaterEqual(len(result["cards"]), 3)
            self.assertEqual(result["cardFactory"]["schema"], "codex.mn.cardFactory.v1")
            self.assertEqual(result["cardFactory"]["cardCount"], len(result["cards"]))
            self.assertEqual(result["cardQuality"]["schema"], "codex.mn.cardQuality.v1")
            self.assertTrue(all(card.get("cardType") for card in result["cards"]))
            self.assertTrue(all(card.get("reviewPrompt") for card in result["cards"]))
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["主线", "方法", "Defense"])
            self.assertNotEqual(result["mindmap"]["title"], "Codex Companion：KNOWS 完整精读")
            self.assertNotIn("local:park-knows-template", result["backend"])

    def test_full_reading_requires_real_ai_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings({"aiBackend": "local"})

            result = companion.generate_full_reading({"prompt": "完整精读", "bookmd5": "generic-book"})

            self.assertFalse(result["ok"])
            self.assertEqual(result["backend"], "ai-unavailable")
            self.assertNotIn("cards", result)
            self.assertNotIn("mindmap", result)
            self.assertIn("真实 AI", result["reply"])

    def test_park_mindmap_uses_model_instead_of_builtin_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 注意力证据\nFigure 2 用来证明目标定位信号。\n\n## 安全层\nCBF-QP 修正 VLA 动作。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap(
                {"prompt": "KNOWS 论文脑图", "bookmd5": "generic-book"}
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_mindmap"])
            self.assertEqual(result["backend"], "codex-cli")
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["注意力证据", "安全层"])
            self.assertNotIn("local:park-knows-mindmap-template", result["backend"])
            self.assertNotIn("快速脑图", result["reply"])

    def test_generate_mindmap_prompt_requests_complete_multi_level_outline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_document_context(payload: dict[str, Any], query: str, max_chars: int = 7000) -> dict[str, Any]:
                return {"ok": True, "text": "全文读取片段：Section 1, Section 2, Section 3"}

            old = companion.document_context_for_model
            companion.document_context_for_model = fake_document_context
            try:
                prompt = companion.build_model_input(
                    {
                        "contextScope": "document",
                        "prompt": "生成完整脑图",
                        "bookmd5": "generic-book",
                    },
                    "generate_mindmap",
                )
            finally:
                companion.document_context_for_model = old

            for marker in [
                "覆盖全文章节",
                "Markdown 层级",
                "`##`",
                "`###`",
                "`####`",
                "二级主题",
                "三级细节点",
                "覆盖统计",
            ]:
                self.assertIn(marker, prompt)

    def test_model_mindmap_reply_preserves_markdown_heading_hierarchy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return (
                    "## 1 引言\n总述问题。\n"
                    "### 研究背景\n说明背景。\n"
                    "#### 安全失败模式\n列出细节。\n"
                    "### 核心贡献\n说明贡献。\n"
                    "## 2 方法\n总述方法。\n"
                    "### 注意力证据\n解释证据。\n",
                    "codex-cli",
                )

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap({"prompt": "生成完整脑图", "bookmd5": "generic-book"})

            self.assertTrue(result["ok"])
            children = result["mindmap"]["children"]
            self.assertEqual([child["title"] for child in children], ["引言", "方法"])
            self.assertEqual([child["title"] for child in children[0]["children"]], ["研究背景", "核心贡献"])
            self.assertEqual(children[0]["children"][0]["children"][0]["title"], "安全失败模式")
            self.assertGreaterEqual(result["mindmapStats"]["nodeCount"], 6)
            self.assertGreaterEqual(result["mindmapStats"]["maxDepth"], 3)
            self.assertIn("节点", result["message"])

    def test_mindmap_target_status_suggests_document_root_for_current_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action(
                {
                    "action": "mindmap_target_status",
                    "topicid": "topic-1",
                    "bookmd5": "book-abc",
                    "documentTitle": "Ding 等 2025. Fast and Robust Visuomotor Riemannian Flow Matching Policy.pdf",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["mindmapTarget"]["state"], "suggested")
            self.assertEqual(result["mindmapTarget"]["target"]["mode"], "document_root")
            self.assertEqual(
                result["mindmapTarget"]["target"]["rootTitle"],
                "Ding 等 2025. Fast and Robust Visuomotor Riemannian Flow Matching Policy · Codex 脑图",
            )
            self.assertRegex(result["mindmapTarget"]["target"]["codexId"], r"^mindmap-target:[a-f0-9]{16}$")
            self.assertIn("document_root", [item["value"] for item in result["mindmapTarget"]["options"]])

    def test_mindmap_target_update_persists_document_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            payload = {
                "action": "mindmap_target_update",
                "targetMode": "document_root",
                "topicid": "topic-1",
                "bookmd5": "book-abc",
                "documentTitle": "Paper.pdf",
            }

            updated = companion.handle_action(payload)
            status = companion.handle_action({**payload, "action": "mindmap_target_status"})

            self.assertTrue(updated["ok"])
            self.assertEqual(updated["mindmapTarget"]["state"], "confirmed")
            self.assertEqual(status["mindmapTarget"]["state"], "confirmed")
            self.assertEqual(status["mindmapTarget"]["target"]["rootTitle"], "Paper · Codex 脑图")

    def test_generate_mindmap_uses_bound_document_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return "## 方法\n解释方法。\n### 结构\n细节。", "codex-cli"

            companion.generate_reply = fake_generate_reply
            companion.handle_action(
                {
                    "action": "mindmap_target_update",
                    "targetMode": "document_root",
                    "topicid": "topic-1",
                    "bookmd5": "book-abc",
                    "documentTitle": "Paper.pdf",
                }
            )

            result = companion.generate_mindmap(
                {
                    "prompt": "生成脑图",
                    "topicid": "topic-1",
                    "bookmd5": "book-abc",
                    "documentTitle": "Paper.pdf",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["mindmap"]["title"], "Paper · Codex 脑图")
            self.assertEqual(result["writeTarget"]["mode"], "document_root")
            self.assertEqual(result["writeTarget"]["rootTitle"], "Paper · Codex 脑图")
            self.assertEqual(result["mindmap"]["writeTarget"]["mode"], "document_root")
            self.assertEqual(result["mindmap"]["codexId"], result["writeTarget"]["codexId"])
            self.assertEqual(result["mnObject"]["schema"], "codex.mn.mnObject.v1")
            self.assertEqual(result["mnObject"]["kind"], "document")
            self.assertEqual(result["mnObject"]["identifiers"]["bookmd5"], "book-abc")

    def test_generate_mindmap_uses_selected_target_from_top_selector_without_append_words(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return "## 新分支\n补充回答里的结构。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap(
                {
                    "prompt": "[create_card_tree] 根据上面的回答创建结构化脑图树",
                    "bookmd5": "book-abc",
                    "selectedNoteId": "note-7",
                    "selectedNoteTitle": "已有脑图根",
                    "mindmapTarget": {
                        "mode": "merge_children_into_selected_node",
                        "selectedNoteId": "note-7",
                        "selectedNoteTitle": "已有脑图根",
                        "label": "当前选中节点：已有脑图根",
                    },
                }
            )

            self.assertTrue(result["ok"])
            self.assertTrue(result["mindmap"]["mergeIntoSelected"])
            self.assertEqual(result["writeTarget"]["mode"], "merge_children_into_selected_node")
            self.assertEqual(result["writeTarget"]["selectedNoteId"], "note-7")
            self.assertEqual(result["mindmap"]["writeTarget"]["selectedNoteTitle"], "已有脑图根")

    def test_generated_cards_and_mindmaps_return_mn_object_for_draft_transactions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                if task == "generate_card":
                    return "## 核心概念\n解释。", "codex-cli"
                return "## 根节点\n说明。\n### 子节点\n细节。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            card = companion.generate_card(
                {
                    "prompt": "把选区制卡",
                    "selectionText": "selected evidence",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "documentTitle": "Paper.pdf",
                    "pageNumber": 6,
                }
            )
            mindmap = companion.generate_mindmap(
                {
                    "prompt": "生成脑图",
                    "selectedNoteId": "N-root",
                    "selectedNoteTitle": "当前根节点",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(card["ok"], card)
            self.assertEqual(card["mnObject"]["kind"], "selection")
            self.assertEqual(card["mnObject"]["sourceRef"]["quote"], "selected evidence")
            self.assertTrue(mindmap["ok"], mindmap)
            self.assertEqual(mindmap["mnObject"]["kind"], "note")
            self.assertEqual(mindmap["mnObject"]["identifiers"]["noteId"], "N-root")

    def test_park_append_mindmap_request_uses_model_not_knows_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 新增概念\n补充 patch mask 和 Figure 2。\n\n## Defense 补充\n说明它不是完整安全证明。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap(
                {
                    "prompt": "把下面这些内容补到现在脑图里：patch mask、Figure 2、defense 边界。",
                    "bookmd5": "generic-book",
                    "selectedNoteTitle": "KNOWS 当前脑图",
                    "selectedNoteId": "note-1",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_mindmap"])
            self.assertEqual(result["backend"], "codex-cli")
            self.assertIn("追加", result["message"])
            self.assertIn("补充到当前脑图", result["mindmap"]["title"])
            self.assertTrue(result["mindmap"]["mergeIntoSelected"])
            self.assertEqual(result["writeTarget"]["mode"], "merge_children_into_selected_node")
            self.assertEqual(result["writeTarget"]["operation"], "append_to_current_mindmap")
            self.assertEqual(result["writeTarget"]["selectedNoteTitle"], "KNOWS 当前脑图")
            self.assertEqual(result["mindmap"]["writeTarget"]["selectedNoteTitle"], "KNOWS 当前脑图")
            self.assertNotIn("KNOWS 论文讲解", result["mindmap"]["title"])
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["新增概念", "Defense 补充"])

            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "originalAction": "generate_mindmap",
                    "draft": result,
                    "topicid": "T1",
                    "bookmd5": "generic-book",
                }
            )
            self.assertEqual(saved["draft"]["write_target"], "当前选中节点：KNOWS 当前脑图")

    def test_append_mindmap_request_requires_selected_node_context(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 不应生成\n没有选中节点时不能写入当前脑图。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap(
                {
                    "prompt": "把这些内容补到现在脑图里：Figure 2 和 mask。",
                    "bookmd5": "generic-book",
                }
            )

            self.assertFalse(result["ok"])
            self.assertEqual(calls, [])
            self.assertIn("选中一个脑图节点", result["message"])
            self.assertNotIn("mindmap", result)

    def test_expand_node_generates_children_merged_into_selected_node(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 约束来源\n解释安全约束从哪里来。\n\n## 失败边界\n说明什么时候不能保证。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.handle_action(
                {
                    "action": "expand_node",
                    "prompt": "展开这个节点",
                    "bookmd5": "generic-book",
                    "selectedNoteId": "note-1",
                    "selectedNoteTitle": "Safety Gate",
                    "selectedNoteText": "CBF-QP filters risky VLA actions.",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["expand_node"])
            self.assertIn("展开当前节点", result["message"])
            self.assertTrue(result["mindmap"]["mergeIntoSelected"])
            self.assertIn("Safety Gate", result["mindmap"]["title"])
            self.assertEqual(result["writeTarget"]["mode"], "merge_children_into_selected_node")
            self.assertEqual(result["writeTarget"]["selectedNoteTitle"], "Safety Gate")
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["约束来源", "失败边界"])

    def test_reorganize_mindmap_is_non_destructive_merge_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 概念层\n把定义、符号、坐标系统一。\n\n## 证据层\n把 Figure 2、mask、高亮证据放在一起。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.handle_action(
                {
                    "action": "reorganize_mindmap",
                    "prompt": "重组当前脑图",
                    "bookmd5": "generic-book",
                    "selectedNoteId": "note-2",
                    "selectedNoteTitle": "论文精读脑图",
                    "selectedNoteText": "patch mask / Figure 2 / defense notes",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["reorganize_mindmap"])
            self.assertIn("重组当前脑图", result["message"])
            self.assertTrue(result["mindmap"]["mergeIntoSelected"])
            self.assertFalse(result["mindmap"].get("replaceChildren", False))
            self.assertEqual(result["writeTarget"]["mode"], "merge_children_into_selected_node")
            self.assertEqual(result["writeTarget"]["operation"], "non_destructive_reorganization_preview")
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["概念层", "证据层"])

    def test_plain_merge_mindmap_prompt_is_append_intent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            self.assertTrue(companion.is_mindmap_append_request({"prompt": "合并脑图，把这些新笔记加进去"}))
            self.assertTrue(companion.is_mindmap_append_request({"prompt": "merge mindmap with the current notes"}))

    def test_model_mindmap_reply_drives_tree_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "## 速度问题\n发送按钮慢是因为走模型。\n\n## 队列策略\n后续动作应等待当前任务结束。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap({"prompt": "解释插件发送按钮和队列问题", "bookmd5": "generic-book"})

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_mindmap"])
            self.assertEqual(result["backend"], "codex-cli")
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["速度问题", "队列策略"])
            self.assertNotEqual([child["title"] for child in result["mindmap"]["children"]], ["问题", "方法", "实验", "Defense"])

    def test_mindmap_local_backend_does_not_return_builtin_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings({"aiBackend": "local"})

            result = companion.generate_mindmap({"prompt": "生成脑图", "bookmd5": "generic-book"})

            self.assertFalse(result["ok"])
            self.assertEqual(result["backend"], "ai-unavailable")
            self.assertNotIn("mindmap", result)
            self.assertIn("内置模板已关闭", result["message"])

    def test_local_backend_does_not_generate_chat_from_builtin_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings({"aiBackend": "local"})

            text, backend = companion.generate_reply({"prompt": "Figure 2 做什么"}, "chat")

            self.assertEqual(backend, "ai-unavailable")
            self.assertIn("真实 AI 后端不可用", text)
            self.assertIn("Codex CLI", text)
            self.assertNotIn("Figure 2 的作用", text)

    def test_card_generation_requires_real_ai_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings({"aiBackend": "local"})

            result = companion.generate_card({"prompt": "请生成卡片", "bookmd5": "generic"})

            self.assertFalse(result["ok"])
            self.assertEqual(result["backend"], "ai-unavailable")
            self.assertNotIn("cards", result)
            self.assertIn("真实 AI", result["reply"])

    def test_generic_fast_mindmap_still_uses_model_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings({"speed": "fast", "aiBackend": "codex_cli"})
            calls: list[str] = []

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                calls.append(task)
                return "模型生成的脑图内容：问题、方法、实验、Defense。", "codex-cli"

            companion.generate_reply = fake_generate_reply

            result = companion.generate_mindmap({"prompt": "自定义材料：方法、实验、局限", "bookmd5": "generic-book"})

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_mindmap"])
            self.assertEqual(result["backend"], "codex-cli")
            self.assertIn("模型生成", result["reply"])
            self.assertEqual([child["title"] for child in result["mindmap"]["children"]], ["问题", "方法", "实验", "Defense"])

    def test_generate_card_splits_model_sections_into_short_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return (
                    "## 概念定位\n" + "这部分解释概念。\n" * 8 +
                    "\n## 公式拆解\n" + "这部分拆公式。\n" * 8 +
                    "\n## Defense 说法\n" + "这部分用于答辩。\n" * 8,
                    "codex-cli",
                )

            companion.generate_reply = fake_generate_reply
            result = companion.generate_card(
                {
                    "prompt": "请根据这段内容生成卡片。" + "原文很长。" * 180,
                    "bookmd5": "generic-book",
                    "topicid": "T1",
                }
            )

            self.assertTrue(result["ok"])
            self.assertGreaterEqual(len(result["cards"]), 3)
            self.assertLessEqual(max(len(card["body"]) for card in result["cards"]), companion.CARD_BODY_MAX_CHARS)
            self.assertTrue(all("## 原文/问题" not in card["body"] for card in result["cards"]))
            self.assertIn("短卡片", result["message"])

    def test_generate_card_splits_single_long_model_reply_into_multiple_compact_cards(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return (
                    "这是一段没有标题的长回复。"
                    "第一句解释概念定位。第二句拆开公式符号。第三句说明实验现象。"
                    "第四句指出局限和失败边界。第五句给出 defense 说法。"
                    "第六句补充和原文的连接。第七句提醒不要误读。第八句总结可操作动作。"
                    * 4,
                    "codex-cli",
                )

            companion.generate_reply = fake_generate_reply
            result = companion.generate_card(
                {
                    "prompt": "把这段内容做成短卡。" + "上下文。" * 80,
                    "bookmd5": "generic-book",
                    "topicid": "T1",
                }
            )

            self.assertTrue(result["ok"])
            self.assertGreaterEqual(len(result["cards"]), 3)
            self.assertLessEqual(companion.CARD_BODY_MAX_CHARS, 900)
            self.assertLessEqual(max(len(card["body"]) for card in result["cards"]), companion.CARD_BODY_MAX_CHARS)

    def test_generate_card_titles_strip_markdown_emphasis(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return "1. **目标**：解释目标。\n2. `方法`：解释方法。", "codex-cli"

            companion.generate_reply = fake_generate_reply
            result = companion.generate_card({"prompt": "生成短卡", "bookmd5": "generic-book"})

            self.assertTrue(result["ok"])
            self.assertEqual(result["cards"][0]["title"], "Codex短卡 01：目标")
            self.assertEqual(result["cards"][1]["title"], "Codex短卡 02：方法")

    def test_generate_card_returns_typed_card_factory_objects_with_sources_and_review_prompts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return (
                    "## 概念定位\n"
                    "解释 attention-guided safety filter 的核心概念。\n\n"
                    "## 公式拆解\n"
                    "说明 M_i mask 和 patch score 的计算关系。\n\n"
                    "## 实验证据\n"
                    "第 6 页显示真实机器人任务中失败动作被过滤。",
                    "codex-cli",
                )

            companion.generate_reply = fake_generate_reply

            result = companion.generate_card(
                {
                    "prompt": "把选区做成复习卡片",
                    "selectionText": "attention-guided safety filter uses image masks to reject risky actions",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "documentTitle": "Park et al. 2026.pdf",
                    "pageNumber": 6,
                    "selectedNoteId": "note-source",
                    "selectedNoteTitle": "Safety Filter",
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["cardFactory"]["schema"], "codex.mn.cardFactory.v1")
            self.assertEqual(result["cardFactory"]["cardCount"], len(result["cards"]))
            self.assertEqual(result["cardFactory"]["sourceRef"]["page"], 6)
            self.assertEqual(result["cardFactory"]["sourceRef"]["noteId"], "note-source")
            self.assertEqual(result["cardQuality"]["schema"], "codex.mn.cardQuality.v1")
            self.assertEqual(result["cardQuality"]["missingSourceCount"], 0)

            card_types = {card["cardType"] for card in result["cards"]}
            self.assertIn("concept", card_types)
            self.assertIn("formula", card_types)
            self.assertIn("evidence", card_types)
            for card in result["cards"]:
                self.assertEqual(card["source"]["page"], 6)
                self.assertEqual(card["source"]["noteId"], "note-source")
                self.assertIn("quote", card["source"])
                self.assertTrue(card["reviewPrompt"])
                self.assertTrue(card["learningGoal"])
                self.assertEqual(card["factory"]["schema"], "codex.mn.cardFactoryCard.v1")

            saved = companion.save_draft(
                {
                    "originalAction": "generate_card",
                    "draft": result,
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )
            self.assertEqual(saved["draft"]["card_factory"]["schema"], "codex.mn.cardFactory.v1")
            self.assertEqual(saved["draft"]["card_factory"]["cardCount"], len(result["cards"]))
            self.assertEqual(saved["draft"]["card_factory"]["sourceRef"]["noteId"], "note-source")

    def test_review_queue_adds_card_factory_draft_cards_once_and_lists_object_scoped_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_generate_reply(payload: dict[str, Any], task: str) -> tuple[str, str]:
                return (
                    "## 概念卡\n解释核心概念。\n\n"
                    "## 公式卡\n拆解 M_i mask 公式。\n\n"
                    "## 证据卡\n第 6 页实验结果支持该结论。",
                    "codex-cli",
                )

            companion.generate_reply = fake_generate_reply
            result = companion.generate_card(
                {
                    "prompt": "加入复习",
                    "selectionText": "attention mask evidence",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "selectedNoteId": "note-source",
                    "selectedNoteTitle": "Safety Filter",
                    "pageNumber": 6,
                }
            )
            saved = companion.save_draft(
                {
                    "originalAction": "generate_card",
                    "draft": result,
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            added = companion.handle_action(
                {
                    "action": "review_queue_add",
                    "draftId": saved["draft"]["id"],
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mnObject": result["mnObject"],
                }
            )
            duplicate = companion.handle_action(
                {
                    "action": "review_queue_add",
                    "draftId": saved["draft"]["id"],
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mnObject": result["mnObject"],
                }
            )
            listed = companion.handle_action(
                {
                    "action": "review_queue_list",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mnObject": result["mnObject"],
                }
            )

            self.assertTrue(added["ok"], added)
            self.assertEqual(added["reviewQueue"]["schema"], "codex.mn.reviewQueue.v1")
            self.assertEqual(added["addedCount"], len(result["cards"]))
            self.assertEqual(duplicate["addedCount"], 0)
            self.assertEqual(duplicate["duplicateCount"], len(result["cards"]))
            self.assertEqual(listed["reviewQueue"]["schema"], "codex.mn.reviewQueue.v1")
            self.assertEqual(listed["summary"]["totalCount"], len(result["cards"]))
            self.assertEqual(listed["summary"]["dueCount"], len(result["cards"]))
            self.assertEqual({item["cardType"] for item in listed["items"]}, {card["cardType"] for card in result["cards"]})
            for item in listed["items"]:
                self.assertEqual(item["mnObjectId"], result["mnObject"]["objectId"])
                self.assertEqual(item["source"]["noteId"], "note-source")
                self.assertTrue(item["reviewPrompt"])
                self.assertEqual(item["state"], "new")

    def test_goal_run_returns_executable_goal_queue_from_goal_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            def fake_chat(payload: dict[str, Any]) -> dict[str, Any]:
                return {"ok": True, "message": "fake", "reply": "目标理解完成。", "backend": "test"}

            companion.chat = fake_chat

            result = companion.run_goal(
                {
                    "goal": {
                        "title": "精读当前材料",
                        "detail": "生成 defense 讲稿、短卡片、脑图，并检查高亮。",
                    },
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "selectedNoteTitle": "当前章节",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(
                [item["action"] for item in result["goalQueue"]],
                ["generate_full_reading", "generate_card", "generate_mindmap", "diagnose_highlights"],
            )
            self.assertTrue(all(item["prompt"] for item in result["goalQueue"]))
            self.assertIn("自动拆分", result["reply"])
            self.assertIn("当前章节", result["goalQueue"][0]["prompt"])

    def test_codex_cli_fast_mode_uses_gpt55_medium_fast_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings(
                {
                    "speed": "fast",
                    "aiBackend": "codex_cli",
                    "codexCliPath": "/tmp/codex",
                    "model": "gpt-5.5",
                    "proxyUrl": "http://127.0.0.1:7890",
                }
            )
            fake_home = Path(tmp) / "home"
            fake_home.joinpath(".codex").mkdir(parents=True)
            fake_home.joinpath(".codex/auth.json").write_text('{"token":"test"}', encoding="utf-8")
            companion.HOME = fake_home
            companion.codex_cli_status = lambda settings: {"available": True, "path": "/tmp/codex"}
            captured: dict[str, Any] = {}

            class FakePopen:
                pid = 4321
                returncode = 0

                def __init__(self, args: list[str], **kwargs: Any) -> None:
                    captured["args"] = args
                    captured["env"] = kwargs.get("env")
                    output_path = Path(args[args.index("--output-last-message") + 1])
                    output_path.write_text("fast cli output", encoding="utf-8")

                def communicate(self, input: str = "", timeout: float | None = None) -> tuple[str, str]:
                    captured["timeout"] = timeout
                    captured["input"] = input
                    return "", ""

                def poll(self) -> int:
                    return self.returncode

            def fake_popen(args: list[str], **kwargs: Any) -> FakePopen:
                captured["args"] = args
                captured["env"] = kwargs.get("env")
                return FakePopen(args, **kwargs)

            old_popen = companion.subprocess.Popen
            companion.subprocess.Popen = fake_popen
            try:
                text, backend = companion.call_codex_cli({"prompt": "生成脑图"}, "generate_mindmap")
            finally:
                companion.subprocess.Popen = old_popen

            self.assertEqual(text, "fast cli output")
            self.assertEqual(backend, "codex-cli")
            self.assertEqual(captured["timeout"], 75)
            self.assertEqual(captured["input"], "")
            self.assertIn("model_reasoning_effort=medium", captured["args"])
            self.assertNotIn("--enable", captured["args"])
            self.assertNotIn("--disable", captured["args"])
            self.assertNotIn("--ephemeral", captured["args"])
            self.assertNotIn("--ignore-rules", captured["args"])
            self.assertIn("--sandbox", captured["args"])
            self.assertIn("read-only", captured["args"])
            self.assertIn("-m", captured["args"])
            self.assertIn("gpt-5.5", captured["args"])
            self.assertEqual(captured["env"]["CODEX_HOME"], str(companion.CODEX_LITE_HOME))
            self.assertEqual(captured["env"]["HOME"], str(companion.CODEX_LITE_HOME))
            self.assertEqual(captured["env"]["HTTP_PROXY"], "http://127.0.0.1:7890")
            self.assertEqual(captured["env"]["HTTPS_PROXY"], "http://127.0.0.1:7890")
            self.assertEqual(captured["env"]["ALL_PROXY"], "http://127.0.0.1:7890")
            self.assertEqual(captured["env"]["http_proxy"], "http://127.0.0.1:7890")
            self.assertIn("127.0.0.1", captured["env"]["NO_PROXY"])
            self.assertIn("localhost", captured["env"]["NO_PROXY"])
            self.assertTrue((companion.CODEX_LITE_HOME / "auth.json").exists())

    def test_codex_cli_retries_transient_cloud_config_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings(
                {
                    "speed": "fast",
                    "aiBackend": "codex_cli",
                    "codexCliPath": "/tmp/codex",
                    "model": "gpt-5.5",
                    "proxyUrl": "http://127.0.0.1:1082",
                }
            )
            companion.codex_cli_status = lambda settings: {"available": True, "path": "/tmp/codex"}
            calls: list[list[str]] = []
            codex_invocations: list[list[str]] = []

            class FakePopen:
                pid = 4321

                def __init__(self, args: list[str], **kwargs: Any) -> None:
                    calls.append(args)
                    if args and args[0] == "/tmp/codex":
                        codex_invocations.append(args)
                    self.returncode = 1 if args and args[0] == "/tmp/codex" and len(codex_invocations) == 1 else 0
                    if self.returncode == 0:
                        if "--output-last-message" in args:
                            output_path = Path(args[args.index("--output-last-message") + 1])
                            output_path.write_text("retry ok", encoding="utf-8")

                def communicate(self, input: str = "", timeout: float | None = None) -> tuple[str, str]:
                    if self.returncode != 0:
                        return "", "Error: timed out waiting for cloud config bundle after 15s"
                    return "", ""

                def poll(self) -> int:
                    return self.returncode

            old_popen = companion.subprocess.Popen
            companion.subprocess.Popen = lambda args, **kwargs: FakePopen(args, **kwargs)
            try:
                text, backend = companion.call_codex_cli({"prompt": "ping"}, "chat")
            finally:
                companion.subprocess.Popen = old_popen

            self.assertEqual(text, "retry ok")
            self.assertEqual(backend, "codex-cli")
            self.assertEqual(len(codex_invocations), 2)

    def test_codex_cli_cloud_config_timeout_message_is_actionable_after_retry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.save_runtime_settings(
                {
                    "speed": "fast",
                    "aiBackend": "codex_cli",
                    "codexCliPath": "/tmp/codex",
                    "model": "gpt-5.5",
                    "proxyUrl": "http://127.0.0.1:1082",
                }
            )
            companion.codex_cli_status = lambda settings: {"available": True, "path": "/tmp/codex"}

            class FakePopen:
                pid = 4321
                returncode = 1

                def __init__(self, args: list[str], **kwargs: Any) -> None:
                    pass

                def communicate(self, input: str = "", timeout: float | None = None) -> tuple[str, str]:
                    return "", "Error: timed out waiting for cloud config bundle after 15s"

                def poll(self) -> int:
                    return self.returncode

            old_popen = companion.subprocess.Popen
            companion.subprocess.Popen = lambda args, **kwargs: FakePopen(args, **kwargs)
            try:
                text, backend = companion.call_codex_cli({"prompt": "ping"}, "chat")
            finally:
                companion.subprocess.Popen = old_popen

            self.assertEqual(backend, "codex-cli-error")
            self.assertIn("Codex CLI 网络/代理初始化超时", text or "")
            self.assertIn("已自动重试一次", text or "")
            self.assertIn("127.0.0.1:1082", text or "")

    def test_codex_cli_discovery_prefers_user_npm_cli_over_old_homebrew_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            fake_home = Path(tmp) / "home"
            npm_cli = fake_home / ".npm-global/bin/codex"
            npm_cli.parent.mkdir(parents=True)
            npm_cli.write_text("#!/bin/sh\n", encoding="utf-8")
            npm_cli.chmod(0o755)
            companion.HOME = fake_home

            path = companion.discover_codex_cli_path({"codexCliPath": ""})

            self.assertEqual(path, str(npm_cli))

    def test_stale_stop_signal_expires_without_blocking_next_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.write_json_file(
                companion.STOP_PATH,
                {
                    "requested": True,
                    "updated_at": "2026-01-01T00:00:00+0800",
                    "reason": "old stop from prior run",
                },
            )

            status = companion.stop_status()

            self.assertFalse(status["requested"])
            self.assertFalse(companion.STOP_PATH.exists())

    def test_custom_prompt_buttons_are_persisted_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            updated = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "customButtons": [
                            *[
                                {
                                    "title": f"常用按钮{i}",
                                    "action": "generate_full_reading" if i == 0 else "chat",
                                    "prompt": f"执行第 {i} 个常用 prompt，整理当前材料。",
                                    "showOnMain": True,
                                }
                                for i in range(8)
                            ],
                            {
                                "title": "坏按钮",
                                "action": "delete_everything",
                                "prompt": "bad",
                            },
                            {
                                "title": "高亮选区",
                                "action": "request_native_highlight_selection",
                                "prompt": "用 MarginNote 原生高亮标出当前 PDF 选区。",
                                "showOnMain": True,
                            },
                            {"title": "", "action": "chat", "prompt": "missing title"},
                        ]
                    },
                }
            )

            self.assertTrue(updated["ok"])
            self.assertEqual(len(updated["settings"]["customButtons"]), 9)
            button = updated["settings"]["customButtons"][0]
            self.assertEqual(button["title"], "常用按钮0")
            self.assertEqual(button["action"], "generate_full_reading")
            self.assertIn("整理当前材料", button["prompt"])
            self.assertTrue(button["showOnMain"])
            self.assertEqual(
                sum(1 for item in updated["settings"]["customButtons"] if item.get("showOnMain")),
                6,
            )
            self.assertEqual(updated["settings"]["customButtons"][8]["action"], "request_native_highlight_selection")
            self.assertIn("原生高亮", updated["settings"]["customButtons"][8]["prompt"])
            self.assertIn("自定义按钮：9", updated["reply"])
            settings = companion.handle_action({"action": "settings_get"})["settings"]
            self.assertEqual(settings["customButtons"], updated["settings"]["customButtons"])

    def test_default_context_scope_setting_is_persisted_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            updated = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "defaultContextScope": "全文",
                    },
                }
            )

            self.assertTrue(updated["ok"])
            self.assertEqual(updated["settings"]["defaultContextScope"], "document")
            self.assertIn("默认上下文：document", updated["reply"])

            invalid = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "defaultContextScope": "everything",
                    },
                }
            )
            self.assertEqual(invalid["settings"]["defaultContextScope"], "auto")

    def test_update_actions_use_github_repo_setting_and_expose_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"githubRepo": "https://github.com/LiuWhale/marginnote-assistant"},
                }
            )
            calls: list[str] = []

            def fake_check(root: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
                calls.append(settings["githubRepo"])
                return {
                    "ok": True,
                    "state": "available",
                    "available": True,
                    "repo": settings["githubRepo"],
                    "currentVersion": current_version,
                    "latestVersion": "0.4.11",
                    "assetName": "CodexCompanion-0.4.11-latest-dist.zip",
                    "downloadUrl": "https://example/CodexCompanion-0.4.11-latest-dist.zip",
                    "message": "发现新版本 0.4.11。",
                }

            def fake_install(root: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
                calls.append("install:" + settings["githubRepo"])
                return {
                    "ok": True,
                    "state": "installing",
                    "repo": settings["githubRepo"],
                    "currentVersion": current_version,
                    "latestVersion": "0.4.11",
                    "message": "已开始安装更新。",
                }

            old_check = companion.update_manager.check_for_update
            old_install = companion.update_manager.install_update
            companion.update_manager.check_for_update = fake_check
            companion.update_manager.install_update = fake_install
            try:
                checked = companion.handle_action({"action": "update_check"})
                installed = companion.handle_action({"action": "update_install"})
                status = companion.status_payload()
            finally:
                companion.update_manager.check_for_update = old_check
                companion.update_manager.install_update = old_install

            self.assertTrue(checked["ok"])
            self.assertTrue(checked["update"]["available"])
            self.assertEqual(installed["update"]["state"], "installing")
            self.assertEqual(calls, ["LiuWhale/marginnote-assistant", "install:LiuWhale/marginnote-assistant"])
            self.assertEqual(status["update"]["latestVersion"], "0.4.11")

    def test_open_url_action_opens_valid_http_url_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[list[str]] = []

            class FakeCompleted:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(args: list[str], **kwargs: Any) -> FakeCompleted:
                calls.append(args)
                return FakeCompleted()

            old_run = companion.subprocess.run
            companion.subprocess.run = fake_run
            try:
                invalid = companion.handle_action({"action": "open_url", "url": "file:///etc/passwd"})
                opened = companion.handle_action(
                    {
                        "action": "open_url",
                        "url": "https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.11",
                    }
                )
            finally:
                companion.subprocess.run = old_run

            self.assertFalse(invalid["ok"])
            self.assertIn("只允许打开 http/https", invalid["message"])
            self.assertTrue(opened["ok"])
            self.assertEqual(calls, [["/usr/bin/open", "https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.11"]])

    def test_settings_goal_upload_stop_and_permission_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            updated = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "permission": "read_only",
                        "model": "gpt-5.2",
                        "speed": "fast",
                        "proxyUrl": "http://127.0.0.1:7890",
                        "aiBackend": "codex_cli",
                    },
                }
            )
            self.assertTrue(updated["ok"])
            self.assertEqual(updated["settings"]["permission"], "read_only")
            self.assertEqual(updated["settings"]["speed"], "fast")
            self.assertEqual(updated["settings"]["proxyUrl"], "http://127.0.0.1:7890")
            self.assertEqual(updated["settings"]["aiBackend"], "codex_cli")
            self.assertIn("代理：已配置", updated["reply"])
            self.assertIn("AI 后端：Codex CLI", updated["reply"])

            status = companion.status_payload()
            self.assertEqual(status["ai_backend"], "codex_cli")
            self.assertIn("codex_cli_available", status)
            self.assertIn("codex_cli_path", status)
            self.assertTrue(status["proxy_configured"])
            self.assertEqual(status["proxy_scheme"], "http")

            blocked = companion.handle_action({"action": "generate_card", "prompt": "make a card"})
            self.assertFalse(blocked["ok"])
            self.assertIn("权限", blocked["message"])

            goal_result = companion.handle_action(
                {
                    "action": "goal_update",
                    "goal": {
                        "title": "读懂 KNOWS",
                        "detail": "生成 defense 讲稿和脑图",
                    },
                }
            )
            self.assertTrue(goal_result["ok"])
            self.assertEqual(goal_result["goal"]["title"], "读懂 KNOWS")

            upload_result = companion.handle_action(
                {
                    "action": "upload_file",
                    "fileName": "notes.md",
                    "fileContent": "# notes\n重点问题",
                }
            )
            self.assertTrue(upload_result["ok"])
            self.assertEqual(upload_result["file"]["name"], "notes.md")
            self.assertTrue(Path(upload_result["file"]["path"]).exists())

            stop_result = companion.handle_action({"action": "stop_current"})
            self.assertTrue(stop_result["ok"])
            self.assertTrue(stop_result["stop"]["requested"])

            stopped_generation = companion.handle_action({"action": "chat", "prompt": "should stop"})
            self.assertFalse(stopped_generation["ok"])
            self.assertTrue(stopped_generation["stopped"])

            queue_result = companion.handle_action({"action": "queue_status"})
            self.assertTrue(queue_result["ok"])
            self.assertIn("pending", queue_result["queue"])
            self.assertIn("当前队列待处理", queue_result["reply"])
            self.assertNotIn("排队引导", queue_result["reply"])
            self.assertFalse(queue_result["queue"]["stop"]["requested"])

            companion.append_history(
                {"topicid": "T1", "bookmd5": "B1", "source": "unittest"},
                "用户问题",
                "助手回答",
            )
            history_result = companion.handle_action(
                {"action": "history_list", "topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            )
            self.assertTrue(history_result["ok"])
            self.assertEqual(len(history_result["history"]), 2)
            self.assertEqual(history_result["history"][0]["role"], "user")

            clear_result = companion.handle_action(
                {"action": "history_clear", "topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            )
            self.assertTrue(clear_result["ok"])
            self.assertEqual(clear_result["removed"], 1)

            settings_result = companion.handle_action({"action": "settings_get"})
            self.assertTrue(settings_result["ok"])
            self.assertEqual(settings_result["settings"]["model"], "gpt-5.2")
            self.assertEqual(settings_result["settings"]["proxyUrl"], "http://127.0.0.1:7890")
            self.assertEqual(settings_result["settings"]["aiBackend"], "codex_cli")
            self.assertEqual(settings_result["goal"]["title"], "读懂 KNOWS")
            self.assertEqual(len(settings_result["files"]), 1)

    def test_margin_note_url_api_settings_status_and_request_preview_hide_secret(self) -> None:
        old_secret = os.environ.get("MN_URL_API_SECRET")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                companion = load_companion(Path(tmp))

                updated = companion.handle_action(
                    {
                        "action": "settings_update",
                        "settings": {
                            "mnApiBackend": "url_api",
                            "mnUrlApiSecret": "mnsec_test_secret_123",
                        },
                    }
                )

                self.assertTrue(updated["ok"])
                self.assertEqual(updated["settings"]["mnApiBackend"], "url_api")
                self.assertTrue(updated["mn_url_api_configured"])
                self.assertIn("URL API：已配置", updated["reply"])
                self.assertNotIn("mnsec_test_secret_123", json.dumps(updated, ensure_ascii=False))

                status = companion.status_payload()
                self.assertEqual(status["mn_api_backend"], "url_api")
                self.assertTrue(status["mn_url_api_configured"])
                self.assertNotIn("mnsec_test_secret_123", json.dumps(status, ensure_ascii=False))

                request_preview = companion.handle_action(
                    {
                        "action": "mn_url_api_build_request",
                        "urlApiAction": "tree",
                        "urlPayload": {"path": "@current", "depth": 2},
                        "requestId": "req_preview",
                    }
                )

                self.assertTrue(request_preview["ok"])
                self.assertEqual(request_preview["request"]["action"], "tree")
                self.assertIn("secret=[REDACTED]", request_preview["request"]["redactedUrl"])
                self.assertNotIn("mnsec_test_secret_123", json.dumps(request_preview, ensure_ascii=False))

                cleared = companion.handle_action(
                    {"action": "settings_update", "settings": {"clearMnUrlApiSecret": True}}
                )
                self.assertFalse(cleared["mn_url_api_configured"])
        finally:
            if old_secret is None:
                os.environ.pop("MN_URL_API_SECRET", None)
            else:
                os.environ["MN_URL_API_SECRET"] = old_secret

    def test_workflow_templates_and_preview_are_exposed_as_read_only_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            templates = companion.handle_action({"action": "workflow_templates"})
            self.assertTrue(templates["ok"])
            self.assertIn("paper_deep_reading", [item["id"] for item in templates["workflowTemplates"]])

            preview = companion.handle_action(
                {
                    "action": "workflow_preview",
                    "prompt": "重组当前脑图结构，保留原来的卡片",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(preview["ok"], preview)
            self.assertEqual(preview["workflow"]["id"], "mindmap_reorganize")
            self.assertIn("reorganize_mindmap", [item["action"] for item in preview["workflow"]["steps"]])
            self.assertIn("工作流：当前脑图重组工作流", preview["reply"])

    def test_skill_marketplace_lists_and_installs_permission_declared_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            status = companion.handle_action({"action": "skill_marketplace_status"})
            self.assertTrue(status["ok"])
            self.assertGreaterEqual(status["skillCount"], 2)
            self.assertIn("knowledge.related_context", [item["id"] for item in status["skills"]])
            write_skill = next(item for item in status["skills"] if item["id"] == "workflow.deep_reading_writer")
            self.assertEqual(write_skill["permission"], "notes")
            self.assertEqual(write_skill["rollback"]["strategy"], "ai_edit_transaction")
            self.assertTrue(write_skill["acceptanceRules"])

            installed = companion.handle_action({"action": "skill_install", "skillId": "workflow.deep_reading_writer"})
            self.assertTrue(installed["ok"], installed)
            self.assertTrue(installed["skill"]["installed"])
            self.assertIn("workflow.deep_reading_writer", installed["installedSkillIds"])

            uninstalled = companion.handle_action({"action": "skill_uninstall", "skillId": "workflow.deep_reading_writer"})
            self.assertTrue(uninstalled["ok"], uninstalled)
            self.assertNotIn("workflow.deep_reading_writer", uninstalled["installedSkillIds"])

    def test_mindmap_diff_preview_reports_structured_changes_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action(
                {
                    "action": "mindmap_diff_preview",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "currentMindmap": {
                        "title": "Paper",
                        "children": [{"title": "Problem", "body": "old", "children": []}],
                    },
                    "proposedMindmap": {
                        "title": "Paper",
                        "children": [
                            {"title": "Problem", "body": "old", "children": []},
                            {"title": "Method", "body": "new", "children": []},
                        ],
                    },
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["mindmapDiff"]["schema"], "codex.mn.mindmapDiff.v1")
            self.assertEqual(result["mindmapDiffOperationPlan"]["schema"], "codex.mn.mindmapDiffOperationPlan.v1")
            self.assertEqual(result["mindmapDiff"]["summary"]["createCount"], 1)
            self.assertEqual(result["mindmapDiff"]["summary"]["mergeCount"], 2)
            self.assertEqual(result["mindmapDiffOperationPlan"]["operationCount"], 3)
            self.assertEqual(result["mindmapDiffOperationPlan"]["applyBoundary"]["localApplyStatus"], "preview_only")
            self.assertEqual(result["mindmapDiffOperationPlan"]["applyBoundary"]["currentApplyPath"], "draft_tree_write")
            self.assertIn("nativeMindmap", result["mindmapDiffOperationPlan"]["requiredCapabilities"])
            self.assertIn("新增 1", result["reply"])
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"], [])

    def test_request_mindmap_diff_apply_queues_create_only_local_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 1,
                "operations": [
                    {
                        "opId": "mindmap-diff:1",
                        "op": "create_mindmap_node",
                        "diffOp": "create",
                        "mutation": "create",
                        "kind": "mindmap",
                        "title": "New Node",
                        "proposedPath": "0.1",
                        "targetParent": "Root",
                        "requires": ["nativeMindmap"],
                        "proposedRef": {"codexId": "new-node"},
                    }
                ],
                "requiredCapabilities": ["nativeMindmap"],
                "applyBoundary": {"localApplyStatus": "ready", "currentApplyPath": "local_operation_queue"},
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_diff_apply",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["applyPlan"]["operationCount"], 1)
            self.assertEqual(result["applyPlan"]["applyBoundary"]["localApplyStatus"], "queued")
            commands = companion.poll_commands("T1", "B1")["commands"]
            self.assertEqual(commands[0]["nativeAction"], "apply_mindmap_diff_operations")
            self.assertTrue(commands[0]["transactionId"].startswith("mindmap-diff-"))
            self.assertEqual(commands[0]["draftId"], "")
            self.assertEqual(commands[0]["mindmapDiffOperationPlan"]["operations"][0]["op"], "create_mindmap_node")
            self.assertEqual(result["applyPlan"]["transactionId"], commands[0]["transactionId"])

    def test_request_mindmap_diff_apply_filters_delete_suggestions_from_native_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 2,
                "operations": [
                    {
                        "opId": "mindmap-diff:create",
                        "op": "create_mindmap_node",
                        "mutation": "create",
                        "title": "New Node",
                        "targetParent": "Root",
                        "requires": ["nativeMindmap"],
                    },
                    {
                        "opId": "mindmap-diff:delete",
                        "op": "suggest_delete_mindmap_node",
                        "mutation": "delete_suggest",
                        "title": "Old Node",
                        "currentRef": {"noteId": "N-old"},
                        "requires": ["nativeMindmapDelete"],
                        "confirmationRequired": True,
                    },
                ],
                "requiredCapabilities": ["nativeMindmap", "nativeMindmapDelete"],
                "applyBoundary": {
                    "localApplyStatus": "ready",
                    "currentApplyPath": "local_operation_queue",
                    "deleteSuggestCount": 1,
                },
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_diff_apply",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["applyPlan"]["operationCount"], 1)
            self.assertEqual(result["applyPlan"]["skippedDeleteSuggestionCount"], 1)
            self.assertEqual(result["applyPlan"]["applyBoundary"]["skippedDeleteSuggestionCount"], 1)
            commands = companion.poll_commands("T1", "B1")["commands"]
            queued_plan = commands[0]["mindmapDiffOperationPlan"]
            self.assertEqual(len(queued_plan["operations"]), 1)
            self.assertEqual(queued_plan["operations"][0]["mutation"], "create")
            self.assertNotIn("delete_suggest", {item.get("mutation") for item in queued_plan["operations"]})

    def test_request_mindmap_diff_apply_blocks_update_without_native_capability(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 1,
                "operations": [
                    {
                        "opId": "mindmap-diff:1",
                        "op": "update_mindmap_node",
                        "diffOp": "update",
                        "mutation": "update",
                        "kind": "mindmap",
                        "title": "Existing Node",
                        "existingPath": "0.2",
                        "currentRef": {"noteId": "N-existing"},
                        "requires": ["nativeMindmapUpdate"],
                    }
                ],
                "requiredCapabilities": ["nativeMindmapUpdate"],
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_diff_apply",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertFalse(result["ok"], result)
            self.assertEqual(result["applyPlan"]["applyBoundary"]["localApplyStatus"], "blocked")
            self.assertEqual(result["blockedOperations"][0]["reason"], "unverified-note-update-api")
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"], [])

    def test_request_mindmap_diff_apply_queues_update_merge_move_when_capabilities_are_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "canCreateNote": True,
                        "canUpdateMindmapNode": True,
                        "canMergeMindmapNode": True,
                        "canMoveMindmapNode": True,
                    },
                }
            )
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 3,
                "operations": [
                    {
                        "opId": "mindmap-diff:update",
                        "op": "update_mindmap_node",
                        "mutation": "update",
                        "title": "Updated Existing",
                        "currentRef": {"noteId": "N-existing"},
                        "requires": ["nativeMindmapUpdate"],
                    },
                    {
                        "opId": "mindmap-diff:merge",
                        "op": "merge_mindmap_node",
                        "mutation": "merge",
                        "title": "Duplicate Existing",
                        "currentRef": {"noteId": "N-duplicate"},
                        "requires": ["nativeMindmapMerge"],
                    },
                    {
                        "opId": "mindmap-diff:move",
                        "op": "move_mindmap_node",
                        "mutation": "move",
                        "title": "Move Existing",
                        "currentRef": {"noteId": "N-child"},
                        "targetParentRef": {"noteId": "N-parent"},
                        "requires": ["nativeMindmapMove"],
                    },
                ],
                "requiredCapabilities": ["nativeMindmapUpdate", "nativeMindmapMerge", "nativeMindmapMove"],
                "applyBoundary": {"localApplyStatus": "preview_only", "currentApplyPath": "draft_tree_write"},
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_diff_apply",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["applyPlan"]["operationCount"], 3)
            self.assertEqual(result["applyPlan"]["applyBoundary"]["localApplyStatus"], "queued")
            self.assertEqual(result["applyPlan"]["applyBoundary"]["blockedOperationCount"], 0)
            commands = companion.poll_commands("T1", "B1")["commands"]
            self.assertEqual(commands[0]["nativeAction"], "apply_mindmap_diff_operations")
            self.assertTrue(commands[0]["transactionId"].startswith("mindmap-diff-"))
            queued_ops = commands[0]["mindmapDiffOperationPlan"]["operations"]
            self.assertEqual([item["mutation"] for item in queued_ops], ["update", "merge", "move"])
            self.assertEqual(queued_ops[2]["targetParentRef"]["noteId"], "N-parent")

    def test_mindmap_diff_apply_finished_event_persists_transaction_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_event(
                {
                    "event": "mindmapDiffApplyFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "mindmap-diff-tx-1",
                        "draftId": "draft-mm",
                        "createdNoteIds": ["N-created"],
                        "appliedOperations": [
                            {"opId": "mindmap-diff:1", "mutation": "create", "noteId": "N-created"}
                        ],
                        "appliedCount": 1,
                        "failedCount": 0,
                        "verification": {
                            "schema": "codex.mn.mindmapDiffApplyVerification.v1",
                            "status": "pass",
                            "summary": "脑图 Diff 验证：通过 1，失败 0。",
                            "operationVerification": [
                                {"opId": "mindmap-diff:1", "noteId": "N-created", "ok": True}
                            ],
                        },
                    },
                }
            )

            status = companion.status_payload()
            tx_status = status["aiEditTransactionStatus"]
            self.assertEqual(tx_status["latest"]["transactionId"], "mindmap-diff-tx-1")
            self.assertEqual(tx_status["latest"]["status"], "pending_confirmation")
            self.assertEqual(tx_status["latest"]["createdNoteIds"], ["N-created"])
            self.assertTrue(tx_status["latest"]["requiresConfirmation"])
            self.assertIn("retain", tx_status["latest"]["availableActions"])
            self.assertIn("rollback", tx_status["latest"]["availableActions"])
            self.assertEqual(tx_status["verification"]["status"], "pass")
            self.assertTrue(tx_status["verification"]["requiresConfirmation"])
            self.assertIn("脑图 Diff", tx_status["verification"]["summary"])

    def test_request_mindmap_diff_apply_respects_read_only_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "read_only"}})
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operations": [
                    {
                        "opId": "mindmap-diff:1",
                        "op": "create_mindmap_node",
                        "mutation": "create",
                        "title": "Blocked Node",
                        "requires": ["nativeMindmap"],
                    }
                ],
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_diff_apply",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertFalse(result["ok"], result)
            self.assertIn("read_only", result["message"])
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"], [])

    def test_request_mindmap_delete_confirmation_records_pending_transaction_without_native_delete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operations": [
                    {
                        "opId": "mindmap-diff:delete",
                        "op": "suggest_delete_mindmap_node",
                        "mutation": "delete_suggest",
                        "title": "Obsolete",
                        "currentRef": {"noteId": "N-old"},
                        "requires": ["nativeMindmapDelete"],
                        "confirmationRequired": True,
                        "confirmationType": "delete_existing_mindmap_node",
                    }
                ],
            }

            result = companion.handle_action(
                {
                    "action": "request_mindmap_delete_confirmation",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "mindmapDiffOperationPlan": plan,
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertTrue(result["transactionId"].startswith("mindmap-delete-"))
            self.assertEqual(result["deleteConfirmation"]["targetNoteIds"], ["N-old"])
            self.assertEqual(result["deleteConfirmation"]["status"], "delete_pending_confirmation")
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"], [])
            status = companion.status_payload()
            tx_status = status["aiEditTransactionStatus"]
            self.assertEqual(tx_status["latest"]["status"], "delete_pending_confirmation")
            self.assertIn("confirm_delete", tx_status["latest"]["availableActions"])
            self.assertIn("dismiss", tx_status["latest"]["availableActions"])

    def test_status_exposes_latest_mindmap_diff_apply_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "mindmapDiffApplyFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "appliedCount": 2,
                        "failedCount": 1,
                        "verification": {
                            "schema": "codex.mn.mindmapDiffApplyVerification.v1",
                            "status": "block",
                            "summary": "脑图 Diff 验证：通过 2，失败 1。",
                            "verifiedCount": 2,
                            "failedVerificationCount": 1,
                            "operationVerification": [
                                {"opId": "op-1", "ok": True, "noteId": "N1"},
                                {"opId": "op-2", "ok": False, "noteId": "N2"},
                            ],
                        },
                    },
                }
            )

            status = companion.status_payload()

            self.assertEqual(status["mindmapDiffApply"]["schema"], "codex.mn.mindmapDiffApplyStatus.v1")
            self.assertEqual(status["mindmapDiffApply"]["status"], "block")
            self.assertEqual(status["mindmapDiffApply"]["appliedCount"], 2)
            self.assertEqual(status["mindmapDiffApply"]["failedCount"], 1)
            self.assertEqual(status["mindmapDiffApply"]["verification"]["failedVerificationCount"], 1)
            self.assertIn("脑图 Diff 验证", status["mindmapDiffApply"]["summary"])

    def test_native_capability_matrix_exposes_mindmap_local_mutation_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "canCreateNote": True,
                        "canUpdateMindmapNode": True,
                        "canMergeMindmapNode": True,
                        "canMoveMindmapNode": True,
                        "canDeleteMindmapNode": False,
                    },
                }
            )

            matrix = companion.latest_native_api_capabilities("T1", "B1")["capabilityMatrix"]

            self.assertTrue(matrix["nativeMindmapUpdate"]["ready"])
            self.assertTrue(matrix["nativeMindmapMerge"]["ready"])
            self.assertTrue(matrix["nativeMindmapMove"]["ready"])
            self.assertFalse(matrix["nativeMindmapDelete"]["ready"])
            self.assertEqual(matrix["nativeMindmapUpdate"]["nativeAction"], "apply_mindmap_diff_operations")

    def test_mindmap_reorganize_workflow_queues_native_tree_read_before_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            started = companion.handle_action(
                {
                    "action": "workflow_start",
                    "workflowId": "mindmap_reorganize",
                    "prompt": "重组当前脑图结构",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "selectedNoteId": "N-root",
                    "selectedNoteTitle": "现有脑图根",
                }
            )

            self.assertTrue(started["ok"], started)
            self.assertEqual(started["workflowRun"]["steps"][0]["status"], "queued")
            self.assertEqual(started["workflowRun"]["steps"][0]["action"], "mn_read_tree")
            commands = companion.poll_commands("T1", "B1")["commands"]
            self.assertEqual(commands[0]["nativeAction"], "read_mindmap_tree")
            self.assertEqual(commands[0]["selectedNoteId"], "N-root")
            self.assertEqual(commands[1]["rawAction"], "reorganize_mindmap")
            self.assertEqual(started["summary"]["queuedCount"], 2)

    def test_mindmap_diff_preview_uses_latest_native_tree_read_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_event(
                {
                    "event": "mindmapTreeReadFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "currentMindmap": {
                            "title": "Paper",
                            "children": [{"title": "Problem", "body": "old", "children": []}],
                        },
                        "nodeCount": 2,
                    },
                }
            )

            result = companion.handle_action(
                {
                    "action": "mindmap_diff_preview",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "proposedMindmap": {
                        "title": "Paper",
                        "children": [
                            {"title": "Problem", "body": "old", "children": []},
                            {"title": "Method", "body": "new", "children": []},
                        ],
                    },
                }
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["mindmapDiff"]["summary"]["currentCount"], 2)
            self.assertEqual(result["mindmapDiff"]["summary"]["createCount"], 1)
            self.assertEqual(result["mindmapTreeCache"]["sourceEvent"], "mindmapTreeReadFinished")

    def test_status_exposes_latest_native_mindmap_tree_cache(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_event(
                {
                    "event": "mindmapTreeReadFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "selectedNoteId": "N-root",
                        "selectedNoteTitle": "Paper Map",
                        "currentMindmap": {
                            "noteId": "N-root",
                            "title": "Paper Map",
                            "children": [
                                {
                                    "noteId": "N1",
                                    "title": "Problem",
                                    "children": [{"noteId": "N1a", "title": "Motivation", "children": []}],
                                },
                                {"noteId": "N2", "title": "Method", "children": []},
                            ],
                        },
                        "nodeCount": 4,
                        "truncatedCount": 0,
                    },
                }
            )

            status = companion.status_payload()

            self.assertEqual(status["mindmapTreeCache"]["schema"], "codex.mn.mindmapTreeCache.v1")
            self.assertTrue(status["mindmapTreeCache"]["available"])
            self.assertEqual(status["mindmapTreeCache"]["nodeCount"], 4)
            self.assertEqual(status["mindmapTreeCache"]["selectedNoteId"], "N-root")
            self.assertEqual(status["mindmapTreeCache"]["rootTitle"], "Paper Map")
            self.assertEqual(status["mindmapTreeCache"]["treePreview"][0]["title"], "Paper Map")
            self.assertEqual(status["mindmapTreeCache"]["treePreview"][1]["depth"], 1)
            self.assertEqual(status["mindmapTreeCache"]["treePreview"][2]["title"], "Motivation")
            self.assertEqual(status["mindmapTreeCache"]["treePreviewCount"], 4)

    def test_agent_plan_combines_current_object_workflow_and_write_gate_without_queueing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action(
                {
                    "action": "knowledge_index_ingest_context",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "title": "已有 VLA 笔记",
                    "text": "Previous VLA safety note.",
                    "source": "unittest",
                }
            )

            planned = companion.handle_action(
                {
                    "action": "agent_plan",
                    "prompt": "把这个选区做成短卡，并关联之前的内容",
                    "selectionText": "selected evidence",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(planned["ok"], planned)
            operation = planned["agentOperation"]
            self.assertEqual(operation["schema"], "codex.mn.agentOperation.v1")
            self.assertEqual(operation["mnObject"]["schema"], "codex.mn.mnObject.v1")
            self.assertEqual(operation["mnObject"]["kind"], "selection")
            self.assertTrue(operation["mnObject"]["objectId"].startswith("mnobj:selection:"))
            self.assertEqual(operation["mnObject"]["sourceRef"]["quote"], "selected evidence")
            self.assertEqual(operation["object"]["mnObjectId"], operation["mnObject"]["objectId"])
            self.assertEqual(operation["object"]["kind"], "selection")
            self.assertEqual(operation["workflow"]["id"], "selection_to_cards")
            self.assertTrue(operation["knowledge"]["enabled"])
            self.assertEqual(operation["knowledge"]["count"], 1)
            self.assertEqual(operation["operationPolicy"]["risk"]["status"], "write_pending_confirmation")
            self.assertEqual(operation["operationPlan"]["schema"], "codex.mn.operationPlan.v1")
            self.assertEqual(operation["operationPlan"]["writeCount"], 1)
            self.assertEqual(operation["verificationPlan"]["schema"], "codex.mn.verificationPlan.v1")
            self.assertTrue(operation["verificationPlan"]["mustVerifyRollback"])
            self.assertEqual(planned["operationPlan"], operation["operationPlan"])
            self.assertEqual(planned["verificationPlan"], operation["verificationPlan"])
            self.assertEqual(planned["operationCompiler"]["schema"], "codex.mn.operationCompiler.v1")
            self.assertIn("计划步骤：", planned["reply"])
            self.assertIn("review_operation_plan", [item["id"] for item in operation["nextActions"]])
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"], [])

    def test_agent_plan_blocks_write_plan_when_required_native_capability_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "notes", "mnApiBackend": "native"}})
            companion.append_event(
                {
                    "event": "nativeApiCapabilities",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "capabilityMatrix": {
                            "nativeCards": {
                                "available": False,
                                "ready": False,
                                "blockedReason": "unverified-note-api",
                                "nextStep": "刷新 MN 原生能力。",
                            }
                        }
                    },
                }
            )

            planned = companion.handle_action(
                {
                    "action": "agent_plan",
                    "prompt": "把这个选区做成短卡",
                    "selectionText": "selected evidence",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(planned["ok"], planned)
            self.assertEqual(planned["operationPlan"]["status"], "blocked")
            self.assertEqual(planned["dryRun"]["status"], "blocked")
            self.assertGreater(planned["dryRun"]["blockedCount"], 0)
            self.assertEqual(planned["operationCompiler"]["status"], "blocked")
            compiler_checks = {item["id"]: item for item in planned["operationCompiler"]["checks"]}
            self.assertEqual(compiler_checks["dry_run"]["tone"], "block")
            self.assertIn("unverified-note-api", planned["dryRun"]["checks"][0]["reason"])

    def test_workflow_start_enqueues_safe_steps_and_pauses_at_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "notes"}})

            started = companion.handle_action(
                {
                    "action": "workflow_start",
                    "workflowId": "selection_to_cards",
                    "prompt": "把当前选区解释并做成短卡",
                    "selectionText": "selected text",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(started["ok"], started)
            self.assertEqual(started["workflowRun"]["workflowId"], "selection_to_cards")
            self.assertEqual(started["workflowRun"]["mnObject"]["schema"], "codex.mn.mnObject.v1")
            self.assertTrue(started["workflowRun"]["mnObject"]["objectId"].startswith("mnobj:selection:"))
            self.assertEqual(started["workflowRun"]["objectRef"]["objectId"], started["workflowRun"]["mnObject"]["objectId"])
            self.assertEqual(started["summary"]["mnObjectId"], started["workflowRun"]["mnObject"]["objectId"])
            self.assertEqual(started["summary"]["mnObjectKind"], "selection")
            self.assertEqual(started["summary"]["queuedCount"], 2)
            self.assertEqual(started["summary"]["waitingConfirmationCount"], 1)
            self.assertIn("写入类步骤不会自动执行", started["reply"])
            commands = companion.poll_commands("T1", "B1")["commands"]
            queued_actions = [item["rawAction"] for item in commands]
            self.assertEqual(queued_actions, ["chat", "generate_card"])
            self.assertTrue(all(item["mnObjectId"] == started["workflowRun"]["mnObject"]["objectId"] for item in commands))

            status = companion.handle_action({"action": "workflow_status", "workflowRunId": started["summary"]["id"]})
            self.assertTrue(status["ok"])
            self.assertEqual(status["summary"]["queuedCount"], 2)
            self.assertEqual(status["summary"]["mnObjectId"], started["workflowRun"]["mnObject"]["objectId"])
            inspector = status["runInspector"]
            self.assertEqual(inspector["schema"], "codex.mn.workflowRunInspector.v1")
            self.assertEqual(inspector["workflowRunId"], started["summary"]["id"])
            self.assertEqual(inspector["stepCounts"]["queued"], 2)
            self.assertEqual(inspector["stepCounts"]["waitingConfirmation"], 1)
            self.assertEqual(inspector["confirmations"][0]["stepId"], "write")
            self.assertEqual([step["nextAction"] for step in inspector["steps"]], ["watch_queue", "watch_queue", "review_dry_run", "confirm_or_reject"])
            self.assertEqual(inspector["steps"][-1]["statusTone"], "warn")

            listed = companion.handle_action({"action": "workflow_list", "topicid": "T1", "bookmd5": "B1"})
            self.assertEqual(len(listed["workflowRuns"]), 1)
            self.assertEqual(listed["workflowRuns"][0]["mnObjectId"], started["workflowRun"]["mnObject"]["objectId"])
            self.assertGreaterEqual(listed["runCount"], 1)
            self.assertEqual(listed["latestStatus"], listed["workflowRuns"][0]["status"])
            self.assertGreaterEqual(len(listed["workflowTemplates"]), 3)
            self.assertIn("selection_to_cards", [item["id"] for item in listed["workflowTemplates"]])

            cancelled = companion.handle_action({"action": "workflow_cancel", "workflowRunId": started["summary"]["id"]})
            self.assertEqual(cancelled["summary"]["status"], "cancelled")

    def test_workflow_start_respects_read_only_permission_before_queueing_note_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "read_only"}})

            started = companion.handle_action(
                {
                    "action": "workflow_start",
                    "workflowId": "selection_to_cards",
                    "prompt": "把当前选区做成短卡",
                    "selectionText": "selected text",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )

            self.assertTrue(started["ok"], started)
            self.assertEqual(started["summary"]["queuedCount"], 1)
            self.assertEqual(started["workflowRun"]["status"], "partial")
            blocked = [step for step in started["workflowRun"]["steps"] if step["status"] == "blocked"]
            self.assertEqual([step["action"] for step in blocked], ["generate_card"])
            self.assertEqual(companion.poll_commands("T1", "B1")["commands"][0]["rawAction"], "chat")

    def test_workflow_retry_step_requeues_recoverable_blocked_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "read_only"}})
            started = companion.handle_action(
                {
                    "action": "workflow_start",
                    "workflowId": "selection_to_cards",
                    "prompt": "把当前选区做成短卡",
                    "selectionText": "selected text",
                    "topicid": "T1",
                    "bookmd5": "B1",
                }
            )
            status = companion.handle_action({"action": "workflow_status", "workflowRunId": started["summary"]["id"]})
            blocked_steps = [step for step in status["runInspector"]["steps"] if step["status"] == "blocked"]
            self.assertEqual([step["stepId"] for step in blocked_steps], ["cards"])
            self.assertTrue(blocked_steps[0]["retryable"])
            self.assertEqual(blocked_steps[0]["nextAction"], "retry_step")

            companion.handle_action({"action": "settings_update", "settings": {"permission": "notes"}})
            retried = companion.handle_action(
                {
                    "action": "workflow_retry_step",
                    "workflowRunId": started["summary"]["id"],
                    "workflowStepId": "cards",
                }
            )

            self.assertTrue(retried["ok"], retried)
            self.assertEqual(retried["retriedStep"]["stepId"], "cards")
            self.assertEqual(retried["retriedStep"]["status"], "queued")
            self.assertEqual(retried["summary"]["queuedCount"], 2)
            commands = companion.poll_commands("T1", "B1")["commands"]
            self.assertEqual([item["rawAction"] for item in commands], ["chat", "generate_card"])
            retried_cards = [step for step in retried["runInspector"]["steps"] if step["stepId"] == "cards"][0]
            self.assertFalse(retried_cards["retryable"])
            self.assertEqual(retried_cards["nextAction"], "watch_queue")

            write_retry = companion.handle_action(
                {
                    "action": "workflow_retry_step",
                    "workflowRunId": started["summary"]["id"],
                    "workflowStepId": "write",
                }
            )
            self.assertFalse(write_retry["ok"])
            self.assertIn("确认", write_retry["message"])

    def test_external_gateway_start_workflow_records_request_ledger_and_reuses_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "read_only"}})

            started = companion.handle_action(
                {
                    "action": "external_gateway_start_workflow",
                    "requestId": "REQ_EXT_1",
                    "caller": "shortcuts",
                    "workflowId": "selection_to_cards",
                    "prompt": "把当前选区解释并做成短卡",
                    "selectionText": "selected text",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "callbackBaseUrl": "http://127.0.0.1:48761/external/callback",
                }
            )

            self.assertTrue(started["ok"], started)
            self.assertEqual(started["externalGateway"]["schema"], "codex.mn.externalGatewayRequest.v1")
            self.assertEqual(started["externalGateway"]["requestId"], "REQ_EXT_1")
            self.assertEqual(started["externalGateway"]["caller"], "shortcuts")
            self.assertEqual(started["externalGateway"]["permission"], "read_only")
            self.assertEqual(started["externalGateway"]["requestedAction"], "workflow_start")
            self.assertEqual(
                started["externalGateway"]["callback"]["success"],
                "http://127.0.0.1:48761/external/callback/success",
            )
            self.assertEqual(started["workflowRun"]["externalRequest"]["requestId"], "REQ_EXT_1")
            self.assertEqual(started["workflowRun"]["externalRequest"]["caller"], "shortcuts")
            self.assertEqual(started["summary"]["queuedCount"], 1)
            self.assertEqual(started["workflowRun"]["status"], "partial")
            blocked = [step for step in started["workflowRun"]["steps"] if step["status"] == "blocked"]
            self.assertEqual([step["action"] for step in blocked], ["generate_card"])

            status = companion.handle_action({"action": "external_gateway_request_status", "requestId": "REQ_EXT_1"})
            self.assertTrue(status["ok"], status)
            self.assertEqual(status["externalGateway"]["requestId"], "REQ_EXT_1")
            self.assertEqual(status["externalGateway"]["workflowRunId"], started["summary"]["id"])
            self.assertEqual(status["externalGateway"]["stage"], "workflow_started")
            self.assertEqual(status["externalGateway"]["result"]["workflowStatus"], "partial")
            self.assertEqual(status["externalGateway"]["callback"]["status"], "pending")

            callback = companion.handle_action(
                {
                    "action": "external_gateway_callback",
                    "requestId": "REQ_EXT_1",
                    "callbackStatus": "success",
                    "payload": {"mnResult": "ok", "updatedNotes": 2},
                }
            )
            self.assertTrue(callback["ok"], callback)
            self.assertEqual(callback["externalGateway"]["stage"], "callback_success")
            self.assertEqual(callback["externalGateway"]["callback"]["status"], "success")
            self.assertEqual(callback["externalGateway"]["callback"]["payload"]["updatedNotes"], 2)
            self.assertEqual(callback["externalGateway"]["callback"]["receivedCount"], 1)

            after_callback = companion.handle_action({"action": "external_gateway_request_status", "requestId": "REQ_EXT_1"})
            self.assertEqual(after_callback["externalGateway"]["callback"]["status"], "success")
            self.assertEqual(after_callback["externalGateway"]["callback"]["history"][0]["status"], "success")

    def test_external_gateway_http_route_maps_to_workflow_start_action(self) -> None:
        source = COMPANION_PATH.read_text(encoding="utf-8")

        self.assertIn('self.path == "/external/workflow/start"', source)
        self.assertIn('"action": "external_gateway_start_workflow"', source)
        self.assertIn('self.path in {"/external/callback/success", "/external/callback/error"}', source)
        self.assertIn('"action": "external_gateway_callback"', source)
        self.assertLess(
            source.index('self.path == "/external/workflow/start"'),
            source.index('if self.path != "/marginnote/action"'),
        )

    def test_operation_ledger_lists_and_loads_object_scoped_operations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:ledger1",
                "kind": "selection",
                "title": "Ledger 选区",
                "sourceRef": {"page": 12, "quote": "ledger source"},
            }
            other_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:other-ledger",
                "kind": "selection",
                "title": "其他选区",
                "sourceRef": {"page": 13, "quote": "other source"},
            }

            workflow = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "workflow_start",
                    "workflowId": "selection_to_cards",
                    "prompt": "解释并制卡",
                    "selectionText": "ledger source",
                }
            )
            self.assertTrue(workflow["ok"], workflow)

            operation_plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 1,
                "operations": [
                    {
                        "opId": "mindmap-diff:ledger-create",
                        "op": "create_mindmap_node",
                        "mutation": "create",
                        "title": "Ledger Node",
                        "requires": ["nativeMindmap"],
                    }
                ],
                "requiredCapabilities": ["nativeMindmap"],
                "applyBoundary": {
                    "localApplyStatus": "queued",
                    "currentApplyPath": "local_operation_queue",
                },
            }
            queued_apply = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "request_mindmap_diff_apply",
                    "transactionId": "ledger-tx",
                    "draftId": "ledger-draft",
                    "mindmapDiffOperationPlan": operation_plan,
                }
            )
            self.assertTrue(queued_apply["ok"], queued_apply)
            queue_id = queued_apply["queued"]["id"]
            self.assertEqual(queued_apply["queued"]["command"]["nativeAction"], "apply_mindmap_diff_operations")
            self.assertEqual(queued_apply["queued"]["command"]["transactionId"], "ledger-tx")

            companion.append_event(
                {
                    "event": "mindmapDiffApplyRequested",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ledger-tx",
                        "draftId": "ledger-draft",
                        "mindmapTitle": "Ledger Diff",
                        "mindmapDiffOperationPlan": operation_plan,
                        "nativeAction": "apply_mindmap_diff_operations",
                        "queueId": queue_id,
                        "mnObjectId": "mnobj:selection:ledger1",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "Ledger 选区",
                        "mnObjectSourceRef": {"page": 12, "quote": "ledger source"},
                    },
                }
            )
            companion.append_event(
                {
                    "event": "mindmapDiffApplyFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ledger-tx",
                        "draftId": "ledger-draft",
                        "nativeAction": "apply_mindmap_diff_operations",
                        "queueId": queue_id,
                        "createdNoteIds": ["N-LEDGER"],
                        "createdCount": 1,
                        "appliedOperations": [
                            {
                                "opId": "mindmap-diff:ledger-create",
                                "mutation": "create",
                                "noteId": "N-LEDGER",
                            }
                        ],
                        "appliedCount": 1,
                        "failedCount": 0,
                        "mindmapDiffOperationPlan": operation_plan,
                        "verification": {
                            "schema": "codex.mn.mindmapDiffApplyVerification.v1",
                            "status": "pass",
                            "summary": "Ledger Diff 验证通过。",
                            "operationVerification": [
                                {"opId": "mindmap-diff:ledger-create", "noteId": "N-LEDGER", "ok": True}
                            ],
                        },
                        "mnObjectId": "mnobj:selection:ledger1",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "Ledger 选区",
                        "mnObjectSourceRef": {"page": 12, "quote": "ledger source"},
                    },
                }
            )
            companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "external_gateway_start_workflow",
                    "requestId": "REQ_LEDGER",
                    "caller": "shortcuts",
                    "workflowId": "selection_to_cards",
                    "prompt": "外部解释并制卡",
                    "selectionText": "ledger source",
                    "callbackBaseUrl": "http://127.0.0.1:48761/external/callback",
                }
            )
            companion.handle_action(
                {
                    **base,
                    "mnObject": other_object,
                    "action": "external_gateway_start_workflow",
                    "requestId": "REQ_OTHER_LEDGER",
                    "caller": "shortcuts",
                    "workflowId": "selection_to_cards",
                    "prompt": "其他对象",
                    "selectionText": "other source",
                }
            )

            ledger = companion.handle_action({**base, "action": "operation_ledger_list", "mnObjectId": "mnobj:selection:ledger1"})

            self.assertTrue(ledger["ok"], ledger)
            self.assertEqual(ledger["schema"], "codex.mn.operationLedger.v1")
            self.assertEqual(ledger["objectRef"]["objectId"], "mnobj:selection:ledger1")
            self.assertGreaterEqual(ledger["counts"]["total"], 3)
            entry_types = {item["entryType"] for item in ledger["entries"]}
            self.assertIn("workflow_run", entry_types)
            self.assertIn("ai_edit_transaction", entry_types)
            self.assertIn("external_gateway_request", entry_types)
            self.assertNotIn("REQ_OTHER_LEDGER", json.dumps(ledger, ensure_ascii=False))
            self.assertTrue(all(item["objectRef"]["objectId"] == "mnobj:selection:ledger1" for item in ledger["entries"]))
            self.assertTrue(all(item["ledgerAction"]["action"] == "operation_ledger_get" for item in ledger["entries"]))

            external_entry = next(item for item in ledger["entries"] if item["entryType"] == "external_gateway_request")
            detail = companion.handle_action({"action": "operation_ledger_get", "ledgerId": external_entry["ledgerId"]})

            self.assertTrue(detail["ok"], detail)
            self.assertEqual(detail["schema"], "codex.mn.operationLedgerEntryDetail.v1")
            self.assertEqual(detail["entry"]["ledgerId"], external_entry["ledgerId"])
            self.assertEqual(detail["entry"]["entryType"], "external_gateway_request")
            self.assertEqual(detail["record"]["requestId"], "REQ_LEDGER")
            self.assertEqual(detail["record"]["objectRef"]["objectId"], "mnobj:selection:ledger1")

            transaction_entry = next(item for item in ledger["entries"] if item["entryType"] == "ai_edit_transaction")
            transaction_detail = companion.handle_action({"action": "operation_ledger_get", "ledgerId": transaction_entry["ledgerId"]})

            self.assertTrue(transaction_detail["ok"], transaction_detail)
            self.assertEqual(transaction_detail["evidence"]["schema"], "codex.mn.operationLedgerEvidence.v1")
            self.assertEqual(transaction_detail["evidence"]["ledgerId"], transaction_entry["ledgerId"])
            self.assertEqual(transaction_detail["evidence"]["status"], "pass")
            self.assertEqual(transaction_detail["evidence"]["verification"]["schema"], "codex.mn.aiEditVerification.v1")
            self.assertEqual(transaction_detail["evidence"]["verification"]["transactionId"], "ledger-tx")
            self.assertEqual(transaction_detail["evidence"]["verification"]["remainingCount"], 1)
            chain = transaction_detail["evidence"]["operationChain"]
            self.assertEqual(chain["schema"], "codex.mn.operationChainEvidence.v1")
            self.assertEqual(chain["operationPlan"]["schema"], "codex.mn.mindmapDiffOperationPlan.v1")
            self.assertEqual(chain["operationPlan"]["operationCount"], 1)
            self.assertEqual(chain["dryRun"]["status"], "queued")
            self.assertEqual(chain["nativeApply"]["nativeAction"], "apply_mindmap_diff_operations")
            self.assertEqual(chain["nativeApply"]["appliedCount"], 1)
            self.assertEqual(chain["nativeApply"]["createdNoteIds"], ["N-LEDGER"])
            self.assertEqual(chain["nativeCommand"]["nativeAction"], "apply_mindmap_diff_operations")
            self.assertEqual(chain["nativeCommand"]["queueId"], queue_id)
            self.assertEqual(chain["nativeCommand"]["operationCount"], 1)
            self.assertEqual(
                [item["event"] for item in chain["nativeEventTimeline"]],
                ["mindmapDiffApplyRequested", "mindmapDiffApplyFinished"],
            )
            self.assertTrue(all(item["queueId"] == queue_id for item in chain["nativeEventTimeline"]))
            self.assertEqual(chain["rollback"]["status"], "pending_confirmation")
            self.assertEqual(chain["residual"]["remainingCount"], 1)
            self.assertEqual(chain["residual"]["remainingNoteIds"], [])

    def test_object_graph_links_current_object_to_operations_and_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:graph1",
                "kind": "selection",
                "title": "Graph 选区",
                "sourceRef": {"page": 7, "quote": "graph source"},
            }

            companion.append_history(
                {**base, "mnObject": mn_object, "conversationId": "CONV_GRAPH"},
                "解释这个对象",
                "这是对象图谱测试回答。",
            )
            workflow = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "workflow_start",
                    "workflowId": "selection_to_cards",
                    "prompt": "解释并制卡",
                    "selectionText": "graph source",
                }
            )
            self.assertTrue(workflow["ok"], workflow)

            operation_plan = {
                "schema": "codex.mn.mindmapDiffOperationPlan.v1",
                "operationCount": 1,
                "operations": [
                    {
                        "opId": "mindmap-diff:graph-create",
                        "op": "create_mindmap_node",
                        "mutation": "create",
                        "title": "Graph Node",
                    }
                ],
            }
            queued_apply = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "request_mindmap_diff_apply",
                    "transactionId": "graph-tx",
                    "draftId": "graph-draft",
                    "mindmapDiffOperationPlan": operation_plan,
                }
            )
            self.assertTrue(queued_apply["ok"], queued_apply)
            companion.append_event(
                {
                    "event": "mindmapDiffApplyFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "graph-tx",
                        "draftId": "graph-draft",
                        "createdNoteIds": ["N-GRAPH"],
                        "createdCount": 1,
                        "appliedCount": 1,
                        "failedCount": 0,
                        "mindmapDiffOperationPlan": operation_plan,
                        "mnObjectId": "mnobj:selection:graph1",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "Graph 选区",
                        "mnObjectSourceRef": {"page": 7, "quote": "graph source"},
                    },
                }
            )
            external = companion.handle_action(
                {
                    **base,
                    "mnObject": mn_object,
                    "action": "external_gateway_start_workflow",
                    "requestId": "REQ_GRAPH",
                    "caller": "shortcuts",
                    "workflowId": "selection_to_cards",
                    "prompt": "外部解释并制卡",
                    "selectionText": "graph source",
                }
            )
            self.assertTrue(external["ok"], external)

            graph = companion.handle_action({**base, "action": "object_graph", "mnObjectId": "mnobj:selection:graph1"})

            self.assertTrue(graph["ok"], graph)
            self.assertEqual(graph["schema"], "codex.mn.objectGraph.v1")
            self.assertEqual(graph["root"]["objectId"], "mnobj:selection:graph1")
            self.assertEqual(graph["root"]["kind"], "selection")
            self.assertGreaterEqual(graph["counts"]["nodes"], 5)
            self.assertGreaterEqual(graph["counts"]["edges"], 4)
            node_types = {item["nodeType"] for item in graph["nodes"]}
            self.assertIn("mn_object", node_types)
            self.assertIn("conversation", node_types)
            self.assertIn("workflow_run", node_types)
            self.assertIn("ai_edit_transaction", node_types)
            self.assertIn("external_gateway_request", node_types)
            self.assertTrue(all(edge["from"] == "mnobj:selection:graph1" or edge["to"] == "mnobj:selection:graph1" for edge in graph["edges"]))
            actionable_nodes = [item for item in graph["nodes"] if item["nodeType"] != "mn_object"]
            self.assertTrue(all(item["graphAction"]["schema"] == "codex.mn.objectGraphAction.v1" for item in actionable_nodes))
            self.assertTrue(all(item["objectRef"]["objectId"] == "mnobj:selection:graph1" for item in actionable_nodes))

    def test_object_graph_links_current_object_to_knowledge_entities_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:knowledge-graph1",
                "kind": "selection",
                "title": "Patch mask graph source",
                "sourceRef": {"page": 5, "quote": "mask over image patches identifies unsafe attended regions"},
            }

            ingested = companion.handle_action(
                {
                    **base,
                    "action": "knowledge_index_ingest_context",
                    "documentTitle": "Safety Filter Paper",
                    "entities": [
                        {
                            "entityType": "mindmap_node",
                            "title": "Patch mask mechanism",
                            "body": "The mask over image patches identifies unsafe attended regions in the graph source.",
                            "noteId": "NODE-GRAPH-KNOWLEDGE",
                            "page": 5,
                            "quote": "mask over image patches",
                            "relations": [
                                {"type": "supports", "targetNoteId": "CARD-GRAPH-KNOWLEDGE", "label": "evidence card"}
                            ],
                        },
                        {
                            "entityType": "card",
                            "title": "Unsafe region evidence",
                            "text": "Unsafe attended regions are rejected using patch-level overlap evidence.",
                            "noteId": "CARD-GRAPH-KNOWLEDGE",
                            "source": {"page": 5, "quote": "unsafe attended regions"},
                        },
                    ],
                }
            )
            self.assertTrue(ingested["ok"], ingested)

            graph = companion.handle_action({**base, "mnObject": mn_object, "action": "object_graph", "limit": 12})

            self.assertTrue(graph["ok"], graph)
            self.assertEqual(graph["schema"], "codex.mn.objectGraph.v1")
            self.assertGreaterEqual(graph["counts"]["knowledge_entity"], 2)
            knowledge_nodes = [item for item in graph["nodes"] if item["nodeType"] == "knowledge_entity"]
            self.assertGreaterEqual(len(knowledge_nodes), 2)
            note_ids = {item["noteId"] for item in knowledge_nodes}
            self.assertIn("NODE-GRAPH-KNOWLEDGE", note_ids)
            self.assertIn("CARD-GRAPH-KNOWLEDGE", note_ids)
            node = next(item for item in knowledge_nodes if item["noteId"] == "NODE-GRAPH-KNOWLEDGE")
            self.assertEqual(node["entityType"], "mindmap_node")
            self.assertEqual(node["sourceRef"]["page"], 5)
            self.assertEqual(node["graphAction"]["action"], "knowledge_index_search")
            root_edges = [edge for edge in graph["edges"] if edge["from"] == "mnobj:selection:knowledge-graph1"]
            self.assertTrue(any(edge["relation"] == "mentions_knowledge" and edge["evidenceType"] == "knowledge_index" for edge in root_edges))
            relation_edges = [edge for edge in graph["edges"] if edge["relation"] == "supports"]
            self.assertTrue(relation_edges, graph["edges"])
            self.assertEqual(relation_edges[0]["evidenceType"], "knowledge_relation")
            self.assertIn("NODE-GRAPH-KNOWLEDGE", relation_edges[0]["from"])
            self.assertIn("CARD-GRAPH-KNOWLEDGE", relation_edges[0]["to"])

    def test_object_graph_links_current_object_to_native_mindmap_tree_relationships(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            companion.append_event(
                {
                    "event": "mindmapTreeReadFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "selectedNoteId": "N-root",
                        "selectedNoteTitle": "Paper Map",
                        "currentMindmap": {
                            "noteId": "N-root",
                            "title": "Paper Map",
                            "body": "root body",
                            "children": [
                                {
                                    "noteId": "N-problem",
                                    "title": "Problem",
                                    "body": "problem body",
                                    "children": [
                                        {
                                            "noteId": "N-motivation",
                                            "title": "Motivation",
                                            "body": "motivation body",
                                            "children": [],
                                        }
                                    ],
                                },
                                {"noteId": "N-method", "title": "Method", "body": "method body", "children": []},
                            ],
                        },
                        "nodeCount": 4,
                        "truncatedCount": 0,
                    },
                }
            )
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:N-root",
                "kind": "mindmap_node",
                "title": "Paper Map",
                "sourceRef": {"noteId": "N-root", "documentTitle": "Paper"},
            }

            graph = companion.handle_action({**base, "mnObject": mn_object, "action": "object_graph", "limit": 12})

            self.assertTrue(graph["ok"], graph)
            self.assertEqual(graph["mindmapTree"]["schema"], "codex.mn.nativeMindmapTreeEvidence.v1")
            self.assertEqual(graph["mindmapTree"]["nodeCount"], 4)
            self.assertEqual(graph["counts"]["mn_note"], 4)
            note_nodes = [item for item in graph["nodes"] if item["nodeType"] == "mn_note"]
            note_ids = {item["noteId"] for item in note_nodes}
            self.assertEqual({"N-root", "N-problem", "N-motivation", "N-method"}, note_ids)
            root_note = next(item for item in note_nodes if item["noteId"] == "N-root")
            self.assertEqual(root_note["sourceRef"]["noteId"], "N-root")
            self.assertEqual(root_note["depth"], 0)
            child_edges = [edge for edge in graph["edges"] if edge["relation"] == "contains" and edge["evidenceType"] == "mindmap_tree_cache"]
            self.assertTrue(any(edge["from"].endswith("N-root") and edge["to"].endswith("N-problem") for edge in child_edges))
            self.assertTrue(any(edge["from"].endswith("N-problem") and edge["to"].endswith("N-motivation") for edge in child_edges))
            focus_edges = [edge for edge in graph["edges"] if edge["relation"] == "focuses_mn_note"]
            self.assertTrue(any(edge["to"].endswith("N-root") for edge in focus_edges))

    def test_object_graph_persists_user_editable_relationship_edges(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:manual-rel-source",
                "kind": "selection",
                "title": "Unsafe attention source",
                "sourceRef": {"page": 9, "quote": "unsafe attended region"},
            }
            target_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:manual-rel-target",
                "kind": "mindmap_node",
                "title": "Safety mask node",
                "sourceRef": {"noteId": "manual-rel-target", "documentTitle": "Paper"},
            }

            saved = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_object,
                    "relation": "supports",
                    "label": "selection supports safety mask",
                    "note": "Manual graph edge created by the user from the object workspace.",
                }
            )

            self.assertTrue(saved["ok"], saved)
            self.assertEqual(saved["schema"], "codex.mn.objectGraphManualRelation.v1")
            self.assertEqual(saved["relation"]["fromObjectId"], "mnobj:selection:manual-rel-source")
            self.assertEqual(saved["relation"]["toObjectId"], "mnobj:note:manual-rel-target")
            self.assertEqual(saved["relation"]["relation"], "supports")
            self.assertEqual(saved["relation"]["evidenceType"], "manual_relation")

            graph = companion.handle_action({**base, "mnObject": mn_object, "action": "object_graph", "limit": 12})

            self.assertTrue(graph["ok"], graph)
            self.assertEqual(graph["manualRelations"]["schema"], "codex.mn.objectGraphManualRelations.v1")
            self.assertEqual(graph["manualRelations"]["count"], 1)
            manual_nodes = [item for item in graph["nodes"] if item["nodeType"] == "manual_mn_object"]
            self.assertEqual(len(manual_nodes), 1)
            self.assertEqual(manual_nodes[0]["objectRef"]["objectId"], "mnobj:note:manual-rel-target")
            self.assertEqual(manual_nodes[0]["graphAction"]["action"], "object_graph_relation_delete")
            manual_edges = [edge for edge in graph["edges"] if edge["evidenceType"] == "manual_relation"]
            self.assertEqual(len(manual_edges), 1)
            self.assertEqual(manual_edges[0]["from"], "mnobj:selection:manual-rel-source")
            self.assertEqual(manual_edges[0]["to"], "mnobj:note:manual-rel-target")
            self.assertEqual(manual_edges[0]["relation"], "supports")
            self.assertEqual(manual_edges[0]["label"], "selection supports safety mask")
            self.assertEqual(graph["counts"]["manual_mn_object"], 1)
            self.assertEqual(graph["counts"]["manual_relation"], 1)

            deleted = companion.handle_action(
                {**base, "action": "object_graph_relation_delete", "relationId": saved["relation"]["relationId"]}
            )
            self.assertTrue(deleted["ok"], deleted)
            graph_after_delete = companion.handle_action({**base, "mnObject": mn_object, "action": "object_graph", "limit": 12})
            self.assertEqual(graph_after_delete["manualRelations"]["count"], 0)
            self.assertFalse([edge for edge in graph_after_delete["edges"] if edge["evidenceType"] == "manual_relation"])

    def test_manual_object_graph_relationships_enter_operation_ledger_and_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:manual-rel-ledger",
                "kind": "selection",
                "title": "Attention evidence",
                "sourceRef": {"page": 11, "quote": "attention mask evidence"},
            }
            target_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:manual-rel-ledger-target",
                "kind": "card",
                "title": "Safety card",
                "sourceRef": {"noteId": "manual-rel-ledger-target", "documentTitle": "Paper"},
            }

            saved = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_object,
                    "relation": "supports",
                    "label": "supports card",
                    "note": "Manual relationship should be auditable.",
                }
            )
            self.assertTrue(saved["ok"], saved)

            ledger = companion.handle_action(
                {**base, "action": "operation_ledger_list", "mnObjectId": "mnobj:selection:manual-rel-ledger"}
            )

            self.assertTrue(ledger["ok"], ledger)
            self.assertEqual(ledger["counts"]["object_graph_manual_relation"], 1)
            manual_entry = next(item for item in ledger["entries"] if item["entryType"] == "object_graph_manual_relation")
            self.assertEqual(manual_entry["status"], "saved")
            self.assertEqual(manual_entry["objectRef"]["objectId"], "mnobj:selection:manual-rel-ledger")
            self.assertEqual(manual_entry["counts"]["manualRelations"], 1)
            self.assertEqual(manual_entry["ledgerAction"]["action"], "operation_ledger_get")

            detail = companion.handle_action({"action": "operation_ledger_get", "ledgerId": manual_entry["ledgerId"]})

            self.assertTrue(detail["ok"], detail)
            self.assertEqual(detail["entry"]["entryType"], "object_graph_manual_relation")
            self.assertEqual(detail["evidence"]["entryType"], "object_graph_manual_relation")
            self.assertEqual(detail["evidence"]["status"], "saved")
            self.assertEqual(detail["evidence"]["manualRelation"]["relationId"], saved["relation"]["relationId"])
            self.assertEqual(detail["evidence"]["manualRelation"]["fromObjectId"], "mnobj:selection:manual-rel-ledger")
            self.assertEqual(detail["evidence"]["manualRelation"]["toObjectId"], "mnobj:note:manual-rel-ledger-target")
            self.assertEqual(detail["evidence"]["manualRelation"]["relation"], "supports")
            self.assertEqual(detail["evidence"]["manualRelation"]["note"], "Manual relationship should be auditable.")

            activity = companion.handle_action(
                {**base, "action": "object_activity", "mnObjectId": "mnobj:selection:manual-rel-ledger"}
            )

            self.assertTrue(activity["ok"], activity)
            self.assertEqual(activity["counts"]["manualRelations"], 1)
            self.assertEqual(activity["manualRelations"][0]["activityKind"], "manual_relation")
            self.assertEqual(activity["manualRelations"][0]["activityAction"]["action"], "operation_ledger_get")

            deleted = companion.handle_action(
                {**base, "action": "object_graph_relation_delete", "relationId": saved["relation"]["relationId"]}
            )
            self.assertTrue(deleted["ok"], deleted)
            ledger_after_delete = companion.handle_action(
                {**base, "action": "operation_ledger_list", "mnObjectId": "mnobj:selection:manual-rel-ledger"}
            )
            statuses = [item["status"] for item in ledger_after_delete["entries"] if item["entryType"] == "object_graph_manual_relation"]
            self.assertIn("deleted", statuses)

    def test_operation_ledger_filters_by_type_status_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:ledger-filter",
                "kind": "selection",
                "title": "Ledger filter source",
                "sourceRef": {"page": 18, "quote": "ledger filter quote"},
            }
            target_a = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:ledger-filter-a",
                "kind": "card",
                "title": "Filtered safety card",
                "sourceRef": {"noteId": "ledger-filter-a", "documentTitle": "Paper"},
            }
            target_b = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:ledger-filter-b",
                "kind": "card",
                "title": "Other obsolete card",
                "sourceRef": {"noteId": "ledger-filter-b", "documentTitle": "Paper"},
            }

            saved_a = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_a,
                    "relation": "supports",
                    "label": "Filtered safety relation",
                    "note": "This saved relation should survive ledger filtering.",
                }
            )
            saved_b = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_b,
                    "relation": "related_to",
                    "label": "Other obsolete relation",
                    "note": "This relation should be filtered out.",
                }
            )
            self.assertTrue(saved_a["ok"], saved_a)
            self.assertTrue(saved_b["ok"], saved_b)
            deleted_b = companion.handle_action(
                {**base, "action": "object_graph_relation_delete", "relationId": saved_b["relation"]["relationId"]}
            )
            self.assertTrue(deleted_b["ok"], deleted_b)

            unfiltered = companion.handle_action(
                {**base, "action": "operation_ledger_list", "mnObjectId": "mnobj:selection:ledger-filter"}
            )
            filtered = companion.handle_action(
                {
                    **base,
                    "action": "operation_ledger_list",
                    "mnObjectId": "mnobj:selection:ledger-filter",
                    "entryTypeFilter": "object_graph_manual_relation",
                    "statusFilter": "saved",
                    "query": "Filtered safety",
                }
            )

            self.assertTrue(unfiltered["ok"], unfiltered)
            self.assertGreaterEqual(unfiltered["counts"]["total"], 3)
            self.assertTrue(filtered["ok"], filtered)
            self.assertEqual(filtered["filters"]["entryTypeFilter"], "object_graph_manual_relation")
            self.assertEqual(filtered["filters"]["statusFilter"], "saved")
            self.assertEqual(filtered["filters"]["query"], "Filtered safety")
            self.assertGreater(filtered["counts"]["unfilteredTotal"], filtered["counts"]["filteredTotal"])
            self.assertEqual(filtered["counts"]["filteredTotal"], 1)
            self.assertEqual(filtered["counts"]["total"], 1)
            self.assertEqual(len(filtered["entries"]), 1)
            self.assertEqual(filtered["entries"][0]["entryType"], "object_graph_manual_relation")
            self.assertEqual(filtered["entries"][0]["status"], "saved")
            self.assertEqual(filtered["entries"][0]["title"], "Filtered safety relation")
            self.assertIn("Filtered safety card", filtered["entries"][0]["summary"])

    def test_object_browser_collects_focus_graph_activity_and_ledger_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:browser-source",
                "kind": "selection",
                "title": "Browser source selection",
                "sourceRef": {"page": 7, "quote": "browser source quote"},
            }
            target_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:browser-target",
                "kind": "mindmap_node",
                "title": "Browser target node",
                "sourceRef": {"noteId": "browser-target", "documentTitle": "Paper"},
            }
            saved = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_object,
                    "relation": "supports",
                    "label": "browser relation",
                    "note": "Object Browser should expose this relation as an auditable object.",
                }
            )
            self.assertTrue(saved["ok"], saved)

            browser = companion.handle_action(
                {**base, "action": "object_browser", "mnObject": mn_object, "limit": 12}
            )

            self.assertTrue(browser["ok"], browser)
            self.assertEqual(browser["schema"], "codex.mn.objectBrowser.v1")
            self.assertEqual(browser["rootObject"]["objectId"], "mnobj:selection:browser-source")
            self.assertGreaterEqual(browser["counts"]["total"], 3)
            self.assertGreaterEqual(browser["counts"]["object_graph"], 1)
            self.assertGreaterEqual(browser["counts"]["object_activity"], 1)
            self.assertGreaterEqual(browser["counts"]["operation_ledger"], 1)
            self.assertEqual(browser["groups"][0]["groupId"], "focus")
            self.assertTrue(any(group["groupId"] == "object_graph" for group in browser["groups"]))
            self.assertTrue(any(group["groupId"] == "operation_ledger" for group in browser["groups"]))

            focus_item = next(item for item in browser["objects"] if item["objectType"] == "focus")
            self.assertEqual(focus_item["objectRef"]["objectId"], "mnobj:selection:browser-source")
            self.assertTrue(any(action["action"] == "object_graph" for action in focus_item["availableActions"]))

            graph_items = [item for item in browser["objects"] if item["objectType"] == "object_graph"]
            self.assertTrue(any(item["kind"] == "manual_mn_object" for item in graph_items), browser["objects"])
            self.assertTrue(any(item["objectRef"]["objectId"] == "mnobj:note:browser-target" for item in graph_items))

            ledger_items = [item for item in browser["objects"] if item["objectType"] == "operation_ledger"]
            self.assertTrue(any(item["kind"] == "object_graph_manual_relation" for item in ledger_items), browser["objects"])
            ledger_item = next(item for item in ledger_items if item["kind"] == "object_graph_manual_relation")
            self.assertEqual(ledger_item["availableActions"][0]["action"], "operation_ledger_get")
            self.assertIn("manualRelation", ledger_item["evidence"])

    def test_object_browser_filters_by_object_type_kind_and_query(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:browser-filter-source",
                "kind": "selection",
                "title": "Browser filter source selection",
                "sourceRef": {"page": 11, "quote": "filter source quote"},
            }
            target_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:browser-filter-target",
                "kind": "mindmap_node",
                "title": "Filtered target concept",
                "sourceRef": {"noteId": "browser-filter-target", "documentTitle": "Filter Paper"},
            }
            saved = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_object,
                    "relation": "supports",
                    "label": "filter relation",
                    "note": "Object Browser filters should find this target only.",
                }
            )
            self.assertTrue(saved["ok"], saved)

            browser = companion.handle_action(
                {
                    **base,
                    "action": "object_browser",
                    "mnObject": mn_object,
                    "limit": 12,
                    "objectTypeFilter": "registry",
                    "kindFilter": "mindmap_node",
                    "query": "Filtered target",
                }
            )

            self.assertTrue(browser["ok"], browser)
            self.assertEqual(browser["filters"]["objectType"], "registry")
            self.assertEqual(browser["filters"]["kind"], "mindmap_node")
            self.assertEqual(browser["filters"]["query"], "Filtered target")
            self.assertGreater(browser["counts"]["unfilteredTotal"], browser["counts"]["filteredTotal"])
            self.assertEqual(browser["counts"]["total"], browser["counts"]["filteredTotal"])
            self.assertGreaterEqual(browser["counts"]["filteredTotal"], 1)
            self.assertTrue(browser["objects"], browser)
            self.assertTrue(all(item["objectType"] == "registry" for item in browser["objects"]))
            self.assertTrue(all(item["kind"] == "mindmap_node" for item in browser["objects"]))
            self.assertEqual(browser["objects"][0]["objectRef"]["objectId"], "mnobj:note:browser-filter-target")

    def test_mn_object_registry_persists_objects_seen_by_object_browser(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:selection:registry-source",
                "kind": "selection",
                "title": "Registry source selection",
                "sourceRef": {"page": 9, "quote": "registry source quote"},
            }
            target_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:registry-target",
                "kind": "mindmap_node",
                "title": "Registry target node",
                "sourceRef": {"noteId": "registry-target", "documentTitle": "Registry Paper"},
            }

            saved = companion.handle_action(
                {
                    **base,
                    "action": "object_graph_relation_save",
                    "mnObject": mn_object,
                    "targetObject": target_object,
                    "relation": "supports",
                    "label": "registry relation",
                    "note": "Registry should persist both relation endpoints.",
                }
            )
            self.assertTrue(saved["ok"], saved)

            registry = companion.handle_action({**base, "action": "mn_object_registry", "mnObject": mn_object})

            self.assertTrue(registry["ok"], registry)
            self.assertEqual(registry["schema"], "codex.mn.mnObjectRegistry.v1")
            registry_ids = [item["objectRef"]["objectId"] for item in registry["objects"]]
            self.assertIn("mnobj:selection:registry-source", registry_ids)
            self.assertIn("mnobj:note:registry-target", registry_ids)
            target_entry = next(
                item for item in registry["objects"] if item["objectRef"]["objectId"] == "mnobj:note:registry-target"
            )
            self.assertGreaterEqual(target_entry["seenCount"], 1)
            self.assertIn("manual_relation", target_entry["evidenceTypes"])

            browser = companion.handle_action({**base, "action": "object_browser", "mnObject": mn_object, "limit": 12})

            self.assertTrue(browser["ok"], browser)
            self.assertGreaterEqual(browser["counts"]["registry"], 1)
            self.assertTrue(any(group["groupId"] == "registry" for group in browser["groups"]))
            registry_items = [item for item in browser["objects"] if item["objectType"] == "registry"]
            self.assertTrue(
                any(item["objectRef"]["objectId"] == "mnobj:note:registry-target" for item in registry_items),
                browser["objects"],
            )

    def test_mn_object_registry_ingests_native_mindmap_tree_cache_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            companion.append_event(
                {
                    "event": "mindmapTreeReadFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "selectedNoteId": "N-root",
                        "selectedNoteTitle": "Paper Map",
                        "currentMindmap": {
                            "noteId": "N-root",
                            "title": "Paper Map",
                            "body": "root body",
                            "children": [
                                {
                                    "noteId": "N-problem",
                                    "title": "Problem",
                                    "body": "problem body",
                                    "children": [
                                        {
                                            "noteId": "N-motivation",
                                            "title": "Motivation",
                                            "body": "motivation body",
                                            "children": [],
                                        }
                                    ],
                                },
                                {"noteId": "N-method", "title": "Method", "body": "method body", "children": []},
                            ],
                        },
                        "nodeCount": 4,
                        "truncatedCount": 0,
                    },
                }
            )

            registry = companion.handle_action({**base, "action": "mn_object_registry"})

            self.assertTrue(registry["ok"], registry)
            registry_by_id = {item["objectRef"]["objectId"]: item for item in registry["objects"]}
            for note_id in ["N-root", "N-problem", "N-motivation", "N-method"]:
                object_id = f"mnobj:note:{note_id}"
                self.assertIn(object_id, registry_by_id)
                self.assertEqual(registry_by_id[object_id]["objectRef"]["sourceRef"]["noteId"], note_id)
                self.assertIn("mindmap_tree_cache", registry_by_id[object_id]["evidenceTypes"])
            self.assertEqual(registry_by_id["mnobj:note:N-problem"]["objectRef"]["sourceRef"]["parentNoteId"], "N-root")
            self.assertEqual(registry["counts"]["kinds"]["mindmap_node"], 4)

            browser = companion.handle_action(
                {
                    **base,
                    "action": "object_browser",
                    "mnObject": {
                        "schema": "codex.mn.mnObject.v1",
                        "objectId": "mnobj:note:N-root",
                        "kind": "mindmap_node",
                        "title": "Paper Map",
                        "sourceRef": {"noteId": "N-root", "documentTitle": "Paper Map"},
                    },
                    "limit": 12,
                }
            )

            self.assertTrue(browser["ok"], browser)
            registry_items = [item for item in browser["objects"] if item["objectType"] == "registry"]
            self.assertTrue(any(item["objectRef"]["objectId"] == "mnobj:note:N-method" for item in registry_items))

    def test_request_mn_object_registry_scan_enqueues_native_scan_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            payload = {"topicid": "T1", "bookmd5": "B1", "source": "unittest", "limit": 80}

            requested = companion.handle_action({**payload, "action": "request_mn_object_registry_scan"})

            self.assertTrue(requested["ok"], requested)
            polled = companion.poll_commands("T1", "B1")
            self.assertTrue(polled["hasCommand"], polled)
            self.assertEqual(polled["command"]["nativeAction"], "scan_mn_objects")
            self.assertEqual(polled["command"]["limit"], 80)

    def test_mn_object_registry_ingests_native_object_scan_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}

            companion.append_event(
                {
                    "event": "mnObjectRegistryScanFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "scanId": "scan-001",
                        "objectCount": 2,
                        "objects": [
                            {
                                "objectId": "mnobj:note:scan-root",
                                "kind": "mindmap_node",
                                "title": "Scanned Root",
                                "sourceRef": {
                                    "noteId": "scan-root",
                                    "documentTitle": "Scanned Paper",
                                    "nodePath": "1",
                                },
                            },
                            {
                                "objectId": "mnobj:note:scan-child",
                                "kind": "mindmap_node",
                                "title": "Scanned Child",
                                "sourceRef": {
                                    "noteId": "scan-child",
                                    "parentNoteId": "scan-root",
                                    "documentTitle": "Scanned Paper",
                                    "nodePath": "1.1",
                                },
                            },
                        ],
                    },
                }
            )

            registry = companion.handle_action({**base, "action": "mn_object_registry", "limit": 20})

            self.assertTrue(registry["ok"], registry)
            by_id = {item["objectRef"]["objectId"]: item for item in registry["objects"]}
            self.assertIn("mnobj:note:scan-root", by_id)
            self.assertIn("mnobj:note:scan-child", by_id)
            self.assertEqual(by_id["mnobj:note:scan-child"]["objectRef"]["sourceRef"]["parentNoteId"], "scan-root")
            self.assertIn("native_object_scan", by_id["mnobj:note:scan-child"]["evidenceTypes"])
            self.assertEqual(registry["counts"]["kinds"]["mindmap_node"], 2)

            browser = companion.handle_action(
                {
                    **base,
                    "action": "object_browser",
                    "mnObject": {
                        "schema": "codex.mn.mnObject.v1",
                        "objectId": "mnobj:note:scan-root",
                        "kind": "mindmap_node",
                        "title": "Scanned Root",
                        "sourceRef": {"noteId": "scan-root", "documentTitle": "Scanned Paper"},
                    },
                    "limit": 20,
                }
            )
            scanned_child = next(
                item
                for item in browser["objects"]
                if item["objectType"] == "registry" and item["objectRef"]["objectId"] == "mnobj:note:scan-child"
            )
            graph_action = next(action for action in scanned_child["availableActions"] if action["action"] == "object_graph")
            self.assertEqual(graph_action["payload"]["mnObjectId"], "mnobj:note:scan-child")
            self.assertEqual(graph_action["payload"]["mnObject"]["sourceRef"]["parentNoteId"], "scan-root")
            self.assertIn("native_object_scan", graph_action["payload"]["evidenceTypes"])

    def test_object_graph_links_native_object_scan_registry_nodes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            base = {"topicid": "T1", "bookmd5": "B1", "source": "unittest"}

            companion.append_event(
                {
                    "event": "mnObjectRegistryScanFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "scanId": "scan-graph-001",
                        "objectCount": 2,
                        "objects": [
                            {
                                "objectId": "mnobj:note:scan-root",
                                "kind": "mindmap_node",
                                "title": "Scanned Root",
                                "summary": "Root summary",
                                "sourceRef": {
                                    "noteId": "scan-root",
                                    "documentTitle": "Scanned Paper",
                                    "nodePath": "1",
                                },
                            },
                            {
                                "objectId": "mnobj:note:scan-child",
                                "kind": "mindmap_node",
                                "title": "Scanned Child",
                                "summary": "Child summary",
                                "sourceRef": {
                                    "noteId": "scan-child",
                                    "parentNoteId": "scan-root",
                                    "documentTitle": "Scanned Paper",
                                    "nodePath": "1.1",
                                },
                            },
                        ],
                    },
                }
            )
            mn_object = {
                "schema": "codex.mn.mnObject.v1",
                "objectId": "mnobj:note:scan-root",
                "kind": "mindmap_node",
                "title": "Scanned Root",
                "sourceRef": {"noteId": "scan-root", "documentTitle": "Scanned Paper"},
            }

            graph = companion.handle_action({**base, "mnObject": mn_object, "action": "object_graph", "limit": 12})

            self.assertTrue(graph["ok"], graph)
            self.assertGreaterEqual(graph["counts"].get("mn_note", 0), 2)
            self.assertGreaterEqual(graph["counts"].get("native_object_scan", 0), 1)
            note_nodes = [item for item in graph["nodes"] if item["nodeType"] == "mn_note"]
            note_ids = {item["noteId"] for item in note_nodes}
            self.assertIn("scan-root", note_ids)
            self.assertIn("scan-child", note_ids)
            child = next(item for item in note_nodes if item["noteId"] == "scan-child")
            self.assertEqual(child["sourceRef"]["parentNoteId"], "scan-root")
            self.assertIn("native_object_scan", child["evidenceTypes"])
            native_edges = [
                edge
                for edge in graph["edges"]
                if edge["relation"] == "contains" and edge["evidenceType"] == "native_object_scan"
            ]
            self.assertTrue(
                any(edge["from"].endswith("scan-root") and edge["to"].endswith("scan-child") for edge in native_edges),
                graph["edges"],
            )

    def test_knowledge_index_ingests_searches_and_clears_current_context_scope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            ingested = companion.handle_action(
                {
                    "action": "knowledge_index_ingest_context",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "documentTitle": "RobotManip Report",
                    "selectionText": "Qwen RobotManip aligns VLA foundation models for manipulation.",
                    "source": "unittest",
                }
            )
            self.assertTrue(ingested["ok"], ingested)

            status = companion.handle_action({"action": "knowledge_index_status", "topicid": "T1", "bookmd5": "B1"})
            self.assertEqual(status["count"], 1)

            found = companion.handle_action(
                {"action": "knowledge_index_search", "query": "VLA manipulation", "topicid": "T1", "bookmd5": "B1"}
            )
            self.assertTrue(found["ok"])
            self.assertEqual(len(found["matches"]), 1)
            self.assertIn("RobotManip", found["matches"][0]["title"])

            cleared = companion.handle_action({"action": "knowledge_index_clear", "topicid": "T1", "bookmd5": "B1"})
            self.assertEqual(cleared["removed"], 1)

    def test_knowledge_index_ingests_structured_marginnote_entities(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            ingested = companion.handle_action(
                {
                    "action": "knowledge_index_ingest_context",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "documentTitle": "Safety Filter Paper",
                    "source": "unittest",
                    "entities": [
                        {
                            "entityType": "mindmap_node",
                            "title": "Attention safety branch",
                            "body": "Mindmap branch about attention-guided safety filters.",
                            "noteId": "NODE-42",
                            "page": 4,
                            "quote": "attention-guided safety filters",
                            "relations": [{"type": "contains", "targetNoteId": "CARD-42"}],
                        },
                        {
                            "entityType": "card",
                            "title": "Patch mask evidence",
                            "text": "A mask over image patches identifies unsafe attended regions.",
                            "noteId": "CARD-42",
                            "source": {"page": 5, "quote": "mask over image patches"},
                        },
                    ],
                }
            )

            self.assertTrue(ingested["ok"], ingested)
            self.assertEqual(ingested["entityCount"], 2)
            status = companion.handle_action({"action": "knowledge_index_status", "topicid": "T1", "bookmd5": "B1"})
            self.assertEqual(status["entityTypes"]["mindmap_node"], 1)
            self.assertEqual(status["entityTypes"]["card"], 1)

            found = companion.handle_action(
                {"action": "knowledge_index_search", "query": "unsafe attended regions", "topicid": "T1", "bookmd5": "B1"}
            )
            self.assertTrue(found["ok"])
            self.assertEqual(found["matches"][0]["noteId"], "CARD-42")
            self.assertEqual(found["matches"][0]["entityType"], "card")
            self.assertEqual(found["matches"][0]["sourceRef"]["page"], 5)
            self.assertIn("mask over image patches", found["reply"])

    def test_model_context_includes_structured_knowledge_entity_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action(
                {
                    "action": "knowledge_index_ingest_context",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                    "entities": [
                        {
                            "entityType": "card",
                            "title": "Patch mask evidence",
                            "text": "A mask over image patches identifies unsafe attended regions.",
                            "noteId": "CARD-42",
                            "source": {"page": 5, "quote": "mask over image patches"},
                        }
                    ],
                }
            )

            model_input = companion.build_model_input(
                {
                    "prompt": "已有 unsafe attended regions 的来源是什么",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "includeKnowledgeIndex": True,
                },
                "chat",
            )

            self.assertIn("noteId=CARD-42", model_input)
            self.assertIn("p.5", model_input)
            self.assertIn("mask over image patches", model_input)

    def test_model_input_uses_knowledge_index_only_when_requested(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action(
                {
                    "action": "knowledge_index_ingest_context",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "title": "RobotManip 索引笔记",
                    "text": "VLA manipulation alignment evidence from previous reading.",
                    "source": "unittest",
                }
            )

            plain = companion.build_model_input(
                {
                    "prompt": "解释当前选区",
                    "selectionText": "current selection",
                    "contextScope": "selection",
                    "topicid": "T1",
                    "bookmd5": "B1",
                },
                "chat",
            )
            self.assertNotIn("本地知识索引检索片段", plain)

            with_index = companion.build_model_input(
                {
                    "prompt": "之前关于 VLA manipulation 的已有笔记是什么",
                    "contextScope": "selection",
                    "topicid": "T1",
                    "bookmd5": "B1",
                },
                "chat",
            )
            self.assertIn("本地知识索引检索片段", with_index)
            self.assertIn("RobotManip 索引笔记", with_index)

    def test_knowledge_index_model_context_can_expand_to_current_notebook_not_global(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            for topicid, bookmd5, title, text in [
                ("T1", "B1", "当前文档笔记", "safety alignment in the current paper"),
                ("T1", "B2", "同 Notebook 另一篇", "safety comparison from another paper"),
                ("T2", "B9", "其他 Notebook", "safety note from global unrelated notebook"),
            ]:
                companion.handle_action(
                    {
                        "action": "knowledge_index_ingest_context",
                        "topicid": topicid,
                        "bookmd5": bookmd5,
                        "title": title,
                        "text": text,
                        "source": "unittest",
                    }
                )

            model_input = companion.build_model_input(
                {
                    "prompt": "跨文档 notebook 里 safety 相关笔记",
                    "contextScope": "selection",
                    "topicid": "T1",
                    "bookmd5": "B1",
                },
                "chat",
            )

            self.assertIn("范围：notebook", model_input)
            self.assertIn("当前文档笔记", model_input)
            self.assertIn("同 Notebook 另一篇", model_input)
            self.assertNotIn("其他 Notebook", model_input)

    def test_stop_current_clears_web_busy_and_acks_current_queue_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            queued = companion.enqueue_command(
                {
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "test",
                    "command": {
                        "rawAction": "generate_mindmap",
                        "prompt": "生成脑图",
                        "source": "test",
                    },
                }
            )
            self.assertTrue(queued["ok"])
            queue_id = queued["queued"]["id"]
            companion.handle_action({"action": "web_busy_update", "busy": True})

            stopped = companion.handle_action(
                {
                    "action": "stop_current",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "queue_id": queue_id,
                }
            )

            self.assertTrue(stopped["ok"])
            self.assertEqual(stopped["queue"]["pending"], 0)
            self.assertFalse(companion.web_busy_status()["busy"])
            self.assertFalse(companion.active_run_status()["active"])
            self.assertEqual(companion.poll_commands("T1", "B1")["pending"], 0)

    def test_stop_current_cancels_registered_generation_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            class FakeProcess:
                pid = 43210

                def __init__(self) -> None:
                    self.terminated = False
                    self.killed = False

                def poll(self) -> None:
                    return None

                def terminate(self) -> None:
                    self.terminated = True

                def wait(self, timeout: float | None = None) -> None:
                    raise companion.subprocess.TimeoutExpired(["codex"], timeout or 0)

                def kill(self) -> None:
                    self.killed = True

            fake = FakeProcess()
            companion.register_current_generation_process(fake, "codex-cli")

            stopped = companion.handle_action({"action": "stop_current", "topicid": "T1", "bookmd5": "B1"})

            self.assertTrue(stopped["ok"])
            self.assertTrue(stopped["cancelledProcess"]["attempted"])
            self.assertTrue(fake.terminated or fake.killed)
            self.assertIsNone(companion.current_generation_process())

    def test_ai_backend_probe_reports_effective_backend_without_model_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"aiBackend": "local"}})

            local_probe = companion.handle_action({"action": "ai_backend_probe"})
            self.assertTrue(local_probe["ok"])
            self.assertFalse(local_probe["ready"])
            self.assertEqual(local_probe["selectedBackend"], "local")
            self.assertEqual(local_probe["effectiveBackend"], "")
            self.assertIn("不会发送测试 prompt", local_probe["reply"])
            self.assertIn("切换 AI 后端", "\n".join(local_probe["nextActions"]))

            companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {
                        "aiBackend": "openai_api",
                        "openaiApiKey": "sk-test-1234567890abcdef",
                    },
                }
            )
            openai_probe = companion.handle_action({"action": "ai_backend_probe"})
            self.assertTrue(openai_probe["ok"])
            self.assertTrue(openai_probe["ready"])
            self.assertEqual(openai_probe["effectiveBackend"], "openai_api")
            self.assertTrue(openai_probe["openai"]["configured"])
            self.assertNotIn("sk-test", openai_probe["reply"])
            self.assertNotIn("openaiApiKey", openai_probe)

    def test_native_highlight_selection_requires_full_permission(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "notes"}})

            blocked = companion.handle_action(
                {
                    "action": "request_native_highlight_selection",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "selectionText": "Attention-Guided Safety Filter",
                }
            )

            self.assertFalse(blocked["ok"])
            self.assertIn("full 权限", blocked["message"])

            companion.handle_action({"action": "settings_update", "settings": {"permission": "full"}})

            allowed = companion.handle_action(
                {
                    "action": "request_native_highlight_selection",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "selectionText": "Attention-Guided Safety Filter",
                }
            )

            self.assertTrue(allowed["ok"])
            self.assertEqual(allowed["queued"]["command"]["nativeAction"], "highlight_current_selection")

    def test_permission_diagnosis_reports_file_access_and_full_disk_access_guidance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            pdf = Path(tmp) / "source.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            db = Path(tmp) / "MarginNotes.sqlite"
            db.write_bytes(b"sqlite")
            companion.DB_PATH = db
            companion.PDF_EXPORT_DIR = Path(tmp) / "exports"

            result = companion.handle_action(
                {
                    "action": "diagnose_permissions",
                    "bookmd5": "B1",
                    "pdfPath": str(pdf),
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "OK")
            self.assertEqual(result["fileAccess"]["sourcePdf"]["status"], "OK")
            self.assertEqual(result["fileAccess"]["exportDir"]["status"], "OK")
            self.assertIn("Full Disk Access", result["reply"])

            def denied_read(path: Path) -> dict[str, Any]:
                return {
                    "path": str(path),
                    "exists": True,
                    "readable": False,
                    "status": "PERMISSION",
                    "message": "Operation not permitted",
                }

            companion.probe_file_read_access = denied_read
            denied = companion.handle_action(
                {
                    "action": "diagnose_permissions",
                    "bookmd5": "B1",
                    "pdfPath": str(pdf),
                }
            )

            self.assertTrue(denied["ok"])
            self.assertEqual(denied["status"], "PERMISSION")
            self.assertEqual(denied["fileAccess"]["sourcePdf"]["status"], "PERMISSION")
            self.assertIn("Operation not permitted", denied["reply"])
            self.assertIn("Full Disk Access", denied["reply"])

    def test_permission_diagnosis_treats_database_permission_as_degraded_when_pdf_export_path_is_usable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            pdf = Path(tmp) / "source.pdf"
            pdf.write_bytes(b"%PDF-1.4\n")
            db = Path(tmp) / "MarginNotes.sqlite"
            db.write_bytes(b"sqlite")
            companion.DB_PATH = db
            companion.PDF_EXPORT_DIR = Path(tmp) / "exports"

            def probe_read(path: Path) -> dict[str, Any]:
                if path == db:
                    return {
                        "path": str(path),
                        "exists": True,
                        "readable": False,
                        "status": "PERMISSION",
                        "message": "Operation not permitted",
                    }
                return {
                    "path": str(path),
                    "exists": True,
                    "readable": True,
                    "status": "OK",
                    "message": "readable",
                }

            companion.probe_file_read_access = probe_read

            result = companion.handle_action(
                {
                    "action": "diagnose_permissions",
                    "bookmd5": "B1",
                    "pdfPath": str(pdf),
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "WARN")
            self.assertEqual(result["fileAccess"]["sourcePdf"]["status"], "OK")
            self.assertEqual(result["fileAccess"]["mnDatabase"]["status"], "PERMISSION")
            self.assertIn("基础文件访问可用", result["message"])
            self.assertIn("MN 数据库", result["reply"])

    def test_open_full_disk_access_settings_uses_macos_privacy_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[list[str]] = []

            class FakeCompleted:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(args: list[str], **kwargs: Any) -> FakeCompleted:
                calls.append(args)
                return FakeCompleted()

            old_run = companion.subprocess.run
            companion.subprocess.run = fake_run
            try:
                result = companion.handle_action({"action": "open_full_disk_access_settings"})
            finally:
                companion.subprocess.run = old_run

            self.assertTrue(result["ok"])
            self.assertEqual(calls[0][0], "/usr/bin/open")
            self.assertIn("Privacy_AllFiles", calls[0][1])
            self.assertIn("Full Disk Access", result["reply"])

    def test_goal_run_is_one_shot_action_that_does_not_persist_active_goal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"aiBackend": "local"}})

            result = companion.handle_action(
                {
                    "action": "goal_run",
                    "goal": {
                        "title": "完成 KNOWS 讲解",
                        "detail": "生成 defense 讲稿、脑图、卡片，并保持原文清洁。",
                    },
                    "selectionText": "Figure 2 shows the overview of KNOWS.",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["goal"]["title"], "完成 KNOWS 讲解")
            self.assertTrue(result["goalOneShot"])
            self.assertEqual(companion.active_goal()["title"], "")
            self.assertEqual(companion.active_goal()["detail"], "")
            self.assertIn("已启动目标", result["message"])
            self.assertIn("完成 KNOWS 讲解", result["reply"])
            history = companion.handle_action(
                {"action": "history_list", "topicid": "T1", "bookmd5": "B1", "source": "unittest"}
            )["history"]
            self.assertGreaterEqual(len(history), 2)
            self.assertIn("目标：完成 KNOWS 讲解", history[0]["content"])

    def test_ai_backend_sanitizes_and_routes_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            os.environ.pop("OPENAI_API_KEY", None)
            companion = load_companion(Path(tmp))

            rejected = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"aiBackend": "unknown-backend"},
                }
            )
            self.assertEqual(rejected["settings"]["aiBackend"], "auto")

            forced_cli = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"aiBackend": "codex_cli", "codexCliPath": "/tmp/missing-codex"},
                }
            )
            self.assertEqual(forced_cli["settings"]["aiBackend"], "codex_cli")
            self.assertEqual(forced_cli["settings"]["codexCliPath"], "/tmp/missing-codex")
            text, backend = companion.generate_reply({"prompt": "Figure 2 做什么"}, "chat")
            self.assertEqual(backend, "codex-cli-error")
            self.assertIn("Codex CLI", text)

            calls: list[str] = []

            def fake_cli(payload: dict[str, Any], task: str) -> tuple[str | None, str]:
                calls.append(task)
                return None, "codex-cli-error"

            companion.call_codex_cli = fake_cli
            companion.save_runtime_settings({"aiBackend": "auto"})
            auto_text, auto_backend = companion.generate_reply({"prompt": "Figure 2 做什么"}, "chat")
            self.assertEqual(calls, ["chat"])
            self.assertEqual(auto_backend, "codex-cli-error")
            self.assertIn("Codex CLI", auto_text)
            self.assertNotIn("Figure 2 的作用", auto_text)

    def test_proxy_url_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            rejected = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"proxyUrl": "file:///tmp/socket"},
                }
            )
            self.assertTrue(rejected["ok"])
            self.assertEqual(rejected["settings"]["proxyUrl"], "")
            self.assertFalse(companion.status_payload()["proxy_configured"])

            rejected_socks = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"proxyUrl": "socks5://127.0.0.1:7890"},
                }
            )
            self.assertTrue(rejected_socks["ok"])
            self.assertEqual(rejected_socks["settings"]["proxyUrl"], "")

            accepted = companion.handle_action(
                {
                    "action": "settings_update",
                    "settings": {"proxyUrl": "https://proxy.example.test:8443"},
                }
            )
            self.assertTrue(accepted["ok"])
            self.assertEqual(accepted["settings"]["proxyUrl"], "https://proxy.example.test:8443")
            self.assertTrue(companion.status_payload()["proxy_configured"])
            self.assertEqual(companion.status_payload()["proxy_scheme"], "https")

    def test_raw_actions_can_be_queued_without_running_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.enqueue_command(
                {
                    "action": "chat",
                    "prompt": "排队解释 Figure 2",
                    "_queue_raw": True,
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                }
            )
            self.assertTrue(result["ok"])

            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["pending"], 1)
            command = queued["commands"][0]
            self.assertEqual(command["rawAction"], "chat")
            self.assertEqual(command["prompt"], "排队解释 Figure 2")
            self.assertNotIn("cards", command)

            goal_result = companion.enqueue_command(
                {
                    "action": "goal_run",
                    "prompt": "目标：继续完成讲解\n生成讲稿和脑图",
                    "_queue_raw": True,
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                }
            )
            self.assertTrue(goal_result["ok"])
            queued_after_goal = companion.poll_commands("T1", "B1")
            self.assertEqual(queued_after_goal["pending"], 2)
            self.assertEqual(queued_after_goal["commands"][1]["rawAction"], "goal_run")

    def test_queue_rejects_and_ignores_malformed_commands(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            rejected = companion.enqueue_command(
                {
                    "action": "unsupported_action",
                    "_queue_raw": True,
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                }
            )
            self.assertFalse(rejected["ok"])
            self.assertIn("unsupported", rejected["message"])

            path = companion.queue_path("T1", "B1")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "id": "BAD1",
                        "topicid": "T1",
                        "bookmd5": "B1",
                        "command": {"ok": True, "message": "queued command"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            polled = companion.poll_commands("T1", "B1")
            self.assertEqual(polled["pending"], 0)
            self.assertEqual(polled["commands"], [])
            self.assertFalse(polled["hasCommand"])
            status = companion.queue_status_payload()
            self.assertEqual(status["pending"], 0)

    def test_request_pdf_cache_queues_native_upload_command_for_plugin_poll(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            source = Path(tmp) / "source.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            companion.KNOWN_PDF_PATHS = {"BOOK1": source}
            companion.cache_pdf_from_source_path = lambda payload, candidate: None

            result = companion.handle_action(
                {
                    "action": "request_pdf_cache",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "cache_pdf_from_current_document")
            self.assertEqual(result["queued"]["command"]["pdfPath"], str(source))
            self.assertIn(str(source), result["queued"]["command"]["pdfPathCandidates"])
            self.assertEqual(result["queue"]["pending"], 1)

            polled = companion.poll_commands("TOPIC1", "BOOK1")

            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "cache_pdf_from_current_document")
            self.assertEqual(polled["commands"][0]["pdfPath"], str(source))
            self.assertIn(str(source), polled["commands"][0]["pdfPathCandidates"])

    def test_request_pdf_cache_caches_readable_source_without_native_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            source = Path(tmp) / "source.pdf"
            source.write_bytes(b"%PDF-1.4\nreadable backend source\n%%EOF\n")
            companion.KNOWN_PDF_PATHS = {"BOOK1": source}

            result = companion.handle_action(
                {
                    "action": "request_pdf_cache",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["pdfCache"]["state"], "cached")
            self.assertEqual(result["queue"]["pending"], 0)
            self.assertTrue(Path(result["pdfCache"]["path"]).is_file())
            self.assertEqual(Path(result["pdfCache"]["path"]).read_bytes(), source.read_bytes())
            self.assertNotIn("queued", result)

    def test_queue_status_exposes_pending_pdf_cache_progress(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.cache_pdf_from_source_path = lambda payload, candidate: None

            result = companion.handle_action(
                {
                    "action": "request_pdf_cache",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "documentTitle": "Ding 等 2025. Fast and Robust Visuomotor Riemannian Flow Matching Policy.pdf",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["pdfCache"]["state"], "waiting_native")
            self.assertTrue(result["pdfCache"]["pending"])
            self.assertIn("MN4", result["pdfCache"]["label"])

            status = companion.queue_status_payload("TOPIC1", "BOOK1")

            self.assertEqual(status["pending"], 1)
            self.assertEqual(status["pdfCache"]["state"], "waiting_native")
            self.assertTrue(status["pdfCache"]["pending"])
            self.assertIn("保持当前 PDF 打开", status["pdfCache"]["detail"])

    def test_cache_pdf_from_marginnote_marks_pdf_cache_ready_in_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

            result = companion.handle_action(
                {
                    "action": "cache_pdf_from_marginnote",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "fileName": "cached.pdf",
                    "pdfBase64": base64.b64encode(pdf_bytes).decode("ascii"),
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["pdfCache"]["state"], "cached")
            self.assertFalse(result["pdfCache"]["pending"])
            self.assertTrue(Path(result["pdfCache"]["path"]).is_file())

            status = companion.queue_status_payload("TOPIC1", "BOOK1")

            self.assertEqual(status["pdfCache"]["state"], "cached")
            self.assertEqual(status["pdfCache"]["path"], result["pdfCache"]["path"])
            self.assertIn("已就绪", status["pdfCache"]["label"])

    def test_cache_pdf_success_clears_stale_native_cache_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.enqueue_command(
                {
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "command": {
                        "nativeAction": "cache_pdf_from_current_document",
                        "message": "cache stale pdf",
                    },
                }
            )
            self.assertEqual(companion.poll_commands("TOPIC1", "BOOK1")["pending"], 1)

            result = companion.handle_action(
                {
                    "action": "cache_pdf_from_marginnote",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "fileName": "source.pdf",
                    "pdfBase64": base64.b64encode(b"%PDF-1.4\ncached\n").decode("ascii"),
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(companion.poll_commands("TOPIC1", "BOOK1")["pending"], 0)

    def test_request_pdf_cache_queues_document_title_candidates_without_pdf_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            file_root = Path(tmp) / "managed-files"
            file_root.mkdir()
            source = file_root / "Yuan 等 2026. Qwen-RobotManip Technical Report.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            companion.DB_PATH = Path(tmp) / "missing.sqlite"
            companion.MN_DOC_ROOTS = []
            companion.MN_DOC_CACHE_ROOTS = []
            companion.ONEDRIVE_PDF_ROOTS = []
            companion.cloud_storage_pdf_roots = lambda: []
            companion.save_runtime_settings({"fileSearchRoots": [str(file_root)]})
            companion.cache_pdf_from_source_path = lambda payload, candidate: None

            result = companion.handle_action(
                {
                    "action": "request_pdf_cache",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "documentTitle": "Yuan 等 2026. Qwen-RobotManip Technical Report.pdf",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "cache_pdf_from_current_document")
            self.assertEqual(result["queued"]["command"]["pdfPath"], str(source))
            self.assertIn(str(source), result["queued"]["command"]["pdfPathCandidates"])

    def test_request_pdf_cache_derives_candidates_when_backend_cannot_list_file_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            file_root = Path(tmp) / "managed-files"
            file_root.mkdir()
            companion.DB_PATH = Path(tmp) / "missing.sqlite"
            companion.MN_DOC_ROOTS = []
            companion.MN_DOC_CACHE_ROOTS = []
            companion.ONEDRIVE_PDF_ROOTS = []
            companion.cloud_storage_pdf_roots = lambda: []
            companion.iter_pdf_files_in_roots = lambda roots, max_files=5000: []
            companion.save_runtime_settings({"fileSearchRoots": [str(file_root)]})

            result = companion.handle_action(
                {
                    "action": "request_pdf_cache",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "documentTitle": (
                        "Liu et al. 2026. Safe online reinforcement learning with diffusion world model "
                        "and Langevin dynamics #1"
                    ),
                    "source": "unit-test",
                }
            )

            expected = file_root / (
                "Liu et al. 2026. Safe online reinforcement learning with diffusion world model "
                "and Langevin dynamics.pdf"
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "cache_pdf_from_current_document")
            self.assertEqual(result["queued"]["command"]["pdfPath"], str(expected))
            self.assertIn(str(expected), result["queued"]["command"]["pdfPathCandidates"])

    def test_request_draft_write_queues_native_write_command_for_plugin_poll(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "notes"}})
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "draft": {
                        "ok": True,
                        "mnObject": {
                            "schema": "codex.mn.mnObject.v1",
                            "objectId": "mnobj:selection:draft123",
                            "kind": "selection",
                            "title": "PDF 选区",
                            "sourceRef": {"page": 4, "quote": "draft source"},
                        },
                        "mindmap": {
                            "title": "验收根节点",
                            "mergeIntoSelected": True,
                            "children": [{"title": "MERGE_NODE_OK_0612", "body": "同文档合并验收"}],
                        },
                    },
                }
            )

            result = companion.handle_action(
                {
                    "action": "request_draft_write",
                    "draftId": saved["draft"]["id"],
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "write_draft")
            self.assertEqual(result["queued"]["command"]["draftId"], saved["draft"]["id"])
            self.assertEqual(result["queued"]["command"]["mnObjectId"], "mnobj:selection:draft123")
            self.assertEqual(result["queued"]["command"]["mnObjectKind"], "selection")
            self.assertEqual(result["queued"]["command"]["mnObjectSourceRef"]["quote"], "draft source")
            self.assertEqual(result["queue"]["pending"], 1)
            self.assertIn(result["dryRun"]["status"], {"ready", "unknown"})

            polled = companion.poll_commands("TOPIC1", "BOOK1")

            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "write_draft")
            self.assertEqual(polled["commands"][0]["draftId"], saved["draft"]["id"])
            self.assertEqual(polled["commands"][0]["mnObjectId"], "mnobj:selection:draft123")

    def test_request_draft_write_blocks_read_only_permission_before_native_queue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "read_only"}})
            saved = companion.save_draft(
                {
                    "action": "draft_save",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "draft": {
                        "ok": True,
                        "cards": [{"title": "Blocked card", "body": "Should not be queued."}],
                    },
                }
            )

            result = companion.handle_action(
                {
                    "action": "request_draft_write",
                    "draftId": saved["draft"]["id"],
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertFalse(result["ok"])
            self.assertEqual(result["dryRun"]["status"], "blocked")
            self.assertEqual(result["dryRun"]["checks"][0]["reason"], "read-only-permission")
            self.assertIn("写入草稿已阻断", result["reply"])
            self.assertEqual(companion.queue_status_payload("TOPIC1", "BOOK1")["pending"], 0)

    def test_request_native_capability_probe_queues_plugin_probe_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action(
                {
                    "action": "request_native_capability_probe",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "probe_native_api_capabilities")
            self.assertIn("刷新 MN 原生能力", result["message"])
            polled = companion.poll_commands("TOPIC1", "BOOK1")
            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "probe_native_api_capabilities")

    def test_request_web_panel_reload_queues_native_panel_reload_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            result = companion.handle_action(
                {
                    "action": "request_web_panel_reload",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "reload_web_panel")
            self.assertIn("重新加载 Codex 面板", result["message"])
            polled = companion.poll_commands("TOPIC1", "BOOK1")
            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "reload_web_panel")

    def test_collect_mn_runtime_evidence_writes_json_without_quitting_mn4(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.ONEDRIVE_COMPANION_DIR = Path(tmp) / "OneDrive/Codex Companion"
            calls: list[list[str]] = []

            class FakeCompleted:
                returncode = 0
                stdout = "[OK] fake doctor\n"
                stderr = ""

            old_run = companion.subprocess.run

            def fake_run(cmd: list[str], **kwargs: Any) -> FakeCompleted:
                calls.append([str(item) for item in cmd])
                return FakeCompleted()

            companion.subprocess.run = fake_run
            try:
                result = companion.handle_action(
                    {
                        "action": "collect_mn_runtime_evidence",
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "source": "unit-test",
                        "waitSeconds": 0,
                    }
                )
            finally:
                companion.subprocess.run = old_run

            self.assertTrue(result["ok"])
            self.assertIn("evidencePath", result)
            evidence_path = Path(result["evidencePath"])
            self.assertTrue(evidence_path.exists())
            payload = json.loads(evidence_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["topicid"], "TOPIC1")
            self.assertEqual(payload["bookmd5"], "BOOK1")
            self.assertIn("mnRuntime", payload)
            self.assertIn("nativeApiCapabilities", payload)
            self.assertIn("probeResult", payload)
            self.assertEqual(payload["doctor"]["doctorReturnCode"], 0)
            self.assertEqual(payload["probeResult"]["queued"]["command"]["nativeAction"], "probe_native_api_capabilities")
            self.assertIn("MN4 运行态证据", result["reply"])
            combined = json.dumps(payload, ensure_ascii=False) + result["reply"] + " ".join(" ".join(call) for call in calls)
            self.assertNotIn("killall", combined)
            self.assertNotIn("quit MarginNote", combined)
            self.assertNotIn("osascript -e 'quit", combined)

    def test_collect_mn_runtime_evidence_classifies_doctor_permission_issue(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.ONEDRIVE_COMPANION_DIR = Path(tmp) / "OneDrive/Codex Companion"

            class FakeCompleted:
                returncode = 1
                stdout = ""
                stderr = (
                    "PermissionError: [Errno 1] Operation not permitted: "
                    "'/Users/liuwhale/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion.zip'"
                )

            old_run = companion.subprocess.run

            def fake_run(cmd: list[str], **kwargs: Any) -> FakeCompleted:
                return FakeCompleted()

            companion.subprocess.run = fake_run
            try:
                result = companion.handle_action(
                    {
                        "action": "collect_mn_runtime_evidence",
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "waitSeconds": 0,
                    }
                )
            finally:
                companion.subprocess.run = old_run

            payload = json.loads(Path(result["evidencePath"]).read_text(encoding="utf-8"))
            self.assertTrue(payload["doctor"]["doctorPermissionIssue"])
            self.assertTrue(result["doctor"]["doctorPermissionIssue"])
            self.assertIn("OneDrive", result["doctor"]["doctorPermissionPath"])
            self.assertIn("Full Disk Access", result["reply"])
            self.assertIn("运行态证据", result["reply"])

    def test_request_native_highlight_selection_queues_mn4_highlight_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "full"}})

            result = companion.handle_action(
                {
                    "action": "request_native_highlight_selection",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "selectionText": "Attention-Guided Safety Filter",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "highlight_current_selection")
            self.assertEqual(result["queued"]["command"]["selectionText"], "Attention-Guided Safety Filter")
            self.assertTrue(result["queued"]["command"]["armIfMissingSelection"])
            self.assertTrue(result["queued"]["command"]["preferNextSelection"])
            self.assertIn("下一次 PDF 选区", result["reply"])
            self.assertIn("先进入等待模式", result["reply"])
            self.assertEqual(result["queue"]["pending"], 1)

            polled = companion.poll_commands("TOPIC1", "BOOK1")

            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "highlight_current_selection")
            self.assertEqual(polled["commands"][0]["selectionText"], "Attention-Guided Safety Filter")
            self.assertTrue(polled["commands"][0]["armIfMissingSelection"])
            self.assertTrue(polled["commands"][0]["preferNextSelection"])

    def test_native_highlight_wizard_start_arms_next_selection_and_reports_waiting_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "settings_update", "settings": {"permission": "full"}})

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_start",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "waiting_selection")
            self.assertEqual(wizard["topicid"], "TOPIC1")
            self.assertEqual(wizard["bookmd5"], "BOOK1")
            self.assertEqual(wizard["timeoutSeconds"], 90)
            self.assertIn("回到 PDF", wizard["instruction"])
            self.assertEqual(result["queued"]["command"]["nativeAction"], "highlight_current_selection")
            self.assertTrue(result["queued"]["command"]["armIfMissingSelection"])
            self.assertEqual(result["queue"]["pending"], 1)

    def test_native_highlight_wizard_status_summarizes_single_document_blockers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.EVENTS_PATH.write_text(
                json.dumps(
                    {
                        "event": "nativeHighlightNextSelectionArmed",
                        "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "extra": {"reason": "missing-selection"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_status",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            self.assertTrue(result["ok"])
            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "waiting_selection")
            self.assertFalse(wizard["visibleHighlightReady"])
            self.assertFalse(wizard["selectionPopupReady"])
            self.assertIn("native_highlight_visible", wizard["blockedChecks"])
            self.assertIn("selection_popup_highlight", wizard["blockedChecks"])

    def test_native_highlight_wizard_status_expires_stale_waiting_selection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.EVENTS_PATH.write_text(
                json.dumps(
                    {
                        "ts": "2000-01-01T00:00:00+0800",
                        "event": "nativeHighlightNextSelectionArmed",
                        "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "extra": {"reason": "missing-selection"},
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_status",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "expired")
            self.assertGreater(wizard["latestEventAgeSeconds"], wizard["timeoutSeconds"])
            self.assertIn("超时", wizard["instruction"])
            self.assertIn("重新启动", result["reply"])

    def test_native_highlight_wizard_status_surfaces_selection_popup_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.EVENTS_PATH.write_text(
                json.dumps(
                    {
                        "event": "selectionPopupHighlightNotificationSkipped",
                        "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "extra": {
                            "reason": "outside-window",
                            "hasDocumentController": True,
                            "selectionLength": 18,
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_status",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "selection_diagnostic")
            self.assertEqual(wizard["latestEvent"]["event"], "selectionPopupHighlightNotificationSkipped")
            self.assertEqual(wizard["latestEvent"]["extra"]["reason"], "outside-window")
            self.assertIn("窗口过滤", wizard["instruction"])

    def test_native_highlight_wizard_status_reports_registered_observer_waiting_for_popup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.EVENTS_PATH.write_text(
                json.dumps(
                    {
                        "event": "selectionPopupHighlightObserverRegistered",
                        "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "extra": {
                            "source": "sceneWillConnect",
                            "notificationName": "PopupMenuOnSelection",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_status",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "waiting_selection")
            self.assertEqual(wizard["latestEvent"]["event"], "selectionPopupHighlightObserverRegistered")
            self.assertIn("observer", wizard["instruction"])
            self.assertIn("PDF 选区通知", wizard["instruction"])

    def test_native_highlight_wizard_status_surfaces_selection_poll_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.EVENTS_PATH.write_text(
                json.dumps(
                    {
                        "event": "nativeHighlightNextSelectionPollExpired",
                        "pluginVersion": companion.CURRENT_PLUGIN_VERSION,
                        "topicid": "TOPIC1",
                        "bookmd5": "BOOK1",
                        "extra": {"reason": "missing-selection", "elapsedSeconds": 91},
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )

            result = companion.handle_action(
                {
                    "action": "native_highlight_wizard_status",
                    "topicid": "TOPIC1",
                    "bookmd5": "BOOK1",
                    "source": "unit-test",
                }
            )

            wizard = result["nativeHighlightWizard"]
            self.assertEqual(wizard["stage"], "expired")
            self.assertEqual(wizard["latestEvent"]["event"], "nativeHighlightNextSelectionPollExpired")
            self.assertIn("主动轮询", wizard["instruction"])

    def test_web_busy_lock_keeps_pending_commands_until_current_task_finishes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.enqueue_command(
                {
                    "action": "chat",
                    "prompt": "排队解释 Figure 2",
                    "_queue_raw": True,
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "unittest",
                }
            )

            locked = companion.handle_action({"action": "web_busy_update", "busy": True})
            self.assertTrue(locked["ok"])
            blocked = companion.poll_commands("T1", "B1")
            self.assertEqual(blocked["pending"], 1)
            self.assertEqual(blocked["commands"], [])
            self.assertEqual(blocked["blocked"], "web_busy")

            unlocked = companion.handle_action({"action": "web_busy_update", "busy": False})
            self.assertTrue(unlocked["ok"])
            ready = companion.poll_commands("T1", "B1")
            self.assertEqual(ready["pending"], 1)
            self.assertEqual(ready["commands"][0]["rawAction"], "chat")

    def test_web_panel_direct_generation_auto_queues_when_backend_busy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "web_busy_update", "busy": True})
            calls: list[str] = []

            def fail_generate_mindmap(payload: dict[str, Any]) -> dict[str, Any]:
                calls.append("generate_mindmap")
                raise AssertionError("web-busy direct actions must enqueue instead of generating")

            companion.generate_mindmap = fail_generate_mindmap

            result = companion.handle_action(
                {
                    "action": "generate_mindmap",
                    "prompt": "生成脑图",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "marginnote4-web-panel",
                }
            )

            self.assertTrue(result["ok"])
            self.assertTrue(result["queued_due_to_web_busy"])
            self.assertEqual(calls, [])
            self.assertIn("队列", result["message"])
            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["pending"], 1)
            self.assertEqual(queued["blocked"], "web_busy")
            companion.handle_action({"action": "web_busy_update", "busy": False})
            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["pending"], 1)
            self.assertEqual(queued["commands"][0]["rawAction"], "generate_mindmap")

    def test_web_panel_direct_chat_auto_queues_when_backend_busy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "web_busy_update", "busy": True})
            calls: list[str] = []

            def fail_chat(payload: dict[str, Any]) -> dict[str, Any]:
                calls.append("chat")
                raise AssertionError("web-busy chat must enqueue instead of running")

            companion.chat = fail_chat

            result = companion.handle_action(
                {
                    "action": "chat",
                    "prompt": "发送按钮问题",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "marginnote4-web-panel",
                }
            )

            self.assertTrue(result["ok"])
            self.assertTrue(result["queued_due_to_web_busy"])
            self.assertEqual(calls, [])
            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["pending"], 1)
            companion.handle_action({"action": "web_busy_update", "busy": False})
            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["commands"][0]["rawAction"], "chat")

    def test_web_panel_lock_owner_runs_current_direct_action_instead_of_queueing_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            companion.handle_action({"action": "web_busy_update", "busy": True})
            calls: list[str] = []

            def fake_chat(payload: dict[str, Any]) -> dict[str, Any]:
                calls.append(str(payload.get("prompt") or ""))
                return {"ok": True, "message": "answered", "reply": "ok"}

            companion.chat = fake_chat

            result = companion.handle_action(
                {
                    "action": "chat",
                    "prompt": "本次发送按钮请求",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "marginnote4-web-panel",
                    "_web_run_owner": True,
                }
            )

            self.assertTrue(result["ok"])
            self.assertNotIn("queued_due_to_web_busy", result)
            self.assertEqual(calls, ["本次发送按钮请求"])
            queued = companion.poll_commands("T1", "B1")
            self.assertEqual(queued["pending"], 0)

    def test_first_web_panel_direct_generation_claims_backend_busy_lock(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))
            calls: list[str] = []

            def fake_generate_mindmap(payload: dict[str, Any]) -> dict[str, Any]:
                calls.append("generate_mindmap")
                return {"ok": True, "message": "generated", "reply": "ok", "mindmap": {"title": "T"}}

            companion.generate_mindmap = fake_generate_mindmap

            result = companion.handle_action(
                {
                    "action": "generate_mindmap",
                    "prompt": "生成脑图",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "source": "marginnote4-web-panel",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(calls, ["generate_mindmap"])
            self.assertTrue(companion.web_busy_status()["busy"])

    def test_ai_edit_events_persist_transaction_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_event(
                {
                    "event": "aiEditTransactionStarted",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-integration",
                        "draftId": "draft-integration",
                        "cards": 1,
                        "hasMindmap": True,
                        "mnObjectId": "mnobj:selection:tx123",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "PDF 选区",
                        "mnObjectSourceRef": {"page": 2, "quote": "selected source"},
                    },
                }
            )
            companion.append_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-integration",
                        "draftId": "draft-integration",
                        "createdNoteIds": ["N1", "N2"],
                        "createdCount": 2,
                        "card_count": 1,
                        "has_mindmap": True,
                    },
                }
            )
            companion.append_event(
                {
                    "event": "aiEditTransactionRejected",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-integration",
                        "ok": True,
                        "deleted": 2,
                        "failed": 0,
                    },
                }
            )

            status = companion.status_payload()
            transactions = status["aiEditTransactions"]
            self.assertEqual(transactions["count"], 1)
            self.assertEqual(transactions["items"][0]["transactionId"], "ai-edit-integration")
            self.assertEqual(transactions["items"][0]["status"], "rolled_back")
            self.assertEqual(transactions["items"][0]["deletedCount"], 2)
            self.assertEqual(transactions["items"][0]["objectRef"]["objectId"], "mnobj:selection:tx123")

            listed = companion.handle_action(
                {"action": "ai_edit_transaction_list", "topicid": "T1", "bookmd5": "B1"}
            )
            self.assertTrue(listed["ok"])
            self.assertEqual(listed["transactions"]["count"], 1)
            self.assertEqual(listed["transactions"]["items"][0]["objectRef"]["kind"], "selection")

            loaded = companion.handle_action(
                {"action": "ai_edit_transaction_get", "transactionId": "ai-edit-integration"}
            )
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["transaction"]["createdNoteIds"], ["N1", "N2"])
            self.assertEqual(loaded["transaction"]["objectRef"]["sourceRef"]["quote"], "selected source")

            verified = companion.handle_action(
                {"action": "ai_edit_transaction_verify", "transactionId": "ai-edit-integration"}
            )
            self.assertTrue(verified["ok"])
            self.assertEqual(verified["verification"]["schema"], "codex.mn.aiEditVerification.v1")
            self.assertEqual(verified["verification"]["status"], "pass")
            self.assertEqual(verified["verification"]["objectRef"]["objectId"], "mnobj:selection:tx123")
            self.assertIn("回滚验证", verified["reply"])

    def test_status_exposes_latest_ai_edit_transaction_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion(Path(tmp))

            companion.append_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-latest",
                        "draftId": "draft-latest",
                        "createdNoteIds": ["N1", "N2", "N3"],
                        "createdCount": 3,
                        "card_count": 2,
                        "has_mindmap": True,
                        "mindmap_title": "目标脑图",
                        "mnObjectId": "mnobj:note:latest123",
                        "mnObjectKind": "note",
                        "mnObjectTitle": "当前章节",
                    },
                }
            )
            companion.append_event(
                {
                    "event": "aiEditTransactionRejected",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-latest",
                        "ok": False,
                        "deleted": 1,
                        "failed": 2,
                        "failures": [
                            {"noteId": "N2", "reason": "still-exists"},
                            {"noteId": "N3", "reason": "still-exists"},
                        ],
                    },
                }
            )

            status = companion.status_payload()
            tx_status = status["aiEditTransactionStatus"]
            self.assertEqual(tx_status["schema"], "codex.mn.aiEditTransactionStatus.v1")
            self.assertTrue(tx_status["available"])
            self.assertEqual(tx_status["latest"]["transactionId"], "ai-edit-latest")
            self.assertEqual(tx_status["latest"]["createdNoteIds"], ["N1", "N2", "N3"])
            self.assertEqual(tx_status["latest"]["objectRef"]["objectId"], "mnobj:note:latest123")
            self.assertEqual(tx_status["verification"]["status"], "block")
            self.assertEqual(tx_status["verification"]["objectRef"]["kind"], "note")
            self.assertEqual(tx_status["verification"]["remainingNoteIds"], ["N2", "N3"])
            self.assertIn("仍可能残留", tx_status["summary"])


if __name__ == "__main__":
    unittest.main()
