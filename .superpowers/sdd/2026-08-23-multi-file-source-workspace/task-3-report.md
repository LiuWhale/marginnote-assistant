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

## Fix Round 1

### Status and Commit

Completed as `8b9bae7` (`Harden source workspace queue binding`).

Changed files:

- `source_workspace.py`
- `companion.py`
- `tests/test_source_workspace.py`
- `tests/test_companion_controls.py`

### Findings Addressed

- Added a deterministic SHA-256 suffix derived from the original conversation ID to every managed workspace directory, while retaining a readable sanitized prefix. `A:B` and `A-B` no longer share storage or cleanup ownership.
- Revision-mismatched generation records are now rejected with workspace-validation evidence, copied to `queue/rejected/<queue-file>.jsonl`, atomically removed from the active queue, and excluded from dispatch. Polling continues to later valid records.
- This supersedes the original report concern that a mismatched item remained pending until manual acknowledgement.
- Explicit inner commands now inherit `conversationId`, ordered `sourceIds`, `followCurrentDocument`, `sourceWorkspaceRevision`, and `contextDocumentKey` from the authoritative enqueue payload.
- Workflow start persists the source binding in its run record. Workflow retry reconstructs its enqueue payload from that stored binding, so a retry request cannot drop or replace the original source revision.
- No `workflow_engine.py` change was required because Companion workflow run records already accept and preserve additional JSON fields.

### RED Evidence

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace.SourceWorkspaceTests.test_distinct_conversation_ids_with_same_readable_prefix_use_distinct_workspaces tests.test_companion_controls.CompanionControlsTests.test_queue_revision_mismatch_quarantines_stale_item_and_dispatches_later_valid_work tests.test_companion_controls.CompanionControlsTests.test_explicit_queue_command_inherits_authoritative_source_binding tests.test_companion_controls.CompanionControlsTests.test_workflow_retry_preserves_source_binding_from_started_run -v
```

Output:

```text
Ran 4 tests in 6.094s

FAILED (failures=2, errors=2)
```

Observed failures were exact reproductions of the review findings:

- `A:B` and `A-B` returned the same workspace path.
- The first stale queue record returned `source_workspace_revision_mismatch` with `pending: 2` and no later command.
- The explicit command raised `KeyError: 'conversationId'`.
- The workflow retry command raised `KeyError: 'conversationId'`.

### GREEN Evidence

Focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace.SourceWorkspaceTests.test_distinct_conversation_ids_with_same_readable_prefix_use_distinct_workspaces tests.test_companion_controls.CompanionControlsTests.test_queue_revision_mismatch_quarantines_stale_item_and_dispatches_later_valid_work tests.test_companion_controls.CompanionControlsTests.test_explicit_queue_command_inherits_authoritative_source_binding tests.test_companion_controls.CompanionControlsTests.test_workflow_retry_preserves_source_binding_from_started_run -v
```

Output:

```text
Ran 4 tests in 4.004s

OK
```

Full regression command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace tests.test_companion_controls -q
```

Output:

```text
----------------------------------------------------------------------
Ran 254 tests in 183.449s

OK
```

Static verification:

- `git diff --check`: passed with no output.
- In-memory `compile()` of all four changed Python files: `syntax ok`.

### Self-Review

- Confirmed colliding readable prefixes produce different paths and clearing one leaves the other workspace intact.
- Confirmed quarantine storage is outside the active queue glob and retains the rejected record, rejection reason, timestamp, and workspace validation evidence.
- Confirmed the stale queue ID is removed before later valid commands are returned and cannot appear in the dispatch list.
- Confirmed explicit command fields are overwritten by the authoritative outer payload rather than trusted from the inner command.
- Confirmed workflow retry uses the binding persisted at workflow start even when the retry request carries no source metadata.
- Confirmed existing unbound single-document queue commands retain their previous behavior.

### Remaining Concerns

- Queue file mutation retains the repository's existing single-process/no-lock assumption; this fix does not introduce a new queue concurrency model.
- Model execution and Web UI integration remain intentionally outside Task 3.

## Fix Round 2

### Status and Commit

Completed as `bf7d7af` (`Migrate owned legacy source workspaces`).

Changed files:

- `source_workspace.py`
- `tests/test_source_workspace.py`
- `tests/test_companion_controls.py`

### Finding Addressed

- Added a constrained compatibility resolver for the single pre-digest workspace path derived from the requested conversation ID.
- Migration is attempted only when the digest path is absent. The legacy root must be a real directory and `manifest.json` must be a real regular file with `codex.mn.sourceWorkspace.v1` and an exact `conversationId` match.
- An owned legacy workspace is moved atomically with `os.rename()` to the digest path. Ownership mismatch, unsafe filesystem types, invalid manifests, or a migration destination race fail closed and leave legacy content untouched.
- `clear_workspace()` may remove the legacy directory only after the same exact ownership proof and the existing managed-entry audit.
- New manifests now retain the original conversation ID instead of the sanitized display prefix, enabling exact future ownership checks.
- Queue validation uses the migrated workspace, so a valid pre-upgrade queued command remains dispatchable and is not quarantined.

### RED Evidence

Command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace.SourceWorkspaceTests.test_valid_legacy_workspace_migrates_to_digest_path_without_touching_source tests.test_source_workspace.SourceWorkspaceTests.test_alias_cannot_migrate_or_clear_another_conversation_legacy_workspace tests.test_companion_controls.CompanionControlsTests.test_matching_queued_command_dispatches_after_legacy_workspace_migration -v
```

Output:

```text
Ran 3 tests in 0.180s

FAILED (failures=3)
```

Observed failures:

- Valid legacy load returned `workspace manifest is missing`.
- Alias clear returned success without proving legacy ownership.
- Polling rejected and quarantined the matching queued command because the digest workspace was missing.

### GREEN Evidence

Focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace.SourceWorkspaceTests.test_valid_legacy_workspace_migrates_to_digest_path_without_touching_source tests.test_source_workspace.SourceWorkspaceTests.test_alias_cannot_migrate_or_clear_another_conversation_legacy_workspace tests.test_companion_controls.CompanionControlsTests.test_matching_queued_command_dispatches_after_legacy_workspace_migration -v
```

Output:

```text
Ran 3 tests in 0.162s

OK
```

Source-workspace module command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace -q
```

Output:

```text
----------------------------------------------------------------------
Ran 13 tests in 0.026s

OK
```

Full regression command:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_source_workspace tests.test_companion_controls -q
```

Output:

```text
----------------------------------------------------------------------
Ran 257 tests in 180.829s

OK
```

Static verification:

- `git diff --check`: passed with no output.
- In-memory `compile()` of the three changed Python files: `syntax ok`.

### Self-Review

- Confirmed no directory scan or broad fallback is used; only `<source-workspaces>/<safe-id>` is considered.
- Confirmed path and manifest filesystem types are inspected without accepting symlink roots or symlink manifests.
- Confirmed exact manifest ownership is checked before rename or legacy cleanup.
- Confirmed alias load and clear both fail, leave the legacy directory intact, and do not create an alias digest workspace.
- Confirmed authorized legacy cleanup removes managed workspace links but leaves original source targets and contents unchanged.
- Confirmed queue polling returns the valid matching command with zero rejected records after migration.

### Remaining Concerns

- A pre-release legacy manifest whose conversation ID was itself altered by the old sanitizer cannot satisfy exact ownership proof. It is intentionally left untouched and must be rebuilt rather than adopted ambiguously.
- The existing queue single-process/no-lock assumption remains unchanged.
