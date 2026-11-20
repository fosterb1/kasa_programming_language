#!/usr/bin/env python3
"""G0.5 experimental native-error annotation from a checked source map.

Never rewrites KBC or claims exact expression columns. An annotation is only
produced when the supplied generated source hashes to the mapping's digest,
and the native diagnostic refers to the exact generated filename.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


class SourceMapError(ValueError):
    pass


def annotate(error: str, generated_file: str, linked_source: str, mapping: dict) -> str:
    if mapping.get("schema_version") != 1 or mapping.get("precision") != "statement_only":
        raise SourceMapError("Unsupported G0.5 source map")
    actual = hashlib.sha256(linked_source.encode("utf-8")).hexdigest()
    if mapping.get("generated_sha256") != actual:
        raise SourceMapError("Generated source does not match source map hash")
    rows = mapping.get("lines")
    if not isinstance(rows, list) or len(rows) != len(linked_source.splitlines()):
        raise SourceMapError("Source map line count disagrees with generated file")
    # Native diagnostics may contain a Windows drive colon. Match the exact
    # compiler filename first instead of splitting on arbitrary ':' tokens.
    prefix = generated_file + ":"
    if not error.startswith(prefix):
        return error
    tail = error[len(prefix):]
    match = re.match(r"(\d+):(\d+):\s*(.*)", tail, flags=re.DOTALL)
    if match is None:
        return error
    number = int(match.group(1))
    if not 1 <= number <= len(rows):
        return error
    entry = rows[number - 1]
    if entry.get("generated_line") != number:
        raise SourceMapError("Source map line indices are not sequential")
    if entry.get("precision") != "statement" or entry.get("synthetic"):
        return error
    filename = entry.get("file")
    line = entry.get("line")
    column = entry.get("column")
    if not isinstance(filename, str) or not filename or type(line) is not int or line < 1 or type(column) is not int or column < 1:
        raise SourceMapError("Invalid mapped source location")
    return (error + "\n"
            + f"  Kasa source statement: {filename}:{line}:{column} "
            + "(statement-level origin; expression column not mapped)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--linked", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--diagnostic", required=True,
                        help="Exact native diagnostic, including generated filename")
    arguments = parser.parse_args(argv)
    try:
        linked = arguments.linked.read_text(encoding="utf-8")
        mapping = json.loads(arguments.map.read_text(encoding="utf-8"))
        print(annotate(arguments.diagnostic, str(arguments.linked), linked, mapping))
    except (OSError, UnicodeError, ValueError, TypeError) as exc:
        print("G0.5 source map annotation refused: " + str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
