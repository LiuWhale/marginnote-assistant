# Multi-File Source Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let one Codex CLI execution read every file explicitly selected for a conversation through a managed, read-only, symlink-based source workspace.

**Architecture:** Add a focused `source_workspace.py` module that owns workspace manifests, atomic symlink trees, validation, revisions, and cleanup. `companion.py` resolves Source Registry candidates and extracted-text artifacts, persists the source selection with conversations and queued requests, and runs Codex CLI with the validated workspace as `cwd`; the Web panel adds a dedicated multi-file picker and source-count status without changing single-document behavior.

**Tech Stack:** Python 3 standard library, existing PyMuPDF extraction path, Codex CLI `exec --sandbox read-only`, MarginNote 4 JavaScript WebView, HTML/CSS, Python `unittest` static and behavioral tests.

**Spec:** `docs/superpowers/specs/2026-08-23-multi-file-source-workspace-design.md`

## Global Constraints

- One send with multiple selected files must produce exactly one Codex CLI `exec` invocation.
- Multi-file mode must never silently drop, truncate, replace, or mutate a selected source.
- Workspaces live under `control/source-workspaces/<conversation-id>/` and contain only Companion-managed links, manifests, and extracted-text links.
- Every original file remains outside workspace ownership; cleanup must not follow symlinks or delete targets.
- Multi-file mode requires Codex CLI. `auto` must not fall back to OpenAI API, and `openai_api` must fail before generation.
- Source set and MarginNote write target remain independent; multi-file reading never authorizes multi-notebook writing.
- Existing single-document conversations, PDF caching, queue isolation, and mind-map validation must retain their current behavior.
- New UI must fit the existing minimum panel size of 390 x 520 without horizontal overflow.

---

### Task 1: Managed Source Workspace Core

**Files:**
- Create: `source_workspace.py`
- Create: `tests/test_source_workspace.py`

**Interfaces:**
- Consumes: `Path` source descriptors with `id`, `title`, `kind`, `path`, and optional `textPath`, `sha256`, `pageCount`, `truncated`.
- Produces: `configure(root: Path | str) -> None`, `build_workspace(conversation_id: str, sources: list[dict], follow_current_document: bool) -> dict`, `load_workspace(conversation_id: str) -> dict`, `validate_workspace(conversation_id: str, expected_revision: str = "") -> dict`, `clear_workspace(conversation_id: str) -> dict`, and `workspace_path(conversation_id: str) -> Path`.

- [ ] **Step 1: Write failing tests for deterministic, safe workspace construction**

```python
def test_build_workspace_creates_ordered_links_and_manifest(self):
    first = self.root / "Paper A.pdf"
    second = self.root / "Paper A copy.pdf"
    first.write_bytes(b"a")
    second.write_bytes(b"b")
    result = source_workspace.build_workspace(
        "CONV-1",
        [
            {"id": "src-a", "title": "Paper A", "kind": "pdf", "path": str(first)},
            {"id": "src-b", "title": "Paper A", "kind": "pdf", "path": str(second)},
        ],
        False,
    )
    self.assertTrue(result["ok"])
    self.assertEqual(result["sourceCount"], 2)
    self.assertNotEqual(result["sources"][0]["fileLink"], result["sources"][1]["fileLink"])
    self.assertTrue((Path(result["workspacePath"]) / "SOURCES.md").exists())
    self.assertTrue((Path(result["workspacePath"]) / "files" / result["sources"][0]["fileLinkName"]).is_symlink())
```

Also add tests for invalid conversation IDs, missing sources, duplicate source IDs, optional text links, stable source order, and `clear_workspace()` preserving target files.

- [ ] **Step 2: Run the new test module and verify RED**

Run: `python3 -m unittest tests.test_source_workspace -v`

Expected: FAIL because `source_workspace.py` does not exist.

- [ ] **Step 3: Implement the versioned manifest and safe path helpers**

```python
SOURCE_WORKSPACE_SCHEMA = "codex.mn.sourceWorkspace.v1"

def safe_conversation_id(value: object) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return text[:120]

def workspace_path(conversation_id: str) -> Path:
    safe_id = safe_conversation_id(conversation_id)
    if not safe_id:
        raise ValueError("missing valid conversationId")
    return SOURCE_WORKSPACES_DIR / safe_id
```

Use canonical source paths only for validation. Generate link names from ordered position, sanitized display name, and the first eight characters of a SHA-256 over `sourceId|canonicalPath`.

- [ ] **Step 4: Implement atomic workspace build, validation, and cleanup**

Build into `control/source-workspaces/.staging-<uuid>`, create `files/`, `text/`, `manifest.json`, and `SOURCES.md`, then replace the previous managed directory. Compute `revision` from the normalized ordered source records plus `followCurrentDocument`. Validation must use `lstat()` for links, verify each resolved target is a regular readable file, and return all failures without deleting the workspace.

Cleanup must iterate only workspace-owned entries and call `unlink()` on symlinks before removing directories; it must never call `resolve().unlink()`.

- [ ] **Step 5: Run core tests and verify GREEN**

Run: `python3 -m unittest tests.test_source_workspace -v`

Expected: all source-workspace tests PASS.

- [ ] **Step 6: Commit the core module**

```bash
git add source_workspace.py tests/test_source_workspace.py
git commit -m "Add managed multi-file source workspaces"
```

---

### Task 2: Stable Source Candidates and Extracted Text Links

**Files:**
- Modify: `source_registry.py:35-170`
- Modify: `companion.py:80-160, 2100-2260, 12140-12540`
- Modify: `tests/test_source_registry.py`
- Modify: `tests/test_companion_controls.py`

**Interfaces:**
- Consumes: existing Source Registry caches, uploads, explicit paths, MarginNote `availableDocuments`, and PDF text-cache records.
- Produces: stable source IDs from `source_registry.stable_source_id(kind: str, identity: str) -> str`, `source_workspace_candidates(payload: dict) -> dict`, and `source_text_artifact(source: dict) -> dict` in `companion.py`.

- [ ] **Step 1: Add failing tests for stable IDs and candidate resolution**

```python
def test_registry_source_id_is_stable_when_list_order_changes(self):
    first = source_registry.build_registry({}, explicit_paths=[self.path_a, self.path_b])
    second = source_registry.build_registry({}, explicit_paths=[self.path_b, self.path_a])
    by_path_first = {item["path"]: item["id"] for item in first["sources"] if item.get("path")}
    by_path_second = {item["path"]: item["id"] for item in second["sources"] if item.get("path")}
    self.assertEqual(by_path_first, by_path_second)
```

Add Companion tests proving that uploaded files, current cached PDF, explicit paths, and selected `availableDocuments` become candidates only when a readable path or cache can be proven.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python3 -m unittest tests.test_source_registry tests.test_companion_controls.CompanionControlsTests.test_source_workspace_candidates_include_only_resolvable_files -v`

Expected: FAIL because stable IDs and candidate APIs are absent.

- [ ] **Step 3: Replace index-based Source Registry IDs with stable IDs**

```python
def stable_source_id(kind: str, identity: str) -> str:
    digest = hashlib.sha256(f"{kind}|{identity}".encode("utf-8")).hexdigest()[:20]
    return f"{kind}:{digest}"
```

Use canonical paths for file-backed sources and `topicid|bookmd5|documentTitle` for MarginNote metadata sources. Preserve the existing registry schema and action plan.

- [ ] **Step 4: Add candidate aggregation in Companion**

Configure `source_workspace` next to the other focused modules. Implement `source_workspace_candidates()` by reusing the same cache index, `uploaded_files()`, configured search roots, explicit document path, and current MarginNote descriptors used by Source Registry. Return:

```python
{
    "ok": True,
    "schema": "codex.mn.sourceWorkspaceCandidates.v1",
    "sources": sources,
    "sourceCount": len(sources),
}
```

Do not expose a root directory as a selectable source. Search roots may yield files only after an explicit filename/search result selection.

- [ ] **Step 5: Reuse PDF extraction for model-readable text artifacts**

Implement `source_text_artifact()` so PDFs call `ensure_pdf_text_cache()` with source-specific `pdfPath`, `bookmd5`, and title. Materialize one Companion-owned UTF-8 file under `control/source-text/<source-id>-<source-sha>.txt`, preserving `[第N页]` markers and the existing truncation statement. Return `textPath`, `pageCount`, `truncated`, and `error`; non-PDF UTF-8 text sources use the original file without creating a second artifact.

- [ ] **Step 6: Run registry and extraction tests**

Run: `python3 -m unittest tests.test_source_registry tests.test_companion_controls -q`

Expected: PASS.

- [ ] **Step 7: Commit source resolution**

```bash
git add source_registry.py companion.py tests/test_source_registry.py tests/test_companion_controls.py
git commit -m "Resolve stable multi-file source candidates"
```

---

### Task 3: Source Workspace API, Conversation Persistence, and Queue Revision Binding

**Files:**
- Modify: `companion.py:220-315, 3060-3260, 6980-7235, 14080-14350`
- Modify: `tests/test_companion_controls.py`

**Interfaces:**
- Consumes: Task 1 workspace APIs and Task 2 candidate descriptors.
- Produces: Companion actions `source_workspace_get`, `source_workspace_update`, `source_workspace_validate`, `source_workspace_clear`; conversation fields `sourceIds`, `followCurrentDocument`, `sourceWorkspaceRevision`; queue command fields with the same names.

- [ ] **Step 1: Add failing API tests**

```python
def test_source_workspace_update_persists_selection_and_returns_revision(self):
    result = companion.handle_action({
        "action": "source_workspace_update",
        "conversationId": "CONV-1",
        "sourceIds": ["upload:one", "upload:two"],
        "followCurrentDocument": False,
    })
    self.assertTrue(result["ok"], result)
    self.assertEqual(result["workspace"]["sourceCount"], 2)
    self.assertTrue(result["workspace"]["revision"])
```

Add tests for unknown source IDs, broken sources, clear behavior, conversation save/load, delete cleanup, and queue revision mismatch.

- [ ] **Step 2: Run API tests and verify RED**

Run: `python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_source_workspace_update_persists_selection_and_returns_revision -v`

Expected: FAIL with unknown action.

- [ ] **Step 3: Implement read-only Companion actions**

Add all four actions to `READ_ONLY_ACTIONS` and dispatch them before generation. `source_workspace_update` must resolve requested IDs against a fresh trusted candidate list, reject unknown IDs, prepare text artifacts, build the workspace, and return candidates plus workspace status. `source_workspace_clear` removes only the managed workspace and updates conversation metadata.

- [ ] **Step 4: Persist source metadata with conversation state**

Extend `read_conversation_file()`, `conversation_summary()`, `conversation_payload_for_new()`, and `save_history()` with:

```python
"sourceIds": unique_string_list(data.get("sourceIds")),
"followCurrentDocument": bool(data.get("followCurrentDocument", True)),
"sourceWorkspaceRevision": str(data.get("sourceWorkspaceRevision") or ""),
```

Loading a conversation validates or rebuilds its workspace and returns the resulting status. Deleting a conversation calls `source_workspace.clear_workspace(conversationId)` after ownership validation.

- [ ] **Step 5: Bind queued work to a source revision**

Include source metadata in queue records and raw queued generation commands. Before dispatching a queued generation, compare `sourceWorkspaceRevision` with `validate_workspace()`. Return an explicit source-workspace mismatch error and acknowledge no write command when revisions differ.

- [ ] **Step 6: Run conversation and queue regression tests**

Run: `python3 -m unittest tests.test_companion_controls -q`

Expected: PASS, including existing cross-document queue isolation tests.

- [ ] **Step 7: Commit API and persistence**

```bash
git add companion.py tests/test_companion_controls.py
git commit -m "Persist conversation source workspaces"
```

---

### Task 4: One-Shot Codex CLI Workspace Execution

**Files:**
- Modify: `companion.py:12490-12860`
- Modify: `tests/test_companion_controls.py`

**Interfaces:**
- Consumes: validated workspace status with `workspacePath`, `revision`, `sourceCount`, and `sources`.
- Produces: `generation_source_workspace(payload: dict) -> dict`, workspace-aware `build_model_input()`, and a single `subprocess.Popen` in `call_codex_cli()` with workspace `cwd`.

- [ ] **Step 1: Add failing one-call and backend-boundary tests**

```python
def test_multi_file_cli_uses_workspace_cwd_and_one_process(self):
    calls = []
    companion.subprocess.Popen = lambda command, **kwargs: calls.append((command, kwargs)) or FakeProcess("ok")
    text, backend = companion.call_codex_cli({
        "prompt": "比较这些文件",
        "conversationId": "CONV-1",
        "sourceIds": ["src-a", "src-b"],
        "sourceWorkspaceRevision": "REV-1",
    }, "chat")
    self.assertEqual(backend, "codex-cli")
    self.assertEqual(len(calls), 1)
    self.assertEqual(Path(calls[0][1]["cwd"]), companion.source_workspace.workspace_path("CONV-1"))
```

Add tests proving `auto` does not fall back after a multi-file CLI failure, `openai_api` blocks before API invocation, missing source acknowledgements mark the response incomplete, and single-document CLI calls keep `cwd=ROOT`.

- [ ] **Step 2: Run focused CLI tests and verify RED**

Run: `python3 -m unittest tests.test_companion_controls.CompanionControlsTests.test_multi_file_cli_uses_workspace_cwd_and_one_process -v`

Expected: FAIL because current `cwd` is always `ROOT`.

- [ ] **Step 3: Add generation workspace validation**

```python
def generation_source_workspace(payload: dict[str, Any]) -> dict[str, Any]:
    source_ids = unique_string_list(payload.get("sourceIds"))
    if len(source_ids) <= 1:
        return {"active": False, "ok": True, "sourceCount": len(source_ids)}
    status = source_workspace.validate_workspace(
        normalize_conversation_id(payload),
        str(payload.get("sourceWorkspaceRevision") or ""),
    )
    return {"active": True, **status}
```

Block generation if validation fails or any source is unreadable.

- [ ] **Step 4: Build a compact workspace prompt instead of concatenating full texts**

When the workspace is active, skip `document_context_for_model()` and append:

```text
资料工作区：<workspacePath>
本次共有 N 个文件。先完整读取 SOURCES.md，再检查其中列出的每个 files/ 或 text/ 条目。
回答末尾必须按清单中的实际 ID 输出，例如：资料读取：pdf:a1b2c3=read; upload:d4e5f6=unread
不得把 unread 文件作为结论依据。
```

Keep selection text, current node context, task description, and write-target safety fields.

- [ ] **Step 5: Run Codex CLI in the workspace and enforce backend behavior**

Set `cwd=str(workspacePath)` only for validated multi-file requests. Keep `--sandbox read-only`. Amend the system prompt to permit read-only inspection commands inside the workspace while forbidding file mutation, patching, external side effects, and unrelated filesystem access.

In `generate_reply()`, when `sourceCount > 1`, require CLI and return a specific `multi-file-workspace-cli-required` error without calling OpenAI API.

- [ ] **Step 6: Parse source acknowledgement status**

Parse the final `资料读取：` line against the manifest source IDs. Return `sourceUsage` with read, unread, and missing IDs. Missing or unread sources set `complete=False`; the Web layer must not expose answer-derived write buttons for incomplete multi-file responses.

- [ ] **Step 7: Run model-input and backend tests**

Run: `python3 -m unittest tests.test_companion_controls -q`

Expected: PASS.

- [ ] **Step 8: Commit CLI execution behavior**

```bash
git add companion.py tests/test_companion_controls.py
git commit -m "Run one Codex call over selected sources"
```

---

### Task 5: Multi-File Source Picker UI

**Files:**
- Modify: `extension/codex.mn.assistant/web/index.html:45-60, 760-805`
- Modify: `extension/codex.mn.assistant/web/app.js:1-120, 1900-2130, 10480-10940`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Modify: `tests/test_web_controls_static.py`
- Modify: `tests/test_resizable_panel_static.py`

**Interfaces:**
- Consumes: Companion source-workspace actions and response `sourceUsage`.
- Produces: `state.sourceWorkspace`, `state.sourceWorkspaceCandidates`, `openSourceWorkspacePage()`, `renderSourceWorkspacePage()`, `saveSourceWorkspaceSelection()`, and payload fields on every generation request.

- [ ] **Step 1: Add failing static UI tests**

```python
def test_chat_header_has_multi_file_source_control_and_page(self):
    self.assertIn('id="sourceWorkspaceButton"', self.html)
    self.assertIn('id="sourceWorkspacePage"', self.html)
    self.assertIn('id="sourceWorkspaceBackButton"', self.html)
    self.assertIn("source_workspace_update", self.js)
    self.assertIn("followCurrentDocument", self.js)
```

Add responsive assertions for `.source-workspace-row`, long filename wrapping, equal-height command buttons, and no fixed width above the 390px panel minimum.

- [ ] **Step 2: Run static tests and verify RED**

Run: `python3 -m unittest tests.test_web_controls_static tests.test_resizable_panel_static -v`

Expected: FAIL because controls are absent.

- [ ] **Step 3: Add the compact header control and dedicated page**

Add `资料` beside `历史`, with count in a nested span. Add a `config-page hidden` source picker modeled on the History page, including current document, notebook documents, uploads, local selections, follow-current checkbox, validation status, `全部取消`, `验证资料`, `完成`, and `返回对话`.

- [ ] **Step 4: Add Web state and API rendering**

Initialize:

```javascript
sourceWorkspace: {schema: 'codex.mn.sourceWorkspace.v1', sourceCount: 0, sources: [], revision: ''},
sourceWorkspaceCandidates: [],
sourceWorkspaceSelection: {},
followCurrentDocument: true,
```

Render each candidate with a native checkbox, file-type label, size, readable/extraction status, and title tooltip. Do not render absolute paths unless a diagnostics disclosure is expanded.

- [ ] **Step 5: Persist selection and include it in generation payloads**

`saveSourceWorkspaceSelection()` posts ordered checked IDs and `conversationId`. On success, update count/tone and append `sourceIds`, `followCurrentDocument`, and `sourceWorkspaceRevision` in the common payload builder used by direct and queued sends.

When the active document changes and follow-current is enabled, update only the current-document membership; when disabled, preserve the explicit selection.

- [ ] **Step 6: Render request and response material status**

Before sending, show `本次资料：N 个文件，均可读`. After a response, show `已读取 X/N 个文件`. If `sourceUsage.complete` is false, render the unread names in red and suppress `复制` only if no answer exists; always suppress card/mind-map write actions for incomplete coverage.

- [ ] **Step 7: Run UI static suites**

Run: `python3 -m unittest tests.test_web_controls_static tests.test_resizable_panel_static -q`

Expected: PASS.

- [ ] **Step 8: Commit the source picker**

```bash
git add extension/codex.mn.assistant/web/index.html extension/codex.mn.assistant/web/app.js extension/codex.mn.assistant/web/app.css tests/test_web_controls_static.py tests/test_resizable_panel_static.py
git commit -m "Add multi-file source picker"
```

---

### Task 6: Documentation, Versioning, Package, and Live Acceptance

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/USER_MANUAL.md`
- Modify: `docs/RELEASE_CHECKLIST.md`
- Modify: `CHANGELOG.md`
- Modify: version constants in `companion.py`, `doctor.py`, `refresh_mn_runtime.py`, `release_acceptance.py`, `package_release.py`, `extension/codex.mn.assistant/main.js`, and `extension/codex.mn.assistant/mnaddon.json`
- Modify: `tests/test_release_docs.py`

**Interfaces:**
- Consumes: completed backend and Web UI.
- Produces: documented user workflow, next patch version, release artifacts, installed local runtime, and live evidence.

- [ ] **Step 1: Add failing documentation contract tests**

Require both READMEs and the user manual to contain `资料`, `一次 Codex CLI 调用`, `SOURCES.md`, `软链接`, `OpenAI API`, and `不会删除原文件`. Require release checklist coverage for a three-file live test and one broken-link failure.

- [ ] **Step 2: Run documentation tests and verify RED**

Run: `python3 -m unittest tests.test_release_docs -v`

Expected: FAIL until documentation is updated.

- [ ] **Step 3: Update user documentation and Changelog**

Document how to select files, follow the current document, inspect read status, distinguish read sources from the write target, and recover from missing permissions or broken links. State that multi-file workspace mode requires Codex CLI and does not fall back to OpenAI API.

- [ ] **Step 4: Bump all version sources consistently**

Use patch version `0.4.53`, update every current-version constant and command example, and verify `build_pkg.DEFAULT_VERSION` still reads the add-on manifest.

- [ ] **Step 5: Run the complete automated suite**

Run:

```bash
python3 -m unittest discover -s tests -q
python3 -m py_compile companion.py source_workspace.py
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
git diff --check
```

Expected: all tests and syntax checks PASS.

- [ ] **Step 6: Build and smoke-test release artifacts**

```bash
python3 package_release.py 0.4.53
python3 build_pkg.py
python3 release_smoke_test.py release/CodexCompanion-0.4.53-latest-dist.zip --mnaddon release/CodexCompanion-0.4.53-latest.mnaddon --install-dry-run
```

Expected: zip and mnaddon PASS; pkg installer root matches the manifest version. Record that pkg signing/notarization remains a separate credential-dependent gate.

- [ ] **Step 7: Install locally and run live three-file acceptance**

Install the add-on to both MarginNote 4 container paths, restart Companion and MarginNote, select three readable files, and send one comparison request. Verify:

- one Codex process used the source workspace as `cwd`;
- `SOURCES.md` lists all three sources;
- the response acknowledges all three source IDs;
- switching the current document does not alter an explicit set when follow-current is off;
- a broken link blocks before model invocation;
- generated mind-map output still writes only to the selected target.

- [ ] **Step 8: Commit the release-ready implementation**

```bash
git add README.md README.zh-CN.md docs/USER_MANUAL.md docs/RELEASE_CHECKLIST.md CHANGELOG.md companion.py doctor.py refresh_mn_runtime.py release_acceptance.py package_release.py extension/codex.mn.assistant/main.js extension/codex.mn.assistant/mnaddon.json tests/test_release_docs.py
git commit -m "Document multi-file source workspaces"
```

Do not push or create a GitHub Release unless the user explicitly requests release after reviewing the completed implementation.

---

## Approved Repair Cycle — 2026-08-24

The user explicitly approved continuing after the final re-review and added one bounded requirement: the source picker must support selecting multiple entries or all entries and removing them from the current conversation workspace without deleting original files or upload records.

### Task 7: Keep The Install Token On Loopback

**Files:**
- Modify: `send_action.py`
- Modify: `refresh_mn_runtime.py`
- Modify: `release_acceptance.py`
- Modify: `tests/test_send_action.py`
- Modify: `tests/test_refresh_mn_runtime.py`
- Modify: `tests/test_release_acceptance.py`

**Interfaces:**
- Produces: `is_local_companion_url(url: str) -> bool` or an equivalent shared predicate.
- Rule: the install token is attached only to `http://127.0.0.1:48761`, `http://localhost:48761`, or `http://[::1]:48761`. Any custom URL receives no implicit token.

- [ ] Write failing tests showing exact loopback URLs receive the token and HTTPS, remote hosts, alternate ports, userinfo, redirects, and deceptive hostnames do not.
- [ ] Run focused tests and verify RED.
- [ ] Implement one canonical URL predicate and apply it before reading or attaching the token in all three clients. Redirect handling must not forward the token to a changed origin.
- [ ] Run focused tests and verify GREEN.
- [ ] Commit with message `fix: keep companion token on loopback`.

### Task 8: Prevent Deleted Sessions From Returning

**Files:**
- Modify: `companion.py`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `tests/test_companion_controls.py`
- Modify: `tests/test_web_controls_static.py`

**Interfaces:**
- Produces: persisted `sessionEpoch`, payload/queue binding for that epoch, and ownership-proven tombstones for deleted sessions.
- Rule: new conversations receive a random epoch; append/source/queued mutations require the current epoch. Delete writes a tombstone before unlinking. History clear advances the epoch before clearing. Missing/tombstoned/mismatched sessions cannot be recreated by ordinary mutations.

- [ ] Write deterministic failing tests for generation finishing after delete, source save after history clear, stale queued command after epoch advance, and normal current-epoch writes.
- [ ] Run focused tests and verify RED.
- [ ] Implement epoch persistence, Web payload propagation, queue binding, tombstone checks, and atomic locked mutation.
- [ ] Run focused and Companion tests and verify GREEN.
- [ ] Commit with message `fix: reject stale session mutations`.

### Task 9: Preserve Failed Queue Work And Confirm Queued Writes

**Files:**
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/source_workspace_lifecycle.js` if a pure queue-result policy helper is needed.
- Modify: `tests/source_workspace_lifecycle.test.js`
- Modify: `tests/test_web_controls_static.py`

**Interfaces:**
- Produces: one shared queue-result handler used by direct queue drain and native/Web queued execution.
- Rule: failed queue work is not acknowledged and is marked deferred/retryable. Inactive-session chat may persist without rendering. Card, mind-map, full-reading, expand, and reorganize results execute only in the bound active session and enter the existing draft/confirmation UI; no queued write is applied automatically.

- [ ] Write executable failing tests for failed result no-ack, inactive session no-render, active chat success ack, inactive write defer, and active write draft/confirmation routing.
- [ ] Run Node/UI tests and verify RED.
- [ ] Implement the shared result policy and wire every queue execution path through it.
- [ ] Run Node/static/full tests and verify GREEN.
- [ ] Commit with message `fix: preserve queued failures and confirmations`.

### Task 10: Bulk Select And Remove Sources

**Files:**
- Modify: `extension/codex.mn.assistant/web/index.html`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Modify: `extension/codex.mn.assistant/web/source_workspace_lifecycle.js` if a pure bulk-selection helper is needed.
- Modify: `ui_functional_acceptance.py`
- Modify: `tests/source_workspace_lifecycle.test.js`
- Modify: `tests/test_web_controls_static.py`
- Modify: `tests/test_resizable_panel_static.py`
- Modify: `tests/test_ui_functional_acceptance.py`

**Interfaces:**
- Produces: bulk-management mode with a removal-selection set independent from source membership.
- Rule: `全选可移除`, `取消全选`, and `移除所选` act only on current conversation membership. Original files and upload records remain untouched. A followed current document is protected until follow-current is disabled. Save/rebuild/validation is atomic and restores membership after failure.

- [ ] Write executable and static failing tests for subset removal, select-all, protected current file, cancel, rollback after failed save, upload/migration gating, and 390 px layout.
- [ ] Run tests and verify RED.
- [ ] Implement dedicated bulk selection state, command bar, confirmation summary, atomic save, and rollback.
- [ ] Run Node/static/full tests and verify GREEN.
- [ ] Commit with message `feat: add bulk source removal`.

### Task 11: Repair-Cycle Documentation And Acceptance

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/USER_MANUAL.md`
- Modify: `docs/RELEASE_CHECKLIST.md`
- Modify: `CHANGELOG.md`
- Modify: release/version tests only when documentation contracts require them.

**Interfaces:**
- Consumes: Tasks 7–10.
- Produces: final `0.4.53` artifacts and installed local runtime. No push, tag, merge, or GitHub Release.

- [ ] Document token loopback behavior, session lifecycle rejection, retryable failed queue work, confirmed queued writes, and bulk source removal safety.
- [ ] Run the complete Python/Node/syntax/version/diff suite.
- [ ] Rebuild zip, mnaddon, and pkg; run smoke and install dry-run.
- [ ] Install packaged `0.4.53`, restart Companion/MarginNote, verify runtime and controls.
- [ ] Live-test multiple upload, subset/select-all removal, original-file preservation, follow-off Lee→Hilton, one real source request, failed queue retention, and draft confirmation without writing a real mind map.
- [ ] Commit documentation changes and run final whole-branch review.
