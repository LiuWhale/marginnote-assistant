from __future__ import annotations

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
                "mindmap": {"title": "Root", "children": []},
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
            loaded = companion.load_draft(saved["draft"]["id"])
            self.assertTrue(loaded["ok"])
            self.assertEqual(loaded["cards"][0]["title"], "T")
            self.assertEqual(loaded["mindmap"]["title"], "Root")

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
            )

            self.assertTrue(started["active"])
            queue = companion.queue_status_payload("T1", "B1")
            self.assertTrue(queue["run"]["active"])
            self.assertEqual(queue["run"]["action"], "chat")
            self.assertEqual(queue["run"]["stage"], "正在询问 Codex")
            self.assertEqual(queue["run"]["detail"], "模型正在生成回答")
            self.assertEqual(queue["run"]["queue_id"], "Q1")
            self.assertGreaterEqual(queue["run"]["elapsed_seconds"], 0)
            self.assertEqual(companion.status_payload()["run"]["action"], "chat")
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
                "native-highlight-arm-next-selection-default\nnative-highlight-prefer-next-selection-v1\nnative-highlight-command-prepared\nselection-popup-diagnostics-v1\nnative-highlight-selection-poll-v1\nselection-popup-scene-observer-v1\nselection-popup-notebook-rebind-v1\nnative-highlight-selection-text-resolver-v1\ncontext-refresh-clears-stale-selection-v1\nai-edit-transaction-rollback-v1\n",
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
                    "pluginVersion": "0.4.1",
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
                    "pluginVersion": "0.4.1",
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
                    "pluginVersion": "0.4.1",
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
                    "pluginVersion": "0.4.1",
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
                    "pluginVersion": "0.4.1",
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
                {"speed": "fast", "aiBackend": "codex_cli", "codexCliPath": "/tmp/codex", "model": "gpt-5.5"}
            )
            fake_home = Path(tmp) / "home"
            fake_home.joinpath(".codex").mkdir(parents=True)
            fake_home.joinpath(".codex/auth.json").write_text('{"token":"test"}', encoding="utf-8")
            companion.HOME = fake_home
            companion.codex_cli_status = lambda settings: {"available": True, "path": "/tmp/codex"}
            captured: dict[str, Any] = {}

            class FakeCompleted:
                returncode = 0
                stdout = ""
                stderr = ""

            def fake_run(args: list[str], **kwargs: Any) -> FakeCompleted:
                captured["args"] = args
                captured["timeout"] = kwargs.get("timeout")
                captured["env"] = kwargs.get("env")
                output_path = Path(args[args.index("--output-last-message") + 1])
                output_path.write_text("fast cli output", encoding="utf-8")
                return FakeCompleted()

            old_run = companion.subprocess.run
            companion.subprocess.run = fake_run
            try:
                text, backend = companion.call_codex_cli({"prompt": "生成脑图"}, "generate_mindmap")
            finally:
                companion.subprocess.run = old_run

            self.assertEqual(text, "fast cli output")
            self.assertEqual(backend, "codex-cli")
            self.assertEqual(captured["timeout"], 75)
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
            self.assertTrue((companion.CODEX_LITE_HOME / "auth.json").exists())

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
                    "latestVersion": "0.4.2",
                    "assetName": "CodexCompanion-0.4.2-latest-dist.zip",
                    "downloadUrl": "https://example/CodexCompanion-0.4.2-latest-dist.zip",
                    "message": "发现新版本 0.4.2。",
                }

            def fake_install(root: Path, settings: dict[str, Any], current_version: str) -> dict[str, Any]:
                calls.append("install:" + settings["githubRepo"])
                return {
                    "ok": True,
                    "state": "installing",
                    "repo": settings["githubRepo"],
                    "currentVersion": current_version,
                    "latestVersion": "0.4.2",
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
            self.assertEqual(status["update"]["latestVersion"], "0.4.2")

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
            self.assertEqual(result["queue"]["pending"], 1)

            polled = companion.poll_commands("TOPIC1", "BOOK1")

            self.assertEqual(polled["pending"], 1)
            self.assertEqual(polled["commands"][0]["nativeAction"], "write_draft")
            self.assertEqual(polled["commands"][0]["draftId"], saved["draft"]["id"])

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


if __name__ == "__main__":
    unittest.main()
