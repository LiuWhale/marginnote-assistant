import unittest

import operation_runtime


class OperationRuntimeTests(unittest.TestCase):
    def test_builds_structured_plan_while_preserving_legacy_manifest_counts(self) -> None:
        manifest = operation_runtime.build_operation_manifest(
            cards=[{"title": "Card A", "body": "Body A"}],
            mindmap={"title": "Root", "children": [{"title": "Child", "children": []}]},
            write_target={"mode": "document_root", "label": "Paper · Codex 脑图"},
        )

        self.assertEqual(manifest["schema"], "codex.mn.operationManifest.v1")
        self.assertEqual(manifest["operationCount"], 3)
        self.assertEqual(manifest["createCards"], 1)
        self.assertEqual(manifest["createMindmapNodes"], 2)
        plan = manifest["operationPlan"]
        self.assertEqual(plan["schema"], "codex.mn.operationPlan.v1")
        self.assertEqual(plan["target"]["mode"], "document_root")
        self.assertEqual([item["op"] for item in plan["operations"]], [
            "create_note",
            "create_mindmap_node",
            "create_mindmap_node",
        ])
        self.assertIn("nativeCards", plan["requiredCapabilities"])
        self.assertIn("nativeMindmap", plan["requiredCapabilities"])

    def test_operation_manifest_audits_card_factory_quality(self) -> None:
        manifest = operation_runtime.build_operation_manifest(
            cards=[
                {
                    "title": "Safety concept",
                    "body": "概念说明。" * 260,
                    "type": "concept",
                },
                {
                    "title": "Safety concept",
                    "body": "短证据卡。\nSource: p.4 attention mask",
                    "cardType": "evidence",
                    "source": {"page": 4, "quote": "attention mask"},
                },
                {
                    "title": "Formula note",
                    "body": "公式卡没有来源。",
                    "cardType": "formula",
                },
            ],
            mindmap=None,
            write_target={"mode": "document_root", "label": "Doc Root"},
        )

        quality = manifest["cardQuality"]
        self.assertEqual(quality["schema"], "codex.mn.cardQuality.v1")
        self.assertEqual(quality["cardCount"], 3)
        self.assertEqual(quality["typedCount"], 3)
        self.assertEqual(quality["typeCounts"]["concept"], 1)
        self.assertEqual(quality["typeCounts"]["evidence"], 1)
        self.assertEqual(quality["typeCounts"]["formula"], 1)
        self.assertEqual(quality["longCardCount"], 1)
        self.assertEqual(quality["missingSourceCount"], 2)
        self.assertEqual(quality["duplicateTitleCount"], 1)
        self.assertEqual(quality["status"], "warn")
        self.assertTrue(any(item["issue"] == "split_long_card" for item in quality["rewriteSuggestions"]))

    def test_dry_run_blocks_read_only_writes(self) -> None:
        manifest = operation_runtime.build_operation_manifest(
            cards=[{"title": "Card A", "body": "Body A"}],
            mindmap=None,
            write_target={},
        )

        dry_run = operation_runtime.simulate_operation_manifest(
            manifest,
            settings={"permission": "read_only", "mnApiBackend": "auto"},
            native_caps={"capabilityMatrix": {"nativeCards": {"ready": True, "available": True}}},
            mn_api={"urlApiConfigured": True},
        )

        self.assertEqual(dry_run["status"], "blocked")
        self.assertEqual(dry_run["blockedCount"], 1)
        self.assertEqual(dry_run["checks"][0]["reason"], "read-only-permission")

    def test_dry_run_can_use_url_api_fallback_when_native_capability_is_unknown(self) -> None:
        manifest = operation_runtime.build_operation_manifest(
            cards=[{"title": "Card A", "body": "Body A"}],
            mindmap=None,
            write_target={},
        )

        dry_run = operation_runtime.simulate_operation_manifest(
            manifest,
            settings={"permission": "notes", "mnApiBackend": "url_api"},
            native_caps={"capabilityMatrix": {}},
            mn_api={"urlApiConfigured": True, "urlApiAvailable": True},
        )

        self.assertEqual(dry_run["status"], "ready")
        self.assertEqual(dry_run["checks"][0]["via"], "url_api")

    def test_mindmap_diff_classifies_create_update_merge_and_duplicates(self) -> None:
        current = {
            "title": "Paper",
            "body": "root",
            "children": [
                {"title": "Problem", "body": "old problem", "children": []},
                {"title": "Method", "body": "old method", "children": []},
            ],
        }
        proposed = {
            "title": "Paper",
            "body": "root",
            "children": [
                {"title": "Problem", "body": "old problem", "children": []},
                {"title": "Method", "body": "new method details", "children": []},
                {
                    "title": "Experiments",
                    "body": "experiment overview",
                    "children": [{"title": "Ablation", "body": "ablation detail", "children": []}],
                },
                {"title": "Method", "body": "duplicate method", "children": []},
            ],
        }

        diff = operation_runtime.build_mindmap_diff(
            proposed,
            current,
            target={"mode": "document_root", "label": "Paper · Codex 脑图"},
        )

        self.assertEqual(diff["schema"], "codex.mn.mindmapDiff.v1")
        self.assertEqual(diff["status"], "ready")
        self.assertEqual(diff["summary"]["proposedCount"], 6)
        self.assertEqual(diff["summary"]["createCount"], 2)
        self.assertEqual(diff["summary"]["updateCount"], 1)
        self.assertEqual(diff["summary"]["mergeCount"], 3)
        self.assertEqual(diff["summary"]["duplicateCount"], 1)
        self.assertEqual(diff["hierarchy"]["maxDepth"], 2)
        self.assertEqual(diff["hierarchy"]["levelCounts"]["1"], 4)
        operations_by_title = {(item["title"], item["op"]) for item in diff["operations"]}
        self.assertIn(("Experiments", "create"), operations_by_title)
        self.assertIn(("Ablation", "create"), operations_by_title)
        self.assertIn(("Method", "update"), operations_by_title)
        self.assertTrue(any(item["reason"] == "duplicate-proposed-title" for item in diff["operations"]))
        self.assertTrue(all("rollback" in item for item in diff["operations"]))

    def test_prunes_mindmap_by_diff_paths_without_mutating_original(self) -> None:
        mindmap = {
            "title": "Root",
            "children": [
                {"title": "Keep A", "children": []},
                {"title": "Drop B", "children": [{"title": "Drop B child", "children": []}]},
                {
                    "title": "Keep C",
                    "children": [
                        {"title": "Drop C child", "children": []},
                        {"title": "Keep C child", "children": []},
                    ],
                },
            ],
        }

        pruned = operation_runtime.prune_mindmap_by_paths(mindmap, ["0.2", "0.3.1"])

        self.assertEqual(operation_runtime.count_mindmap_nodes(pruned), 4)
        self.assertEqual([child["title"] for child in pruned["children"]], ["Keep A", "Keep C"])
        self.assertEqual([child["title"] for child in pruned["children"][1]["children"]], ["Keep C child"])
        self.assertEqual([child["title"] for child in mindmap["children"]], ["Keep A", "Drop B", "Keep C"])

    def test_edits_mindmap_by_diff_paths_without_mutating_original(self) -> None:
        mindmap = {
            "title": "Root",
            "children": [
                {"title": "Keep A", "body": "A body", "children": []},
                {"title": "Old B", "body": "B body", "children": []},
                {"title": "Keep C", "children": [{"title": "Old child", "children": []}]},
            ],
        }

        edited = operation_runtime.edit_mindmap_nodes_by_paths(
            mindmap,
            [
                {"proposedPath": "0.2", "title": "Edited B", "body": "Edited B body"},
                {"path": "0.3.1", "body": "Edited child body"},
                {"proposedPath": "bad.path", "title": "Ignored"},
            ],
        )

        self.assertEqual(edited["children"][1]["title"], "Edited B")
        self.assertEqual(edited["children"][1]["body"], "Edited B body")
        self.assertEqual(edited["children"][2]["children"][0]["title"], "Old child")
        self.assertEqual(edited["children"][2]["children"][0]["body"], "Edited child body")
        self.assertEqual(mindmap["children"][1]["title"], "Old B")
        self.assertNotIn("body", mindmap["children"][2]["children"][0])

    def test_mindmap_diff_operations_preserve_object_references(self) -> None:
        diff = operation_runtime.build_mindmap_diff(
            proposed_mindmap={
                "title": "Paper",
                "children": [
                    {
                        "title": "Method",
                        "body": "new method",
                        "codexId": "draft-method",
                        "source": {"page": 3, "quote": "method quote"},
                        "children": [],
                    }
                ],
            },
            current_mindmap={
                "title": "Paper",
                "noteId": "mn-root",
                "children": [
                    {"title": "Method", "body": "old method", "noteId": "mn-method", "children": []}
                ],
            },
            target={"mode": "document_root", "label": "Paper · Codex 脑图"},
        )

        method_op = next(item for item in diff["operations"] if item["title"] == "Method")
        self.assertEqual(method_op["op"], "update")
        self.assertEqual(method_op["currentRef"]["noteId"], "mn-method")
        self.assertEqual(method_op["proposedRef"]["codexId"], "draft-method")
        self.assertEqual(method_op["source"]["page"], 3)
        self.assertEqual(method_op["source"]["quote"], "method quote")

    def test_builds_local_mindmap_diff_operation_plan(self) -> None:
        diff = {
            "schema": "codex.mn.mindmapDiff.v1",
            "operations": [
                {
                    "op": "create",
                    "title": "New Node",
                    "proposedPath": "0.1",
                    "targetParent": "root",
                    "proposedRef": {"codexId": "new-node"},
                    "source": {"page": 1},
                },
                {
                    "op": "update",
                    "title": "Old Node",
                    "proposedPath": "0.2",
                    "existingPath": "0.4",
                    "currentRef": {"noteId": "mn-old"},
                    "proposedRef": {"codexId": "old-node-new"},
                },
                {
                    "op": "merge",
                    "title": "Duplicate Node",
                    "proposedPath": "0.3",
                    "existingPath": "0.5",
                    "currentRef": {"noteId": "mn-dup"},
                    "duplicateOf": "0.1",
                },
                {
                    "op": "move",
                    "title": "Moved Node",
                    "proposedPath": "0.4",
                    "existingPath": "0.6",
                    "currentRef": {"noteId": "mn-move"},
                    "targetParent": "0.1",
                },
            ],
        }

        plan = operation_runtime.build_mindmap_diff_operation_plan(diff, excluded_paths=["0.3"])

        self.assertEqual(plan["schema"], "codex.mn.mindmapDiffOperationPlan.v1")
        self.assertEqual(plan["operationCount"], 3)
        self.assertEqual(plan["skippedCount"], 1)
        self.assertEqual(
            [item["op"] for item in plan["operations"]],
            ["create_mindmap_node", "update_mindmap_node", "move_mindmap_node"],
        )
        self.assertTrue(all(item["selected"] is True for item in plan["operations"]))
        self.assertTrue(all(item["selectionState"] == "included" for item in plan["operations"]))
        self.assertEqual(plan["skipped"][0]["selected"], False)
        self.assertEqual(plan["skipped"][0]["selectionState"], "excluded_by_user")
        self.assertEqual(plan["skipped"][0]["diffOp"], "merge")
        self.assertEqual(plan["skipped"][0]["op"], "merge_mindmap_node")
        self.assertEqual(plan["operations"][1]["currentRef"]["noteId"], "mn-old")
        self.assertEqual(plan["operations"][2]["requires"], ["nativeMindmapMove"])
        self.assertIn("nativeMindmapUpdate", plan["requiredCapabilities"])

    def test_mindmap_diff_operation_plan_exposes_current_apply_boundary(self) -> None:
        diff = {
            "schema": "codex.mn.mindmapDiff.v1",
            "operations": [
                {"op": "create", "title": "New Node", "proposedPath": "0.1"},
                {
                    "op": "update",
                    "title": "Existing Node",
                    "proposedPath": "0.2",
                    "existingPath": "0.5",
                    "currentRef": {"noteId": "mn-existing"},
                },
            ],
        }

        plan = operation_runtime.build_mindmap_diff_operation_plan(diff)

        self.assertEqual(plan["applyBoundary"]["localApplyStatus"], "preview_only")
        self.assertEqual(plan["applyBoundary"]["currentApplyPath"], "draft_tree_write")
        self.assertEqual(plan["applyBoundary"]["plannedLocalMutations"], ["create", "update"])
        self.assertEqual(plan["applyBoundary"]["directlyExecutableMutations"], ["create"])
        self.assertEqual(plan["applyBoundary"]["blockedLocalMutations"], ["update"])

    def test_create_only_mindmap_diff_operation_plan_is_locally_applyable(self) -> None:
        diff = {
            "schema": "codex.mn.mindmapDiff.v1",
            "operations": [
                {"op": "create", "title": "Root", "proposedPath": "0"},
                {"op": "create", "title": "Child", "proposedPath": "0.1"},
            ],
        }

        plan = operation_runtime.build_mindmap_diff_operation_plan(diff)

        self.assertEqual(plan["applyBoundary"]["localApplyStatus"], "ready")
        self.assertEqual(plan["applyBoundary"]["currentApplyPath"], "local_operation_queue")
        self.assertEqual(plan["applyBoundary"]["acceptButtonBehavior"], "queues_local_create_operations")
        self.assertEqual(plan["applyBoundary"]["blockedLocalMutations"], [])

    def test_mindmap_diff_marks_current_only_nodes_as_delete_suggestions(self) -> None:
        proposed = {
            "title": "Paper",
            "children": [{"title": "Kept", "body": "new", "children": []}],
        }
        current = {
            "title": "Paper",
            "children": [
                {"title": "Kept", "body": "old", "noteId": "N-kept", "children": []},
                {"title": "Obsolete", "body": "remove me", "noteId": "N-old", "children": []},
            ],
        }

        diff = operation_runtime.build_mindmap_diff(proposed, current)
        delete_ops = [item for item in diff["operations"] if item["op"] == "delete_suggest"]
        plan = operation_runtime.build_mindmap_diff_operation_plan(diff)
        plan_delete_ops = [item for item in plan["operations"] if item["mutation"] == "delete_suggest"]

        self.assertEqual(diff["summary"]["deleteSuggestCount"], 1)
        self.assertEqual(delete_ops[0]["title"], "Obsolete")
        self.assertEqual(delete_ops[0]["currentRef"]["noteId"], "N-old")
        self.assertEqual(delete_ops[0]["reason"], "missing-in-proposed-tree")
        self.assertEqual(plan_delete_ops[0]["op"], "suggest_delete_mindmap_node")
        self.assertEqual(plan_delete_ops[0]["confirmationRequired"], True)
        self.assertEqual(plan_delete_ops[0]["confirmationType"], "delete_existing_mindmap_node")
        self.assertEqual(plan["applyBoundary"]["deleteSuggestCount"], 1)
        self.assertIn("delete_suggest", plan["applyBoundary"]["confirmationRequiredMutations"])


if __name__ == "__main__":
    unittest.main()
