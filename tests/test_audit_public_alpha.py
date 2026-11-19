"""No release on the basis of a local flag alone."""
import importlib.util
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "scripts/audit_public_alpha.py"
spec = importlib.util.spec_from_file_location("kasa_release_audit", SOURCE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

def test_public_alpha_fails_closed_even_with_local_documents(tmp_path):
    for name in tool.REQUIRED:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("draft")
    result = tool.gate(tmp_path)
    assert not result["ready"]
    assert sum(item["passed"] for item in result["checks"]) == len(tool.REQUIRED)
    assert all(not c["passed"] for c in result["checks"] if c["name"] in tool.EXTERNAL)

def test_missing_license_and_compatibility_policy_are_blockers(tmp_path):
    result = tool.gate(tmp_path)
    assert not result["ready"]
    assert any(c["name"] == "LICENSE" and not c["passed"] for c in result["checks"])
    assert any("COMPATIBILITY" in c["name"] and not c["passed"] for c in result["checks"])

def test_gate_never_claims_external_approval_from_local_evidence(tmp_path):
    (tmp_path / "build").mkdir()
    (tmp_path / "build/approved.json").write_text('{"all_passed":true}')
    assert not tool.gate(tmp_path)["ready"]
