# Changelog

All notable changes to Codex Companion are documented here.

## 0.4.18 - 2026-06-24

### Fixed

- Fixed intermittent chat progress cards that could stop counting or show `0s` because `/status` polling accepted a stale completed run from a previous request.
- Generation run state now carries the current request id, and the WebView progress poller ignores run-state updates that do not belong to the active request.

## 0.4.17 - 2026-06-24

### Added

- Added a main-chat PDF cache status banner for the current document, showing when MN4 is still caching the PDF, when the cached copy is ready, or when macOS file permissions blocked direct reading.

### Changed

- The "cache current PDF" control now uses the same native MN4 queue path as automatic fallback caching, so it can work even when the background Companion process cannot read the original PDF path.
- Queue/status responses now include structured `pdfCache` progress data for the active document.

## 0.4.16 - 2026-06-24

### Fixed

- Fixed PDF discovery after switching to another MarginNote document whose title is reported without `.pdf` and with a MarginNote copy suffix such as `#1`.
- Fixed native PDF cache requests when the background Companion process cannot list a configured OneDrive/iCloud file directory: Companion now derives likely PDF candidate paths directly from `documentTitle` and passes them to the MN4 native plugin.

## 0.4.15 - 2026-06-24

### Added

- Added automatic current-PDF discovery from MarginNote document title/file-name metadata, so configured file roots can work without manually entering a full PDF path.
- Added selection-text PDF discovery: when no filename is available, Companion can scan configured file roots and identify the current PDF from the active PDF selection text.

### Changed

- Improved missing-PDF diagnostics to distinguish saved directory roots from missing document filename/selection evidence, instead of asking users to manually add a `bookmd5` mapping.

## 0.4.14 - 2026-06-23

### Added

- Added a settings-page diagnostic log viewer backed by `logs/diagnostics.jsonl`, with action lifecycle records, request ids, elapsed time, failure summaries, and log clearing.
- Added file path management in settings so users can maintain multiple local search roots for MarginNote document source recovery.

### Changed

- Current-document source lookup now also searches configured file roots recursively by recorded file name, improving recovery when MarginNote only exposes an MNDoc filename.
- Diagnostic logging redacts API keys, tokens, base64 payloads, and large generated content while preserving useful action, path, and error metadata.

## 0.4.13 - 2026-06-23

### Added

- Added independent new-conversation and history pages for document-bound chat sessions.
- Added broader PDF path recovery across MarginNote document caches and common OneDrive/iCloud paper roots.

### Fixed

- Reduced the risk of MarginNote 4 RemoteTextInput crashes by pausing background context refresh while text inputs are focused, slowing the refresh interval, and releasing the prompt focus after send.
- Stopped background context refresh from mutating the prompt textarea when a PDF selection is cleared.
- Filtered stale “missing pdfPath” assistant replies out of future model history after a PDF path becomes resolvable.

## 0.4.12 - 2026-06-23

### Changed

- Moved the context refresh button and context scope controls from the main chat surface into the settings page.
- Kept the main chat surface focused on conversation, update notices, and generation status while preserving context controls under Settings.

## 0.4.11 - 2026-06-23

### Fixed

- Fixed the updater download button by opening release URLs through the local Companion service first, with the MarginNote bridge kept as a fallback.
- Added visible in-progress feedback while checking GitHub Releases so the update check no longer appears unresponsive.

## 0.4.10 - 2026-06-23

### Fixed

- Fixed the proxy setting for Codex CLI runs by injecting `HTTP_PROXY`, `HTTPS_PROXY`, and `ALL_PROXY` into the CLI subprocess environment.
- Kept local Companion traffic out of the proxy with `NO_PROXY=127.0.0.1,localhost,::1`.

## 0.4.9 - 2026-06-23

### Fixed

- Fixed Stop so it actually terminates the active Codex CLI generation process instead of only setting a stop flag.
- Fixed queued generation cancellation by sending the active queue id from the web panel, clearing the web busy lock, and acknowledging the cancelled queue item.
- Fixed stopped runs being shown as ordinary failures; stopped generations now freeze as `已停止` and do not continue writing cards or mind maps.

## 0.4.8 - 2026-06-23

### Fixed

- Fixed the MarginNote toolbar icon so it uses a transparent template-mask asset instead of rendering as a filled black block.

## 0.4.7 - 2026-06-23

### Added

- Added the new GPT-image2-directed Codex Companion logo assets and replaced the MarginNote toolbar icon.

## 0.4.6 - 2026-06-23

### Changed

- Changed the update action from in-plugin install to opening the GitHub Release download page, avoiding macOS Full Disk Access requirements for self-updates.

## 0.4.5 - 2026-06-23

### Changed

- Published a maintenance release to let `0.4.4` installations test the visible update install flow.

## 0.4.4 - 2026-06-23

### Fixed

- Fixed the update install button feeling unresponsive by showing immediate download/install feedback before the long request returns.
- Fixed failed background installs staying stuck in `installing`; permission errors in the install log now surface as a visible update error.
- Added a write-permission preflight before running the installer so missing Full Disk Access is reported directly.

## 0.4.3 - 2026-06-23

### Changed

- Published a maintenance release to verify the in-plugin GitHub Release update flow from `0.4.2` to `0.4.3`.

## 0.4.2 - 2026-06-23

### Fixed

- Fixed update checks failing with GitHub API rate-limit errors by checking the public GitHub release page and lazy-loaded release assets before falling back to the REST API.

## 0.4.1 - 2026-06-23

### Added

- Added a GitHub Release update center in settings, with a main-chat update notice when a newer release is available.
- Added release zip validation and background installer launch for plugin updates, using `LiuWhale/marginnote-assistant` as the default repository.

### Changed

- Streamlined the settings page to keep only active user-facing controls: AI backend, model/speed/proxy, OpenAI key, context scope, connection state, permissions, PDF cache, health check, and native capability refresh.
- Removed currently unused settings-page controls for queue/history management, uploaded file context, custom-button management, release/evidence diagnostics, and the local placeholder backend option.
- Kept deeper diagnostics, release acceptance, package smoke tests, queue internals, and automation endpoints available for scripts and development workflows.

## 0.4.0 - 2026-06-23

### Added

- Built-in-AI-style chat surface with the send box fixed in the main interface.
- Dedicated settings page for AI backend, model, speed, proxy, OpenAI key, permissions, runtime state, diagnostics, queue controls, file context, and custom prompt buttons.
- Explicit context scope control: automatic, selection/node only, and full-document retrieval.
- Reviewable AI edit operation for adding answers or card trees into the mind map; rejecting removes the newly added branch.
- Structured full-document mind-map generation prompt with deeper Markdown hierarchy and coverage statistics.
- Runtime setting `defaultContextScope`, persisted and sanitized in Companion.
- `runtime_config.py` module for shared runtime defaults and settings sanitizers.
- Public README, MIT license, changelog, `.gitignore`, and cover-art asset location for open-source release.

### Changed

- Main UI keeps only the chat experience plus minimal status/context controls; advanced controls moved behind the gear button.
- Custom prompt buttons are managed from settings and may be pinned to the main surface up to the configured limit.
- Generated content no longer falls back to built-in template answers when real AI is unavailable.
- Package version moved from the 0.3.x RC line to `0.4.0`.
- Release packaging now treats open-source metadata as first-class package-root files.

### Fixed

- Saved default context scope now survives settings reloads and normalizes Chinese aliases such as `全文`.
- Queue/status controls are no longer mixed into the main chat surface.
- Custom button deletion path remains reachable after UI simplification.
- Markdown mind-map parsing preserves deeper heading hierarchy into nested MarginNote nodes.

### Release Notes

- This release can be packaged and smoke-tested locally.
- Public GitHub publishing still requires adding a remote that the maintainer controls.
- Signed and notarized macOS `.pkg` release still requires Developer ID Installer and Apple notarization credentials.

## 0.3.11 RC - 2026-06-12

### Added

- MarginNote WebView panel, local Companion service, queue system, card/mind-map draft writing, runtime diagnostics, release acceptance tooling, and native highlight evidence workflows.

### Notes

- This line was an internal release-candidate series used to validate MarginNote native API behavior and packaging gates.
