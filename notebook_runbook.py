from __future__ import annotations

from typing import Any

from object_intake import object_ref_has_real_identity, workspace_action


NOTEBOOK_RUNBOOK_SCHEMA = "codex.mn.notebookRunbook.v1"
NOTEBOOK_RUNBOOK_STEP_SCHEMA = "codex.mn.notebookRunbookStep.v1"
NOTEBOOK_RUNBOOK_CONTINUE_SCHEMA = "codex.mn.notebookRunbookContinue.v1"
NOTEBOOK_RUNBOOK_AUTO_PLAN_SCHEMA = "codex.mn.notebookRunbookAutoPlan.v1"
NOTEBOOK_RUNBOOK_PREFLIGHT_RUN_SCHEMA = "codex.mn.notebookRunbookPreflightRun.v1"


def empty_preflight_run() -> dict[str, Any]:
    return {
        "schema": NOTEBOOK_RUNBOOK_PREFLIGHT_RUN_SCHEMA,
        "runId": "",
        "status": "idle",
        "writePolicy": "no_write_preflight",
        "mode": "safe_preflight",
        "actionCount": 0,
        "completedCount": 0,
        "failedCount": 0,
        "actions": [],
        "updatedAt": "",
    }


def runbook_step(
    step_id: str,
    title: str,
    status: str,
    detail: str,
    *,
    action: dict[str, Any] | None = None,
    evidence: str = "",
) -> dict[str, Any]:
    tone = {
        "ready": "ready",
        "action_required": "warning",
        "blocked": "danger",
        "pending": "secondary",
    }.get(status, "secondary")
    return {
        "schema": NOTEBOOK_RUNBOOK_STEP_SCHEMA,
        "id": step_id,
        "title": title,
        "status": status,
        "tone": tone,
        "detail": detail,
        "evidence": evidence,
        "action": action if isinstance(action, dict) else {},
    }


def runbook_summary(steps: list[dict[str, Any]]) -> dict[str, int]:
    ready = sum(1 for step in steps if step.get("status") == "ready")
    blocked = sum(1 for step in steps if step.get("status") == "blocked")
    action_required = sum(1 for step in steps if step.get("status") == "action_required")
    pending = sum(1 for step in steps if step.get("status") == "pending")
    return {
        "total": len(steps),
        "ready": ready,
        "blocked": blocked,
        "actionRequired": action_required,
        "pending": pending,
    }


def continue_action(step: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(step, dict):
        return {}
    action = step.get("action") if isinstance(step.get("action"), dict) else {}
    if not action.get("action"):
        return {}
    return {
        "schema": NOTEBOOK_RUNBOOK_CONTINUE_SCHEMA,
        "stepId": str(step.get("id") or ""),
        "stepTitle": str(step.get("title") or ""),
        "label": f"继续：{step.get('title') or action.get('label') or '下一步'}",
        "action": str(action.get("action") or ""),
        "payload": action.get("payload") if isinstance(action.get("payload"), dict) else {},
        "surface": str(action.get("surface") or ""),
        "detail": str(step.get("detail") or action.get("detail") or ""),
        "tone": str(action.get("tone") or step.get("tone") or "primary"),
    }


def auto_plan(steps: list[dict[str, Any]], latest_run: dict[str, Any] | None = None) -> dict[str, Any]:
    safe_step_ids = ["source_inventory", "scan_objects", "mindmap_baseline", "operation_plan"]
    actions: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    by_id = {str(step.get("id") or ""): step for step in steps if isinstance(step, dict)}
    for step_id in safe_step_ids:
        step = by_id.get(step_id) if isinstance(by_id.get(step_id), dict) else {}
        if not step:
            continue
        status = str(step.get("status") or "")
        action = continue_action(step)
        if status == "action_required" and action.get("action"):
            actions.append({**action, "order": len(actions) + 1})
        elif status == "blocked":
            blocked.append(
                {
                    "stepId": step_id,
                    "stepTitle": str(step.get("title") or ""),
                    "detail": str(step.get("detail") or ""),
                }
            )
    return {
        "schema": NOTEBOOK_RUNBOOK_AUTO_PLAN_SCHEMA,
        "mode": "safe_preflight",
        "label": "自动准备工作台",
        "canRun": bool(actions),
        "actions": actions,
        "blocked": blocked,
        "latestRun": latest_run if isinstance(latest_run, dict) and latest_run else empty_preflight_run(),
        "detail": "顺序执行安全预检动作：补来源、扫描 MN 对象、读取脑图基线、生成操作计划；不直接写入 MarginNote。",
    }


def _actions_by_id(primary_actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}


def _runbook_status(counts: dict[str, int]) -> str:
    if counts["blocked"]:
        return "blocked"
    if counts["actionRequired"]:
        return "action_required"
    if counts["ready"] == counts["total"]:
        return "ready"
    return "pending"


def _next_step(steps: list[dict[str, Any]]) -> dict[str, Any]:
    for status_group in ("action_required", "pending", "blocked"):
        next_step = next(
            (
                step
                for step in steps
                if step.get("status") == status_group
                and isinstance(step.get("action"), dict)
                and step.get("action", {}).get("action")
            ),
            {},
        )
        if next_step:
            return next_step
    return {}


def build_runbook(
    summary: dict[str, Any],
    primary_actions: list[dict[str, Any]],
    *,
    latest_run: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actions_by_id = _actions_by_id(primary_actions)
    focus = summary.get("focusObject") if isinstance(summary.get("focusObject"), dict) else {}
    objects = summary.get("objects") if isinstance(summary.get("objects"), dict) else {}
    mindmap = summary.get("mindmap") if isinstance(summary.get("mindmap"), dict) else {}
    review = summary.get("reviewQueue") if isinstance(summary.get("reviewQueue"), dict) else {}
    workflows = summary.get("workflows") if isinstance(summary.get("workflows"), dict) else {}
    ledger = summary.get("ledger") if isinstance(summary.get("ledger"), dict) else {}
    readiness = summary.get("readiness") if isinstance(summary.get("readiness"), dict) else {}
    source_registry = summary.get("sourceRegistry") if isinstance(summary.get("sourceRegistry"), dict) else {}
    source_summary = source_registry.get("summary") if isinstance(source_registry.get("summary"), dict) else {}
    source_action_plan = source_registry.get("actionPlan") if isinstance(source_registry.get("actionPlan"), dict) else {}
    source_repair_action = source_action_plan.get("recommendedAction") if isinstance(source_action_plan.get("recommendedAction"), dict) else {}

    has_notebook_scope = bool(summary.get("topicid") or summary.get("bookmd5"))
    has_context = bool(has_notebook_scope or summary.get("documentTitle") or object_ref_has_real_identity(focus))
    source_readable = int(source_summary.get("readable") or 0) > 0
    registry_count = int(objects.get("registry") or 0)
    native_scan_count = int(objects.get("nativeScan") or 0)
    mindmap_ready = str(mindmap.get("status") or "") == "available"
    review_total = int(review.get("total") or 0)
    workflow_count = int(workflows.get("runCount") or 0)
    ledger_total = int(ledger.get("total") or 0)
    mn_api_available = bool(readiness.get("mnApiAvailable"))

    source_action = actions_by_id.get("open_source_registry") if source_readable else source_repair_action
    mn_objects_action = actions_by_id.get("open_object_browser") if native_scan_count > 0 else (actions_by_id.get("scan_mn_objects") if has_notebook_scope else {})
    mindmap_action = actions_by_id.get("open_mindmap_studio") if mindmap_ready else (actions_by_id.get("read_mindmap_tree") if has_notebook_scope else {})
    workflow_action = actions_by_id.get("open_workflow_builder") if workflow_count > 0 else actions_by_id.get("open_workflows")

    steps = [
        runbook_step(
            "context_scope",
            "确认上下文",
            "ready" if has_context else "blocked",
            "已识别当前 notebook、文档或 MNObject。" if has_context else "还没有可用的 MarginNote 上下文。",
            evidence=str(summary.get("documentTitle") or summary.get("bookmd5") or summary.get("topicid") or ""),
        ),
        runbook_step(
            "source_inventory",
            "核对来源清单",
            "ready" if source_readable else ("action_required" if has_context else "blocked"),
            f"已有 {int(source_summary.get('readable') or 0)} 个可读来源，可进入全文任务。" if source_readable else "需要先缓存 PDF、选择文件或登记路径，避免全文任务只看到标题/选区。",
            action=source_action,
            evidence=f"readable={int(source_summary.get('readable') or 0)} / total={int(source_summary.get('total') or 0)} / pendingCache={int(source_summary.get('pendingNativeCache') or 0)}",
        ),
        runbook_step(
            "scan_objects",
            "扫描 MN 对象",
            "ready" if native_scan_count > 0 else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"Native Scan 已确认 {native_scan_count} 个原生对象。" if native_scan_count > 0 else ("需要扫描当前 notebook 的原生对象，Object Browser 才不是只看聊天和本地证据。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能请求 MN4 扫描真实对象。"),
            action=mn_objects_action,
            evidence=f"objects={int(objects.get('total') or 0)} / registry={registry_count} / nativeScan={native_scan_count}",
        ),
        runbook_step(
            "mindmap_baseline",
            "读取脑图基线",
            "ready" if mindmap_ready else ("action_required" if mn_api_available and has_notebook_scope else "blocked"),
            f"已读取 {int(mindmap.get('nodeCount') or 0)} 个脑图节点。" if mindmap_ready else ("需要读取当前脑图树，后续 Diff/合并/回滚才有真实基线。" if has_notebook_scope else "缺少 notebook topic/book 作用域，不能读取当前脑图树。"),
            action=mindmap_action,
            evidence=str(mindmap.get("rootTitle") or mindmap.get("updatedAt") or ""),
        ),
        runbook_step(
            "card_coverage",
            "检查卡片覆盖",
            "ready" if review_total > 0 else ("pending" if has_context else "blocked"),
            f"已有 {review_total} 张对象级复习卡。" if review_total > 0 else "当前对象还没有复习卡；进入 Card Factory 查看覆盖和质量状态，生成仍需用户明确触发。",
            action=actions_by_id.get("open_card_factory"),
            evidence=f"cards={review_total} / due={int(review.get('due') or 0)} / new={int(review.get('new') or 0)}",
        ),
        runbook_step(
            "operation_plan",
            "生成操作计划",
            "action_required" if has_context else "blocked",
            "把当前对象、权限、目标脑图和写入意图编译成 Operation Plan，再决定是否写入。" if has_context else "缺少上下文，不能生成可靠操作计划。",
            action=actions_by_id.get("plan_next_operation") if has_context else {},
            evidence=f"permission={readiness.get('permission') or 'unknown'} / mnApi={readiness.get('mnApiBackend') or 'unknown'}",
        ),
        runbook_step(
            "workflow_runtime",
            "检查工作流",
            "ready" if workflow_count > 0 else "pending",
            f"已有 {workflow_count} 个 workflow run，最近状态：{workflows.get('latestStatus') or 'unknown'}。" if workflow_count > 0 else "还没有当前文档 workflow run；长任务应从这里进入可审计运行。",
            action=workflow_action,
            evidence=f"templates={int(workflows.get('templateCount') or 0)}",
        ),
        runbook_step(
            "operation_evidence",
            "核对操作证据",
            "ready" if ledger_total > 0 else "pending",
            f"Operation Ledger 已有 {ledger_total} 条证据。" if ledger_total > 0 else "还没有当前文档账本证据；写入、确认和回滚应在这里留痕。",
            action=actions_by_id.get("open_operation_ledger"),
            evidence=f"filtered={int(ledger.get('filteredTotal') or ledger_total)} / total={ledger_total}",
        ),
    ]
    counts = runbook_summary(steps)
    next_step = _next_step(steps)
    return {
        "schema": NOTEBOOK_RUNBOOK_SCHEMA,
        "status": _runbook_status(counts),
        "summary": counts,
        "steps": steps,
        "nextStep": next_step if isinstance(next_step, dict) else {},
        "continueAction": continue_action(next_step),
        "autoPlan": auto_plan(steps, latest_run),
    }
