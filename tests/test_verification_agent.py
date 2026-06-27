import unittest

import verification_agent


class VerificationAgentTests(unittest.TestCase):
    def test_reports_unknown_when_native_probe_missing(self) -> None:
        report = verification_agent.verify_transaction(
            {
                "createdNoteIds": ["n1"],
                "nativeProbe": {},
            }
        )

        self.assertEqual(report["schema"], "codex.mn.verificationReport.v1")
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertIn("native_probe_missing", report["problems"])

    def test_reports_fail_when_expected_object_absent(self) -> None:
        report = verification_agent.verify_transaction(
            {
                "createdNoteIds": ["n1"],
                "createdCardIds": ["c1"],
                "nativeProbe": {
                    "objects": [
                        {"noteId": "n1", "exists": False},
                        {"cardId": "c1", "exists": True},
                    ]
                },
            }
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("n1", report["missingNoteIds"])
        self.assertEqual(report["presentCardIds"], ["c1"])

    def test_reports_pass_when_expected_objects_are_present(self) -> None:
        report = verification_agent.verify_transaction(
            {
                "createdNoteIds": ["n1"],
                "createdCardIds": ["c1"],
                "nativeProbe": {
                    "objects": [
                        {"noteId": "n1", "exists": True},
                        {"cardId": "c1", "exists": True},
                    ]
                },
            }
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["presentNoteIds"], ["n1"])
        self.assertEqual(report["presentCardIds"], ["c1"])
        self.assertFalse(report["problems"])

    def test_source_registry_fails_when_no_readable_source(self) -> None:
        report = verification_agent.verify_source_registry(
            {
                "schema": "codex.mn.sourceRegistry.v1",
                "sources": [
                    {"sourceId": "pdf:missing", "readable": False},
                    {"sourceId": "upload:stale", "readable": False},
                ],
            }
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertIn("no_readable_source", report["problems"])

    def test_workflow_and_skill_runs_report_terminal_status(self) -> None:
        workflow_report = verification_agent.verify_workflow_run(
            {"runId": "wf1", "status": "completed", "steps": [{"status": "completed"}]}
        )
        skill_report = verification_agent.verify_skill_run(
            {"runId": "sk1", "status": "completed", "acceptance": {"status": "accepted"}}
        )

        self.assertEqual(workflow_report["status"], "PASS")
        self.assertEqual(skill_report["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
