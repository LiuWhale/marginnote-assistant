# Codex Companion for MarginNote 4

![Codex Companion cover](assets/cover.png)

Codex Companion is a local-first MarginNote 4 extension that adds a Codex-style AI chat panel, document context controls, and reviewable card/mind-map creation to MarginNote.

It is designed for reading, annotating, and restructuring long documents. Academic papers are a major use case, but the plugin is intentionally general: it can work with any document that MarginNote exposes through its notebook, PDF, and selection APIs.

> This project is not affiliated with MarginNote, OpenAI, or Apple.

## What It Does

- Chat inside MarginNote with context from the current PDF selection, current mind-map node, or current document.
- Choose context explicitly: automatic, selection/node only, or full-document retrieval.
- Generate MarginNote cards and structured mind-map branches from model output.
- Add the latest answer to the mind map through a reviewable AI edit operation: accept keeps the new nodes, reject removes them.
- Use a clean built-in-AI-style chat surface; advanced controls live in a separate settings page.
- Configure AI backend: local Codex CLI, OpenAI API, or automatic fallback.
- Check GitHub Releases for plugin updates and install the latest release zip from settings.
- Queue actions while another generation is running, and stop the active task.
- Cache the current PDF through the MarginNote process to reduce macOS file-permission failures.
- Manage extra local file search roots from settings when MarginNote only exposes a document filename.
- View and clear structured diagnostic logs from settings for failed actions, path resolution, and Companion requests.
- Check Companion health, MarginNote runtime state, and native bridge capabilities from settings.
- Run release gates, package smoke tests, and deeper diagnostics from the command line.

Goal-style runs are treated as 一次性长任务 and 不会保存成长期当前目标, so ordinary chat and card generation do not silently inherit an old defense or reading goal.

## Architecture

The project has two cooperating parts:

- `extension/codex.mn.assistant`: the MarginNote 4 add-on, including the WebView UI and native MarginNote API bridge.
- `companion`: a local Python service on `127.0.0.1:48761` that handles model calls, queues, draft payloads, diagnostics, release checks, and file/PDF caches.

Installed paths:

```text
~/.codex/marginnote-assistant
~/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant
~/Library/LaunchAgents/com.codex.paper-companion.plist
```

Runtime state such as logs, drafts, queue files, uploaded context, `.env`, and event history is intentionally excluded from source control and release archives.

## Requirements

- macOS with MarginNote 4.
- Python 3.10+.
- Optional: Codex CLI available on `PATH` for local Codex-backed answers.
- Optional: OpenAI API key if you want direct OpenAI API calls.
- Optional: PyMuPDF (`fitz`) for annotated PDF copy export.

## Install From Release Zip

Download and unzip the latest `CodexCompanion-<version>-latest-dist.zip`, then run:

```bash
./install.sh
```

Or double-click:

```text
Install Codex Companion.command
```

Restart MarginNote 4, open a notebook, then open the Codex Companion panel from the add-on toolbar.

To uninstall:

```bash
./uninstall.sh
```

or double-click:

```text
Uninstall Codex Companion.command
```

## Configure AI

Open the settings page from the panel gear button.

Supported backends:

- `auto`: try Codex CLI first, then OpenAI API.
- `codex_cli`: require a working local Codex CLI.
- `openai_api`: require an OpenAI API key.

The OpenAI key is stored locally in `.env` and is never echoed back into the WebView. The release package includes `.env.example`, not your `.env`.

## Update

Open settings, set the GitHub repository, then click `检查更新`. The default repository is `LiuWhale/marginnote-assistant`.

If a newer GitHub Release is available, the main chat surface shows a compact update notice. Installing an update downloads the release zip, verifies that it contains `install.sh`, `companion/`, and `extension/codex.mn.assistant/`, then starts the bundled installer. Reopen the Codex panel after installation; restart MarginNote 4 if native files do not reload.

## Develop

Run the unit tests:

```bash
python3 -m unittest discover -s tests
```

Check Python syntax:

```bash
python3 -m py_compile companion.py runtime_config.py update_manager.py doctor.py release_acceptance.py release_smoke_test.py package_release.py prepare_release_handoff.py send_action.py single_document_acceptance.py
```

Check WebView JavaScript syntax:

```bash
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/web/app.js"
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/main.js"
node --check "$HOME/Library/Containers/QReader.MarginStudy.easy/Data/Library/MarginNote Extensions/codex.mn.assistant/CodexWebPanelController.js"
```

Start Companion manually:

```bash
./start_companion.sh
```

Check service status:

```bash
curl http://127.0.0.1:48761/status
```

## Package And Release

Build a clean release zip:

```bash
python3 package_release.py 0.4.19
```

Smoke-test the zip:

```bash
python3 release_smoke_test.py release/CodexCompanion-0.4.19-latest-dist.zip
python3 release_smoke_test.py release/CodexCompanion-0.4.19-latest-dist.zip --install-dry-run
```

Run the release acceptance report:

```bash
python3 release_acceptance.py release/CodexCompanion-0.4.19-latest-dist.zip --json
```

Release acceptance may remain blocked until you provide machine-specific evidence such as native highlight proof, signed/notarized package proof, or cross-machine install proof. Those gates are evidence checks, not source packaging failures.

## Privacy And Safety

- Original PDFs are not modified by annotated export; export writes a highlighted copy.
- Native highlighter actions use MarginNote's current active PDF selection when available.
- The package excludes `.env`, uploaded files, event logs, queue files, drafts, sessions, runtime caches, and backups.
- The local service listens only on `127.0.0.1` by default.
- Model output is staged as editable draft content before writing cards or mind-map branches.

## Repository Layout

```text
.
├── companion.py                 # local HTTP service and action dispatcher
├── runtime_config.py            # runtime defaults and settings sanitizers
├── doctor.py                    # local diagnostics
├── release_acceptance.py        # release gate runner
├── package_release.py           # clean release zip builder
├── extension/codex.mn.assistant # MarginNote 4 add-on source
├── tests/                       # unit and static-contract tests
├── docs/                        # user, product, privacy, and release docs
└── assets/                      # public README assets
```

## License

MIT. See [LICENSE](LICENSE).
