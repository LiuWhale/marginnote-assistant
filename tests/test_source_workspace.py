import json
import tempfile
import unittest
from pathlib import Path

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
        source.update({"sha256": "abc123", "pageCount": 4, "truncated": True})

        result = source_workspace.build_workspace("CONV-4", [source], True)

        self.assertTrue(result["ok"], result)
        item = result["sources"][0]
        self.assertEqual(item["sha256"], "abc123")
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


if __name__ == "__main__":
    unittest.main()
