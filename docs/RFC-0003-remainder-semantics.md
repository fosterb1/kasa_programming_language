# RFC-0003 — Signed integer remainder in Kasa

**Status:** Implemented in branch `feature/remainder-conformance-v1`; regression tests provided; review and release testing ongoing.  
**Date:** 2026-11-17  
**Scope:** Existing `%` operator; **no new Twi words or keywords**.

## Problem

Python's integer `%` uses floor-division semantics. JavaScript BigInt and C++ use a truncating remainder, causing the same Kasa code to produce different outputs. This is unacceptable for classroom exercises and portable `.kasa` files.

Before this change, `ka -7 % 3` printed `2` with Python but `-1` with the browser and native VM.

## Normative rule

For any integer `a` and nonzero integer `b`:

```text
q = floor(a / b)
r = a - q * b
a % b == r
```

The following properties hold:

- `a == q * b + r`.
- `abs(r) < abs(b)`.
- `r == 0` or `r` has the **same sign as the divisor** `b`.
- Both operands must be integers. Boolean and floating-point operands cause a `TypeError`.
- `b == 0` causes a `ZeroDivisionError`.
- The existing numeric limits remain: the C++ runtime uses signed 64-bit integers, while Python/JavaScript support larger bounded integers. This RFC does **not** address that limitation.

## Examples

| Source expression | Kasa result |
|---|---:|
| `7 % 3` | `1` |
| `-7 % 3` | `2` |
| `7 % -3` | `-2` |
| `-7 % -3` | `-1` |
| `-9 % 3` | `0` |
| `9007199254740993 % 7` | `5` |

## Implementation and tests

Python is the reference implementation and already follows the specified rule. JavaScript and C++ adjust the truncating remainder when its nonzero sign differs from that of the divisor. The native VM preserves its existing special case for `INT64_MIN % -1` to avoid undefined signed overflow.

The shared corpus at [`tests/conformance_remainder.json`](../tests/conformance_remainder.json) contains successful cases and error categories. It runs in Python pytest, JavaScript Node tests, and the native VM's Python-driven comparison harness. New cases should be added to the shared corpus rather than only to one runtime.

## Compatibility

This changes **existing** JavaScript and native behavior for signed operands, to match the Python reference. Any program depending on C++/JavaScript-style truncating remainder may produce a different result. The change is intentional, documented, and must be identified in release notes.

## Linguistic and governance review

No new linguistic term is introduced. The current Twi tokens remain subject to the [linguistic evidence policy](./LANGUAGE_RESEARCH_POLICY.md). The existing `%` symbol is mathematical syntax, not a Twi word. Further language behavior differences should receive similarly explicit semantic documentation and cross-runtime fixtures.
