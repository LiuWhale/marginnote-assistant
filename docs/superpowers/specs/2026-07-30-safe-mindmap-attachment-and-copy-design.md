# Safe Mindmap Attachment And Reply Copy Design

## Goal

Make the reply-level "Generate mindmap tree" action safe for both short questions and full-document answers. The plugin must place the generated subtree under the most relevant existing node without replacing the current mindmap. Every completed Codex answer must also provide a reliable one-click Markdown copy action.

## Scope

This change covers:

- mindmap generation launched from a completed chat answer;
- automatic parent selection inside the current document mindmap;
- non-destructive Diff, confirmation, rejection, and rollback behavior;
- a copy-to-clipboard control on completed assistant answers.

It does not change full-document mindmap generation requested as a standalone task, user-message cards, progress/status cards, or MarginNote native clipboard behavior outside the Codex panel.

## Mindmap Attachment Contract

The plugin reads the current target mindmap before preparing a reply-derived subtree. It compares the answer topic and proposed subtree titles with the existing node titles, bodies, paths, and stable note identifiers.

Parent selection follows this order:

1. Use the currently selected node only when it still exists in the same notebook and is semantically compatible with the answer.
2. Otherwise choose the highest-scoring compatible node in the current document mindmap.
3. If no candidate passes the confidence threshold, attach the subtree under the stable document mindmap root.
4. If the document root does not exist, create one stable document root and attach the subtree beneath it.

The route decision is persisted in the draft as a stable parent note reference, selected-parent title, confidence, reason, and fallback status. Native write code must resolve the same note identifier immediately before applying the operation. A missing or changed target blocks the write and requests a refreshed preview instead of silently choosing another location.

## Non-Destructive Write Rules

Reply-derived mindmaps are create-only:

- existing node titles, comments, parent relationships, and children are not modified;
- existing nodes are never deleted, replaced, or recreated;
- only new subtree nodes may appear in the apply plan;
- repeated titles or equivalent existing content are reported as duplicates and omitted from the new subtree;
- the preview states the chosen parent and the number of nodes to be created or skipped.

The existing AI edit transaction remains the confirmation boundary. Accept keeps the newly created subtree. Reject deletes both the newly created structure and the underlying newly created notes/cards. Partial failure produces residual identifiers and a blocked status instead of reporting a successful rollback.

## Parent Selection

Candidate scoring is deterministic and local. It normalizes Chinese and English text, then combines:

- exact and partial title matches;
- keyword overlap between the answer/subtree and the node title/body;
- path relevance, favoring a specific matching branch over the document root;
- the selected-node preference when the selection is still compatible;
- duplicate and self-reference penalties.

The model may propose a topic label, but it cannot directly choose an arbitrary note identifier. The Companion maps the label to verified candidates and applies the confidence threshold. Low-confidence results always fall back to the document root, as approved, without an extra selection dialog.

## Reply Copy Control

Each completed Codex answer renders one copy icon button below the answer body. User messages, queue summaries, progress reports, errors, and system/status cards do not render this control.

The button copies the answer's original Markdown source so headings, lists, formulas, links, and code blocks remain intact. It uses the modern Clipboard API when available and a WebView-compatible hidden-textarea fallback otherwise. On success, the button temporarily shows "Copied"; on failure, it shows a visible failure state without altering the answer.

Repeated rendering and history restoration must create exactly one copy button per completed answer. Copying must not submit a prompt, change focus to the chat composer, or enqueue an action.

## Data Flow

1. The user clicks "Generate mindmap tree" below a completed answer.
2. The WebView sends the answer Markdown, current notebook/document identifiers, selected note reference, and current target information.
3. Companion requests or uses a fresh current-mindmap snapshot.
4. Companion builds the proposed subtree, scores verified parent candidates, removes duplicates, and emits a create-only Diff.
5. The preview identifies the destination parent and fallback reason.
6. Acceptance sends the parent note identifier and create-only operations to the native handler.
7. The native handler revalidates the parent, creates the subtree in one undo group, records created note identifiers, and opens the existing accept/reject transaction UI.
8. Rejection deletes all recorded new notes and verifies that no residual notes remain.

## Error Handling

- No current notebook or document: block generation with a context-refresh instruction.
- Mindmap tree unavailable: request a native refresh and do not create a standalone root elsewhere.
- Target changed after preview: block apply and require a new preview.
- No confident parent: attach under the stable document root.
- Duplicate answer content: skip duplicates and report the skipped count.
- Clipboard permission/API failure: use the fallback; if both fail, show "Copy failed".
- Rollback residuals: keep the transaction visible with the exact residual note identifiers.

## Tests

Backend tests must prove:

- a compatible selected node is chosen;
- an incompatible selection does not override a stronger semantic candidate;
- a low-confidence answer falls back to the stable document root;
- only create operations are emitted for reply-derived mindmaps;
- duplicate proposed nodes are skipped;
- stale or missing parent identifiers block apply;
- rejection removes all created note objects and reports residual failures.

WebView and native static/functional tests must prove:

- every completed assistant answer has exactly one copy button;
- user/status/progress cards have no copy button;
- the copied value is the original Markdown source;
- Clipboard API and textarea fallback paths work;
- copy clicks do not send or enqueue chat actions;
- reply mindmap preview displays the chosen parent and fallback reason;
- generated nodes are attached under the verified parent without modifying existing nodes.

## Acceptance Criteria

- A short answer can generate a subtree that is automatically attached to a relevant existing branch.
- Low-confidence placement attaches beneath the current document root.
- Existing mindmap nodes remain byte-for-byte and structurally unchanged.
- Rejecting the edit leaves no newly created notes or cards.
- Every completed Codex answer can be copied as Markdown with one click.
