# Context Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a usable Auto / Selection / Full Text context selector backed by real PDF full-text retrieval.

**Architecture:** The web panel owns the user's scope choice and sends `contextScope` with every action. Companion normalizes the scope, builds model input from either selection/node context or retrieved PDF chunks, and caches extracted PDF text under the existing upload cache.

**Tech Stack:** MarginNote extension HTML/CSS/JavaScript, Python Companion HTTP service, PyMuPDF via subprocess, `unittest`, `node --check`.

---

### Task 1: Backend Scope Routing

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/companion.py`
- Test: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_companion_controls.py`

- [ ] Add tests for `normalize_context_scope`, selection priority in auto mode, explicit document mode, and document intent in auto mode.
- [ ] Add helpers for selected material context, user prompt context, context-scope normalization, and effective scope selection.
- [ ] Update `build_model_input` to include selected material only in selection scope and document retrieval only in document scope.

### Task 2: PDF Text Cache And Retrieval

**Files:**
- Modify: `/Users/liuwhale/.codex/marginnote-assistant/companion.py`
- Test: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_companion_controls.py`

- [ ] Add text-cache constants under the existing PDF cache directory.
- [ ] Extract page text with PyMuPDF, repair PDF math Unicode loss, chunk by page, and save JSON cache keyed by book id and PDF hash.
- [ ] Retrieve chunks using query-term scoring with page-ordered output and first-page fallback.
- [ ] Return a clear status when the PDF cannot be resolved or PyMuPDF is unavailable.

### Task 3: Web Panel Scope Control

**Files:**
- Modify: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/index.html`
- Modify: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.css`
- Modify: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js`
- Test: `/Users/liuwhale/.codex/marginnote-assistant/tests/test_web_controls_static.py`

- [ ] Add an Auto / Selection / Full Text segmented control in the current-content box.
- [ ] Store the chosen scope in JS state, render active buttons, and include `contextScope` in all Companion payloads and queued actions.
- [ ] Update visible source text so the user knows whether AI will use selection or full-document retrieval.

### Task 4: Verification

**Files:**
- Verify: `/Users/liuwhale/.codex/marginnote-assistant/companion.py`
- Verify: `/Users/liuwhale/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js`

- [ ] Run targeted backend and web static tests.
- [ ] Run full `unittest discover`.
- [ ] Run `python3 -m py_compile` for Companion scripts and `node --check` for web JS.
- [ ] Restart the Companion LaunchAgent and ask MarginNote to reload the web panel.
