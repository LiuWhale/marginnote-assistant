# Codex Companion for MarginNote 4

![Codex Companion cover](assets/cover.png)

[![Latest Release](https://img.shields.io/github/v/release/LiuWhale/marginnote-assistant?label=release)](https://github.com/LiuWhale/marginnote-assistant/releases/latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Languages: **English** | [简体中文](README.zh-CN.md)

Codex Companion is a local-first AI assistant plugin for MarginNote 4. It connects Codex / OpenAI-style chat to the current MarginNote document, PDF selection, note node, and mind map, so you can explain material, create cards, generate structured mind-map trees, and review AI edits before they are kept.

It is not limited to academic papers. Papers, book chapters, course material, project documents, meeting notes, and any document that MarginNote can expose through its APIs can be used as context.

> This project is not affiliated with MarginNote, OpenAI, or Apple.

## What It Can Do

- Chat inside the MarginNote 4 panel with context from the current selection, node, or document.
- Choose the context scope explicitly: auto, selection/node only, or full document.
- Generate short MarginNote cards and structured mind-map branches, with draft or AI-edit confirmation before writing.
- Turn the latest answer into a mind-map tree; accept keeps it, reject attempts to remove the nodes and cards created by that edit.
- Select the target mind map at the top of the chat before writing, reducing the risk of creating nodes in the wrong notebook or page.
- Queue actions while another generation is running; pending tasks continue automatically.
- Stop the current generation; stopped tasks do not continue writing cards or mind maps.
- Show a persistent current-document cache light: yellow while caching, green when ready, red on failure.
- Provide chat history, new conversations, settings, file path management, structured logs, and diagnostics.
- Check GitHub Releases for updates and open the matching download page.
- Keep the original PDF clean by default; annotated export writes a copy instead of overwriting the source file.

Goal-style runs are one-shot long tasks. They are not saved as a persistent global goal, so normal chat, card generation, and mind-map generation do not silently inherit an old defense, reading, or presentation objective.

## Quick Install

1. Open the [Latest Release](https://github.com/LiuWhale/marginnote-assistant/releases/latest).
2. Download `CodexCompanion-<version>-latest-dist.zip`.
3. Unzip it and double-click:

```text
Install Codex Companion.command
```

Or run this from the unzipped folder:

```bash
./install.sh
```

4. Restart MarginNote 4.
5. Open a notebook or document, then open Codex Companion from the MarginNote add-on toolbar.

To uninstall, double-click:

```text
Uninstall Codex Companion.command
```

Or run:

```bash
./uninstall.sh
```

## First-Time Setup

Open settings from the gear button in the plugin panel.

Recommended settings:

- `AI Backend`: `auto`
- `Model`: `gpt-5.5`
- `Speed`: `fast`
- `Codex CLI`: preferred when the local Codex CLI is installed and logged in.
- `OpenAI Key`: use this when you want direct OpenAI API calls instead of Codex CLI.

Backend modes:

- `auto`: try local Codex CLI first, then OpenAI API.
- `codex_cli`: require a working local Codex CLI.
- `openai_api`: require an OpenAI API key.

If neither Codex CLI nor an OpenAI key is available, chat, card creation, mind-map generation, and full reading actions fail with a clear reason. The plugin does not use local templates to fake AI-generated content.

## Daily Use

### Ask Directly

Type a question in the main chat, press Enter, or click `发送 / 可排队`. The input clears after sending. If another task is already running, the new request enters the queue.

### Explain A Selection

Select text in a PDF or note node, then ask a question or click an explanation action. In `auto` context mode, the plugin prefers the active selection and falls back to the current document when no selection is available.

### Create A Mind-Map Tree

1. Choose the target mind map at the top of the chat.
2. Click `生成脑图树` under the latest answer, or ask for a structured mind map from the full document.
3. The plugin writes the mind-map branch into MarginNote first.
4. It then shows AI edit confirmation: `接受` keeps it, `拒绝` removes the new edit where the native API allows it.

If the current document has no suitable mind-map page, create or select the target in MarginNote first, then refresh the target list. This is safer than silently writing to an unrelated existing mind map.

### Create Cards

Cards are split into short, reviewable items rather than one oversized note. Generated cards go through a draft or AI-edit confirmation before they are written to MarginNote.

### New Conversation And History

The main chat can start a new conversation. History is a separate page for viewing or clearing conversations scoped to the current notebook / document.

## Full-Document Reading And Caching

MarginNote sometimes exposes only a document title, `bookmd5`, or selection text, not the original PDF path. Codex Companion tries these routes in order:

1. Use the current MarginNote document context.
2. Resolve the document through known file path mappings.
3. Search user-managed file roots from the settings page.
4. Ask the MarginNote plugin process to cache the current PDF into the local Companion service.

When macOS prevents the background service from reading OneDrive, iCloud, or sandboxed paths, the MarginNote-process cache route is usually more reliable than direct Python file access. The bottom status light shows whether caching is pending, ready, or failed.

Common messages:

- `Operation not permitted`: macOS privacy permissions blocked the background Companion from reading the file.
- `No resolvable local PDF path`: MarginNote did not expose a source path and no known mapping matched.
- `Keep the document open in MarginNote 4`: the plugin has asked MarginNote itself to read and upload the cache.

## Updates

The settings page provides two low-risk update controls:

- `检查更新`: check GitHub Releases for `LiuWhale/marginnote-assistant`.
- `打开下载页`: open the latest Release page for manual download and install.

The default update flow opens the download page instead of silently replacing the installed extension, because macOS permissions can block a background service from writing into the MarginNote extension directory. Manual installation is clearer and easier to audit.

## Permissions

Most card and mind-map workflows do not require Full Disk Access.

Extra permissions may be needed for:

- Direct background reading of files in OneDrive, iCloud, or protected folders: grant Full Disk Access to Terminal, Python, or the Companion runtime.
- System-level automated clicking: grant Accessibility permission to the runtime performing automation.
- Exporting annotated PDFs to some cloud folders: grant write access to the destination.

The plugin cannot simply inherit all of MarginNote's system permissions. MarginNote, the WebView, and the Python Companion are separate processes, and macOS controls their file and automation permissions separately.

## Privacy And Data

- The local Companion listens on `127.0.0.1:48761` by default.
- The OpenAI key is stored locally in `.env` and is never echoed back into the plugin UI.
- With `openai_api`, the selected text, note content, document snippets, and user request may be sent to OpenAI.
- With `codex_cli`, content is passed to local `codex exec`; network/account behavior follows your Codex CLI setup.
- The original PDF is not modified by default; annotated export writes a copy.
- Release packages exclude `.env`, uploaded files, logs, queues, drafts, sessions, and caches.

See [Privacy and Permissions](docs/PRIVACY_AND_PERMISSIONS.md) for details.

## FAQ

### The panel says "Codex Companion is not running"

Check the local service:

```bash
curl http://127.0.0.1:48761/status
```

If it does not respond, restart Companion:

```bash
./start_companion.sh
```

Or rerun the installer so the LaunchAgent is loaded again.

### The panel is connected, but sending fails

Open settings and check:

- Whether the selected AI backend is available.
- Whether Codex CLI is installed and logged in.
- Whether the OpenAI key has been saved.
- Whether the proxy URL uses a supported `http://` or `https://` scheme.
- The most recent `error` field in structured logs.

### Why can it sometimes not read the full document?

The MarginNote plugin API does not always expose the original PDF path. This is common with OneDrive, iCloud, sandbox caches, imported copies, and multi-document notebooks. The background Companion may only see a title or `bookmd5`. Prefer current-document caching and file path management over hard-coding one PDF path.

### Why can rejected mind-map edits leave cards behind?

The plugin records the nodes created by each edit and attempts to delete both the mind-map outline and the corresponding cards. In some MarginNote versions, deleting the outline and deleting the card object are separate native operations. If cards remain, export logs from settings and file an issue with the edit id and deletion result.

### `npm install -g @openai/codex` fails with `ENOTEMPTY`

This usually means the global `@openai/codex` directory has leftover files or another install process touched it. Confirm no npm install is running, remove the stale global package directory, then reinstall. Clearing only the npm cache usually does not fix `ENOTEMPTY` because the conflict is in the global install path.

## Logs And Diagnostics

Structured event log:

```text
~/.codex/marginnote-assistant/events.jsonl
```

Common runtime paths:

```text
~/.codex/marginnote-assistant
~/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant
~/Library/LaunchAgents/com.codex.paper-companion.plist
```

The settings page can show Companion health, AI probing, MarginNote runtime status, file path management, and recent logs. When reporting a bug, include:

- Plugin version.
- MarginNote 4 version.
- Action name.
- Most recent error message.
- Relevant `events.jsonl` entries.

## Development

Run tests:

```bash
python3 -m unittest discover -s tests
```

Check Python syntax:

```bash
python3 -m py_compile companion.py diagnostic_log.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py
```

Check WebView JavaScript:

```bash
node --check extension/codex.mn.assistant/web/app.js
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/CodexWebPanelController.js
```

Start Companion locally:

```bash
./start_companion.sh
```

Check service status:

```bash
curl http://127.0.0.1:48761/status
```

## Package And Release

Build the release zip:

```bash
python3 package_release.py 0.4.24
```

Smoke test:

```bash
python3 release_smoke_test.py release/CodexCompanion-0.4.24-latest-dist.zip
python3 release_smoke_test.py release/CodexCompanion-0.4.24-latest-dist.zip --install-dry-run
```

Release acceptance:

```bash
python3 release_acceptance.py release/CodexCompanion-0.4.24-latest-dist.zip --json
```

Release acceptance may remain blocked by machine-specific evidence such as native visible highlight proof, signed/notarized package proof, or cross-machine install proof. These are release evidence gates, not source packaging failures.

## Repository Layout

```text
.
├── companion.py                 # local HTTP service and action dispatcher
├── runtime_config.py            # runtime defaults and settings sanitizers
├── update_manager.py            # GitHub Release update checks
├── doctor.py                    # local diagnostics
├── release_acceptance.py        # release gate runner
├── package_release.py           # clean release zip builder
├── extension/codex.mn.assistant # MarginNote 4 add-on source
├── tests/                       # unit and static-contract tests
├── docs/                        # user, product, privacy, and release docs
└── assets/                      # README cover and icons
```

## Documentation

- [Chinese README](README.zh-CN.md)
- [User Manual](docs/USER_MANUAL.md)
- [Privacy and Permissions](docs/PRIVACY_AND_PERMISSIONS.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Current Release Audit](docs/CURRENT_RELEASE_AUDIT.md)
- [MarginNote AI Chat Parity](docs/MN4_AI_CHAT_PARITY.md)

## License

MIT. See [LICENSE](LICENSE).
