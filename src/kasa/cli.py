"""Command-line tools for running and checking Kasa programs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .core import Interpreter, KasaError, parse
from .diagnostics import explain_error


def run_file(path: str, check: bool = False, explain: bool = False,
             diagnostics_json: bool = False) -> int:
    source = ""
    try:
        source = Path(path).read_text(encoding="utf-8")
        program = parse(source, filename=path)
        if not check:
            Interpreter(filename=path).run(program)
        return 0
    except (OSError, UnicodeError) as exc:
        if diagnostics_json:
            print(json.dumps({"schema_version": 1, "category": "FileError",
                              "message": f"Cannot read source: {exc}", "file": path,
                              "line": None, "column": None}, ensure_ascii=False), file=sys.stderr)
        else:
            print(f"kasa: cannot read {path}: {exc}", file=sys.stderr)
        return 2
    except KasaError as exc:
        if diagnostics_json:
            print(json.dumps({"schema_version": 1, "category": exc.category,
                              "message": exc.message, "file": exc.filename,
                              "line": exc.token.line, "column": exc.token.column},
                             ensure_ascii=False), file=sys.stderr)
        else:
            print(explain_error(exc, source) if explain else exc, file=sys.stderr)
        return 1


def repl() -> int:
    print("Kasa 0.1 REPL — type 'exit' or 'quit' to leave")
    runtime = Interpreter(filename="<repl>")
    lines: list[str] = []
    depth = 0
    try:
        while True:
            try:
                line = input("... " if depth else "kasa> ")
            except EOFError:
                print()
                return 0
            if not lines and line.strip() in ("exit", "quit"):
                return 0
            lines.append(line)
            word = line.strip().split(maxsplit=1)[0] if line.strip() else ""
            if word in ("sɛ", "mpɛn", "bere_a", "dwumadie"):
                depth += 1
            elif word == "awiei":
                depth = max(0, depth - 1)
            if depth:
                continue
            source = "\n".join(lines) + "\n"
            lines = []
            try:
                runtime.run(parse(source, filename="<repl>"))
            except KasaError as exc:
                print(exc, file=sys.stderr)
    except KeyboardInterrupt:
        print("\nGoodbye")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="kasa", description="A Twi-first educational programming language")
    parser.add_argument("--version", action="version", version=f"Kasa {__version__}")
    subs = parser.add_subparsers(dest="command", required=True)
    for command in ("run", "check"):
        sub = subs.add_parser(command, help=f"{command.title()} a .kasa program")
        sub.add_argument("file", help="Path to a UTF-8 .kasa source file")
        diagnostic = sub.add_mutually_exclusive_group()
        diagnostic.add_argument("--explain", action="store_true", help="Show the source line and a beginner-friendly correction hint")
        diagnostic.add_argument("--diagnostics-json", action="store_true",
                                help="Emit one structured JSON object to stderr on error (schema v1)")
    subs.add_parser("repl", help="Start an interactive Kasa interpreter")
    args = parser.parse_args(argv)
    if args.command == "repl":
        return repl()
    return run_file(args.file, check=args.command == "check", explain=args.explain,
                    diagnostics_json=args.diagnostics_json)


if __name__ == "__main__":
    raise SystemExit(main())
