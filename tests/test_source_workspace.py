import hashlib
import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import source_workspace


class SourceWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        source_workspace.configure(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def _source(self, name, source_id=None, text_path=None):
        path = self.root / name
        path.write_text(f"contents of {name}\n", encoding="utf-8")
        item = {
            "id": source_id or name,
            "title": Path(name).stem,
            "kind": "pdf" if path.suffix == ".pdf" else "text",
            "path": str(path),
        }
        if text_path is not None:
            item["textPath"] = str(text_path)
        return item

    def test_build_workspace_creates_ordered_links_and_manifest(self):
        first = self.root / "Paper A.pdf"
        second = self.root / "Paper A copy.pdf"
        first.write_bytes(b"a")
        second.write_bytes(b"b")

        result = source_workspace.build_workspace(
            "CONV-1",
            [
                {"id": "src-a", "title": "Paper A", "kind": "pdf", "path": str(first)},
                {"id": "src-b", "title": "Paper A", "kind": "pdf", "path": str(second)},
            ],
            False,
        )

        self.assertTrue(result["ok"], result)
        self.assertEqual(result["sourceCount"], 2)
        self.assertEqual([item["sourceId"] for item in result["sources"]], ["src-a", "src-b"])
        self.assertNotEqual(result["sources"][0]["fileLink"], result["sources"][1]["fileLink"])
        workspace = Path(result["workspacePath"])
        self.assertTrue((workspace / "SOURCES.md").exists())
        self.assertTrue((workspace / "manifest.json").exists())
        self.assertTrue((workspace / "files" / result["sources"][0]["fileLinkName"]).is_symlink())
        manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], source_workspace.SOURCE_WORKSPACE_SCHEMA)
        self.assertFalse(manifest["followCurrentDocument"])
        sources_text = (workspace / "SOURCES.md").read_text(encoding="utf-8")
        self.assertIn("Inspect every listed source before answering.", sources_text)
        self.assertIn("Do not modify any file.", sources_text)

    def test_conversation_id_is_sanitized_and_invalid_ids_are_rejected(self):
        self.assertEqual(source_workspace.safe_conversation_id(" ../CONV 1/ "), "CONV-1")
        self.assertEqual(source_workspace.safe_conversation_id("..."), "")
        with self.assertRaises(ValueError):
            source_workspace.workspace_path("../")
        with self.assertRaises(ValueError):
            source_workspace.build_workspace("../", [], False)

    def test_distinct_conversation_ids_with_same_readable_prefix_use_distinct_workspaces(self):
        colon_source = self._source("colon.txt", "colon")
        dash_source = self._source("dash.txt", "dash")

        colon = source_workspace.build_workspace("A:B", [colon_source], False)
        dash = source_workspace.build_workspace("A-B", [dash_source], False)

        self.assertTrue(colon["ok"] and dash["ok"])
        self.assertNotEqual(colon["workspacePath"], dash["workspacePath"])
        self.assertEqual(source_workspace.load_workspace("A:B")["sources"][0]["sourceId"], "colon")
        self.assertEqual(source_workspace.load_workspace("A-B")["sources"][0]["sourceId"], "dash")

        cleared = source_workspace.clear_workspace("A:B")

        self.assertTrue(cleared["ok"], cleared)
        self.assertFalse(Path(colon["workspacePath"]).exists())
        self.assertTrue(Path(dash["workspacePath"]).is_dir())

    def test_valid_legacy_workspace_falls_back_without_touching_source_or_digest_path(self):
        source = self._source("legacy-owned.txt", "legacy-owned")
        original_contents = Path(source["path"]).read_text(encoding="utf-8")
        built = source_workspace.build_workspace("CONV-LEGACY", [source], False)
        digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.SOURCE_WORKSPACES_DIR / source_workspace.safe_conversation_id("CONV-LEGACY")
        digest_path.rename(legacy_path)

        loaded = source_workspace.load_workspace("CONV-LEGACY")

        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(Path(loaded["workspacePath"]), legacy_path)
        self.assertTrue(legacy_path.is_dir())
        self.assertFalse(digest_path.exists())
        self.assertEqual(loaded["sources"][0]["sourceId"], "legacy-owned")
        self.assertEqual(Path(source["path"]).read_text(encoding="utf-8"), original_contents)

    def test_preexisting_digest_destination_is_never_replaced_by_legacy_fallback(self):
        source = self._source("preexisting-destination.txt", "preexisting")
        conversation_id = "CONV-PREEXISTING"
        built = source_workspace.build_workspace(conversation_id, [source], False)
        digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.legacy_workspace_path(conversation_id)
        digest_path.rename(legacy_path)
        digest_path.mkdir()
        marker = digest_path / "destination-marker.txt"
        marker.write_text("do not replace", encoding="utf-8")
        destination_inode = digest_path.stat().st_ino

        loaded = source_workspace.load_workspace(conversation_id)

        self.assertFalse(loaded["ok"])
        self.assertEqual(digest_path.stat().st_ino, destination_inode)
        self.assertEqual(marker.read_text(encoding="utf-8"), "do not replace")
        self.assertTrue(legacy_path.is_dir())
        self.assertTrue(Path(source["path"]).is_file())

    def test_destination_appearing_during_fallback_is_never_replaced(self):
        source = self._source("racing-destination.txt", "racing")
        conversation_id = "CONV-RACING"
        built = source_workspace.build_workspace(conversation_id, [source], False)
        digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.legacy_workspace_path(conversation_id)
        digest_path.rename(legacy_path)
        original_ownership = source_workspace._legacy_workspace_ownership
        destination_inode = 0

        def ownership_with_conflict(path, requested_id):
            nonlocal destination_inode
            result = original_ownership(path, requested_id)
            digest_path.mkdir()
            (digest_path / "race-marker.txt").write_text("keep race winner", encoding="utf-8")
            destination_inode = digest_path.stat().st_ino
            return result

        source_workspace._legacy_workspace_ownership = ownership_with_conflict
        try:
            loaded = source_workspace.load_workspace(conversation_id)
        finally:
            source_workspace._legacy_workspace_ownership = original_ownership

        self.assertFalse(loaded["ok"])
        self.assertEqual(digest_path.stat().st_ino, destination_inode)
        self.assertEqual((digest_path / "race-marker.txt").read_text(encoding="utf-8"), "keep race winner")
        self.assertTrue(legacy_path.is_dir())
        self.assertTrue(Path(source["path"]).is_file())

    def test_legacy_fallback_never_invokes_overwrite_capable_rename(self):
        source = self._source("rename-race.txt", "rename-race")
        conversation_id = "CONV-RENAME-RACE"
        built = source_workspace.build_workspace(conversation_id, [source], False)
        digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.legacy_workspace_path(conversation_id)
        digest_path.rename(legacy_path)
        original_rename = source_workspace.os.rename
        rename_calls = []

        def conflicting_rename(source_path, destination_path):
            rename_calls.append((source_path, destination_path))
            Path(destination_path).mkdir()
            original_rename(source_path, destination_path)

        source_workspace.os.rename = conflicting_rename
        try:
            loaded = source_workspace.load_workspace(conversation_id)
        finally:
            source_workspace.os.rename = original_rename

        self.assertTrue(loaded["ok"], loaded)
        self.assertEqual(rename_calls, [])
        self.assertEqual(Path(loaded["workspacePath"]), legacy_path)
        self.assertTrue(legacy_path.is_dir())
        self.assertFalse(digest_path.exists())
        self.assertTrue(Path(source["path"]).is_file())

    def test_alias_cannot_migrate_or_clear_another_conversation_legacy_workspace(self):
        source = self._source("alias-owned.txt", "alias-owned")
        source_path = Path(source["path"])
        original_contents = source_path.read_text(encoding="utf-8")
        owner_id = "A:B"
        alias_id = "A-B"
        built = source_workspace.build_workspace(owner_id, [source], False)
        owner_digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.SOURCE_WORKSPACES_DIR / source_workspace.safe_conversation_id(owner_id)
        owner_digest_path.rename(legacy_path)

        loaded_as_alias = source_workspace.load_workspace(alias_id)
        cleared_as_alias = source_workspace.clear_workspace(alias_id)

        self.assertFalse(loaded_as_alias["ok"])
        self.assertFalse(cleared_as_alias["ok"])
        self.assertTrue(legacy_path.is_dir())
        self.assertFalse(source_workspace.workspace_path(alias_id).exists())
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_text(encoding="utf-8"), original_contents)

        cleared_as_owner = source_workspace.clear_workspace(owner_id)

        self.assertTrue(cleared_as_owner["ok"], cleared_as_owner)
        self.assertFalse(legacy_path.exists())
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_text(encoding="utf-8"), original_contents)

    def test_missing_source_and_duplicate_source_id_fail_without_workspace(self):
        missing = self.root / "missing.pdf"
        result = source_workspace.build_workspace(
            "CONV-2",
            [{"id": "missing", "title": "Missing", "kind": "pdf", "path": str(missing)}],
            False,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["errors"])
        self.assertFalse(source_workspace.workspace_path("CONV-2").exists())

        first = self._source("one.txt", "same")
        duplicate = self._source("two.txt", "same")
        result = source_workspace.build_workspace("CONV-3", [first, duplicate], False)
        self.assertFalse(result["ok"])
        self.assertTrue(any("duplicate" in error.lower() for error in result["errors"]))

    def test_optional_text_link_is_created_and_metadata_is_preserved(self):
        text = self.root / "paper.txt"
        text.write_text("extracted", encoding="utf-8")
        source = self._source("paper.pdf", "pdf-1", text)
        source_sha256 = hashlib.sha256(Path(source["path"]).read_bytes()).hexdigest()
        text_sha256 = hashlib.sha256(text.read_bytes()).hexdigest()
        source.update({"sha256": source_sha256, "pageCount": 4, "truncated": True})

        result = source_workspace.build_workspace("CONV-4", [source], True)

        self.assertTrue(result["ok"], result)
        item = result["sources"][0]
        self.assertEqual(item["sha256"], source_sha256)
        self.assertEqual(item["textSha256"], text_sha256)
        self.assertEqual(item["pageCount"], 4)
        self.assertTrue(item["truncated"])
        workspace = Path(result["workspacePath"])
        self.assertTrue((workspace / item["textLink"]).is_symlink())
        self.assertEqual((workspace / item["textLink"]).read_text(encoding="utf-8"), "extracted")

    def test_link_names_and_revision_are_stable_for_same_ordered_sources(self):
        first = self._source("first.md", "a")
        second = self._source("second.md", "b")
        one = source_workspace.build_workspace("CONV-5", [first, second], False)
        two = source_workspace.build_workspace("CONV-5", [first, second], False)

        self.assertTrue(one["ok"] and two["ok"])
        self.assertEqual(one["revision"], two["revision"])
        self.assertEqual(
            [item["fileLink"] for item in one["sources"]],
            [item["fileLink"] for item in two["sources"]],
        )
        reversed_result = source_workspace.build_workspace("CONV-5", [second, first], False)
        self.assertNotEqual(one["revision"], reversed_result["revision"])

    def test_validation_reports_missing_target_and_revision_mismatch_without_deleting_workspace(self):
        source = self._source("keep.txt", "keep")
        built = source_workspace.build_workspace("CONV-6", [source], False)
        workspace = Path(built["workspacePath"])
        source_path = Path(source["path"])
        source_path.unlink()

        validation = source_workspace.validate_workspace("CONV-6", built["revision"])

        self.assertFalse(validation["ok"])
        self.assertTrue(validation["errors"])
        self.assertTrue(workspace.exists())
        mismatch = source_workspace.validate_workspace("CONV-6", "wrong-revision")
        self.assertFalse(mismatch["ok"])
        self.assertTrue(any("revision" in error.lower() for error in mismatch["errors"]))

    def test_clear_workspace_removes_managed_links_but_preserves_target_files(self):
        source = self._source("original.txt", "original")
        built = source_workspace.build_workspace("CONV-7", [source], False)
        workspace = Path(built["workspacePath"])
        source_path = Path(source["path"])
        original_contents = source_path.read_text(encoding="utf-8")

        result = source_workspace.clear_workspace("CONV-7")

        self.assertTrue(result["ok"], result)
        self.assertFalse(workspace.exists())
        self.assertTrue(source_path.exists())
        self.assertEqual(source_path.read_text(encoding="utf-8"), original_contents)

    def test_missing_backup_never_deletes_the_current_workspace_during_restore(self):
        conversation_id = "CONV-MISSING-BACKUP"
        original = self._source("backup-original.txt", "backup-original")
        replacement = self._source("backup-replacement.txt", "backup-replacement")
        first = source_workspace.build_workspace(conversation_id, [original], False)
        transaction = source_workspace.backup_workspace(conversation_id)
        second = source_workspace.build_workspace(conversation_id, [replacement], False)
        discarded = source_workspace.discard_workspace_backup(conversation_id, transaction)

        restored = source_workspace.restore_workspace_backup(conversation_id, transaction)
        current = source_workspace.validate_workspace(conversation_id, second["revision"])

        self.assertTrue(first["ok"] and transaction["ok"] and second["ok"] and discarded["ok"])
        self.assertFalse(restored["ok"], restored)
        self.assertTrue(current["ok"], current)
        self.assertEqual([item["sourceId"] for item in current["sources"]], ["backup-replacement"])

    def test_clear_workspace_leaves_unrecognized_content_untouched(self):
        source = self._source("owned.txt", "owned")
        built = source_workspace.build_workspace("CONV-8", [source], False)
        workspace = Path(built["workspacePath"])
        unknown = workspace / "unexpected.txt"
        unknown.write_text("keep me", encoding="utf-8")

        result = source_workspace.clear_workspace("CONV-8")

        self.assertFalse(result["ok"])
        self.assertTrue(unknown.exists())
        self.assertTrue(workspace.exists())
        self.assertTrue((workspace / built["sources"][0]["fileLink"]).is_symlink())

    def test_clear_workspace_retries_every_partial_deletion_stage_without_touching_targets(self):
        stages = (
            "file_link",
            "text_link",
            "sources_file",
            "files_dir",
            "text_dir",
            "manifest",
            "workspace_root",
        )
        for stage_index, stage in enumerate(stages, start=1):
            with self.subTest(stage=stage):
                conversation_id = f"CONV-CLEANUP-STAGE-{stage_index}"
                extracted = self.root / f"stage-{stage_index}-text.txt"
                extracted.write_text(f"extracted {stage_index}", encoding="utf-8")
                source = self._source(
                    f"stage-{stage_index}.pdf",
                    f"stage-{stage_index}",
                    extracted,
                )
                source_path = Path(source["path"])
                source_bytes = source_path.read_bytes()
                extracted_bytes = extracted.read_bytes()
                built = source_workspace.build_workspace(conversation_id, [source], False)
                self.assertTrue(built["ok"], built)
                workspace = Path(built["workspacePath"])
                record = built["sources"][0]
                stage_paths = {
                    "file_link": workspace / record["fileLink"],
                    "text_link": workspace / record["textLink"],
                    "sources_file": workspace / "SOURCES.md",
                    "files_dir": workspace / "files",
                    "text_dir": workspace / "text",
                    "manifest": workspace / "manifest.json",
                    "workspace_root": workspace,
                }
                fail_path = stage_paths[stage]
                failed = False
                original_unlink = Path.unlink
                original_rmdir = Path.rmdir

                def injected_unlink(path: Path, *args, **kwargs):
                    nonlocal failed
                    if not failed and stage in {"file_link", "text_link", "sources_file", "manifest"} and path == fail_path:
                        failed = True
                        raise OSError(f"synthetic {stage} deletion failure")
                    return original_unlink(path, *args, **kwargs)

                def injected_rmdir(path: Path, *args, **kwargs):
                    nonlocal failed
                    if not failed and stage in {"files_dir", "text_dir", "workspace_root"} and path == fail_path:
                        failed = True
                        raise OSError(f"synthetic {stage} deletion failure")
                    return original_rmdir(path, *args, **kwargs)

                with mock.patch.object(Path, "unlink", injected_unlink):
                    with mock.patch.object(Path, "rmdir", injected_rmdir):
                        first = source_workspace.clear_workspace(conversation_id)

                self.assertTrue(failed)
                self.assertFalse(first["ok"], first)
                self.assertTrue((workspace / "manifest.json").is_file())
                self.assertEqual(source_path.read_bytes(), source_bytes)
                self.assertEqual(extracted.read_bytes(), extracted_bytes)

                retried = source_workspace.clear_workspace(conversation_id)

                self.assertTrue(retried["ok"], retried)
                self.assertFalse(workspace.exists())
                self.assertEqual(source_path.read_bytes(), source_bytes)
                self.assertEqual(extracted.read_bytes(), extracted_bytes)

    def test_partial_cleanup_retry_rejects_unexpected_entries(self):
        source = self._source("partial-unexpected.txt", "partial-unexpected")
        source_path = Path(source["path"])
        original_contents = source_path.read_text(encoding="utf-8")
        built = source_workspace.build_workspace("CONV-PARTIAL-UNEXPECTED", [source], False)
        workspace = Path(built["workspacePath"])
        link = workspace / built["sources"][0]["fileLink"]
        original_unlink = Path.unlink
        failed = False

        def fail_link_once(path: Path, *args, **kwargs):
            nonlocal failed
            if not failed and path == link:
                failed = True
                raise OSError("synthetic link failure")
            return original_unlink(path, *args, **kwargs)

        with mock.patch.object(Path, "unlink", fail_link_once):
            first = source_workspace.clear_workspace("CONV-PARTIAL-UNEXPECTED")
        self.assertFalse(first["ok"], first)
        unexpected = workspace / "unexpected.txt"
        unexpected.write_text("do not remove", encoding="utf-8")

        retried = source_workspace.clear_workspace("CONV-PARTIAL-UNEXPECTED")

        self.assertFalse(retried["ok"], retried)
        self.assertTrue(unexpected.is_file())
        self.assertTrue((workspace / "manifest.json").is_file())
        self.assertTrue(source_path.is_file())
        self.assertEqual(source_path.read_text(encoding="utf-8"), original_contents)

    def test_cleanup_rejects_manifest_tampering_before_deleting_managed_entries(self):
        for index, tampering in enumerate(("conversation", "unexpected_field"), start=1):
            with self.subTest(tampering=tampering):
                conversation_id = f"CONV-CLEANUP-MANIFEST-{index}"
                source = self._source(f"manifest-{index}.txt", f"manifest-{index}")
                source_path = Path(source["path"])
                original_contents = source_path.read_text(encoding="utf-8")
                built = source_workspace.build_workspace(conversation_id, [source], False)
                workspace = Path(built["workspacePath"])
                manifest_path = workspace / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                if tampering == "conversation":
                    manifest["conversationId"] = "OTHER-CONVERSATION"
                else:
                    manifest["unexpected"] = "blocked"
                manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
                before_entries = {
                    str(path.relative_to(workspace)) for path in workspace.rglob("*")
                }

                result = source_workspace.clear_workspace(conversation_id)

                self.assertFalse(result["ok"], result)
                self.assertEqual(
                    {str(path.relative_to(workspace)) for path in workspace.rglob("*")},
                    before_entries,
                )
                self.assertTrue((workspace / built["sources"][0]["fileLink"]).is_symlink())
                self.assertEqual(source_path.read_text(encoding="utf-8"), original_contents)

    def test_validation_rejects_regular_file_substitution_for_declared_link(self):
        source = self._source("declared.txt", "declared")
        built = source_workspace.build_workspace("CONV-9", [source], False)
        workspace = Path(built["workspacePath"])
        link = workspace / built["sources"][0]["fileLink"]
        link.unlink()
        link.write_text("substituted", encoding="utf-8")

        result = source_workspace.validate_workspace("CONV-9", built["revision"])

        self.assertFalse(result["ok"])
        self.assertTrue(any("symlink" in error.lower() or "invalid" in error.lower() for error in result["errors"]))

    def test_validation_rejects_redirected_symlink_for_declared_link(self):
        first = self._source("first.txt", "first")
        second = self._source("second.txt", "second")
        built = source_workspace.build_workspace("CONV-10", [first, second], False)
        workspace = Path(built["workspacePath"])
        first_link = workspace / built["sources"][0]["fileLink"]
        second_link = workspace / built["sources"][1]["fileLink"]
        first_link.unlink()
        first_link.symlink_to(second_link.resolve())

        result = source_workspace.validate_workspace("CONV-10", built["revision"])

        self.assertFalse(result["ok"])
        self.assertTrue(any("target" in error.lower() for error in result["errors"]))

    def test_validation_rejects_in_place_original_and_text_replacement(self):
        original = self.root / "paper.pdf"
        extracted = self.root / "paper.txt"
        original.write_bytes(b"%PDF-1.4\noriginal")
        extracted.write_text("original extracted text", encoding="utf-8")
        built = source_workspace.build_workspace(
            "CONV-INTEGRITY",
            [
                {
                    "id": "paper",
                    "title": "Paper",
                    "kind": "pdf",
                    "path": str(original),
                    "textPath": str(extracted),
                }
            ],
            False,
        )
        self.assertTrue(built["ok"], built)

        original.write_bytes(b"%PDF-1.4\nreplacement")
        replaced_original = source_workspace.validate_workspace("CONV-INTEGRITY", built["revision"])
        self.assertFalse(replaced_original["ok"], replaced_original)
        self.assertTrue(any("sha256" in error.lower() or "content" in error.lower() for error in replaced_original["errors"]))

        original.write_bytes(b"%PDF-1.4\noriginal")
        extracted.write_text("replacement extracted text", encoding="utf-8")
        replaced_text = source_workspace.validate_workspace("CONV-INTEGRITY", built["revision"])
        self.assertFalse(replaced_text["ok"], replaced_text)
        self.assertTrue(any("text" in error.lower() and "sha256" in error.lower() for error in replaced_text["errors"]))

    def test_load_rejects_manifest_ownership_allowlist_and_sources_content_tampering(self):
        source = self._source("strict.txt", "strict")
        built = source_workspace.build_workspace("CONV-STRICT-OWNER", [source], False)
        workspace = Path(built["workspacePath"])
        manifest_path = workspace / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        manifest["conversationId"] = "OTHER-CONVERSATION"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        wrong_owner = source_workspace.load_workspace("CONV-STRICT-OWNER")
        self.assertFalse(wrong_owner["ok"], wrong_owner)

        rebuilt = source_workspace.build_workspace("CONV-STRICT-ALLOWLIST", [source], False)
        workspace = Path(rebuilt["workspacePath"])
        manifest_path = workspace / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["unexpected"] = "not allowed"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        unknown_manifest_field = source_workspace.load_workspace("CONV-STRICT-ALLOWLIST")
        self.assertFalse(unknown_manifest_field["ok"], unknown_manifest_field)

        rebuilt = source_workspace.build_workspace("CONV-STRICT-SOURCES", [source], False)
        workspace = Path(rebuilt["workspacePath"])
        (workspace / "SOURCES.md").write_text("tampered source instructions", encoding="utf-8")
        tampered_sources = source_workspace.validate_workspace("CONV-STRICT-SOURCES", rebuilt["revision"])
        self.assertFalse(tampered_sources["ok"], tampered_sources)
        self.assertTrue(any("sources.md" in error.lower() for error in tampered_sources["errors"]))

    def test_revision_changes_when_source_bytes_change_at_same_path(self):
        source = self._source("replace-in-place.txt", "replace-in-place")
        first = source_workspace.build_workspace("CONV-REVISION", [source], False)
        Path(source["path"]).write_text("new bytes at the same path", encoding="utf-8")
        second = source_workspace.build_workspace("CONV-REVISION", [source], False)

        self.assertTrue(first["ok"] and second["ok"])
        self.assertNotEqual(first["revision"], second["revision"])

    def test_legacy_manifest_with_sanitizer_altered_owner_fails_closed(self):
        source = self._source("legacy-sanitized.txt", "legacy-sanitized")
        owner = "A:B"
        built = source_workspace.build_workspace(owner, [source], False)
        digest_path = Path(built["workspacePath"])
        legacy_path = source_workspace.legacy_workspace_path(owner)
        digest_path.rename(legacy_path)
        manifest_path = legacy_path / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["conversationId"] = source_workspace.safe_conversation_id(owner)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        loaded = source_workspace.load_workspace(owner)
        cleared = source_workspace.clear_workspace(owner)

        self.assertFalse(loaded["ok"], loaded)
        self.assertFalse(cleared["ok"], cleared)
        self.assertTrue(legacy_path.is_dir())
        self.assertTrue(Path(source["path"]).is_file())

    def test_cleanup_removes_only_owned_stale_orphans_and_unreferenced_managed_text(self):
        now = time.time()
        old_eight_days = now - 8 * 24 * 60 * 60
        old_two_days = now - 2 * 24 * 60 * 60
        active_source = self._source("active.txt", "active")
        orphan_source = self._source("orphan.txt", "orphan")
        recent_source = self._source("recent.txt", "recent")
        active = source_workspace.build_workspace("ACTIVE", [active_source], False)
        orphan = source_workspace.build_workspace("ORPHAN", [orphan_source], False)
        recent = source_workspace.build_workspace("RECENT", [recent_source], False)
        for path in (Path(active["workspacePath"]), Path(orphan["workspacePath"])):
            os.utime(path, (old_eight_days, old_eight_days))
            os.utime(path / "manifest.json", (old_eight_days, old_eight_days))
        os.utime(Path(recent["workspacePath"]), (now - 6 * 24 * 60 * 60, now - 6 * 24 * 60 * 60))

        staging_source = self._source("staging.txt", "staging")
        staging_built = source_workspace.build_workspace("STAGING", [staging_source], False)
        staging = source_workspace.SOURCE_WORKSPACES_DIR / ".staging-owned"
        Path(staging_built["workspacePath"]).rename(staging)
        os.utime(staging, (old_two_days, old_two_days))
        os.utime(staging / "manifest.json", (old_two_days, old_two_days))

        ambiguous = source_workspace.SOURCE_WORKSPACES_DIR / "ambiguous"
        ambiguous.mkdir()
        (ambiguous / "user-file.txt").write_text("keep", encoding="utf-8")
        os.utime(ambiguous, (old_eight_days, old_eight_days))
        symlink_target = self.root / "symlink-target"
        symlink_target.mkdir()
        workspace_link = source_workspace.SOURCE_WORKSPACES_DIR / "linked"
        workspace_link.symlink_to(symlink_target, target_is_directory=True)

        text_dir = self.root / "control" / "source-text"
        text_dir.mkdir(parents=True, exist_ok=True)
        orphan_text = "orphan managed artifact"
        orphan_digest = hashlib.sha256(orphan_text.encode("utf-8")).hexdigest()
        managed_orphan = text_dir / f"managed-{'a' * 16}-{orphan_digest}.txt"
        managed_orphan.write_text(orphan_text, encoding="utf-8")
        os.utime(managed_orphan, (old_eight_days, old_eight_days))
        ambiguous_text = text_dir / "legacy-ambiguous.txt"
        ambiguous_text.write_text("keep", encoding="utf-8")
        os.utime(ambiguous_text, (old_eight_days, old_eight_days))

        result = source_workspace.cleanup_orphans(
            {"ACTIVE"},
            text_artifacts_dir=text_dir,
            now=now,
        )

        self.assertTrue(result["ok"], result)
        self.assertTrue(Path(active["workspacePath"]).is_dir())
        self.assertFalse(Path(orphan["workspacePath"]).exists())
        self.assertTrue(Path(recent["workspacePath"]).is_dir())
        self.assertFalse(staging.exists())
        self.assertTrue(ambiguous.is_dir())
        self.assertTrue(workspace_link.is_symlink())
        self.assertTrue(symlink_target.is_dir())
        self.assertFalse(managed_orphan.exists())
        self.assertTrue(ambiguous_text.is_file())
        for source_item in (active_source, orphan_source, recent_source, staging_source):
            self.assertTrue(Path(source_item["path"]).is_file())

    def test_cleanup_accepts_exact_owned_pre_integrity_manifest_without_following_sources(self):
        now = time.time()
        old = now - 8 * 24 * 60 * 60
        source = self._source("legacy-cleanup.txt", "legacy-cleanup")
        built = source_workspace.build_workspace("LEGACY-CLEANUP", [source], False)
        workspace = Path(built["workspacePath"])
        manifest_path = workspace / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest.pop("sourcesMdSha256")
        for item in manifest["sources"]:
            item.pop("textSha256")
            item.pop("textLinkName")
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        os.utime(workspace, (old, old))
        os.utime(manifest_path, (old, old))

        result = source_workspace.cleanup_orphans(set(), now=now)

        self.assertTrue(result["ok"], result)
        self.assertFalse(workspace.exists())
        self.assertTrue(Path(source["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
