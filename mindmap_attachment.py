from __future__ import annotations

import copy
import re
import unicodedata
from typing import Any


ROUTING_SCHEMA = "codex.mn.replyMindmapAttachment.v1"
DEFAULT_CONFIDENCE_THRESHOLD = 0.34
SELECTED_COMPATIBILITY_THRESHOLD = 0.20
_GENERIC_TERMS = {
    "codex",
    "mindmap",
    "map",
    "answer",
    "reply",
    "topic",
    "node",
    "paper",
    "回答",
    "脑图",
    "节点",
    "主题",
    "内容",
    "说明",
    "文档",
    "论文",
}


def _normalized_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).casefold()
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"[`*_#>\[\](){}|/\\:：,，.。;；!?！？\-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _title_key(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def _terms(value: Any) -> set[str]:
    text = _normalized_text(value)
    terms = {
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if len(token) >= 2 and token not in _GENERIC_TERMS
    }
    for sequence in re.findall(r"[\u3400-\u9fff]+", text):
        if sequence not in _GENERIC_TERMS and len(sequence) >= 2:
            terms.add(sequence)
        for width in (2, 3):
            for index in range(max(0, len(sequence) - width + 1)):
                token = sequence[index : index + width]
                if token not in _GENERIC_TERMS:
                    terms.add(token)
    return terms


def _semantic_signals(value: Any) -> set[str]:
    text = _normalized_text(value)
    signals = {
        token
        for token in re.findall(r"[a-z0-9]+", text)
        if len(token) >= 2 and token not in _GENERIC_TERMS
    }
    for sequence in re.findall(r"[\u3400-\u9fff]+", text):
        if len(sequence) >= 2 and sequence not in _GENERIC_TERMS:
            signals.add(sequence)
    return signals


def _semantic_overlap_count(query_signals: set[str], candidate_signals: set[str]) -> int:
    matched_queries: set[str] = set()
    for query in query_signals:
        for candidate in candidate_signals:
            if candidate == query:
                matched_queries.add(query)
                break
            candidate_is_cjk = bool(re.fullmatch(r"[\u3400-\u9fff]+", candidate))
            query_is_cjk = bool(re.fullmatch(r"[\u3400-\u9fff]+", query))
            if candidate_is_cjk and query_is_cjk and (candidate in query or query in candidate):
                matched_queries.add(query)
                break
    return len(matched_queries)


def _tree_text(node: Any) -> str:
    parts: list[str] = []

    def walk(item: Any) -> None:
        if not isinstance(item, dict):
            return
        parts.append(str(item.get("title") or ""))
        parts.append(str(item.get("body") or ""))
        children = item.get("children") if isinstance(item.get("children"), list) else []
        for child in children:
            walk(child)

    walk(node)
    return "\n".join(parts)


def flatten_current_nodes(tree: dict[str, Any]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []

    def walk(node: Any, depth: int, path: str, inherited_document_id: str) -> None:
        if not isinstance(node, dict):
            return
        note_id = str(node.get("noteId") or node.get("id") or "").strip()
        title = str(node.get("title") or node.get("name") or "").strip()
        document_id = str(node.get("documentId") or inherited_document_id or "").strip()
        if note_id and note_id != "notebook-root":
            nodes.append(
                {
                    "noteId": note_id,
                    "title": title,
                    "body": str(node.get("body") or ""),
                    "documentId": document_id,
                    "depth": depth,
                    "path": path,
                }
            )
        children = node.get("children") if isinstance(node.get("children"), list) else []
        for index, child in enumerate(children, start=1):
            walk(child, depth + 1, f"{path}.{index}" if path else str(index), document_id)

    walk(tree, 0, "1", str(tree.get("documentId") or ""))
    return nodes


def _coverage(query_terms: set[str], candidate_terms: set[str]) -> float:
    if not query_terms or not candidate_terms:
        return 0.0
    overlap = query_terms & candidate_terms
    if not overlap:
        return 0.0
    return len(overlap) / max(1, min(len(query_terms), len(candidate_terms)))


def _candidate_score(
    query_terms: set[str],
    query_signals: set[str],
    candidate: dict[str, Any],
) -> float:
    title_terms = _terms(candidate.get("title"))
    body_terms = _terms(candidate.get("body"))
    candidate_signals = _semantic_signals(
        f"{candidate.get('title') or ''}\n{candidate.get('body') or ''}"
    )
    if _semantic_overlap_count(query_signals, candidate_signals) < 3:
        return 0.0
    title_score = _coverage(query_terms, title_terms)
    body_score = _coverage(query_terms, body_terms)
    depth = max(0, int(candidate.get("depth") or 0))
    specificity = min(depth, 4) * 0.015 if title_score or body_score else 0.0
    corroboration = 0.08 if title_score and body_score else 0.0
    return min(1.0, title_score * 0.72 + body_score * 0.72 + specificity + corroboration)


def rank_candidates(
    candidates: list[dict[str, Any]],
    query_terms: set[str],
    query_signals: set[str],
    selected_note_id: str,
) -> list[dict[str, Any]]:
    selected_note_id = str(selected_note_id or "").strip()
    ranked: list[dict[str, Any]] = []
    for candidate in candidates:
        base_score = _candidate_score(query_terms, query_signals, candidate)
        selected_compatible = (
            candidate.get("noteId") == selected_note_id
            and base_score >= SELECTED_COMPATIBILITY_THRESHOLD
        )
        score = min(1.0, base_score + (0.16 if selected_compatible else 0.0))
        ranked.append(
            {
                **candidate,
                "baseScore": round(base_score, 4),
                "score": round(score, 4),
                "selectedCompatible": selected_compatible,
            }
        )
    ranked.sort(
        key=lambda item: (
            bool(item.get("selectedCompatible")),
            float(item.get("score") or 0.0),
            int(item.get("depth") or 0),
            str(item.get("title") or ""),
        ),
        reverse=True,
    )
    return ranked


def _prune_duplicate_children(
    children: list[Any],
    existing_keys: set[str],
    proposed_keys: set[str],
    duplicates: list[dict[str, str]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for child in children:
        if not isinstance(child, dict):
            continue
        cloned = {key: copy.deepcopy(value) for key, value in child.items() if key != "children"}
        title = str(cloned.get("title") or "").strip()
        key = _title_key(title)
        nested = child.get("children") if isinstance(child.get("children"), list) else []
        pruned_nested = _prune_duplicate_children(nested, existing_keys, proposed_keys, duplicates)
        reason = ""
        if key and key in existing_keys:
            reason = "existing-title"
        elif key and key in proposed_keys:
            reason = "repeated-proposed-title"
        if reason:
            duplicates.append({"title": title, "reason": reason})
            output.extend(pruned_nested)
            continue
        if key:
            proposed_keys.add(key)
        cloned["children"] = pruned_nested
        output.append(cloned)
    return output


def prune_duplicate_proposed_nodes(
    proposed_tree: dict[str, Any],
    current_nodes: list[dict[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    tree = copy.deepcopy(proposed_tree) if isinstance(proposed_tree, dict) else {}
    existing_keys = {
        key
        for key in (_title_key(item.get("title")) for item in current_nodes)
        if key
    }
    duplicates: list[dict[str, str]] = []
    children = tree.get("children") if isinstance(tree.get("children"), list) else []
    tree["children"] = _prune_duplicate_children(children, existing_keys, set(), duplicates)
    return tree, duplicates


def _verified_parent_target(candidate: dict[str, Any], reason: str) -> dict[str, Any]:
    title = str(candidate.get("title") or "").strip()
    confidence = float(candidate.get("score") or 0.0)
    return {
        "mode": "verified_parent_node",
        "operation": "append_reply_subtree",
        "label": f"自动接入：{title}" if title else "自动接入已有脑图节点",
        "parentNoteId": str(candidate.get("noteId") or ""),
        "parentNoteTitle": title,
        "parentEvidenceBody": str(candidate.get("body") or ""),
        "parentDocumentId": str(candidate.get("documentId") or ""),
        "confidence": round(confidence, 4),
        "reason": reason,
    }


def plan_reply_attachment(
    proposed_tree: dict[str, Any],
    current_tree: dict[str, Any],
    selected_note_id: str,
    document_root_target: dict[str, Any],
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    expected_document_id: str = "",
) -> dict[str, Any]:
    candidates = flatten_current_nodes(current_tree)
    expected_document_id = str(expected_document_id or "").strip()
    if expected_document_id:
        candidates = [
            candidate
            for candidate in candidates
            if str(candidate.get("documentId") or "") == expected_document_id
        ]
    query_text = _tree_text(proposed_tree)
    query_terms = _terms(query_text)
    query_signals = _semantic_signals(query_text)
    ranked = rank_candidates(candidates, query_terms, query_signals, selected_note_id)
    selected = next(
        (item for item in ranked if item.get("selectedCompatible")),
        None,
    )
    best = selected or (ranked[0] if ranked else None)
    fallback = not best or float(best.get("score") or 0.0) < confidence_threshold
    if fallback:
        shallowest_depth = min((int(item.get("depth") or 0) for item in candidates), default=-1)
        document_roots = [
            item for item in candidates if int(item.get("depth") or 0) == shallowest_depth
        ]
        if expected_document_id and len(document_roots) == 1:
            reason = "unique-current-document-root"
            write_target = _verified_parent_target(
                {**document_roots[0], "score": 1.0},
                reason,
            )
            fallback = False
        else:
            write_target = copy.deepcopy(document_root_target)
            write_target["confidence"] = round(float(best.get("score") or 0.0) if best else 0.0, 4)
            write_target["reason"] = "low-confidence-document-root-fallback"
            reason = "low-confidence-document-root-fallback"
    else:
        reason = "compatible-selected-node" if best.get("selectedCompatible") else "best-semantic-match"
        write_target = _verified_parent_target(best, reason)

    pruned_tree, duplicates = prune_duplicate_proposed_nodes(proposed_tree, candidates)
    confidence = float(write_target.get("confidence") or 0.0)
    return {
        "schema": ROUTING_SCHEMA,
        "tree": pruned_tree,
        "writeTarget": write_target,
        "duplicateCount": len(duplicates),
        "duplicates": duplicates,
        "routing": {
            "schema": ROUTING_SCHEMA,
            "reason": reason,
            "fallback": fallback,
            "confidence": round(confidence, 4),
            "parentNoteId": str(write_target.get("parentNoteId") or ""),
            "parentNoteTitle": str(write_target.get("parentNoteTitle") or write_target.get("rootTitle") or ""),
            "candidateCount": len(ranked),
            "topCandidates": [
                {
                    "noteId": str(item.get("noteId") or ""),
                    "title": str(item.get("title") or ""),
                    "score": float(item.get("score") or 0.0),
                    "selectedCompatible": bool(item.get("selectedCompatible")),
                }
                for item in ranked[:5]
            ],
        },
    }


def tree_fingerprint(tree: dict[str, Any]) -> str:
    segments: list[str] = []

    def walk(node: Any) -> None:
        if not isinstance(node, dict):
            return
        children = node.get("children") if isinstance(node.get("children"), list) else []
        segments.extend(
            [
                str(node.get("noteId") or node.get("id") or ""),
                str(node.get("title") or node.get("name") or ""),
                str(node.get("body") or ""),
                str(node.get("documentId") or ""),
                str(len(children)),
            ]
        )
        for child in children:
            walk(child)

    walk(tree)
    canonical = "\x1f".join(segments)
    value = 0x811C9DC5
    encoded = canonical.encode("utf-16-le", errors="surrogatepass")
    for index in range(0, len(encoded), 2):
        code_unit = encoded[index] | (encoded[index + 1] << 8)
        value ^= code_unit
        value = (value * 0x01000193) & 0xFFFFFFFF
    return f"fnv1a32:{value:08x}"


def build_create_only_diff(
    proposed_tree: dict[str, Any],
    write_target: dict[str, Any],
) -> dict[str, Any]:
    operations: list[dict[str, Any]] = []
    diff_operations: list[dict[str, Any]] = []
    target_parent_ref = {
        "noteId": str(write_target.get("parentNoteId") or ""),
        "title": str(write_target.get("parentNoteTitle") or write_target.get("rootTitle") or ""),
        "codexId": str(write_target.get("codexId") or ""),
    }

    def walk(children: list[Any], parent_path: str) -> None:
        for index, child in enumerate(children, start=1):
            if not isinstance(child, dict):
                continue
            path = f"{parent_path}.{index}" if parent_path else str(index)
            title = str(child.get("title") or "Codex 节点").strip() or "Codex 节点"
            body = str(child.get("body") or "").strip()
            parent_ref = target_parent_ref if not parent_path else {"proposedPath": parent_path}
            diff_operations.append(
                {
                    "op": "create",
                    "title": title,
                    "shortBody": body[:220],
                    "proposedPath": path,
                    "existingPath": "",
                    "duplicateOf": "",
                    "targetParent": str(write_target.get("label") or ""),
                    "targetParentRef": parent_ref,
                    "currentRef": {},
                    "proposedRef": {
                        "codexId": str(child.get("codexId") or ""),
                        "proposedPath": path,
                    },
                    "confidence": float(write_target.get("confidence") or 1.0),
                    "reason": "reply-derived-create-only",
                    "rollback": {
                        "type": "delete_created_note",
                        "requiresTransactionLedger": True,
                    },
                }
            )
            operations.append(
                {
                    "opId": f"reply-mindmap:{len(operations) + 1}",
                    "op": "create_mindmap_node",
                    "diffOp": "create",
                    "mutation": "create",
                    "kind": "mindmap",
                    "title": title,
                    "bodyPreview": body[:220],
                    "proposedPath": path,
                    "existingPath": "",
                    "targetParent": str(write_target.get("label") or ""),
                    "targetParentRef": parent_ref,
                    "currentRef": {},
                    "proposedRef": {
                        "codexId": str(child.get("codexId") or ""),
                        "proposedPath": path,
                    },
                    "source": {},
                    "requires": ["nativeMindmap"],
                    "rollback": {
                        "type": "delete_created_note",
                        "requiresTransactionLedger": True,
                    },
                    "selected": True,
                    "selectionState": "included",
                    "confirmationRequired": False,
                    "confirmationType": "",
                }
            )
            nested = child.get("children") if isinstance(child.get("children"), list) else []
            walk(nested, path)

    children = proposed_tree.get("children") if isinstance(proposed_tree.get("children"), list) else []
    walk(children, "")
    diff = {
        "schema": "codex.mn.mindmapDiff.v1",
        "status": "ready" if operations else "empty",
        "mode": "reply-derived-create-only",
        "target": copy.deepcopy(write_target),
        "summary": {
            "proposedCount": len(operations),
            "currentCount": 0,
            "createCount": len(operations),
            "updateCount": 0,
            "mergeCount": 0,
            "moveCount": 0,
            "deleteSuggestCount": 0,
            "duplicateCount": 0,
        },
        "operations": diff_operations,
        "duplicates": [],
    }
    plan = {
        "schema": "codex.mn.mindmapDiffOperationPlan.v1",
        "status": "ready" if operations else "empty",
        "mode": "reply-derived-create-only",
        "operationCount": len(operations),
        "operations": operations,
        "skipped": [],
        "requiredCapabilities": ["nativeMindmap"] if operations else [],
        "plannedMutations": ["create"] if operations else [],
        "applyBoundary": {
            "localApplyStatus": "ready" if operations else "empty",
            "currentApplyPath": "draft_tree_write",
            "createOnly": True,
        },
    }
    return {"mindmapDiff": diff, "mindmapDiffOperationPlan": plan}
