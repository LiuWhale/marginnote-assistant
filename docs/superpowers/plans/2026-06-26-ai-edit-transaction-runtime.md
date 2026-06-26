# AI Edit Transaction Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a persistent transaction runtime for AI edits so MN card/mindmap writes are recorded, inspectable, accepted, rejected, and verifiable from the Companion backend.

**Architecture:** Keep the existing MN4 native write path, but add a backend transaction store under `control/ai-edit-transactions`. MN4 native events remain the source of actual note creation and rollback, while Companion consumes those events to persist transaction manifests and status. This is Phase 1 foundation for operation plans, verification agent, and later URL API adapter integration.

**Tech Stack:** Python 3 standard library, existing `companion.py` HTTP/event flow, existing MarginNote JSB native bridge in `extension/codex.mn.assistant/main.js`, `unittest`.

---

## File Structure

- Create: `transaction_manager.py`  
  Owns transaction file paths, safe ids, transaction creation, event application, accept/reject status updates, summaries, and retention-safe JSON writes.

- Modify: `companion.py`  
  Imports `transaction_manager`, configures its directory from `ROOT`, calls it from `append_event()`, exposes read-only transaction summaries in `/status`, and adds direct actions for listing/getting transactions.

- Modify: `extension/codex.mn.assistant/main.js`  
  Enriches existing AI edit events with `draftId`, `createdNoteIds`, `createdCount`, rollback deletion counts, and transaction state so Companion has enough evidence.

- Create: `tests/test_transaction_manager.py`  
  Unit tests for event-driven transaction persistence and summary behavior.

- Modify: `tests/test_companion_controls.py`  
  Integration tests that native event ingestion creates/updates persistent transactions through `append_event()`.

- Modify: `tests/test_web_controls_static.py` or `tests/test_resizable_panel_static.py` if UI status exposure changes.

## Task 1: Transaction Store Unit

**Files:**
- Create: `transaction_manager.py`
- Test: `tests/test_transaction_manager.py`

- [ ] **Step 1: Write tests for transaction event ingestion**

```python
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import transaction_manager


class TransactionManagerTests(unittest.TestCase):
    def test_started_ready_accept_and_reject_events_update_transaction_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transaction_manager.configure(root)

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
            self.assertEqual(loaded["status"], "accepted")

    def test_reject_event_records_deleted_failed_and_rollback_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transaction_manager.configure(root)
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

    def test_latest_summary_filters_by_topic_and_book(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            transaction_manager.configure(root)
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_transaction_manager -v`  
Expected: FAIL because `transaction_manager.py` does not exist.

- [ ] **Step 3: Implement transaction_manager.py**

Create functions:

```python
configure(root: Path) -> None
apply_native_event(event_record: dict[str, Any]) -> dict[str, Any]
load_transaction(transaction_id: str) -> dict[str, Any]
latest_summary(topicid: str = "", bookmd5: str = "", limit: int = 8) -> dict[str, Any]
```

Store one JSON per transaction at `control/ai-edit-transactions/<safe-id>.json`. Sanitize ids to `[A-Za-z0-9_-]`, keep created note ids unique, and never throw for unrelated native events; return `{"ok": False, "reason": "ignored-event"}`.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_transaction_manager -v`  
Expected: PASS.

## Task 2: Companion Event Integration

**Files:**
- Modify: `companion.py`
- Test: `tests/test_companion_controls.py`

- [ ] **Step 1: Add integration test**

Add a test that loads Companion with a temp root, calls `append_event()` with `aiEditTransactionStarted`, `aiEditOperationReady`, and `aiEditTransactionRejected`, then asserts `status_payload()["aiEditTransactions"]` contains the transaction and rollback counts.

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_ai_edit_events_persist_transaction_summary -v`  
Expected: FAIL because status does not expose `aiEditTransactions`.

- [ ] **Step 3: Wire transaction_manager into companion.py**

Import and configure `transaction_manager`. In `append_event()`, after writing `events.jsonl`, call `transaction_manager.apply_native_event(record)` and ignore `ignored-event`. In `status_payload()`, include:

```python
"aiEditTransactions": transaction_manager.latest_summary(
    topicid=str(payload_topic_id or ""),
    bookmd5=str(payload_book_md5 or ""),
    limit=8,
)
```

If `status_payload()` has no payload argument, use an unfiltered latest summary and add filtered summaries to action responses where topic/book are available.

- [ ] **Step 4: Run integration test**

Run: `python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_ai_edit_events_persist_transaction_summary -v`  
Expected: PASS.

## Task 3: Native Event Enrichment

**Files:**
- Modify: `extension/codex.mn.assistant/main.js`
- Test: `tests/test_resizable_panel_static.py` or a new static test

- [ ] **Step 1: Add static test for event payload contract**

Assert `main.js` contains:

```text
aiEditTransactionStarted
aiEditOperationReady
aiEditTransactionAccepted
aiEditTransactionRejected
createdNoteIds
undoRollback
deleted
failed
failures
```

- [ ] **Step 2: Run test to verify current state**

Run: `python3 -m unittest tests.test_resizable_panel_static -v`  
Expected: PASS if current native payload already has all fields; otherwise FAIL and patch native events.

- [ ] **Step 3: Patch native events if needed**

Ensure accept/reject events include `draftId`, `createdNoteIds`, `createdCount`, `topicid`, and rollback details. Keep existing UI callbacks unchanged.

- [ ] **Step 4: Run static tests**

Run: `python3 -m unittest tests.test_resizable_panel_static tests.test_web_controls_static -v`  
Expected: PASS.

## Task 4: Verification Commands

**Files:**
- Modify: `companion.py`
- Test: `tests/test_companion_controls.py`

- [ ] **Step 1: Add `ai_edit_transaction_list` and `ai_edit_transaction_get` actions**

These are read-only actions. They let UI or diagnostics fetch transaction history without parsing logs.

- [ ] **Step 2: Test read-only action permission**

Add these actions to `READ_ONLY_ACTIONS`. Test `handle_action({"action": "ai_edit_transaction_list"})` returns a summary.

- [ ] **Step 3: Run action tests**

Run: `python3 -m unittest tests.test_companion_controls -v`  
Expected: PASS.

## Task 5: Verification

**Files:**
- No new files unless tests require fixtures.

- [ ] **Step 1: Run focused tests**

Run:

```bash
python3 -m unittest tests.test_transaction_manager tests.test_companion_controls tests.test_resizable_panel_static tests.test_web_controls_static -v
```

Expected: PASS.

- [ ] **Step 2: Run syntax checks**

Run:

```bash
python3 -m py_compile companion.py transaction_manager.py diagnostic_log.py update_manager.py runtime_config.py
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
```

Expected: no output and exit code 0.

- [ ] **Step 3: Run full unit suite**

Run: `python3 -m unittest discover -s tests -v`  
Expected: PASS.

## Scope Gaps After Phase 1

This plan does not implement the full Operation Language, Knowledge Graph, Workflow Engine, URL API adapter, or skill marketplace. It creates the transaction runtime they require. The next plan should target `MarginNoteApiAdapter + URL API Gateway integration` or `Mindmap Diff Engine`.

