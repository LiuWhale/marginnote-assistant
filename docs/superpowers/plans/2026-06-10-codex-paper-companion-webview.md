# Codex Paper Companion WebView Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an input-capable WebView panel to the existing MarginNote 4 companion plugin.

**Architecture:** Keep existing companion actions and native MN card/mindmap writes. Add a local WebView UI that talks to `main.js` through `codexpaper://` URLs, then lets `main.js` reuse the existing Companion HTTP client.

**Tech Stack:** MarginNote JSB, `UIWebView`, local HTML/CSS/JS, Python stdlib HTTP companion, zsh packaging.

---

### Task 1: Add WebView Controller

**Files:**
- Create: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexWebPanelController.js`

- [ ] Create a `UIViewController <UIWebViewDelegate>` with a header, close button, resize handle, and embedded `UIWebView`.
- [ ] Load `mainPath + "/web/index.html"` by file URL.
- [ ] Intercept `codexpaper://action`, `codexpaper://close`, and `codexpaper://context`.
- [ ] Expose `setPromptText`, `setStatus`, `setReply`, and `setBusy` so `main.js` can update the page.
- [ ] Escape JSON before injecting JavaScript into the WebView.

### Task 2: Add Web UI

**Files:**
- Create: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/index.html`
- Create: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.css`
- Create: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js`

- [ ] Build the first screen as the actual paper companion, not a landing page.
- [ ] Provide prompt input, selected-text preview, response history, and action buttons.
- [ ] Send actions through `codexpaper://action?name=...&prompt=...`.
- [ ] Render native callback functions: `CodexPanel.setContext`, `CodexPanel.setStatus`, `CodexPanel.setReply`, and `CodexPanel.setBusy`.

### Task 3: Prefer WebView in `main.js`

**Files:**
- Modify: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/main.js`

- [ ] Require `CodexWebPanelController`.
- [ ] Instantiate WebView panel first and legacy panel only as fallback.
- [ ] Pass `mainPath`, `addon`, and `addonWindow` into the controller.
- [ ] Extend event payloads to show whether the WebView panel loaded.
- [ ] Call `setBusy(false)` after Companion responses or connection errors.

### Task 4: Friendly Unsupported Actions

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/companion.py`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/send_action.py`

- [ ] Add `explain_selection`, `export_annotated_pdf`, and `diagnose_highlights` action names.
- [ ] Route `explain_selection` to the same backend as chat.
- [ ] Return explicit, non-destructive messages for highlighter/export actions until native MN highlight support is proven.

### Task 5: Docs, Doctor, Package

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/README.md`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/docs/PRODUCT_SPEC.md`
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/doctor.py`
- Create: `/Users/liuwhale/.codex/marginnote-assistant/package_release.sh`

- [ ] Update docs to describe the WebView panel as implemented.
- [ ] Make `doctor.py` verify WebView controller plus all three web assets.
- [ ] Build a release package that includes `extension/codex.mn.assistant` and `companion`.
- [ ] Sync the latest package and docs to OneDrive.

### Task 6: Verification

**Commands:**

```bash
node --check "/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/main.js"
node --check "/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexPanelController.js"
node --check "/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexWebPanelController.js"
node --check "/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js"
python3 -m py_compile /Users/liuwhale/.codex/marginnote-assistant/companion.py /Users/liuwhale/.codex/marginnote-assistant/send_action.py /Users/liuwhale/.codex/marginnote-assistant/doctor.py
python3 -m json.tool "/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/mnaddon.json"
/Users/liuwhale/.codex/marginnote-assistant/doctor.py
```

Expected: static checks pass; doctor reports WebView chat UI as OK while native highlight/export remains a warning, not a hidden failure.
