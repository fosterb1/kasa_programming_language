"""Opt-in G1 Python imports: source-level execution only, no native/JS parity."""
from __future__ import annotations

import io
import os
from pathlib import Path
import subprocess
import sys

import pytest

from kasa import parse
from kasa.core import KasaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from run_kasa_modules_experimental import execute_module_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def run(source: str, *, generation: str = "g1", steps: int = 100_000):
    output = io.StringIO()
    runtime = execute_module_source(source, stdout=output, generation=generation, max_steps=steps)
    return output.getvalue(), runtime


def test_g1_math_and_collections_namespace_output():
    output, runtime = run(
        "fa math firi stdlib: m\nfa collections firi stdlib: c\n"
        "ma scores = [40, 60, 80, 90]\n"
        "ka m.kasa_total(scores)\n"
        "ka m.kasa_average_or(scores, 0)\n"
        "ka m.kasa_count_above(scores, 60)\n"
        "ka c.kasa_count_distinct([1, 2, 1, 3])\n"
        "ka c.kasa_all_equal([8, 8])\n"
    )
    assert output == "270\n67.5\n2\n3\nnokware\n"
    assert "m" not in runtime.globals.values
    assert "c" not in runtime.globals.values
    assert "kasa_total" not in runtime.globals.values


def test_g1_default_alias_and_empty_fallback():
    output, _ = run("fa math firi stdlib\nka math.kasa_average_or([], -1)\n")
    assert output == "-1\n"


def test_g0_default_still_exposes_only_g0_exports():
    output, _ = run("fa math firi stdlib: m\nka m.kasa_sum([2, 3])\n", generation="g0")
    assert output == "5\n"
    with pytest.raises(KasaError, match="does not export"):
        run("fa math firi stdlib: m\nka m.kasa_total([2, 3])\n", generation="g0")
    with pytest.raises(KasaError, match="does not export"):
        run("fa math firi stdlib: m\nka m.kasa_sum([2, 3])\n", generation="g1")


@pytest.mark.parametrize(("source", "message"), [
    ("fa missing firi stdlib: x\nka 1\n", "Unknown catalog module"),
    ("fa math firi stdlib: x\nfa math firi stdlib: y\nka 1\n", "more than once"),
    ("fa math firi stdlib: x\nfa collections firi stdlib: x\nka 1\n", "alias reused"),
    ("fa math firi external: m\nka 1\n", "Only the pinned stdlib"),
    ("fa math firi stdlib: m\nka m.hidden([1])\n", "does not export"),
    ("fa math firi stdlib: m\nma m = 3\n", "Module alias cannot"),
    ("fa math firi stdlib: m\nka 1\nfa collections firi stdlib: c\n", "precede statements"),
])
def test_invalid_g1_source_rejected_before_output(source, message):
    output = io.StringIO()
    with pytest.raises(KasaError, match=message):
        execute_module_source(source, stdout=output, generation="g1")
    assert output.getvalue() == ""


def test_g1_execution_budget_applies():
    with pytest.raises(KasaError, match="Execution limit"):
        run(
            "fa math firi stdlib: m\nmpɛn 100\nka m.kasa_total([1, 2])\nawiei\n",
            steps=25,
        )


def test_default_parser_remains_unchanged():
    with pytest.raises(KasaError):
        parse("fa math firi stdlib: m\nka m.kasa_total([1])\n")


def test_cli_g1_requires_explicit_flag(tmp_path):
    app = tmp_path / "school.kasa"
    app.write_text("fa math firi stdlib: m\nka m.kasa_total([10, 20])\n", encoding="utf-8")
    argv = [sys.executable, str(ROOT / "scripts/run_kasa_modules_experimental.py"), str(app)]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    default = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert default.returncode != 0 and "does not export" in default.stderr
    selected = subprocess.run(argv + ["--generation", "g1"], cwd=ROOT, env=env, capture_output=True, text=True, timeout=20)
    assert selected.returncode == 0, selected.stderr
    assert selected.stdout == "30\n"


def test_invalid_generation_rejected():
    with pytest.raises(ValueError, match="generations"):
        run("fa math\nka 1", generation="g2")
