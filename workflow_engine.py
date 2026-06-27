from __future__ import annotations

import hashlib
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any


WORKFLOW_SCHEMA = "codex.mn.workflowPreview.v1"
WORKFLOW_RUN_SCHEMA = "codex.mn.workflowRun.v1"
WORKFLOW_RUNTIME_SCHEMA = "codex.mn.workflowRuntime.v2"
_ROOT = Path.home() / ".codex/marginnote-assistant"
_RUNS_DIR = _ROOT / "workflow-runs"


WORKFLOW_TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "paper_deep_reading",
        "title": "文档精读工作流",
        "trigger": "manual",
        "context": ["current_document", "pdf_cache", "mindmap_target"],
        "steps": [
            {"id": "cache_pdf", "action": "request_pdf_cache", "title": "缓存当前文档全文", "writes": False},
            {"id": "full_reading", "action": "generate_full_reading", "title": "生成完整精读回答", "writes": False},
            {"id": "mindmap_tree", "action": "generate_mindmap", "title": "生成结构化脑图树草稿", "writes": False},
            {"id": "cards", "action": "generate_card", "title": "拆成大小适中的短卡草稿", "writes": False},
            {"id": "dry_run", "action": "operation_plan_preview", "title": "写入前操作计划 dry-run", "writes": False},
            {"id": "write", "action": "write_draft", "title": "用户确认后写入 MarginNote", "writes": True},
            {"id": "verify", "action": "ai_edit_transaction_get", "title": "验证写入与回滚账本", "writes": False},
        ],
        "confirmationPoints": ["write"],
        "requiredCapabilities": ["cacheCurrentPdf", "nativeCards", "nativeMindmap", "rollbackLedger"],
    },
    {
        "id": "selection_to_cards",
        "title": "选区制卡工作流",
        "trigger": "manual_or_selection",
        "context": ["selection", "current_document"],
        "steps": [
            {"id": "explain", "action": "chat", "title": "解释当前选区", "writes": False},
            {"id": "cards", "action": "generate_card", "title": "生成短卡草稿", "writes": False},
            {"id": "dry_run", "action": "operation_plan_preview", "title": "写入前操作计划 dry-run", "writes": False},
            {"id": "write", "action": "write_draft", "title": "用户确认后写入 MarginNote", "writes": True},
        ],
        "confirmationPoints": ["write"],
        "requiredCapabilities": ["nativeCards", "rollbackLedger"],
    },
    {
        "id": "mindmap_reorganize",
        "title": "当前脑图重组工作流",
        "trigger": "manual",
        "context": ["selected_node", "mindmap_tree", "current_document"],
        "steps": [
            {"id": "read_tree", "action": "mn_read_tree", "title": "读取当前脑图或选中子树", "writes": False},
            {"id": "reorganize", "action": "reorganize_mindmap", "title": "生成非破坏式重组草稿", "writes": False},
            {"id": "dry_run", "action": "operation_plan_preview", "title": "写入前操作计划 dry-run", "writes": False},
            {"id": "write", "action": "write_draft", "title": "用户确认后追加到目标节点", "writes": True},
            {"id": "verify", "action": "ai_edit_transaction_get", "title": "验证新增分支并允许拒绝回滚", "writes": False},
        ],
        "confirmationPoints": ["write"],
        "requiredCapabilities": ["nativeMindmap", "readMindmapTree", "rollbackLedger"],
    },
]


def configure(root: Path | str) -> None:
    global _ROOT, _RUNS_DIR
    _ROOT = Path(root).expanduser()
    _RUNS_DIR = _ROOT / "workflow-runs"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def _safe_run_id(value: Any) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(value or ""))[:96]


def _run_path(run_id: str) -> Path:
    clean = _safe_run_id(run_id)
    if not clean:
        raise ValueError("missing workflow run id")
    return _RUNS_DIR / f"{clean}.json"


def _read_json(path: Path, default: dict[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return value if isinstance(value, dict) else default


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _event(event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    return {
        "event": event,
        "ts": _now(),
        "stepId": str(payload.get("stepId") or ""),
        "status": str(payload.get("status") or ""),
        "message": str(payload.get("message") or ""),
    }


def _step_status_for_new_run(step: dict[str, Any], index: int) -> str:
    if index == 1:
        return "pending"
    return "pending"


def _normalize_run_status(steps: list[dict[str, Any]], current: str = "") -> str:
    statuses = {str(step.get("status") or "") for step in steps if isinstance(step, dict)}
    if current == "cancelled" or "cancelled" in statuses and statuses.issubset({"cancelled", "completed"}):
        return "cancelled"
    if statuses.intersection({"failed", "blocked"}):
        return "partial"
    if "waiting_confirmation" in statuses:
        return "waiting_confirmation"
    if "queued" in statuses:
        return "queued"
    if "running" in statuses:
        return "running"
    if statuses and statuses.issubset({"completed", "skipped"}):
        return "completed"
    return "pending"


def _load_run(run_id: str) -> dict[str, Any]:
    clean = _safe_run_id(run_id)
    if not clean:
        return {}
    return _read_json(_run_path(clean), {})


def save_run(run: dict[str, Any]) -> dict[str, Any]:
    run = dict(run) if isinstance(run, dict) else {}
    run_id = _safe_run_id(run.get("runId") or run.get("id"))
    if not run_id:
        raise ValueError("missing workflow run id")
    run["id"] = str(run.get("id") or run_id)
    run["runId"] = str(run.get("runId") or run_id)
    run["runtimeSchema"] = str(run.get("runtimeSchema") or WORKFLOW_RUNTIME_SCHEMA)
    run["updatedAt"] = _now()
    _write_json(_run_path(run_id), run)
    return run


def create_run(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload) if isinstance(payload, dict) else {}
    preview = build_workflow_preview(payload)
    now = _now()
    seed = f"{now}|{uuid.uuid4()}|{preview.get('id')}"
    run_id = _safe_run_id(payload.get("runId") or hashlib.sha256(seed.encode("utf-8")).hexdigest()[:20])
    steps: list[dict[str, Any]] = []
    for index, step in enumerate(preview.get("steps") if isinstance(preview.get("steps"), list) else [], start=1):
        if not isinstance(step, dict):
            continue
        step_id = str(step.get("id") or step.get("action") or f"step_{index}")
        steps.append(
            {
                "stepId": step_id,
                "id": step_id,
                "index": index,
                "title": str(step.get("title") or step_id),
                "action": str(step.get("action") or ""),
                "writes": bool(step.get("writes")),
                "status": _step_status_for_new_run(step, index),
                "evidence": {},
                "events": [],
            }
        )
    run = {
        "schema": WORKFLOW_RUN_SCHEMA,
        "runtimeSchema": WORKFLOW_RUNTIME_SCHEMA,
        "id": run_id,
        "runId": run_id,
        "workflowId": str(preview.get("id") or ""),
        "title": str(preview.get("title") or ""),
        "status": _normalize_run_status(steps),
        "topicid": str(payload.get("topicid") or ""),
        "bookmd5": str(payload.get("bookmd5") or ""),
        "objectRef": payload.get("objectRef") if isinstance(payload.get("objectRef"), dict) else {},
        "steps": steps,
        "events": [_event("workflow_created", {"status": "pending"})],
        "createdAt": now,
        "updatedAt": now,
        "preview": preview,
    }
    save_run(run)
    return {"ok": True, "runId": run_id, "workflowRun": run}


def update_step(run_id: str, step_id: str, status: str, evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    run = _load_run(run_id)
    if not run:
        return {"ok": False, "message": "workflow run not found", "runId": _safe_run_id(run_id)}
    evidence = evidence if isinstance(evidence, dict) else {}
    clean_step_id = str(step_id or "").strip()
    target: dict[str, Any] | None = None
    for step in run.get("steps") if isinstance(run.get("steps"), list) else []:
        if not isinstance(step, dict):
            continue
        candidate = str(step.get("stepId") or step.get("id") or step.get("action") or "")
        if clean_step_id == candidate:
            target = step
            break
    if target is None:
        return {"ok": False, "message": "workflow step not found", "runId": _safe_run_id(run_id), "stepId": clean_step_id}
    target["status"] = str(status or "unknown")
    target["evidence"] = {**(target.get("evidence") if isinstance(target.get("evidence"), dict) else {}), **evidence}
    if evidence.get("queueId"):
        target["queueId"] = str(evidence.get("queueId") or "")
    target_event = _event("workflow_step_updated", {"stepId": clean_step_id, "status": target["status"], "message": evidence.get("message") or ""})
    step_events = target.get("events") if isinstance(target.get("events"), list) else []
    target["events"] = [*step_events, target_event][-20:]
    run_events = run.get("events") if isinstance(run.get("events"), list) else []
    run["events"] = [*run_events, target_event][-100:]
    run["status"] = _normalize_run_status([step for step in run.get("steps", []) if isinstance(step, dict)], str(run.get("status") or ""))
    save_run(run)
    return {"ok": True, "runId": _safe_run_id(run_id), "stepId": clean_step_id, "workflowRun": run, "step": target}


def next_runnable_step(run_id: str) -> dict[str, Any]:
    run = _load_run(run_id)
    if not run:
        return {"ok": False, "message": "workflow run not found", "runId": _safe_run_id(run_id)}
    priority = ["waiting_confirmation", "running", "queued", "pending", "blocked", "failed"]
    steps = [step for step in run.get("steps") if isinstance(step, dict)] if isinstance(run.get("steps"), list) else []
    for status in priority:
        for step in steps:
            if str(step.get("status") or "") == status:
                return {
                    "ok": True,
                    "runId": str(run.get("runId") or run.get("id") or ""),
                    "stepId": str(step.get("stepId") or step.get("id") or step.get("action") or ""),
                    "status": status,
                    "action": str(step.get("action") or ""),
                    "writes": bool(step.get("writes")),
                    "requiresConfirmation": bool(step.get("writes")) or status == "waiting_confirmation",
                    "evidence": step.get("evidence") if isinstance(step.get("evidence"), dict) else {},
                    "step": step,
                }
    return {"ok": False, "message": "no runnable workflow step", "runId": str(run.get("runId") or run.get("id") or "")}


def resume_run(run_id: str) -> dict[str, Any]:
    run = _load_run(run_id)
    if not run:
        return {"ok": False, "message": "workflow run not found", "runId": _safe_run_id(run_id)}
    if str(run.get("status") or "") == "cancelled":
        return {"ok": False, "message": "cancelled workflow cannot resume", "workflowRun": run}
    next_step = next_runnable_step(run_id)
    run_events = run.get("events") if isinstance(run.get("events"), list) else []
    run["events"] = [*run_events, _event("workflow_resumed", {"status": str(next_step.get("status") or "")})][-100:]
    run["status"] = str(next_step.get("status") or _normalize_run_status([step for step in run.get("steps", []) if isinstance(step, dict)]))
    save_run(run)
    return {"ok": True, "message": "workflow resumed", "workflowRun": run, "nextStep": next_step}


def cancel_run(run_id: str) -> dict[str, Any]:
    run = _load_run(run_id)
    if not run:
        return {"ok": False, "message": "workflow run not found", "runId": _safe_run_id(run_id)}
    for step in run.get("steps") if isinstance(run.get("steps"), list) else []:
        if not isinstance(step, dict):
            continue
        if str(step.get("status") or "") not in {"completed", "done", "skipped"}:
            step["status"] = "cancelled"
    run_events = run.get("events") if isinstance(run.get("events"), list) else []
    run["events"] = [*run_events, _event("workflow_cancelled", {"status": "cancelled"})][-100:]
    run["status"] = "cancelled"
    save_run(run)
    return {"ok": True, "message": "workflow cancelled", "workflowRun": run}


def list_workflow_templates() -> list[dict[str, Any]]:
    templates: list[dict[str, Any]] = []
    for item in WORKFLOW_TEMPLATES:
        templates.append(
            {
                "id": str(item["id"]),
                "title": str(item["title"]),
                "trigger": str(item["trigger"]),
                "context": list(item.get("context") or []),
                "stepCount": len(item.get("steps") or []),
                "confirmationPoints": list(item.get("confirmationPoints") or []),
                "requiredCapabilities": list(item.get("requiredCapabilities") or []),
            }
        )
    return templates


def infer_workflow_id(text: str) -> str:
    value = str(text or "")
    if re.search(r"重组|重排|整理.*脑图|reorganize|restructure|regroup", value, re.I):
        return "mindmap_reorganize"
    if re.search(r"选区|这段|公式|制卡|短卡|card", value, re.I) and not re.search(r"全文|完整|精读", value, re.I):
        return "selection_to_cards"
    if re.search(r"精读|全文|完整|论文|文档|讲稿|deep\s*reading|full", value, re.I):
        return "paper_deep_reading"
    return "selection_to_cards"


def _find_template(workflow_id: str) -> dict[str, Any]:
    clean_id = str(workflow_id or "").strip()
    for item in WORKFLOW_TEMPLATES:
        if item["id"] == clean_id:
            return item
    return WORKFLOW_TEMPLATES[0]


def _capability_summary(
    required: list[str],
    native_caps: dict[str, Any] | None = None,
    mn_api: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    native_caps = native_caps if isinstance(native_caps, dict) else {}
    mn_api = mn_api if isinstance(mn_api, dict) else {}
    matrix = native_caps.get("capabilityMatrix") if isinstance(native_caps.get("capabilityMatrix"), dict) else {}
    url_api_ready = bool(mn_api.get("urlApiConfigured") or mn_api.get("urlApiAvailable"))
    summaries: list[dict[str, Any]] = []
    for capability_id in required:
        key = str(capability_id)
        if key == "rollbackLedger":
            summaries.append({"id": key, "status": "ready", "via": "transaction_manager"})
            continue
        if key == "readMindmapTree" and url_api_ready:
            summaries.append({"id": key, "status": "ready", "via": "url_api"})
            continue
        capability = matrix.get(key) if isinstance(matrix.get(key), dict) else {}
        if capability.get("ready"):
            summaries.append({"id": key, "status": "ready", "via": "native"})
        elif capability.get("available"):
            summaries.append(
                {
                    "id": key,
                    "status": "unknown",
                    "reason": str(capability.get("blockedReason") or "not-ready"),
                    "nextStep": str(capability.get("nextStep") or ""),
                }
            )
        elif key in {"nativeCards", "nativeMindmap"} and url_api_ready:
            summaries.append({"id": key, "status": "ready", "via": "url_api"})
        else:
            summaries.append(
                {
                    "id": key,
                    "status": "unknown",
                    "reason": "capability-unverified",
                    "nextStep": "刷新 MN 能力；如需跨插件读写，配置 URL API Gateway。",
                }
            )
    return summaries


def build_workflow_preview(
    payload: dict[str, Any],
    *,
    native_caps: dict[str, Any] | None = None,
    mn_api: dict[str, Any] | None = None,
) -> dict[str, Any]:
    prompt = "\n".join(
        str(part or "")
        for part in [
            payload.get("workflowId"),
            payload.get("prompt"),
            payload.get("title"),
            payload.get("detail"),
        ]
        if part
    )
    workflow_id = str(payload.get("workflowId") or "").strip() or infer_workflow_id(prompt)
    template = _find_template(workflow_id)
    steps = [dict(step) for step in template.get("steps") or [] if isinstance(step, dict)]
    capabilities = _capability_summary(list(template.get("requiredCapabilities") or []), native_caps, mn_api)
    blocked = [item for item in capabilities if item.get("status") == "blocked"]
    unknown = [item for item in capabilities if item.get("status") == "unknown"]
    if blocked:
        status = "blocked"
    elif unknown:
        status = "needs_capability_refresh"
    else:
        status = "ready"
    return {
        "schema": WORKFLOW_SCHEMA,
        "id": str(template["id"]),
        "title": str(template["title"]),
        "status": status,
        "trigger": str(template["trigger"]),
        "context": list(template.get("context") or []),
        "steps": steps,
        "stepCount": len(steps),
        "confirmationPoints": list(template.get("confirmationPoints") or []),
        "requiredCapabilities": capabilities,
    }
