from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from typing import Any


DOCTOR_PATH = Path(__file__).resolve().parents[1] / "doctor.py"


def load_doctor() -> Any:
    spec = importlib.util.spec_from_file_location("codex_mn_doctor_checks", DOCTOR_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class DoctorNativeApiChecks(unittest.TestCase):
    def test_required_native_handler_features_cover_v2_object_workbench_actions(self) -> None:
        doctor = load_doctor()

        for feature in [
            "native-mn-object-registry-scan-v1",
            "native-mn-object-existence-probe-v1",
            "native-mindmap-diff-apply-create-v1",
            "native-mindmap-delete-suggestion-confirm-v1",
        ]:
            self.assertIn(feature, doctor.REQUIRED_NATIVE_HANDLER_FEATURES)

    def write_zip(self, path: Path, entries: dict[str, str]) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            for name, content in entries.items():
                archive.writestr(name, content)

    def test_companion_service_uses_lightweight_health_when_status_is_slow(self) -> None:
        doctor = load_doctor()
        calls: list[str] = []

        class FakeResponse:
            def __init__(self, payload: dict[str, Any]) -> None:
                self.payload = payload

            def __enter__(self) -> "FakeResponse":
                return self

            def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
                return False

            def read(self) -> bytes:
                return json.dumps(self.payload).encode("utf-8")

        def fake_urlopen(url: str, timeout: float = 5) -> FakeResponse:
            calls.append(str(url))
            if str(url).endswith("/health"):
                return FakeResponse({"ok": True, "message": "alive"})
            if str(url).endswith("/status"):
                raise TimeoutError("status payload is slow")
            raise AssertionError(f"unexpected url {url}")

        doctor.request.urlopen = fake_urlopen

        check = doctor.check_companion()

        self.assertEqual(check.status, "OK")
        self.assertIn("/health", calls[0])
        self.assertIn("/status", calls[1])
        self.assertIn("status=unavailable", check.detail)

    def test_runtime_web_controls_require_current_button_layout_regions(self) -> None:
        doctor = load_doctor()

        for control_id in [
            "aiChatShell",
            "modeSwitchBar",
            "chatModeButton",
            "agentWorkspaceModeButton",
            "modeIntentLine",
            "workspaceNavigator",
            "workspaceNavigatorSummary",
            "workspaceNavConsoleButton",
            "workspaceNavMindmapStudioButton",
            "workspaceNavCardFactoryButton",
            "workspaceNavLedgerExplorerButton",
            "workspaceNavKnowledgeGraphButton",
            "workspaceNavWorkflowBuilderButton",
            "workspaceNavSkillCenterButton",
            "notebookWorkspacePanel",
            "notebookWorkspaceTitle",
            "notebookWorkspaceSummary",
            "notebookWorkspaceRefreshButton",
            "notebookWorkspaceFocus",
            "notebookWorkspaceObjectCount",
            "notebookWorkspaceMindmap",
            "notebookWorkspaceReview",
            "notebookWorkspaceWorkflow",
            "notebookWorkspaceLedger",
            "notebookWorkspaceActions",
            "commandPanePanel",
            "commandPaneHeader",
            "commandPaneStatus",
            "commandPaneToggleButton",
            "commandPaneBody",
            "commandPaneComposer",
            "workbenchTabs",
            "workbenchTabObject",
            "workbenchTabOperation",
            "workbenchTabKnowledge",
            "workbenchTabWorkflow",
            "objectWorkspacePanel",
            "objectGraphPanel",
            "objectGraphRelationAddButton",
            "objectGraphRelationEditor",
            "objectGraphRelationTargetInput",
            "objectGraphRelationTypeInput",
            "objectGraphRelationLabelInput",
            "objectGraphRelationNoteInput",
            "objectGraphRelationSaveButton",
            "objectGraphRelationCancelButton",
            "objectActivityPanel",
            "operationLedgerPanel",
            "operationWorkspacePanel",
            "operationCompilerPanel",
            "operationCompilerSummary",
            "operationPlanStats",
            "operationCompilerChecks",
            "operationDryRunDetails",
            "operationCompilerRepairActions",
            "operationWorkspaceNextActions",
            "mindmapStudioPanel",
            "mindmapStudioSummary",
            "mindmapStudioCurrentTree",
            "mindmapStudioDiffStage",
            "mindmapStudioApplyStage",
            "mindmapStudioTransactionStage",
            "mindmapStudioReadTreeButton",
            "mindmapStudioPreviewDiffButton",
            "mindmapStudioApplySelectedButton",
            "mindmapStudioVerifyButton",
            "mindmapStudioRollbackButton",
            "mindmapStudioStatusLine",
            "knowledgeWorkspacePanel",
            "workflowWorkspacePanel",
            "agentWorkbenchBar",
            "mindmapDiffWorkbench",
            "aiEditTransactionCenter",
            "aiEditTransactionResidualProof",
            "promptInput",
            "sendButton",
            "stopButton",
            "contextButton",
            "contextScopeAutoButton",
            "contextScopeSelectionButton",
            "contextScopeDocumentButton",
            "closeButton",
            "liveHistory",
            "contextSourceLine",
            "aiReadinessLine",
            "aiReadinessDetail",
            "selectionPreview",
            "statusPill",
            "contextLine",
            "readinessPanel",
            "mnApiStatusLine",
        ]:
            self.assertIn(control_id, doctor.REQUIRED_WEB_CONTROL_IDS)
        for legacy_control_id in [
            "stagedActionLine",
            "runStagedActionButton",
            "clearStagedActionButton",
            "aiActionPanel",
            "nodeToolPanel",
            "workflowActionGrid",
            "workflowActionGroups",
            "goalActionPanel",
            "moreToolsPanel",
            "moreToolsSummary",
            "secondaryToolsPanel",
            "secondaryToolsSummary",
            "sourceActionPanel",
            "sourceActionGrid",
            "sourceToolGrid",
            "mindmapActionPanel",
            "mindmapToolGrid",
            "buttonCenterLayout",
            "goalRunPanel",
            "primaryActionGrid",
            "workflowActionPanel",
        ]:
            self.assertNotIn(legacy_control_id, doctor.REQUIRED_WEB_CONTROL_IDS)

    def test_runtime_source_files_include_current_web_css(self) -> None:
        doctor = load_doctor()

        sources = [str(path) for path in doctor.runtime_source_files()]

        self.assertTrue(any(path.endswith("web/app.css") for path in sources))

    def test_doctor_reports_stale_runtime_web_controls_when_events_predate_installed_assets(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            (extension / "web/app.js").write_text("new controls\n", encoding="utf-8")
            controls = [item for item in doctor.REQUIRED_WEB_CONTROL_IDS if item != "nativeCapabilitiesLine"]
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T05:00:00+0800",
                        "event": "webControlsReady",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "controls": ",".join(controls),
                            "missing": "",
                            "minWidth": "390",
                            "minHeight": "520",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            os.utime(events, (1000, 1000))
            os.utime(extension / "web/app.js", (2000, 2000))
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = extension

            check = doctor.check_runtime_web_controls()

            self.assertEqual(check.status, "WARN")
            self.assertIn("stale", check.detail)
            self.assertTrue(check.evidence["staleRuntime"])

    def test_doctor_keeps_web_controls_stale_when_later_unrelated_events_touch_log(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            (extension / "web/app.js").write_text("new controls\n", encoding="utf-8")
            controls = [item for item in doctor.REQUIRED_WEB_CONTROL_IDS if item not in {"nativeCapabilitiesLine", "runStateLine"}]
            rows = [
                {
                    "ts": "2026-06-11T03:34:34+0800",
                    "event": "webControlsReady",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "controls": ",".join(controls),
                        "missing": "",
                        "minWidth": "390",
                        "minHeight": "520",
                    },
                },
                {
                    "ts": "2026-06-11T06:38:55+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            os.utime(events, (1781131135, 1781131135))
            os.utime(extension / "web/app.js", (1781130900, 1781130900))
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = extension

            check = doctor.check_runtime_web_controls()

            self.assertEqual(check.status, "WARN")
            self.assertIn("stale runtime event", check.detail)
            self.assertTrue(check.evidence["staleRuntime"])

    def test_runtime_web_controls_report_reload_panel_unknown_as_handler_stale(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            (extension / "main.js").write_text("current runtime\n", encoding="utf-8")
            controls = list(doctor.REQUIRED_WEB_CONTROL_IDS)
            rows = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "controls": ",".join(controls),
                        "missing": "",
                        "minWidth": "390",
                        "minHeight": "520",
                    },
                },
                {
                    "ts": "2026-06-11T13:10:08+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "reload_web_panel"},
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            os.utime(extension / "main.js", (1_000, 1_000))
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = extension

            check = doctor.check_runtime_web_controls()

            self.assertEqual(check.status, "WARN")
            self.assertIn("reload_web_panel", check.detail)
            self.assertTrue(check.evidence["runtimeHandlerStale"])
            self.assertIn("reload_web_panel", check.evidence["runtimeHandlerStaleActions"])

    def test_database_check_reports_general_codex_content_not_park_template_counts(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db)
            try:
                conn.execute(
                    "create table ZBOOKNOTE (ZTOPICID text, ZBOOKMD5 text, ZNOTETITLE text, ZCOMMENT text, ZHIGHLIGHTS blob)"
                )
                rows = [
                    ("T1", "B1", "Codex短卡 01：主线", "<!--codex-paper-companion:{\"codexId\":\"full-reading:card:01\"}-->", None),
                    ("T1", "B1", "Codex 脑图：当前材料", "<!--codex-paper-companion:{\"codexId\":\"full-reading:mindmap:root\"}-->", None),
                    ("T1", "B1", "Codex高亮：选区", "", None),
                ]
                conn.executemany("insert into ZBOOKNOTE values (?, ?, ?, ?, ?)", rows)
                conn.commit()
            finally:
                conn.close()
            doctor.DB_PATH = db

            check = doctor.check_database()

            self.assertEqual(check.name, "MN4 Codex content")
            self.assertEqual(check.status, "OK")
            self.assertIn("codex_notes=3", check.detail)
            self.assertIn("cards=1", check.detail)
            self.assertIn("mindmap_nodes=1", check.detail)
            self.assertIn("highlight_nodes=1", check.detail)
            self.assertNotIn("KNOWS", check.detail)
            self.assertNotIn("Park", check.name + check.detail)
            self.assertEqual(check.evidence["codexNotes"], 3)

    def test_database_check_warns_without_codex_content_using_general_wording(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db)
            try:
                conn.execute("create table ZBOOKNOTE (ZTOPICID text, ZBOOKMD5 text, ZNOTETITLE text)")
                conn.execute("insert into ZBOOKNOTE values ('T1', 'B1', '普通笔记')")
                conn.commit()
            finally:
                conn.close()
            doctor.DB_PATH = db

            check = doctor.check_database()

            self.assertEqual(check.name, "MN4 Codex content")
            self.assertEqual(check.status, "WARN")
            self.assertIn("codex_notes=0", check.detail)
            self.assertNotIn("KNOWS", check.detail)

    def test_native_highlight_warning_uses_general_validation_wording(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db)
            try:
                conn.execute("create table ZBOOKNOTE (ZBOOKMD5 text, ZTOPICID text, ZHIGHLIGHTS blob)")
                conn.commit()
            finally:
                conn.close()
            doctor.DB_PATH = db

            check = doctor.check_native_highlights()

            self.assertEqual(check.name, "Native highlight blobs")
            self.assertEqual(check.status, "WARN")
            self.assertIn("visible native highlights are not proven", check.detail)
            self.assertNotIn("Park", check.detail)
            self.assertNotIn("KNOWS", check.detail)

    def test_native_highlight_ok_includes_scope_evidence(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db)
            try:
                conn.execute("create table ZBOOKNOTE (ZBOOKMD5 text, ZTOPICID text, ZHIGHLIGHTS blob)")
                conn.execute(
                    "insert into ZBOOKNOTE values (?, ?, ?)",
                    (doctor.NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5, doctor.NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID, b"blob"),
                )
                conn.commit()
            finally:
                conn.close()
            doctor.DB_PATH = db

            check = doctor.check_native_highlights()

            self.assertEqual(check.status, "OK")
            self.assertEqual(check.evidence["native_highlight_blobs"], 1)
            self.assertEqual(check.evidence["topicid"], doctor.NATIVE_HIGHLIGHT_VALIDATION_TOPIC_ID)
            self.assertEqual(check.evidence["bookmd5"], doctor.NATIVE_HIGHLIGHT_VALIDATION_BOOK_MD5)

    def test_doctor_requires_ai_chat_core_control_in_runtime_webview(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            extension = root / "extension"
            (extension / "web").mkdir(parents=True)
            (extension / "web/app.js").write_text("installed controls\n", encoding="utf-8")
            os.utime(extension / "web/app.js", (1781120000, 1781120000))
            controls = [item for item in doctor.REQUIRED_WEB_CONTROL_IDS if item != "aiChatShell"]
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T05:00:00+0800",
                        "event": "webControlsReady",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "controls": ",".join(controls),
                            "missing": "",
                            "minWidth": "390",
                            "minHeight": "520",
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = extension

            check = doctor.check_runtime_web_controls()

            self.assertEqual(check.status, "FAIL")
            self.assertIn("aiChatShell", check.detail)

    def test_doctor_marks_native_api_probe_stale_when_events_predate_installed_assets(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events = root / "events.jsonl"
            extension = root / "extension"
            extension.mkdir()
            (extension / "main.js").write_text("new capability matrix\n", encoding="utf-8")
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T03:34:36+0800",
                        "event": "nativeApiCapabilities",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "hasNativeHighlightCandidate": False,
                            "hasAnnotatedExportCandidate": False,
                            "candidateMethods": [],
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            os.utime(events, (1000, 1000))
            os.utime(extension / "main.js", (2000, 2000))
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = extension

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("stale", check.detail)
            self.assertTrue(check.evidence["staleRuntime"])

    def test_doctor_reports_latest_native_api_capability_event(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T01:30:00+0800",
                        "event": "nativeApiCapabilities",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "hasNativeHighlightCandidate": True,
                            "hasAnnotatedExportCandidate": False,
                            "candidateMethods": ["studyController.AppendHighlight"],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                            ],
                            "capabilityMatrix": {
                                "nativeHighlightSelection": {
                                    "label": "原生高亮当前 PDF 选区",
                                    "ready": True,
                                    "available": True,
                                    "entryAction": "request_native_highlight_selection",
                                }
                            },
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = Path(tmp) / "missing-extension"

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "OK")
            self.assertIn("highlight_candidate=True", check.detail)
            self.assertIn("export_candidate=False", check.detail)
            self.assertEqual(check.evidence["candidateMethods"], ["studyController.AppendHighlight"])

    def test_doctor_reports_ready_native_api_actions_from_capability_matrix(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T03:30:00+0800",
                        "event": "nativeApiCapabilities",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "hasNativeHighlightCandidate": True,
                            "hasAnnotatedExportCandidate": False,
                            "candidateMethods": ["selectionDocumentController.highlightFromSelection"],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                            ],
                            "capabilityMatrix": {
                                "nativeHighlightSelection": {
                                    "label": "原生高亮当前 PDF 选区",
                                    "ready": True,
                                    "available": True,
                                    "entryAction": "request_native_highlight_selection",
                                },
                                "annotatedPdfExport": {
                                    "label": "导出带标注 PDF 副本",
                                    "ready": False,
                                    "available": True,
                                    "entryAction": "export_annotated_pdf",
                                    "blockedReason": "needs-pdf-cache-or-path",
                                },
                            },
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = Path(tmp) / "missing-extension"

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "OK")
            self.assertIn("ready_actions=1", check.detail)
            self.assertIn("blocked_actions=1", check.detail)
            self.assertEqual(check.evidence["readyActions"], ["nativeHighlightSelection"])
            self.assertEqual(check.evidence["blockedActions"], ["annotatedPdfExport"])

    def test_doctor_warns_when_native_api_probe_is_from_old_runtime_without_matrix(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T03:34:36+0800",
                        "event": "nativeApiCapabilities",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "hasNativeHighlightCandidate": True,
                            "hasAnnotatedExportCandidate": False,
                            "candidateMethods": ["selectionDocumentController.highlightFromSelection"],
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            doctor.EVENTS_PATH = events

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("capability_matrix=False", check.detail)

    def test_doctor_detects_runtime_handler_stale_when_probe_native_action_is_unknown(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-06-11T03:34:36+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": [],
                        "capabilityMatrix": {},
                    },
                },
                {
                    "ts": "2026-06-11T06:38:55+0800",
                    "event": "nativeQueueCommandReceived",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
                {
                    "ts": "2026-06-11T06:38:55+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = Path(tmp) / "missing-extension"

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("runtime_handler_stale=True", check.detail)
            self.assertIn("reopen the Codex panel", check.detail)
            self.assertTrue(check.evidence["runtimeHandlerStale"])

    def test_doctor_detects_runtime_handler_stale_when_native_handler_features_missing(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "extension"
            extension.mkdir()
            main_js = extension / "main.js"
            main_js.write_text(
                "native-highlight-arm-next-selection-default\nnative-highlight-prefer-next-selection-v1\nnative-highlight-command-prepared\nselection-popup-diagnostics-v1\nnative-highlight-selection-poll-v1\nselection-popup-scene-observer-v1\nselection-popup-notebook-rebind-v1\nnative-highlight-selection-text-resolver-v1\ncontext-refresh-clears-stale-selection-v1\nai-edit-transaction-rollback-v1\nai-edit-undo-rollback-v2\nnative-mn-object-registry-scan-v1\nnative-mn-object-existence-probe-v1\nnative-mindmap-diff-apply-create-v1\nnative-mindmap-delete-suggestion-confirm-v1\n",
                encoding="utf-8",
            )
            doctor.EXT_DIR = extension
            events = Path(tmp) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-06-11T03:34:36+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": [],
                        "capabilityMatrix": {"nativeCards": {"ready": True}},
                    },
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            doctor.EVENTS_PATH = events

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("runtime_handler_stale=True", check.detail)
            self.assertIn("native-handler-features", check.evidence["runtimeHandlerStaleActions"])
            self.assertEqual(
                check.evidence["missingNativeHandlerFeatures"],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                ],
            )

    def test_doctor_fails_closed_when_installed_handler_feature_source_is_missing(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "extension"
            extension.mkdir()
            doctor.EXT_DIR = extension
            events = Path(tmp) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-06-11T03:34:36+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": [],
                        "capabilityMatrix": {"nativeCards": {"ready": True}},
                    },
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            doctor.EVENTS_PATH = events

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("runtime_handler_stale=True", check.detail)
            self.assertEqual(
                check.evidence["requiredNativeHandlerFeatures"],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                ],
            )
            self.assertEqual(
                check.evidence["missingNativeHandlerFeatures"],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                ],
            )

    def test_doctor_detects_runtime_handler_stale_when_reload_panel_action_is_unknown(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-06-11T10:23:46+0800",
                    "event": "webControlsReady",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "controls": ",".join(doctor.REQUIRED_WEB_CONTROL_IDS),
                        "missing": "",
                        "minWidth": "390",
                        "minHeight": "520",
                    },
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": [],
                        "capabilityMatrix": {"nativeCards": {"available": True, "ready": True}},
                    },
                },
                {
                    "ts": "2026-06-11T13:10:08+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "reload_web_panel"},
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = Path(tmp) / "missing-extension"

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "WARN")
            self.assertIn("reload_web_panel", check.detail)
            self.assertIn("reopen the Codex panel", check.detail)
            self.assertTrue(check.evidence["runtimeHandlerStale"])
            self.assertIn("reload_web_panel", check.evidence["runtimeHandlerStaleActions"])

    def test_doctor_clears_runtime_handler_stale_after_new_successful_probe(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            rows = [
                {
                    "ts": "2026-06-11T06:38:55+0800",
                    "event": "nativeQueueCommandUnknown",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilityProbeRequested",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {"nativeAction": "probe_native_api_capabilities"},
                },
                {
                    "ts": "2026-06-11T10:24:33+0800",
                    "event": "nativeApiCapabilities",
                    "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "hasNativeHighlightCandidate": False,
                        "hasAnnotatedExportCandidate": False,
                        "candidateMethods": [],
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
                            "native-mn-object-registry-scan-v1",
                            "native-mn-object-existence-probe-v1",
                            "native-mindmap-diff-apply-create-v1",
                            "native-mindmap-delete-suggestion-confirm-v1",
                        ],
                        "capabilityMatrix": {
                            "nativeCards": {"available": True, "ready": True},
                            "nativeHighlightSelection": {"available": False, "ready": False},
                        },
                    },
                },
            ]
            events.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
            doctor.EVENTS_PATH = events
            doctor.EXT_DIR = Path(tmp) / "missing-extension"

            check = doctor.check_runtime_native_api_capabilities()

            self.assertEqual(check.status, "OK")
            self.assertNotIn("runtime_handler_stale=True", check.detail)
            self.assertFalse(check.evidence["runtimeHandlerStale"])

    def test_doctor_reports_pdf_export_runtime_when_pymupdf_python_exists(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            doctor.ONEDRIVE_DIR = Path(tmp)
            doctor.find_pymupdf_python = lambda: (Path("/tmp/pymupdf-python"), None)

            check = doctor.check_pdf_export_runtime()

            self.assertEqual(check.status, "OK")
            self.assertIn("PyMuPDF", check.detail)
            self.assertEqual(check.evidence["python"], "/tmp/pymupdf-python")
            self.assertEqual(check.evidence["exportDir"], str(Path(tmp) / "exports"))

    def test_doctor_reports_companion_file_access_permission_diagnosis(self) -> None:
        doctor = load_doctor()
        doctor.http_action_json = lambda payload, timeout=8: {
            "ok": True,
            "status": "PERMISSION",
            "message": "需要 Full Disk Access",
            "fileAccess": {
                "sourcePdf": {"status": "PERMISSION", "path": "/tmp/source.pdf"},
                "pdfCache": {"status": "OK", "path": "/tmp/cache.pdf"},
                "mnDatabase": {"status": "PERMISSION", "path": "/tmp/MarginNotes.sqlite"},
                "exportDir": {"status": "OK", "path": "/tmp/exports"},
            },
        }

        check = doctor.check_companion_file_access_permissions()

        self.assertEqual(check.status, "WARN")
        self.assertIn("PERMISSION", check.detail)
        self.assertIn("pdfCache=OK", check.detail)
        self.assertIn("mnDatabase=PERMISSION", check.detail)
        self.assertEqual(check.evidence["fileAccess"]["sourcePdf"]["status"], "PERMISSION")

    def test_release_package_check_requires_installable_clean_zip(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.zip"
            cloud = Path(tmp) / "cloud.zip"
            entries = {
                "CodexCompanion-test/README-FIRST.txt": "Run: ./install.sh\n",
                "CodexCompanion-test/install.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/uninstall.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/Install Codex Companion.command": "#!/bin/zsh\n./install.sh\n",
                "CodexCompanion-test/Uninstall Codex Companion.command": "#!/bin/zsh\n./uninstall.sh\n",
                "CodexCompanion-test/Collect Native Highlight Evidence.command": "#!/bin/zsh\n--collect-native-highlight-evidence\n",
                "CodexCompanion-test/Collect Single Document Acceptance.command": "#!/bin/zsh\nsingle_document_acceptance.py\n",
                "CodexCompanion-test/Collect Cross-Machine Evidence.command": "#!/bin/zsh\n--collect-cross-machine-evidence\n",
                "CodexCompanion-test/Build Signed Package.command": "#!/bin/zsh\n--auto-sign\n",
                "CodexCompanion-test/Notarize Package.command": "#!/bin/zsh\nnotarize_pkg.py\n",
                "CodexCompanion-test/Prepare Release Handoff.command": "#!/bin/zsh\nprepare_release_handoff.py\n",
                "CodexCompanion-test/release_smoke_test.py": "print('smoke')\n",
                "CodexCompanion-test/single_document_acceptance.py": "codex-companion-single-document-acceptance-v1\n",
                "CodexCompanion-test/build_pkg.py": "PACKAGE_IDENTIFIER = \"com.codex.marginnote-companion\"\n",
                "CodexCompanion-test/notarize_pkg.py": "notarytool submit\n",
                "CodexCompanion-test/prepare_release_handoff.py": "Prepare a Codex Companion release handoff bundle\n",
                "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                "CodexCompanion-test/extension/codex.mn.assistant/main.js": "// ok\n",
            }
            self.write_zip(local, entries)
            self.write_zip(cloud, entries)
            doctor.LATEST_PACKAGE = local
            doctor.ONEDRIVE_LATEST_PACKAGE = cloud

            check = doctor.check_release_package()

            self.assertEqual(check.status, "OK")
            self.assertIn("installable", check.detail)
            self.assertTrue(check.evidence["hashesMatch"])
            self.assertEqual(check.evidence["badEntries"], [])
            self.assertNotIn("Install Codex Companion.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Collect Native Highlight Evidence.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Collect Single Document Acceptance.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Collect Cross-Machine Evidence.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Build Signed Package.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Notarize Package.command", check.evidence["missingRootFiles"])
            self.assertNotIn("Prepare Release Handoff.command", check.evidence["missingRootFiles"])
            self.assertNotIn("release_smoke_test.py", check.evidence["missingRootFiles"])
            self.assertNotIn("single_document_acceptance.py", check.evidence["missingRootFiles"])
            self.assertNotIn("build_pkg.py", check.evidence["missingRootFiles"])
            self.assertNotIn("notarize_pkg.py", check.evidence["missingRootFiles"])
            self.assertNotIn("prepare_release_handoff.py", check.evidence["missingRootFiles"])

    def test_release_package_check_warns_on_onedrive_permission_denied_without_traceback(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.zip"
            self.write_zip(
                local,
                {
                    "CodexCompanion-test/README-FIRST.txt": "Run: ./install.sh\n",
                    "CodexCompanion-test/install.sh": "#!/bin/zsh\n",
                    "CodexCompanion-test/uninstall.sh": "#!/bin/zsh\n",
                    "CodexCompanion-test/Install Codex Companion.command": "#!/bin/zsh\n./install.sh\n",
                    "CodexCompanion-test/Uninstall Codex Companion.command": "#!/bin/zsh\n./uninstall.sh\n",
                    "CodexCompanion-test/Collect Native Highlight Evidence.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/Collect Single Document Acceptance.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/Collect Cross-Machine Evidence.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/Build Signed Package.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/Notarize Package.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/Prepare Release Handoff.command": "#!/bin/zsh\n",
                    "CodexCompanion-test/release_smoke_test.py": "print('smoke')\n",
                    "CodexCompanion-test/build_pkg.py": "PACKAGE_IDENTIFIER = \"com.codex.marginnote-companion\"\n",
                    "CodexCompanion-test/notarize_pkg.py": "notarytool submit\n",
                    "CodexCompanion-test/prepare_release_handoff.py": "Prepare a Codex Companion release handoff bundle\n",
                    "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                    "CodexCompanion-test/extension/codex.mn.assistant/main.js": "// ok\n",
                },
            )

            class DeniedPath:
                def __init__(self, value: str) -> None:
                    self.value = value

                def exists(self) -> bool:
                    return True

                def read_bytes(self) -> bytes:
                    raise PermissionError("[Errno 1] Operation not permitted")

                def __fspath__(self) -> str:
                    return self.value

                def __str__(self) -> str:
                    return self.value

            doctor.LATEST_PACKAGE = local
            doctor.ONEDRIVE_LATEST_PACKAGE = DeniedPath(
                "/Users/liuwhale/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion.zip"
            )

            check = doctor.check_release_package()

            self.assertEqual(check.status, "WARN")
            self.assertIn("permission", check.detail)
            self.assertIn("Full Disk Access", check.detail)
            self.assertTrue(check.evidence["permissionIssue"])
            self.assertIn("OneDrive", check.evidence["permissionPath"])
            self.assertIn("Operation not permitted", check.evidence["permissionError"])
            self.assertNotIn("Traceback", json.dumps(check.evidence, ensure_ascii=False))

    def test_release_pkg_check_reports_unsigned_nopayload_pkg(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.pkg"
            cloud = Path(tmp) / "cloud.pkg"
            local.write_text("pkg", encoding="utf-8")
            cloud.write_text("pkg", encoding="utf-8")
            doctor.LATEST_PKG = local
            doctor.ONEDRIVE_LATEST_PKG = cloud

            def fake_shell(args: list[str], timeout: float = 8):
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                result = Result()
                if args[:2] == ["pkgutil", "--check-signature"]:
                    result.stdout = 'Package "local.pkg":\n   Status: no signature\n'
                elif args[:2] == ["pkgutil", "--payload-files"]:
                    result.stdout = ""
                return result

            doctor.shell = fake_shell

            check = doctor.check_release_pkg()

            self.assertEqual(check.status, "WARN")
            self.assertIn("no signature", check.detail)
            self.assertTrue(check.evidence["hashesMatch"])
            self.assertEqual(check.evidence["payloadFileCount"], 0)

    def test_release_sha256_manifest_warns_when_manifest_does_not_match_artifacts(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            local_zip = root / "CodexCompanion-test-dist.zip"
            cloud_zip = root / "cloud-CodexCompanion-test-dist.zip"
            local_pkg = root / "CodexCompanion-test.pkg"
            cloud_pkg = root / "cloud-CodexCompanion-test.pkg"
            local_manifest = root / "SHA256SUMS.txt"
            cloud_manifest = root / "cloud-SHA256SUMS.txt"
            for path, data in [
                (local_zip, b"zip"),
                (cloud_zip, b"zip"),
                (local_pkg, b"pkg"),
                (cloud_pkg, b"pkg"),
            ]:
                path.write_bytes(data)
            local_manifest.write_text("0" * 64 + "  CodexCompanion-test-dist.zip\n", encoding="utf-8")
            cloud_manifest.write_text(local_manifest.read_text(encoding="utf-8"), encoding="utf-8")
            doctor.LATEST_PACKAGE = local_zip
            doctor.ONEDRIVE_LATEST_PACKAGE = cloud_zip
            doctor.LATEST_PKG = local_pkg
            doctor.ONEDRIVE_LATEST_PKG = cloud_pkg
            doctor.RELEASE_SHA256SUMS = local_manifest
            doctor.ONEDRIVE_RELEASE_SHA256SUMS = cloud_manifest

            check = doctor.check_release_sha256_manifest()

            self.assertEqual(check.status, "WARN")
            self.assertIn("zip_mismatch", check.detail)
            self.assertFalse(check.evidence["artifactsMatch"])

    def test_release_maintainer_prerequisites_warn_when_signing_and_notary_credentials_are_missing(self) -> None:
        doctor = load_doctor()

        def fake_shell(args: list[str], timeout: float = 8):
            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            result = Result()
            if args[:3] == ["security", "find-identity", "-v"]:
                result.stdout = "     0 valid identities found\n"
            return result

        old_env = os.environ.copy()
        try:
            for key in [
                "NOTARYTOOL_KEYCHAIN_PROFILE",
                "CODEX_MN_NOTARYTOOL_KEYCHAIN_PROFILE",
                "APPLE_ID",
                "APPLE_TEAM_ID",
                "APPLE_APP_SPECIFIC_PASSWORD",
            ]:
                os.environ.pop(key, None)
            doctor.shell = fake_shell

            check = doctor.check_release_maintainer_prerequisites()
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        self.assertEqual(check.status, "WARN")
        self.assertIn("missing_developer_id_installer", check.detail)
        self.assertIn("missing_notary_credentials", check.detail)
        self.assertFalse(check.evidence["autoSignReady"])
        self.assertFalse(check.evidence["notaryCredentialsConfigured"])

    def test_release_maintainer_prerequisites_ok_with_single_identity_and_notary_env(self) -> None:
        doctor = load_doctor()

        def fake_shell(args: list[str], timeout: float = 8):
            class Result:
                returncode = 0
                stdout = ""
                stderr = ""

            result = Result()
            if args[:3] == ["security", "find-identity", "-v"]:
                result.stdout = (
                    '  1) FEDCBA9876543210 "Developer ID Installer: Example Team (ABCDE12345)"\n'
                    "     1 valid identities found\n"
                )
            return result

        old_env = os.environ.copy()
        try:
            os.environ["NOTARYTOOL_KEYCHAIN_PROFILE"] = "CodexNotary"
            doctor.shell = fake_shell

            check = doctor.check_release_maintainer_prerequisites()
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        self.assertEqual(check.status, "OK")
        self.assertTrue(check.evidence["autoSignReady"])
        self.assertEqual(check.evidence["developerIdInstallerCount"], 1)
        self.assertEqual(check.evidence["notaryCredentialsMode"], "keychain-profile")

    def test_release_pkg_check_warns_on_onedrive_permission_denied_without_traceback(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.pkg"
            local.write_text("pkg", encoding="utf-8")

            class DeniedPath:
                def __init__(self, value: str) -> None:
                    self.value = value

                def exists(self) -> bool:
                    return True

                def read_bytes(self) -> bytes:
                    raise PermissionError("[Errno 1] Operation not permitted")

                def __fspath__(self) -> str:
                    return self.value

                def __str__(self) -> str:
                    return self.value

            doctor.LATEST_PKG = local
            doctor.ONEDRIVE_LATEST_PKG = DeniedPath(
                "/Users/liuwhale/Library/CloudStorage/OneDrive-个人/Codex Companion/CodexCompanion.pkg"
            )

            check = doctor.check_release_pkg()

            self.assertEqual(check.status, "WARN")
            self.assertIn("permission", check.detail)
            self.assertIn("Full Disk Access", check.detail)
            self.assertTrue(check.evidence["permissionIssue"])
            self.assertIn("OneDrive", check.evidence["permissionPath"])
            self.assertIn("Operation not permitted", check.evidence["permissionError"])
            self.assertNotIn("Traceback", json.dumps(check.evidence, ensure_ascii=False))

    def test_card_write_dedupe_accepts_model_driven_variable_card_count(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "ts": "2026-06-11T09:00:00+0800",
                        "event": "createCardsFinished",
                        "pluginVersion": doctor.CURRENT_PLUGIN_VERSION,
                        "extra": {
                            "requested": 4,
                            "created": 0,
                            "skipped": 4,
                            "dedupeScanned": 120,
                        },
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            doctor.EVENTS_PATH = events

            check = doctor.check_full_reading_dedupe()

            self.assertEqual(check.status, "OK")
            self.assertIn("requested=4", check.detail)
            self.assertNotIn("requested=15", check.detail)

    def test_card_write_dedupe_warns_without_fixed_park_count_requirement(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            events = Path(tmp) / "events.jsonl"
            events.write_text("", encoding="utf-8")
            doctor.EVENTS_PATH = events

            check = doctor.check_full_reading_dedupe()

            self.assertEqual(check.status, "WARN")
            self.assertIn("requested>0", check.detail)
            self.assertNotIn("requested=15", check.detail)

    def test_release_pkg_check_fails_when_payload_is_not_empty(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.pkg"
            cloud = Path(tmp) / "cloud.pkg"
            local.write_text("pkg", encoding="utf-8")
            cloud.write_text("pkg", encoding="utf-8")
            doctor.LATEST_PKG = local
            doctor.ONEDRIVE_LATEST_PKG = cloud

            def fake_shell(args: list[str], timeout: float = 8):
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                result = Result()
                if args[:2] == ["pkgutil", "--check-signature"]:
                    result.stdout = "Status: signed by a certificate trusted by Mac OS X\n"
                elif args[:2] == ["pkgutil", "--payload-files"]:
                    result.stdout = "./Users/Shared/Codex Companion/._bad\n"
                return result

            doctor.shell = fake_shell

            check = doctor.check_release_pkg()

            self.assertEqual(check.status, "WARN")
            self.assertIn("payload_files=1", check.detail)
            self.assertEqual(check.evidence["payloadFileCount"], 1)

    def test_release_pkg_check_reports_signed_pkg_without_notarization(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.pkg"
            cloud = Path(tmp) / "cloud.pkg"
            local.write_text("pkg", encoding="utf-8")
            cloud.write_text("pkg", encoding="utf-8")
            doctor.LATEST_PKG = local
            doctor.ONEDRIVE_LATEST_PKG = cloud

            def fake_shell(args: list[str], timeout: float = 8):
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                result = Result()
                if args[:2] == ["pkgutil", "--check-signature"]:
                    result.stdout = "Status: signed by a certificate trusted by Mac OS X\n"
                elif args[:2] == ["pkgutil", "--payload-files"]:
                    result.stdout = ""
                elif args[:3] == ["xcrun", "stapler", "validate"]:
                    result.returncode = 65
                    result.stderr = "The validate action failed. Could not find ticket.\n"
                elif args[:2] == ["spctl", "-a"]:
                    result.returncode = 3
                    result.stderr = "rejected\n"
                return result

            doctor.shell = fake_shell

            check = doctor.check_release_pkg()

            self.assertEqual(check.status, "WARN")
            self.assertIn("not notarized", check.detail)
            self.assertTrue(check.evidence["signed"])
            self.assertFalse(check.evidence["notarized"])
            self.assertEqual(check.evidence["staplerReturnCode"], 65)

    def test_release_pkg_check_accepts_signed_notarized_nopayload_pkg(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.pkg"
            cloud = Path(tmp) / "cloud.pkg"
            local.write_text("pkg", encoding="utf-8")
            cloud.write_text("pkg", encoding="utf-8")
            doctor.LATEST_PKG = local
            doctor.ONEDRIVE_LATEST_PKG = cloud

            def fake_shell(args: list[str], timeout: float = 8):
                class Result:
                    returncode = 0
                    stdout = ""
                    stderr = ""

                result = Result()
                if args[:2] == ["pkgutil", "--check-signature"]:
                    result.stdout = "Status: signed by a certificate trusted by Mac OS X\n"
                elif args[:2] == ["pkgutil", "--payload-files"]:
                    result.stdout = ""
                elif args[:3] == ["xcrun", "stapler", "validate"]:
                    result.stdout = "The validate action worked!\n"
                elif args[:2] == ["spctl", "-a"]:
                    result.stderr = "accepted\n"
                return result

            doctor.shell = fake_shell

            check = doctor.check_release_pkg()

            self.assertEqual(check.status, "OK")
            self.assertIn("notarized", check.detail)
            self.assertTrue(check.evidence["signed"])
            self.assertTrue(check.evidence["notarized"])
            self.assertEqual(check.evidence["staplerReturnCode"], 0)
            self.assertEqual(check.evidence["spctlReturnCode"], 0)

    def test_release_package_check_warns_when_double_click_installers_are_missing(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.zip"
            cloud = Path(tmp) / "cloud.zip"
            entries = {
                "CodexCompanion-test/README-FIRST.txt": "Run: ./install.sh\n",
                "CodexCompanion-test/install.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/uninstall.sh": "#!/bin/zsh\n",
                "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                "CodexCompanion-test/extension/codex.mn.assistant/main.js": "// ok\n",
            }
            self.write_zip(local, entries)
            self.write_zip(cloud, entries)
            doctor.LATEST_PACKAGE = local
            doctor.ONEDRIVE_LATEST_PACKAGE = cloud

            check = doctor.check_release_package()

            self.assertEqual(check.status, "WARN")
            self.assertIn("Install Codex Companion.command", check.evidence["missingRootFiles"])
            self.assertIn("release_smoke_test.py", check.evidence["missingRootFiles"])

    def test_release_package_check_warns_when_root_installer_missing(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            local = Path(tmp) / "local.zip"
            cloud = Path(tmp) / "cloud.zip"
            entries = {
                "CodexCompanion-test/README-FIRST.txt": "old\n",
                "CodexCompanion-test/companion/companion.py": "print('ok')\n",
                "CodexCompanion-test/extension/codex.mn.assistant/main.js": "// ok\n",
            }
            self.write_zip(local, entries)
            self.write_zip(cloud, entries)
            doctor.LATEST_PACKAGE = local
            doctor.ONEDRIVE_LATEST_PACKAGE = cloud

            check = doctor.check_release_package()

            self.assertEqual(check.status, "WARN")
            self.assertIn("missing_root", check.detail)
            self.assertIn("install.sh", check.evidence["missingRootFiles"])

    def test_launch_agent_warns_when_only_legacy_label_is_loaded(self) -> None:
        doctor = load_doctor()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            agent_dir = home / "Library/LaunchAgents"
            agent_dir.mkdir(parents=True)
            (agent_dir / "com.liuwhale.codex-marginnote-assistant.plist").write_text("legacy", encoding="utf-8")
            doctor.HOME = home
            doctor.os.getuid = lambda: 501

            def fake_shell(args: list[str], timeout: float = 8):
                class Result:
                    returncode = 0 if args[-1].endswith("com.liuwhale.codex-marginnote-assistant") else 113
                    stdout = ""
                    stderr = ""

                return Result()

            doctor.shell = fake_shell

            check = doctor.check_launch_agent()

            self.assertEqual(check.status, "WARN")
            self.assertIn("preferred label is not loaded", check.detail)
            self.assertEqual(check.evidence["loaded"], ["com.liuwhale.codex-marginnote-assistant"])


if __name__ == "__main__":
    unittest.main()
