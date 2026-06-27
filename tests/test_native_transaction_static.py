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

    def test_transaction_bridge_can_rebuild_rollback_transaction_from_ledger_params(self) -> None:
        for marker in [
            "rejectAiEditTransaction(rejectTransactionId, params)",
            "acceptAiEditTransaction(acceptTransactionId, params)",
            "confirmMindmapDeleteTransaction(confirmDeleteTransactionId, params)",
            "dismissMindmapDeleteTransaction(dismissDeleteTransactionId, params)",
        ]:
            self.assertIn(marker, self.panel_controller_js)
        for marker in [
            "function aiEditObjectRefFromBridgeParams",
            "function aiEditCreatedNoteIdsFromBridgeParams",
            "function fallbackAiEditTransactionFromBridge",
            "createdNoteIdsString.split('|')",
            "fallbackAiEditTransactionFromBridge(transactionId, fallback)",
            "this.aiEditTransactions[transactionId] = transaction;",
            "acceptAiEditTransaction = function(transactionId, fallback)",
            "rejectAiEditTransaction = function(transactionId, fallback)",
        ]:
            self.assertIn(marker, self.main_js)

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

    def test_reject_transaction_carries_card_rollback_evidence(self) -> None:
        for marker in [
            "createdCardIds",
            "createdCardIdsMap",
            "recordAiEditCreatedCard",
            "deletedCardIds",
            "failedCardIds",
            "deleteCardForAiEdit",
            "reason: 'card-delete-unsupported'",
        ]:
            self.assertIn(marker, self.main_js)

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
