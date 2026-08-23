# Multi-File Source Workspace Design

Date: 2026-08-23
Target release: next Codex Companion release after 0.4.52
Status: approved in chat, pending written-spec review

## 1. Objective

Codex Companion must let a user select multiple files and make all selected files available to one Codex CLI execution. The implementation must not reduce the request to independent per-file model calls, silently omit files, concatenate an unbounded amount of text into the prompt, or mutate the original files.

The primary user-visible result is a session-scoped `资料` control in the chat header. It shows the selected source count, opens a dedicated source picker, and makes the selected source set part of the conversation state.

## 2. Product Semantics

### 2.1 One model call

One user send produces one Codex CLI `exec` invocation. The invocation starts with a managed source workspace as its working directory. Codex reads the files listed in `SOURCES.md` during that invocation and produces one response.

This mode is distinct from cross-document retrieval and map-reduce summarization. Those may remain separate future capabilities, but they do not satisfy this feature.

### 2.2 Source set and active MarginNote document

The active MarginNote document remains the current interaction anchor. It controls selection context, current node context, conversation auto-switching, and the default source suggestion. The source set is an explicit list that may include the active document and additional files.

Changing the active MarginNote document does not silently replace an explicitly selected source set. The source picker offers a `跟随当前文件` setting:

- Enabled: the current MarginNote document is automatically present in the source set and updates when the open document changes.
- Disabled: the selected source set remains unchanged until the user edits it.

The initial value is enabled with only the current document selected.

### 2.3 Read sources versus write target

The source set and MarginNote write target are independent:

- Chat, explanation, comparison, full reading, and mind-map generation may read every selected source.
- Card or mind-map writes still require one explicit current MarginNote notebook and one validated target.
- Selecting several source files never authorizes writing to several notebooks or choosing a mind map implicitly.

## 3. Managed Workspace

### 3.1 Location and identity

Each conversation owns one workspace:

```text
control/source-workspaces/<conversation-id>/
```

The conversation ID is sanitized before it becomes a directory name. If no conversation exists yet, the Web panel creates one before the first multi-file request.

Each workspace contains:

```text
SOURCES.md
manifest.json
files/
text/
```

- `files/` contains symlinks to selected original files or stable Companion cache files.
- `text/` contains symlinks to Companion-managed extracted-text artifacts when the original format is not reliably readable by Codex CLI.
- `manifest.json` is machine-readable state.
- `SOURCES.md` is the model-facing ordered source contract.

### 3.2 Link names

Links use deterministic, collision-resistant names:

```text
001--paper-title--a1b2c3d4.pdf
002--notes--e5f60718.md
```

The suffix is derived from the canonical source identity, not from the original path alone. Names are ASCII-safe where possible and never contain parent-directory traversal.

### 3.3 Supported source kinds

The first implementation supports:

- Current MarginNote PDF or its Companion cache.
- Other documents reported by the current MarginNote notebook when a resolvable path or cache exists.
- Files already uploaded to Companion.
- Files explicitly selected from the local filesystem.
- Files found through configured search roots after explicit user selection.

Supported extensions for direct links are PDF, Markdown, plain text, JSON, CSV, source code, DOCX, PPTX, and common image formats. A source is selectable only if it is a regular readable file or a verified Companion cache artifact.

Directories are not accepted in the first release. The user selects files, not arbitrary directory trees.

### 3.4 PDF and binary formats

A symlink to the original file is always retained when readable. For PDF, DOCX, and PPTX, the workspace also exposes a Companion-managed UTF-8 text representation when extraction succeeds. The model-facing manifest tells Codex to prefer the extracted text for semantic reading and use the original file only when it needs figures, layout, or metadata.

PDF extraction reuses the existing page-aware cache. The text representation preserves source boundaries and page markers. It must not claim to be complete when extraction was truncated or failed.

### 3.5 Atomic rebuild

Workspace updates use a staging directory followed by atomic replacement of the managed directory. A failed rebuild leaves the previous valid workspace untouched. Rebuilding or deleting a workspace may remove only Companion-created links, manifests, and extracted artifacts. It must never unlink, move, edit, or delete a source target.

## 4. Source Manifest

`manifest.json` uses a versioned schema:

```json
{
  "schema": "codex.mn.sourceWorkspace.v1",
  "conversationId": "...",
  "followCurrentDocument": true,
  "updatedAt": "...",
  "sources": [
    {
      "sourceId": "...",
      "displayName": "...",
      "kind": "marginnote_pdf",
      "originalPath": "...",
      "fileLink": "files/001--...pdf",
      "textLink": "text/001--...txt",
      "sha256": "...",
      "readable": true,
      "textReadable": true,
      "pageCount": 18,
      "truncated": false,
      "error": ""
    }
  ]
}
```

`SOURCES.md` lists every source in the same order and contains these instructions:

1. Inspect every listed source before answering.
2. Prefer `text/` for extracted semantic content and `files/` for originals.
3. State which sources were successfully read.
4. Explicitly list unreadable or unsupported sources.
5. Cite the display name and page number or local section when making source-specific claims.
6. Do not modify any file.

Absolute original paths remain in the local manifest for diagnostics but are not copied into chat history or diagnostic logs unless sanitized.

## 5. Companion API and State

### 5.1 New actions

The Companion exposes read-only source-workspace actions:

- `source_workspace_get`
- `source_workspace_update`
- `source_workspace_validate`
- `source_workspace_clear`

`source_workspace_update` accepts source IDs selected from trusted registries. An explicit local file selected by the native file picker may provide a path, but arbitrary paths from model output or queued prompts are rejected.

### 5.2 Conversation persistence

Conversation metadata stores:

- Ordered selected source IDs.
- `followCurrentDocument`.
- Last validation status.
- Workspace schema version.

History stores source identities and display names, not file contents. Loading a conversation restores the source set and rebuilds the workspace after validating that targets still exist.

### 5.3 Queue binding

Every queued generation request carries:

- `conversationId`.
- `sourceWorkspaceRevision`.
- Ordered source IDs.
- Existing `contextDocumentKey`.

Before execution, Companion verifies that the queued revision matches the current workspace. A changed or missing source set blocks the queued request instead of running it against different files.

## 6. Codex CLI Execution

### 6.1 Working directory

For a validated non-empty multi-file source set, `call_codex_cli()` uses the conversation workspace as `cwd`. Single-document requests without an explicit multi-file selection keep the existing project working directory to avoid changing current behavior.

The CLI remains in `--sandbox read-only`. The system prompt permits read-only inspection of the workspace and explicitly forbids mutation, patching, file creation, network side effects, or commands unrelated to reading selected sources.

### 6.2 Prompt contract

The prompt contains a compact workspace contract rather than the concatenated full text:

```text
资料工作区：<workspace path>
先读取 SOURCES.md，并检查其中列出的全部 N 个文件。
本次回答必须报告成功读取和未读取的文件；不得把未读取文件当作已使用。
```

The user prompt, selected MarginNote text, active node context, task instructions, and write-target safety contract remain in the model input.

### 6.3 Backend behavior

Multi-file workspace mode requires Codex CLI because the OpenAI API cannot access local symlinks. When the source set contains more than one file:

- `codex_cli`: run normally.
- `auto`: require an available Codex CLI and do not fall back to OpenAI API for this request.
- `openai`: block before generation and explain that local workspace sources require Codex CLI.

This rule prevents a fallback response from silently ignoring the selected files.

## 7. User Interface

### 7.1 Chat header

Add one compact control near the context indicator:

```text
资料 3
```

Its states are:

- Neutral: no explicit source set.
- Green: all selected sources are readable.
- Yellow: validation or text extraction is in progress.
- Red: one or more sources are missing or unreadable.

### 7.2 Source picker page

The picker is a dedicated page, consistent with History and Settings, with `返回对话` at the top. It contains:

- Current document section.
- Current notebook files.
- Uploaded files.
- Explicitly selected local files.
- Search-root matches only after user search.
- `跟随当前文件` toggle.
- Per-source checkbox, type, size, read state, text extraction state, and remove action.
- `全部取消`, `验证资料`, and `完成` commands.

The picker does not expose internal hashes or absolute paths in the ordinary view. Diagnostics may show them in an expandable technical section.

### 7.3 Composer and response state

The composer remains usable while sources validate. Sending is blocked only when the selected set is invalid. Before a request starts, the conversation displays one compact material line such as:

```text
本次资料：3 个文件，均可读
```

The assistant response footer shows `已读取 3/3 个文件`. If Codex reports a source as unreadable, the result is visibly marked incomplete and does not offer write actions that imply complete coverage.

## 8. Failure Handling

The request is blocked before model invocation when:

- No selected source can be resolved.
- A symlink target disappeared.
- Workspace revision does not match the queued request.
- More than one source is selected and Codex CLI is unavailable.
- The configured backend is OpenAI-only.
- Workspace creation or validation fails.

A request may continue with a subset only after the user removes failed sources. The plugin never silently drops a source.

Codex runtime output is treated as incomplete when it does not acknowledge every `sourceId` from `SOURCES.md`. The UI reports the missing acknowledgements. The first release does not automatically rerun the model.

## 9. Security and Privacy

- Only user-selected files or verified current MarginNote sources enter a workspace.
- No recursive directory linking.
- Symlink targets are canonicalized and verified before creation.
- Workspace links are read-only from the model's sandbox perspective.
- Source contents are not copied into conversation history or ordinary logs.
- Sensitive path fields use the existing diagnostic sanitizer.
- Clearing a conversation removes only its managed workspace.
- A periodic cleanup removes orphaned workspaces whose conversations no longer exist, without following links.

## 10. Compatibility and Migration

Existing single-document conversations continue unchanged. Their current PDF cache, `contextDocumentKey`, document-follow behavior, queue isolation, and mind-map write checks remain authoritative.

The source workspace augments, rather than replaces, Source Registry. Source Registry discovers and validates candidates; the source picker creates an explicit ordered set from those candidates.

No existing conversation is migrated into multi-file mode automatically.

## 11. Testing and Acceptance

### 11.1 Unit tests

- Deterministic workspace naming and source ordering.
- Symlink creation without source mutation.
- Atomic rebuild preserves the previous workspace after failure.
- Duplicate filenames remain distinct.
- Missing, unreadable, and broken-link sources block generation.
- Conversation save/load restores source IDs and follow-current behavior.
- Queue revision mismatch blocks execution.
- Multi-file requests use workspace `cwd` and exactly one Codex CLI invocation.
- OpenAI-only and unavailable-CLI configurations fail before generation.
- Single-document behavior remains unchanged.

### 11.2 Static UI tests

- Header source-count control exists and fits the minimum panel width.
- Source picker has a return action, checkboxes, status states, and responsive rows.
- Long filenames wrap or truncate with a tooltip and never push controls outside the panel.
- Send availability follows source validation state.

### 11.3 Live acceptance

Using one MarginNote notebook with at least three documents:

1. Select three files, including the current PDF.
2. Verify the workspace has three file links, a manifest, and extracted PDF text links where available.
3. Ask one comparison question.
4. Confirm one Codex CLI process runs with the workspace as `cwd`.
5. Confirm the answer acknowledges all three files and identifies source-specific claims.
6. Switch the active MarginNote document and verify the explicit set remains stable when follow-current is disabled.
7. Remove one source and verify the next request sees only two.
8. Break one source link and verify sending is blocked before model invocation.
9. Generate a mind map from all three sources and verify writing still targets only the explicitly selected current mind map.
10. Clear the conversation and verify original files remain untouched.

## 12. Non-Goals

- Recursive ingestion of arbitrary folders.
- Automatic semantic retrieval across every notebook file.
- Multi-call map-reduce synthesis.
- OpenAI API Files or vector-store upload.
- Writing one generated result into several notebooks at once.
- Editing, renaming, moving, or deleting selected source files.
