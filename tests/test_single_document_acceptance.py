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
        "knowledgeConsolePanel",
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
        "notebookWorkspaceSources",
        "notebookWorkspaceActions",
        "notebookObjectIntake",
        "notebookObjectIntakeSummary",
        "notebookObjectIntakeRoutes",
        "notebookObjectTaskComposer",
        "notebookObjectTaskComposerSummary",
        "notebookObjectTaskComposerList",
        "sourceRegistryPanel",
        "notebookWorkspaceSourceRegistry",
        "notebookWorkspaceSourceSummary",
        "notebookWorkspaceSourceList",
        "notebookWorkspaceSourceActionStatus",
        "notebookWorkspaceSourceActions",
        "notebookWorkspaceStudyProgram",
        "notebookWorkspaceStudyCoverage",
        "notebookWorkspaceStudyGaps",
        "notebookWorkspaceStudyRecommendations",
        "notebookWorkspaceRunbook",
        "notebookWorkspaceRunbookSummary",
        "notebookWorkspaceRunbookAutoButton",
        "notebookWorkspaceRunbookAutoStatus",
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
        "studioCanvasPanel",
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
        "operationLedgerDrawer",
        "operationLedgerPanel",
        "operationWorkspacePanel",
        "verificationReportPanel",
        "realMnAcceptancePanel",
        "realMnAcceptanceStatusLine",
        "realMnAcceptanceChecklist",
        "realMnAcceptanceRunAllButton",
        "singleDocumentAcceptanceLine",
        "singleDocumentAcceptanceDetail",
        "singleDocumentAcceptanceButton",
        "mainUiFunctionalAcceptanceLine",
        "mainUiFunctionalAcceptanceDetail",
        "mainUiFunctionalAcceptanceButton",
        "realMnAcceptanceSafeEvidenceButton",
        "mainNativeHighlightWizardPanel",
        "mainNativeHighlightWizardLine",
        "mainNativeHighlightWizardDetail",
        "mainNativeHighlightWizardActions",
        "nativeHighlightWizardRetryButton",
        "nativeHighlightWizardRefreshButton",
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
        "workflowBuilderBoardPanel",
        "workflowBuilderBoardSummary",
        "workflowBuilderBoardLanes",
        "externalGatewayPanel",
        "skillCenterPanel",
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
                    "native-highlight-selection-poll-probe-v1",
                    "selection-popup-scene-observer-v1",
                            "selection-popup-notebook-rebind-v1",
                            "native-highlight-selection-text-resolver-v1",
                            "native-pdf-selection-probe-v1",
                            "native-pdf-selection-image-probe-v1",
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

    def native_highlight_api_evidence_without_blob(self, module: Any) -> dict[str, Any]:
        return {
            "schema": "codex-companion-native-highlight-v1",
            "ok": True,
            "topicid": "T1",
            "bookmd5": "B1",
            "highlightScope": {"topicid": "T1", "bookmd5": "B1"},
            "events": {
                "latestPosted": {
                    **event("nativeHighlightSelectionPosted", highlightReturned=True, selectorVerified=True),
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "extra": {
                        "highlightReturned": True,
                        "selectorVerified": True,
                        "attemptedUnverifiedSelector": False,
                        "hasSelectionImage": True,
                        "selectionImageBytes": 1878,
                        "selectionLength": 6,
                    },
                }
            },
            "highlightBlobCheck": {"status": "WARN", "native_highlight_blobs": 0, "topicid": "T1", "bookmd5": "B1"},
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

    def test_native_highlight_api_proof_can_pass_without_database_blob(self) -> None:
        module = load_module()
        check = module.check_native_highlight_visible(
            events=self.complete_events(),
            native_highlight_evidence=self.native_highlight_api_evidence_without_blob(module),
            topicid="T1",
            bookmd5="B1",
        )

        self.assertEqual(check["status"], "PASS")
        self.assertIn("nativeHighlightApiProof", check["evidence"])
        self.assertTrue(check["evidence"]["nativeHighlightApiProof"]["ok"])

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

    def test_runtime_web_controls_prefers_complete_event_when_legacy_event_is_later(self) -> None:
        module = load_module()
        events = [
            event(
                "webControlsReady",
                controls=CURRENT_WEB_CONTROLS,
                missing="",
            ),
            event(
                "webControlsReady",
                controls="aiChatShell,modeSwitchBar,promptInput,sendButton,selectionPreview",
                missing="",
            ),
        ]

        check = module.check_runtime_web_controls(events, "T1", "B1")

        self.assertEqual(check["status"], "PASS")
        self.assertIn("notebookWorkspaceRunbook", check["evidence"]["event"]["extra"]["controls"])

    def test_cross_document_evidence_is_blocked_even_when_event_name_matches(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            module.ROOT = Path(tmp)
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

    def test_pdf_cache_accepts_readable_same_book_companion_cache(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.ROOT = root
            cache_dir = root / "uploads" / "pdf-cache"
            cache_dir.mkdir(parents=True)
            pdf_path = cache_dir / "B1-current.pdf"
            pdf_path.write_bytes(b"%PDF-1.7\n% test pdf cache\n")
            index_path = cache_dir / "index.json"
            index_path.write_text(
                module.json_dumps(
                    {
                        "B1": {
                            "bookmd5": "B1",
                            "path": str(pdf_path),
                            "size": pdf_path.stat().st_size,
                            "cached_at": "2026-06-28T04:43:24+0800",
                        }
                    }
                ),
                encoding="utf-8",
            )
            events = [
                item
                for item in self.complete_events()
                if item["event"] != "pdfCacheUploadPosted"
            ]
            events.append(event("pdfCacheUploadPosted", topicid="OTHER", bookmd5="OTHER", ok=True, size=1024))

            check = module.check_pdf_cache(events, "T1", "B1")

        self.assertEqual(check["status"], "PASS")
        self.assertIn("Companion cache", check["detail"])
        self.assertEqual(check["evidence"]["companionPdfCache"]["bookmd5"], "B1")
        self.assertEqual(check["evidence"]["companionPdfCache"]["fileSize"], len(b"%PDF-1.7\n% test pdf cache\n"))

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

    def test_selection_popup_passes_when_notification_drives_native_highlight(self) -> None:
        module = load_module()
        events = [
            item
            for item in self.complete_events()
            if item["event"] not in {"selectionPopupHighlightMenuInstalled", "nativeHighlightSelectionPosted"}
        ]
        events.append(event("selectionPopupHighlightNotificationObserved", hasSelectionPayload=True, hasSelectionImage=True))
        events.append(
            {
                **event("nativeHighlightSelectionPosted"),
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "extra": {
                    "highlightReturned": True,
                    "selectorVerified": True,
                    "attemptedUnverifiedSelector": False,
                    "hasSelectionImage": True,
                    "selectionImageBytes": 1878,
                    "selectionLength": 6,
                },
            }
        )

        check = module.check_selection_popup(events, "T1", "B1")

        self.assertEqual(check["status"], "PASS")
        self.assertIn("nativeHighlightApiProof", check["evidence"])

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

    def test_cli_does_not_attach_auto_discovered_highlight_evidence_from_other_document(self) -> None:
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
            other = self.native_highlight_evidence()
            other["topicid"] = "OTHER_TOPIC"
            other["bookmd5"] = "OTHER_BOOK"
            other["highlightScope"] = {"topicid": "OTHER_TOPIC", "bookmd5": "OTHER_BOOK"}
            other["highlightBlobCheck"]["topicid"] = "OTHER_TOPIC"
            other["highlightBlobCheck"]["bookmd5"] = "OTHER_BOOK"
            highlight_path = evidence_dir / "codex-companion-native-highlight-evidence-current.json"
            highlight_path.write_text(module.json_dumps(other), encoding="utf-8")
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

            self.assertEqual(code, 1)
            report = module.read_json(output_path)
            highlight_check = next(item for item in report["checks"] if item["id"] == "native_highlight_visible")
            self.assertEqual(highlight_check["evidence"]["nativeHighlightEvidence"], {})


if __name__ == "__main__":
    unittest.main()
