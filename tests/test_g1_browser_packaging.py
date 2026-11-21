"""G1 opt-in browser ZIP packaging checks. No web or browser required."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
from zipfile import ZipFile

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playground"))
try:
    from build_site import build_bundle, packaged_g1_modules
finally:
    sys.path.remove(str(ROOT / "playground"))


def test_default_zip_excludes_g1(tmp_path):
    archive_path = build_bundle(tmp_path / "default.zip")
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert "kasa-pinned-modules.js" in names
        assert "kasa-g1-pinned-modules.js" not in names
        assert b"const KASA_HAS_G1_PINNED_MODULES = false;" in archive.read("worker.js")
        assert b"const KASA_PACKAGED_G1_MODULES = false;" in archive.read("sw.js")


def test_explicit_g1_zip_contains_pinned_sources_and_flags(tmp_path):
    archive_path = build_bundle(tmp_path / "g1.zip", include_g1=True)
    with ZipFile(archive_path) as archive:
        names = set(archive.namelist())
        assert "kasa-pinned-modules.js" in names
        assert "kasa-g1-pinned-modules.js" in names
        worker = archive.read("worker.js")
        sw = archive.read("sw.js")
        assert b"const KASA_HAS_G1_PINNED_MODULES = true;" in worker
        assert b"const KASA_HAS_PINNED_MODULES = true;" in worker
        assert b"const KASA_PACKAGED_G1_MODULES = true;" in sw
        asset = archive.read("kasa-g1-pinned-modules.js")
        assert b"self.KasaG1PinnedModules = Object.freeze(" in asset
        assert b"kasa_count_distinct" in asset
        assert b"kasa_average_or" in asset


def test_pin_check_rejects_changed_source(tmp_path):
    location = tmp_path / "repo"
    directory = location / "stdlib/g1"
    directory.mkdir(parents=True)
    for name in ("catalog.json", "math.kasa", "collections.kasa"):
        (directory / name).write_bytes((ROOT / "stdlib/g1" / name).read_bytes())
    with pytest.raises(Exception, match="(?i)hash mismatch"):
        (directory / "math.kasa").write_bytes(
            (directory / "math.kasa").read_bytes() + b"\n# changed\n"
        )
        packaged_g1_modules(location)


def test_source_identity_remains_pinned():
    catalog = json.loads((ROOT / "stdlib/g1/catalog.json").read_text(encoding="utf-8"))
    for module in catalog["modules"]:
        path = ROOT / module["source"]
        raw = path.read_bytes().replace(b"\r\n", b"\n")
        assert module["content_identity"] == "sha256:" + hashlib.sha256(raw).hexdigest()
