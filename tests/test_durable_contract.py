"""Run the same admission contract through the durable adapter and cold recovery."""
from pathlib import Path
from tempfile import TemporaryDirectory

from reachability.model import Rule
from reachability.service import AdmissionService
from tests import test_admission as contract
from tests.support import Driver


class DurableAdmissionContractTests(contract.AdmissionTests):
    def setUp(self):
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "contract.db"
        self.service = AdmissionService((Rule("join", "1", (contract.A, contract.B), contract.C),
                                         Rule("next", "1", (contract.A,), contract.B),
                                         Rule("back", "1", (contract.B,), contract.A)),
                                        database=self.path)
        self.addCleanup(self.service.close)
        self.driver = Driver(self.service)
        self.driver.context()

    def tearDown(self):
        expected = {name: self.service.snapshot(name) for name in self.service._contexts}
        self.service.close()
        with AdmissionService(database=self.path) as recovered:
            self.assertEqual({name: recovered.snapshot(name) for name in expected}, expected)
