from __future__ import annotations

import re
from typing import Any


WORKFLOW_SCHEMA = "codex.mn.workflowPreview.v1"


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
