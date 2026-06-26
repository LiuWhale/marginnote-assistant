from __future__ import annotations

import copy
import re
from typing import Any


MANIFEST_SCHEMA = "codex.mn.operationManifest.v1"
PLAN_SCHEMA = "codex.mn.operationPlan.v1"
PER_OPERATION_DRY_RUN_SCHEMA = "codex.mn.perOperationDryRun.v1"
MINDMAP_DIFF_SCHEMA = "codex.mn.mindmapDiff.v1"
MINDMAP_DIFF_OPERATION_PLAN_SCHEMA = "codex.mn.mindmapDiffOperationPlan.v1"
CARD_QUALITY_SCHEMA = "codex.mn.cardQuality.v1"
CARD_BODY_TARGET_MAX = 900


def _clean_text(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    if len(text) > limit:
        return text[: max(0, limit - 1)] + "..."
    return text


def _target_summary(write_target: dict[str, Any] | None) -> dict[str, str]:
    target = write_target if isinstance(write_target, dict) else {}
    keys = [
        "mode",
        "operation",
        "label",
        "rootTitle",
        "selectedNoteId",
        "selectedNoteTitle",
        "codexId",
        "topicid",
        "bookmd5",
    ]
    return {key: _clean_text(target.get(key), 200) for key in keys if _clean_text(target.get(key), 200)}


def count_mindmap_nodes(node: Any) -> int:
    if not isinstance(node, dict):
        return 0
    total = 1
    children = node.get("children") if isinstance(node.get("children"), list) else []
    for child in children:
        total += count_mindmap_nodes(child)
    return total


def _normalize_mindmap_key(value: Any) -> str:
    text = str(value or "").lower()
    text = re.sub(r"[\s\-_/#:：,，.;；、()[\]{}<>《》\"'“”‘’]+", "", text)
    return text


def _mindmap_body(node: dict[str, Any]) -> str:
    return str(node.get("body") or node.get("comment") or node.get("content") or "").strip()


def _mindmap_node_ref(node: dict[str, Any] | None) -> dict[str, Any]:
    node = node if isinstance(node, dict) else {}
    ref: dict[str, Any] = {}
    note_id = _clean_text(node.get("noteId") or node.get("noteid") or node.get("id"), 160)
    codex_id = _clean_text(node.get("codexId") or node.get("codex_id"), 160)
    source_id = _clean_text(node.get("sourceId") or node.get("source_id"), 160)
    if note_id:
        ref["noteId"] = note_id
    if codex_id:
        ref["codexId"] = codex_id
    if source_id:
        ref["sourceId"] = source_id
    return ref


def _mindmap_source(node: dict[str, Any] | None) -> dict[str, Any]:
    node = node if isinstance(node, dict) else {}
    source = node.get("source") if isinstance(node.get("source"), dict) else {}
    clean: dict[str, Any] = {}
    for key in ["page", "pageLabel", "quote", "url", "noteId", "docMd5", "bookMd5"]:
        value = source.get(key) if isinstance(source, dict) else None
        if value is None:
            value = node.get(key)
        if value is None or value == "":
            continue
        clean[key] = value if isinstance(value, (int, float)) else _clean_text(value, 240)
    return clean


def _flatten_mindmap_nodes(node: Any, *, path: str = "0", parent_path: str = "", depth: int = 0) -> list[dict[str, Any]]:
    if not isinstance(node, dict):
        return []
    title = _clean_text(node.get("title") or "未命名脑图节点", 120) or "未命名脑图节点"
    body = _mindmap_body(node)
    item = {
        "title": title,
        "key": _normalize_mindmap_key(title),
        "body": body,
        "bodyKey": _normalize_mindmap_key(body),
        "path": path,
        "parentPath": parent_path,
        "depth": depth,
        "ref": _mindmap_node_ref(node),
        "source": _mindmap_source(node),
    }
    out = [item]
    children = node.get("children") if isinstance(node.get("children"), list) else []
    for index, child in enumerate(children, start=1):
        out.extend(_flatten_mindmap_nodes(child, path=f"{path}.{index}", parent_path=path, depth=depth + 1))
    return out


def _mindmap_hierarchy(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    level_counts: dict[str, int] = {}
    max_depth = 0
    for node in nodes:
        depth = int(node.get("depth") or 0)
        max_depth = max(max_depth, depth)
        key = str(depth)
        level_counts[key] = level_counts.get(key, 0) + 1
    return {
        "maxDepth": max_depth,
        "levelCounts": level_counts,
    }


def _index_existing_mindmap(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for node in nodes:
        key = str(node.get("key") or "")
        if key and key not in index:
            index[key] = node
    return index


def _mindmap_diff_operation(
    *,
    op: str,
    node: dict[str, Any],
    reason: str,
    target: dict[str, str],
    existing: dict[str, Any] | None = None,
    duplicate_of: str = "",
) -> dict[str, Any]:
    existing = existing if isinstance(existing, dict) else {}
    target_parent = str(existing.get("parentPath") or node.get("parentPath") or target.get("label") or "")
    rollback = {
        "type": "delete_created_node" if op == "create" else "restore_previous_node",
        "proposedPath": str(node.get("path") or ""),
        "existingPath": str(existing.get("path") or ""),
        "requiresTransactionLedger": True,
    }
    if op == "merge":
        rollback["type"] = "no_write_or_restore_merge"
    if op == "delete_suggest":
        rollback["type"] = "no_write_until_delete_confirmed"
    return {
        "op": op,
        "title": str(node.get("title") or ""),
        "shortBody": _clean_text(node.get("body"), 220),
        "proposedPath": str(node.get("path") or ""),
        "existingPath": str(existing.get("path") or ""),
        "duplicateOf": duplicate_of,
        "targetParent": target_parent,
        "proposedRef": {} if op == "delete_suggest" else (node.get("ref") if isinstance(node.get("ref"), dict) else {}),
        "currentRef": existing.get("ref") if isinstance(existing.get("ref"), dict) else {},
        "source": node.get("source") if isinstance(node.get("source"), dict) else {},
        "confidence": 0.96 if reason in {"title-match", "same-body"} else 0.82,
        "reason": reason,
        "rollback": rollback,
    }


def build_mindmap_diff(
    proposed_mindmap: dict[str, Any] | None,
    current_mindmap: dict[str, Any] | None,
    target: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proposed_nodes = _flatten_mindmap_nodes(proposed_mindmap)
    current_nodes = _flatten_mindmap_nodes(current_mindmap)
    target_summary = _target_summary(target)
    existing_by_title = _index_existing_mindmap(current_nodes)
    first_proposed_by_title: dict[str, dict[str, Any]] = {}
    operations: list[dict[str, Any]] = []
    duplicates: list[dict[str, str]] = []
    counts = {
        "create": 0,
        "update": 0,
        "merge": 0,
        "move": 0,
        "delete_suggest": 0,
    }

    for node in proposed_nodes:
        title_key = str(node.get("key") or "")
        existing = existing_by_title.get(title_key)
        duplicate_of = ""
        if title_key and title_key in first_proposed_by_title:
            first = first_proposed_by_title[title_key]
            duplicate_of = str(first.get("path") or "")
            duplicates.append(
                {
                    "title": str(node.get("title") or ""),
                    "path": str(node.get("path") or ""),
                    "duplicateOf": duplicate_of,
                }
            )
            op = "merge"
            reason = "duplicate-proposed-title"
            existing = existing or first
        elif existing:
            if str(existing.get("bodyKey") or "") and str(node.get("bodyKey") or "") and existing.get("bodyKey") != node.get("bodyKey"):
                op = "update"
                reason = "body-diff"
            else:
                op = "merge"
                reason = "title-match"
        else:
            op = "create"
            reason = "new-title"

        if title_key and title_key not in first_proposed_by_title:
            first_proposed_by_title[title_key] = node
        counts[op] = counts.get(op, 0) + 1
        operations.append(
            _mindmap_diff_operation(
                op=op,
                node=node,
                reason=reason,
                target=target_summary,
                existing=existing,
                duplicate_of=duplicate_of,
            )
        )

    proposed_keys = {str(node.get("key") or "") for node in proposed_nodes if str(node.get("key") or "")}
    for current in current_nodes:
        title_key = str(current.get("key") or "")
        if not title_key or title_key in proposed_keys:
            continue
        if int(current.get("depth") or 0) <= 0:
            continue
        counts["delete_suggest"] = counts.get("delete_suggest", 0) + 1
        operations.append(
            _mindmap_diff_operation(
                op="delete_suggest",
                node=current,
                reason="missing-in-proposed-tree",
                target=target_summary,
                existing=current,
            )
        )

    hierarchy = _mindmap_hierarchy(proposed_nodes)
    return {
        "schema": MINDMAP_DIFF_SCHEMA,
        "status": "ready" if proposed_nodes else "empty",
        "target": target_summary,
        "summary": {
            "proposedCount": len(proposed_nodes),
            "currentCount": len(current_nodes),
            "createCount": counts["create"],
            "updateCount": counts["update"],
            "mergeCount": counts["merge"],
            "moveCount": counts["move"],
            "deleteSuggestCount": counts["delete_suggest"],
            "duplicateCount": len(duplicates),
        },
        "hierarchy": hierarchy,
        "operations": operations,
        "duplicates": duplicates,
    }


def prune_mindmap_by_paths(mindmap: dict[str, Any] | None, excluded_paths: list[Any] | None) -> dict[str, Any]:
    if not isinstance(mindmap, dict):
        return {}
    excluded = {
        str(path).strip()
        for path in (excluded_paths or [])
        if re.fullmatch(r"\d+(?:\.\d+)*", str(path).strip() or "")
    }

    def clone_node(node: dict[str, Any], path: str) -> dict[str, Any] | None:
        if path in excluded:
            return None
        cloned = {key: copy.deepcopy(value) for key, value in node.items() if key != "children"}
        children = node.get("children") if isinstance(node.get("children"), list) else []
        cloned_children: list[dict[str, Any]] = []
        for index, child in enumerate(children, start=1):
            if not isinstance(child, dict):
                continue
            child_clone = clone_node(child, f"{path}.{index}")
            if child_clone is not None:
                cloned_children.append(child_clone)
        cloned["children"] = cloned_children
        return cloned

    return clone_node(mindmap, "0") or {}


def edit_mindmap_nodes_by_paths(mindmap: dict[str, Any] | None, node_edits: list[Any] | None) -> dict[str, Any]:
    if not isinstance(mindmap, dict):
        return {}
    edits: dict[str, dict[str, str]] = {}
    for raw in node_edits or []:
        if not isinstance(raw, dict):
            continue
        path = str(raw.get("proposedPath") or raw.get("path") or "").strip()
        if not re.fullmatch(r"\d+(?:\.\d+)*", path):
            continue
        edit: dict[str, str] = {}
        if "title" in raw:
            title = _clean_text(raw.get("title"), 180)
            if title:
                edit["title"] = title
        if "body" in raw or "shortBody" in raw:
            edit["body"] = _clean_text(raw.get("body") if "body" in raw else raw.get("shortBody"), 2000)
        if edit:
            edits[path] = edit

    def clone_node(node: dict[str, Any], path: str) -> dict[str, Any]:
        cloned = {key: copy.deepcopy(value) for key, value in node.items() if key != "children"}
        edit = edits.get(path) or {}
        if "title" in edit:
            cloned["title"] = edit["title"]
        if "body" in edit:
            cloned["body"] = edit["body"]
        children = node.get("children") if isinstance(node.get("children"), list) else []
        cloned_children: list[dict[str, Any]] = []
        for index, child in enumerate(children, start=1):
            if not isinstance(child, dict):
                continue
            cloned_children.append(clone_node(child, f"{path}.{index}"))
        cloned["children"] = cloned_children
        return cloned

    return clone_node(mindmap, "0")


def build_mindmap_diff_operation_plan(
    mindmap_diff: dict[str, Any] | None,
    excluded_paths: list[Any] | None = None,
) -> dict[str, Any]:
    diff = mindmap_diff if isinstance(mindmap_diff, dict) else {}
    excluded = {
        str(path).strip()
        for path in (excluded_paths or [])
        if re.fullmatch(r"\d+(?:\.\d+)*", str(path).strip() or "")
    }
    operations_in = diff.get("operations") if isinstance(diff.get("operations"), list) else []
    op_map = {
        "create": ("create_mindmap_node", "create", ["nativeMindmap"]),
        "update": ("update_mindmap_node", "update", ["nativeMindmapUpdate"]),
        "merge": ("merge_mindmap_node", "merge", ["nativeMindmapMerge"]),
        "move": ("move_mindmap_node", "move", ["nativeMindmapMove"]),
        "delete_suggest": ("suggest_delete_mindmap_node", "delete_suggest", ["nativeMindmapDelete"]),
    }
    operations: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []

    for index, raw in enumerate(operations_in, start=1):
        if not isinstance(raw, dict):
            continue
        proposed_path = str(raw.get("proposedPath") or "")
        diff_op = str(raw.get("op") or "")
        op_name, mutation, requires = op_map.get(diff_op, ("inspect_mindmap_node", "read", []))
        if proposed_path in excluded:
            skipped.append(
                {
                    "opId": f"mindmap-diff:{index}",
                    "op": op_name,
                    "diffOp": diff_op,
                    "mutation": mutation,
                    "kind": "mindmap",
                    "title": _clean_text(raw.get("title"), 120),
                    "bodyPreview": _clean_text(raw.get("shortBody"), 180),
                    "proposedPath": proposed_path,
                    "existingPath": str(raw.get("existingPath") or ""),
                    "targetParent": _clean_text(raw.get("targetParent"), 160),
                    "duplicateOf": str(raw.get("duplicateOf") or ""),
                    "currentRef": raw.get("currentRef") if isinstance(raw.get("currentRef"), dict) else {},
                    "proposedRef": raw.get("proposedRef") if isinstance(raw.get("proposedRef"), dict) else {},
                    "source": raw.get("source") if isinstance(raw.get("source"), dict) else {},
                    "requires": requires,
                    "rollback": raw.get("rollback") if isinstance(raw.get("rollback"), dict) else {},
                    "selected": False,
                    "selectionState": "excluded_by_user",
                    "reason": "excluded-by-user",
                    "confirmationRequired": mutation == "delete_suggest",
                    "confirmationType": "delete_existing_mindmap_node" if mutation == "delete_suggest" else "",
                }
            )
            continue
        operations.append(
            {
                "opId": f"mindmap-diff:{index}",
                "op": op_name,
                "diffOp": diff_op,
                "mutation": mutation,
                "kind": "mindmap",
                "title": _clean_text(raw.get("title"), 120),
                "bodyPreview": _clean_text(raw.get("shortBody"), 180),
                "proposedPath": proposed_path,
                "existingPath": str(raw.get("existingPath") or ""),
                "targetParent": _clean_text(raw.get("targetParent"), 160),
                "duplicateOf": str(raw.get("duplicateOf") or ""),
                "currentRef": raw.get("currentRef") if isinstance(raw.get("currentRef"), dict) else {},
                "proposedRef": raw.get("proposedRef") if isinstance(raw.get("proposedRef"), dict) else {},
                "source": raw.get("source") if isinstance(raw.get("source"), dict) else {},
                "requires": requires,
                "rollback": raw.get("rollback") if isinstance(raw.get("rollback"), dict) else {},
                "selected": True,
                "selectionState": "included",
                "confirmationRequired": mutation == "delete_suggest",
                "confirmationType": "delete_existing_mindmap_node" if mutation == "delete_suggest" else "",
            }
        )

    required_capabilities = sorted({requirement for op in operations for requirement in op.get("requires", [])})
    planned_mutations: list[str] = []
    for operation in operations:
        mutation = str(operation.get("mutation") or "")
        if mutation and mutation not in planned_mutations:
            planned_mutations.append(mutation)
    directly_executable = [mutation for mutation in planned_mutations if mutation == "create"]
    blocked_local = [
        mutation
        for mutation in planned_mutations
        if mutation not in directly_executable and mutation not in {"read"}
    ]
    create_only_local_apply = bool(operations) and bool(directly_executable) and not blocked_local
    delete_suggest_count = sum(1 for operation in operations if operation.get("mutation") == "delete_suggest")
    return {
        "schema": MINDMAP_DIFF_OPERATION_PLAN_SCHEMA,
        "status": "ready" if operations else "empty",
        "operationCount": len(operations),
        "skippedCount": len(skipped),
        "operations": operations,
        "skipped": skipped,
        "requiredCapabilities": required_capabilities,
        "applyBoundary": {
            "localApplyStatus": "ready" if create_only_local_apply else "preview_only",
            "currentApplyPath": "local_operation_queue" if create_only_local_apply else "draft_tree_write",
            "plannedLocalMutations": planned_mutations,
            "directlyExecutableMutations": directly_executable,
            "blockedLocalMutations": blocked_local,
            "confirmationRequiredMutations": [
                mutation for mutation in planned_mutations if mutation == "delete_suggest"
            ],
            "deleteSuggestCount": delete_suggest_count,
            "acceptButtonBehavior": "queues_local_create_operations" if create_only_local_apply else "writes_pruned_proposed_tree",
            "message": (
                "当前面板可将 create-only 的脑图 Diff 排队给 MN 原生局部执行器。"
                if create_only_local_apply
                else "当前面板已经能生成局部 create/update/merge/move 操作计划；"
                "接受按钮仍走草稿树写入路径。局部 update/merge/move 需要后续 MN 原生执行器。"
            ),
        },
    }


def _flatten_mindmap_operations(
    node: dict[str, Any],
    *,
    path: str = "0",
    parent_ref: str = "",
    depth: int = 0,
    target_mode: str = "",
) -> list[dict[str, Any]]:
    title = _clean_text(node.get("title") or "未命名脑图节点", 120) or "未命名脑图节点"
    body = _clean_text(node.get("body") or node.get("comment") or node.get("content") or "", 180)
    op_id = f"mindmap:{path}"
    operation = {
        "opId": op_id,
        "op": "create_mindmap_node",
        "mutation": "create",
        "kind": "mindmap",
        "title": title,
        "bodyPreview": body,
        "bodyLength": len(str(node.get("body") or node.get("comment") or node.get("content") or "")),
        "path": path,
        "parentRef": parent_ref,
        "depth": depth,
        "targetMode": target_mode,
        "requires": ["nativeMindmap"],
    }
    operations = [operation]
    children = node.get("children") if isinstance(node.get("children"), list) else []
    for index, child in enumerate(children, start=1):
        if not isinstance(child, dict):
            continue
        operations.extend(
            _flatten_mindmap_operations(
                child,
                path=f"{path}.{index}",
                parent_ref=op_id,
                depth=depth + 1,
                target_mode=target_mode,
            )
        )
    return operations


def build_operation_plan(
    cards: list[Any] | None,
    mindmap: dict[str, Any] | None,
    write_target: dict[str, Any] | None,
) -> dict[str, Any]:
    clean_cards = [item for item in (cards or []) if isinstance(item, dict)]
    target = _target_summary(write_target)
    target_mode = target.get("mode", "")
    operations: list[dict[str, Any]] = []
    for index, card in enumerate(clean_cards, start=1):
        body = str(card.get("body") or card.get("comment") or "")
        operations.append(
            {
                "opId": f"card:{index}",
                "op": "create_note",
                "mutation": "create",
                "kind": "card",
                "title": _clean_text(card.get("title") or f"卡片 {index}", 120) or f"卡片 {index}",
                "bodyPreview": _clean_text(body, 180),
                "bodyLength": len(body),
                "targetMode": target_mode,
                "requires": ["nativeCards"],
            }
        )
    if isinstance(mindmap, dict):
        operations.extend(_flatten_mindmap_operations(mindmap, target_mode=target_mode))

    required_capabilities = sorted(
        {requirement for operation in operations for requirement in operation.get("requires", [])}
    )
    return {
        "schema": PLAN_SCHEMA,
        "target": target,
        "operationCount": len(operations),
        "operations": operations,
        "requiredCapabilities": required_capabilities,
        "verify": {
            "expectedCreatedItems": len(operations),
            "expectedCards": len(clean_cards),
            "expectedMindmapNodes": count_mindmap_nodes(mindmap) if isinstance(mindmap, dict) else 0,
            "requiresRollbackLedger": bool(operations),
        },
    }


def _card_type(card: dict[str, Any], title: str, body: str) -> str:
    explicit = _clean_text(card.get("cardType") or card.get("type") or card.get("kind"), 80).lower()
    if explicit:
        return explicit
    value = f"{title}\n{body}".lower()
    if re.search(r"公式|notation|equation|symbol|符号", value):
        return "formula"
    if re.search(r"实验|结果|ablation|evidence|证据|figure|table", value):
        return "evidence"
    if re.search(r"局限|限制|failure|limitation|边界", value):
        return "limitation"
    if re.search(r"问题|quiz|复习|检查", value):
        return "review"
    if re.search(r"方法|算法|pipeline|policy|model", value):
        return "method"
    return "concept"


def _card_source(card: dict[str, Any], body: str) -> dict[str, Any]:
    source = card.get("source") if isinstance(card.get("source"), dict) else {}
    ref: dict[str, Any] = {}
    page = card.get("page", source.get("page"))
    quote = card.get("quote", source.get("quote"))
    if page not in (None, ""):
        ref["page"] = page if isinstance(page, (int, float)) else _clean_text(page, 40)
    if quote:
        ref["quote"] = _clean_text(quote, 240)
    if not ref and re.search(r"\b(source|来源|quote|p\.|page|页码)\b|第\s*\d+\s*页", body, re.I):
        ref["inline"] = True
    return ref


def audit_card_quality(cards: list[Any] | None) -> dict[str, Any]:
    clean_cards = [item for item in (cards or []) if isinstance(item, dict)]
    type_counts: dict[str, int] = {}
    duplicate_titles: list[str] = []
    seen_titles: set[str] = set()
    long_cards: list[dict[str, Any]] = []
    missing_sources: list[dict[str, Any]] = []
    rewrite_suggestions: list[dict[str, Any]] = []

    for index, card in enumerate(clean_cards, start=1):
        title = _clean_text(card.get("title") or f"卡片 {index}", 160) or f"卡片 {index}"
        body = str(card.get("body") or card.get("comment") or "")
        card_type = _card_type(card, title, body)
        type_counts[card_type] = type_counts.get(card_type, 0) + 1

        title_key = _normalize_mindmap_key(title)
        if title_key and title_key in seen_titles:
            duplicate_titles.append(title)
            rewrite_suggestions.append(
                {
                    "cardIndex": index,
                    "issue": "deduplicate_title",
                    "title": title,
                    "suggestion": "合并同名卡片，或把标题改成更具体的知识点。",
                }
            )
        elif title_key:
            seen_titles.add(title_key)

        body_length = len(body)
        if body_length > CARD_BODY_TARGET_MAX:
            long_cards.append({"cardIndex": index, "title": title, "bodyLength": body_length})
            rewrite_suggestions.append(
                {
                    "cardIndex": index,
                    "issue": "split_long_card",
                    "title": title,
                    "bodyLength": body_length,
                    "suggestion": "拆成多张短卡，每张只保留一个概念、公式或证据点。",
                }
            )

        source_ref = _card_source(card, body)
        if not source_ref:
            missing_sources.append({"cardIndex": index, "title": title})
            rewrite_suggestions.append(
                {
                    "cardIndex": index,
                    "issue": "add_source",
                    "title": title,
                    "suggestion": "补充页码、quote 或来源节点，避免卡片脱离原文证据。",
                }
            )

    issue_count = len(long_cards) + len(missing_sources) + len(duplicate_titles)
    return {
        "schema": CARD_QUALITY_SCHEMA,
        "status": "pass" if issue_count == 0 else "warn",
        "cardCount": len(clean_cards),
        "typedCount": sum(type_counts.values()),
        "typeCounts": type_counts,
        "longCardCount": len(long_cards),
        "longCards": long_cards,
        "missingSourceCount": len(missing_sources),
        "missingSources": missing_sources,
        "duplicateTitleCount": len(duplicate_titles),
        "duplicateTitles": duplicate_titles,
        "targetBodyMax": CARD_BODY_TARGET_MAX,
        "rewriteSuggestions": rewrite_suggestions[:40],
    }


def build_operation_manifest(
    cards: list[Any] | None,
    mindmap: dict[str, Any] | None,
    write_target: dict[str, Any] | None,
) -> dict[str, Any]:
    plan = build_operation_plan(cards, mindmap, write_target)
    card_count = len([item for item in (cards or []) if isinstance(item, dict)])
    mindmap_count = count_mindmap_nodes(mindmap) if isinstance(mindmap, dict) else 0
    target = plan.get("target") if isinstance(plan.get("target"), dict) else {}
    return {
        "schema": MANIFEST_SCHEMA,
        "operationCount": card_count + mindmap_count,
        "createCards": card_count,
        "createMindmapNodes": mindmap_count,
        "targetMode": str(target.get("mode") or ""),
        "targetLabel": str(target.get("label") or ""),
        "operations": [
            {"op": "create_cards", "count": card_count}
            for card_count in [card_count]
            if card_count
        ]
        + [
            {
                "op": "create_mindmap_nodes",
                "count": mindmap_count,
                "targetMode": str(target.get("mode") or ""),
                "targetLabel": str(target.get("label") or ""),
            }
            for mindmap_count in [mindmap_count]
            if mindmap_count
        ],
        "operationPlan": plan,
        "cardQuality": audit_card_quality(cards),
        "dryRun": {
            "status": "not_checked",
            "message": "尚未执行写入前 dry-run。",
        },
    }


def _capability_state(native_caps: dict[str, Any], key: str) -> dict[str, Any]:
    matrix = native_caps.get("capabilityMatrix") if isinstance(native_caps.get("capabilityMatrix"), dict) else {}
    capability = matrix.get(key) if isinstance(matrix.get(key), dict) else {}
    return {
        "ready": bool(capability.get("ready")),
        "available": bool(capability.get("available")),
        "blockedReason": _clean_text(capability.get("blockedReason"), 120),
        "nextStep": _clean_text(capability.get("nextStep"), 240),
    }


def _operation_note_id(operation: dict[str, Any]) -> str:
    current_ref = operation.get("currentRef") if isinstance(operation.get("currentRef"), dict) else {}
    proposed_ref = operation.get("proposedRef") if isinstance(operation.get("proposedRef"), dict) else {}
    return _clean_text(
        current_ref.get("noteId")
        or current_ref.get("id")
        or proposed_ref.get("noteId")
        or proposed_ref.get("id"),
        160,
    )


def _operation_dry_run_item(
    operation: dict[str, Any],
    *,
    status: str,
    reason: str,
    next_step: str,
    via: str,
    capability_evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    current_ref = operation.get("currentRef") if isinstance(operation.get("currentRef"), dict) else {}
    proposed_ref = operation.get("proposedRef") if isinstance(operation.get("proposedRef"), dict) else {}
    requirements = operation.get("requires") if isinstance(operation.get("requires"), list) else []
    if status == "ready" and via == "url_api":
        verification_level = "url_api_ready"
    elif status == "ready":
        verification_level = "native_capability_ready"
    elif status == "unknown":
        verification_level = "native_capability_unknown"
    else:
        verification_level = "native_capability_missing"
    primary_requirement = ""
    for evidence in capability_evidence:
        if not bool(evidence.get("ready")):
            primary_requirement = str(evidence.get("requirement") or "")
            break
    if not primary_requirement and capability_evidence:
        primary_requirement = str(capability_evidence[0].get("requirement") or "")
    return {
        "opId": str(operation.get("opId") or ""),
        "op": str(operation.get("op") or ""),
        "mutation": str(operation.get("mutation") or ""),
        "kind": str(operation.get("kind") or ""),
        "title": _clean_text(operation.get("title"), 160),
        "status": status,
        "via": via,
        "reason": reason,
        "nextStep": next_step,
        "requirement": primary_requirement,
        "requiredCapabilities": [str(item) for item in requirements],
        "noteId": _operation_note_id(operation),
        "currentRef": current_ref,
        "proposedRef": proposed_ref,
        "targetParent": _clean_text(operation.get("targetParent") or operation.get("parentRef"), 200),
        "existingPath": str(operation.get("existingPath") or ""),
        "proposedPath": str(operation.get("proposedPath") or operation.get("path") or ""),
        "verificationLevel": verification_level,
        "capabilityEvidence": capability_evidence,
    }


def simulate_operation_manifest(
    manifest: dict[str, Any],
    settings: dict[str, Any] | None = None,
    native_caps: dict[str, Any] | None = None,
    mn_api: dict[str, Any] | None = None,
) -> dict[str, Any]:
    settings = settings if isinstance(settings, dict) else {}
    native_caps = native_caps if isinstance(native_caps, dict) else {}
    mn_api = mn_api if isinstance(mn_api, dict) else {}
    plan = manifest.get("operationPlan") if isinstance(manifest.get("operationPlan"), dict) else {}
    operations = plan.get("operations") if isinstance(plan.get("operations"), list) else []
    permission = str(settings.get("permission") or "notes")
    backend = str(settings.get("mnApiBackend") or mn_api.get("backend") or "auto")
    url_api_ready = bool(mn_api.get("urlApiConfigured") or mn_api.get("urlApiAvailable"))
    checks: list[dict[str, Any]] = []
    blocked: list[dict[str, str]] = []
    unknown: list[dict[str, str]] = []
    ready: list[dict[str, Any]] = []

    for operation in operations:
        if not isinstance(operation, dict):
            continue
        requirements = operation.get("requires") if isinstance(operation.get("requires"), list) else []
        if permission == "read_only" and str(operation.get("mutation") or "") in {"create", "update", "move", "delete"}:
            item = _operation_dry_run_item(
                operation,
                status="blocked",
                reason="read-only-permission",
                next_step="在设置页把权限从 read_only 改为 notes 或 full。",
                via="permission",
                capability_evidence=[],
            )
            checks.append(item)
            blocked.append(item)
            continue

        requirement_status = "ready"
        reason = ""
        next_step = ""
        via = "native"
        capability_evidence: list[dict[str, Any]] = []
        for requirement in requirements:
            requirement_key = str(requirement)
            capability = _capability_state(native_caps, requirement_key)
            capability_evidence.append(
                {
                    "requirement": requirement_key,
                    "ready": bool(capability["ready"]),
                    "available": bool(capability["available"]),
                    "blockedReason": capability["blockedReason"],
                    "nextStep": capability["nextStep"],
                }
            )
            if capability["ready"]:
                continue
            if backend in {"auto", "url_api"} and url_api_ready:
                via = "url_api"
                continue
            if backend == "url_api" and not url_api_ready:
                requirement_status = "blocked"
                reason = "url-api-secret-missing"
                next_step = "在设置页配置 URL API Secret，或切回自动/原生插件后端。"
                break
            if capability["available"]:
                requirement_status = "unknown"
                reason = capability["blockedReason"] or "native-capability-not-ready"
                next_step = capability["nextStep"] or "刷新 MN 能力后重试。"
                break
            requirement_status = "unknown" if backend == "auto" else "blocked"
            reason = capability["blockedReason"] or f"{requirement_key}-unverified"
            next_step = capability["nextStep"] or "打开当前文档并刷新 MN 能力；或配置 URL API Gateway。"
            break

        item = _operation_dry_run_item(
            operation,
            status=requirement_status,
            reason=reason,
            next_step=next_step,
            via=via,
            capability_evidence=capability_evidence,
        )
        checks.append(item)
        if requirement_status == "blocked":
            blocked.append(item)
        elif requirement_status == "unknown":
            unknown.append(item)
        else:
            ready.append(item)

    if blocked:
        status = "blocked"
        message = f"写入前 dry-run 阻断：{len(blocked)} 个操作不可执行。"
    elif unknown:
        status = "unknown"
        message = f"写入前 dry-run 未完全确认：{len(unknown)} 个操作需要刷新 MN 能力或配置 URL API。"
    else:
        status = "ready"
        message = f"写入前 dry-run 通过：{len(checks)} 个操作可执行。"
    return {
        "schema": "codex.mn.operationDryRun.v1",
        "status": status,
        "message": message,
        "operationCount": len(checks),
        "blockedCount": len(blocked),
        "unknownCount": len(unknown),
        "checks": checks,
        "perOperation": {
            "schema": PER_OPERATION_DRY_RUN_SCHEMA,
            "status": status,
            "operationCount": len(checks),
            "readyCount": len(ready),
            "blockedCount": len(blocked),
            "unknownCount": len(unknown),
            "items": checks,
        },
    }
