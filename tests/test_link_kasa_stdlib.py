"""Group 0 safe source linker tests; never invokes a compiler or installer."""
import importlib.util
from pathlib import Path

import pytest

ORIGINAL_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kasa_linker", ORIGINAL_ROOT / "scripts/link_kasa_stdlib.py")
linker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(linker)


@pytest.fixture
def setup(tmp_path, monkeypatch):
    source_root = tmp_path / "repo"
    for module, (relative, _) in linker.LIBRARIES.items():
        target = source_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ORIGINAL_ROOT / relative).read_bytes())
    app = tmp_path / "app.kasa"
    app.write_text("ka kasa_sum([1, 2, 3])\nka kasa_contains([1, 2], 2)\n", encoding="utf-8")
    monkeypatch.setattr(linker, "ROOT", source_root)
    monkeypatch.setattr(linker, "OUTPUT_ROOT", source_root / "build" / "stdlib-linked")
    return source_root, app


def test_two_pinned_libraries_link_to_new_source(setup):
    root, app = setup
    destination = root / "build/stdlib-linked/output.kasa"
    actual = linker.link(app, ["math", "collections"], destination)
    text = actual.read_text(encoding="utf-8")
    assert "dwumadie kasa_sum(values)" in text
    assert "dwumadie kasa_contains(values, needle)" in text
    assert "ka kasa_sum([1, 2, 3])" in text
    assert app.read_text(encoding="utf-8") == "ka kasa_sum([1, 2, 3])\nka kasa_contains([1, 2], 2)\n"


def test_existing_output_never_overwritten(setup):
    root, app = setup
    output = root / "build/stdlib-linked/existing.kasa"
    output.parent.mkdir(parents=True)
    output.write_text("IMPORTANT")
    with pytest.raises(linker.LinkError, match="already exists"):
        linker.link(app, ["math"], output)
    assert output.read_text() == "IMPORTANT"


@pytest.mark.parametrize("bad", ["../math", "math/../../evil", "C:\\temp", "", "Math", "missing", "collections.kasa"])
def test_module_allowlist_and_traversal_rejected(setup, bad):
    root, app = setup
    output = root / "build/stdlib-linked/no.kasa"
    with pytest.raises(linker.LinkError, match="unsafe"):
        linker.link(app, [bad], output)
    assert not output.exists()


def test_duplicate_module_rejected(setup):
    root, app = setup
    with pytest.raises(linker.LinkError, match="Duplicate"):
        linker.link(app, ["math", "math"], root / "build/stdlib-linked/no.kasa")


def test_changed_library_bytes_rejected(setup):
    root, app = setup
    (root / "stdlib/experimental/math.kasa").write_text("dwumadie kasa_abs(n)\n sanma 999\nawiei\n")
    output = root / "build/stdlib-linked/no.kasa"
    with pytest.raises(linker.LinkError, match="changed"):
        linker.link(app, ["math"], output)
    assert not output.exists()


def test_function_collision_rejected(setup):
    root, app = setup
    app.write_text("dwumadie kasa_sum(xs)\nsanma 5\nawiei\n")
    with pytest.raises(linker.LinkError, match="collides"):
        linker.link(app, ["math"], root / "build/stdlib-linked/no.kasa")


def test_refuses_output_outside_build(setup):
    _, app = setup
    with pytest.raises(linker.LinkError, match="Output must"):
        linker.link(app, ["math"], app.parent / "other.kasa")


def test_invalid_app_utf8_rejected(setup):
    root, app = setup
    app.write_bytes(b"\xff\xfe")
    with pytest.raises(linker.LinkError, match="UTF-8"):
        linker.link(app, ["math"], root / "build/stdlib-linked/no.kasa")


def test_source_too_large_rejected(setup):
    root, app = setup
    app.write_text("#" + "x" * 51000)
    with pytest.raises(linker.LinkError, match="50,000-byte"):
        linker.link(app, ["math"], root / "build/stdlib-linked/no.kasa")


def test_library_symlink_refused(setup):
    root, app = setup
    lib = root / "stdlib/experimental/math.kasa"
    copy = root / "stdlib/experimental/math-copy.kasa"
    copy.write_bytes(lib.read_bytes())
    lib.unlink()
    try:
        lib.symlink_to(copy)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink not allowed on this workstation")
    with pytest.raises(linker.LinkError, match="Library source"):
        linker.link(app, ["math"], root / "build/stdlib-linked/no.kasa")


def test_output_directory_symlink_refused(setup):
    root, app = setup
    other = root / "outside"
    other.mkdir()
    (root / "build").mkdir()
    try:
        (root / "build/stdlib-linked").symlink_to(other, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink not allowed on this workstation")
    with pytest.raises(linker.LinkError, match="Output directory"):
        linker.link(app, ["math"], root / "build/stdlib-linked/no.kasa")
    assert not list(other.iterdir())
