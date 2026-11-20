#!/usr/bin/env python3
"""G0.5 KBC1 independence and malformed-bytecode regression gate.

Compiles opt-in, pinned Kasa module source to ordinary KBC1 through the
existing native compiler. Verifies that execution succeeds after linked source
is deleted and rejects targeted corrupted copies before any VM output.

No source, standard-library, catalog, or KBC1 format is modified.
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

from link_kasa_modules_hygienic import link_source  # noqa: E402

NATIVE = ROOT / "build" / "kasa-local" / (
    "Release/kasa-native.exe" if os.name == "nt" else "kasa-native"
)
PROGRAM = (
    "fa math firi stdlib: m\n"
    "fa collections firi stdlib: c\n"
    "ka m.kasa_sum([10, 20, 30])\n"
    "ka c.kasa_contains([1, 2, 3], 2)\n"
)
EXPECTED = "60\nnokware\n"


def invoke(native: Path, *arguments: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(native), *arguments], cwd=ROOT,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=timeout, check=False,
    )


def checked(native: Path, *arguments: str) -> str:
    result = invoke(native, *arguments)
    if result.returncode or result.stderr:
        raise AssertionError(
            f"Native command failed: {arguments!r}, code={result.returncode}, "
            f"stdout={result.stdout!r}, stderr={result.stderr!r}"
        )
    return result.stdout


def reject(native: Path, path: Path, label: str) -> None:
    checked_modes = ("check-bytecode", "run-bytecode")
    for mode in checked_modes:
        result = invoke(native, mode, str(path))
        if result.returncode == 0:
            raise AssertionError(f"{label}: {mode} accepted invalid KBC1")
        if result.stdout:
            raise AssertionError(f"{label}: {mode} produced stdout before rejection")
    print("PASS rejected " + label + " (check + execute)", flush=True)


def verify(native_path: Path) -> None:
    native = native_path.resolve(strict=True)
    if not native.is_file():
        raise OSError("Native executable missing: " + str(native))
    with tempfile.TemporaryDirectory(prefix="kasa-g05-kbc-") as tmp:
        folder = Path(tmp)
        linked = folder / "linked.kasa"
        bytecode = folder / "linked.kbc"
        linked.write_text(link_source(PROGRAM, filename="g05-independence.kasa"),
                          encoding="utf-8", newline="\n")
        checked(native, "compile", str(linked), "-o", str(bytecode))
        original = bytecode.read_bytes()
        if not original.startswith(b"KBC1") or len(original) < 20:
            raise AssertionError("Expected a nonempty KBC1 artifact")
        checked(native, "check-bytecode", str(bytecode))
        if checked(native, "run-bytecode", str(bytecode)) != EXPECTED:
            raise AssertionError("Initial compiled output differs from reference")

        # The runtime sees only a compiled KBC1 file. Removing intermediate
        # source proves the executable cannot rely on that source at runtime.
        linked.unlink()
        if checked(native, "run-bytecode", str(bytecode)) != EXPECTED:
            raise AssertionError("KBC1 depends on linked source at execution")
        print("PASS self-contained KBC1 after linked source deletion", flush=True)

        cases: dict[str, bytes] = {
            "wrong-magic": b"BAD!" + original[4:],
            "unsupported-version": original[:4] + b"\xff\xff" + original[6:],
            "truncated": original[:-1],
            "trailing-data": original + b"\x00",
            "body-byte-flip": original[:18] + bytes([original[18] ^ 0x80]) + original[19:],
        }
        for label, mutation in cases.items():
            modified = folder / (label + ".kbc")
            modified.write_bytes(mutation)
            reject(native, modified, label)
    print("PASS G0.5 KBC1 independence and 5 corruption cases "
          "(10 rejection checks), no bytecode format changes")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, default=NATIVE)
    arguments = parser.parse_args(argv)
    try:
        verify(arguments.native)
    except (OSError, ValueError, AssertionError, subprocess.TimeoutExpired) as error:
        print("FAIL G0.5 KBC1 safety: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
