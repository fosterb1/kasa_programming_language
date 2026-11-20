"""End-to-end opt-in Kasa module source execution (NOT approved syntax)."""
import io
import sys
from pathlib import Path

import pytest

from kasa import parse
from kasa.core import KasaError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from run_kasa_modules_experimental import execute_module_source
finally:
    sys.path.remove(str(ROOT / "scripts"))


def test_real_kasa_source_uses_math_and_collections():
    stream = io.StringIO()
    runtime = execute_module_source(
        "@math:m\n@collections:c\n"
        "ka m.kasa_sum([10, 20, 30])\n"
        "ka c.kasa_contains([1, 2, 3], 2)\n",
        stdout=stream,
    )
    assert stream.getvalue() == "60\nnokware\n"
    assert runtime.globals.values == {}


def test_math_private_export_rejected_before_any_output():
    out = io.StringIO()
    with pytest.raises(KasaError, match="does not export"):
        execute_module_source('@math:m\nka "must not print"\nka m.private(1)', stdout=out)
    assert out.getvalue() == ""


@pytest.mark.parametrize("source, message", [
    ("@unknown:x\nka 1", "Unknown catalog module"),
    ("@math:m\n@collections:m\nka 1", "alias reused"),
    ("@math:m\n@math:z\nka 1", "more than once"),
    ("@math:ka\nka 1", "reserved"),
    ("@math:m\nka m.kasa_sum([1])\n@collections:c", "precede statements"),
    ("@math:m\nka c.kasa_sum([1])", "Unknown module alias"),
    ("@math:m\nka 1\nma m = 4", "Module alias cannot"),
])
def test_invalid_module_source_is_rejected(source, message):
    with pytest.raises(KasaError, match=message):
        execute_module_source(source, stdout=io.StringIO())


def test_normal_parser_refuses_experimental_declaration_and_dot():
    for source in ["@math:m\nka 1", "ka m.kasa_sum([1])"]:
        with pytest.raises(KasaError, match="SyntaxError"):
            parse(source)


def test_colon_or_dotted_text_inside_string_is_not_a_declaration():
    out = io.StringIO()
    execute_module_source('@math:m\nka "@collections:c"\nka "m.kasa_sum(1)"', stdout=out)
    assert out.getvalue() == "@collections:c\nm.kasa_sum(1)\n"


def test_step_quota_applies_to_module_function_calls():
    with pytest.raises(KasaError, match="Execution limit"):
        execute_module_source('@math:m\nmpɛn 100\nka m.kasa_sum([1, 2])\nawiei', max_steps=25)


def test_direct_script_launch_without_pytest_pythonpath():
    """The published command must work in a clean Python subprocess."""
    import os
    import subprocess

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "run_kasa_modules_experimental.py"),
        str(ROOT / "stdlib" / "demos" / "group0_source_import_experiment.kasa"),
    ]
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout == "60\nnokware\n"
    assert result.stderr == ""


def test_provisional_fa_imports_with_aliases():
    stream = io.StringIO()
    execute_module_source(
        "fa math: m\nfa collections: c\n"
        "ka m.kasa_sum([10, 20, 30])\n"
        "ka c.kasa_contains([1, 2, 3], 2)\n",
        stdout=stream,
    )
    assert stream.getvalue() == "60\nnokware\n"


def test_provisional_fa_import_without_alias():
    stream = io.StringIO()
    execute_module_source("fa math\nka math.kasa_sum([1, 2, 3])\n", stdout=stream)
    assert stream.getvalue() == "6\n"


def test_new_fa_syntax_is_still_rejected_by_stable_parser():
    with pytest.raises(KasaError):
        parse("fa math\nka math.kasa_sum([1])")


@pytest.mark.parametrize("source, message", [
    ("fa math: ka\nka 1", "reserved"),
    ("fa math: m\nfa collections: m\nka 1", "alias reused"),
    ("fa math: m\nka 1\nfa collections: c", "precede statements"),
])
def test_provisional_fa_invalid_cases(source, message):
    with pytest.raises(KasaError, match=message):
        execute_module_source(source)
