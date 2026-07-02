from __future__ import annotations

from typing import Any

import workflow_engine


NOTEBOOK_WORKSPACE_ACTION_SCHEMA = "codex.mn.notebookWorkspaceAction.v1"
OBJECT_TASK_COMPOSER_SCHEMA = "codex.mn.objectTaskComposer.v1"
OBJECT_TASK_DRAFT_SCHEMA = "codex.mn.objectTaskDraft.v1"
OBJECT_TASK_WORKFLOW_CANDIDATE_SCHEMA = "codex.mn.objectTaskWorkflowCandidate.v1"


def workspace_action(
    action_id: str,
    label: str,
    action: str,
    payload: dict[str, Any],
    surface: str,
    detail: str,
    style: str = "secondary",
) -> dict[str, Any]:
    return {
        "schema": NOTEBOOK_WORKSPACE_ACTION_SCHEMA,
        "id": action_id,
        "label": label,
        "action": action,
        "payload": payload,
        "surface": surface,
        "detail": detail,
        "style": style,
    }


def task_draft(
    task_id: str,
    route_id: str,
    title: str,
    status: str,
    objective: str,
    *,
    route_action: dict[str, Any] | None = None,
    compile_action: dict[str, Any] | None = None,
    workflow_candidate: dict[str, Any] | None = None,
    start_action: dict[str, Any] | None = None,
    evidence: str = "",
    output: str = "",
    write_policy: str = "no_write_task_draft",
) -> dict[str, Any]:
    return {
        "schema": OBJECT_TASK_DRAFT_SCHEMA,
        "id": task_id,
        "routeId": route_id,
        "title": title,
        "status": status,
        "objective": objective,
        "evidence": evidence,
        "expectedOutput": output,
        "writePolicy": write_policy,
        "routeAction": route_action if isinstance(route_action, dict) else {},
        "compileAction": compile_action if isinstance(compile_action, dict) else {},
        "workflowCandidate": workflow_candidate if isinstance(workflow_candidate, dict) else {},
        "startAction": start_action if isinstance(start_action, dict) else {},
    }


def _routes_by_id(object_intake: dict[str, Any]) -> dict[str, dict[str, Any]]:
    routes = object_intake.get("routes") if isinstance(object_intake, dict) else []
    return {str(item.get("id") or ""): item for item in routes if isinstance(item, dict)}


def _actions_by_id(primary_actions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item.get("id") or ""): item for item in primary_actions if isinstance(item, dict)}


def build_composer(
    summary: dict[str, Any],
    primary_actions: list[dict[str, Any]],
    object_intake: dict[str, Any],
    *,
    native_caps: dict[str, Any] | None = None,
    mn_api: dict[str, Any] | None = None,
) -> dict[str, Any]:
    actions_by_id = _actions_by_id(primary_actions)
    routes_by_id = _routes_by_id(object_intake)
    object_ref = object_intake.get("objectRef") if isinstance(object_intake.get("objectRef"), dict) else {}
    object_label = str(object_intake.get("objectLabel") or object_ref.get("title") or object_ref.get("objectId") or "")
    has_context = bool(object_ref.get("objectId") or summary.get("topicid") or summary.get("bookmd5") or summary.get("documentTitle"))
    native_caps = native_caps if isinstance(native_caps, dict) else {}
    mn_api = mn_api if isinstance(mn_api, dict) else {}

    def compile_plan_action(action_id: str, prompt: str, detail: str) -> dict[str, Any]:
        base_payload = {
            "mnObject": object_ref,
            "mnObjectId": str(object_ref.get("objectId") or ""),
            "topicid": str(summary.get("topicid") or ""),
            "bookmd5": str(summary.get("bookmd5") or ""),
            "documentTitle": str(summary.get("documentTitle") or ""),
            "prompt": prompt,
            "source": "object-task-composer",
            "writePolicy": "no_write_task_draft",
        }
        return workspace_action(
            action_id,
            "编译计划",
            "agent_plan",
            base_payload,
            "mindmap_studio",
            detail,
            "primary",
        )

    def workflow_candidate(
        workflow_id: str,
        prompt: str,
        *,
        task_id: str,
        action_id: str,
        detail: str,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        payload = {
            "workflowId": workflow_id,
            "prompt": prompt,
            "mnObject": object_ref,
            "mnObjectId": str(object_ref.get("objectId") or ""),
            "topicid": str(summary.get("topicid") or ""),
            "bookmd5": str(summary.get("bookmd5") or ""),
            "documentTitle": str(summary.get("documentTitle") or ""),
            "source": "object-task-composer",
            "taskId": task_id,
        }
        preview = workflow_engine.build_workflow_preview(payload, native_caps=native_caps, mn_api=mn_api)
        candidate = {
            "schema": OBJECT_TASK_WORKFLOW_CANDIDATE_SCHEMA,
            "workflowId": str(preview.get("id") or workflow_id),
            "title": str(preview.get("title") or workflow_id),
            "status": str(preview.get("status") or "unknown"),
            "stepCount": int(preview.get("stepCount") or 0),
            "confirmationPoints": preview.get("confirmationPoints") if isinstance(preview.get("confirmationPoints"), list) else [],
            "requiredCapabilities": preview.get("requiredCapabilities") if isinstance(preview.get("requiredCapabilities"), list) else [],
        }
        start_action = workspace_action(
            action_id,
            "启动 workflow",
            "workflow_start",
            payload,
            "workflow_builder",
            detail,
            "primary",
        )
        return candidate, start_action

    def route_status(route_id: str) -> str:
        return str((routes_by_id.get(route_id) or {}).get("status") or ("pending" if has_context else "blocked"))

    def route_action(route_id: str) -> dict[str, Any]:
        route = routes_by_id.get(route_id) if isinstance(routes_by_id.get(route_id), dict) else {}
        action = route.get("action") if isinstance(route.get("action"), dict) else {}
        return action

    mindmap_candidate, start_mindmap = workflow_candidate(
        "mindmap_reorganize",
        f"围绕当前对象重组或补全脑图：{object_label}",
        task_id="task_mindmap_operation_plan",
        action_id="start_mindmap_workflow",
        detail="启动当前对象的脑图重组 workflow；写入步骤仍需确认。",
    )
    card_candidate, start_card = workflow_candidate(
        "selection_to_cards",
        f"围绕当前对象生成可复习短卡：{object_label}",
        task_id="task_card_operation_plan",
        action_id="start_card_workflow",
        detail="启动当前对象的制卡 workflow；写入步骤仍需确认。",
    )
    deep_reading_candidate, start_deep_reading = workflow_candidate(
        "paper_deep_reading",
        f"为当前对象启动完整学习 workflow：{object_label}",
        task_id="task_workflow_operation_plan",
        action_id="start_deep_reading_workflow",
        detail="启动当前对象的完整精读 workflow；写入步骤仍需确认。",
    )

    tasks = [
        task_draft(
            "task_source_preflight",
            "route_source_registry",
            "材料读取预检",
            route_status("route_source_registry"),
            "确认当前对象是否有可读 PDF、上传文件或路径来源。",
            route_action=route_action("route_source_registry"),
            evidence=(routes_by_id.get("route_source_registry") or {}).get("evidence", ""),
            output="Source Registry 可读来源或修复动作",
        ),
        task_draft(
            "task_object_inventory",
            "route_object_browser",
            "对象清单预检",
            route_status("route_object_browser"),
            "确认当前 notebook 真实 MN 对象是否已扫描，并打开 Object Browser。",
            route_action=route_action("route_object_browser"),
            evidence=(routes_by_id.get("route_object_browser") or {}).get("evidence", ""),
            output="MNObject Registry / Object Browser",
        ),
        task_draft(
            "task_mindmap_operation_plan",
            "route_mindmap_studio",
            "脑图操作草案",
            "action_required" if has_context else "blocked",
            "围绕当前对象规划脑图补全、重组、合并或新建；只生成计划，不直接写入。",
            route_action=route_action("route_mindmap_studio"),
            compile_action=compile_plan_action(
                "compile_mindmap_task",
                f"围绕当前对象规划脑图操作：{object_label}。先读取现有脑图，输出补全/重组/合并计划，不直接写入。",
                "把当前对象送入 Operation Compiler，生成脑图相关操作计划。",
            ),
            workflow_candidate=mindmap_candidate,
            start_action=start_mindmap,
            evidence=(routes_by_id.get("route_mindmap_studio") or {}).get("evidence", ""),
            output="Operation Plan / Mindmap Studio",
            write_policy="confirmation_required_workflow",
        ),
        task_draft(
            "task_card_operation_plan",
            "route_card_factory",
            "卡片学习草案",
            "action_required" if has_context else "blocked",
            "围绕当前对象规划短卡、来源、学习目标和复习提示；只生成计划，不直接写入。",
            route_action=route_action("route_card_factory"),
            compile_action=compile_plan_action(
                "compile_card_task",
                f"把当前对象规划成可复习短卡：{object_label}。按概念、公式、方法、证据和局限制定制卡计划，不直接写入。",
                "把当前对象送入 Operation Compiler，生成 Card Factory 相关操作计划。",
            ),
            workflow_candidate=card_candidate,
            start_action=start_card,
            evidence=(routes_by_id.get("route_card_factory") or {}).get("evidence", ""),
            output="Operation Plan / Card Factory",
            write_policy="confirmation_required_workflow",
        ),
        task_draft(
            "task_workflow_operation_plan",
            "route_workflow_builder",
            "长任务草案",
            "pending" if has_context else "blocked",
            "把精读、制卡、脑图重组等长任务转成可暂停、可恢复、可验收 workflow 草案。",
            route_action=route_action("route_workflow_builder"),
            compile_action=compile_plan_action(
                "compile_workflow_task",
                f"为当前对象选择可审计 workflow：{object_label}。输出步骤、确认点、证据和风险，不直接写入。",
                "把当前对象送入 Operation Compiler，生成 workflow 级操作计划。",
            ),
            workflow_candidate=deep_reading_candidate,
            start_action=start_deep_reading,
            evidence=(routes_by_id.get("route_workflow_builder") or {}).get("evidence", ""),
            output="Workflow Builder / Operation Plan",
            write_policy="confirmation_required_workflow",
        ),
        task_draft(
            "task_skill_selection",
            "route_skill_center",
            "技能选择草案",
            "pending" if has_context else "blocked",
            "查看可安装或可运行技能包，只有满足权限、dry-run、rollback 和 acceptance 的技能才进入后续计划。",
            route_action=actions_by_id.get("open_skill_center") or route_action("route_skill_center"),
            evidence=(routes_by_id.get("route_skill_center") or {}).get("evidence", ""),
            output="Skill Center / skill operation plan",
        ),
        task_draft(
            "task_verification_review",
            "route_verification_center",
            "验证回滚草案",
            route_status("route_verification_center"),
            "查看当前对象是否已有 PASS/FAIL/UNKNOWN 验证报告，并决定是否需要修复、probe 或回滚。",
            route_action=route_action("route_verification_center"),
            evidence=(routes_by_id.get("route_verification_center") or {}).get("evidence", ""),
            output="Verification Center / Repair Plan",
        ),
    ]
    actionable = [
        task
        for task in tasks
        if task.get("status") in {"action_required", "pending"}
        and (
            (isinstance(task.get("compileAction"), dict) and task.get("compileAction", {}).get("action"))
            or (isinstance(task.get("routeAction"), dict) and task.get("routeAction", {}).get("action"))
        )
    ]
    recommended = actionable[:3] if actionable else tasks[:2]
    return {
        "schema": OBJECT_TASK_COMPOSER_SCHEMA,
        "mode": "draft_first",
        "requiresPrompt": False,
        "writePolicy": "no_write_task_draft",
        "status": "blocked" if not has_context else ("action_required" if any(task.get("status") == "action_required" for task in tasks) else "pending"),
        "objectRef": object_ref,
        "objectLabel": object_label,
        "taskCount": len(tasks),
        "recommendedTaskIds": [str(task.get("id") or "") for task in recommended],
        "tasks": tasks,
    }
