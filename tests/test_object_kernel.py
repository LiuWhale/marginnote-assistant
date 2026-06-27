import tempfile
import unittest
from pathlib import Path

import object_kernel


class ObjectKernelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        object_kernel.configure(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_builds_stable_selection_object(self):
        payload = {
            "topicid": "T1",
            "bookmd5": "B1",
            "selectionText": "Attention mask evidence",
            "documentTitle": "Paper.pdf",
            "page": 3,
        }

        first = object_kernel.build_object(payload)
        second = object_kernel.build_object(payload)

        self.assertEqual(first["schema"], "codex.mn.mnObject.v1")
        self.assertEqual(first["objectId"], second["objectId"])
        self.assertTrue(first["objectId"].startswith("mnobj:selection:"))
        self.assertEqual(first["kind"], "selection")
        self.assertEqual(first["sourceRef"]["page"], 3)
        self.assertEqual(first["sourceRef"]["quote"], "Attention mask evidence")

    def test_registers_document_object_and_tracks_seen_count(self):
        payload = {
            "topicid": "T1",
            "bookmd5": "B1",
            "documentTitle": "Paper.pdf",
        }
        obj = object_kernel.build_object(payload)

        first = object_kernel.register_object(obj, evidence_type="context_payload")
        second = object_kernel.register_object(obj, evidence_type="context_payload")
        registry = object_kernel.registry_list({"topicid": "T1", "bookmd5": "B1"})

        self.assertEqual(first["object"]["objectId"], second["object"]["objectId"])
        self.assertEqual(registry["schema"], "codex.mn.mnObjectRegistry.v1")
        self.assertEqual(registry["total"], 1)
        self.assertEqual(registry["objects"][0]["seenCount"], 2)
        self.assertIn("context_payload", registry["objects"][0]["evidenceTypes"])

    def test_ingests_native_scan_nodes_as_note_objects(self):
        result = object_kernel.ingest_native_scan(
            {
                "topicid": "T1",
                "bookmd5": "B1",
                "documentTitle": "Paper.pdf",
                "nodes": [
                    {"noteId": "n1", "title": "Root", "parentNoteId": ""},
                    {"noteId": "n2", "title": "Child", "parentNoteId": "n1", "path": "Root / Child"},
                ],
            }
        )

        self.assertEqual(result["schema"], "codex.mn.mnObjectRegistryScan.v1")
        self.assertEqual(result["ingestedCount"], 2)
        registry = object_kernel.registry_list({"topicid": "T1", "bookmd5": "B1"})
        object_ids = {item["objectId"] for item in registry["objects"]}
        self.assertIn("mnobj:note:n1", object_ids)
        self.assertIn("mnobj:note:n2", object_ids)
        child = next(item for item in registry["objects"] if item["objectId"] == "mnobj:note:n2")
        self.assertEqual(child["sourceRef"]["parentNoteId"], "n1")
        self.assertIn("native_object_scan", child["evidenceTypes"])


if __name__ == "__main__":
    unittest.main()
