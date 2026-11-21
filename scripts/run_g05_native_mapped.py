#!/usr/bin/env python3
"""Run experimental Kasa imports with native C++ and mapped statement errors.

Uses trusted catalog prelinking into a temporary ordinary Kasa file. The
native CLI itself remains unchanged; output/diagnostics are not fabricated.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from annotate_g05_diagnostic import annotate  # noqa: E402
from link_kasa_modules_hygienic import link_source  # noqa: E402

DEFAULT_NATIVE = ROOT / "build" / "kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)


def run_mapped(program: str, filename: str, native: Path, *, timeout: int = 30) -> tuple[int, str, str]:
    """Return real exit code, stdout and annotated stderr, with temporary files."""
    if not native.is_file():
        raise OSError("Native compiler executable is missing: " + str(native))
    mapping = {}
    linked = link_source(program, filename=filename, source_map=mapping)
    with tempfile.TemporaryDirectory(prefix="kasa-g05-mapped-") as folder:
        path = Path(folder) / "linked.kasa"
        path.write_text(linked, encoding="utf-8", newline="\n")
        result = subprocess.run(
            [str(native.resolve()), "run", str(path)], cwd=ROOT,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=timeout, check=False,
        )
        # Treat each diagnostic line independently. Exact file prefix required,
        # including on Windows where the filename may start with a drive letter.
        stderr = "\n".join(
            annotate(line, str(path), linked, mapping)
            for line in result.stderr.splitlines()
        )
        if result.stderr.endswith("\n"):
            stderr += "\n"
        return result.returncode, result.stdout, stderr


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--native", type=Path, default=DEFAULT_NATIVE)
    args = parser.parse_args(argv)
    try:
        program = args.app.read_text(encoding="utf-8")
        code, stdout, stderr = run_mapped(program, str(args.app), args.native)
    except (OSError, UnicodeError, ValueError, subprocess.TimeoutExpired) as error:
        print("G0.5 native mapped execution refused: " + str(error),
              file=sys.stderr)
        return 2
    sys.stdout.write(stdout)
    sys.stderr.write(stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
