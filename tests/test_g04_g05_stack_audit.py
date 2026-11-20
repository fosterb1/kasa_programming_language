"""Read-only branch-audit classification tests; no real Git checkout modified."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "g04_g05_stack_audit", ROOT / "scripts" / "audit_g04_g05_stack.py"
)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def setup_snapshot(monkeypatch, *, dirty=False, omit_g04=False,
                   surprise_native=False, broken_ancestry=False, merged=False):
    revisions = {
        module.MAIN: "a" * 40,
        module.G04: "b" * 40,
        module.G05: "c" * 40,
        "HEAD": "c" * 40,
    }
    def checked(*args):
        if args[:2] == ("rev-parse", "--verify") and args[2].endswith("^{tree}"):
            return "d" * 40
        if args[:2] == ("rev-parse", "--verify"):
            return revisions[args[2]]
        if args == ("rev-parse", "HEAD"):
            return revisions["HEAD"]
        if args == ("status", "--porcelain", "--untracked-files=no"):
            return " M scripts/foo.py" if dirty else ""
        raise AssertionError(args)
    def files(base, head):
        if base == (module.MAIN + "^1" if merged else module.MAIN):
            items = set(module.G04_FILES)
            if omit_g04:
                items.remove("playground/kasa-runtime.js")
            return items
        assert base == (module.MAIN if merged else module.G04)
        result = set(module.G05_REQUIRED)
        if surprise_native:
            result.add("native/src/parser.cpp")
        return result
    monkeypatch.setattr(module, "checked", checked)
    monkeypatch.setattr(module, "changed_files", files)
    def ancestry(a, b):
        if broken_ancestry:
            return False
        edges = ({(module.G04, module.MAIN), (module.MAIN, module.G05),
                  (module.G04, module.G05)} if merged else
                 {(module.MAIN, module.G04), (module.G04, module.G05)})
        return (a, b) in edges
    monkeypatch.setattr(module, "ancestor", ancestry)
    return revisions


def test_clean_stacked_scope_is_not_merge_approval(monkeypatch):
    setup_snapshot(monkeypatch)
    result = module.audit()
    assert result["status"] == "scope_ok_not_merge_approval"
    assert all(result["checks"].values())
    assert "not" in result["caveat"]


def test_dirty_worktree_forces_review(monkeypatch):
    setup_snapshot(monkeypatch, dirty=True)
    result = module.audit()
    assert result["status"] == "review_required"
    assert result["checks"]["tracked_worktree_clean"] is False


def test_unexpected_g04_diff_forces_review(monkeypatch):
    setup_snapshot(monkeypatch, omit_g04=True)
    result = module.audit()
    assert result["checks"]["g04_exact_file_scope"] is False
    assert result["status"] == "review_required"


def test_native_change_in_g05_forces_review(monkeypatch):
    setup_snapshot(monkeypatch, surprise_native=True)
    result = module.audit()
    assert result["checks"]["no_native_or_core_parser_changed_in_g05"] is False
    assert result["status"] == "review_required"


def test_ancestry_break_forces_review(monkeypatch):
    setup_snapshot(monkeypatch, broken_ancestry=True)
    result = module.audit()
    assert result["checks"]["g04_integrated_into_main_or_pre_merge_main_is_ancestor"] is False
    assert result["checks"]["g04_ancestor_of_g05"] is False
    assert result["status"] == "review_required"


def test_post_merge_main_topology_passes(monkeypatch):
    setup_snapshot(monkeypatch, merged=True)
    result = module.audit()
    assert result["topology"] == "g04_merged_main_g05_reconciled"
    assert result["status"] == "scope_ok_not_merge_approval"
    assert all(result["checks"].values())


def test_post_merge_unexpected_native_change_fails(monkeypatch):
    setup_snapshot(monkeypatch, merged=True, surprise_native=True)
    result = module.audit()
    assert result["status"] == "review_required"
    assert result["checks"]["no_native_or_core_parser_changed_in_g05"] is False


def test_post_merge_wrong_tree_fails(monkeypatch):
    setup_snapshot(monkeypatch, merged=True)
    old = module.checked
    def altered(*args):
        if args == ("rev-parse", "--verify", module.G04 + "^{tree}"):
            return "f" * 40
        return old(*args)
    monkeypatch.setattr(module, "checked", altered)
    result = module.audit()
    assert result["status"] == "review_required"
    assert result["checks"]["main_tree_matches_g04_after_merge"] is False
