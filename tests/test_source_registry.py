import tempfile
import unittest
from pathlib import Path

import source_registry


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        source_registry.configure(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_builds_registry_with_missing_source_gap(self):
        registry = source_registry.build_registry(
            {"topicid": "T1", "bookmd5": "B1", "documentTitle": "Paper.pdf"},
            caches=[],
            explicit_paths=[],
            uploads=[],
            roots=[],
        )

        self.assertEqual(registry["schema"], "codex.mn.sourceRegistry.v1")
        self.assertEqual(registry["readableCount"], 0)
        self.assertEqual(registry["status"], "missing")
        self.assertEqual(registry["gaps"][0]["id"], "source_registry")

    def test_builds_registry_with_readable_cache(self):
        registry = source_registry.build_registry(
            {"topicid": "T1", "bookmd5": "B1", "documentTitle": "Paper.pdf"},
            caches=[{"path": "/tmp/Paper.pdf", "readable": True, "sha256": "abc"}],
            explicit_paths=[],
            uploads=[],
            roots=[],
        )

        self.assertEqual(registry["status"], "ready")
        self.assertEqual(registry["readableCount"], 1)
        self.assertEqual(registry["sources"][0]["kind"], "pdf_cache")
        self.assertEqual(registry["sources"][0]["metadata"]["sha256"], "abc")
        self.assertEqual(registry["gaps"], [])

    def test_records_source_action_lifecycle_and_latest_run(self):
        run = source_registry.record_action_run(
            {
                "topicid": "T1",
                "bookmd5": "B1",
                "documentTitle": "Paper.pdf",
                "actionId": "cache_current_pdf",
                "actionLabel": "缓存当前 PDF",
                "status": "running",
                "event": "started",
                "message": "已开始缓存。",
            }
        )

        self.assertEqual(run["sourceActionRun"]["schema"], "codex.mn.sourceRegistryActionRun.v1")
        self.assertEqual(run["sourceActionRun"]["status"], "running")
        self.assertEqual(run["sourceActionRun"]["actionId"], "cache_current_pdf")

        done = source_registry.record_action_run(
            {
                **run["sourceActionRun"],
                "status": "completed",
                "event": "completed",
                "message": "缓存完成。",
                "result": {"ok": True},
            }
        )
        latest = source_registry.latest_action_run("T1", "B1")

        self.assertEqual(done["sourceActionRun"]["status"], "completed")
        self.assertEqual(latest["runId"], run["sourceActionRun"]["runId"])
        self.assertEqual(latest["status"], "completed")
        self.assertEqual(latest["message"], "缓存完成。")


if __name__ == "__main__":
    unittest.main()
