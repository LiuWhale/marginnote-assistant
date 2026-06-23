# Changelog

All notable changes to Codex Companion are documented here.

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
