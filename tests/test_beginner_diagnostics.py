"""The beginner-help display must never change program behavior or error codes."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from kasa.core import KasaError
from kasa.diagnostics import explain_error


def cli(tmp_path: Path, code: str, *options: str, mode: str = "run") -> subprocess.CompletedProcess[str]:
    path = tmp_path / "kasa-lesson.kasa"
    path.write_text(code, encoding="utf-8")
    return subprocess.run([sys.executable, "-m", "kasa", mode, str(path), *options],
                          capture_output=True, text=True, check=False)


def test_unknown_name_suggests_ma_and_shows_caret(tmp_path: Path) -> None:
    result = cli(tmp_path, 'ma ɛdin = "Ama"\nka unknown_name', "--explain")
    assert result.returncode == 1
    assert "NameError" in result.stderr
    assert "2 | ka unknown_name" in result.stderr
    assert "^" in result.stderr
    assert '"ma edin = "Ama"' not in result.stderr
    assert 'ma edin = "Ama"' in result.stderr


def test_default_errors_remain_unchanged(tmp_path: Path) -> None:
    raw = cli(tmp_path, "ka 1 / 0")
    guided = cli(tmp_path, "ka 1 / 0", "--explain")
    assert raw.returncode == guided.returncode == 1
    assert raw.stderr == guided.stderr.splitlines()[0] + "\n"
    assert "Help: " not in raw.stderr
    assert "A divisor cannot be zero" in guided.stderr


def test_missing_block_end_explained_in_check_mode(tmp_path: Path) -> None:
    result = cli(tmp_path, "sɛ nokware a\n ka 1", "--explain", mode="check")
    assert result.returncode == 1
    assert "SyntaxError" in result.stderr
    assert "awiei" in result.stderr


def test_success_output_identical_with_explanations(tmp_path: Path) -> None:
    expected = 'Maakye, Ghana!\n'
    basic = cli(tmp_path, 'ka "Maakye, Ghana!"')
    explained = cli(tmp_path, 'ka "Maakye, Ghana!"', "--explain")
    assert basic.returncode == explained.returncode == 0
    assert explained.stdout == basic.stdout == expected
    assert explained.stderr == basic.stderr == ""


@pytest.mark.parametrize("code,category,fragment", [
    ('ka [1][5]', "IndexError", "tentɛn"),
    ('ka 1 + "Ama"', "TypeError", "nɔma"),
    ('sɛ 2 a\n  ka 1\nawiei', "TypeError", "nokware"),
    ('ka "unfinished', "SyntaxError", "double quotes"),
])
def test_common_beginner_errors(tmp_path: Path, code: str, category: str, fragment: str) -> None:
    output = cli(tmp_path, code, "--explain")
    assert output.returncode == 1
    assert category in output.stderr and fragment in output.stderr


def test_source_is_limited_and_control_characters_are_escaped() -> None:
    from kasa.core import Token
    error = KasaError("NameError", "not defined", Token("NAME", "x", 1, 30), "x.kasa")
    output = explain_error(error, "ka " + "a" * 250 + "\x1b[31m", max_width=70)
    assert "\x1b" not in output
    assert "Help: " in output
    assert len(output.splitlines()[1]) < 100
