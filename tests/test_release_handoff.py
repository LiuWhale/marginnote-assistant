from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HANDOFF_PATH = Path(__file__).resolve().parents[1] / "prepare_release_handoff.py"


def load_module():
    spec = importlib.util.spec_from_file_location("codex_mn_release_handoff", HANDOFF_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


class ReleaseHandoffTests(unittest.TestCase):
    def test_build_handoff_bundle_copies_artifacts_and_writes_gate_next_actions(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_pkg = root / "CodexCompanion-0.4.1-latest.pkg"
            package_zip.write_bytes(b"zip payload")
            package_pkg.write_bytes(b"pkg payload")
            report = {
                "releasable": False,
                "blockers": [
                    {
                        "name": "native_visible_highlight",
                        "detail": "0 rows have ZHIGHLIGHTS",
                        "nextActions": ["Open PDF, select text, click 高亮选区."],
                    },
                    {
                        "name": "signed_pkg",
                        "detail": "no signature",
                        "nextActions": ["Run Build Signed Package.command."],
                    },
                ],
                "warnings": [
                    {
                        "name": "release_maintainer_prerequisites",
                        "detail": "missing Developer ID Installer",
                        "nextActions": ["Install certificate."],
                    }
                ],
                "gates": [],
            }

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=package_pkg,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=root / "OneDrive",
                timestamp="20260611-130000",
            )

            self.assertTrue(result["ok"])
            bundle_dir = Path(result["bundleDir"])
            self.assertTrue((bundle_dir / package_zip.name).exists())
            self.assertTrue((bundle_dir / package_pkg.name).exists())
            self.assertTrue((bundle_dir / "release_acceptance.json").exists())
            self.assertTrue((bundle_dir / "SHA256SUMS.txt").exists())
            self.assertTrue((bundle_dir / "mn-runtime-evidence-template.json").exists())
            self.assertTrue((bundle_dir / "native-highlight-evidence-template.json").exists())
            self.assertTrue((bundle_dir / "cross-machine-evidence-template.json").exists())
            self.assertTrue((bundle_dir / "single-document-acceptance-template.json").exists())
            handoff = (bundle_dir / "RELEASE_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("native_visible_highlight", handoff)
            self.assertIn("Open PDF, select text, click 高亮选区.", handoff)
            self.assertIn("signed_pkg", handoff)
            self.assertIn("Run Build Signed Package.command.", handoff)
            self.assertIn("release_maintainer_prerequisites", handoff)
            self.assertIn(package_zip.name, handoff)
            self.assertIn(package_pkg.name, handoff)
            self.assertTrue(Path(result["bundleZip"]).exists())
            self.assertTrue(Path(result["onedriveBundleDir"]).exists())
            self.assertTrue(Path(result["onedriveBundleZip"]).exists())

    def test_evidence_templates_use_acceptance_schemas_and_placeholder_fields(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
            )

            bundle_dir = Path(result["bundleDir"])
            native_template = json.loads(
                (bundle_dir / "native-highlight-evidence-template.json").read_text(encoding="utf-8")
            )
            runtime_template = json.loads(
                (bundle_dir / "mn-runtime-evidence-template.json").read_text(encoding="utf-8")
            )
            cross_template = json.loads(
                (bundle_dir / "cross-machine-evidence-template.json").read_text(encoding="utf-8")
            )
            single_doc_template = json.loads(
                (bundle_dir / "single-document-acceptance-template.json").read_text(encoding="utf-8")
            )
            self.assertEqual(native_template["schema"], module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA)
            self.assertEqual(runtime_template["schema"], module.MN_RUNTIME_EVIDENCE_SCHEMA)
            self.assertEqual(cross_template["schema"], module.CROSS_MACHINE_EVIDENCE_SCHEMA)
            self.assertEqual(single_doc_template["schema"], module.SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA)
            self.assertEqual(runtime_template["pluginVersion"], module.CURRENT_PLUGIN_VERSION)
            self.assertEqual(native_template["pluginVersion"], module.CURRENT_PLUGIN_VERSION)
            self.assertEqual(single_doc_template["pluginVersion"], module.CURRENT_PLUGIN_VERSION)
            self.assertIn("statusAfter", runtime_template)
            self.assertIn("events", native_template)
            self.assertIn("installChecks", cross_template)
            self.assertIn("checks", single_doc_template)
            self.assertFalse(runtime_template["ok"])
            self.assertFalse(native_template["ok"])
            self.assertFalse(cross_template["ok"])
            self.assertFalse(single_doc_template["ok"])

    def test_handoff_native_highlight_instructions_use_active_collection_flow(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
            )

            bundle_dir = Path(result["bundleDir"])
            handoff = (bundle_dir / "RELEASE_HANDOFF.md").read_text(encoding="utf-8")
            native_template = json.loads(
                (bundle_dir / "native-highlight-evidence-template.json").read_text(encoding="utf-8")
            )
            self.assertIn("--try-native-highlight", handoff)
            self.assertIn("nativeHighlightSelectionPosted", handoff)
            self.assertIn("single_document_acceptance.py", handoff)
            self.assertIn("Collect Single Document Acceptance.command", handoff)
            self.assertIn("highlightAttempt", native_template)

    def test_build_handoff_bundle_copies_discovered_evidence_files(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            native_evidence = evidence_dir / "codex-companion-native-highlight-evidence-20260611-020000.json"
            native_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
                        "ok": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
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
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            copied = bundle_dir / "evidence" / native_evidence.name
            self.assertTrue(copied.exists())
            self.assertIn(f"evidence/{native_evidence.name}", result["includedFiles"])
            self.assertIn(
                f"evidence/{native_evidence.name}",
                (bundle_dir / "SHA256SUMS.txt").read_text(encoding="utf-8"),
            )
            self.assertIn(
                f"evidence/{native_evidence.name}",
                (bundle_dir / "RELEASE_HANDOFF.md").read_text(encoding="utf-8"),
            )

    def test_handoff_marks_stale_runtime_evidence_as_diagnostic_not_release_proof(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            runtime_evidence = evidence_dir / "CodexCompanion-MNRuntimeEvidence-20260611-020000.json"
            runtime_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                        "ok": False,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "mnRuntime": {
                            "ready": False,
                            "runtimeHandlerStale": True,
                            "runtimeHandlerStaleActions": ["reload_web_panel"],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {
                "releasable": False,
                "blockers": [{"name": "runtime_web_controls", "detail": "stale runtime"}],
                "warnings": [],
                "gates": [],
            }

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertFalse((bundle_dir / "evidence" / runtime_evidence.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / runtime_evidence.name).exists())
            self.assertIn(f"diagnostics/evidence/{runtime_evidence.name}", result["includedFiles"])
            self.assertNotIn(f"evidence/{runtime_evidence.name}", result["includedFiles"])
            handoff = (bundle_dir / "RELEASE_HANDOFF.md").read_text(encoding="utf-8")
            self.assertIn("Diagnostic Evidence", handoff)
            self.assertIn("not release proof", handoff)
            self.assertIn(f"diagnostics/evidence/{runtime_evidence.name}", handoff)

    def test_collect_acceptance_report_passes_release_proof_runtime_evidence(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            runtime_evidence = evidence_dir / "CodexCompanion-MNRuntimeEvidence-20260612-010000.json"
            runtime_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                        "ok": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "mnRuntime": {
                            "ready": True,
                            "staleRuntime": False,
                            "runtimeHandlerStale": False,
                            "sourceMtime": 9999999999,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            captured: dict[str, object] = {}
            original_run = module.subprocess.run

            def fake_run(command, **kwargs):
                captured["command"] = command
                return subprocess.CompletedProcess(command, 1, stdout='{"releasable": false}', stderr="")

            module.subprocess.run = fake_run
            try:
                report = module.collect_acceptance_report(package_zip, evidence_search_dirs=[evidence_dir])
            finally:
                module.subprocess.run = original_run

            command = captured["command"]
            self.assertIn("--mn-runtime-evidence", command)
            self.assertIn(str(runtime_evidence), command)
            self.assertEqual(
                report["handoffCollection"]["mnRuntimeEvidence"],
                str(runtime_evidence),
            )

    def test_handoff_marks_runtime_evidence_older_than_current_source_as_diagnostic(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            extension = root / "codex.mn.assistant"
            (extension / "web").mkdir(parents=True)
            source = extension / "web/app.css"
            source.write_text("new layout\n", encoding="utf-8")
            os.utime(source, (2_000_000_000, 2_000_000_000))
            module.LIVE_EXTENSION = extension
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            runtime_evidence = evidence_dir / "CodexCompanion-MNRuntimeEvidence-20260611-030000.json"
            runtime_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.MN_RUNTIME_EVIDENCE_SCHEMA,
                        "ok": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "mnRuntime": {
                            "ready": True,
                            "staleRuntime": False,
                            "runtimeHandlerStale": False,
                            "sourceMtime": 1_900_000_000,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertFalse((bundle_dir / "evidence" / runtime_evidence.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / runtime_evidence.name).exists())
            self.assertIn(f"diagnostics/evidence/{runtime_evidence.name}", result["includedFiles"])
            self.assertNotIn(f"evidence/{runtime_evidence.name}", result["includedFiles"])

    def test_handoff_marks_cross_machine_evidence_for_wrong_package_as_diagnostic(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"current zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            cross_evidence = evidence_dir / "codex-companion-cross-machine-evidence-20260611-020000.json"
            cross_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.CROSS_MACHINE_EVIDENCE_SCHEMA,
                        "ok": True,
                        "package": {"sha256": "sha-for-an-older-build"},
                        "installChecks": {
                            "MN4 extension manifest": True,
                            "Companion service": True,
                            "LaunchAgent": True,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {
                "releasable": False,
                "blockers": [{"name": "cross_machine_install", "detail": "missing cross-machine evidence"}],
                "warnings": [],
                "gates": [],
            }

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertFalse((bundle_dir / "evidence" / cross_evidence.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / cross_evidence.name).exists())
            self.assertIn(f"diagnostics/evidence/{cross_evidence.name}", result["includedFiles"])
            self.assertNotIn(f"evidence/{cross_evidence.name}", result["includedFiles"])

    def test_handoff_marks_incomplete_native_highlight_evidence_as_diagnostic(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            native_evidence = evidence_dir / "codex-companion-native-highlight-evidence-20260611-020000.json"
            native_evidence.write_text(
                json.dumps(
                    {
                        "schema": module.NATIVE_HIGHLIGHT_EVIDENCE_SCHEMA,
                        "ok": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {
                "releasable": False,
                "blockers": [{"name": "native_visible_highlight", "detail": "missing native highlight"}],
                "warnings": [],
                "gates": [],
            }

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertFalse((bundle_dir / "evidence" / native_evidence.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / native_evidence.name).exists())
            self.assertIn(f"diagnostics/evidence/{native_evidence.name}", result["includedFiles"])
            self.assertNotIn(f"evidence/{native_evidence.name}", result["includedFiles"])

    def test_handoff_copies_single_document_acceptance_evidence_by_release_status(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            valid = evidence_dir / "codex-companion-single-document-acceptance-20260612-010000.json"
            invalid = evidence_dir / "codex-companion-single-document-acceptance-20260612-020000.json"
            valid.write_text(
                json.dumps(
                    {
                        "schema": module.SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
                        "ok": True,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "topicid": "topic-a",
                        "bookmd5": "book-a",
                        "summary": {"singleDocumentAcceptance": "PASS", "total": 1, "passed": 1, "blocked": 0},
                        "checks": [{"id": "runtime_web_controls", "status": "PASS"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            invalid.write_text(
                json.dumps(
                    {
                        "schema": module.SINGLE_DOCUMENT_ACCEPTANCE_SCHEMA,
                        "ok": False,
                        "pluginVersion": module.CURRENT_PLUGIN_VERSION,
                        "topicid": "topic-a",
                        "bookmd5": "book-a",
                        "summary": {"singleDocumentAcceptance": "BLOCK", "total": 1, "passed": 0, "blocked": 1},
                        "checks": [{"id": "card_write", "status": "BLOCK"}],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertTrue((bundle_dir / "evidence" / valid.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / invalid.name).exists())
            self.assertIn(f"evidence/{valid.name}", result["includedFiles"])
            self.assertIn(f"diagnostics/evidence/{invalid.name}", result["includedFiles"])

    def test_default_evidence_search_dirs_include_diagnostics_evidence(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            diagnostics_dir = root / "release" / "diagnostics" / "evidence"
            diagnostics_dir.mkdir(parents=True)
            package_zip = root / "release" / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"zip payload")
            old_root = module.ROOT
            module.ROOT = root
            try:
                dirs = module.default_evidence_search_dirs(package_zip)
            finally:
                module.ROOT = old_root

        self.assertIn(diagnostics_dir.resolve(), [path.resolve() for path in dirs])

    def test_handoff_keeps_valid_evidence_when_newer_diagnostic_file_exists(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package_zip = root / "CodexCompanion-0.4.1-latest-dist.zip"
            package_zip.write_bytes(b"current zip payload")
            package_sha = module.sha256_file(package_zip)
            evidence_dir = root / "evidence-src"
            evidence_dir.mkdir()
            valid = evidence_dir / "codex-companion-cross-machine-evidence-20260611-010000.json"
            invalid = evidence_dir / "codex-companion-cross-machine-evidence-20260611-020000.json"
            valid.write_text(
                json.dumps(
                    {
                        "schema": module.CROSS_MACHINE_EVIDENCE_SCHEMA,
                        "ok": True,
                        "package": {"sha256": package_sha},
                        "installChecks": {
                            "MN4 extension manifest": True,
                            "Companion service": True,
                            "LaunchAgent": True,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            invalid.write_text(
                json.dumps(
                    {
                        "schema": module.CROSS_MACHINE_EVIDENCE_SCHEMA,
                        "ok": True,
                        "package": {"sha256": "wrong-package"},
                        "installChecks": {
                            "MN4 extension manifest": True,
                            "Companion service": True,
                            "LaunchAgent": True,
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            report = {"releasable": False, "blockers": [], "warnings": [], "gates": []}

            result = module.build_handoff_bundle(
                package_zip=package_zip,
                package_pkg=None,
                acceptance_report=report,
                output_parent=root / "handoff",
                onedrive_parent=None,
                timestamp="20260611-130000",
                evidence_search_dirs=[evidence_dir],
            )

            bundle_dir = Path(result["bundleDir"])
            self.assertTrue((bundle_dir / "evidence" / valid.name).exists())
            self.assertTrue((bundle_dir / "diagnostics" / "evidence" / invalid.name).exists())
            self.assertIn(f"evidence/{valid.name}", result["includedFiles"])
            self.assertIn(f"diagnostics/evidence/{invalid.name}", result["includedFiles"])


if __name__ == "__main__":
    unittest.main()
