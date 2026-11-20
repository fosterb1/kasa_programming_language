#!/usr/bin/env python3
"""Read-only local topology and scope audit for stacked experimental G0.4/G0.5 PRs.

No network calls, branch changes, merges, writes, or approval side effects.
Exit 0 means the expected Git ancestry/file scope matches, NOT merge approval.
Run on a checkout after 'git fetch origin' has been done deliberately by owner.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
MAIN = "refs/remotes/origin/main"
G04 = "refs/remotes/origin/dev/g04-module-cross-runtime-fixtures"
G05 = "refs/remotes/origin/dev/g05-native-module-contract"

G04_FILES = frozenset({
    "docs/G03_SOURCE_IMPORT_ACCEPTANCE.md",
    "docs/G04_SHARED_MODULE_CONFORMANCE.md",
    "playground/kasa-runtime.js",
    "scripts/run_kasa_modules_experimental.py",
    "scripts/verify_real_module_browser.py",
    "tests/conformance_experimental_modules.json",
    "tests/test_g03_source_import_acceptance.py",
    "tests/test_js_module_cross_runtime_fixtures.cjs",
    "tests/test_module_cross_runtime_fixtures.py",
})
G05_REQUIRED = frozenset({
    "scripts/compile_g05_modules.py",
    "scripts/link_kasa_modules_hygienic.py",
    "scripts/verify_g05_release.py",
    "tests/test_g05_strict_publication.py",
    "tests/test_g05_publication_race.py",
    "docs/G05_EXIT_REVIEW.md",
})
G05_ALLOWED_PREFIXES = ("docs/", "scripts/", "tests/")


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True,
        text=True, encoding="utf-8", errors="replace", check=False, timeout=30,
    )


def checked(*args: str) -> str:
    command = git(*args)
    if command.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {command.stderr.strip() or 'failed'}")
    return command.stdout.strip()


def ancestor(parent: str, child: str) -> bool:
    return git("merge-base", "--is-ancestor", parent, child).returncode == 0


def changed_files(base: str, head: str) -> set[str]:
    return set(filter(None, checked(
        "diff", "--name-only", "--diff-filter=ACDMRTUXB", f"{base}...{head}"
    ).splitlines()))


def audit() -> dict:
    revisions = {name: checked("rev-parse", "--verify", ref) for name, ref in
                 (("main", MAIN), ("g04", G04), ("g05", G05))}
    changes04 = changed_files(MAIN, G04)
    changes05 = changed_files(G04, G05)
    head = checked("rev-parse", "HEAD")
    tracked_status = checked("status", "--porcelain", "--untracked-files=no")
    checks = {
        "main_ancestor_of_g04": ancestor(MAIN, G04),
        "g04_ancestor_of_g05": ancestor(G04, G05),
        "g04_exact_file_scope": changes04 == G04_FILES,
        "g05_minimum_expected_files": G05_REQUIRED <= changes05,
        "g05_files_restricted_to_docs_scripts_tests": all(
            path.startswith(G05_ALLOWED_PREFIXES) for path in changes05
        ),
        "no_native_or_core_parser_changed_in_g05": all(
            not path.startswith(("native/", "src/", "playground/")) for path in changes05
        ),
        "local_head_matches_g05_remote": head == revisions["g05"],
        "tracked_worktree_clean": not tracked_status,
    }
    return {
        "schema_version": 1,
        "purpose": "read-only experimental integration topology check",
        "revisions": revisions,
        "local_head": head,
        "checks": checks,
        "g04_changed_files": sorted(changes04),
        "g05_changed_files": sorted(changes05),
        "tracked_worktree_status": tracked_status,
        "status": "scope_ok_not_merge_approval" if all(checks.values()) else "review_required",
        "caveat": (
            "Scope/topology checks do not run code, prove security, authorize a merge, "
            "or replace release evidence and independent review."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pretty", action="store_true", help="print readable JSON")
    args = parser.parse_args(argv)
    try:
        result = audit()
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "review_required", "error": str(error)}))
        return 2
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0 if result["status"] == "scope_ok_not_merge_approval" else 1


if __name__ == "__main__":
    raise SystemExit(main())
