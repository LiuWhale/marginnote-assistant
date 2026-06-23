from __future__ import annotations

import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
COMPANION_PATH = ROOT / "companion.py"


def load_companion_module(root: Path) -> Any:
    old_root = os.environ.get("CODEX_MN_COMPANION_HOME")
    os.environ["CODEX_MN_COMPANION_HOME"] = str(root)
    try:
        spec = importlib.util.spec_from_file_location("codex_mn_companion", COMPANION_PATH)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        if old_root is None:
            os.environ.pop("CODEX_MN_COMPANION_HOME", None)
        else:
            os.environ["CODEX_MN_COMPANION_HOME"] = old_root


def flatten_tree(node: dict[str, Any]) -> list[dict[str, Any]]:
    out = [node]
    for child in node.get("children", []) or []:
        out.extend(flatten_tree(child))
    return out


class PayloadMetadataTests(unittest.TestCase):
    def test_generated_payload_helpers_assign_stable_unique_codex_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            companion = load_companion_module(Path(tmp))
            cards = companion.attach_card_ids(
                [{"title": "A", "body": "a"}, {"title": "B", "body": "b"}],
                "full-reading",
            )
            tree = companion.attach_tree_ids(
                {
                    "title": "Root",
                    "children": [
                        {"title": "One"},
                        {"title": "Two", "children": [{"title": "Two-A"}]},
                    ],
                },
                "full-reading",
            )

        nodes = flatten_tree(tree)

        self.assertEqual(len(cards), 2)
        self.assertEqual(len(nodes), 4)

        card_ids = [card.get("codexId") for card in cards]
        node_ids = [node.get("codexId") for node in nodes]
        all_ids = card_ids + node_ids

        self.assertTrue(all(isinstance(item, str) and item.startswith("full-reading:") for item in all_ids))
        self.assertEqual(len(all_ids), len(set(all_ids)))
        self.assertEqual(cards[0]["codexId"], "full-reading:card:01")
        self.assertEqual(tree["codexId"], "full-reading:mindmap:root")
        self.assertEqual(nodes[-1]["codexId"], "full-reading:mindmap:2.1")


if __name__ == "__main__":
    unittest.main()
