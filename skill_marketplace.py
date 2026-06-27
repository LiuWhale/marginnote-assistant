from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


_ROOT = Path.home() / ".codex/marginnote-assistant"
_SKILL_DIR = _ROOT / "skills"
_INSTALLED_PATH = _SKILL_DIR / "installed-skills.json"
_MANIFEST_DIR = _SKILL_DIR / "manifests"
_RUNS_PATH = _SKILL_DIR / "skill-runs.json"

MANIFEST_SCHEMA = "codex.mn.skillManifest.v1"
VALIDATION_SCHEMA = "codex.mn.skillManifestValidation.v1"
OPERATION_PLAN_SCHEMA = "codex.mn.skillOperationPlan.v1"
SKILL_RUN_SCHEMA = "codex.mn.skillRun.v1"


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
        "dryRun": {"required": True, "mode": "operation_plan"},
        "rollback": {"strategy": "ai_edit_transaction", "reason": "写入后通过事务中心保留、回滚和验证。"},
        "acceptanceRules": [
            "写入前必须经过 dry-run 或 AI 编辑确认点。",
            "生成卡片需要来源线索，超长卡或缺来源卡必须进入质量审计。",
            "用户拒绝后必须能通过事务账本回滚本次新增内容。",
        ],
    },
]


def configure(root: Path | str) -> None:
    global _ROOT, _SKILL_DIR, _INSTALLED_PATH, _MANIFEST_DIR, _RUNS_PATH
    _ROOT = Path(root).expanduser()
    _SKILL_DIR = _ROOT / "skills"
    _INSTALLED_PATH = _SKILL_DIR / "installed-skills.json"
    _MANIFEST_DIR = _SKILL_DIR / "manifests"
    _RUNS_PATH = _SKILL_DIR / "skill-runs.json"


def _clean_id(value: Any) -> str:
    return "".join(ch for ch in str(value or "").strip() if ch.isalnum() or ch in "._-")[:120]


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, tuple):
        return [str(item).strip() for item in value if str(item).strip()]
    if value is None or value == "":
        return []
    return [str(value).strip()]


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _canonical_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    raw = manifest if isinstance(manifest, dict) else {}
    skill_id = _clean_id(raw.get("skillId") or raw.get("id"))
    outputs = _clean_list(raw.get("outputs") if "outputs" in raw else raw.get("outputOperations"))
    inputs = _clean_list(raw.get("inputs") if "inputs" in raw else raw.get("inputObjectTypes"))
    actions = _clean_list(raw.get("actions") if "actions" in raw else raw.get("action"))
    prompts = _clean_list(raw.get("prompts") if "prompts" in raw else raw.get("promptTemplate"))
    acceptance_rules = _clean_list(raw.get("acceptanceRules") if "acceptanceRules" in raw else raw.get("acceptance"))
    permissions = _clean_list(raw.get("permissions") if "permissions" in raw else raw.get("permission"))
    permission = str(raw.get("permission") or "").strip()
    if not permission:
        lowered_permissions = {item.lower() for item in permissions}
        if "delete" in lowered_permissions:
            permission = "delete"
        elif lowered_permissions.intersection({"notes", "write", "mindmap", "cards"}):
            permission = "notes"
        else:
            permission = "read_only"
    dry_run = raw.get("dryRun")
    if isinstance(dry_run, bool):
        dry_run = {"required": dry_run}
    rollback = raw.get("rollback") if isinstance(raw.get("rollback"), dict) else {}
    action_payload = raw.get("actionPayload") if isinstance(raw.get("actionPayload"), dict) else {}
    normalized = {
        "schema": str(raw.get("schema") or MANIFEST_SCHEMA),
        "id": skill_id,
        "skillId": skill_id,
        "title": str(raw.get("title") or raw.get("name") or skill_id or "").strip(),
        "name": str(raw.get("name") or raw.get("title") or skill_id or "").strip(),
        "version": str(raw.get("version") or "").strip(),
        "category": str(raw.get("category") or "custom").strip(),
        "description": str(raw.get("description") or "").strip(),
        "permission": permission,
        "permissions": permissions or [permission],
        "inputObjectTypes": inputs,
        "inputs": inputs,
        "outputOperations": outputs,
        "outputs": outputs,
        "actions": actions,
        "action": str(raw.get("action") or (actions[0] if actions else "")).strip(),
        "actionPayload": action_payload,
        "uiPanel": str(raw.get("uiPanel") or "skill").strip(),
        "promptTemplate": str(raw.get("promptTemplate") or (prompts[0] if prompts else "")).strip(),
        "prompts": prompts,
        "requiresConfirmation": _truthy(raw.get("requiresConfirmation")),
        "dryRun": dry_run if isinstance(dry_run, dict) else {},
        "rollback": rollback,
        "acceptanceRules": acceptance_rules,
        "acceptance": acceptance_rules,
        "allowsDelete": _truthy(raw.get("allowsDelete")),
        "deleteConfirmationRule": raw.get("deleteConfirmationRule") or "",
    }
    return normalized


def _risk_level(manifest: dict[str, Any]) -> str:
    permission = str(manifest.get("permission") or "").lower()
    ops = " ".join(_clean_list(manifest.get("outputOperations")) + _clean_list(manifest.get("actions"))).lower()
    if permission == "delete" or "delete" in ops or "remove" in ops:
        return "delete"
    if permission not in {"", "read_only", "read-only", "read"}:
        return "write"
    if any(token in ops for token in ["write", "create", "update", "mindmap", "card", "note"]):
        return "write"
    return "read"


def _safety_badges(manifest: dict[str, Any], risk_level: str) -> list[str]:
    badges = ["只读" if risk_level == "read" else ("删除" if risk_level == "delete" else "写入")]
    if manifest.get("requiresConfirmation"):
        badges.append("确认")
    if isinstance(manifest.get("dryRun"), dict) and manifest["dryRun"]:
        badges.append("预演")
    rollback = manifest.get("rollback") if isinstance(manifest.get("rollback"), dict) else {}
    if rollback and rollback.get("strategy") != "not_required":
        badges.append("回滚")
    if risk_level == "delete" and manifest.get("allowsDelete"):
        badges.append("允许删除")
    return badges


def validate_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    normalized = _canonical_manifest(manifest)
    missing: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    if normalized["schema"] != MANIFEST_SCHEMA:
        errors.append("schema must be codex.mn.skillManifest.v1")
    for field in ["id", "title", "version"]:
        if not _is_present(normalized.get(field)):
            missing.append(field)
    risk_level = _risk_level(normalized)
    if risk_level in {"write", "delete"}:
        if not normalized.get("requiresConfirmation"):
            missing.append("requiresConfirmation")
        dry_run = normalized.get("dryRun") if isinstance(normalized.get("dryRun"), dict) else {}
        if not dry_run or dry_run.get("required") is False:
            missing.append("dryRun")
        rollback = normalized.get("rollback") if isinstance(normalized.get("rollback"), dict) else {}
        if not rollback or not rollback.get("strategy"):
            missing.append("rollback")
        if not normalized.get("acceptanceRules"):
            missing.append("acceptance")
    else:
        rollback = normalized.get("rollback") if isinstance(normalized.get("rollback"), dict) else {}
        if not rollback:
            normalized["rollback"] = {"strategy": "not_required", "reason": "只读技能不写入 MarginNote。"}
    if risk_level == "delete":
        if not normalized.get("allowsDelete"):
            missing.append("allowsDelete")
        if not _is_present(normalized.get("deleteConfirmationRule")):
            missing.append("deleteConfirmationRule")
    missing = sorted(set(missing))
    ok = not missing and not errors
    validation = {
        "ok": ok,
        "schema": VALIDATION_SCHEMA,
        "manifestId": normalized.get("id") or "",
        "status": "valid" if ok else "invalid",
        "riskLevel": risk_level,
        "missing": missing,
        "errors": errors,
        "warnings": warnings,
        "safetyBadges": _safety_badges(normalized, risk_level),
        "normalizedManifest": normalized,
        "message": "技能 manifest 有效。" if ok else "技能 manifest 未通过安全校验。",
    }
    return validation


def _external_manifest_path(skill_id: str) -> Path:
    return _MANIFEST_DIR / f"{_clean_id(skill_id)}.json"


def _read_external_manifests() -> list[dict[str, Any]]:
    if not _MANIFEST_DIR.exists():
        return []
    manifests: list[dict[str, Any]] = []
    for path in sorted(_MANIFEST_DIR.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(raw, dict):
            manifests.append(raw)
    return manifests


def _all_manifests() -> list[dict[str, Any]]:
    external = _read_external_manifests()
    external_ids = {_clean_id(item.get("skillId") or item.get("id")) for item in external}
    builtins = [dict(skill) for skill in BUILTIN_SKILLS if _clean_id(skill.get("id")) not in external_ids]
    return builtins + external


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
    for skill in _all_manifests():
        normalized = _canonical_manifest(skill)
        if normalized["id"] == clean:
            return dict(skill)
    return None


def _with_install_state(skill: dict[str, Any], installed_state: dict[str, Any]) -> dict[str, Any]:
    validation = validate_manifest(skill)
    skill = dict(validation["normalizedManifest"])
    installed_ids = set(installed_state.get("installedSkillIds") or [])
    skill["installed"] = skill["id"] in installed_ids
    skill["installedAt"] = str((installed_state.get("installedAt") or {}).get(skill["id"]) or "")
    skill["schema"] = MANIFEST_SCHEMA
    skill["validation"] = {key: value for key, value in validation.items() if key != "normalizedManifest"}
    skill["riskLevel"] = validation["riskLevel"]
    skill["safetyBadges"] = validation["safetyBadges"]
    skill["canRun"] = bool(validation["ok"])
    return skill


def status() -> dict[str, Any]:
    installed_state = _read_installed()
    skills = [_with_install_state(skill, installed_state) for skill in _all_manifests()]
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
        "invalidSkillCount": sum(1 for skill in skills if not skill.get("validation", {}).get("ok")),
        "path": str(_INSTALLED_PATH),
    }


def install(skill_id: str) -> dict[str, Any]:
    skill = _skill_by_id(skill_id)
    if not skill:
        return {"ok": False, "message": "未找到该技能包。", "skillId": _clean_id(skill_id)}
    validation = validate_manifest(skill)
    if not validation["ok"]:
        return {"ok": False, "message": "技能 manifest 未通过安全校验，已拒绝安装。", "validation": validation}
    state = _read_installed()
    installed_ids = set(state.get("installedSkillIds") or [])
    normalized = validation["normalizedManifest"]
    installed_ids.add(normalized["id"])
    installed_at = state.get("installedAt") if isinstance(state.get("installedAt"), dict) else {}
    installed_at[normalized["id"]] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state = {"installedSkillIds": sorted(installed_ids), "installedAt": installed_at}
    _write_installed(state)
    return {
        "ok": True,
        "message": f"已安装技能：{normalized['title']}",
        "skill": _with_install_state(normalized, state),
        "installedSkillIds": state["installedSkillIds"],
        "marketplace": status(),
    }


def install_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    validation = validate_manifest(manifest)
    if not validation["ok"]:
        return {"ok": False, "message": "技能 manifest 未通过安全校验，已拒绝安装。", "validation": validation}
    normalized = validation["normalizedManifest"]
    _MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    _external_manifest_path(normalized["id"]).write_text(
        json.dumps(normalized, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    installed = install(normalized["id"])
    installed["validation"] = validation
    return installed


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


def skill_operation_plan(skill_id: str, object_ref: dict[str, Any] | None = None) -> dict[str, Any]:
    clean = _clean_id(skill_id)
    skill = _skill_by_id(clean)
    if not skill:
        return {"ok": False, "message": "未找到该技能包。", "skillId": clean}
    validation = validate_manifest(skill)
    if not validation["ok"]:
        return {
            "ok": False,
            "message": "技能 manifest 未通过安全校验，无法生成操作计划。",
            "skillId": clean,
            "validation": validation,
        }
    installed_state = _read_installed()
    if clean not in set(installed_state.get("installedSkillIds") or []):
        return {"ok": False, "message": "技能尚未安装。", "skillId": clean, "validation": validation}
    normalized = validation["normalizedManifest"]
    risk_level = validation["riskLevel"]
    operations = []
    for index, operation in enumerate(normalized.get("outputOperations") or normalized.get("actions") or [], start=1):
        operations.append(
            {
                "index": index,
                "operation": operation,
                "phase": "dry_run" if risk_level in {"write", "delete"} else "read",
                "requiresConfirmation": bool(normalized.get("requiresConfirmation")),
            }
        )
    return {
        "ok": True,
        "schema": OPERATION_PLAN_SCHEMA,
        "skillId": clean,
        "title": normalized.get("title") or clean,
        "objectRef": object_ref if isinstance(object_ref, dict) else {},
        "riskLevel": risk_level,
        "safetyBadges": validation["safetyBadges"],
        "executionMode": "dry_run_first" if risk_level in {"write", "delete"} else "direct_read_only",
        "requiresConfirmation": bool(normalized.get("requiresConfirmation")),
        "dryRun": normalized.get("dryRun") if isinstance(normalized.get("dryRun"), dict) else {},
        "rollback": normalized.get("rollback") if isinstance(normalized.get("rollback"), dict) else {},
        "acceptanceRules": list(normalized.get("acceptanceRules") or []),
        "operations": operations,
        "validation": validation,
    }


def _read_runs() -> list[dict[str, Any]]:
    if not _RUNS_PATH.exists():
        return []
    try:
        raw = json.loads(_RUNS_PATH.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(raw, dict):
        raw = raw.get("runs")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _write_runs(runs: list[dict[str, Any]]) -> None:
    _SKILL_DIR.mkdir(parents=True, exist_ok=True)
    _RUNS_PATH.write_text(
        json.dumps({"schema": "codex.mn.skillRunLedger.v1", "runs": runs}, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def record_skill_run(payload: dict[str, Any]) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    skill_id = _clean_id(payload.get("skillId") or payload.get("id"))
    now_ms = int(time.time() * 1000)
    record = {
        "schema": SKILL_RUN_SCHEMA,
        "runId": f"skillrun_{now_ms}_{skill_id or 'unknown'}",
        "skillId": skill_id,
        "objectRef": payload.get("objectRef") if isinstance(payload.get("objectRef"), dict) else {},
        "status": str(payload.get("status") or "unknown"),
        "phase": str(payload.get("phase") or ""),
        "backend": str(payload.get("backend") or ""),
        "acceptance": payload.get("acceptance") if isinstance(payload.get("acceptance"), dict) else {},
        "createdAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    runs = _read_runs()
    runs.insert(0, record)
    _write_runs(runs[:200])
    return {"ok": True, "message": "技能运行记录已保存。", "record": record, "path": str(_RUNS_PATH)}


def latest_skill_runs(limit: int = 10) -> dict[str, Any]:
    try:
        safe_limit = max(1, min(100, int(limit)))
    except Exception:
        safe_limit = 10
    runs = _read_runs()[:safe_limit]
    return {
        "ok": True,
        "schema": "codex.mn.skillRunLedger.v1",
        "runs": runs,
        "runCount": len(runs),
        "path": str(_RUNS_PATH),
    }
