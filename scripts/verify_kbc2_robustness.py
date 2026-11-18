"""Deterministic KBC2 loader robustness test (no execution of mutated bytecode).

Compile known KBC2 fixtures, mutate bytes, and feed each result to the loader
through check-bytecode. Run in normal or sanitizer-instrumented native builds.
This is bounded negative/robustness testing, NOT exhaustive security fuzzing.
"""
from __future__ import annotations

import argparse
import binascii
import json
import pathlib
import random
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURE_PATH = ROOT / "tests" / "conformance_arbitrary_integers.json"
SEED = 0x4B424332
MAX_CASES = 320


def run(binary: pathlib.Path, command: str, file: pathlib.Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run([str(binary), command, str(file)],
                          capture_output=True, timeout=10, check=False)


def checksum(data: bytearray) -> None:
    data[12:16] = (binascii.crc32(data[16:]) & 0xffffffff).to_bytes(4, "little")


def check_exit(result: subprocess.CompletedProcess[bytes], label: str) -> None:
    # Expected results are successful validation or a controlled validation
    # error (1/2). A signal, timeout, abort or a sanitizer report is a failure.
    if result.returncode not in (0, 1, 2):
        raise AssertionError(f"{label}: loader terminated abnormally ({result.returncode}): "
                             f"{result.stderr.decode('utf-8', 'replace')[:350]}")
    if b"AddressSanitizer" in result.stderr or b"runtime error:" in result.stderr:
        raise AssertionError(f"{label}: sanitizer diagnostic: {result.stderr[:350]!r}")


def mutate(data: bytes, rng: random.Random, index: int) -> tuple[bytes, bool]:
    altered = bytearray(data)
    variant = index % 8
    must_reject = False
    if variant == 0:
        altered[0] ^= 1                     # wrong magic
        must_reject = True
    elif variant == 1:
        altered[4] = 255                   # wrong version
        must_reject = True
    elif variant == 2:
        altered[6] = 1                     # unsupported flags
        must_reject = True
    elif variant == 3:
        altered[8:12] = (0).to_bytes(4, "little")
        must_reject = True
    elif variant == 4:
        offset = rng.randrange(16, len(altered))
        altered[offset] ^= 1 << rng.randrange(8)  # CRC deliberately stale
        must_reject = True
    elif variant == 5:
        altered = altered[:-rng.randint(1, min(9, len(altered) - 16))]
        must_reject = True
    elif variant == 6:
        offset = rng.randrange(16, len(altered))
        altered[offset] ^= 1 << rng.randrange(8)
        checksum(altered)                  # deeper parser/VM verifier
    else:
        offset = rng.randrange(16, len(altered))
        altered[offset] = rng.randrange(256)
        checksum(altered)
    return bytes(altered), must_reject


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=pathlib.Path, required=True)
    args = parser.parse_args()
    binary = args.binary.resolve()
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))["cases"]
    # Include a small int64-only KBC2 program and examples containing large
    # literals, nested list data and nested function bodies.
    selected = [
        next(case for case in fixtures if case["name"] == name)
        for name in ("big_int_literal", "nested_list_bigint_equality",
                     "big_int_multiply", "big_int_to_text_roundtrip")
    ]
    rng = random.Random(SEED)
    trials = 0
    rejected = 0
    admitted = 0
    with tempfile.TemporaryDirectory(prefix="kasa-kbc2-mutations-") as directory:
        folder = pathlib.Path(directory)
        source = folder / "fixture.kasa"
        original = folder / "original.kbc"
        changed = folder / "changed.kbc"
        for case in selected:
            source.write_bytes(case["source"].encode("utf-8"))
            compiled = run(binary, "compile-kbc2", source)
            if compiled.returncode != 0:
                raise AssertionError(f"Compilation failed for {case['name']}: {compiled.stderr!r}")
            # compile writes <source-stem>.kbc when no -o argument is present
            raw = source.with_suffix(".kbc").read_bytes()
            if raw[:6] != b"KBC2\x02\x00":
                raise AssertionError(f"Invalid reference header: {case['name']}")
            for i in range(MAX_CASES // len(selected)):
                damaged, must_reject = mutate(raw, rng, i)
                changed.write_bytes(damaged)
                outcome = run(binary, "check-bytecode", changed)
                check_exit(outcome, f"{case['name']} #{i}")
                if must_reject and outcome.returncode == 0:
                    raise AssertionError(f"{case['name']} #{i}: corrupted envelope accepted")
                trials += 1
                if outcome.returncode == 0:
                    admitted += 1  # checksum-adjusted changes may remain valid
                else:
                    rejected += 1
    if trials != MAX_CASES or rejected == 0:
        raise AssertionError("Incomplete mutation coverage")
    print(f"PASS KBC2 robustness: {trials} deterministic mutations, "
          f"{rejected} rejected, {admitted} structurally accepted; no abnormal exits")
    print("Note: accepted modified bytecode was never executed.")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, OSError, ValueError, StopIteration, subprocess.TimeoutExpired) as exc:
        print(f"FAIL KBC2 robustness: {exc}", file=sys.stderr)
        sys.exit(1)
