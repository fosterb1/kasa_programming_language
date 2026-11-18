"""Isolated tests for the parity report gate; no native toolchain is needed."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_parity_report.py"
spec = importlib.util.spec_from_file_location("audit_parity_report", SCRIPT)
audit_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit_module)


def report():
    return {
        "schema_version": 1, "profile": "parity", "dry_run": False,
        "wasm_requested": False,
        "source_revision": {"commit": "a" * 40, "working_tree_clean": True},
        "counts": {"passed": 8, "failed": 0, "not_run": 0},
        "checks": [{"name": name, "command": ["python", "-V"],
                    "status": "passed", "exit_code": 0} for name in audit_module.STAGES],
    }


class ParityReportAuditTests(unittest.TestCase):
    def test_complete_report_is_accepted(self):
        self.assertEqual(audit_module.audit(report()), [])

    def test_dry_run_is_rejected(self):
        data = report()
        data["dry_run"] = True
        self.assertTrue(audit_module.audit(data))

    def test_missing_stage_is_rejected(self):
        data = report()
        data["checks"].pop()
        self.assertTrue(audit_module.audit(data))

    def test_failed_stage_is_rejected(self):
        data = report()
        data["checks"][3]["exit_code"] = 1
        self.assertTrue(audit_module.audit(data))

    def test_dirty_or_missing_revision_is_rejected(self):
        data = report()
        data["source_revision"] = {"commit": None, "working_tree_clean": False}
        self.assertTrue(audit_module.audit(data))

    def test_dirty_diagnostic_override_does_not_waive_stages(self):
        data = report()
        data["source_revision"]["working_tree_clean"] = False
        self.assertEqual(audit_module.audit(data, require_clean=False), [])
        data["checks"][0]["status"] = "not_run"
        self.assertTrue(audit_module.audit(data, require_clean=False))

    def test_duplicate_stage_is_rejected(self):
        data = report()
        data["checks"][1]["name"] = data["checks"][0]["name"]
        self.assertTrue(audit_module.audit(data))

    def test_boolean_exit_code_is_rejected(self):
        data = report()
        data["checks"][0]["exit_code"] = False
        self.assertTrue(audit_module.audit(data))


if __name__ == "__main__":
    unittest.main()
