from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import base64
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


COMPANION_PATH = Path(__file__).resolve().parents[1] / "companion.py"


def load_companion(root: Path) -> Any:
    old_root = os.environ.get("CODEX_MN_COMPANION_HOME")
    os.environ["CODEX_MN_COMPANION_HOME"] = str(root)
    try:
        spec = importlib.util.spec_from_file_location("codex_mn_companion_pdf_export", COMPANION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old_root is None:
            os.environ.pop("CODEX_MN_COMPANION_HOME", None)
        else:
            os.environ["CODEX_MN_COMPANION_HOME"] = old_root


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pymupdf_python() -> str | None:
    candidates = [
        os.environ.get("CODEX_MN_PYMUPDF_PYTHON"),
        "/Users/liuwhale/miniforge3/bin/python3",
        sys.executable,
    ]
    for candidate in candidates:
        if not candidate:
            continue
        try:
            subprocess.run(
                [candidate, "-c", "import fitz"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return candidate
        except Exception:
            continue
    return None


def create_pdf(path: Path, text: str) -> None:
    python = pymupdf_python()
    if python is None:
        raise unittest.SkipTest("PyMuPDF is required for this test")
    script = """
import fitz
import sys
doc = fitz.open()
page = doc.new_page()
page.insert_text((72, 96), sys.argv[2], fontsize=12)
doc.save(sys.argv[1])
doc.close()
"""
    subprocess.run([python, "-c", script, str(path), text], check=True)


def annotation_types(path: Path) -> list[str]:
    python = pymupdf_python()
    if python is None:
        raise unittest.SkipTest("PyMuPDF is required for this test")
    script = """
import fitz
import json
import sys
doc = fitz.open(sys.argv[1])
types = []
for page in doc:
    for annot in page.annots() or []:
        types.append(annot.type[1])
doc.close()
print(json.dumps(types))
"""
    completed = subprocess.run([python, "-c", script, str(path)], check=True, text=True, capture_output=True)
    return list(json.loads(completed.stdout))


class PdfExportTests(unittest.TestCase):
    def test_resolve_pdf_source_accepts_file_url_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            source = Path(tmp) / "source file.pdf"
            source.write_bytes(b"%PDF-1.4\n")

            companion = load_companion(root)
            resolved, error = companion.resolve_pdf_source({"pdfPath": source.as_uri()}, "")

            self.assertIsNone(error)
            self.assertEqual(resolved, source)

    def test_resolve_pdf_source_uses_marginnote_book_database_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            docs = Path(tmp) / "MNDocs"
            docs.mkdir()
            source = docs / "source.pdf"
            source.write_bytes(b"%PDF-1.4\n")
            db_path = Path(tmp) / "MarginNotes.sqlite"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute("create table ZBOOK (ZMD5 text, ZMD5LONG text, ZPATH text, ZBOOKURL text, ZFILE text)")
                conn.execute(
                    "insert into ZBOOK (ZMD5, ZMD5LONG, ZPATH, ZBOOKURL, ZFILE) values (?, ?, ?, ?, ?)",
                    ("SHORT", "LONGBOOK", "$$$MNDOCLINK$$$iCloud.QReader.MarginStudy.easy/MNDocs", "source.pdf", "source.pdf"),
                )
                conn.commit()
            finally:
                conn.close()

            companion = load_companion(root)
            companion.DB_PATH = db_path
            companion.MN_DOC_ROOTS = [docs]

            resolved, error = companion.resolve_pdf_source({}, "LONGBOOK")

            self.assertIsNone(error)
            self.assertEqual(resolved, source)

    def test_cache_pdf_from_marginnote_is_used_as_pdf_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            companion = load_companion(root)
            pdf_bytes = b"%PDF-1.4\n% cached pdf\n"

            result = companion.handle_action(
                {
                    "action": "cache_pdf_from_marginnote",
                    "bookmd5": "BOOK1",
                    "pdfPath": "/blocked/source.pdf",
                    "fileName": "source.pdf",
                    "pdfBase64": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["cache"]["bookmd5"], "BOOK1")
            cached_path = Path(result["cache"]["path"])
            self.assertTrue(cached_path.exists())
            self.assertEqual(cached_path.read_bytes(), pdf_bytes)

            resolved, error = companion.resolve_pdf_source({}, "BOOK1")

            self.assertIsNone(error)
            self.assertEqual(resolved, cached_path)

    def test_diagnose_permissions_reports_pdf_cache_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            companion = load_companion(root)
            pdf_bytes = b"%PDF-1.4\n% cached pdf\n"
            cached = companion.handle_action(
                {
                    "action": "cache_pdf_from_marginnote",
                    "bookmd5": "BOOK1",
                    "pdfPath": "/blocked/source.pdf",
                    "fileName": "source.pdf",
                    "pdfBase64": base64.b64encode(pdf_bytes).decode("ascii"),
                }
            )

            result = companion.diagnose_permissions({"bookmd5": "BOOK1"})

            self.assertTrue(cached["ok"])
            self.assertTrue(result["ok"])
            self.assertEqual(result["fileAccess"]["pdfCache"]["status"], "OK")
            self.assertEqual(result["fileAccess"]["pdfCache"]["path"], cached["cache"]["path"])
            self.assertIn("PDF缓存", result["reply"])

    def test_export_annotated_pdf_creates_highlighted_copy_without_touching_original(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            source = Path(tmp) / "source.pdf"
            create_pdf(source, "Attention guided safety filter keeps the robot away from obstacles.")
            before_hash = sha256(source)

            companion = load_companion(root)
            companion.KNOWN_PDF_PATHS = {"TESTBOOK": source}
            companion.PDF_EXPORT_DIR = Path(tmp) / "exports"

            result = companion.export_annotated_pdf(
                {
                    "topicid": "T1",
                    "bookmd5": "TESTBOOK",
                    "selectionText": "Attention guided safety filter",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["backend"], "local:pymupdf-highlight-copy")
            self.assertEqual(result["annotations_created"], 1)
            self.assertFalse(result["modifiedOriginal"])
            self.assertEqual(sha256(source), before_hash)

            output = Path(result["outputPdf"])
            self.assertTrue(output.exists())
            self.assertNotEqual(output.resolve(), source.resolve())
            self.assertTrue(output.resolve().is_relative_to(companion.PDF_EXPORT_DIR.resolve()))
            self.assertEqual(annotation_types(output), ["Highlight"])

    def test_export_annotated_pdf_with_cached_pdf_keeps_output_filename_under_filesystem_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            source = Path(tmp) / "Park et al. 2026. Your Model Already Knows Attention-Guided Safety Filter for Vision-Language-Action Models.pdf"
            create_pdf(source, "Attention guided safety filter keeps the robot away from obstacles.")
            before_hash = sha256(source)

            companion = load_companion(root)
            companion.PDF_EXPORT_DIR = Path(tmp) / "exports"
            book_md5 = "253dd5804dd4973bcea545ebcc7ee5a760c73581e1a4e25904fd10ae4b8d1246"
            cached = companion.handle_action(
                {
                    "action": "cache_pdf_from_marginnote",
                    "bookmd5": book_md5,
                    "pdfPath": str(source),
                    "fileName": source.name,
                    "pdfBase64": base64.b64encode(source.read_bytes()).decode("ascii"),
                }
            )

            result = companion.export_annotated_pdf(
                {
                    "topicid": "T1",
                    "bookmd5": book_md5,
                    "selectionText": "Attention guided safety filter",
                }
            )

            self.assertTrue(cached["ok"])
            self.assertTrue(result["ok"], result.get("reply"))
            output = Path(result["outputPdf"])
            self.assertLessEqual(len(output.name.encode("utf-8")), 255)
            self.assertTrue(output.exists())
            self.assertEqual(annotation_types(output), ["Highlight"])
            self.assertEqual(sha256(source), before_hash)

    def test_export_annotated_pdf_permission_error_returns_visible_diagnostic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "companion"
            root.mkdir()
            source = Path(tmp) / "source.pdf"
            source.write_bytes(b"%PDF-1.4\n")

            companion = load_companion(root)
            companion.KNOWN_PDF_PATHS = {"TESTBOOK": source}

            def denied_hash(path: Path) -> str:
                raise PermissionError("Operation not permitted")

            companion.sha256_file = denied_hash

            result = companion.export_annotated_pdf(
                {
                    "topicid": "T1",
                    "bookmd5": "TESTBOOK",
                    "selectionText": "Attention guided safety filter",
                }
            )

            self.assertTrue(result["ok"])
            self.assertEqual(result["status"], "PERMISSION")
            self.assertEqual(result["backend"], "local:pymupdf-highlight-copy")
            self.assertFalse(result["modifiedOriginal"])
            self.assertIn("Full Disk Access", result["reply"])
            self.assertIn("Operation not permitted", result["reply"])


if __name__ == "__main__":
    unittest.main()
