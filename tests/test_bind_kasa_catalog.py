"""G0.3 catalog-backed Python namespace binder tests.

Only trusted repository files or pytest's temporary directories are read.
No source is executed outside the bounded Kasa reference interpreter.
"""
import importlib.util
import io
from pathlib import Path
import shutil
import sys

import pytest

from kasa.core import Environment, Interpreter, Node, parse
from kasa.modules import ModuleBindingError

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
try:
    spec = importlib.util.spec_from_file_location(
        "bind_kasa_catalog", SCRIPTS / "bind_kasa_catalog.py"
    )
    binder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(binder)
finally:
    sys.path.remove(str(SCRIPTS))


def invoke(runtime, function, args):
    token = parse("ka 1")[0].token
    return runtime.evaluate(
        Node("call", token, children=(
            Node("name", token, value="selected"),
            tuple(Node("literal", token, value=value) for value in args),
        )),
        Environment({"selected": function}),
    )


@pytest.fixture
def copied_catalog(tmp_path):
    root = tmp_path / "repo"
    for relative in ["stdlib/catalog.json", *binder.ALLOWED.values()]:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return root, root / "stdlib/catalog.json"


def test_binds_real_pinned_libraries_without_global_leakage():
    runtime = Interpreter(stdout=io.StringIO())
    libraries = binder.bind_catalog_modules(runtime)
    assert set(libraries) == {"math", "collections"}
    assert runtime.globals.values == {}
    assert invoke(runtime, libraries["math"].resolve("kasa_sum"), [[3, 5, 7]]) == 15
    assert invoke(runtime, libraries["math"].resolve("kasa_abs"), [-8]) == 8
    assert invoke(
        runtime, libraries["collections"].resolve("kasa_count_equal"),
        [[2, 1, 2, 2], 2],
    ) == 3
    assert invoke(
        runtime, libraries["collections"].resolve("kasa_contains"), [[1, 2], 7]
    ) is False
    assert runtime.globals.values == {}


def test_private_or_unknown_export_is_refused():
    runtime = Interpreter(stdout=io.StringIO())
    libraries = binder.bind_catalog_modules(runtime)
    with pytest.raises(ModuleBindingError, match="does not export"):
        libraries["math"].resolve("secret")
    with pytest.raises(TypeError):
        libraries["math"].exports["new"] = libraries["math"].resolve("kasa_abs")


def test_copied_valid_catalog_binds(copied_catalog):
    root, path = copied_catalog
    runtime = Interpreter(stdout=io.StringIO())
    libraries = binder.bind_catalog_modules(runtime, catalog_path=path, root=root)
    assert invoke(runtime, libraries["math"].resolve("kasa_clamp"), [15, 0, 10]) == 10


def test_mutated_source_is_rejected_before_bind(copied_catalog):
    root, path = copied_catalog
    source = root / binder.ALLOWED["math"]
    source.write_bytes(source.read_bytes() + b"\n# mutation\n")
    runtime = Interpreter(stdout=io.StringIO())
    with pytest.raises(binder.CatalogError, match="hash mismatch"):
        binder.bind_catalog_modules(runtime, catalog_path=path, root=root)
    assert runtime.globals.values == {}


def test_unknown_catalog_export_is_rejected(copied_catalog):
    import json
    root, path = copied_catalog
    data = json.loads(path.read_text(encoding="utf-8"))
    data["modules"][0]["exports"].append("unknown_function")
    path.write_text(json.dumps(data), encoding="utf-8")
    runtime = Interpreter(stdout=io.StringIO())
    with pytest.raises(binder.CatalogError, match="undeclared"):
        binder.bind_catalog_modules(runtime, catalog_path=path, root=root)
    assert runtime.globals.values == {}
