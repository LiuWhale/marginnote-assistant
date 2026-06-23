# Codex Paper Companion WebView Design

## Goal

Turn the existing MarginNote 4 companion prototype into an in-app paper-reading panel that ordinary users can operate without Terminal: type questions, use selected PDF text, generate native MN cards, generate a mindmap branch, inspect connection state, and see clear status for highlighters and PDF export.

## Scope

This iteration implements the missing input-capable plugin panel. It does not claim solved native visible highlighting, because the only proven direct-highlight route is experimental SQLite state and is disabled by default. The UI must expose that boundary honestly and keep the original PDF clean.

## Architecture

The MarginNote extension keeps the existing native-card and native-mindmap implementation in `main.js`. A new `CodexWebPanelController.js` hosts a local `UIWebView`, loads `web/index.html`, and intercepts `codexpaper://` URLs from the page. The web page sends actions to the controller, the controller calls the existing `sendPanelAction()`, and `main.js` posts to the existing local Companion endpoint at `127.0.0.1:48761`.

If the WebView fails to load, the legacy `CodexPanelController.js` remains available as a fallback. Companion remains the same trust boundary: it can generate responses and payloads, while MarginNote-native writes happen inside the plugin process.

## Components

- `CodexWebPanelController.js`: MarginNote-side WebView host, JS injection, custom URL bridge, context updates, close/resize UI.
- `web/index.html`: input-capable app surface with history, prompt box, context preview, action buttons, and status bar.
- `web/app.css`: restrained, dense paper-reading UI with responsive constraints for the fixed panel.
- `web/app.js`: client-side bridge, optimistic messages, button state, context rendering, and result callbacks.
- `main.js`: prefers the WebView controller, exposes context/status/reply to the web UI, and falls back to the old panel.
- `companion.py`: keeps existing actions, adds friendly responses for not-yet-publishable highlight/export actions where needed.
- `doctor.py`: verifies that WebView files exist and reports the UI gap closed only when the files and manifest are present.

## Data Flow

1. User types a prompt or selects PDF text.
2. Web page navigates to `codexpaper://action?name=<action>&prompt=<encoded>`.
3. `CodexWebPanelController` intercepts the URL and calls `addon.sendPanelAction(name, prompt)`.
4. `main.js` builds MarginNote context: topic id, document md5, selected text, selected note title/body.
5. Companion returns a reply plus optional `cards` and `mindmap`.
6. `main.js` renders reply/status back into the panel and creates cards/mindmap with MarginNote native APIs.

## Error Handling

- Companion unavailable: panel shows a clear local-service error and keeps the typed prompt.
- WebView load failure: controller shows a small HTML error page; the legacy panel file remains installed.
- Unsupported highlight/export: Companion returns a user-facing explanation instead of attempting unsafe database writes.
- Repeated generation: current behavior may append duplicates; this remains a known release gap until a note metadata/dedup task is implemented.

## Verification

- Static: `node --check` for all plugin JS, `python3 -m py_compile` for Python, `python3 -m json.tool` for manifest.
- Service: `/status` and direct `send_action.py chat --direct`.
- Plugin bridge: programmatic queue action still creates cards/mindmap after MN4 is open.
- Release: package zip contains extension WebView files, companion scripts, docs, and excludes logs/sessions/cache.
- Visual QA: after MN4 reload, confirm the panel shows input, history, context, and no clipped controls.

## Remaining v1.0 Risks

- Native visible highlights need a stable MN4 API or a maintainable import/export route.
- Annotated PDF export should create a copy only after native annotations exist.
- Cross-machine install and signing are still required before public distribution.
