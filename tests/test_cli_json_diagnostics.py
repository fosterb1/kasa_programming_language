"""Opt-in CLI JSON diagnostics for editor integrations."""
from __future__ import annotations

import json

import pytest

from kasa.cli import main


def test_syntax_error_json_stderr(tmp_path, capsys):
    source = tmp_path / "akwabaa.kasa"
    source.write_text("ka @\n", encoding="utf-8")
    assert main(["check", str(source), "--diagnostics-json"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    parsed = json.loads(captured.err)
    assert parsed["schema_version"] == 1
    assert parsed["category"] == "SyntaxError"
    assert parsed["file"] == str(source)
    assert (parsed["line"], parsed["column"]) == (1, 4)
    assert parsed["message"]


def test_runtime_error_json_stderr(tmp_path, capsys):
    source = tmp_path / "runtime.kasa"
    source.write_text("ka 1 / 0\n", encoding="utf-8")
    assert main(["run", str(source), "--diagnostics-json"]) == 1
    parsed = json.loads(capsys.readouterr().err)
    assert parsed["category"] == "ZeroDivisionError"
    assert parsed["line"] == 1


def test_file_error_json(tmp_path, capsys):
    path = tmp_path / "missing.kasa"
    assert main(["check", str(path), "--diagnostics-json"]) == 2
    parsed = json.loads(capsys.readouterr().err)
    assert parsed["category"] == "FileError"
    assert parsed["line"] is None and parsed["column"] is None


def test_success_is_quiet_and_normal_cli_stays_text(tmp_path, capsys):
    source = tmp_path / "ok.kasa"
    source.write_text('ka "Maakye!"\n', encoding="utf-8")
    assert main(["check", str(source), "--diagnostics-json"]) == 0
    assert capsys.readouterr().err == ""
    source.write_text("ka @\n", encoding="utf-8")
    assert main(["check", str(source)]) == 1
    assert "SyntaxError" in capsys.readouterr().err


def test_explain_and_json_are_exclusive(tmp_path):
    with pytest.raises(SystemExit) as error:
        main(["check", str(tmp_path / "x.kasa"), "--explain", "--diagnostics-json"])
    assert error.value.code == 2
