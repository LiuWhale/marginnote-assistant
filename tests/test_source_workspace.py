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


if __name__ == "__main__":
    unittest.main()
