"""G0.2 catalog contract: all tests are read-only or operate in tmp_path."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("catalog_validator", ROOT / "scripts/validate_kasa_catalog.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture
def environment(tmp_path):
    base = tmp_path / "repo"
    path = base / "stdlib/catalog.json"
    path.parent.mkdir(parents=True)
    raw = (ROOT / "stdlib/catalog.json").read_bytes()
    path.write_bytes(raw)
    for relative in validator.ALLOWED.values():
        source = base / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes((ROOT / relative).read_bytes())
    return base, path


def _change(environment, action):
    root, path = environment
    data = json.loads(path.read_text(encoding="utf-8"))
    action(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    return root, path


def test_actual_catalog_is_valid():
    modules = validator.load_catalog()
    assert {entry["id"] for entry in modules} == {"math", "collections"}


def test_copied_catalog_is_valid(environment):
    base, path = environment
    modules = validator.load_catalog(path, base)
    assert len(modules) == 2


def test_order_is_deterministic_and_dependencies_first(environment):
    base, path = _change(environment, lambda c: c["modules"][1]["dependencies"].append("math"))
    assert [m["id"] for m in validator.load_catalog(path, base)] == ["math", "collections"]


@pytest.mark.parametrize("field,value,message", [
    ("id", "../evil", "unsafe module ID"),
    ("source", "../evil.kasa", "trusted allowlist"),
    ("exports", ["unknown"], "undeclared"),
    ("exports", ["kasa_abs", "kasa_abs"], "duplicate"),
    ("exports", [], "at least one"),
    ("dependencies", ["unknown"], "Missing dependency"),
    ("content_identity", "sha256:0", "SHA-256"),
])
def test_bad_module_metadata_rejected(environment, field, value, message):
    base, path = _change(environment, lambda c: c["modules"][0].__setitem__(field, value))
    with pytest.raises(validator.CatalogError, match=message):
        validator.load_catalog(path, base)


def test_duplicate_module_rejected(environment):
    base, path = _change(environment, lambda c: c["modules"][1].__setitem__("id", "math"))
    with pytest.raises(validator.CatalogError, match="Duplicate module ID"):
        validator.load_catalog(path, base)


def test_cycle_rejected(environment):
    def change(c):
        c["modules"][0]["dependencies"] = ["collections"]
        c["modules"][1]["dependencies"] = ["math"]
    base, path = _change(environment, change)
    with pytest.raises(validator.CatalogError, match="Dependency cycle"):
        validator.load_catalog(path, base)


def test_source_tampering_rejected(environment):
    base, path = environment
    source = base / validator.ALLOWED["math"]
    source.write_bytes(source.read_bytes() + b"\n# changed\n")
    with pytest.raises(validator.CatalogError, match="hash mismatch"):
        validator.load_catalog(path, base)


def test_windows_crlf_normalized(environment):
    base, path = environment
    source = base / validator.ALLOWED["math"]
    canonical = source.read_bytes().replace(b"\r\n", b"\n")
    source.write_bytes(canonical.replace(b"\n", b"\r\n"))
    assert len(validator.load_catalog(path, base)) == 2


def test_malformed_line_endings_rejected(environment):
    base, path = environment
    source = base / validator.ALLOWED["math"]
    canonical = source.read_bytes().replace(b"\r\n", b"\n")
    source.write_bytes(canonical.replace(b"\n", b"\r\r\n"))
    with pytest.raises(validator.CatalogError, match="line ending"):
        validator.load_catalog(path, base)


def test_unexpected_top_level_statement_rejected(environment):
    base, path = environment
    source = base / validator.ALLOWED["math"]
    source.write_bytes(source.read_bytes() + b"\nka 1\n")
    data = json.loads(path.read_text(encoding="utf-8"))
    canonical = source.read_bytes().replace(b"\r\n", b"\n")
    import hashlib
    data["modules"][0]["content_identity"] = "sha256:" + hashlib.sha256(canonical).hexdigest()
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(validator.CatalogError, match="top-level functions"):
        validator.load_catalog(path, base)


def test_duplicate_json_keys_rejected(environment):
    base, path = environment
    path.write_text('{"schema_version":1,"schema_version":1,"modules":[]}', encoding="utf-8")
    with pytest.raises(validator.CatalogError, match="Duplicate JSON key"):
        validator.load_catalog(path, base)


def test_wrong_schema_rejected(environment):
    base, path = _change(environment, lambda c: c.__setitem__("schema_version", 2))
    with pytest.raises(validator.CatalogError, match="schema"):
        validator.load_catalog(path, base)


def test_module_symlink_rejected(environment):
    base, path = environment
    source = base / validator.ALLOWED["math"]
    real = source.parent / "math-copy.kasa"
    real.write_bytes(source.read_bytes())
    source.unlink()
    try:
        source.symlink_to(real)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not allowed on this system")
    with pytest.raises(validator.CatalogError, match="linked"):
        validator.load_catalog(path, base)


def test_no_such_catalog_rejected(environment):
    base, _ = environment
    with pytest.raises(validator.CatalogError, match="regular file"):
        validator.load_catalog(base / "missing.json", base)
