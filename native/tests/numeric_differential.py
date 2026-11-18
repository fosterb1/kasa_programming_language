"""Differentially verify native mixed int64/binary64 comparisons against Python.

Run: python native/tests/numeric_differential.py build/kasa-local/kasa-numeric-compare-probe
Runs 10,000 deterministically seeded finite IEEE-754 values, plus 80 boundaries.
This is a targeted numeric helper test; it is NOT full native VM/KBC1 conformance.
"""
from __future__ import annotations

import math
from pathlib import Path
import random
import struct
import subprocess
import sys


SEED = 20261118
RANDOM_CASES = 10_000
BOUNDARY_INTS = (
    -(2**63), -(2**63) + 1, -(2**53) - 1, -1,
    0, 1, 2**53 + 1, 2**63 - 1,
)
BOUNDARY_FLOATS = (
    -1.0e300, -(2.0**63), -(2.0**53), -0.5, -0.0,
    0.0, 0.5, 2.0**53, 2.0**63, 1.0e300,
)


def cases() -> list[tuple[int, float]]:
    rng = random.Random(SEED)
    generated: list[tuple[int, float]] = []
    for _ in range(RANDOM_CASES):
        integer = rng.randrange(-(2**63), 2**63)
        while True:
            bits = rng.getrandbits(64)
            decimal = struct.unpack(">d", bits.to_bytes(8, "big"))[0]
            if math.isfinite(decimal):
                break
        generated.append((integer, decimal))
    generated.extend((i, d) for i in BOUNDARY_INTS for d in BOUNDARY_FLOATS)
    return generated


def verify(binary: Path) -> int:
    if not binary.is_file():
        print(f"FAIL: numeric probe not found: {binary}", file=sys.stderr)
        return 1
    fixtures = cases()
    requests = "".join(f"{integer} {decimal!r}\n" for integer, decimal in fixtures)
    expected = [int(integer > decimal) - int(integer < decimal)
                for integer, decimal in fixtures]
    try:
        completed = subprocess.run(
            [str(binary)], input=requests, capture_output=True, text=True,
            errors="replace", check=False, timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"FAIL: cannot execute numeric probe: {error}", file=sys.stderr)
        return 1
    if completed.returncode != 0:
        print(f"FAIL: numeric probe exited {completed.returncode}: "
              f"{completed.stderr[-1500:]}", file=sys.stderr)
        return 1
    try:
        actual = [int(line) for line in completed.stdout.splitlines()]
    except ValueError:
        print("FAIL: numeric probe returned noninteger output", file=sys.stderr)
        return 1
    if len(actual) != len(expected):
        print(f"FAIL: expected {len(expected)} comparisons, got {len(actual)}",
              file=sys.stderr)
        return 1
    mismatches = [index for index, (a, b) in enumerate(zip(actual, expected))
                  if a != b]
    if mismatches:
        for index in mismatches[:5]:
            print(f"FAIL case {index}: input={fixtures[index]!r}, "
                  f"native={actual[index]}, Python={expected[index]}",
                  file=sys.stderr)
        print(f"FAIL: {len(mismatches)} numeric mismatches", file=sys.stderr)
        return 1
    print(f"PASS: {len(expected)}/{len(expected)} Python/native numeric "
          f"comparisons matched (seed={SEED})")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: numeric_differential.py PATH_TO_NATIVE_PROBE", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(verify(Path(sys.argv[1]).resolve()))
