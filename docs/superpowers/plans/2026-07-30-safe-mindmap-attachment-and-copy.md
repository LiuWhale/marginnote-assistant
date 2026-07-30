# Safe Mindmap Attachment And Reply Copy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Safely attach reply-derived mindmap subtrees beneath a verified relevant parent without modifying existing nodes, and add one-click Markdown copying to every completed Codex answer.

**Architecture:** A new pure Python planner scores verified nodes from the cached current mindmap, removes duplicate proposed nodes, and returns a stable create-only attachment route. `companion.py` invokes it only for reply-derived mindmaps and carries the route into drafts. The native handler resolves the planned parent by note ID immediately before writing, while the WebView adds an explicit reply-derived flag and a clipboard control with a textarea fallback.

**Tech Stack:** Python 3 standard library, MarginNote JavaScript bridge, browser Clipboard API, `unittest`, existing static WebView contracts.

## Global Constraints

- Reply-derived mindmaps may create new notes only; they must not update, merge, move, delete, rename, or replace existing nodes.
- A compatible selected node wins; otherwise use the strongest semantic candidate; low-confidence routing falls back to the stable document root.
- A planned existing parent is addressed by stable note ID and revalidated immediately before native write.
- Rejecting the AI edit must delete the underlying newly created notes and report residual identifiers.
- Copy controls appear only on completed Codex answers and copy the original Markdown source.
- Copy actions must not submit prompts, enqueue actions, or move focus to the composer.

---

### Task 1: Pure Reply Mindmap Attachment Planner

**Files:**
- Create: `mindmap_attachment.py`
- Create: `tests/test_mindmap_attachment.py`

**Interfaces:**
- Consumes: proposed and current tree dictionaries using `title`, `body`, `noteId`, and `children`.
- Produces: `plan_reply_attachment(proposed_tree, current_tree, selected_note_id, document_root_target) -> dict` with `tree`, `writeTarget`, `routing`, and `duplicateCount`.

- [ ] **Step 1: Write failing planner tests**

```python
def test_compatible_selected_node_wins():
    result = plan_reply_attachment(proposed, current, "method-node", root_target)
    assert result["writeTarget"]["mode"] == "verified_parent_node"
    assert result["writeTarget"]["parentNoteId"] == "method-node"

def test_stronger_candidate_beats_incompatible_selection():
    result = plan_reply_attachment(proposed, current, "intro-node", root_target)
    assert result["writeTarget"]["parentNoteId"] == "attention-node"

def test_low_confidence_falls_back_to_document_root():
    result = plan_reply_attachment(unrelated, current, "", root_target)
    assert result["writeTarget"]["mode"] == "document_root"

def test_existing_and_repeated_titles_are_removed_from_proposed_tree():
    result = plan_reply_attachment(proposed_with_duplicates, current, "", root_target)
    assert result["duplicateCount"] == 2
    assert collect_titles(result["tree"]) == ["New topic"]
```

- [ ] **Step 2: Run tests and verify RED**

Run: `python3 -m unittest -q tests.test_mindmap_attachment`

Expected: import failure because `mindmap_attachment.py` does not exist.

- [ ] **Step 3: Implement deterministic scoring and deduplication**

```python
def plan_reply_attachment(
    proposed_tree: dict[str, Any],
    current_tree: dict[str, Any],
    selected_note_id: str,
    document_root_target: dict[str, Any],
    confidence_threshold: float = 0.34,
) -> dict[str, Any]:
    candidates = flatten_current_nodes(current_tree)
    query_terms = tree_terms(proposed_tree)
    ranked = rank_candidates(candidates, query_terms, selected_note_id)
    target = verified_parent_target(ranked[0]) if ranked and ranked[0]["score"] >= confidence_threshold else dict(document_root_target)
    tree, duplicate_count = prune_duplicate_proposed_nodes(proposed_tree, candidates)
    return {
        "tree": tree,
        "writeTarget": target,
        "routing": route_summary(target, ranked),
        "duplicateCount": duplicate_count,
    }
```

- [ ] **Step 4: Run planner tests and verify GREEN**

Run: `python3 -m unittest -q tests.test_mindmap_attachment`

Expected: all planner tests pass.

### Task 2: Companion Reply-Derived Generation Contract

**Files:**
- Modify: `companion.py`
- Modify: `tests/test_companion_controls.py`

**Interfaces:**
- Consumes: `replyDerivedMindmap: true`, cached mindmap tree, generated proposed tree, selected node context.
- Produces: `mindmapAttachment` metadata and a create-only `mindmapDiffOperationPlan`.

- [ ] **Step 1: Write failing Companion tests**

```python
def test_reply_derived_mindmap_uses_cached_tree_and_verified_parent():
    result = companion.generate_mindmap(reply_payload)
    assert result["mindmapAttachment"]["parentNoteId"] == "method-node"
    assert result["writeTarget"]["mode"] == "verified_parent_node"

def test_reply_derived_mindmap_diff_is_create_only():
    result = companion.generate_mindmap(reply_payload)
    mutations = {item["mutation"] for item in result["mindmapDiffOperationPlan"]["operations"]}
    assert mutations <= {"create"}

def test_reply_derived_mindmap_without_tree_requests_refresh_and_does_not_generate():
    result = companion.generate_mindmap(reply_payload_without_cache)
    assert not result["ok"]
    assert result["mindmapRefreshRequired"] is True
```

- [ ] **Step 2: Run the targeted tests and verify RED**

Run: `python3 -m unittest -q tests.test_companion_controls.CompanionControlsTests.test_reply_derived_mindmap_uses_cached_tree_and_verified_parent tests.test_companion_controls.CompanionControlsTests.test_reply_derived_mindmap_diff_is_create_only tests.test_companion_controls.CompanionControlsTests.test_reply_derived_mindmap_without_tree_requests_refresh_and_does_not_generate`

Expected: failures because reply-derived routing metadata and create-only plans do not exist.

- [ ] **Step 3: Integrate planner and build create-only operations**

```python
if truthy_payload_flag(payload.get("replyDerivedMindmap")):
    cache = read_latest_mindmap_tree(normalize_topic_id(payload), normalize_book_md5(payload))
    current = _payload_mindmap(cache.get("currentMindmap"))
    if not current:
        refresh = request_mindmap_tree({**payload, "source": "reply-derived-mindmap"})
        return {
            "ok": False,
            "message": "正在读取当前脑图，请读取完成后再次生成。",
            "mindmapRefreshRequired": True,
            "mindmapRefresh": refresh,
        }
    planned = mindmap_attachment.plan_reply_attachment(
        tree,
        current,
        str(payload.get("selectedNoteId") or ""),
        document_root_mindmap_target(payload),
    )
```

Create-only operations must contain `create_mindmap_node`, `mutation: create`, proposed paths, and `targetParentRef` for the verified parent. Existing-title duplicates are excluded rather than converted into merge/update operations.

- [ ] **Step 4: Run targeted and complete Companion tests**

Run: `python3 -m unittest -q tests.test_companion_controls`

Expected: all Companion control tests pass.

### Task 3: Native Verified-Parent Write Guard

**Files:**
- Modify: `extension/codex.mn.assistant/main.js`
- Modify: `tests/test_resizable_panel_static.py`

**Interfaces:**
- Consumes: `writeTarget.mode = verified_parent_node`, `parentNoteId`, and `parentNoteTitle`.
- Produces: child nodes attached to the verified existing note or a blocked `createMindmapFailed` event.

- [ ] **Step 1: Write failing native static contract test**

```python
def test_reply_mindmap_resolves_verified_parent_without_overwriting_existing_nodes(self):
    body = extract_create_mindmap(self.main)
    self.assertIn("verified_parent_node", body)
    self.assertIn("findNoteById(ctx.notebook, targetParentNoteId)", body)
    self.assertIn("verified-parent-missing", body)
    self.assertNotIn("note.noteTitle = rootTitle", body)
```

- [ ] **Step 2: Run static test and verify RED**

Run: `python3 -m unittest -q tests.test_resizable_panel_static.ResizablePanelContractTest.test_reply_mindmap_resolves_verified_parent_without_overwriting_existing_nodes`

Expected: failure because `verified_parent_node` is not implemented.

- [ ] **Step 3: Implement native parent revalidation**

```javascript
var wantsVerifiedParent = targetMode === 'verified_parent_node';
var targetParentNoteId = String(valueOf(writeTarget, 'parentNoteId') || '');
var verifiedParent = wantsVerifiedParent ? findNoteById(ctx.notebook, targetParentNoteId) : null;
if (wantsVerifiedParent && !verifiedParent) {
  this.postEvent('createMindmapFailed', {reason: 'verified-parent-missing', expectedNoteId: targetParentNoteId});
  return;
}
```

Route reply-derived children through the same `makeNode` function under `verifiedParent`. Do not assign to any existing note title/body or reparent existing notes.

- [ ] **Step 4: Run JavaScript syntax and static tests**

Run: `node --check extension/codex.mn.assistant/main.js && python3 -m unittest -q tests.test_resizable_panel_static`

Expected: syntax succeeds and all static tests pass.

### Task 4: Completed-Answer Markdown Copy Button

**Files:**
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Modify: `tests/test_resizable_panel_static.py`

**Interfaces:**
- Consumes: original answer Markdown passed to `addAssistantReplyWithActions` or restored from conversation history.
- Produces: exactly one `.reply-copy-button` under each completed assistant answer.

- [ ] **Step 1: Write failing copy-button tests**

```python
def test_completed_answers_have_markdown_copy_with_fallback(self):
    self.assertIn("buildReplyCopyButton", self.app)
    self.assertIn("navigator.clipboard.writeText", self.app)
    self.assertIn("document.execCommand('copy')", self.app)
    self.assertIn("reply-copy-button", self.css)

def test_history_assistant_answers_use_completed_reply_renderer(self):
    body = extract_render_history_items(self.app)
    self.assertIn("addCompletedAssistantReply", body)
```

- [ ] **Step 2: Run copy tests and verify RED**

Run: `python3 -m unittest -q tests.test_resizable_panel_static.ResizablePanelContractTest.test_completed_answers_have_markdown_copy_with_fallback tests.test_resizable_panel_static.ResizablePanelContractTest.test_history_assistant_answers_use_completed_reply_renderer`

Expected: failures because the copy control does not exist.

- [ ] **Step 3: Implement clipboard helper and renderer**

```javascript
function writeTextToClipboard(text, callback) {
  function fallback() {
    var textarea = document.createElement('textarea');
    textarea.value = String(text || '');
    document.body.appendChild(textarea);
    textarea.select();
    var ok = document.execCommand('copy');
    document.body.removeChild(textarea);
    callback(ok);
  }
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(String(text || '')).then(function() { callback(true); }).catch(fallback);
  } else {
    fallback();
  }
}
```

`addCompletedAssistantReply(text, includeMindmapAction)` appends the copy button once, keeps `text` in the closure as Markdown, and optionally appends the existing reply mindmap action. History restoration calls it with `includeMindmapAction = false`.

- [ ] **Step 4: Mark reply-derived mindmap requests explicitly**

Extend `executeAction` and `requestDraftAction` to accept an extra payload object. `runAgentNextAction` passes:

```javascript
{
  replyDerivedMindmap: true,
  sourceAnswerMarkdown: String(replyText || '')
}
```

The extra object must be copied through `companionPayload` and queue payloads.

- [ ] **Step 5: Run WebView syntax and static tests**

Run: `node --check extension/codex.mn.assistant/web/app.js && python3 -m unittest -q tests.test_resizable_panel_static`

Expected: syntax succeeds and all static tests pass.

### Task 5: Integration Verification And Documentation

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/USER_MANUAL.md`
- Test: `tests/test_companion_controls.py`
- Test: `tests/test_mindmap_attachment.py`
- Test: `tests/test_resizable_panel_static.py`

**Interfaces:**
- Consumes: all behavior from Tasks 1-4.
- Produces: documented, packaged behavior with complete regression evidence.

- [ ] **Step 1: Document user-visible behavior**

Add an Unreleased entry explaining automatic safe attachment, root fallback, create-only Diff, and Markdown copy buttons. Add a concise user-manual section describing the destination shown in preview and the copy result state.

- [ ] **Step 2: Run focused verification**

Run:

```bash
python3 -m unittest -q tests.test_mindmap_attachment
python3 -m unittest -q tests.test_companion_controls
python3 -m unittest -q tests.test_resizable_panel_static
python3 -m unittest -q tests.test_release_docs tests.test_release_packaging
python3 -m py_compile companion.py mindmap_attachment.py
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
git diff --check
```

Expected: all tests and syntax checks pass with no diff whitespace errors.

- [ ] **Step 3: Install the updated local plugin**

Run:

```bash
./install_extension.sh
./install_companion.sh
```

Expected: both MarginNote container paths and the Companion LaunchAgent are updated. MarginNote must be fully restarted to load changed native JavaScript.

- [ ] **Step 4: Review the final diff**

Run: `git status --short --branch && git diff --stat && git diff`

Expected: only planner, Companion, WebView/native code, tests, changelog, user manual, and this implementation plan are changed.
