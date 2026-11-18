# Beginner-friendly Kasa diagnostics

Kasa is designed for learners, so syntax and runtime errors should teach—not
just stop execution. The Python reference CLI now offers an optional source
frame and an actionable hint. Both remain **opt-in** and do not alter Kasa
language semantics or error categories used for cross-runtime conformance.

```bash
kasa run examples/hello.kasa --explain
kasa check my_program.kasa --explain
```

If `ka unknown_name` is executed, the CLI shows the source location, points
to the relevant column, and suggests how to declare a variable with `ma`.
For a missing block terminator it explains when to use `awiei`.

This is the **first teaching interface**, not a completed Twi localization.
Hints are intentionally in simple English while referencing correct Twi
programming keywords. Native C++/WebAssembly and browser diagnostics are not
localized by this change. Future work should involve Ghanaian educators and
Twi speakers to review proposed localized labels and messages before shipping
an optional Twi-language translation across all runtimes.

The basic CLI remains backward compatible: without `--explain`, existing
one-line errors and exit codes remain unchanged. The display is bounded and
filters terminal control characters; Unicode visual caret alignment remains
approximate in unusual terminals that display multiple code points in a
single cell.
