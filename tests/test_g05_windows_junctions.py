"""G0.5 real Windows junction detection without modifying repository directories.

Junction creation is attempted only in a pytest temporary directory. A lack
of Windows policy support is reported as a SKIP, never a security pass.
"""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from compile_g05_modules import _linked_directory, CompileError, compile_modules
finally:
    sys.path.remove(str(ROOT / "scripts"))


def test_real_windows_junction_is_detected(tmp_path):
    if os.name != "nt":
        pytest.skip("Real Windows junction test requires Windows")
    if not hasattr(Path, "is_junction"):
        pytest.skip("Python Path.is_junction unavailable; use Python 3.12+")
    target = tmp_path / "target"
    target.mkdir()
    junction = tmp_path / "junction"
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(junction), str(target)],
        capture_output=True, text=True, errors="replace", timeout=15,
        check=False,
    )
    if result.returncode != 0 or not junction.is_junction():
        pytest.skip("Windows junction creation unavailable: "
                    + (result.stderr.strip() or result.stdout.strip())[:300])
    try:
        assert junction.is_junction()
        assert _linked_directory(junction)
        assert not _linked_directory(target)
    finally:
        # rmdir on a junction removes the link, not its target. Do not call
        # shutil.rmtree on a junction path.
        if junction.is_junction():
            junction.rmdir()
    assert target.is_dir()


def test_rejects_junction_marker_before_reading_application(tmp_path, monkeypatch):
    """Prove the compiler's early linked-directory rejection branch.

    This complements, but does not replace, the real junction detection test.
    No repository build folder or source catalog is changed.
    """
    import compile_g05_modules as compiler

    source = tmp_path / "input.kasa"
    source.write_text("fa math firi stdlib: m\nka 1\n", encoding="utf-8")
    output = ROOT / "build" / "g05-compiled" / "junction-guard-only.kbc"
    if output.exists():
        pytest.skip("Dedicated output filename already exists; won't overwrite")

    original = compiler._linked_directory
    protected = ROOT / "build" / "g05-compiled"

    def simulate_linked_directory(path):
        if path == protected:
            return True
        return original(path)

    monkeypatch.setattr(compiler, "_linked_directory", simulate_linked_directory)
    with pytest.raises(CompileError, match="Linked output directory refused"):
        compile_modules(source, output)
    assert not output.exists()
