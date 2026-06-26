# Changelog

All notable changes to Codex Companion are documented here.

## Unreleased

## 0.4.39 - 2026-06-27

### Added

- Added a first `Source Registry Action Plan` to `notebook_workspace`. The registry now returns `codex.mn.sourceRegistryActionPlan.v1` plus `sourceActions` for caching the current PDF, choosing a local PDF file, opening file-path management, and refreshing MarginNote context.
- Added visible Source Registry action buttons in the Notebook Workspace through `notebookWorkspaceSourceActions`.
- Promoted `notebookWorkspaceSourceActions` to required WebView/runtime controls in doctor and single-document acceptance checks.

### Changed

- Source Registry is now an actionable workspace component instead of a status-only panel. When full-document material is missing, the Study Program gap points directly to the recommended source action.

## 0.4.38 - 2026-06-27

### Added

- Added the first `Source Registry` kernel to `notebook_workspace`. The workspace now returns `codex.mn.sourceRegistry.v1`, unifying the current MarginNote document, explicit PDF paths, cached PDFs, uploaded files, and configured file search roots into source objects with readability status and evidence.
- Added a visible `Source Registry` panel to Notebook Workspace with `notebookWorkspaceSources`, `notebookWorkspaceSourceRegistry`, `notebookWorkspaceSourceSummary`, and `notebookWorkspaceSourceList`.
- Connected Study Program coverage to Source Registry. If there is no readable PDF cache, explicit PDF path, or uploaded material, Study Program reports a `source_registry` gap instead of pretending the document is readable.
- Separated total uploads from readable uploads, so a stale upload record no longer makes full-document workflows look ready.

### Changed

- Promoted material readability from a settings/path-management concern into the notebook-first workspace. This moves the product closer to v3 Source Registry behavior and keeps file/PDF/cache state visible before any chat prompt or workflow execution.

## 0.4.37 - 2026-06-27

### Added

- Added `codex.mn.studyProgram.v1` to `notebook_workspace`. Notebook Workspace now returns a zero-message Study Program with coverage scores, concrete gaps, and recommended workflows before the user types a prompt.
- Added the visible `Study Program` panel to the Notebook Workspace first screen. It shows object, mind-map, review-card, workflow, and ledger gaps, then offers direct workflow recommendations such as `paper_deep_reading`, `mindmap_reorganize`, and `selection_to_cards`.
- Promoted `notebookWorkspaceStudyProgram`, `notebookWorkspaceStudyCoverage`, `notebookWorkspaceStudyGaps`, and `notebookWorkspaceStudyRecommendations` to required WebView/runtime controls in doctor and single-document acceptance checks.

### Changed

- Moved the v3 transition one step closer to a zero-message Notebook Knowledge OS: opening a document can now produce a learning plan and executable workflow recommendations without first asking a chat question.

## 0.4.36 - 2026-06-27

### Added

- Added `notebook_runbook_preflight_record` and schema `codex.mn.notebookRunbookPreflightRun.v1`. Notebook Runbook AutoPlan now records running/completed/failed preflight runs with `writePolicy=no_write_preflight`, action counts, event history, and the safe action list.
- Added `autoPlan.latestRun` to `codex.mn.notebookRunbookAutoPlan.v1`, plus the visible `notebookWorkspaceRunbookAutoStatus` line in Notebook Workspace. Users can see whether the latest AutoPlan preflight is idle, running, completed, failed, or cancelled.
- Added `notebook_runbook_preflight` entries to Operation Ledger list/detail, including verification evidence that the preflight did not perform MarginNote writes.

### Changed

- Sharpened the v3.0 design boundary: the ultimate product must support zero-message notebook workflows, live object kernels, transactional native editing, source registry, workflow runtime, connector gateway, skill runtime, and verification agent behavior instead of only improving the current chat, buttons, settings, queue, and logs.

## 0.4.35 - 2026-06-27

### Added

- Added `autoPlan` to `codex.mn.notebookRunbook.v1` with schema `codex.mn.notebookRunbookAutoPlan.v1`. The plan groups safe preflight actions such as native MN object scanning, mind-map baseline reading, and operation planning without performing writes.
- Added the visible `notebookWorkspaceRunbookAutoButton` in Notebook Workspace. It runs the safe preflight plan sequentially through existing workspace actions and keeps write operations behind the existing Diff, confirmation, and ledger gates.

## 0.4.34 - 2026-06-27

### Added

- Added `nextStep` and `continueAction` to `codex.mn.notebookRunbook.v1`, plus the visible `notebookWorkspaceRunbookContinueButton`. The workspace now has a single "continue next step" entry that chooses the first actionable runbook gap instead of forcing the user to inspect every row.
- Added registry evidence counting for `MNObject Registry`, so the notebook runbook can distinguish objects imported from cached mind-map trees from objects confirmed by a native MarginNote scan.

### Changed

- Tightened the "scan MN objects" runbook step: it is only ready after `native_object_scan` evidence exists. Cached mind-map nodes still appear in Object Browser, but they no longer make the native scan step look complete.
- Runbook continuation now prioritizes `action_required` steps, then `pending` steps, and only falls back to blocked steps when nothing else can be executed.

## 0.4.33 - 2026-06-27

### Added

- Added the first `Notebook Runbook` inside `Notebook Workspace`. The Companion now returns `codex.mn.notebookRunbook.v1` from `notebook_workspace`, turning the notebook overview into an executable checklist for context scope, native MN object scanning, mind-map baseline reading, operation planning, workflow runtime, and Operation Ledger evidence. Each step carries status, evidence, and an action that drives the existing object scan, mind-map read, operation plan, workflow, or ledger surface.
- Promoted the runbook to a required WebView/runtime surface by adding dedicated `notebookWorkspaceRunbook`, `notebookWorkspaceRunbookSummary`, and `notebookWorkspaceRunbookList` controls to the panel, static checks, doctor checks, and single-document acceptance control list.

## 0.4.32 - 2026-06-27

### Changed

- Moved the chat stream out of the Agent Workspace tab set into a dedicated `Command Pane`. In Workspace mode the command pane keeps the prompt and send button available but collapses the conversation history by default, so `Notebook Workspace`, object, operation, knowledge, and workflow surfaces become the primary working area. `Chat Mode` still opens the full conversation for lightweight reading Q&A.

## 0.4.31 - 2026-06-27

### Added

- Added the first Notebook Workspace summary surface. The Companion exposes `notebook_workspace` with `codex.mn.notebookWorkspace.v1`, aggregating the current focus object, Object Browser counts, mind-map tree cache, review queue, workflow runs, and Operation Ledger counts into one workspace payload. The WebView now renders this as a first-screen Agent Workspace overview with direct actions for MN object scanning, mind-map tree reading, operation planning, review queue, workflows, and ledger inspection.

## 0.4.30 - 2026-06-27

### Changed

- Tightened runtime and release acceptance gates so `native-mn-object-registry-scan-v1`, `native-mn-object-existence-probe-v1`, `native-mindmap-diff-apply-create-v1`, and `native-mindmap-delete-suggestion-confirm-v1` are all required native handler features, matching the v2 object workbench capabilities declared by the MarginNote add-on.

## 0.4.29 - 2026-06-27

### Added

- Added the first Operation Compiler surface: `agent_plan` now returns `codex.mn.operationPlan.v1`, `codex.mn.verificationPlan.v1`, and `codex.mn.operationCompiler.v1`, and the operation workspace renders planned steps, write count, verification status, compiler checks, and blocking reasons.
- Added Operation Compiler controls to doctor, Web static checks, and single-document acceptance so the structured plan layer is treated as a required runtime surface rather than hidden JSON.
- Moved native capability dry-run forward into `agent_plan`: write-capable workflow plans now reuse the operation dry-run gate before a draft exists, so missing required native capabilities can block the plan instead of failing only at final write time.
- Gated Agent Workspace and reply next-action buttons with Operation Compiler status: write-capable or confirmation actions are disabled when the compiler reports blocked or unknown dry-run/capability state, while read-only actions remain available.
- Added first-stage Operation Compiler repair actions: blocked plans can now surface actionable recovery buttons such as refreshing MarginNote native capabilities, opening settings, or caching the current PDF.
- Added first-stage per-operation dry-run evidence for mind-map operations: `operationDryRunDetails` now shows each planned node operation's mutation, noteId, required capability, status, reason, and verification level, and blocked local Diff apply responses return the same `codex.mn.perOperationDryRun.v1` payload.
- Added `codex.mn.residualProof.v1` to AI edit transaction verification, so rollback/retain evidence can report each created or target note's expected state, actual state, residual flag, and native-event evidence level instead of only a residual count.
- Added native MN object existence probing for edit transactions: Companion can enqueue `probe_mn_object_existence`, the MarginNote handler checks real note objects by `noteId`, and transaction verification uses the probe to report confirmed residual objects instead of relying only on deleted/failed counts.
- Added a visible AI edit transaction action for native object existence probes: when verification still depends on delete counts or failed rollback events, the transaction center now exposes `检查真实对象` and requests `request_mn_object_existence_probe`.

### Changed

- Reframed the v3.0 ultimate design as `Notebook Knowledge OS`: the default end-state is a Notebook Workspace plus workflow-based learning agent, not a stronger chat page with more buttons.
- Split the long-term roadmap into explicit product stages: `v0.4.x` Chat Companion, `v1.x` Study Copilot, `v2.x` Native Knowledge Editor, and `v3.x` Notebook Knowledge OS, so current Agent Workspace panels cannot be mistaken for the final Knowledge IDE.

## 0.4.28 - 2026-06-27

### Added

- Added the first visible dual-mode shell: the WebView now has `Chat Mode` for lightweight reading conversation and `Agent Workspace` for object, operation, knowledge, and workflow workspaces. Switching to chat focuses the dialog panel; switching to workspace restores the last non-chat workspace pane.
- Added the first `Workspace Navigator` in Agent Workspace, exposing `Knowledge Console`, `Mindmap Studio`, `Card Factory`, `Operation Ledger`, `Knowledge Graph`, `Workflow Builder`, and `Skill Center` as first-class product entries instead of hidden tab details.
- Added the first operational `Mindmap Studio` panel. It is not a renamed answer button: the operation workspace now exposes `读取现有脑图`, `预览 Diff`, `应用所选`, `验证事务`, and `回滚事务`, and summarizes the current tree, latest Diff, apply status, and transaction state in one place.
- Added External Automation Gateway callback ledger updates: `POST /external/callback/success` and `POST /external/callback/error` now update the matching request ledger with callback status, payload, history, and received count.
- Added the first Knowledge Console risk panel: `agent_plan` now returns `codex.mn.riskRegister.v1` with permission, context scope, target mind map, dry-run, and confirmation risk items, and the object workspace renders those items before Object Browser, Graph, Activity, and Ledger.
- Added the first object-scoped Object Browser: `object_browser` aggregates the current focus `MNObject`, Object Graph nodes, Object Activity items, and Operation Ledger entries into a browsable object list with per-object actions. The Web object workspace now has an Object Browser panel above Object Graph.
- Added Object Browser filtering: the Web object workspace now exposes object type, kind, and keyword controls, and `object_browser` returns `filters`, `filteredTotal`, and `unfilteredTotal` so users can narrow the current object list without leaving the Knowledge Console.
- Added the first persistent `MNObject Registry`: `mn_object_registry` stores seen MarginNote objects as `codex.mn.mnObjectRegistry.v1` entries, registers manual relation endpoints, ingests native `mindmapTreeReadFinished` tree-cache nodes as `mnobj:note:<noteId>` objects, and lets Object Browser show a Registry group alongside graph, activity, and ledger objects.
- Added active native object scanning for the Object Browser: `objectRegistryScanButton` / `扫描 MN` calls `request_mn_object_registry_scan`, enqueues `scan_mn_objects`, ingests `mnObjectRegistryScanFinished` payloads as `native_object_scan` evidence in `MNObject Registry`, promotes scanned notes into Object Graph as `mn_note` nodes with `native_object_scan` parent-child `contains` edges, and lets clicking a scanned registry object open that object's graph, activity feed, and ledger with its own `mnObject` payload.
- Added the first Card Factory metadata layer: `generate_card` and full-reading card generation now return a `codex.mn.cardFactory.v1` summary, add `cardType`, source, `learningGoal`, `reviewPrompt`, and `codex.mn.cardFactoryCard.v1` metadata to each generated card, preserve `card_factory` in saved drafts, and show card type/source/length/duplicate-title quality signals in the AI edit confirmation panel.
- Added the first Card Factory Review Queue: `review_queue_add/list` stores deduplicated draft cards as `codex.mn.reviewQueue.v1`, scopes queue entries by topic/book/current `MNObject`, adds a `加入复习队列` action to the AI edit confirmation panel, and shows queued review cards in the Knowledge workspace.
- Added the first object-scoped Object Graph: `object_graph` links the current `MNObject` to related conversations, workflow runs, AI edit transactions, external gateway requests, diagnostic logs, Knowledge Index entities/relations, and cached native MarginNote mind-map tree nodes with `contains` relationships. The Web object workspace now shows these graph nodes as navigation into evidence.
- Added the first editable Object Graph relationship layer: `object_graph_relation_save/delete` persists user-maintained `manual_relation` edges between `MNObject` IDs, records saved/deleted events as `object_graph_manual_relation` Operation Ledger entries with `manualRelation` evidence, and surfaces those relationship events in Object Activity. The Web object workspace now includes a compact relationship editor and opens the relationship ledger detail from the activity feed.
- Added an object-scoped Operation Ledger API and Web panel: `operation_ledger_list/get` aggregates workflow runs, AI edit transactions, external gateway requests, and manual Object Graph relationship events for the current `MNObject`, and selecting a ledger item now opens an object-workspace evidence panel with transaction verification, native command/event timeline, operation-chain evidence, workflow confirmation state, external callback evidence, and manual relationship evidence.
- Added Operation Ledger filtering: the Web object workspace now exposes entry type, status, and keyword controls, and `operation_ledger_list` returns `filters`, `filteredTotal`, and `unfilteredTotal` so users can narrow audit evidence without scrolling through unrelated workflow, transaction, external, or manual-relation entries.
- Added the first recoverable Workflow Run Inspector: `workflow_status` now returns `codex.mn.workflowRunInspector.v1` with per-step status, tone, queue IDs, confirmation points, next actions, and retry metadata. The Workflow Runtime page can open a recent run, inspect each step, and retry recoverable failed/blocked direct or queueable steps without jumping back into the chat stream.

### Changed

- Rewrote the ultimate design boundary as a dual-mode product: `Chat Mode` remains the lightweight reading conversation, while `Agent Workspace Mode` becomes the object-first, operation-first, evidence-first production system instead of a larger chat panel with more buttons.

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
