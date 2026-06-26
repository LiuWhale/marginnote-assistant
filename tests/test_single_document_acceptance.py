from __future__ import annotations

import importlib.util
import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "single_document_acceptance.py"
CURRENT_WEB_CONTROLS = ",".join(
    [
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
        "notebookWorkspaceRunbook",
        "notebookWorkspaceRunbookSummary",
        "notebookWorkspaceRunbookContinueButton",
        "notebookWorkspaceRunbookList",
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
    ]
)


def load_module() -> Any:
    spec = importlib.util.spec_from_file_location("codex_mn_single_document_acceptance", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def event(name: str, topicid: str = "T1", bookmd5: str = "B1", **extra: Any) -> dict[str, Any]:
    return {
        "ts": "2026-06-12T13:30:00+0800",
        "event": name,
        "topicid": topicid,
        "bookmd5": bookmd5,
        "pluginVersion": "0.4.11",
        "extra": extra,
    }


class SingleDocumentAcceptanceTests(unittest.TestCase):
    def complete_events(self) -> list[dict[str, Any]]:
        return [
            event(
                "webControlsReady",
                controls=CURRENT_WEB_CONTROLS,
                missing="",
                minWidth=390,
                minHeight=520,
            ),
            event(
                "nativeApiCapabilities",
                capabilityMatrix={
                    "nativeCards": {"ready": True},
                    "nativeMindmap": {"ready": True},
                    "undoGroupedWrites": {"ready": True},
                    "refreshAfterWrite": {"ready": True},
                    "nativeHighlightSelection": {"available": True},
                    "annotatedPdfExport": {"available": True},
                },
                handlerFeatures=[
                    "native-highlight-arm-next-selection-default",
                    "native-highlight-prefer-next-selection-v1",
                    "native-highlight-command-prepared",
                    "selection-popup-diagnostics-v1",
                    "native-highlight-selection-poll-v1",
                    "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "context-refresh-clears-stale-selection-v1",
                ],
            ),
            event("handleResponse", action="explain_selection", message="完成", cards=0, hasMindmap=False),
            event("createCardsFinished", requested=2, created=2, skipped=0),
            event("createMindmapFinished", created=True, createdCount=4, mode="createRoot"),
            event("createMindmapFinished", created=True, createdCount=2, mode="mergeIntoSelected"),
            event("pdfCacheUploadPosted", ok=True, size=1024, path="/tmp/doc.pdf"),
            event("nativeHighlightSelectionPosted", selectorVerified=True, selectionLength=24),
            event("selectionPopupHighlightMenuInstalled", selectionLength=24),
            event("commandsReceived", count=1, mode="array-sync"),
            event("commandsAcked", count=1),
        ]

    def complete_action_results(self) -> list[dict[str, Any]]:
        return [
            {"action": "settings_update", "topicid": "T1", "bookmd5": "B1", "result": {"ok": True}},
            {"action": "upload_file", "topicid": "T1", "bookmd5": "B1", "result": {"ok": True, "file": {"name": "notes.md"}}},
            {"action": "goal_run", "topicid": "T1", "bookmd5": "B1", "result": {"ok": True, "goalQueue": [{"action": "generate_card"}]}},
            {"action": "history_list", "topicid": "T1", "bookmd5": "B1", "result": {"ok": True, "history": [{"role": "user"}]}},
            {"action": "queue_status", "topicid": "T1", "bookmd5": "B1", "result": {"ok": True, "queue": {"pending": 0}}},
            {
                "action": "export_annotated_pdf",
                "topicid": "T1",
                "bookmd5": "B1",
                "result": {
                    "ok": True,
                    "status": "OK",
                    "annotations_created": 1,
                    "modifiedOriginal": False,
                    "outputPdf": "/tmp/doc-annotated.pdf",
                },
            },
        ]

    def native_highlight_evidence(self) -> dict[str, Any]:
        return {
            "schema": "codex-companion-native-highlight-v1",
            "ok": True,
            "topicid": "T1",
            "bookmd5": "B1",
            "highlightScope": {"topicid": "T1", "bookmd5": "B1"},
            "highlightAttemptEvent": event("nativeHighlightSelectionPosted", selectorVerified=True, selectionLength=24),
            "highlightBlobCheck": {"status": "OK", "native_highlight_blobs": 1, "topicid": "T1", "bookmd5": "B1"},
        }

    def test_complete_single_document_evidence_passes_all_required_checks(self) -> None:
        module = load_module()

        report = module.evaluate_single_document_acceptance(
            topicid="T1",
            bookmd5="B1",
            events=self.complete_events(),
            action_results=self.complete_action_results(),
            native_highlight_evidence=self.native_highlight_evidence(),
        )

        self.assertTrue(report["ok"], report)
        self.assertEqual(report["schema"], "codex-companion-single-document-acceptance-v1")
        self.assertEqual(report["topicid"], "T1")
        self.assertEqual(report["bookmd5"], "B1")
        self.assertEqual(report["summary"]["passed"], report["summary"]["total"])
        self.assertEqual(report["summary"]["blocked"], 0)

    def test_runtime_web_controls_requires_current_button_groups(self) -> None:
        module = load_module()
        events = [
            event(
                "webControlsReady",
                controls="promptInput,sendButton,selectionPreview",
                missing="",
            )
        ]

        check = module.check_runtime_web_controls(events, "T1", "B1")

        self.assertEqual(check["status"], "BLOCK")
        self.assertIn("aiChatShell", check["evidence"]["absent"])
        self.assertIn("modeSwitchBar", check["evidence"]["absent"])
        self.assertIn("agentWorkspaceModeButton", check["evidence"]["absent"])
        self.assertIn("workspaceNavigator", check["evidence"]["absent"])
        self.assertIn("workspaceNavMindmapStudioButton", check["evidence"]["absent"])
        self.assertIn("objectWorkspacePanel", check["evidence"]["absent"])
        self.assertIn("objectGraphPanel", check["evidence"]["absent"])
        self.assertIn("objectGraphRelationAddButton", check["evidence"]["absent"])
        self.assertIn("operationLedgerPanel", check["evidence"]["absent"])
        self.assertIn("knowledgeWorkspacePanel", check["evidence"]["absent"])
        self.assertIn("workflowWorkspacePanel", check["evidence"]["absent"])
        self.assertIn("agentWorkbenchBar", check["evidence"]["absent"])
        self.assertIn("liveHistory", check["evidence"]["absent"])
        self.assertIn("readinessPanel", check["evidence"]["absent"])

    def test_cross_document_evidence_is_blocked_even_when_event_name_matches(self) -> None:
        module = load_module()
        events = self.complete_events()
        events[3] = event("createCardsFinished", topicid="T1", bookmd5="OTHER", requested=2, created=2)

        report = module.evaluate_single_document_acceptance(
            topicid="T1",
            bookmd5="B1",
            events=events,
            action_results=self.complete_action_results(),
            native_highlight_evidence=self.native_highlight_evidence(),
        )

        self.assertFalse(report["ok"], report)
        blocked = {item["id"]: item for item in report["checks"] if item["status"] == "BLOCK"}
        self.assertIn("card_write", blocked)
        self.assertIn("same topic/book", blocked["card_write"]["detail"])

    def test_selection_popup_blocker_includes_latest_diagnostic_event(self) -> None:
        module = load_module()
        events = [
            item
            for item in self.complete_events()
            if item["event"] != "selectionPopupHighlightMenuInstalled"
        ]
        events.append(
            event(
                "selectionPopupHighlightMenuSkipped",
                reason="missing-selection-text",
                hasDocumentController=True,
                hasLastSelectionText=False,
            )
        )

        check = module.check_selection_popup(events, "T1", "B1")

        self.assertEqual(check["status"], "BLOCK")
        self.assertIn("latestDiagnosticEvent", check["evidence"])
        self.assertEqual(check["evidence"]["latestDiagnosticEvent"]["event"], "selectionPopupHighlightMenuSkipped")
        self.assertEqual(check["evidence"]["latestDiagnosticEvent"]["extra"]["reason"], "missing-selection-text")

    def test_selection_popup_blocker_reports_registered_observer_without_popup_notification(self) -> None:
        module = load_module()
        events = [
            item
            for item in self.complete_events()
            if item["event"] != "selectionPopupHighlightMenuInstalled"
        ]
        events.append(
            event(
                "selectionPopupHighlightObserverRegistered",
                source="sceneWillConnect",
                notificationName="PopupMenuOnSelection",
            )
        )

        check = module.check_selection_popup(events, "T1", "B1")

        self.assertEqual(check["status"], "BLOCK")
        self.assertIn("latestDiagnosticEvent", check["evidence"])
        self.assertEqual(check["evidence"]["latestDiagnosticEvent"]["event"], "selectionPopupHighlightObserverRegistered")
        self.assertIn("observer registered", check["detail"])

    def test_cli_writes_report_json_from_event_and_action_result_files(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.jsonl"
            events_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_events()) + "\n",
                encoding="utf-8",
            )
            actions_path = root / "actions.jsonl"
            actions_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_action_results()) + "\n",
                encoding="utf-8",
            )
            highlight_path = root / "native-highlight.json"
            highlight_path.write_text(module.json_dumps(self.native_highlight_evidence()), encoding="utf-8")
            output_path = root / "single-document-report.json"

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = module.main(
                    [
                        "--topicid",
                        "T1",
                        "--bookmd5",
                        "B1",
                        "--events",
                        str(events_path),
                        "--action-results",
                        str(actions_path),
                        "--native-highlight-evidence",
                        str(highlight_path),
                        "--output",
                        str(output_path),
                        "--json",
                    ]
                )

            self.assertEqual(code, 0)
            self.assertIn("singleDocumentAcceptance", stdout.getvalue())
            report = module.read_json(output_path)
            self.assertTrue(report["ok"], report)
            self.assertIn("singleDocumentAcceptance", report["summary"])

    def test_cli_uses_default_recorded_action_results_when_not_explicitly_passed(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.jsonl"
            events_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_events()) + "\n",
                encoding="utf-8",
            )
            actions_path = root / "action-results.jsonl"
            actions_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_action_results()) + "\n",
                encoding="utf-8",
            )
            module.DEFAULT_ACTION_RESULTS_PATH = actions_path
            highlight_path = root / "native-highlight.json"
            highlight_path.write_text(module.json_dumps(self.native_highlight_evidence()), encoding="utf-8")
            output_path = root / "single-document-report.json"

            with contextlib.redirect_stdout(io.StringIO()):
                code = module.main(
                    [
                        "--topicid",
                        "T1",
                        "--bookmd5",
                        "B1",
                        "--events",
                        str(events_path),
                        "--native-highlight-evidence",
                        str(highlight_path),
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(code, 0)
            report = module.read_json(output_path)
            self.assertTrue(report["ok"], report)
            self.assertEqual(report["summary"]["singleDocumentAcceptance"], "PASS")

    def test_cli_auto_discovers_default_native_highlight_evidence(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            events_path = root / "events.jsonl"
            events_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_events()) + "\n",
                encoding="utf-8",
            )
            actions_path = root / "action-results.jsonl"
            actions_path.write_text(
                "\n".join(module.json_dumps(item) for item in self.complete_action_results()) + "\n",
                encoding="utf-8",
            )
            module.ROOT = root
            module.DEFAULT_ACTION_RESULTS_PATH = actions_path
            evidence_dir = root / "release" / "evidence"
            evidence_dir.mkdir(parents=True)
            highlight_path = evidence_dir / "codex-companion-native-highlight-evidence-current.json"
            highlight_path.write_text(module.json_dumps(self.native_highlight_evidence()), encoding="utf-8")
            output_path = root / "single-document-report.json"

            with contextlib.redirect_stdout(io.StringIO()):
                code = module.main(
                    [
                        "--topicid",
                        "T1",
                        "--bookmd5",
                        "B1",
                        "--events",
                        str(events_path),
                        "--output",
                        str(output_path),
                    ]
                )

            self.assertEqual(code, 0)
            report = module.read_json(output_path)
            self.assertTrue(report["ok"], report)
            highlight_check = next(item for item in report["checks"] if item["id"] == "native_highlight_visible")
            evidence = highlight_check["evidence"]["nativeHighlightEvidence"]
            self.assertTrue(evidence["autoDiscovered"])
            self.assertEqual(evidence["sourcePath"], str(highlight_path))


if __name__ == "__main__":
    unittest.main()
