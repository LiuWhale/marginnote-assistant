from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MAIN_JS = PROJECT_ROOT / "extension/codex.mn.assistant/main.js"
PANEL_CONTROLLER_JS = PROJECT_ROOT / "extension/codex.mn.assistant/CodexWebPanelController.js"


class NativeTransactionStaticTests(unittest.TestCase):
    def setUp(self) -> None:
        self.main_js = MAIN_JS.read_text(encoding="utf-8")
        self.panel_controller_js = PANEL_CONTROLLER_JS.read_text(encoding="utf-8")

    def test_ai_edit_events_carry_backend_transaction_evidence(self) -> None:
        for marker in [
            "aiEditTransactionStarted",
            "aiEditOperationReady",
            "aiEditTransactionAccepted",
            "aiEditTransactionRejected",
            "transactionId",
            "draftId",
            "createdNoteIds",
            "createdCount",
            "undoRollback",
            "deleted",
            "failed",
            "failures",
            "mnObjectId",
            "mnObjectKind",
            "mnObjectTitle",
            "mnObjectSourceRef",
            "objectRef",
        ]:
            self.assertIn(marker, self.main_js)

    def test_ai_edit_transaction_carries_queued_write_ownership(self) -> None:
        begin_body = self.main_js.split(
            "CodexAssistantAddon.prototype.beginAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.recordAiEditCreatedNote", 1)[0]
        finish_body = self.main_js.split(
            "CodexAssistantAddon.prototype.finishAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.acceptAiEditTransaction", 1)[0]
        accept_body = self.main_js.split(
            "CodexAssistantAddon.prototype.acceptAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.rejectAiEditTransaction", 1)[0]
        reject_body = self.main_js.split(
            "CodexAssistantAddon.prototype.rejectAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.writeDraft", 1)[0]

        self.assertIn("queueId", begin_body)
        self.assertIn("queueId: transaction.queueId", finish_body)
        self.assertIn("queueId: transaction ? transaction.queueId :", accept_body)
        self.assertIn("queueId: transaction.queueId", reject_body)
        for marker in ["sessionId", "sessionEpoch", "contextDocumentKey"]:
            self.assertIn(marker, begin_body)
            self.assertIn(marker, finish_body)

    def test_mindmap_diff_apply_registers_rollbackable_ai_edit_transaction(self) -> None:
        body = self.main_js.split("CodexAssistantAddon.prototype.applyMindmapDiffOperations", 1)[1].split(
            "CodexAssistantAddon.prototype.handleNativeQueueCommand", 1
        )[0]
        for marker in [
            "this.aiEditTransactions = this.aiEditTransactions || {};",
            "this.aiEditTransactions[transactionId]",
            "createdNoteIds: created.map(function(note) { return noteIdentifier(note); })",
            "createdNoteIdsMap",
            "mindmapDiffTransaction.createdNotes = created;",
            "objectRef: aiEditObjectRefFromDraft(command)",
            "startedAt",
        ]:
            self.assertIn(marker, body)

    def test_transaction_bridge_cannot_rebuild_rollback_authority_from_url_params(self) -> None:
        for marker in [
            "rejectAiEditTransaction(rejectTransactionId, params)",
            "acceptAiEditTransaction(acceptTransactionId, params)",
            "confirmMindmapDeleteTransaction(confirmDeleteTransactionId, params)",
            "dismissMindmapDeleteTransaction(dismissDeleteTransactionId, params)",
        ]:
            self.assertIn(marker, self.panel_controller_js)
        self.assertIn("function aiEditObjectRefFromBridgeParams", self.main_js)
        self.assertNotIn("function aiEditCreatedNoteIdsFromBridgeParams", self.main_js)
        self.assertNotIn("function aiEditCreatedCardIdsFromBridgeParams", self.main_js)
        self.assertNotIn("function fallbackAiEditTransactionFromBridge", self.main_js)
        reject_body = self.main_js.split(
            "CodexAssistantAddon.prototype.rejectAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.writeDraft", 1)[0]
        self.assertNotIn("this.aiEditTransactions[transactionId] = transaction", reject_body)
        self.assertIn("acceptAiEditTransaction = function(transactionId, fallback)", self.main_js)
        self.assertIn("rejectAiEditTransaction = function(transactionId, fallback)", self.main_js)

    def test_native_delete_suggestion_confirmation_posts_transaction_events(self) -> None:
        for marker in [
            "confirmMindmapDeleteTransaction = function(transactionId, fallback)",
            "dismissMindmapDeleteTransaction = function(transactionId, fallback)",
            "mindmapDeleteSuggestionConfirmed",
            "mindmapDeleteSuggestionDismissed",
            "targetNoteIdsString.split('|')",
            "deleteNoteForAiEdit(note, ctx, noteId)",
            "deleted: deleted",
            "failed: failed.length",
        ]:
            self.assertIn(marker, self.main_js)

    def test_reject_transaction_constrains_card_evidence_to_created_notes(self) -> None:
        for marker in [
            "createdCardIds",
            "createdCardIdsMap",
            "recordAiEditCreatedCard",
            "deletedCardIds",
            "failedCardIds",
        ]:
            self.assertIn(marker, self.main_js)
        reject_body = self.main_js.split(
            "CodexAssistantAddon.prototype.rejectAiEditTransaction", 1
        )[1].split("\n  CodexAssistantAddon.prototype.writeDraft", 1)[0]
        self.assertIn("if (!transaction.createdNoteIdsMap[cardId]) continue;", reject_body)
        self.assertNotIn("deleteCardForAiEdit", reject_body)

    def test_native_object_registry_scan_command_posts_registry_event(self) -> None:
        for marker in [
            "scan_mn_objects",
            "scanMnObjects",
            "serializeMnObjectForRegistry",
            "mnObjectRegistryScanRequested",
            "mnObjectRegistryScanFinished",
            "native_object_scan",
            "objectId: 'mnobj:note:' + noteId",
            "parentNoteId",
            "nodePath",
        ]:
            self.assertIn(marker, self.main_js)

    def test_native_object_registry_scan_command_is_routed_from_queue(self) -> None:
        body = self.main_js.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("if (nativeAction === 'scan_mn_objects')", body)
        self.assertIn("this.scanMnObjects(command)", body)

    def test_native_object_existence_probe_command_posts_probe_event(self) -> None:
        for marker in [
            "probe_mn_object_existence",
            "probeMnObjectExistence",
            "mnObjectExistenceProbeRequested",
            "mnObjectExistenceProbeFinished",
            "objectId: 'mnobj:note:' + noteId",
            "exists: !!note",
        ]:
            self.assertIn(marker, self.main_js)

    def test_native_object_existence_probe_command_is_routed_from_queue(self) -> None:
        body = self.main_js.split("CodexAssistantAddon.prototype.handleNativeQueueCommand", 1)[1].split(
            "CodexAssistantAddon.prototype.ackCommands", 1
        )[0]
        self.assertIn("if (nativeAction === 'probe_mn_object_existence')", body)
        self.assertIn("this.probeMnObjectExistence(command)", body)


if __name__ == "__main__":
    unittest.main()
