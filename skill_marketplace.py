from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


_ROOT = Path.home() / ".codex/marginnote-assistant"
_SKILL_DIR = _ROOT / "skills"
_INSTALLED_PATH = _SKILL_DIR / "installed-skills.json"


BUILTIN_SKILLS: list[dict[str, Any]] = [
    {
        "id": "knowledge.related_context",
        "title": "相关知识检索",
        "version": "0.1.0",
        "category": "knowledge",
        "description": "围绕当前 MNObject 检索已授权的本地知识索引，并把来源、页码和关系作为回答证据。",
        "permission": "read_only",
        "inputObjectTypes": ["selection", "note", "document", "notebook"],
        "outputOperations": ["knowledge_index_search"],
        "action": "knowledge_index_search",
        "uiPanel": "knowledge",
        "promptTemplate": "检索和当前对象相关的历史知识、证据、支持/反驳关系，并列出来源。",
        "requiresConfirmation": False,
        "rollback": {"strategy": "not_required", "reason": "只读检索不写入 MarginNote。"},
        "acceptanceRules": [
            "只返回当前用户授权范围内的索引结果。",
            "每条结果必须保留 title、sourceRef 或 noteId 之一，避免无来源回答。",
        ],
    },
    {
        "id": "workflow.deep_reading_writer",
        "title": "文档精读写入工作流",
        "version": "0.1.0",
        "category": "workflow",
        "description": "对当前文档执行精读、脑图树和短卡草稿生成，并通过确认点写入 MarginNote。",
        "permission": "notes",
        "inputObjectTypes": ["document"],
        "outputOperations": ["workflow_start", "generate_mindmap", "generate_card", "write_draft"],
        "action": "workflow_start",
        "actionPayload": {"workflowId": "paper_deep_reading"},
        "uiPanel": "workflow",
        "promptTemplate": "精读当前文档，生成结构化脑图树和大小适中的短卡草稿。",
        "requiresConfirmation": True,
        "rollback": {"strategy": "ai_edit_transaction", "reason": "写入后通过事务中心保留、回滚和验证。"},
        "acceptanceRules": [
            "写入前必须经过 dry-run 或 AI 编辑确认点。",
            "生成卡片需要来源线索，超长卡或缺来源卡必须进入质量审计。",
            "用户拒绝后必须能通过事务账本回滚本次新增内容。",
        ],
    },
]


def configure(root: Path | str) -> None:
    global _ROOT, _SKILL_DIR, _INSTALLED_PATH
    _ROOT = Path(root).expanduser()
    _SKILL_DIR = _ROOT / "skills"
    _INSTALLED_PATH = _SKILL_DIR / "installed-skills.json"


def _clean_id(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip() if ch.isalnum() or ch in "._-")[:120]


def _read_installed() -> dict[str, Any]:
    if not _INSTALLED_PATH.exists():
        return {"installedSkillIds": [], "installedAt": {}}
    try:
        raw = json.loads(_INSTALLED_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"installedSkillIds": [], "installedAt": {}}
    if not isinstance(raw, dict):
        return {"installedSkillIds": [], "installedAt": {}}
    ids = [_clean_id(item) for item in raw.get("installedSkillIds", []) if _clean_id(item)]
    installed_at = raw.get("installedAt") if isinstance(raw.get("installedAt"), dict) else {}
    return {"installedSkillIds": sorted(set(ids)), "installedAt": installed_at}


def _write_installed(state: dict[str, Any]) -> None:
    _SKILL_DIR.mkdir(parents=True, exist_ok=True)
    _INSTALLED_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def _skill_by_id(skill_id: str) -> dict[str, Any] | None:
    clean = _clean_id(skill_id)
    for skill in BUILTIN_SKILLS:
        if skill["id"] == clean:
            return dict(skill)
    return None


def _with_install_state(skill: dict[str, Any], installed_state: dict[str, Any]) -> dict[str, Any]:
    skill = dict(skill)
    installed_ids = set(installed_state.get("installedSkillIds") or [])
    skill["installed"] = skill["id"] in installed_ids
    skill["installedAt"] = str((installed_state.get("installedAt") or {}).get(skill["id"]) or "")
    skill["schema"] = "codex.mn.skillManifest.v1"
    return skill


def status() -> dict[str, Any]:
    installed_state = _read_installed()
    skills = [_with_install_state(skill, installed_state) for skill in BUILTIN_SKILLS]
    return {
        "ok": True,
        "schema": "codex.mn.skillMarketplace.v1",
        "message": f"技能市场：{len(skills)} 个内置技能，已安装 {len(installed_state['installedSkillIds'])} 个。",
        "skills": skills,
        "skillCount": len(skills),
        "installedCount": len(installed_state["installedSkillIds"]),
        "installedSkillIds": installed_state["installedSkillIds"],
        "readOnlyCount": sum(1 for skill in skills if skill.get("permission") == "read_only"),
        "writeSkillCount": sum(1 for skill in skills if skill.get("permission") != "read_only"),
        "path": str(_INSTALLED_PATH),
    }


def install(skill_id: str) -> dict[str, Any]:
    skill = _skill_by_id(skill_id)
    if not skill:
        return {"ok": False, "message": "未找到该技能包。", "skillId": _clean_id(skill_id)}
    state = _read_installed()
    installed_ids = set(state.get("installedSkillIds") or [])
    installed_ids.add(skill["id"])
    installed_at = state.get("installedAt") if isinstance(state.get("installedAt"), dict) else {}
    installed_at[skill["id"]] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state = {"installedSkillIds": sorted(installed_ids), "installedAt": installed_at}
    _write_installed(state)
    return {
        "ok": True,
        "message": f"已安装技能：{skill['title']}",
        "skill": _with_install_state(skill, state),
        "installedSkillIds": state["installedSkillIds"],
        "marketplace": status(),
    }


def uninstall(skill_id: str) -> dict[str, Any]:
    clean = _clean_id(skill_id)
    state = _read_installed()
    installed_ids = set(state.get("installedSkillIds") or [])
    installed_ids.discard(clean)
    installed_at = state.get("installedAt") if isinstance(state.get("installedAt"), dict) else {}
    installed_at.pop(clean, None)
    state = {"installedSkillIds": sorted(installed_ids), "installedAt": installed_at}
    _write_installed(state)
    return {
        "ok": True,
        "message": "技能已卸载。",
        "skillId": clean,
        "installedSkillIds": state["installedSkillIds"],
        "marketplace": status(),
    }
