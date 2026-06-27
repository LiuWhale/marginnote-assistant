# Release Status Matrix

This matrix prevents two mistakes:

- Treating the current public preview as a final v1.0 release.
- Treating the current Agent Workspace slices as the finished v3 MarginNote Knowledge Agent OS.

Current release candidate: `0.4.40` public preview.

Current UI shell: `Chat Mode` plus first-stage `Agent Workspace`. The runtime-required Knowledge OS anchors are:

- `knowledgeConsolePanel`
- `studioCanvasPanel`
- `operationLedgerDrawer`
- `sourceRegistryPanel`
- `verificationReportPanel`
- `externalGatewayPanel`
- `skillCenterPanel`

These anchors are required by WebView static tests, `doctor.py`, and `single_document_acceptance.py`. A deployed runtime that does not report them is stale or incomplete.

## Kernel Matrix

| Area | Implemented now | First-stage boundary | Verification | Preview / final impact |
| --- | --- | --- | --- | --- |
| Live MN Object Kernel | `object_kernel.py` builds `codex.mn.mnObject.v1` objects, persists scoped `codex.mn.mnObjectRegistry.v1`, and ingests native scan evidence. | Still a first-stage registry, not full live Finder-style notebook browsing. | `tests.test_object_kernel`, Object Browser static/runtime gates, `native_object_scan` evidence. | Required for Knowledge OS claims; public preview can ship with first-stage registry if documented. |
| Source Registry action evidence | `source_registry.py` builds `codex.mn.sourceRegistry.v1` from current MN document, cached PDFs, explicit file paths, uploads, and file search roots. Source actions record `codex.mn.sourceRegistryActionRun.v1`. | Does not yet provide full cross-notebook source fabric or automatic permission repair. | `tests.test_source_registry`, `notebookWorkspaceSourceActions`, `sourceRegistryPanel`, single-document web control gate. | Required for reliable full-document workflows; missing readable sources should block full-document claims, not preview installation. |
| External Automation Gateway v2 | `external_gateway.py` normalizes external URL/API requests, strips secrets, rejects direct write/delete requests, and records callback lifecycle evidence. | External systems can start workflow requests; they still cannot bypass dry-run, confirmation, ledger, or rollback. | `tests.test_external_gateway`, `/external/workflow/start`, `/external/callback/success`, `/external/callback/error`, Operation Ledger external evidence. | Required before advertising external automation. Preview can expose it as local automation gateway. |
| Transactional Native Editor | AI edit transaction evidence separates note and card IDs for create/delete/failure/residual proof. Reject paths no longer count unsupported card cleanup as clean rollback. | Native object deletion/probe coverage is still incomplete; residual proof can remain `UNKNOWN` without native probe. | `tests.test_transaction_manager`, `tests.test_native_transaction_static`, Operation Ledger transaction detail, `codex.mn.residualProof.v1`. | Required for write safety claims. Final/v3 claims need stronger native probe evidence. |
| Workflow Runtime v2 | `workflow_engine.py` persists workflow runs, step state, next-step inspection, resume, retry, cancel, and event evidence. Web Run Inspector exposes steps and recovery actions. | It is a workflow state-machine slice, not a full visual Workflow Builder. | `tests.test_workflow_engine`, `workflowRunInspectorPanel`, `workflow_next_step`, `workflow_resume`, `workflow_retry_step`. | Required for replacing queue-only behavior. Preview can ship as workflow runtime slice. |
| Skill Runtime v2 | `skill_marketplace.py` validates `codex.mn.skillManifest.v1`, rejects unsafe write/delete manifests, installs valid skills, builds dry-run-first operation plans, and records `codex.mn.skillRun.v1`. | Skill packages are local and first-stage; not yet a full marketplace with upgrade/migration UI. | `tests.test_skill_marketplace`, `skillCenterPanel`, `skill_operation_plan`, `skill_run_record`, `skill_run_latest`. | Required before calling custom prompts "skills". Preview can expose local validated skills. |
| Verification Agent | `verification_agent.py` returns `codex.mn.verificationReport.v1` with strict `PASS`, `FAIL`, or `UNKNOWN` for transactions, source registries, workflow runs, and skill runs. Operation Ledger details include verification reports for workflow/transaction entries. | Without native object probe, transaction presence is `UNKNOWN`, not `PASS`. A visual Verification Center is still future work. | `tests.test_verification_agent`, Operation Ledger details, `release_acceptance.evaluate_acceptance(final_claim=True, verification_reports=[...])`. | Public preview is unaffected. Any final/v3 claim requires at least one current-document `PASS` `codex.mn.verificationReport.v1`. |

## Current Required Gates

| Gate | Required evidence | Current release decision |
| --- | --- | --- |
| Runtime shell | Current MN4 WebView reports the Knowledge OS anchors above. | Required for the preview package to be considered installed correctly. |
| Single document acceptance | `Collect Single Document Acceptance.command`, `single_document_acceptance.py`, `single_document_acceptance_summary`, `singleDocumentAcceptanceButton`, and the settings-page `本文档验收` entry produce/consume same-topic evidence. | Required before final v1.0. Public preview can ship while this remains documented as pending. |
| Native visible highlight | Same-topic native highlight event and `ZHIGHLIGHTS` blob evidence. | Still a hard blocker for final v1.0. |
| Signed/notarized pkg | Developer ID Installer signature, notarization, stapled ticket, Gatekeeper install assessment. | Hard blocker for final installer release. |
| Cross-machine install | Structured second-user/second-machine evidence with matching artifact hash and install doctor checks. | Hard blocker for final release. |
| final/v3 claim | `final_claim=True` release acceptance plus a current-document `PASS` `codex.mn.verificationReport.v1`. | Required before calling the product final v3. |

## One-Shot Goal Boundary

One-shot goals remain 一次性长任务. They do not save as persistent long-term context and 不会保存成长期当前目标. Ordinary chat, card generation, and mind-map generation must not inherit an old one-shot goal.

## Verification Commands

```bash
python3 -m unittest \
  tests.test_object_kernel \
  tests.test_source_registry \
  tests.test_external_gateway \
  tests.test_transaction_manager \
  tests.test_workflow_engine \
  tests.test_skill_marketplace \
  tests.test_verification_agent \
  tests.test_web_controls_static \
  tests.test_doctor_checks \
  tests.test_single_document_acceptance \
  tests.test_release_docs
```

```bash
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
git diff --check
```

## Current Blockers

Current `0.4.40` work is still a public preview, not final v1.0 or v3:

- Native visible highlight evidence is still required for final release.
- Same-topic single-document PASS evidence is still required.
- Signed and notarized pkg evidence is still required.
- Cross-machine install evidence is still required.
- Full v3 still needs a complete Notebook Knowledge IDE, cross-document Knowledge Graph Studio, visual Workflow Builder, visual Verification Center, and stronger native object probe coverage.
