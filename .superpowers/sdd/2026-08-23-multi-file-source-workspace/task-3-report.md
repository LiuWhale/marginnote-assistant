# Task 3 Report: Source Workspace API, Conversation Persistence, and Queue Revision Binding

## Status

Completed and committed as `c3c5e29` (`Persist conversation source workspaces`).

## Files

- `companion.py`
- `tests/test_companion_controls.py`

This report is recorded separately from the implementation commit.

## Implemented Scope

- Added the read-only Companion actions `source_workspace_get`, `source_workspace_update`, `source_workspace_validate`, and `source_workspace_clear`.
- Resolved requested source IDs only from a fresh trusted candidate list, rejected unknown IDs, prepared text artifacts, and refused partial workspace builds when extraction failed.
- Persisted ordered `sourceIds`, `followCurrentDocument`, and `sourceWorkspaceRevision` in new, saved, listed, and loaded conversation state.
- Validated an existing workspace on conversation load and rebuilt it from trusted candidates when missing or stale.
- Cleared the managed workspace only after conversation document/MNObject ownership validation; legacy sessions without a conversation ID remain deletable.
- Added source metadata to queue records and raw generation commands.
- Blocked queued generation dispatch when the queued source revision, source IDs, or required binding no longer matches the managed workspace.
- Left model execution and the Web UI unchanged, as required.

## RED Evidence

Required API RED command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_source_workspace_update_persists_selection_and_returns_revision -v
```

Result: 1 test ran and failed with `未知动作：source_workspace_update`, confirming the action dispatch was absent.

Rebuild revision RED command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_conversation_load_restores_source_metadata_and_rebuilds_missing_workspace -v
```

Result: 1 test ran and failed because the loaded conversation returned the pre-rebuild revision instead of the rebuilt workspace revision.

Legacy deletion RED command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_conversation_delete_keeps_legacy_sessions_without_conversation_id_compatible -v
```

Result: 1 test errored because cleanup attempted to derive a workspace path from an empty legacy `conversationId`.

## GREEN Evidence

Focused Task 3 command:

```sh
python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_source_workspace_update_persists_selection_and_returns_revision tests.test_companion_controls.CompanionControlsTests.test_source_workspace_update_rejects_unknown_and_broken_sources tests.test_companion_controls.CompanionControlsTests.test_source_workspace_clear_preserves_history_and_clears_conversation_metadata tests.test_companion_controls.CompanionControlsTests.test_conversation_load_restores_source_metadata_and_rebuilds_missing_workspace tests.test_companion_controls.CompanionControlsTests.test_conversation_delete_clears_workspace_only_after_ownership_validation tests.test_companion_controls.CompanionControlsTests.test_queue_revision_mismatch_blocks_raw_generation_dispatch -v
```

Result: 6 tests ran in 1.163 seconds; all passed.

The rebuild revision regression passed independently after updating the returned conversation metadata. The ownership-aware and legacy conversation deletion tests then ran together: 2 tests in 0.337 seconds; both passed.

Final regression command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_companion_controls -q
```

Result: 241 tests ran in 176.015 seconds; all passed, including existing cross-document conversation and queue behavior.

Static checks:

- `git diff --check`: passed with no output.
- In-memory `compile()` of `companion.py` and `tests/test_companion_controls.py`: `syntax ok`.

## Commit

- `c3c5e29 Persist conversation source workspaces`

## Self-Review

- Confirmed all source paths originate from `source_workspace_candidates()` and no arbitrary path is accepted by the update action.
- Confirmed failed extraction does not call `build_workspace()` and therefore does not replace an existing managed workspace with a partial source set.
- Confirmed source actions find saved conversations by stable conversation ID and apply the existing `contextDocumentKey` and MNObject ownership checks before mutation.
- Confirmed conversation deletion performs ownership validation before workspace cleanup.
- Confirmed queued raw generation records and commands carry the same ordered source metadata and stale bindings return no dispatchable command.
- Confirmed legacy queued actions without a selected source set continue through the existing path.
- Confirmed the diff is limited to the two implementation files required by the task; the report is the requested SDD artifact.

## Concerns

- A queue item blocked by a source-workspace mismatch remains pending until the caller updates or acknowledges it; this preserves the specification's no-silent-rebinding rule.
- Model execution from the managed workspace and Web UI source controls remain intentionally out of scope for Task 3.
