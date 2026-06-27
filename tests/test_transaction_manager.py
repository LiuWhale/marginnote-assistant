from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import transaction_manager


class TransactionManagerTests(unittest.TestCase):
    def test_started_ready_accept_events_update_transaction_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))

            started = transaction_manager.apply_native_event(
                {
                    "event": "aiEditTransactionStarted",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-1",
                        "draftId": "draft-1",
                        "cards": 2,
                        "hasMindmap": True,
                    },
                }
            )
            self.assertTrue(started["ok"])
            self.assertEqual(started["transaction"]["status"], "started")

            ready = transaction_manager.apply_native_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-1",
                        "draftId": "draft-1",
                        "createdNoteIds": ["N1", "N2", "N3"],
                        "createdCount": 3,
                        "card_count": 2,
                        "has_mindmap": True,
                    },
                }
            )
            self.assertEqual(ready["transaction"]["status"], "ready")
            self.assertEqual(ready["transaction"]["createdNoteIds"], ["N1", "N2", "N3"])

            accepted = transaction_manager.apply_native_event(
                {
                    "event": "aiEditTransactionAccepted",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-1",
                        "message": "已保留本次 AI 编辑结果。",
                    },
                }
            )

            self.assertEqual(accepted["transaction"]["status"], "accepted")
            loaded = transaction_manager.load_transaction("ai-edit-1")
            self.assertEqual(loaded["transactionId"], "ai-edit-1")
            self.assertEqual(loaded["draftId"], "draft-1")
            self.assertEqual(loaded["createdCount"], 3)

    def test_mindmap_diff_apply_finished_persists_transaction_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))

            result = transaction_manager.apply_native_event(
                {
                    "event": "mindmapDiffApplyFinished",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "mindmap-diff-apply-1",
                        "draftId": "draft-mm",
                        "createdNoteIds": ["N-new"],
                        "appliedOperations": [
                            {"opId": "mindmap-diff:1", "mutation": "create", "noteId": "N-new"}
                        ],
                        "appliedCount": 1,
                        "failedCount": 0,
                        "verification": {
                            "schema": "codex.mn.mindmapDiffApplyVerification.v1",
                            "status": "pass",
                            "summary": "脑图 Diff 验证：通过 1，失败 0。",
                            "operationVerification": [
                                {"opId": "mindmap-diff:1", "noteId": "N-new", "ok": True}
                            ],
                        },
                    },
                }
            )

            self.assertTrue(result["ok"], result)
            tx = result["transaction"]
            self.assertEqual(tx["transactionId"], "mindmap-diff-apply-1")
            self.assertEqual(tx["status"], "pending_confirmation")
            self.assertEqual(tx["createdNoteIds"], ["N-new"])
            self.assertEqual(tx["createdCount"], 1)
            self.assertTrue(tx["hasMindmap"])
            self.assertTrue(tx["requiresConfirmation"])
            self.assertIn("retain", tx["availableActions"])
            self.assertIn("rollback", tx["availableActions"])
            self.assertEqual(tx["mindmapDiffApply"]["verification"]["status"], "pass")
            report = transaction_manager.verification_report(tx)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["transactionStatus"], "pending_confirmation")
            self.assertTrue(report["requiresConfirmation"])
            self.assertIn("保留", report["summary"])
            self.assertIn("脑图 Diff", report["summary"])

    def test_mindmap_delete_suggestion_events_create_confirmation_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))

            prepared = transaction_manager.apply_native_event(
                {
                    "event": "mindmapDeleteSuggestionPrepared",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "delete-suggest-1",
                        "targetNoteIds": ["N-old"],
                        "deleteOperations": [
                            {
                                "opId": "mindmap-diff:delete",
                                "title": "Obsolete",
                                "currentRef": {"noteId": "N-old"},
                                "reason": "missing-in-proposed-tree",
                            }
                        ],
                    },
                }
            )

            tx = prepared["transaction"]
            self.assertEqual(tx["status"], "delete_pending_confirmation")
            self.assertTrue(tx["requiresConfirmation"])
            self.assertEqual(tx["targetNoteIds"], ["N-old"])
            self.assertIn("confirm_delete", tx["availableActions"])
            self.assertIn("dismiss", tx["availableActions"])
            report = transaction_manager.verification_report(tx)
            self.assertEqual(report["status"], "pending")
            self.assertEqual(report["transactionStatus"], "delete_pending_confirmation")
            self.assertTrue(report["requiresConfirmation"])
            self.assertEqual(report["targetNoteIds"], ["N-old"])
            self.assertIn("删除建议", report["summary"])

            confirmed = transaction_manager.apply_native_event(
                {
                    "event": "mindmapDeleteSuggestionConfirmed",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "delete-suggest-1",
                        "ok": True,
                        "deleted": 1,
                        "failed": 0,
                        "targetNoteIds": ["N-old"],
                    },
                }
            )

            self.assertEqual(confirmed["transaction"]["status"], "delete_confirmed")
            confirmed_report = transaction_manager.verification_report(confirmed["transaction"])
            self.assertEqual(confirmed_report["status"], "pass")
            self.assertIn("已删除", confirmed_report["summary"])

    def test_transaction_preserves_mn_object_reference_in_summary_and_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))
            ready = transaction_manager.apply_native_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-object",
                        "draftId": "draft-object",
                        "createdNoteIds": ["N1"],
                        "mnObjectId": "mnobj:selection:abc123",
                        "mnObjectKind": "selection",
                        "mnObjectTitle": "PDF 选区",
                        "mnObjectSourceRef": {"page": 3, "quote": "source quote"},
                    },
                }
            )

            tx = ready["transaction"]
            self.assertEqual(tx["objectRef"]["objectId"], "mnobj:selection:abc123")
            self.assertEqual(tx["objectRef"]["kind"], "selection")
            self.assertEqual(tx["objectRef"]["sourceRef"]["quote"], "source quote")

            summary = transaction_manager.transaction_summary(tx)
            verification = transaction_manager.verification_report(tx)
            latest = transaction_manager.latest_status(topicid="T1", bookmd5="B1")

            self.assertEqual(summary["objectRef"]["objectId"], "mnobj:selection:abc123")
            self.assertEqual(verification["objectRef"]["objectId"], "mnobj:selection:abc123")
            self.assertEqual(latest["latest"]["objectRef"]["objectId"], "mnobj:selection:abc123")
            self.assertEqual(latest["verification"]["objectRef"]["kind"], "selection")

    def test_reject_event_records_deleted_failed_and_rollback_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))
            transaction_manager.apply_native_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-2",
                        "draftId": "draft-2",
                        "createdNoteIds": ["N1", "N2"],
                        "createdCount": 2,
                    },
                }
            )

            rejected = transaction_manager.apply_native_event(
                {
                    "event": "aiEditTransactionRejected",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-2",
                        "ok": False,
                        "deleted": 1,
                        "failed": 1,
                        "failures": [{"noteId": "N2", "reason": "still-exists-after-delete"}],
                        "undoRollback": {"ok": False, "method": "undo", "remaining": 1},
                    },
                }
            )

            tx = rejected["transaction"]
            self.assertEqual(tx["status"], "rollback_failed")
            self.assertEqual(tx["deletedCount"], 1)
            self.assertEqual(tx["failedCount"], 1)
            self.assertEqual(tx["failures"][0]["noteId"], "N2")
            self.assertEqual(tx["undoRollback"]["method"], "undo")

    def test_reject_report_distinguishes_outline_and_card_residuals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))
            transaction_manager.apply_native_event(
                {
                    "event": "aiEditOperationReady",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-card-residual",
                        "draftId": "draft-card",
                        "createdNoteIds": ["N1", "N2"],
                        "createdCardIds": ["C1"],
                        "createdCount": 2,
                        "card_count": 1,
                        "has_mindmap": True,
                    },
                }
            )

            rejected = transaction_manager.apply_native_event(
                {
                    "event": "aiEditTransactionRejected",
                    "topicid": "T1",
                    "bookmd5": "B1",
                    "extra": {
                        "transactionId": "ai-edit-card-residual",
                        "ok": False,
                        "deleted": 1,
                        "failed": 2,
                        "deletedNoteIds": ["N1"],
                        "failedNoteIds": ["N2"],
                        "deletedCardIds": [],
                        "failedCardIds": ["C1"],
                        "failures": [
                            {"noteId": "N2", "reason": "still-exists-after-delete"},
                            {"cardId": "C1", "reason": "card-delete-unsupported"},
                        ],
                    },
                }
            )

            tx = rejected["transaction"]
            self.assertEqual(tx["deletedNoteIds"], ["N1"])
            self.assertEqual(tx["failedNoteIds"], ["N2"])
            self.assertEqual(tx["createdCardIds"], ["C1"])
            self.assertEqual(tx["deletedCardIds"], [])
            self.assertEqual(tx["failedCardIds"], ["C1"])
            report = transaction_manager.verification_report(tx)
            residual = report["residualProof"]
            self.assertEqual(report["status"], "block")
            self.assertEqual(residual["schema"], "codex.mn.residualProof.v1")
            self.assertEqual(residual["status"], "block")
            self.assertIn("N2", residual["residualNoteIds"])
            self.assertIn("C1", residual["residualCardIds"])
            self.assertEqual(residual["remainingCount"], 2)
            by_object = {item["objectId"]: item for item in residual["objects"]}
            self.assertEqual(by_object["mnobj:note:N2"]["objectType"], "mindmap_node")
            self.assertEqual(by_object["mnobj:card:C1"]["objectType"], "card")

    def test_verification_report_distinguishes_complete_and_failed_rollback(self) -> None:
        complete = {
            "transactionId": "ai-edit-ok",
            "status": "rolled_back",
            "createdNoteIds": ["N1", "N2"],
            "createdCount": 2,
            "deletedCount": 2,
            "failedCount": 0,
        }
        failed = {
            "transactionId": "ai-edit-failed",
            "status": "rollback_failed",
            "createdNoteIds": ["N1", "N2", "N3"],
            "createdCount": 3,
            "deletedCount": 1,
            "failedCount": 2,
            "failures": [{"noteId": "N2", "reason": "still-exists-after-delete"}],
        }

        complete_report = transaction_manager.verification_report(complete)
        failed_report = transaction_manager.verification_report(failed)

        self.assertEqual(complete_report["schema"], "codex.mn.aiEditVerification.v1")
        self.assertEqual(complete_report["status"], "pass")
        self.assertTrue(complete_report["rollbackComplete"])
        self.assertEqual(complete_report["remainingCount"], 0)
        self.assertIn("PASS", complete_report["summary"])

        self.assertEqual(failed_report["status"], "block")
        self.assertFalse(failed_report["rollbackComplete"])
        self.assertEqual(failed_report["remainingCount"], 2)
        self.assertEqual(failed_report["remainingNoteIds"], ["N2", "N3"])
        self.assertIn("N2", failed_report["summary"])

    def test_latest_summary_filters_by_topic_and_book(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            transaction_manager.configure(Path(tmp))
            for idx, topic in enumerate(["T1", "T2"], start=1):
                transaction_manager.apply_native_event(
                    {
                        "event": "aiEditOperationReady",
                        "topicid": topic,
                        "bookmd5": "B1",
                        "extra": {
                            "transactionId": f"ai-edit-{idx}",
                            "draftId": f"draft-{idx}",
                            "createdNoteIds": [f"N{idx}"],
                        },
                    }
                )

            summary = transaction_manager.latest_summary(topicid="T1", bookmd5="B1", limit=10)

            self.assertEqual(summary["count"], 1)
            self.assertEqual(summary["items"][0]["transactionId"], "ai-edit-1")


if __name__ == "__main__":
    unittest.main()
