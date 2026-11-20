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
    from build_site import FILES, WASM_FILES, MODULE_DESTINATION, ROOT as SITE_ROOT, build_bundle

    archive_path = build_bundle(tmp_path / "kasa_web.zip")
    with ZipFile(archive_path) as archive:
        expected = set(FILES.values())
        if all((SITE_ROOT / name).is_file() for name in WASM_FILES):
            expected.update(WASM_FILES.values())
        assert set(archive.namelist()) == expected | {MODULE_DESTINATION}
        assert b"self.KasaPinnedModules" in archive.read(MODULE_DESTINATION)
        assert b"const KASA_HAS_PINNED_MODULES = true;" in archive.read("worker.js")
        assert b"const KASA_PACKAGED_MODULES = true;" in archive.read("sw.js")
        assert b"generated at build time. */\nself.KasaPinnedModules" in archive.read(MODULE_DESTINATION)
        assert b'<!doctype html>' in archive.read("index.html")
        assert b'function executeKasa' in archive.read("kasa-runtime.js")
        assert b'kasa-runtime.js' in archive.read("worker.js")
        assert b'pyodide' not in archive.read("worker.js").lower()


def test_wasm_bundle_requires_complete_pair(tmp_path, monkeypatch):
    import build_site
    from zipfile import ZipFile
    from shutil import copyfile

    local = tmp_path / "repo"
    for source in [*build_site.FILES, "stdlib/catalog.json", "stdlib/experimental/math.kasa", "stdlib/experimental/collections.kasa"]:
        (local / source).parent.mkdir(parents=True, exist_ok=True)
        copyfile(build_site.ROOT / source, local / source)
    monkeypatch.setattr(build_site, "ROOT", local)
    output = tmp_path / "site.zip"
    with pytest.raises(RuntimeError, match="WebAssembly not built"):
        build_site.build_bundle(output, require_wasm=True)

    native_js = local / "playground/native/kasa-native.js"
    native_wasm = local / "playground/native/kasa-native.wasm"
    native_js.parent.mkdir(parents=True, exist_ok=True)
    native_js.write_text("var createKasaModule = () => {};", encoding="utf-8")
    with pytest.raises(RuntimeError, match="Incomplete native build"):
        build_site.build_bundle(output)

    native_wasm.write_bytes(b"not WebAssembly")
    with pytest.raises(RuntimeError, match="WASM asset is invalid"):
        build_site.build_bundle(output)

    # Test the packager's file inclusion logic with a valid WASM header;
    # this is NOT a real Emscripten runtime or an end-to-end WASM test.
    native_wasm.write_bytes(b"\x00asm\x01\x00\x00\x00")
    build_site.build_bundle(output, require_wasm=True)
    with ZipFile(output) as bundle:
        assert set(bundle.namelist()) == set(build_site.FILES.values()) | set(build_site.WASM_FILES.values()) | {build_site.MODULE_DESTINATION}
        assert b"const KASA_HAS_WASM = true;" in bundle.read("worker.js")
        assert bundle.read("native/kasa-native.wasm").startswith(b"\x00asm")
    assert b"const KASA_HAS_WASM = false;" in (local / "playground/worker.js").read_bytes()


def test_packaging_rejects_tampered_stdlib_source(tmp_path, monkeypatch):
    from shutil import copyfile
    from build_site import FILES, ROOT as SITE_ROOT, build_bundle
    import build_site

    local = tmp_path / "repo"
    for source in [*FILES, "stdlib/catalog.json", "stdlib/experimental/math.kasa", "stdlib/experimental/collections.kasa"]:
        (local / source).parent.mkdir(parents=True, exist_ok=True)
        copyfile(SITE_ROOT / source, local / source)
    (local / "stdlib/experimental/math.kasa").write_text(
        "# altered\n", encoding="utf-8"
    )
    monkeypatch.setattr(build_site, "ROOT", local)
    with pytest.raises(RuntimeError, match="source hash mismatch"):
        build_bundle(tmp_path / "invalid.zip")
