"""Release evidence parser and fail-closed status tests (no native build required)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from verify_g05_release import pytest_summary, GATES, TESTS
finally:
    sys.path.remove(str(ROOT / "scripts"))


def test_skips_are_not_counted_as_passes():
    result = pytest_summary(
        "================ short test summary info ================\n"
        "SKIPPED [1] tests/test_g05_compile_command.py: symlink privilege unavailable\n"
        "54 passed, 1 skipped in 1.4s\n"
    )
    assert result["passed"] == 54
    assert result["skipped"] == 1
    assert len(result["skip_details"]) == 1
    assert "symlink" in result["skip_details"][0]


def test_failures_and_zero_skips_are_distinct():
    result = pytest_summary("1 failed, 53 passed, 1 skipped in 1.36s")
    assert result["failed"] == 1
    assert result["passed"] == 53
    assert result["skipped"] == 1
    good = pytest_summary("55 passed in 1.36s")
    assert good["passed"] == 55
    assert good.get("skipped", 0) == 0
    assert good["skip_details"] == []


def test_release_gate_includes_required_safety_stages():
    names = [name for name, _, _ in GATES]
    assert names == ["native_full", "g05_pytest", "native_kbc_parity", "kbc_independence"]
    assert "tests/test_g05_build_reproducibility.py" in TESTS
    assert "tests/test_g05_native_mapped_runner.py" in TESTS
    assert "tests/test_g05_windows_junctions.py" in TESTS
    assert "tests/test_g05_negative_corpus.py" in TESTS
    assert "tests/test_g05_publication_race.py" in TESTS
    assert "tests/test_g05_strict_publication.py" in TESTS
    assert any("--profile" in args and "full" in args for _, args, _ in GATES)
    assert all(timeout > 0 for _, _, timeout in GATES)
