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

## Fix Round 1

### Findings Addressed

- **C1:** `conversation_new` previously inherited the active conversation's `sourceIds` and `sourceWorkspaceRevision` through the common payload builder.
- **I1:** source-workspace callbacks could apply a response after the active conversation changed inside the same document.
- **I2:** the minimum-width header depended on a tightly packed single row and could clip controls despite reduced fixed button widths.

### RED Evidence

Added these tests before production changes:

```text
test_new_conversation_payload_is_source_clean_and_failure_preserves_state
test_source_workspace_callbacks_ignore_stale_conversation_or_document
test_minimum_width_header_reflows_without_horizontal_clipping
```

Focused command:

```text
python3 -m unittest \
  tests.test_web_controls_static.WebControlsStaticTests.test_new_conversation_payload_is_source_clean_and_failure_preserves_state \
  tests.test_web_controls_static.WebControlsStaticTests.test_source_workspace_callbacks_ignore_stale_conversation_or_document \
  tests.test_resizable_panel_static.ResizablePanelContractTest.test_minimum_width_header_reflows_without_horizontal_clipping \
  -v
```

Observed before implementation: all three tests failed for the intended missing source-clean branch, missing async identity guard, and missing two-row minimum-width header contract.

### Implementation

- `companionPayload('conversation_new', ...)` now removes `conversationId`, `sessionId`, `sourceIds`, and `sourceWorkspaceRevision`, and forces `followCurrentDocument = true`.
- Successful conversation creation goes through `initializeNewConversationState()`, which clears old candidates/workspace state and initializes selection and follow state only from the returned new-conversation summary before current-document auto-selection runs.
- A failed `conversation_new` callback does not call conversation/source-state initializers, preserving the active conversation and source selection.
- All four source actions now use `postSourceWorkspace()`. Each dispatch captures a monotonically increasing token, `conversationId`, and `contextDocumentKey`; the callback returns before any mutation unless all three still match.
- Conversation loads, document changes, and active-conversation deletion invalidate prior source requests and clear their in-flight send gate.
- At `max-width: 520px`, the topbar now has stable `identity modes` and `actions actions` rows. The action row uses five equal `minmax(0, 1fr)` tracks across the 366px content width, with normal wrapping and no fixed 42px/46px buttons.

### GREEN Evidence

Final verification:

```text
python3 -m unittest tests.test_web_controls_static tests.test_resizable_panel_static -q
Ran 140 tests in 0.274s
OK

node --check extension/codex.mn.assistant/web/app.js
exit 0

git diff --check
exit 0
```

### Self-Review and Concerns

- Confirmed stale source callbacks cannot mutate selection, count, rows, status, revision, or send eligibility because the guard runs before the action callback.
- Confirmed the source-clean branch affects only `conversation_new`; direct and queued generation payloads retain their source snapshot contract.
- Confirmed document-switch follow behavior is reapplied only after a clean new conversation exists: enabled follow replaces old current-document members, while disabled follow restores the explicit selection through a subsequent guarded workspace update.
- No backend file was changed.
- Live MarginNote WebView timing and visual interaction remain unverified in this static fix round.

## Fix Round 2

### Findings Addressed

- **A:** transient document context keys could reset the active conversation immediately. With `followCurrentDocument=false`, the Web state still showed the explicit set while a transient missing-topic conversation was persisted with empty/default source metadata.
- **B:** the source page could select only already registered candidates and had no one-operation multi-file upload path. The backend accepted UTF-8 text or local paths, but not strict raw-byte payloads from the WebView.

### RED Evidence

Backend tests were added first for:

```text
test_upload_file_accepts_strict_base64_binary_bytes
test_upload_file_base64_rejects_ambiguous_unsafe_or_oversized_payloads
test_upload_file_partial_batch_failure_preserves_successful_binary_upload
test_source_text_artifact_allows_supported_binary_originals_without_utf8_decode
test_automatic_document_conversation_persists_explicit_source_binding
```

Static/UI tests were added first for:

```text
test_automatic_document_switch_waits_for_stable_identity_and_rebinds_sources
test_source_workspace_page_supports_ordered_multi_file_binary_uploads
test_source_workspace_multi_file_upload_status_wraps_at_minimum_width
test_source_workspace_buttons_are_classified_by_real_interaction_type
```

The initial focused run failed at the intended missing boundaries: `fileContentBase64` was rejected as absent input; unsafe/data-URL/oversized cases had no strict classifier; binary originals were routed through UTF-8 handling; debounce/rebinding functions and picker controls were absent; upload status CSS and acceptance classification were absent. The direct backend persistence regression already passed, confirming that a stable automatic `conversation_new` payload containing `sourceIds` and `followCurrentDocument=false` is persisted correctly by the server.

### Automatic Document Switch

- Added a `450 ms` debounce around automatic document switching.
- A switch cannot commit until the latest context contains a topic/notebook ID, book/document ID, and document title or path.
- Transient payloads update the pending key and restart the timer; they do not call `conversation_new` or reset the current conversation.
- Generation is disabled while the switch is pending, committing, rebuilding, or validating.
- The first switch observation snapshots ordered source IDs, follow mode, and current-document member IDs. Repeated transient/full payloads reuse that snapshot.
- The internal automatic `conversation_new` payload carries the preserved source IDs and follow value with an empty revision. User-clicked `新对话` still removes source IDs/revision and defaults follow mode to true.
- After the stable conversation is persisted, the Web layer refreshes candidates, replaces only old current-document members when follow is enabled, saves the source set, and explicitly validates the rebuilt workspace.
- Internal source-page conversation creation is coalesced, preventing the initial source refresh and a fast upload click from creating duplicate empty conversations.
- Manual new/load actions wait while an automatic switch commits so a stale automatic response cannot override the user's conversation choice.

### Multi-File Upload

- Added `添加文件`, a hidden `type=file multiple` input, progress status, and per-file error output to the dedicated source page.
- One picker operation accepts at most `20` files; each file is limited to `20,000,000` decoded bytes.
- Files are read and uploaded sequentially in picker order. Each success is retained independently; a later read/upload failure does not remove earlier uploads.
- Successful upload IDs are resolved against refreshed trusted candidates, auto-selected in original order, saved, and validated.
- The picker accepts PDF, DOCX, PPTX, Markdown/text, JSON/CSV, notebooks, TeX/BibTeX, common source-code formats, and common image formats.
- `register_upload()` now accepts `fileContentBase64`, rejects data URLs, uses strict base64 validation, rejects path separators/NUL in binary-upload names, checks decoded size, and atomically moves decoded bytes into the upload directory.
- Existing `fileContent` and `filePath` behavior remains available with the existing text/path size boundaries.
- DOCX, PPTX, and common image files remain readable original links in source workspaces rather than being incorrectly forced through UTF-8 decoding. PDFs retain page-aware extraction; text and source files retain UTF-8 validation.
- The upload index retains up to `200` records so one 20-file operation does not evict a smaller existing selected set before workspace rebuild.
- The HTTP binding remains unchanged at localhost `127.0.0.1`.

### GREEN Evidence

Focused lifecycle/backend/UI run:

```text
Ran 10 tests in 0.839s
OK
```

Complete backend controls:

```text
python3 -m unittest tests.test_companion_controls -q
Ran 268 tests in 192.850s
OK
```

Final static/UI/acceptance run:

```text
python3 -m unittest \
  tests.test_web_controls_static \
  tests.test_resizable_panel_static \
  tests.test_ui_functional_acceptance -q
Ran 152 tests in 1.047s
OK
```

Final repository-wide run after all code changes:

```text
python3 -m unittest discover -s tests -q
Ran 734 tests in 264.772s
OK
```

Additional checks:

```text
node --check extension/codex.mn.assistant/web/app.js
exit 0

git diff --check
exit 0
```

### Self-Review and Concerns

- Confirmed automatic creation is the only `conversation_new` path allowed to retain source metadata; manual creation remains source-clean.
- Confirmed a missing-topic transient context cannot dispatch automatic conversation creation.
- Confirmed successful binary uploads survive partial batch failure and no failure path deletes prior upload records or files.
- Confirmed raw bytes are never inserted into chat history or ordinary diagnostics.
- Confirmed the new picker button is classified as a file-picker control by UI functional acceptance.
- Live MarginNote WebView timing, native picker interaction, and real 20 MB transfers were not exercised in this implementation run.
