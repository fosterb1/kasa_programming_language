"""G0.3 module alias preflight regression checks (no execution or writes)."""
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    spec = importlib.util.spec_from_file_location(
        "plan_kasa_modules", ROOT / "scripts/plan_kasa_modules.py"
    )
    planner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planner)
    from validate_kasa_catalog import load_catalog
finally:
    sys.path.remove(str(ROOT / "scripts"))


def catalog():
    return load_catalog()


def test_two_modules_keep_separate_export_names():
    p = planner.plan_bindings(["math:m", "collections:c"], catalog())
    assert p["mode"] == "preflight_only"
    assert p["load_order"] == ["collections", "math"]
    assert p["capabilities_granted"] == []
    assert [b["alias"] for b in p["bindings"]] == ["c", "m"]
    assert "kasa_sum" in p["bindings"][1]["exports"]


def test_transitive_dependency_is_ordered_before_caller():
    modules = [dict(m) for m in catalog()]
    for m in modules:
        if m["id"] == "collections":
            m["dependencies"] = ["math"]
    # preflight consumes dependency-first catalog returned by the validator.
    modules.sort(key=lambda m: (m["id"] != "math", m["id"]))
    p = planner.plan_bindings(["collections:c"], modules)
    assert p["load_order"] == ["math", "collections"]
    assert [b["module"] for b in p["bindings"]] == ["collections"]


@pytest.mark.parametrize("specs, message", [
    ([], "at least one"),
    (["math"], "module:alias"),
    (["math:m:extra"], "module:alias"),
    (["unknown:x"], "Unknown catalog module"),
    (["math:ka"], "reserved"),
    (["math:1invalid"], "Invalid"),
    (["math:m", "math:n"], "more than once"),
    (["math:x", "collections:x"], "alias reused"),
])
def test_invalid_bindings_rejected(specs, message):
    with pytest.raises(planner.NamespacePlanError, match=message):
        planner.plan_bindings(specs, catalog())


def test_missing_dependency_rejected():
    modules = [dict(m) for m in catalog()]
    modules[0]["dependencies"] = ["unknown"]
    with pytest.raises(planner.NamespacePlanError, match="Missing module dependency"):
        planner.plan_bindings([modules[0]["id"] + ":m"], modules)


def test_cycle_rejected():
    modules = [dict(m) for m in catalog()]
    modules[0]["dependencies"] = [modules[1]["id"]]
    modules[1]["dependencies"] = [modules[0]["id"]]
    with pytest.raises(planner.NamespacePlanError, match="cycle"):
        planner.plan_bindings([modules[0]["id"] + ":m"], modules)
