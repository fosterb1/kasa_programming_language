"""G0.5 namespace isolation stress cases using synthetic pinned test catalogs.

Tests cannot alter the real standard library: each case constructs its own
temporary catalog and source identity, then temporarily extends the allowlist.
No test package or Kasa bytecode is installed or produced.
"""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from link_kasa_modules_hygienic import link_source, HygienicLinkError
    from validate_kasa_catalog import ALLOWED
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa import Interpreter, parse


def run_plain(source: str) -> str:
    out = io.StringIO()
    Interpreter(stdout=out).run(parse(source))
    return out.getvalue()


@pytest.fixture
def isolated_catalog(tmp_path, monkeypatch):
    """Two modules intentionally share both an exported and a private name."""
    modules = {
        "alpha": (
            "dwumadie helper(x)\n"
            "    sanma x + 1\n"
            "awiei\n"
            "dwumadie shared(x)\n"
            "    sanma helper(x) + 10\n"
            "awiei\n"
        ),
        "beta": (
            "dwumadie helper(x)\n"
            "    sanma x * 2\n"
            "awiei\n"
            "dwumadie shared(x)\n"
            "    sanma helper(x) + 100\n"
            "awiei\n"
        ),
    }
    catalog = []
    for module, source in modules.items():
        relative = f"stdlib/experimental/{module}.kasa"
        file = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(source.encode("utf-8"))
        monkeypatch.setitem(ALLOWED, module, relative)
        catalog.append({
            "id": module,
            "source": relative,
            "exports": ["shared"],
            "dependencies": [],
            "content_identity": "sha256:" + hashlib.sha256(source.encode("utf-8")).hexdigest(),
        })
    manifest = tmp_path / "stdlib" / "catalog.json"
    manifest.write_text(json.dumps({"schema_version": 1, "modules": catalog}), encoding="utf-8")
    return tmp_path


def test_colliding_exports_and_private_helpers_are_distinct(isolated_catalog):
    source = (
        "fa alpha firi stdlib: a\n"
        "fa beta firi stdlib: b\n"
        "dwumadie helper(x)\n"
        "    sanma 999\n"
        "awiei\n"
        "dwumadie shared(x)\n"
        "    sanma 888\n"
        "awiei\n"
        "ka a.shared(3)\n"
        "ka b.shared(3)\n"
        "ka helper(3)\n"
        "ka shared(3)\n"
    )
    linked = link_source(source, root=isolated_catalog)
    assert run_plain(linked) == "14\n106\n999\n888\n"
    for internal in (
        "__kasa_g05_alpha_helper",
        "__kasa_g05_beta_helper",
        "__kasa_g05_alpha_shared",
        "__kasa_g05_beta_shared",
    ):
        assert ("dwumadie " + internal + "(") in linked
    assert "dwumadie helper(" in linked
    assert "dwumadie shared(" in linked


def test_private_helper_cannot_be_imported_even_when_it_exists(isolated_catalog):
    source = "fa alpha firi stdlib: a\nka a.helper(3)\n"
    with pytest.raises(Exception, match="does not export"):
        link_source(source, root=isolated_catalog)


def test_nested_calls_keep_private_bindings_and_namespace(isolated_catalog):
    source = (
        "fa alpha firi stdlib: left\n"
        "fa beta firi stdlib: right\n"
        "ka left.shared(right.shared(2))\n"
    )
    assert run_plain(link_source(source, root=isolated_catalog)) == "115\n"


def test_string_contents_are_never_treated_as_private_member_access(isolated_catalog):
    source = (
        "fa alpha firi stdlib: a\n"
        'ka "a.helper(10) is not a call"\n'
        "ka a.shared(2)\n"
    )
    assert run_plain(link_source(source, root=isolated_catalog)) == (
        "a.helper(10) is not a call\n13\n"
    )
