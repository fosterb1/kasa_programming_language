"""Deterministically compare the native binary64 formatter with Python's display.

The probe accepts hexadecimal IEEE-754 binary64 bits, one per line.
This tests a component and does not replace full native VM/KBC1 parity.
"""
from __future__ import annotations

import math
from pathlib import Path
import random
import struct
import subprocess
import sys


def run(binary: Path, *, n: int = 10_000) -> int:
    if not binary.is_file():
        print(f"Missing native probe executable: {binary}", file=sys.stderr)
        return 2
    rng = random.Random(20261118)
    bits = [rng.getrandbits(64) for _ in range(n)]
    values = [(b, struct.unpack(">d", b.to_bytes(8, "big"))[0]) for b in bits]
    values = [(b, number) for b, number in values if math.isfinite(number)]
    try:
        completed = subprocess.run(
            [str(binary)], input="".join(f"{b:016x}\n" for b, _ in values),
            capture_output=True, text=True, timeout=25, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Native decimal probe failed: {error}", file=sys.stderr)
        return 2
    if completed.returncode != 0:
        print(completed.stderr or f"Probe exited {completed.returncode}", file=sys.stderr)
        return 1
    actual = completed.stdout.splitlines()
    if len(actual) != len(values):
        print(f"Expected {len(values)} probe lines, got {len(actual)}", file=sys.stderr)
        return 1
    failures = [(i, repr(number), output) for i, ((_, number), output)
                in enumerate(zip(values, actual), start=1) if repr(number) != output]
    for index, expected, output in failures[:10]:
        print(f"FAIL sample {index}: Python {expected!r}, native {output!r}", file=sys.stderr)
    print(f"{len(values) - len(failures)}/{len(values)} deterministic native/Python decimal display comparisons passed")
    return 0 if not failures else 1


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python float_display_differential.py <native-probe>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(Path(sys.argv[1]).resolve()))
