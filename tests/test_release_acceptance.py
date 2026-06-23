from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import unittest
import zipfile
from unittest.mock import patch
from pathlib import Path


ACCEPTANCE_PATH = Path(__file__).resolve().parents[1] / "release_acceptance.py"


class ReleaseAcceptanceTests(unittest.TestCase):
    def load_module(self):
        spec = importlib.util.spec_from_file_location("codex_mn_release_acceptance", ACCEPTANCE_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module

    def test_acceptance_blocks_unsigned_pkg_missing_native_highlight_and_cross_machine_evidence(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "WARN", "detail": "0 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {"name": "Latest RC pkg", "status": "WARN", "detail": "no signature"},
        ]
        smoke = {"ok": True, "installDryRun": {"ok": True}}

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke=smoke,
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
        )

        self.assertFalse(report["releasable"])
        blockers = {item["name"]: item for item in report["gates"] if item["status"] == "BLOCK"}
        self.assertIn("native_visible_highlight", blockers)
        self.assertIn("signed_pkg", blockers)
        self.assertIn("notarized_pkg", blockers)
        self.assertIn("cross_machine_install", blockers)
        self.assertIn("ZHIGHLIGHTS", blockers["native_visible_highlight"]["detail"])
        self.assertIn("no signature", blockers["signed_pkg"]["detail"])

    def test_acceptance_separates_signed_pkg_from_notarized_pkg(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "2 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {
                "name": "Latest RC pkg",
                "status": "WARN",
                "detail": "not notarized",
                "evidence": {"signed": True, "notarized": False, "staplerReturnCode": 65},
            },
        ]
        smoke = {"ok": True, "installDryRun": {"ok": True}}

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke=smoke,
            doctor_checks=doctor_checks,
            cross_machine_verified=True,
        )

        gates = {item["name"]: item for item in report["gates"]}
        self.assertEqual(gates["signed_pkg"]["status"], "PASS")
        self.assertEqual(gates["notarized_pkg"]["status"], "BLOCK")
        self.assertIn("not notarized", gates["notarized_pkg"]["detail"])
        self.assertFalse(report["releasable"])

    def test_acceptance_passes_only_when_all_hard_gates_have_evidence(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "2 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {
                "name": "Latest RC pkg",
                "status": "OK",
                "detail": "signed notarized nopayload pkg; local and OneDrive hashes match",
                "evidence": {"signed": True, "notarized": True, "staplerReturnCode": 0, "spctlReturnCode": 0},
            },
        ]
        smoke = {"ok": True, "installDryRun": {"ok": True}}

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke=smoke,
            doctor_checks=doctor_checks,
            cross_machine_verified=True,
            single_document_acceptance={"ok": True, "path": "/tmp/single-document.json"},
        )

        self.assertTrue(report["releasable"], report)
        self.assertFalse([item for item in report["gates"] if item["status"] == "BLOCK"])

    def test_acceptance_blocks_without_single_document_acceptance_evidence(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "2 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {
                "name": "Latest RC pkg",
                "status": "OK",
                "detail": "signed notarized nopayload pkg; local and OneDrive hashes match",
                "evidence": {"signed": True, "notarized": True, "staplerReturnCode": 0, "spctlReturnCode": 0},
            },
        ]

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=True,
            single_document_acceptance={"ok": False, "problems": ["missing-evidence-path"]},
        )

        blockers = {item["name"]: item for item in report["blockers"]}
        self.assertIn("single_document_acceptance", blockers)
        self.assertIn("missing-evidence-path", blockers["single_document_acceptance"]["detail"])
        next_actions = "\n".join(blockers["single_document_acceptance"]["nextActions"])
        self.assertIn("single_document_acceptance.py", next_actions)
        self.assertIn(
            "Collect Single Document Acceptance.command",
            next_actions,
        )
        self.assertNotIn("--native-highlight-evidence", next_actions)

    def test_single_document_acceptance_evidence_requires_schema_ok_and_all_checks(self) -> None:
        module = self.load_module()
        valid = {
            "schema": module.SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
            "ok": True,
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "summary": {"singleDocumentAcceptance": "PASS", "total": 2, "passed": 2, "blocked": 0},
            "checks": [
                {"id": "runtime_web_controls", "status": "PASS"},
                {"id": "card_write", "status": "PASS"},
            ],
        }
        invalid = {
            **valid,
            "ok": False,
            "summary": {"singleDocumentAcceptance": "BLOCK", "total": 2, "passed": 1, "blocked": 1},
            "checks": [
                {"id": "runtime_web_controls", "status": "PASS"},
                {"id": "card_write", "status": "BLOCK", "detail": "wrong document"},
            ],
        }

        self.assertTrue(module.validate_single_document_acceptance_evidence(valid)["ok"])
        result = module.validate_single_document_acceptance_evidence(invalid)
        self.assertFalse(result["ok"])
        self.assertIn("check-blocked:card_write", result["problems"])
        self.assertIn("card_write", result["blockedChecks"])

    def test_auto_discovery_prefers_latest_valid_single_document_acceptance_evidence(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = {
                "schema": module.SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
                "ok": True,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "topicid": "topic-a",
                "bookmd5": "book-a",
                "summary": {"singleDocumentAcceptance": "PASS", "total": 1, "passed": 1, "blocked": 0},
                "checks": [{"id": "runtime_web_controls", "status": "PASS"}],
            }
            invalid = {
                **valid,
                "ok": False,
                "summary": {"singleDocumentAcceptance": "BLOCK", "total": 1, "passed": 0, "blocked": 1},
                "checks": [{"id": "runtime_web_controls", "status": "BLOCK"}],
            }
            valid_path = root / "codex-companion-single-document-acceptance-20260612-010000.json"
            invalid_path = root / "codex-companion-single-document-acceptance-20260612-020000.json"
            valid_path.write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")

            result = module.single_document_acceptance_result(None, search_dirs=[root])

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["path"], str(valid_path))
            self.assertTrue(result["autoDiscovered"])

    def test_acceptance_can_use_structured_native_highlight_evidence_when_live_doctor_scope_differs(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "WARN", "detail": "0 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {
                "name": "Latest RC pkg",
                "status": "OK",
                "detail": "signed notarized nopayload pkg; local and OneDrive hashes match",
                "evidence": {"signed": True, "notarized": True, "staplerReturnCode": 0, "spctlReturnCode": 0},
            },
        ]
        native_highlight_evidence = {
            "ok": True,
            "path": "/tmp/native-highlight-evidence.json",
            "event": {"event": "nativeHighlightSelectionPosted", "pluginVersion": "0.4.9"},
            "doctorHighlightCheck": {"name": "Native highlight blobs", "status": "OK", "detail": "1 rows have ZHIGHLIGHTS"},
        }

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=True,
            native_highlight_evidence=native_highlight_evidence,
        )

        gates = {item["name"]: item for item in report["gates"]}
        self.assertEqual(gates["native_visible_highlight"]["status"], "PASS")
        self.assertIn("native-highlight-evidence.json", json.dumps(gates["native_visible_highlight"], ensure_ascii=False))
        self.assertTrue(report["releasable"], report)

    def test_native_highlight_evidence_requires_posted_event_and_blob_check(self) -> None:
        module = self.load_module()
        valid = {
            "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
            "events": {
                "latestPosted": {
                    "event": "nativeHighlightSelectionPosted",
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "topicid": "topic-a",
                    "bookmd5": "book-a",
                }
            },
            "highlightBlobCheck": {
                "status": "OK",
                "topicid": "topic-a",
                "bookmd5": "book-a",
                "native_highlight_blobs": 1,
            },
        }
        missing_event = {
            **valid,
            "events": {"latestPosted": None},
        }
        missing_blob = {
            **valid,
            "highlightBlobCheck": {
                "status": "WARN",
                "topicid": "topic-a",
                "bookmd5": "book-a",
                "native_highlight_blobs": 0,
            },
        }

        self.assertTrue(module.validate_native_highlight_evidence(valid)["ok"])
        self.assertIn("missing-nativeHighlightSelectionPosted", module.validate_native_highlight_evidence(missing_event)["problems"])
        self.assertIn("native-highlight-blobs-not-ok", module.validate_native_highlight_evidence(missing_blob)["problems"])

    def test_native_highlight_evidence_rejects_missing_or_mismatched_scope(self) -> None:
        module = self.load_module()
        scoped = {
            "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
            "events": {
                "latestPosted": {
                    "event": "nativeHighlightSelectionPosted",
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "topicid": "topic-a",
                    "bookmd5": "book-a",
                }
            },
            "highlightBlobCheck": {
                "status": "OK",
                "topicid": "topic-a",
                "bookmd5": "book-a",
                "native_highlight_blobs": 1,
            },
        }
        missing_scope = {
            **scoped,
            "events": {
                "latestPosted": {
                    "event": "nativeHighlightSelectionPosted",
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                }
            },
        }
        mismatched_scope = {
            **scoped,
            "highlightBlobCheck": {
                "status": "OK",
                "topicid": "other-topic",
                "bookmd5": "book-a",
                "native_highlight_blobs": 1,
            },
        }

        self.assertIn("missing-native-highlight-scope", module.validate_native_highlight_evidence(missing_scope)["problems"])
        self.assertIn("native-highlight-scope-mismatch", module.validate_native_highlight_evidence(mismatched_scope)["problems"])

    def test_native_highlight_evidence_reports_active_attempt_failure_reason(self) -> None:
        module = self.load_module()
        evidence = {
            "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
            "events": {"latestPosted": None},
            "highlightBlobCheck": {
                "status": "WARN",
                "topicid": "",
                "bookmd5": "",
                "native_highlight_blobs": 0,
            },
            "highlightAttempt": {
                "requested": True,
                "ok": False,
                "reason": "missing-selection",
                "wait": {"reason": "missing-selection"},
            },
        }

        result = module.validate_native_highlight_evidence(evidence)

        self.assertFalse(result["ok"])
        self.assertIn("native-highlight-attempt-failed:missing-selection", result["problems"])
        self.assertEqual(result["highlightAttemptReason"], "missing-selection")

    def test_acceptance_native_highlight_blocker_surfaces_attempt_failure_reason(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "WARN", "detail": "0 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "hash ok"},
            {"name": "Latest RC pkg", "status": "WARN", "detail": "no signature"},
        ]
        native_highlight_evidence = {
            "ok": False,
            "problems": [
                "missing-nativeHighlightSelectionPosted",
                "native-highlight-attempt-failed:missing-selection",
                "native-highlight-blobs-not-ok",
            ],
            "highlightAttemptReason": "missing-selection",
            "highlightBlobCheck": {"detail": "latest nativeHighlightSelectionPosted event lacks topicid/bookmd5"},
        }

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
            native_highlight_evidence=native_highlight_evidence,
        )

        blockers = {item["name"]: item for item in report["blockers"]}
        detail = blockers["native_visible_highlight"]["detail"]
        self.assertIn("missing-selection", detail)
        self.assertIn("missing-nativeHighlightSelectionPosted", detail)
        self.assertIn("latest nativeHighlightSelectionPosted", detail)
        self.assertIn("nativeHighlightEvidence", blockers["native_visible_highlight"]["evidence"])

    def test_acceptance_native_highlight_missing_evidence_keeps_doctor_detail(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "WARN", "detail": "0 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "hash ok"},
            {"name": "Latest RC pkg", "status": "WARN", "detail": "no signature"},
        ]

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
            native_highlight_evidence={"ok": False, "problems": ["missing-evidence-path"]},
        )

        blockers = {item["name"]: item for item in report["blockers"]}
        detail = blockers["native_visible_highlight"]["detail"]
        self.assertIn("missing-evidence-path", detail)
        self.assertIn("0 rows have ZHIGHLIGHTS", detail)

    def test_mn_runtime_evidence_can_satisfy_runtime_and_native_api_gates(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "WARN", "detail": "stale runtime event"},
            {"name": "MN4 native API probe", "status": "WARN", "detail": "stale native probe"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "1 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "hash ok"},
        ]
        mn_runtime_evidence = {
            "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "statusAfter": {
                "mnRuntime": {
                    "ready": True,
                    "webControlsReady": True,
                    "nativeApiReady": True,
                    "staleRuntime": False,
                    "runtimeHandlerStale": False,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                },
                "nativeApiCapabilities": {
                    "available": True,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
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
                    "capabilityMatrix": {
                        "nativeCards": {"ready": True},
                        "nativeMindmap": {"ready": True},
                    },
                },
            },
        }

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
            mn_runtime_evidence=mn_runtime_evidence,
        )

        gates = {gate["name"]: gate for gate in report["gates"]}
        self.assertEqual(gates["runtime_web_controls"]["status"], "PASS")
        self.assertEqual(gates["native_api_matrix"]["status"], "PASS")
        self.assertIn("mnRuntimeEvidence", gates["runtime_web_controls"]["evidence"])
        self.assertIn("mnRuntimeEvidence", gates["native_api_matrix"]["evidence"])

    def test_prevalidated_mn_runtime_evidence_can_satisfy_runtime_gates(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "WARN", "detail": "runtime handler does not know ['probe_native_api_capabilities']"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "matrix ok"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "1 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "hash ok"},
        ]
        mn_runtime_validation = {
            "ok": True,
            "problems": [],
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "mnRuntime": {
                "ready": True,
                "webControlsReady": True,
                "nativeApiReady": True,
                "staleRuntime": False,
                "runtimeHandlerStale": False,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            },
            "nativeApiCapabilities": {
                "available": True,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
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
                "capabilityMatrix": {
                    "nativeCards": {"ready": True},
                    "nativeMindmap": {"ready": True},
                },
            },
            "path": "/tmp/mn-runtime.json",
        }

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
            mn_runtime_evidence=mn_runtime_validation,
        )

        gates = {gate["name"]: gate for gate in report["gates"]}
        self.assertEqual(gates["runtime_web_controls"]["status"], "PASS")
        self.assertEqual(gates["native_api_matrix"]["status"], "PASS")
        self.assertIn("mnRuntimeEvidence", gates["runtime_web_controls"]["evidence"])

    def test_mn_runtime_evidence_rejects_stale_runtime_or_stale_handler(self) -> None:
        module = self.load_module()
        mn_runtime_evidence = {
            "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "statusAfter": {
                "mnRuntime": {
                    "ready": False,
                    "webControlsReady": True,
                    "nativeApiReady": True,
                    "staleRuntime": False,
                    "runtimeHandlerStale": True,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                },
                "nativeApiCapabilities": {
                    "available": True,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "capabilityMatrix": {},
                },
            },
        }

        result = module.validate_mn_runtime_evidence(mn_runtime_evidence)

        self.assertFalse(result["ok"])
        self.assertIn("runtime-not-ready", result["problems"])
        self.assertIn("runtime-handler-stale", result["problems"])

    def test_mn_runtime_evidence_rejects_missing_required_native_handler_features(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "codex.mn.assistant"
            extension.mkdir(parents=True)
            (extension / "main.js").write_text(
                "native-highlight-arm-next-selection-default\nnative-highlight-prefer-next-selection-v1\nnative-highlight-command-prepared\nselection-popup-diagnostics-v1\nnative-highlight-selection-poll-v1\nselection-popup-scene-observer-v1\nselection-popup-notebook-rebind-v1\nnative-highlight-selection-text-resolver-v1\ncontext-refresh-clears-stale-selection-v1\nai-edit-transaction-rollback-v1\nai-edit-undo-rollback-v2\n",
                encoding="utf-8",
            )
            module.LIVE_EXTENSION = extension
            mn_runtime_evidence = {
                "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "statusAfter": {
                    "mnRuntime": {
                        "ready": True,
                        "webControlsReady": True,
                        "nativeApiReady": True,
                        "staleRuntime": False,
                        "runtimeHandlerStale": False,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "sourceMtime": 1_900_000_000,
                        "latestEventTs": "2030-03-17T17:46:40+0800",
                    },
                    "nativeApiCapabilities": {
                        "available": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "capabilityMatrix": {"nativeCards": {"ready": True}},
                        "handlerFeatures": ["native-highlight-command-prepared"],
                    },
                },
            }

            result = module.validate_mn_runtime_evidence(mn_runtime_evidence)

        self.assertFalse(result["ok"])
        self.assertIn("missing-native-handler-feature:native-highlight-arm-next-selection-default", result["problems"])

    def test_mn_runtime_evidence_rejects_missing_handler_features_even_when_source_is_missing(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "codex.mn.assistant"
            extension.mkdir(parents=True)
            module.LIVE_EXTENSION = extension
            mn_runtime_evidence = {
                "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "statusAfter": {
                    "mnRuntime": {
                        "ready": True,
                        "webControlsReady": True,
                        "nativeApiReady": True,
                        "staleRuntime": False,
                        "runtimeHandlerStale": False,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "sourceMtime": 1_900_000_000,
                        "latestEventTs": "2030-03-17T17:46:40+0800",
                    },
                    "nativeApiCapabilities": {
                        "available": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "capabilityMatrix": {"nativeCards": {"ready": True}},
                        "handlerFeatures": [],
                    },
                },
            }

            result = module.validate_mn_runtime_evidence(mn_runtime_evidence)

        self.assertFalse(result["ok"])
        self.assertEqual(
            result["requiredNativeHandlerFeatures"],
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
        self.assertIn("missing-native-handler-feature:native-highlight-arm-next-selection-default", result["problems"])
        self.assertIn("missing-native-handler-feature:native-highlight-prefer-next-selection-v1", result["problems"])
        self.assertIn("missing-native-handler-feature:native-highlight-command-prepared", result["problems"])
        self.assertIn("missing-native-handler-feature:selection-popup-diagnostics-v1", result["problems"])
        self.assertIn("missing-native-handler-feature:native-highlight-selection-poll-v1", result["problems"])
        self.assertIn("missing-native-handler-feature:selection-popup-scene-observer-v1", result["problems"])

    def test_mn_runtime_evidence_rejects_when_current_runtime_sources_are_newer(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "codex.mn.assistant"
            (extension / "web").mkdir(parents=True)
            source = extension / "web/app.js"
            source.write_text("new runtime asset\n", encoding="utf-8")
            os.utime(source, (2_000_000_000, 2_000_000_000))
            module.LIVE_EXTENSION = extension
            mn_runtime_evidence = {
                "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "statusAfter": {
                    "mnRuntime": {
                        "ready": True,
                        "webControlsReady": True,
                        "nativeApiReady": True,
                        "staleRuntime": False,
                        "runtimeHandlerStale": False,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "sourceMtime": 1_900_000_000,
                        "latestEventTs": "2030-03-17T17:46:40+0800",
                    },
                    "nativeApiCapabilities": {
                        "available": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "capabilityMatrix": {"nativeCards": {"ready": True}},
                    },
                },
            }

            result = module.validate_mn_runtime_evidence(mn_runtime_evidence)

        self.assertFalse(result["ok"])
        self.assertIn("runtime-evidence-stale-against-current-source", result["problems"])
        self.assertEqual(result["currentRuntimeSource"]["path"], str(source))

    def test_prevalidated_mn_runtime_evidence_is_rechecked_against_current_sources(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            extension = Path(tmp) / "codex.mn.assistant"
            (extension / "web").mkdir(parents=True)
            source = extension / "web/index.html"
            source.write_text("<html>new</html>\n", encoding="utf-8")
            os.utime(source, (2_000_000_000, 2_000_000_000))
            module.LIVE_EXTENSION = extension
            mn_runtime_validation = {
                "ok": True,
                "problems": [],
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "mnRuntime": {
                    "ready": True,
                    "webControlsReady": True,
                    "nativeApiReady": True,
                    "staleRuntime": False,
                    "runtimeHandlerStale": False,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "sourceMtime": 1_900_000_000,
                },
                "nativeApiCapabilities": {
                    "available": True,
                    "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    "capabilityMatrix": {"nativeCards": {"ready": True}},
                },
            }

            result = module.validate_mn_runtime_evidence(mn_runtime_validation)

        self.assertFalse(result["ok"])
        self.assertIn("runtime-evidence-stale-against-current-source", result["problems"])
        self.assertEqual(result["currentRuntimeSource"]["path"], str(source))

    def test_collect_native_highlight_evidence_checks_blobs_for_latest_posted_scope(self) -> None:
        module = self.load_module()
        posted = {
            "event": "nativeHighlightSelectionPosted",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
        }

        with patch.object(module, "run_doctor_json", return_value=([], {"ok": True})), \
            patch.object(module, "read_recent_plugin_events", return_value=[posted]), \
            patch.object(
                module,
                "check_native_highlight_blobs_for_event",
                return_value={"status": "OK", "topicid": "topic-a", "bookmd5": "book-a", "native_highlight_blobs": 1},
            ) as blob_check:
            evidence = module.collect_native_highlight_evidence()

        self.assertTrue(evidence["ok"], evidence)
        blob_check.assert_called_once_with(posted)
        self.assertEqual(evidence["highlightBlobCheck"]["topicid"], "topic-a")

    def test_collect_native_highlight_evidence_can_try_highlight_before_collecting(self) -> None:
        module = self.load_module()
        before = [
            {
                "event": "nativeApiCapabilities",
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "topicid": "topic-a",
                "bookmd5": "book-a",
            }
        ]
        posted = {
            "event": "nativeHighlightSelectionPosted",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
        }
        calls: list[tuple[str, str, dict[str, object]]] = []

        def fake_post(base_url: str, path: str, payload: dict[str, object], timeout: int = 30) -> dict[str, object]:
            calls.append((base_url, path, payload))
            return {"ok": True, "queued": {"id": "Q1"}}

        with patch.object(module, "run_doctor_json", return_value=([], {"ok": True})), \
            patch.object(module, "read_recent_plugin_events", side_effect=[before, before + [posted], before + [posted]]), \
            patch.object(
                module,
                "check_native_highlight_blobs_for_event",
                return_value={"status": "OK", "topicid": "topic-a", "bookmd5": "book-a", "native_highlight_blobs": 1},
            ):
            evidence = module.collect_native_highlight_evidence(
                try_native_highlight=True,
                base_url="http://127.0.0.1:48761",
                topicid="topic-a",
                bookmd5="book-a",
                selection_text="Attention guided safety filter",
                timeout_seconds=0.1,
                interval_seconds=0.01,
                post=fake_post,
            )

        self.assertTrue(evidence["ok"], evidence)
        self.assertEqual(calls[0][0], "http://127.0.0.1:48761")
        self.assertEqual(calls[0][1], "/marginnote/action")
        self.assertEqual(calls[0][2]["action"], "request_native_highlight_selection")
        self.assertEqual(calls[0][2]["topicid"], "topic-a")
        self.assertEqual(calls[0][2]["bookmd5"], "book-a")
        self.assertEqual(calls[0][2]["selectionText"], "Attention guided safety filter")
        self.assertEqual(evidence["highlightAttempt"]["request"]["queued"]["id"], "Q1")
        self.assertEqual(evidence["highlightAttempt"]["event"]["event"], "nativeHighlightSelectionPosted")

    def test_wait_for_native_highlight_result_reports_failed_event(self) -> None:
        module = self.load_module()
        failed = {
            "event": "nativeHighlightSelectionFailed",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"reason": "missing-selection"},
        }
        reads = [
            [{"event": "nativeApiCapabilities", "pluginVersion": module.CURRENT_PLUGIN_VERSION}],
            [{"event": "nativeApiCapabilities", "pluginVersion": module.CURRENT_PLUGIN_VERSION}, failed],
        ]

        with patch.object(module, "read_recent_plugin_events", side_effect=reads):
            result = module.wait_for_native_highlight_result(previous_event_count=1, timeout_seconds=0.2, interval_seconds=0.01)

        self.assertFalse(result["ok"])
        self.assertEqual(result["event"]["event"], "nativeHighlightSelectionFailed")
        self.assertEqual(result["reason"], "missing-selection")

    def test_wait_for_native_highlight_result_reports_armed_next_selection_event(self) -> None:
        module = self.load_module()
        armed = {
            "event": "nativeHighlightNextSelectionArmed",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"reason": "missing-selection"},
        }
        reads = [[{"event": "nativeApiCapabilities", "pluginVersion": module.CURRENT_PLUGIN_VERSION}, armed]]

        with patch.object(module, "read_recent_plugin_events", side_effect=reads):
            result = module.wait_for_native_highlight_result(previous_event_count=1, timeout_seconds=0, interval_seconds=0.01)

        self.assertFalse(result["ok"])
        self.assertEqual(result["event"]["event"], "nativeHighlightNextSelectionArmed")
        self.assertEqual(result["reason"], "armed-next-selection")

    def test_wait_for_native_highlight_result_waits_through_armed_event_until_posted(self) -> None:
        module = self.load_module()
        armed = {
            "event": "nativeHighlightNextSelectionArmed",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"reason": "missing-selection"},
        }
        posted = {
            "event": "nativeHighlightSelectionPosted",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"selectionLength": 32},
        }
        reads = [
            [{"event": "nativeApiCapabilities", "pluginVersion": module.CURRENT_PLUGIN_VERSION}, armed],
            [{"event": "nativeApiCapabilities", "pluginVersion": module.CURRENT_PLUGIN_VERSION}, armed, posted],
        ]

        with patch.object(module, "read_recent_plugin_events", side_effect=reads):
            result = module.wait_for_native_highlight_result(previous_event_count=1, timeout_seconds=0.2, interval_seconds=0.01)

        self.assertTrue(result["ok"])
        self.assertEqual(result["event"]["event"], "nativeHighlightSelectionPosted")
        self.assertEqual(result["reason"], "")

    def test_collect_native_highlight_evidence_keeps_armed_attempt_as_blocker_not_timeout(self) -> None:
        module = self.load_module()
        before = [
            {
                "event": "nativeApiCapabilities",
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "topicid": "topic-a",
                "bookmd5": "book-a",
            }
        ]
        armed = {
            "event": "nativeHighlightNextSelectionArmed",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"reason": "missing-selection"},
        }
        calls: list[tuple[str, str, dict[str, object]]] = []

        def fake_post(base_url: str, path: str, payload: dict[str, object], timeout: int = 30) -> dict[str, object]:
            calls.append((base_url, path, payload))
            return {"ok": True, "queued": {"id": "Q-ARMED"}}

        with patch.object(module, "run_doctor_json", return_value=([], {"ok": True})), \
            patch.object(module, "read_recent_plugin_events", side_effect=[before, before + [armed], before + [armed]]), \
            patch.object(
                module,
                "check_native_highlight_blobs_for_event",
                return_value={"status": "WARN", "topicid": "", "bookmd5": "", "native_highlight_blobs": 0},
            ):
            evidence = module.collect_native_highlight_evidence(
                try_native_highlight=True,
                base_url="http://127.0.0.1:48761",
                topicid="topic-a",
                bookmd5="book-a",
                timeout_seconds=0,
                interval_seconds=0.01,
                post=fake_post,
            )

        self.assertEqual(len(calls), 1)
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["highlightAttempt"]["reason"], "armed-next-selection")
        self.assertEqual(evidence["highlightAttempt"]["cleanup"]["reason"], "native-highlight-attempt-finished")
        self.assertIn("native-highlight-attempt-armed-next-selection", evidence["problems"])
        self.assertIn("missing-nativeHighlightSelectionPosted", evidence["problems"])

    def test_wait_for_native_highlight_result_handles_truncated_event_window(self) -> None:
        module = self.load_module()
        before_last = {
            "ts": "2026-06-12T11:33:18+0800",
            "event": "nativeApiCapabilities",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
        }
        failed = {
            "ts": "2026-06-12T11:33:20+0800",
            "event": "nativeHighlightSelectionFailed",
            "pluginVersion": module.CURRENT_PLUGIN_VERSION,
            "topicid": "topic-a",
            "bookmd5": "book-a",
            "extra": {"reason": "missing-selection"},
        }
        truncated_window = [
            {"ts": "2026-06-12T11:33:19+0800", "event": "commandsReceived", "pluginVersion": module.CURRENT_PLUGIN_VERSION}
        ] * 1999 + [failed]

        with patch.object(module, "read_recent_plugin_events", return_value=truncated_window):
            result = module.wait_for_native_highlight_result(
                previous_event_count=2000,
                timeout_seconds=0.2,
                interval_seconds=0.01,
                previous_latest_event=before_last,
            )

        self.assertFalse(result["ok"])
        self.assertEqual(result["event"]["event"], "nativeHighlightSelectionFailed")
        self.assertEqual(result["reason"], "missing-selection")

    def test_collect_native_highlight_evidence_cleans_timed_out_request_queue_item(self) -> None:
        module = self.load_module()
        before = [
            {
                "event": "nativeApiCapabilities",
                "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                "topicid": "topic-a",
                "bookmd5": "book-a",
            }
        ]
        calls: list[tuple[str, str, dict[str, object]]] = []

        def fake_post(base_url: str, path: str, payload: dict[str, object], timeout: int = 30) -> dict[str, object]:
            calls.append((base_url, path, payload))
            if path == "/marginnote/action":
                return {"ok": True, "queued": {"id": "Q-TIMEOUT"}}
            return {"ok": True, "removed": 1}

        with patch.object(module, "run_doctor_json", return_value=([], {"ok": True})), \
            patch.object(module, "read_recent_plugin_events", return_value=before), \
            patch.object(
                module,
                "check_native_highlight_blobs_for_event",
                return_value={"status": "WARN", "topicid": "", "bookmd5": "", "native_highlight_blobs": 0},
            ):
            evidence = module.collect_native_highlight_evidence(
                try_native_highlight=True,
                base_url="http://127.0.0.1:48761",
                topicid="topic-a",
                bookmd5="book-a",
                timeout_seconds=0,
                interval_seconds=0.01,
                post=fake_post,
            )

        self.assertEqual(calls[0][1], "/marginnote/action")
        self.assertEqual(calls[1][1], "/marginnote/ack")
        self.assertEqual(calls[1][2]["ids"], ["Q-TIMEOUT"])
        self.assertEqual(evidence["highlightAttempt"]["reason"], "timeout")
        self.assertEqual(evidence["highlightAttempt"]["cleanup"]["removed"], 1)

    def test_native_highlight_event_reader_falls_back_to_project_events_without_companion_import(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            project_root = Path(tmp)
            event = {"event": "nativeHighlightSelectionPosted", "pluginVersion": module.CURRENT_PLUGIN_VERSION}
            (project_root / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")
            module.LAYOUT["projectRoot"] = project_root

            real_import = __import__

            def fake_import(name, *args, **kwargs):
                if name == "companion":
                    raise ImportError("no packaged companion module")
                return real_import(name, *args, **kwargs)

            with patch("builtins.__import__", side_effect=fake_import):
                rows = module.read_recent_plugin_events()

        self.assertTrue(rows, "event reader should read project events.jsonl even when companion import fails")
        self.assertEqual(rows[-1]["event"], "nativeHighlightSelectionPosted")

    def test_acceptance_surfaces_release_maintainer_prerequisites_as_warning_not_blocker(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "OK", "detail": "controls loaded"},
            {"name": "MN4 native API probe", "status": "OK", "detail": "ready_actions=3 capability_matrix=True"},
            {"name": "Native highlight blobs", "status": "OK", "detail": "2 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "OK", "detail": "local and OneDrive SHA256SUMS match"},
            {
                "name": "Latest RC pkg",
                "status": "OK",
                "detail": "signed notarized nopayload pkg; local and OneDrive hashes match",
                "evidence": {"signed": True, "notarized": True, "staplerReturnCode": 0, "spctlReturnCode": 0},
            },
            {
                "name": "Release maintainer prerequisites",
                "status": "WARN",
                "detail": "missing_developer_id_installer; missing_notary_credentials",
            },
        ]

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=doctor_checks,
            cross_machine_verified=True,
        )

        self.assertTrue(report["releasable"], report)
        warnings = {item["name"]: item for item in report["warnings"]}
        self.assertIn("release_maintainer_prerequisites", warnings)
        self.assertIn("missing_developer_id_installer", warnings["release_maintainer_prerequisites"]["detail"])

    def test_acceptance_reports_missing_doctor_checks_as_blockers(self) -> None:
        module = self.load_module()

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}},
            doctor_checks=[],
            cross_machine_verified=True,
        )

        blockers = {item["name"] for item in report["gates"] if item["status"] == "BLOCK"}
        self.assertIn("runtime_web_controls", blockers)
        self.assertIn("native_api_matrix", blockers)
        self.assertIn("native_visible_highlight", blockers)
        self.assertIn("release_sha256_manifest", blockers)
        self.assertIn("signed_pkg", blockers)
        self.assertIn("notarized_pkg", blockers)

    def test_blocked_gates_include_actionable_next_actions(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 runtime Web controls", "status": "WARN", "detail": "stale runtime event"},
            {
                "name": "MN4 native API probe",
                "status": "WARN",
                "detail": "runtime_handler_stale=True",
            },
            {"name": "Native highlight blobs", "status": "WARN", "detail": "0 rows have ZHIGHLIGHTS"},
            {"name": "Release SHA256 manifest", "status": "WARN", "detail": "zip_mismatch"},
            {
                "name": "Latest RC pkg",
                "status": "WARN",
                "detail": "no signature",
                "evidence": {"signed": False, "notarized": False},
            },
        ]

        report = module.evaluate_acceptance(
            unit_tests_ok=True,
            syntax_ok=True,
            smoke={"ok": True, "installDryRun": {"ok": True}, "sha256": "abc123"},
            doctor_checks=doctor_checks,
            cross_machine_verified=False,
        )

        blockers = {item["name"]: item for item in report["blockers"]}
        for name in [
            "runtime_web_controls",
            "native_api_matrix",
            "native_visible_highlight",
            "release_sha256_manifest",
            "signed_pkg",
            "notarized_pkg",
            "cross_machine_install",
        ]:
            self.assertTrue(blockers[name]["nextActions"], name)
        self.assertIn("restart_marginnote4", "\n".join(blockers["runtime_web_controls"]["nextActions"]))
        self.assertIn("Refresh MN", "\n".join(blockers["native_api_matrix"]["nextActions"]))
        self.assertIn("高亮选区", "\n".join(blockers["native_visible_highlight"]["nextActions"]))
        self.assertIn("SHA256SUMS", "\n".join(blockers["release_sha256_manifest"]["nextActions"]))
        self.assertIn("Build Signed Package.command", "\n".join(blockers["signed_pkg"]["nextActions"]))
        self.assertIn("Notarize Package.command", "\n".join(blockers["notarized_pkg"]["nextActions"]))
        self.assertIn("Collect Cross-Machine Evidence.command", "\n".join(blockers["cross_machine_install"]["nextActions"]))

    def test_runtime_next_actions_prioritize_reopening_panel_when_reload_command_is_unknown(self) -> None:
        module = self.load_module()

        runtime_actions = module.next_actions_for_gate(
            "runtime_web_controls",
            "runtime handler does not know ['reload_web_panel']; stale runtime event",
        )
        native_actions = module.next_actions_for_gate(
            "native_api_matrix",
            "runtime_handler_stale=True; MN4 runtime treated ['reload_web_panel'] as unknown",
        )

        self.assertIn("关闭再重新打开 Codex 面板", runtime_actions[0])
        self.assertIn("Refresh MN Runtime.command", "\n".join(runtime_actions))
        self.assertIn("设置页", "\n".join(runtime_actions))
        self.assertIn("发布验收结果", "\n".join(runtime_actions))
        self.assertNotIn("stale-runtime recovery button", "\n".join(runtime_actions))
        self.assertNotIn("面板里使用重启 MN4 恢复按钮", "\n".join(runtime_actions))
        self.assertIn("关闭再重新打开 Codex 面板", native_actions[0])
        self.assertIn("reload_web_panel", "\n".join(native_actions))
        self.assertNotIn("restart_marginnote4 recovery button", "\n".join(native_actions))

    def test_sha256_manifest_permission_blocker_points_to_full_disk_access(self) -> None:
        module = self.load_module()

        actions = module.next_actions_for_gate(
            "release_sha256_manifest",
            "permission_denied: grant Full Disk Access to the Companion service/Python and retry",
        )

        self.assertIn("Full Disk Access", "\n".join(actions))
        self.assertIn("SHA256SUMS.txt", "\n".join(actions))

    def test_print_text_shows_blocker_next_actions(self) -> None:
        module = self.load_module()
        report = {
            "releasable": False,
            "gates": [
                {
                    "name": "signed_pkg",
                    "status": "BLOCK",
                    "detail": "no signature",
                    "nextActions": ["Run Build Signed Package.command."],
                },
                {
                    "name": "unit_tests",
                    "status": "PASS",
                    "detail": "unit test suite passed",
                    "nextActions": [],
                },
            ],
        }

        with patch("builtins.print") as printed:
            module.print_text(report)

        output = "\n".join(" ".join(str(arg) for arg in call.args) for call in printed.call_args_list)
        self.assertIn("Next actions:", output)
        self.assertIn("Run Build Signed Package.command.", output)

    def test_run_can_keep_full_stdout_for_large_doctor_json(self) -> None:
        module = self.load_module()

        class Completed:
            returncode = 0
            stdout = "x" * 5000
            stderr = "err"

        with patch.object(module.subprocess, "run", return_value=Completed()):
            result = module.run(["doctor"], stdout_limit=None)

        self.assertEqual(result["stdout"], "x" * 5000)
        self.assertEqual(result["stderr"], "err")

    def test_run_unit_tests_extracts_release_extension_for_web_static_tests(self) -> None:
        module = self.load_module()
        captured: dict[str, object] = {}

        class Completed:
            returncode = 0
            stdout = "ok"
            stderr = ""

        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "CodexCompanion-test-dist.zip"
            with zipfile.ZipFile(package, "w") as archive:
                archive.writestr("CodexCompanion-test/extension/codex.mn.assistant/web/index.html", "<html></html>")
                archive.writestr("CodexCompanion-test/extension/codex.mn.assistant/web/app.js", "console.log('ok');\n")
                archive.writestr("CodexCompanion-test/extension/codex.mn.assistant/web/app.css", "body{}\n")
                archive.writestr("CodexCompanion-test/extension/codex.mn.assistant/CodexWebPanelController.js", "// ok\n")
                archive.writestr("CodexCompanion-test/extension/codex.mn.assistant/mnaddon.json", "{}\n")

            def fake_run(args: list[str], **kwargs: object) -> Completed:
                captured["args"] = args
                captured["env"] = kwargs.get("env")
                return Completed()

            with patch.object(module.subprocess, "run", side_effect=fake_run):
                result = module.run_unit_tests(package)

        env = captured["env"]
        self.assertTrue(result["ok"])
        self.assertIsInstance(env, dict)
        ext_dir = Path(env["CODEX_MN_TEST_EXTENSION_DIR"])  # type: ignore[index]
        self.assertTrue(str(ext_dir).endswith("extension/codex.mn.assistant"))
        self.assertIn("/opt/homebrew/bin", env["PATH"])  # type: ignore[index]

    def test_compact_command_result_removes_large_stdout_from_report(self) -> None:
        module = self.load_module()

        compact = module.compact_command_result(
            {
                "args": ["doctor"],
                "returncode": 1,
                "stdout": "x" * 5000,
                "stderr": "warning",
                "ok": False,
            },
            parsed_items=16,
        )

        self.assertEqual(compact["stdout"], "<parsed 16 JSON items>")
        self.assertEqual(compact["stdoutLength"], 5000)
        self.assertEqual(compact["stderr"], "warning")

    def test_project_paths_work_from_development_root(self) -> None:
        module = self.load_module()
        paths = module.resolve_layout(ACCEPTANCE_PATH.parent)

        self.assertEqual(paths["projectRoot"], ACCEPTANCE_PATH.parent)
        self.assertEqual(paths["doctor"], ACCEPTANCE_PATH.parent / "doctor.py")
        self.assertEqual(paths["tests"], ACCEPTANCE_PATH.parent / "tests")

    def test_project_paths_work_from_release_package_root(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            package_root = Path(tmp) / "CodexCompanion-test"
            companion_root = package_root / "companion"
            (companion_root / "tests").mkdir(parents=True)
            (companion_root / "doctor.py").write_text("print('doctor')\n", encoding="utf-8")
            (companion_root / "release_acceptance.py").write_text("# nested copy\n", encoding="utf-8")
            package_root.mkdir(exist_ok=True)
            (package_root / "release_acceptance.py").write_text("# root copy\n", encoding="utf-8")

            paths = module.resolve_layout(package_root)

            self.assertEqual(paths["projectRoot"], companion_root.resolve())
            self.assertEqual(paths["doctor"], (companion_root / "doctor.py").resolve())
            self.assertEqual(paths["tests"], (companion_root / "tests").resolve())

    def test_cross_machine_evidence_requires_schema_hash_install_checks_and_different_identity(self) -> None:
        module = self.load_module()
        evidence = {
            "schema": "codex-companion-cross-machine-install-v1",
            "environment": {"host": "other-mac", "user": "tester"},
            "package": {"sha256": "abc123"},
            "doctor": {
                "checks": [
                    {"name": "MN4 extension manifest", "status": "OK"},
                    {"name": "Companion service", "status": "OK"},
                    {"name": "LaunchAgent", "status": "OK"},
                ]
            },
        }

        result = module.validate_cross_machine_evidence(
            evidence,
            expected_package_sha256="abc123",
            current_identity={"host": "this-mac", "user": "liuwhale"},
        )

        self.assertTrue(result["ok"], result)

    def test_cross_machine_evidence_rejects_same_identity_or_wrong_hash(self) -> None:
        module = self.load_module()
        evidence = {
            "schema": "codex-companion-cross-machine-install-v1",
            "environment": {"host": "this-mac", "user": "liuwhale"},
            "package": {"sha256": "wrong"},
            "doctor": {"checks": []},
        }

        result = module.validate_cross_machine_evidence(
            evidence,
            expected_package_sha256="abc123",
            current_identity={"host": "this-mac", "user": "liuwhale"},
        )

        self.assertFalse(result["ok"])
        self.assertIn("package-sha256-mismatch", result["problems"])
        self.assertIn("same-host-and-user", result["problems"])
        self.assertIn("missing-ok-check:MN4 extension manifest", result["problems"])

    def test_collect_cross_machine_evidence_writes_schema_and_doctor_checks(self) -> None:
        module = self.load_module()
        doctor_checks = [
            {"name": "MN4 extension manifest", "status": "OK"},
            {"name": "Companion service", "status": "OK"},
            {"name": "LaunchAgent", "status": "OK"},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "pkg.zip"
            package.write_bytes(b"pkg")
            expected_sha = module.sha256_file(package)

            with patch.object(module, "machine_identity", return_value={"host": "h", "user": "u"}), patch.object(
                module, "run_doctor_json", return_value=(doctor_checks, {"ok": True})
            ):
                evidence = module.collect_cross_machine_evidence(package)

        self.assertEqual(evidence["schema"], "codex-companion-cross-machine-install-v1")
        self.assertEqual(evidence["environment"], {"host": "h", "user": "u"})
        self.assertEqual(evidence["doctor"]["checks"], doctor_checks)
        self.assertEqual(evidence["package"]["sha256"], expected_sha)

    def test_auto_discovers_latest_non_template_evidence_by_schema(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            template = root / "cross-machine-evidence-template.json"
            template.write_text(
                json.dumps({"schema": module.EVIDENCE_SCHEMA, "ok": False}, ensure_ascii=False),
                encoding="utf-8",
            )
            older = root / "codex-companion-cross-machine-evidence-20260611-010000.json"
            older.write_text(
                json.dumps({"schema": module.EVIDENCE_SCHEMA, "generatedAt": "old"}, ensure_ascii=False),
                encoding="utf-8",
            )
            latest = root / "codex-companion-cross-machine-evidence-20260611-020000.json"
            latest.write_text(
                json.dumps({"schema": module.EVIDENCE_SCHEMA, "generatedAt": "latest"}, ensure_ascii=False),
                encoding="utf-8",
            )

            discovered = module.discover_evidence_file(
                module.EVIDENCE_SCHEMA,
                module.CROSS_MACHINE_EVIDENCE_PATTERNS,
                [root],
            )

            self.assertEqual(discovered, latest)

    def test_missing_cli_evidence_path_uses_auto_discovered_cross_machine_file(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "CodexCompanion-0.4.9-latest-dist.zip"
            package.write_bytes(b"pkg")
            expected_sha = module.sha256_file(package)
            evidence = {
                "schema": module.EVIDENCE_SCHEMA,
                "environment": {"host": "other-mac", "user": "tester"},
                "package": {"sha256": expected_sha},
                "doctor": {
                    "checks": [
                        {"name": "MN4 extension manifest", "status": "OK"},
                        {"name": "Companion service", "status": "OK"},
                        {"name": "LaunchAgent", "status": "OK"},
                    ]
                },
            }
            evidence_path = root / "codex-companion-cross-machine-evidence-20260611-020000.json"
            evidence_path.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")

            result = module.cross_machine_evidence_result(
                None,
                expected_package_sha256=expected_sha,
                search_dirs=[root],
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["path"], str(evidence_path))
            self.assertTrue(result["autoDiscovered"])

    def test_auto_discovery_prefers_latest_valid_cross_machine_evidence_over_newer_invalid_file(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "CodexCompanion-0.4.9-latest-dist.zip"
            package.write_bytes(b"pkg")
            expected_sha = module.sha256_file(package)
            valid = {
                "schema": module.EVIDENCE_SCHEMA,
                "environment": {"host": "other-mac", "user": "tester"},
                "package": {"sha256": expected_sha},
                "doctor": {
                    "checks": [
                        {"name": "MN4 extension manifest", "status": "OK"},
                        {"name": "Companion service", "status": "OK"},
                        {"name": "LaunchAgent", "status": "OK"},
                    ]
                },
            }
            invalid = {
                "schema": module.EVIDENCE_SCHEMA,
                "environment": {"host": "other-mac", "user": "tester"},
                "package": {"sha256": "older-package"},
                "doctor": {"checks": []},
            }
            valid_path = root / "codex-companion-cross-machine-evidence-20260611-010000.json"
            invalid_path = root / "codex-companion-cross-machine-evidence-20260611-020000.json"
            valid_path.write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")

            result = module.cross_machine_evidence_result(
                None,
                expected_package_sha256=expected_sha,
                search_dirs=[root],
            )

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["path"], str(valid_path))
            self.assertTrue(result["autoDiscovered"])

    def test_auto_discovery_prefers_latest_valid_native_highlight_evidence_over_newer_invalid_file(self) -> None:
        module = self.load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            valid = {
                "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
                "events": {
                    "latestPosted": {
                        "event": "nativeHighlightSelectionPosted",
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "topicid": "topic-a",
                        "bookmd5": "book-a",
                    }
                },
                "highlightBlobCheck": {
                    "status": "OK",
                    "topicid": "topic-a",
                    "bookmd5": "book-a",
                    "native_highlight_blobs": 1,
                },
            }
            invalid = {
                "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
                "events": {},
                "highlightBlobCheck": {"status": "WARN", "native_highlight_blobs": 0},
            }
            valid_path = root / "codex-companion-native-highlight-evidence-20260611-010000.json"
            invalid_path = root / "codex-companion-native-highlight-evidence-20260611-020000.json"
            valid_path.write_text(json.dumps(valid, ensure_ascii=False), encoding="utf-8")
            invalid_path.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")

            result = module.native_highlight_evidence_result(None, search_dirs=[root])

            self.assertTrue(result["ok"], result)
            self.assertEqual(result["path"], str(valid_path))
            self.assertTrue(result["autoDiscovered"])


if __name__ == "__main__":
    unittest.main()
