import tempfile
import unittest
from pathlib import Path

import knowledge_index


class KnowledgeIndexTests(unittest.TestCase):
    def test_ingest_status_search_and_clear_are_scoped(self) -> None:
        old_root = knowledge_index._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                knowledge_index.configure(Path(tmp))

                first = knowledge_index.ingest_entry(
                    kind="context",
                    title="Qwen-RobotManip",
                    text="Alignment unlocks scale for robotic manipulation foundation models.",
                    topicid="T1",
                    bookmd5="B1",
                    source="test",
                )
                second = knowledge_index.ingest_entry(
                    kind="context",
                    title="Other Paper",
                    text="A different document about attention safety filters.",
                    topicid="T2",
                    bookmd5="B2",
                    source="test",
                )

                self.assertTrue(first["ok"])
                self.assertTrue(second["ok"])
                self.assertEqual(knowledge_index.status("T1", "B1")["count"], 1)

                scoped = knowledge_index.search("robotic manipulation", topicid="T1", bookmd5="B1")
                self.assertEqual(len(scoped["matches"]), 1)
                self.assertEqual(scoped["matches"][0]["title"], "Qwen-RobotManip")

                other_scope = knowledge_index.search("attention safety", topicid="T1", bookmd5="B1")
                self.assertEqual(other_scope["matches"], [])

                cleared = knowledge_index.clear("T1", "B1")
                self.assertEqual(cleared["removed"], 1)
                self.assertEqual(knowledge_index.status()["count"], 1)
            finally:
                knowledge_index.configure(old_root)

    def test_ingests_structured_marginnote_entities_with_source_and_relations(self) -> None:
        old_root = knowledge_index._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                knowledge_index.configure(Path(tmp))

                result = knowledge_index.ingest_entities(
                    [
                        {
                            "entityType": "mindmap_node",
                            "title": "Attention-guided safety filter",
                            "body": "Uses attention over image patches to identify unsafe robot actions.",
                            "noteId": "NODE-1",
                            "page": 4,
                            "quote": "attention-guided safety filter",
                            "relations": [
                                {"type": "supports", "targetNoteId": "CARD-1", "label": "evidence card"}
                            ],
                        },
                        {
                            "entityType": "card",
                            "title": "Unsafe action evidence",
                            "text": "The filter rejects actions when attended patches overlap unsafe regions.",
                            "noteId": "CARD-1",
                            "source": {"page": 5, "quote": "overlap unsafe regions"},
                        },
                    ],
                    topicid="T1",
                    bookmd5="B1",
                    source="mn-entity-sync",
                )

                self.assertTrue(result["ok"], result)
                self.assertEqual(result["entityCount"], 2)
                status = knowledge_index.status("T1", "B1")
                self.assertEqual(status["kinds"]["mindmap_node"], 1)
                self.assertEqual(status["kinds"]["card"], 1)
                self.assertEqual(status["entityTypes"]["mindmap_node"], 1)

                found = knowledge_index.search("unsafe robot actions", topicid="T1", bookmd5="B1")
                self.assertEqual(found["matches"][0]["entityType"], "mindmap_node")
                self.assertEqual(found["matches"][0]["noteId"], "NODE-1")
                self.assertEqual(found["matches"][0]["sourceRef"]["page"], 4)
                self.assertIn("attention-guided safety filter", found["matches"][0]["sourceRef"]["quote"])
                self.assertEqual(found["matches"][0]["relations"][0]["targetNoteId"], "CARD-1")
            finally:
                knowledge_index.configure(old_root)


if __name__ == "__main__":
    unittest.main()
