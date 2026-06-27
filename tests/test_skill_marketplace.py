import tempfile
import unittest
from pathlib import Path

import skill_marketplace


class SkillMarketplaceTests(unittest.TestCase):
    def test_write_skill_requires_dry_run_rollback_and_acceptance(self) -> None:
        bad = {
            "schema": "codex.mn.skillManifest.v1",
            "skillId": "bad.writer",
            "name": "Bad Writer",
            "version": "1.0.0",
            "permissions": ["notes"],
            "outputs": ["write_draft"],
        }

        result = skill_marketplace.validate_manifest(bad)

        self.assertFalse(result["ok"])
        self.assertEqual(result["manifestId"], "bad.writer")
        self.assertIn("requiresConfirmation", result["missing"])
        self.assertIn("dryRun", result["missing"])
        self.assertIn("rollback", result["missing"])
        self.assertIn("acceptance", result["missing"])
        self.assertEqual(result["riskLevel"], "write")

    def test_delete_skill_requires_delete_permission_and_confirmation_rule(self) -> None:
        bad = {
            "schema": "codex.mn.skillManifest.v1",
            "id": "bad.delete",
            "title": "Bad Delete",
            "version": "1.0.0",
            "permission": "delete",
            "outputOperations": ["delete_notes"],
            "requiresConfirmation": True,
            "dryRun": {"required": True},
            "rollback": {"strategy": "ai_edit_transaction"},
            "acceptanceRules": ["用户确认后才删除。"],
        }

        result = skill_marketplace.validate_manifest(bad)

        self.assertFalse(result["ok"])
        self.assertEqual(result["riskLevel"], "delete")
        self.assertIn("allowsDelete", result["missing"])
        self.assertIn("deleteConfirmationRule", result["missing"])

    def test_install_manifest_persists_valid_external_skill(self) -> None:
        old_root = skill_marketplace._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                skill_marketplace.configure(Path(tmp))
                manifest = {
                    "schema": "codex.mn.skillManifest.v1",
                    "skillId": "custom.deep_mindmap",
                    "name": "Deep Mindmap",
                    "version": "1.2.3",
                    "permissions": ["notes"],
                    "inputs": ["document"],
                    "outputs": ["generate_mindmap", "write_draft"],
                    "prompts": ["生成完整、分层、短卡化的脑图。"],
                    "actions": ["generate_mindmap"],
                    "requiresConfirmation": True,
                    "dryRun": {"required": True, "mode": "operation_plan"},
                    "rollback": {"strategy": "ai_edit_transaction"},
                    "acceptance": ["创建后先显示 AI 编辑操作，拒绝时必须回滚新增卡片和脑图结构。"],
                }

                installed = skill_marketplace.install_manifest(manifest)
                status = skill_marketplace.status()

                self.assertTrue(installed["ok"], installed)
                external = next(item for item in status["skills"] if item["id"] == "custom.deep_mindmap")
                self.assertTrue(external["installed"])
                self.assertEqual(external["schema"], "codex.mn.skillManifest.v1")
                self.assertEqual(external["validation"]["status"], "valid")
                self.assertEqual(external["riskLevel"], "write")
                self.assertIn("写入", external["safetyBadges"])
                self.assertIn("回滚", external["safetyBadges"])
            finally:
                skill_marketplace.configure(old_root)

    def test_skill_operation_plan_requires_validation_and_dry_run_first(self) -> None:
        old_root = skill_marketplace._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                skill_marketplace.configure(Path(tmp))
                installed = skill_marketplace.install("workflow.deep_reading_writer")
                self.assertTrue(installed["ok"], installed)

                plan = skill_marketplace.skill_operation_plan(
                    "workflow.deep_reading_writer",
                    {"objectType": "document", "objectId": "DOC1", "bookmd5": "BOOK1"},
                )

                self.assertTrue(plan["ok"], plan)
                self.assertEqual(plan["schema"], "codex.mn.skillOperationPlan.v1")
                self.assertEqual(plan["skillId"], "workflow.deep_reading_writer")
                self.assertEqual(plan["executionMode"], "dry_run_first")
                self.assertTrue(plan["requiresConfirmation"])
                self.assertEqual(plan["rollback"]["strategy"], "ai_edit_transaction")
                self.assertIn("generate_mindmap", [item["operation"] for item in plan["operations"]])
                self.assertTrue(plan["acceptanceRules"])
            finally:
                skill_marketplace.configure(old_root)

    def test_skill_run_record_keeps_auditable_lifecycle(self) -> None:
        old_root = skill_marketplace._ROOT
        with tempfile.TemporaryDirectory() as tmp:
            try:
                skill_marketplace.configure(Path(tmp))

                saved = skill_marketplace.record_skill_run(
                    {
                        "skillId": "workflow.deep_reading_writer",
                        "objectRef": {"objectType": "document", "objectId": "DOC1"},
                        "status": "completed",
                        "phase": "accepted",
                        "backend": "codex-cli",
                        "acceptance": {"status": "accepted", "createdCards": 12, "createdMindmapNodes": 8},
                    }
                )
                runs = skill_marketplace.latest_skill_runs(limit=3)

                self.assertTrue(saved["ok"], saved)
                self.assertEqual(saved["record"]["schema"], "codex.mn.skillRun.v1")
                self.assertTrue(saved["record"]["runId"].startswith("skillrun_"))
                self.assertEqual(runs["runs"][0]["skillId"], "workflow.deep_reading_writer")
                self.assertEqual(runs["runs"][0]["acceptance"]["createdCards"], 12)
            finally:
                skill_marketplace.configure(old_root)

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
