# Knowledge Agent OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Chat Companion + Agent Workspace preview into the first real slice of the MarginNote Knowledge Agent OS by extracting object, source, workflow, automation, skill, and verification kernels from the current monolithic Companion service.

**Architecture:** Keep the existing WebView, Companion HTTP API, native MarginNote bridge, and release pipeline. Move v3 kernels into focused Python modules with schema-stable APIs, then let `companion.py` become an adapter layer. Each slice must add object-level evidence, Operation Ledger visibility, and tests before UI expansion.

**Tech Stack:** Python 3 standard library, existing `unittest` suite, MarginNote add-on JavaScript under `extension/codex.mn.assistant`, local JSON stores under `~/.codex/marginnote-assistant`, existing package/release scripts.

---

## Current Boundaries

The current repository already contains useful first-stage surfaces:

- `agent_workbench.py`: MNObject detection, agent operation, risk and compiler primitives.
- `operation_runtime.py`: mind-map Diff, card quality, operation manifest and dry-run primitives.
- `workflow_engine.py`: static workflow templates and preview logic.
- `skill_marketplace.py`: built-in skill manifest and install state.
- `transaction_manager.py`: AI edit transaction summaries and rollback evidence.
- `knowledge_index.py`: first-stage local knowledge entities and relations.
- `companion.py`: HTTP/action handler plus large embedded implementations for Source Registry, Notebook Workspace, External Gateway, Operation Ledger, Object Graph, Object Browser, and MNObject Registry.
- `extension/codex.mn.assistant/web/app.js`: current UI rendering for Notebook Workspace, Object Workspace, Operation Compiler, Workflow, Skill and Ledger panels.

The next engineering step is not to add more buttons. It is to move the v3 kernels out of `companion.py`, make their outputs schema-stable, and make every user-visible object/action carry evidence that can be inspected.

External automation should borrow the protocol shape from the public `url-api-marginnote` project: a fixed `marginnote4app://addon/api?...` entry, `requestId`, `secret`, `x-success`, `x-error`, permission groups, anti-replay, and note actions such as `read`, `ls`, `find`, `tree`, `write`, and `delete`. Codex Companion must not copy the dangerous part as direct write access; it should translate external calls into `agentOperation` or workflow runs that still pass dry-run, confirmation, Operation Ledger, and rollback checks.

---

### Task 1: Extract Live MN Object Kernel

**Files:**
- Create: `object_kernel.py`
- Modify: `companion.py`
- Test: `tests/test_object_kernel.py`
- Update docs if needed: `docs/ULTIMATE_PLUGIN_DESIGN.md`

- [x] **Step 1: Write the failing kernel tests**

Create `tests/test_object_kernel.py` with tests for stable object IDs, registry persistence, native scan ingestion, and scope filtering.

```python
import tempfile
import unittest
from pathlib import Path

import object_kernel


class ObjectKernelTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        object_kernel.configure(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_registers_selection_with_stable_object_id(self):
        payload = {
            "topicid": "T1",
            "bookmd5": "B1",
            "selectionText": "Attention mask evidence",
            "documentTitle": "Paper.pdf",
            "page": 3,
        }
        first = object_kernel.build_object(payload)
        second = object_kernel.build_object(payload)
        self.assertEqual(first["schema"], "codex.mn.mnObject.v1")
        self.assertEqual(first["objectId"], second["objectId"])
        self.assertEqual(first["kind"], "selection")
        self.assertEqual(first["sourceRef"]["page"], 3)

    def test_ingests_native_scan_nodes_as_registry_objects(self):
        result = object_kernel.ingest_native_scan(
            {
                "topicid": "T1",
                "bookmd5": "B1",
                "nodes": [
                    {"noteId": "n1", "title": "Root", "parentNoteId": ""},
                    {"noteId": "n2", "title": "Child", "parentNoteId": "n1"},
                ],
            }
        )
        self.assertEqual(result["schema"], "codex.mn.mnObjectRegistryScan.v1")
        self.assertEqual(result["ingestedCount"], 2)
        registry = object_kernel.registry_list({"topicid": "T1", "bookmd5": "B1"})
        object_ids = {item["objectId"] for item in registry["objects"]}
        self.assertIn("mnobj:note:n1", object_ids)
        self.assertIn("mnobj:note:n2", object_ids)
        self.assertIn("native_object_scan", registry["objects"][0]["evidenceTypes"])
```

- [x] **Step 2: Run the failing test**

Run:

```bash
python3 -m unittest tests.test_object_kernel
```

Expected: import or attribute failure because `object_kernel.py` does not exist.

- [x] **Step 3: Implement `object_kernel.py`**

Implement:

```python
MN_OBJECT_SCHEMA = "codex.mn.mnObject.v1"
MN_OBJECT_REGISTRY_SCHEMA = "codex.mn.mnObjectRegistry.v1"
MN_OBJECT_REGISTRY_SCAN_SCHEMA = "codex.mn.mnObjectRegistryScan.v1"

def configure(root: Path | str) -> None: ...
def build_object(payload: dict[str, Any]) -> dict[str, Any]: ...
def register_object(obj: dict[str, Any], evidence_type: str = "observed") -> dict[str, Any]: ...
def ingest_native_scan(payload: dict[str, Any]) -> dict[str, Any]: ...
def registry_list(payload: dict[str, Any]) -> dict[str, Any]: ...
def object_scope_key(topicid: str, bookmd5: str) -> str: ...
```

Use deterministic object IDs:

- Native notes: `mnobj:note:<noteId>`.
- Documents: `mnobj:document:<sha1(topicid|bookmd5|documentTitle)>`.
- Selections: `mnobj:selection:<sha1(topicid|bookmd5|page|selectionText)>`.
- Unknowns: `mnobj:unknown:<sha1(payload)>`.

Store under `ROOT / "mn-object-registry" / "<scope>.json"` with objects sorted by `lastSeen` descending.

- [x] **Step 4: Wire `companion.py` to the kernel**

Replace local registry functions in `companion.py` with thin calls to `object_kernel`. Keep public action names stable:

- `mn_object_registry`
- `request_mn_object_registry_scan`
- `object_browser`
- `object_graph`
- `object_activity`
- `operation_ledger_list`

Do not change JSON schema names returned to the WebView.

- [x] **Step 5: Run regression tests**

Run:

```bash
python3 -m unittest tests.test_object_kernel tests.test_companion_controls tests.test_release_docs tests.test_web_controls_static
```

Expected: all pass.

- [ ] **Step 6: Commit**

```bash
git add object_kernel.py companion.py tests/test_object_kernel.py docs/ULTIMATE_PLUGIN_DESIGN.md
git commit -m "refactor: extract live MN object kernel"
```

---

### Task 2: Extract Source Registry and Action Evidence

**Files:**
- Create: `source_registry.py`
- Modify: `companion.py`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/index.html`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Modify: `doctor.py`
- Modify: `single_document_acceptance.py`
- Test: `tests/test_source_registry.py`
- Test: `tests/test_web_controls_static.py`
- Test: `tests/test_doctor_checks.py`
- Test: `tests/test_single_document_acceptance.py`

- [x] **Step 1: Write the failing backend tests**

Create `tests/test_source_registry.py`.

```python
import tempfile
import unittest
from pathlib import Path

import source_registry


class SourceRegistryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        source_registry.configure(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_builds_registry_with_readable_cache_and_missing_reason(self):
        payload = {"topicid": "T1", "bookmd5": "B1", "documentTitle": "Paper.pdf"}
        registry = source_registry.build_registry(payload, caches=[], explicit_paths=[], uploads=[], roots=[])
        self.assertEqual(registry["schema"], "codex.mn.sourceRegistry.v1")
        self.assertEqual(registry["readableCount"], 0)
        self.assertIn("source_registry", registry["gaps"][0]["id"])

    def test_records_source_action_lifecycle(self):
        run = source_registry.record_action_run(
            {
                "topicid": "T1",
                "bookmd5": "B1",
                "actionId": "cache_current_pdf",
                "actionLabel": "缓存当前 PDF",
                "status": "running",
                "event": "started",
            }
        )
        self.assertEqual(run["sourceActionRun"]["status"], "running")
        done = source_registry.record_action_run({**run["sourceActionRun"], "status": "completed", "event": "completed"})
        self.assertEqual(done["sourceActionRun"]["status"], "completed")
        latest = source_registry.latest_action_run("T1", "B1")
        self.assertEqual(latest["status"], "completed")
```

- [x] **Step 2: Run the failing test**

Run:

```bash
python3 -m unittest tests.test_source_registry
```

Expected: import failure.

- [x] **Step 3: Implement `source_registry.py`**

Implement:

```python
SOURCE_REGISTRY_SCHEMA = "codex.mn.sourceRegistry.v1"
SOURCE_ACTION_PLAN_SCHEMA = "codex.mn.sourceRegistryActionPlan.v1"
SOURCE_ACTION_RUN_SCHEMA = "codex.mn.sourceRegistryActionRun.v1"

def configure(root: Path | str) -> None: ...
def build_registry(payload, caches, explicit_paths, uploads, roots) -> dict[str, Any]: ...
def build_action_plan(payload, registry) -> dict[str, Any]: ...
def record_action_run(payload) -> dict[str, Any]: ...
def latest_action_run(topicid: str, bookmd5: str) -> dict[str, Any]: ...
```

Action run records must include `runId`, `status`, `actionId`, `actionLabel`, `topicid`, `bookmd5`, `startedAt`, `updatedAt`, `event`, `message`, and `result`.

- [x] **Step 4: Add WebView status evidence**

Add a source action status line:

```html
<div id="notebookWorkspaceSourceActionStatus" class="notebook-source-action-status idle">来源动作：尚未运行</div>
```

Add JS helpers:

```javascript
function sourceRegistryActionStatusText(run) { ... }
function renderNotebookSourceActionStatus(run) { ... }
function recordSourceRegistryActionRun(item, status, result, done) { ... }
function runSourceRegistryTrackedAction(item, done) { ... }
```

Tracked actions must record `running`, then `completed` or `failed`, then refresh `notebook_workspace`.

- [x] **Step 5: Update static tests**

Add assertions in `tests/test_web_controls_static.py` for:

- `notebookWorkspaceSourceActionStatus`
- `recordSourceRegistryActionRun`
- `source_registry_action_record`
- `sourceRegistryActionStatusText`

- [x] **Step 6: Run regression tests**

```bash
python3 -m unittest tests.test_source_registry tests.test_web_controls_static tests.test_companion_controls
```

- [ ] **Step 7: Commit**

```bash
git add source_registry.py companion.py extension/codex.mn.assistant/web/index.html extension/codex.mn.assistant/web/app.js extension/codex.mn.assistant/web/app.css tests/test_source_registry.py tests/test_web_controls_static.py
git commit -m "feat: record source registry action evidence"
```

---

### Task 3: External Automation Gateway v2

**Files:**
- Create: `external_gateway.py`
- Modify: `companion.py`
- No change needed for this slice: `workflow_engine.py`
- Test: `tests/test_external_gateway.py`
- Update docs: `docs/ULTIMATE_PLUGIN_DESIGN.md`, `docs/PROGRAMMATIC_VERIFICATION.md`

- [x] **Step 1: Write gateway protocol tests**

Create `tests/test_external_gateway.py`.

```python
import tempfile
import unittest
from pathlib import Path

import external_gateway


class ExternalGatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        external_gateway.configure(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_rejects_direct_write_without_workflow(self):
        result = external_gateway.normalize_request(
            {
                "requestId": "req1",
                "caller": "shortcut",
                "secret": "mnsec_test",
                "action": "write",
                "payload": {"path": "@id:n1", "content": "direct write"},
            }
        )
        self.assertFalse(result["ok"])
        self.assertEqual(result["code"], "DIRECT_WRITE_FORBIDDEN")

    def test_accepts_workflow_request_with_callback(self):
        result = external_gateway.normalize_request(
            {
                "requestId": "req2",
                "caller": "shortcut",
                "secret": "mnsec_test",
                "action": "workflow_start",
                "x-success": "shortcuts://success",
                "x-error": "shortcuts://error",
                "payload": {"workflowId": "paper_deep_reading", "objectRef": {"objectId": "mnobj:document:x"}},
            }
        )
        self.assertTrue(result["ok"])
        operation = result["agentOperation"]
        self.assertEqual(operation["schema"], "codex.mn.agentOperation.v1")
        self.assertEqual(operation["external"]["requestId"], "req2")
```

- [x] **Step 2: Implement `external_gateway.py`**

Implement:

```python
EXTERNAL_REQUEST_SCHEMA = "codex.mn.externalGatewayRequest.v1"

def configure(root: Path | str) -> None: ...
def normalize_request(payload: dict[str, Any]) -> dict[str, Any]: ...
def record_request(record: dict[str, Any]) -> dict[str, Any]: ...
def update_callback(payload: dict[str, Any]) -> dict[str, Any]: ...
def request_status(payload: dict[str, Any]) -> dict[str, Any]: ...
```

Protocol fields:

- `requestId`: required unique caller ID.
- `caller`: required display name.
- `secret`: accepted but never echoed in status.
- `action`: allowed values `ping`, `read`, `ls`, `find`, `tree`, `workflow_start`, `agent_operation`.
- `x-success` and `x-error`: optional callbacks.
- `payload`: parsed object.

Direct `write` and `delete` must return `DIRECT_WRITE_FORBIDDEN` unless converted into a workflow requiring confirmation.

- [x] **Step 3: Wire Companion endpoints**

Keep existing endpoints stable:

- `/external/workflow/start`
- `/external/callback/success`
- `/external/callback/error`
- `external_gateway_start_workflow`
- `external_gateway_request_status`
- `external_gateway_callback`

`companion.py` should call `external_gateway.normalize_request`, create a workflow run, then store the gateway record.

- [x] **Step 4: Add Operation Ledger evidence**

Ensure `operation_ledger_list` and `operation_ledger_get` show:

- requestId
- caller
- action
- objectRef
- callback URLs with secrets stripped
- workflowRunId
- status
- callback history

- [x] **Step 5: Run tests**

```bash
python3 -m unittest tests.test_external_gateway tests.test_workflow_engine tests.test_companion_controls
```

- [ ] **Step 6: Commit**

```bash
git add external_gateway.py companion.py workflow_engine.py tests/test_external_gateway.py docs/ULTIMATE_PLUGIN_DESIGN.md docs/PROGRAMMATIC_VERIFICATION.md
git commit -m "feat: harden external automation gateway"
```

---

### Task 4: Transactional Native Editor Evidence

**Files:**
- Modify: `transaction_manager.py`
- No change needed for this slice: `operation_runtime.py`
- Modify: `companion.py`
- Modify: `extension/codex.mn.assistant/main.js`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Test: `tests/test_transaction_manager.py`
- Test: `tests/test_native_transaction_static.py`
- Test: `tests/test_web_controls_static.py`
- Test: `tests/test_companion_controls.py`

- [x] **Step 1: Write tests for residual proof completeness**

Extend `tests/test_transaction_manager.py`:

```python
def test_reject_report_distinguishes_outline_and_card_residuals(self):
    tx = transaction_manager.create_transaction(
        {
            "transactionId": "txn1",
            "createdNoteIds": ["n1", "n2"],
            "createdCardIds": ["c1"],
            "operationPlan": {"schema": "codex.mn.operationPlan.v1"},
        }
    )
    report = transaction_manager.record_rollback_result(
        "txn1",
        {
            "deletedNoteIds": ["n1"],
            "failedNoteIds": ["n2"],
            "deletedCardIds": [],
            "failedCardIds": ["c1"],
        },
    )
    residual = report["verification"]["residualProof"]
    self.assertEqual(residual["status"], "failed")
    self.assertIn("n2", residual["residualNoteIds"])
    self.assertIn("c1", residual["residualCardIds"])
```

- [x] **Step 2: Implement transaction evidence schema**

Add or normalize:

```python
TRANSACTION_SCHEMA = "codex.mn.operationTransaction.v1"
RESIDUAL_PROOF_SCHEMA = "codex.mn.residualProof.v1"
```

Every transaction summary must separate:

- `createdNoteIds`
- `createdCardIds`
- `updatedNoteIds`
- `movedNoteIds`
- `suggestedDeleteNoteIds`
- `deletedNoteIds`
- `deletedCardIds`
- `residualNoteIds`
- `residualCardIds`
- `verification.status`

- [x] **Step 3: Update native JS command contract**

In `extension/codex.mn.assistant/main.js`, ensure reject/rollback commands carry both outline IDs and card IDs. If native API cannot delete cards separately, return an explicit `unsupported` result instead of counting it as success.

- [x] **Step 4: Expose ledger detail**

`operation_ledger_get` must show card residuals and outline residuals separately.

- [x] **Step 5: Run tests**

```bash
python3 -m unittest tests.test_transaction_manager tests.test_native_transaction_static tests.test_operation_runtime
node --check extension/codex.mn.assistant/main.js
```

- [ ] **Step 6: Commit**

```bash
git add transaction_manager.py operation_runtime.py companion.py extension/codex.mn.assistant/main.js tests/test_transaction_manager.py tests/test_native_transaction_static.py
git commit -m "feat: separate note and card rollback evidence"
```

---

### Task 5: Workflow Runtime v2

**Files:**
- Modify: `workflow_engine.py`
- Modify: `companion.py`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Test: `tests/test_workflow_engine.py`
- Test: `tests/test_companion_controls.py`
- Test: `tests/test_web_controls_static.py`

- [x] **Step 1: Write tests for resumable runs**

Extend `tests/test_workflow_engine.py`:

```python
def test_workflow_run_can_resume_from_waiting_confirmation(self):
    run = workflow_engine.create_run({"workflowId": "paper_deep_reading", "objectRef": {"objectId": "mnobj:document:x"}})
    run = workflow_engine.update_step(run["runId"], "write", "waiting_confirmation", {"draftId": "draft1"})
    resumed = workflow_engine.next_runnable_step(run["runId"])
    self.assertEqual(resumed["status"], "waiting_confirmation")
    self.assertEqual(resumed["stepId"], "write")
```

- [x] **Step 2: Implement persisted workflow run store**

Add:

```python
def configure(root: Path | str) -> None: ...
def create_run(payload: dict[str, Any]) -> dict[str, Any]: ...
def update_step(run_id: str, step_id: str, status: str, evidence: dict[str, Any]) -> dict[str, Any]: ...
def next_runnable_step(run_id: str) -> dict[str, Any]: ...
def resume_run(run_id: str) -> dict[str, Any]: ...
def cancel_run(run_id: str) -> dict[str, Any]: ...
```

Store under `ROOT / "workflow-runs"`.

- [x] **Step 3: Connect existing queue semantics**

`companion.py` should keep pending queue behavior, but UI and ledger should treat queue IDs as implementation details under workflow steps.

- [x] **Step 4: Update Workflow Inspector**

Web UI should show step status, objectRef, queueId, confirmation point, retry availability, and evidence summary. It should not show retry for write/confirmation steps.

- [x] **Step 5: Run tests**

```bash
python3 -m unittest tests.test_workflow_engine tests.test_companion_controls tests.test_web_controls_static
```

- [ ] **Step 6: Commit**

```bash
git add workflow_engine.py companion.py extension/codex.mn.assistant/web/app.js tests/test_workflow_engine.py tests/test_companion_controls.py
git commit -m "feat: persist resumable workflow runs"
```

---

### Task 6: Skill Runtime v2

Status: implemented in the current worktree.

Implemented surface:

- `skill_marketplace.validate_manifest(...)`
- `skill_marketplace.install_manifest(...)`
- `skill_marketplace.skill_operation_plan(...)`
- `skill_marketplace.record_skill_run(...)`
- `skill_marketplace.latest_skill_runs(...)`
- Companion actions: `skill_operation_plan`, `skill_run_record`, `skill_run_latest`
- Web Skill Center safety badges, invalid manifest state, dry-run plan preview, recent skill run refresh

**Files:**
- Modify: `skill_marketplace.py`
- Modify: `companion.py`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Test: `tests/test_skill_marketplace.py`
- Test: `tests/test_companion_controls.py`
- Test: `tests/test_web_controls_static.py`

- [x] **Step 1: Write tests for manifest validation**

Extend `tests/test_skill_marketplace.py`:

```python
def test_write_skill_requires_dry_run_rollback_and_acceptance(self):
    bad = {
        "schema": "codex.mn.skillManifest.v1",
        "skillId": "bad.writer",
        "name": "Bad Writer",
        "version": "1.0.0",
        "permissions": ["notes"],
        "outputs": ["write_draft"],
    }
    result = skill_marketplace.validate_manifest(bad)
    self.assertFalse(result["ok"])
    self.assertIn("rollback", result["missing"])
    self.assertIn("acceptance", result["missing"])
```

- [x] **Step 2: Implement manifest validator**

Add:

```python
def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]: ...
def install_manifest(manifest: dict[str, Any]) -> dict[str, Any]: ...
def skill_operation_plan(skill_id: str, object_ref: dict[str, Any]) -> dict[str, Any]: ...
```

Rules:

- Read-only skills may omit rollback.
- Write skills must declare `requiresConfirmation`, `dryRun`, `rollback`, and `acceptance`.
- Delete skills must declare `allowsDelete=true` and a delete confirmation rule.

- [x] **Step 3: Expose Skill Center actions**

The Web UI should show `只读`, `写入`, `删除/回滚` badges and disable run actions when validation fails.

- [x] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_skill_marketplace tests.test_web_controls_static
```

Focused verification run:

```bash
python3 -m unittest \
  tests.test_skill_marketplace \
  tests.test_companion_controls.CompanionControlsTests.test_skill_marketplace_lists_and_installs_permission_declared_skills \
  tests.test_companion_controls.CompanionControlsTests.test_skill_runtime_actions_return_operation_plan_and_run_ledger \
  tests.test_web_controls_static.WebControlsStaticTests.test_knowledge_and_workflow_workspaces_are_executable_not_status_only
```

- [ ] **Step 5: Commit**

```bash
git add skill_marketplace.py companion.py extension/codex.mn.assistant/web/app.js tests/test_skill_marketplace.py
git commit -m "feat: validate publishable skill manifests"
```

---

### Task 7: Verification Agent

Status: implemented in the current worktree.

Implemented surface:

- `verification_agent.verify_transaction(...)`
- `verification_agent.verify_source_registry(...)`
- `verification_agent.verify_workflow_run(...)`
- `verification_agent.verify_skill_run(...)`
- `operation_ledger_get` now includes `codex.mn.verificationReport.v1` for workflow and transaction entries.
- `release_acceptance.evaluate_acceptance(..., final_claim=True, verification_reports=[...])` now blocks final/v3 claims without a current-document PASS verification report.

**Files:**
- Create: `verification_agent.py`
- Modify: `companion.py`
- Modify: `release_acceptance.py`
- Test: `tests/test_verification_agent.py`
- Test: `tests/test_release_acceptance.py`

- [x] **Step 1: Write verification tests**

Create `tests/test_verification_agent.py`.

```python
import unittest

import verification_agent


class VerificationAgentTests(unittest.TestCase):
    def test_reports_unknown_when_native_probe_missing(self):
        report = verification_agent.verify_transaction(
            {
                "createdNoteIds": ["n1"],
                "nativeProbe": {},
            }
        )
        self.assertEqual(report["schema"], "codex.mn.verificationReport.v1")
        self.assertEqual(report["status"], "UNKNOWN")
        self.assertIn("native_probe_missing", report["problems"])

    def test_reports_fail_when_expected_object_absent(self):
        report = verification_agent.verify_transaction(
            {
                "createdNoteIds": ["n1"],
                "nativeProbe": {"objects": [{"noteId": "n1", "exists": False}]},
            }
        )
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("n1", report["missingNoteIds"])
```

- [x] **Step 2: Implement verification report**

Implement:

```python
VERIFICATION_REPORT_SCHEMA = "codex.mn.verificationReport.v1"

def verify_transaction(transaction: dict[str, Any]) -> dict[str, Any]: ...
def verify_source_registry(registry: dict[str, Any]) -> dict[str, Any]: ...
def verify_workflow_run(run: dict[str, Any]) -> dict[str, Any]: ...
def verify_skill_run(run: dict[str, Any]) -> dict[str, Any]: ...
```

Status values must be `PASS`, `FAIL`, or `UNKNOWN`.

- [x] **Step 3: Use report in ledger and release acceptance**

`operation_ledger_get` should include the report. `release_acceptance.py` should require at least one current-document verification report for final v1/v3 claims, but not for preview release.

- [x] **Step 4: Run tests**

```bash
python3 -m unittest tests.test_verification_agent tests.test_release_acceptance tests.test_single_document_acceptance
```

Focused verification run:

```bash
python3 -m unittest \
  tests.test_verification_agent \
  tests.test_release_acceptance \
  tests.test_single_document_acceptance \
  tests.test_companion_controls.CompanionControlsTests.test_operation_ledger_lists_and_loads_object_scoped_operations
```

- [ ] **Step 5: Commit**

```bash
git add verification_agent.py companion.py release_acceptance.py tests/test_verification_agent.py tests/test_release_acceptance.py
git commit -m "feat: add verification agent reports"
```

---

### Task 8: UI Workspace Reframe

Status: implemented in the current worktree.

Implemented surface:

- Added runtime-required shell anchors: `knowledgeConsolePanel`, `studioCanvasPanel`, `operationLedgerDrawer`, `sourceRegistryPanel`, `verificationReportPanel`, `externalGatewayPanel`, and `skillCenterPanel`.
- Kept legacy IDs intact for WebView bridge, doctor, and single-document acceptance compatibility.
- Updated WebView required control reporting, doctor gates, and single-document runtime acceptance checks to require the new OS shell anchors.
- Workspace Navigator now focuses product-level panels such as `knowledgeConsolePanel`, `operationLedgerDrawer`, and `skillCenterPanel`.

**Files:**
- Modify: `extension/codex.mn.assistant/web/index.html`
- Modify: `extension/codex.mn.assistant/web/app.js`
- Modify: `extension/codex.mn.assistant/web/app.css`
- Test: `tests/test_web_controls_static.py`
- Test: `tests/test_doctor_checks.py`
- Test: `tests/test_single_document_acceptance.py`

- [x] **Step 1: Add static tests for OS layout anchors**

Extend `tests/test_web_controls_static.py` to require:

- `knowledgeConsolePanel`
- `studioCanvasPanel`
- `commandPanePanel`
- `operationLedgerDrawer`
- `sourceRegistryPanel`
- `verificationReportPanel`
- `externalGatewayPanel`
- `skillCenterPanel`

- [x] **Step 2: Rename visual hierarchy without breaking old IDs**

Keep old IDs for compatibility. Add new wrapper IDs:

```html
<section id="knowledgeConsolePanel">...</section>
<section id="studioCanvasPanel">...</section>
<aside id="commandPanePanel">...</aside>
<section id="operationLedgerDrawer">...</section>
```

- [x] **Step 3: Render object-first empty states**

Workspace mode should show:

- current object
- source readiness
- study gaps
- latest workflow
- latest ledger failure
- next executable workflow

before showing chat history.

- [x] **Step 4: Run UI static checks**

```bash
python3 -m unittest tests.test_web_controls_static tests.test_doctor_checks tests.test_single_document_acceptance
node --check extension/codex.mn.assistant/web/app.js
```

Focused verification run:

```bash
python3 -m unittest tests.test_web_controls_static tests.test_doctor_checks tests.test_single_document_acceptance
node --check extension/codex.mn.assistant/web/app.js
```

- [ ] **Step 5: Commit**

```bash
git add extension/codex.mn.assistant/web/index.html extension/codex.mn.assistant/web/app.js extension/codex.mn.assistant/web/app.css tests/test_web_controls_static.py tests/test_doctor_checks.py tests/test_single_document_acceptance.py
git commit -m "feat: reframe workspace as knowledge OS shell"
```

---

### Task 9: Documentation and Release Gates

Status: implemented in the current worktree.

Implemented surface:

- Rebuilt `docs/RELEASE_STATUS_MATRIX.md` around Knowledge OS kernels and shell anchors instead of old button-grid controls.
- Updated `docs/CURRENT_RELEASE_AUDIT.md` with the current worktree evidence for object/source/gateway/transaction/workflow/skill/verification kernels and Knowledge OS shell anchors.
- Updated README, Chinese README, product spec, user manual, and programmatic verification docs for seven kernels, Skill Runtime v2, Verification Agent v1, and final/v3 verification report gating.
- Updated `tests/test_release_docs.py` so docs protect current kernels and shell anchors rather than stale button-era markers.

**Files:**
- Modify: `README.md`
- Modify: `README.zh-CN.md`
- Modify: `docs/PRODUCT_SPEC.md`
- Modify: `docs/USER_MANUAL.md`
- Modify: `docs/RELEASE_STATUS_MATRIX.md`
- Modify: `docs/CURRENT_RELEASE_AUDIT.md`
- Modify: `CHANGELOG.md`
- Test: `tests/test_release_docs.py`

- [x] **Step 1: Update docs after each implemented kernel**

For every task above, update docs with:

- what is now implemented
- what remains first-stage only
- how to verify it
- whether it affects public preview or final v3 claims

- [x] **Step 2: Add release matrix rows**

Add matrix rows for:

- Live MN Object Kernel
- Source Registry action evidence
- External Automation Gateway v2
- Transactional Native Editor
- Workflow Runtime v2
- Skill Runtime v2
- Verification Agent

- [x] **Step 3: Run docs tests**

```bash
python3 -m unittest tests.test_release_docs
```

Focused verification run:

```bash
python3 -m unittest tests.test_release_docs
```

- [ ] **Step 4: Commit**

```bash
git add README.md README.zh-CN.md docs/PRODUCT_SPEC.md docs/USER_MANUAL.md docs/RELEASE_STATUS_MATRIX.md docs/CURRENT_RELEASE_AUDIT.md CHANGELOG.md tests/test_release_docs.py
git commit -m "docs: track knowledge OS implementation gates"
```

---

### Task 10: Release Candidate Verification

**Files:**
- Modify only versioned packaging files needed by existing scripts.
- Use existing release scripts.

- [x] **Step 1: Run full local verification**

```bash
python3 -m unittest discover -s tests
node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
python3 -m py_compile companion.py agent_workbench.py operation_runtime.py workflow_engine.py skill_marketplace.py transaction_manager.py knowledge_index.py doctor.py release_acceptance.py single_document_acceptance.py package_release.py build_pkg.py
git diff --check
```

Completed verification:

```bash
python3 -m unittest discover -s tests
# Ran 535 tests OK

node --check extension/codex.mn.assistant/main.js
node --check extension/codex.mn.assistant/web/app.js
python3 -m py_compile companion.py agent_workbench.py operation_runtime.py workflow_engine.py skill_marketplace.py transaction_manager.py knowledge_index.py doctor.py release_acceptance.py single_document_acceptance.py package_release.py build_pkg.py object_kernel.py source_registry.py external_gateway.py verification_agent.py
git diff --check
```

- [x] **Step 2: Package**

Use the next version after the current release.

```bash
python3 package_release.py 0.4.40
python3 build_pkg.py release/CodexCompanion-0.4.40-latest-dist.zip --json
python3 release_smoke_test.py release/CodexCompanion-0.4.40-latest-dist.zip --mnaddon release/CodexCompanion-0.4.40-latest.mnaddon
python3 release_smoke_test.py release/CodexCompanion-0.4.40-latest-dist.zip --mnaddon release/CodexCompanion-0.4.40-latest.mnaddon --install-dry-run
```

Completed package evidence:

```text
release/CodexCompanion-0.4.40-latest-dist.zip: generated and mirrored to OneDrive
release/CodexCompanion-0.4.40-latest.mnaddon: generated and mirrored to OneDrive
release/CodexCompanion-0.4.40-latest.pkg: generated and mirrored to OneDrive, signed=false
sha256: recorded in release/SHA256SUMS.txt and the OneDrive SHA256SUMS.txt mirror
release smoke: PASS
install dry-run: PASS
```

- [x] **Step 3: Local install**

```bash
./install.sh
```

Then restart or reopen MarginNote 4 so WebView/native runtime reports the new version.

Completed local install evidence:

```text
/bin/zsh /tmp/codex-companion-install-b6SaRM/CodexCompanion-0.4.40/install.sh
MN4 extension manifest: Codex Companion / 0.4.40
Companion service: OK, LaunchAgent com.codex.paper-companion
Doctor summary: 0 fail, 8 warn, 10 ok
Remaining runtime action: restart MarginNote 4 or reopen the panel so 0.4.40 WebView/native events are recorded.
```

- [x] **Step 4: Acceptance**

```bash
python3 release_acceptance.py release/CodexCompanion-0.4.40-latest-dist.zip --json
```

Preview release may still block on signed/notarized/cross-machine/native-highlight gates. Do not label it final v1 or v3 until those gates pass.

Completed acceptance evidence:

```text
releasable=false
blockers=runtime_web_controls,native_api_matrix,native_visible_highlight,signed_pkg,notarized_pkg,cross_machine_install,single_document_acceptance
```

- [x] **Step 5: Commit, tag, push, release**

```bash
git status --short
git add .
git commit -m "release: v0.4.40"
git tag v0.4.40
git push origin main
git push origin v0.4.40
gh release create v0.4.40 release/CodexCompanion-0.4.40-latest-dist.zip release/CodexCompanion-0.4.40-latest.mnaddon release/CodexCompanion-0.4.40-latest.pkg --title "Codex Companion v0.4.40" --notes-file release/RELEASE_NOTES.md
```

Completed release evidence:

```text
commit=main at tag v0.4.40
tag=v0.4.40
release=https://github.com/LiuWhale/marginnote-assistant/releases/tag/v0.4.40
assets=CodexCompanion-0.4.40-latest-dist.zip,CodexCompanion-0.4.40-latest.mnaddon,CodexCompanion-0.4.40-latest.pkg,SHA256SUMS.txt
```

---

## Plan Self-Review

- Scope coverage: The plan maps the v3 design into object, source, transaction, workflow, automation, skill, verification, UI, docs, and release tasks.
- Placeholder scan: There are no unresolved placeholder markers. Each task defines concrete files, test commands, and expected behavior.
- Type consistency: Schema names match the design document: `codex.mn.mnObject.v1`, `codex.mn.sourceRegistry.v1`, `codex.mn.agentOperation.v1`, `codex.mn.operationTransaction.v1`, `codex.mn.skillManifest.v1`, and `codex.mn.verificationReport.v1`.
- Risk note: This is not a one-commit implementation. It is a phased plan for turning the current preview into the Knowledge OS architecture without pretending the existing panels already satisfy v3.
