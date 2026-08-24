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

This report was the only additional file in the initial Task 5 implementation. Fix Rounds 2 and 3 later expanded the approved scope to `companion.py`, backend tests, and HTTP/upload behavior as documented below.

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
- The initial Task 5 implementation did not modify backend contracts; Fix Rounds 2 and 3 below intentionally add the approved upload and HTTP safety changes.

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
- Fix Round 1 itself did not change backend files; Fix Round 2 subsequently changed `companion.py` under the expanded approved write set.
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

## Fix Round 3

### Findings Addressed

- **C1:** cross-document response suppression could hide an automatic `conversation_new` result before cleanup, orphan the persisted conversation, and strand migration flags.
- **I1:** queued goal/write/text execution and queue drain did not share the migration gate.
- **I2:** a document or conversation switch could suppress upload completion and leave upload controls/generation disabled.
- **I3:** the HTTP handler read the declared request body before enforcing any encoded upload ceiling.
- **I4:** strict decoding still accepted noncanonical padded base64 such as `Zh==` and `AB==`.
- **I5:** previous lifecycle tests checked source markers but did not execute asynchronous epoch/interleaving behavior.
- **M1:** earlier report wording said no backend file changed without limiting that statement to the initial implementation/fix round.

### RED Evidence

Added backend RED tests for:

```text
test_json_post_body_limit_rejects_before_reading_request_bytes
test_json_post_body_requires_valid_length_and_rejects_chunked_encoding
```

Extended the strict upload rejection test with noncanonical `Zh==` and `AB==` cases. Before implementation, both payloads were stored successfully, the HTTP pre-read helper was absent, and the lifecycle helper/static wiring test failed.

Added `tests/source_workspace_lifecycle.test.js` before the helper implementation. Its initial Node run failed because `source_workspace_lifecycle.js` did not exist.

### Executable Lifecycle Helper

- Added `source_workspace_lifecycle.js`, loaded before `app.js` and exported for both the WebView and Node.
- Migration and upload handles carry monotonically increasing epochs. `finish*()` succeeds only for the active handle, so an older callback cannot unlock a newer lifecycle.
- The helper exposes pending/in-flight migration state, upload cancellation state, and one central generation-blocked predicate.
- Executable Node tests cover:
  - migration superseded before its conversation callback;
  - exact stale-conversation cleanup ownership payload;
  - upload cancellation after one successful file;
  - an older upload callback failing to unlock a newer upload;
  - generation remaining blocked for the complete migration lifecycle.

### Migration and Cleanup

- `postCompanion()` now parses a cross-document response and sends it to an explicit stale-response callback before returning.
- Every stale `conversation_new` result with a persisted conversation is deleted through a raw exact-payload request. The cleanup payload retains the original topic, book, context key, document/object ownership, conversation ID, and session ID rather than inheriting current context.
- A migration handle records the newly persisted conversation and original request payload. Superseding or canceling that handle triggers cleanup immediately; a later stale callback is idempotently ignored for the same conversation ID.
- Pending, in-flight, canceled, superseded, failed, and completed migration states synchronize UI booleans only from the active helper handle.
- Cancellation restores the original conversation and source-workspace snapshot if that state was already cleared before the user returned to the original document.
- Source-page operations are closed/blocked during migration unless they carry the active internal migration handle, preventing an unrelated refresh from suppressing an internal rebuild callback.

### Central Generation Gate

- Direct generation continues through the common source/lifecycle availability check.
- `runQueuedCommand()`, `drainNextQueuedAction()`, and the text/goal/draft request entry points now check the same migration predicate.
- A blocked queued command is neither acknowledged nor executed. One bounded defer timer retries queue drain after migration instead of accumulating repeated callbacks.
- Chat, goal, card, mind-map, full-reading, node expansion/reorganization, and reply-derived write paths therefore cannot execute against the old source binding while migration is active.

### Upload Cancellation

- Upload remains active through candidate refresh, auto-selection, source save, and validation, not only through byte transfer.
- Document switch, new conversation, and conversation load explicitly cancel the active upload handle, release the file-picker button, preserve server-side successes, and tell the user to reselect unfinished files.
- Every FileReader, upload response, refresh, save, and validation continuation checks the active upload epoch before mutating UI or source state.
- An older upload completion cannot release controls owned by a newer upload lifecycle.

### HTTP and Base64 Safety

- Added a JSON POST ceiling sized for one canonical 20 MB binary upload plus bounded JSON/context overhead.
- `do_POST()` now rejects missing, invalid, nonpositive, transfer-encoded/chunked, or oversized `Content-Length` before `rfile.read()`.
- It also rejects short reads before JSON parsing.
- After `b64decode(..., validate=True)`, the backend re-encodes decoded bytes with standard `b64encode()` and requires exact string equality. Noncanonical padding and alternate representations are rejected before file creation.
- Decoded file bytes remain limited to 20 MB; data URLs and unsafe names remain rejected.

### GREEN Evidence

Focused backend safety tests:

```text
Ran 6 tests in 0.707s
OK
```

Executable Node interleavings:

```text
node --test tests/source_workspace_lifecycle.test.js
5 tests passed
```

Complete backend controls:

```text
python3 -m unittest tests.test_companion_controls -q
Ran 270 tests in 186.079s
OK
```

Changed Web/UI modules:

```text
python3 -m unittest \
  tests.test_web_controls_static \
  tests.test_resizable_panel_static \
  tests.test_ui_functional_acceptance -q
Ran 153 tests in 0.696s
OK
```

Final repository-wide Python suite:

```text
python3 -m unittest discover -s tests -q
Ran 737 tests in 193.078s
OK
```

Additional checks:

```text
node --check extension/codex.mn.assistant/web/app.js
node --check extension/codex.mn.assistant/web/source_workspace_lifecycle.js
git diff --check
```

All returned exit `0`.

### Concerns

- The executable helper tests cover lifecycle interleavings deterministically, but a live MarginNote WebView switch/upload run was not available in this fix round.
- Stale conversation cleanup is best-effort over the localhost Companion endpoint; cleanup failure is surfaced in panel status and no stale callback can unlock the active newer lifecycle.
