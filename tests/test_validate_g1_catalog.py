"""G1.2.1 separate pinned manifest hardening tests; all fixtures are local."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("g1_validator", ROOT / "scripts/validate_g1_catalog.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


@pytest.fixture
def environment(tmp_path):
    root = tmp_path / "repo"
    manifest = root / "stdlib/g1/catalog.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes((ROOT / "stdlib/g1/catalog.json").read_bytes())
    for relative in validator.ALLOWED.values():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())
    return root, manifest


def rewrite(environment, change):
    root, manifest = environment
    data = json.loads(manifest.read_text(encoding="utf-8"))
    change(data)
    manifest.write_text(json.dumps(data), encoding="utf-8")
    return root, manifest


def test_actual_catalog_has_nine_exports():
    modules = validator.validate()
    assert [m["id"] for m in modules] == ["collections", "math"]
    assert sum(len(m["exports"]) for m in modules) == 9


def test_copied_repository_is_valid(environment):
    root, manifest = environment
    assert len(validator.validate(manifest, root)) == 2


def test_g0_catalog_is_unchanged():
    g0 = json.loads((ROOT / "stdlib/catalog.json").read_text(encoding="utf-8"))
    assert {m["source"] for m in g0["modules"]} == {
        "stdlib/experimental/math.kasa", "stdlib/experimental/collections.kasa"
    }


@pytest.mark.parametrize(("field", "value", "error"), [
    ("id", "../math", "identifier"),
    ("source", "../unexpected.kasa", "allowlist"),
    ("exports", ["kasa_total"], "reviewed G1 contract"),
    ("exports", ["kasa_total", "kasa_total"], "reviewed G1 contract"),
    ("dependencies", ["collections"], "does not permit"),
    ("content_identity", "sha256:broken", "SHA-256"),
])
def test_reject_bad_module_fields(environment, field, value, error):
    root, manifest = rewrite(environment, lambda x: x["modules"][0].__setitem__(field, value))
    with pytest.raises(validator.G1CatalogError, match=error):
        validator.validate(manifest, root)


def test_duplicate_module_rejected(environment):
    root, manifest = rewrite(
        environment, lambda data: data["modules"][1].__setitem__("id", "math")
    )
    with pytest.raises(validator.G1CatalogError, match="Duplicate module"):
        validator.validate(manifest, root)


def test_wrong_schema_rejected(environment):
    root, manifest = rewrite(environment, lambda x: x.__setitem__("schema_version", 2))
    with pytest.raises(validator.G1CatalogError, match="schema version"):
        validator.validate(manifest, root)


def test_duplicate_json_keys_rejected(environment):
    root, manifest = environment
    manifest.write_text(
        '{"schema_version":1,"schema_version":1,"modules":[]}', encoding="utf-8"
    )
    with pytest.raises(validator.G1CatalogError, match="Duplicate JSON key"):
        validator.validate(manifest, root)


def test_changed_g1_source_is_rejected(environment):
    root, manifest = environment
    source = root / "stdlib/g1/math.kasa"
    source.write_bytes(source.read_bytes() + b"\n# tampered\n")
    with pytest.raises(validator.G1CatalogError, match="hash mismatch"):
        validator.validate(manifest, root)


def test_crlf_checkout_is_supported(environment):
    root, manifest = environment
    source = root / "stdlib/g1/math.kasa"
    data = source.read_bytes().replace(b"\r\n", b"\n")
    source.write_bytes(data.replace(b"\n", b"\r\n"))
    assert len(validator.validate(manifest, root)) == 2


def test_lone_carriage_return_is_rejected(environment):
    root, manifest = environment
    source = root / "stdlib/g1/math.kasa"
    source.write_bytes(source.read_bytes() + b"\r")
    with pytest.raises(validator.G1CatalogError, match="line endings"):
        validator.validate(manifest, root)


def test_top_level_side_effect_rejected_even_if_rehashed(environment):
    root, manifest = environment
    source = root / "stdlib/g1/math.kasa"
    source.write_bytes(source.read_bytes() + b"\nka 12\n")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["modules"][0]["content_identity"] = (
        "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    )
    manifest.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(validator.G1CatalogError, match="top-level functions"):
        validator.validate(manifest, root)


def test_missing_file_rejected(environment):
    root, manifest = environment
    (root / "stdlib/g1/math.kasa").unlink()
    with pytest.raises(validator.G1CatalogError, match="missing or linked"):
        validator.validate(manifest, root)


def test_source_symlink_rejected(environment):
    root, manifest = environment
    source = root / "stdlib/g1/math.kasa"
    copy = source.parent / "copy.kasa"
    copy.write_bytes(source.read_bytes())
    source.unlink()
    try:
        source.symlink_to(copy)
    except (OSError, NotImplementedError):
        pytest.skip("This filesystem does not permit symlinks")
    with pytest.raises(validator.G1CatalogError, match="missing or linked"):
        validator.validate(manifest, root)


def test_catalog_outside_root_rejected(environment):
    root, _ = environment
    with pytest.raises(validator.G1CatalogError, match="under root"):
        validator.validate(ROOT / "stdlib/g1/catalog.json", root)
