from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from reachability.adapter_runtime import AdapterError, ROOT, verify_native_build, verify_source
from reachability.atomspace_adapter import AtomSpaceBatch
from reachability.pln_adapter import FORMULA_PREFIX, PeTTaFormulaRuntime, TruthValue


class AdapterBoundaryTests(TestCase):
    def test_formula_revision_matches_lock(self):
        lock = json.loads((ROOT / "adapters.lock.json").read_text())
        self.assertEqual(FORMULA_PREFIX, "trueagi-pln/" + lock["sources"]["pln"]["commit"] + "/")

    def test_native_inputs_are_bounded_and_nonexecutable(self):
        batch = AtomSpaceBatch()
        atom = batch.node("text")
        key = batch.node("key", predicate=True)
        for value in ((float("nan"),), (float("inf"),), (True,), [1.0], ("x",)):
            with self.subTest(value=value), self.assertRaises(ValueError):
                batch.set_value(atom, key, value)
        with self.assertRaises(ValueError):
            batch.node("x" * 65537)
        with self.assertRaises(ValueError):
            batch.link((99,))
        with self.assertRaises(ValueError):
            batch.set_value(atom, atom, "value")

    def test_missing_native_build_fails_explicitly(self):
        with TemporaryDirectory() as directory, self.assertRaises(AdapterError):
            AtomSpaceBatch().run(Path(directory))

    def test_modified_native_binary_fails_receipt_validation(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "bin").mkdir()
            binary = root / "bin/atomspace_batch"
            binary.write_bytes(b"original")
            receipt = {"lock_sha256": sha256((ROOT / "adapters.lock.json").read_bytes()).hexdigest(),
                       "native_source_sha256": sha256((ROOT / "native/atomspace_batch.cc").read_bytes()).hexdigest(),
                       "files": {"bin/atomspace_batch": sha256(binary.read_bytes()).hexdigest()}}
            (root / "adapter-build.json").write_text(json.dumps(receipt))
            verify_native_build(root)
            binary.write_bytes(b"modified")
            with self.assertRaises(AdapterError):
                verify_native_build(root)

    def test_wrong_source_commit_is_rejected(self):
        with patch("reachability.adapter_runtime.checked_run", return_value="wrong\n"), self.assertRaises(AdapterError):
            verify_source("pln", ROOT / "artifacts")

    def test_runtime_version_drift_is_rejected(self):
        with patch("reachability.pln_adapter.verify_source", return_value=Path("unused")), \
                patch("reachability.pln_adapter.checked_run", return_value="SWI-Prolog version 9.0.0 for x86_64-linux\n"), \
                self.assertRaises(AdapterError):
            PeTTaFormulaRuntime().evaluate("Truth_Revision", (TruthValue(.5, .5), TruthValue(.5, .5)))

    def test_no_arbitrary_formula_entry_point(self):
        with self.assertRaises(ValueError):
            PeTTaFormulaRuntime().evaluate("(shell arbitrary)", ())
        class ExecutableArgument:
            def metta(self):
                raise AssertionError("unvalidated arguments must never render code")
        with self.assertRaises(ValueError):
            PeTTaFormulaRuntime().evaluate("Truth_Revision", (ExecutableArgument(), ExecutableArgument()))

    def test_forged_native_readback_is_rejected(self):
        batch = AtomSpaceBatch()
        batch.node("expected")
        pin = json.loads((ROOT / "adapters.lock.json").read_text())["sources"]["atomspace"]["commit"]
        wrong = f"reachability-atomspace-batch/v1 {pin}\nA 0 0 N 77726f6e67\nSIZE 1\n"
        with patch("reachability.atomspace_adapter.verify_native_build"), \
                patch("reachability.atomspace_adapter.checked_run", return_value=wrong), self.assertRaises(AdapterError):
            batch.run()
