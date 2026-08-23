# Task 5 Report: Multi-File Source Picker UI

## Status

Implemented and committed on `feature/multi-file-source-workspace`.

The Web panel now has one compact `资料 N` header control and a dedicated source page. The page reads and persists the reviewed source-workspace contract, carries the conversation-bound source snapshot through direct and queued generation requests, reports source coverage on answers, and fails closed before answer-derived card or mind-map writes when coverage is incomplete.

## Scope

Implementation changes are limited to:

- `extension/codex.mn.assistant/web/index.html`
- `extension/codex.mn.assistant/web/app.js`
- `extension/codex.mn.assistant/web/app.css`
- `tests/test_web_controls_static.py`
- `tests/test_resizable_panel_static.py`

This report is the only additional file. No backend file was changed.

## TDD Evidence

### RED

Command:

```text
python3 -m unittest \
  tests.test_web_controls_static.WebControlsStaticTests.test_chat_header_has_multi_file_source_control_and_page \
  tests.test_web_controls_static.WebControlsStaticTests.test_generation_payload_and_source_coverage_are_fail_closed \
  tests.test_web_controls_static.WebControlsStaticTests.test_follow_current_document_preserves_explicit_selection \
  tests.test_resizable_panel_static.ResizablePanelContractTest.test_source_workspace_page_fits_minimum_panel_and_long_names \
  -v
```

Observed result before production edits: `4` tests ran and all `4` failed for the intended missing controls, source payload/coverage behavior, follow-current synchronization, and responsive source-page CSS. The full two-suite RED run had exactly these four new failures; existing tests remained green.

### GREEN

Final command:

```text
python3 -m unittest tests.test_web_controls_static tests.test_resizable_panel_static -q
```

Observed result:

```text
Ran 137 tests in 0.285s
OK
```

Additional verification:

```text
node --check extension/codex.mn.assistant/web/app.js  # exit 0
git diff --check                                      # exit 0
```

## Implementation

### Source Picker

- Added the compact `资料 N` control with neutral, green, yellow, and red states.
- Added a History/Settings-style full page with `返回对话`, the current file, notebook files, uploads, local/search candidates, native checkboxes, per-file type/size/readability/extraction state, removal, validation, clear-all, and done controls.
- Long names use full-title tooltips and `overflow-wrap: anywhere`; absolute paths are absent from ordinary rows and are populated only after the technical diagnostics disclosure is expanded.
- The initial followed workspace selects the current document when a conversation has no stored selection.

### State and Persistence

- Added `state.sourceWorkspace`, `state.sourceWorkspaceCandidates`, `state.sourceWorkspaceSelection`, and `state.followCurrentDocument`.
- Added `source_workspace_get`, `source_workspace_update`, `source_workspace_validate`, and `source_workspace_clear` flows.
- Conversation new/load summaries hydrate `sourceIds`, `followCurrentDocument`, and `sourceWorkspaceRevision`.
- With follow enabled, a document switch removes all old current-document representations, preserves every additional explicit source, adds the new current document, and rebuilds the new conversation workspace. With follow disabled, membership is unchanged and rebuilt as-is; unavailable preserved IDs remain visible and fail validation rather than being silently dropped.

### Generation and Coverage Safety

- The common payload builder always carries ordered `sourceIds`, `followCurrentDocument`, `sourceWorkspaceRevision`, and `conversationId`.
- Enqueued commands retain their original source snapshot, and queued execution forwards that snapshot instead of replacing it with current UI state.
- Sending is blocked while a selected workspace is unsaved, invalid, mismatched, or validating.
- Requests show `本次资料：N 个文件，均可读`; replies show `已读取 X/N 个文件`.
- The footer accepts both the reviewed `readIds`/`unreadIds`/`missingIds` names and the current backend's `read`/`unread`/`missing` aliases.
- Incomplete or unconfirmed source usage keeps a real textual answer copyable but suppresses answer-derived actions. Draft and goal flows also stop before draft persistence, native write dispatch, or derived queue creation unless both `sourceUsage.complete === true` and `answerDerivedWritesEligible === true`.

## Static Layout Evidence

No screenshot artifact was produced. The responsive static suite verifies:

- `.source-workspace-row` uses `18px minmax(0, 1fr) auto` tracks.
- `.source-workspace-name` has `min-width: 0` and `overflow-wrap: anywhere`.
- `.source-workspace-commands` uses three equal `minmax(0, 1fr)` columns.
- Command buttons have a shared minimum height and `height: 100%`.
- The source page introduces no fixed width above the panel's `390px` minimum.
- The `max-width: 520px` header layout leaves room for the added compact source control.

## Commits

- `a327b5d` - `Add multi-file source picker`
- Report commit - the separate commit containing this report.

## Self-Review

- Re-read binding sections 2.2, 7, and 8 against the final implementation.
- Confirmed source selection remains read-only authority and never broadens the existing single-notebook write target.
- Confirmed missing source acknowledgements fail closed for every answer-derived write path.
- Confirmed ordinary rows and tooltips expose names and status, not absolute paths or hashes.
- Confirmed only the five authorized implementation/test files changed before the implementation commit.
- Confirmed no backend contract or backend implementation was modified.

## Concerns

- Verification is static plus JavaScript syntax checking; a live MarginNote WebView/Companion session was not available in this task, so native visual interaction and real source-candidate data were not exercised here.
- The reviewed candidate response does not guarantee a byte-size field. The UI shows a formatted size when `size`, `byteSize`, or `fileSize` exists and otherwise displays `大小未知`.
