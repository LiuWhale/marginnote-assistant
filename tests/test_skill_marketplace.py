import tempfile
import unittest
from pathlib import Path

import skill_marketplace


class SkillMarketplaceTests(unittest.TestCase):
    def test_builtin_skills_declare_permissions_rollback_and_acceptance_rules(self) -> None:
        old_root = skill_marketplace._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                skill_marketplace.configure(Path(tmp))

                status = skill_marketplace.status()

                self.assertTrue(status["ok"])
                self.assertGreaterEqual(status["skillCount"], 2)
                skill_ids = [item["id"] for item in status["skills"]]
                self.assertIn("knowledge.related_context", skill_ids)
                self.assertIn("workflow.deep_reading_writer", skill_ids)

                read_skill = next(item for item in status["skills"] if item["id"] == "knowledge.related_context")
                write_skill = next(item for item in status["skills"] if item["id"] == "workflow.deep_reading_writer")
                self.assertEqual(read_skill["permission"], "read_only")
                self.assertEqual(read_skill["rollback"]["strategy"], "not_required")
                self.assertEqual(write_skill["permission"], "notes")
                self.assertTrue(write_skill["requiresConfirmation"])
                self.assertEqual(write_skill["rollback"]["strategy"], "ai_edit_transaction")
                self.assertTrue(read_skill["acceptanceRules"])
                self.assertTrue(write_skill["acceptanceRules"])
            finally:
                skill_marketplace.configure(old_root)

    def test_install_and_uninstall_skill_persist_local_state(self) -> None:
        old_root = skill_marketplace._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                skill_marketplace.configure(Path(tmp))

                installed = skill_marketplace.install("knowledge.related_context")
                self.assertTrue(installed["ok"], installed)
                self.assertIn("knowledge.related_context", installed["installedSkillIds"])
                self.assertTrue(installed["skill"]["installed"])

                status = skill_marketplace.status()
                self.assertEqual(status["installedCount"], 1)
                self.assertTrue(next(item for item in status["skills"] if item["id"] == "knowledge.related_context")["installed"])

                removed = skill_marketplace.uninstall("knowledge.related_context")
                self.assertTrue(removed["ok"], removed)
                self.assertNotIn("knowledge.related_context", removed["installedSkillIds"])
            finally:
                skill_marketplace.configure(old_root)


if __name__ == "__main__":
    unittest.main()
