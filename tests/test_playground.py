"""Smoke and resource-limit tests for the browser-facing Kasa adapter."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playground"))
from runner import execute_kasa  # noqa: E402


@pytest.mark.parametrize(("source", "expected"), [
    ('ka "Maakye, Ghana!"', 'Maakye, Ghana!\n'),
    ('ma edin="Kofi"\nka "Maakye, " + edin', 'Maakye, Kofi\n'),
    ('sɛ nokware a\nka "yes"\nanyɛ_saa_a\nka "no"\nawiei', 'yes\n'),
    ('mpɛn 3\nka "Hi"\nawiei', 'Hi\nHi\nHi\n'),
    ('dwumadie fa_bi(a,b)\nsanma a+b\nawiei\nka fa_bi(4,6)', '10\n'),
    ('ma xs=[1,2,3]\nka xs[1]', '2\n'),
])
def test_program_execution(source, expected):
    result = execute_kasa(source)
    assert result["ok"] is True
    assert result["output"] == expected
    assert not result["error"]


def test_syntax_check_does_not_execute():
    result = execute_kasa('ka 1 / 0', mode="check")
    assert result["ok"] is True
    assert result["output"] == ""
    assert result["steps"] == 0


def test_input_stream():
    assert execute_kasa('ka bisa()', 'Akosua\n')["output"] == 'Akosua\n'


def test_kasa_errors_have_source_locations():
    result = execute_kasa('ka 1 / 0')
    assert result["ok"] is False
    assert 'playground.kasa:' in result["error"]
    assert 'ZeroDivisionError' in result["error"]


def test_reject_non_kasa_syntax():
    result = execute_kasa('import os\nos.system("echo bad")')
    assert result["ok"] is False
    assert "SyntaxError" in result["error"]


def test_resource_limits():
    assert "Source exceeds" in execute_kasa("#" * 50_001)["error"]
    assert "Input exceeds" in execute_kasa("ka 1", "x" * 50_001)["error"]
    assert "Execution limit" in execute_kasa("bere_a nokware\nawiei")["error"]


def test_output_limit_preserves_partial_output():
    result = execute_kasa('mpɛn 20000\n ka "abcdefghijklmnop"\nawiei')
    assert result["ok"] is False
    assert "Output exceeded" in result["error"]
    assert 0 < len(result["output"]) <= 64_000


def test_isolation_between_runs():
    assert execute_kasa('ma secret="hello"')["ok"]
    failed = execute_kasa('ka secret')
    assert failed["ok"] is False
    assert "Unknown name" in failed["error"]


def test_results_json_serializable():
    import json
    assert json.loads(json.dumps(execute_kasa('ka "ɛ"')))["output"] == "ɛ\n"


def test_packaged_web_bundle(tmp_path):
    from zipfile import ZipFile
    from build_site import FILES, build_bundle

    archive_path = build_bundle(tmp_path / "kasa_web.zip")
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == set(FILES.values())
        assert b'<!doctype html>' in archive.read("index.html")
        assert b'function executeKasa' in archive.read("kasa-runtime.js")
        assert b'kasa-runtime.js' in archive.read("worker.js")
        assert b'pyodide' not in archive.read("worker.js").lower()
