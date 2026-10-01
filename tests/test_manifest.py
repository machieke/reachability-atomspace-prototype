import ast
from hashlib import sha256
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ManifestTests(unittest.TestCase):
    def test_pinned_design_inputs_match(self):
        manifest = json.loads((ROOT / "implementation_manifest.json").read_text())
        for path, expected in manifest["design_inputs"].items():
            with self.subTest(path=path):
                self.assertEqual(sha256((ROOT / path).read_bytes()).hexdigest(), expected)

    def test_runtime_does_not_import_evaluator(self):
        # This is an import boundary check, not a process/filesystem sandbox.
        for path in (ROOT / "reachability").glob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                modules = ([node.module or ""] if isinstance(node, ast.ImportFrom)
                           else [alias.name for alias in node.names]
                           if isinstance(node, ast.Import) else [])
                self.assertTrue(all(not name.startswith(("tests", "reachability_validation_design"))
                                    for name in modules), path.name)
