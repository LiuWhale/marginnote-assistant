# Changelog

All notable changes to Codex Companion are documented here.

## 0.4.27 - 2026-06-25

### Added

- Built and published a native MarginNote add-on bundle, `CodexCompanion-<version>-latest.mnaddon`, alongside the full installer zip.
- Added `.mnaddon` smoke checks so release validation verifies that `main.js`, `mnaddon.json`, WebView files, and the icon are at the archive root rather than nested under `codex.mn.assistant/`.
- Added `.mnaddon` entries to release SHA256 manifests and OneDrive release mirroring.

## 0.4.26 - 2026-06-25

### Fixed

- Retried transient Codex CLI startup failures when the CLI reports `timed out waiting for cloud config bundle after 15s`, and replaced the raw error with an actionable proxy/login/network message.
- Clarified the settings readiness wording: finding a Codex CLI or OpenAI key is now shown as "AI backend discovered" rather than proof that generation has already succeeded.
- Fixed the bottom send button so its built-in `发送 / 可排队` two-line label is not duplicated by the global busy-state `可排队` pseudo-label.

## 0.4.25 - 2026-06-24

### Changed

- Split the GitHub README into an English default `README.md` and a full Chinese `README.zh-CN.md`, with language links at the top of both files.
- Added `README.zh-CN.md` to release packaging and release smoke checks so distributed zips include both languages.
- Extracted diagnostic log sanitizing, pruning, reading, and clearing into `diagnostic_log.py`, keeping the existing Companion API while shrinking `companion.py`.

## 0.4.24 - 2026-06-24

### Fixed

- Centered the bottom send button label and split it into two lines, `发送` and `可排队`, so the queue hint stays readable in narrow MarginNote panel widths.
- Bumped the WebView resource cache key so MarginNote reloads the updated send-button layout after installing the release.

## 0.4.23 - 2026-06-24

### Added

- Added a persistent top-of-chat target mindmap selector with green/yellow/red status, so generated mindmaps are explicitly tied to the current document or the selected MN node before writing.
- Added Companion-side per-document mindmap target bindings in `control/mindmap-targets.json`; document targets use stable `mindmap-target:<hash>` root IDs so later generations append to the same Codex mindmap root.

### Fixed

- Reused an existing document mindmap root by appending generated children instead of skipping the whole write when the root already exists.
- Added native write-target validation for selected-node mindmap writes, preventing a stale target from silently creating or merging into the wrong location.

## 0.4.22 - 2026-06-24

### Added

- Added Companion-side direct PDF caching before falling back to MarginNote native upload, so readable local or cloud PDFs can be cached without waiting for the MN4 plugin process.
- Added a manual "choose PDF to cache" fallback in the chat footer and configuration page. This lets the Web panel upload the selected PDF bytes directly to Companion when macOS blocks LaunchAgent access to OneDrive or iCloud paths.

### Fixed

- Kept the native MN4 cache queue as a fallback only when Companion cannot read or receive the PDF bytes directly.
- Removed the old personal OneDrive default path list from production code; automatic lookup now uses generic CloudStorage provider scanning plus user-managed file roots.

## 0.4.21 - 2026-06-24

### Added

- Added automatic current-document PDF cache requests after the Web panel receives MarginNote context with `topicid` and `bookmd5`.
- Automatic PDF caching is deduplicated per document and skips documents that are already cached or waiting for native MN4 upload.

## 0.4.20 - 2026-06-24

### Fixed

- Kept the bottom PDF cache status light visible even before the current document is recognized or cached, using a grey idle state instead of hiding the indicator.
- Updated the WebView resource cache key so MarginNote reloads the always-visible cache light UI.

## 0.4.19 - 2026-06-24

### Changed

- Moved the current-document PDF cache status indicator to the bottom composer area so it stays visible while chatting.
- Added persistent cache status lights: yellow while MN4 is caching the PDF, green after the cache is ready, and red when caching or PDF access fails.
- The bottom cache light now also follows MarginNote native status messages such as PDF upload started, completed, or failed.

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
