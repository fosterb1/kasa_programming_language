#!/usr/bin/env python3
"""G0.5a restricted, opt-in hygienic source linker for pinned Kasa stdlib.

Produces flattened Kasa source ONLY after static preflight, rejecting unsupported
binding patterns. Not a native parser, sandbox, runtime loader or KBC format.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from kasa import parse  # noqa: E402
from kasa.core import BUILTIN_NAMES, KasaError, Node  # noqa: E402
from preflight_native_modules import preflight  # noqa: E402
from validate_kasa_catalog import ALLOWED, _is_linked, load_catalog  # noqa: E402

RESERVED_PREFIX = "__kasa_g05_"
MAX_OUTPUT_BYTES = 100_000


class HygienicLinkError(ValueError):
    """Unrepresentable source binding or unsafe output path."""


def walk(node):
    if isinstance(node, Node):
        yield node
        yield from walk(node.children)
    elif isinstance(node, (tuple, list)):
        for child in node:
            yield from walk(child)


def _quoted(value: str) -> str:
    # Kasa lexer supports exactly these escapes; prevent host repr differences.
    return '"' + (value.replace("\\", "\\\\").replace('"', '\\"')
                     .replace("\n", "\\n").replace("\r", "\\r")
                     .replace("\t", "\\t")) + '"'


def _expr(node: Node, functions: dict[str, str], aliases: dict[str, str],
          *, module: bool = False, called: bool = False) -> str:
    kind = node.kind
    if kind == "literal":
        v = node.value
        if v is None:
            return "hwee"
        if v is True:
            return "nokware"
        if v is False:
            return "atoro"
        if isinstance(v, str):
            return _quoted(v)
        if type(v) in (int, float):
            return repr(v)
        raise HygienicLinkError("Unsupported Kasa literal")
    if kind == "name":
        name = node.value
        if module and name in functions:
            return functions[name]
        return name
    if kind == "module_member":
        if module or not called:
            raise HygienicLinkError("Only direct module function calls are supported")
        alias = node.children[0].value
        if alias not in aliases:
            raise HygienicLinkError("Unknown module alias")
        return RESERVED_PREFIX + aliases[alias] + "_" + node.value
    if kind == "call":
        callee, args = node.children
        return _expr(callee, functions, aliases, module=module, called=True) + "(" + ", ".join(
            _expr(arg, functions, aliases, module=module) for arg in args) + ")"
    if kind == "list":
        return "[" + ", ".join(_expr(item, functions, aliases, module=module)
                                for item in node.children) + "]"
    if kind == "index":
        return _expr(node.children[0], functions, aliases, module=module) + "[" + _expr(
            node.children[1], functions, aliases, module=module) + "]"
    if kind == "unary":
        operator = "ɛnyɛ " if node.value == "NOT" else "-"
        return "(" + operator + _expr(node.children[0], functions, aliases, module=module) + ")"
    if kind == "binary":
        op = {"AND": "ne", "OR": "anaa"}.get(node.value, node.value)
        return "(" + _expr(node.children[0], functions, aliases, module=module) + " " + op + " " + _expr(
            node.children[1], functions, aliases, module=module) + ")"
    raise HygienicLinkError("Unsupported expression for native source linker: " + kind)


def _statements(nodes, functions: dict[str, str], aliases: dict[str, str],
                *, module: bool, indent: int = 0) -> list[str]:
    lines = []
    prefix = "    " * indent
    def exp(n):
        return _expr(n, functions, aliases, module=module)
    for stmt in nodes:
        kind = stmt.kind
        if kind == "function":
            if module and indent > 0:
                raise HygienicLinkError("Nested module functions are unsupported")
            name, params = stmt.value
            emitted_name = functions.get(name, name) if module else name
            lines.append(prefix + "dwumadie " + emitted_name + "(" + ", ".join(params) + ")")
            lines.extend(_statements(stmt.children[0], functions, aliases, module=module, indent=indent + 1))
            lines.append(prefix + "awiei")
        elif kind == "print":
            lines.append(prefix + "ka " + exp(stmt.children[0]))
        elif kind == "assign":
            target, value = stmt.children
            lines.append(prefix + "ma " + exp(target) + " = " + exp(value))
        elif kind == "return":
            value = stmt.children[0]
            lines.append(prefix + "sanma" + (" " + exp(value) if value is not None else ""))
        elif kind == "expression":
            lines.append(prefix + exp(stmt.children[0]))
        elif kind == "if":
            condition, yes, no = stmt.children
            lines.append(prefix + "sɛ " + exp(condition) + " a")
            lines.extend(_statements(yes, functions, aliases, module=module, indent=indent + 1))
            if no:
                lines.append(prefix + "anyɛ_saa_a")
                lines.extend(_statements(no, functions, aliases, module=module, indent=indent + 1))
            lines.append(prefix + "awiei")
        elif kind in ("while", "repeat"):
            condition, body = stmt.children
            lines.append(prefix + ("bere_a " if kind == "while" else "mpɛn ") + exp(condition))
            lines.extend(_statements(body, functions, aliases, module=module, indent=indent + 1))
            lines.append(prefix + "awiei")
        elif kind == "break":
            lines.append(prefix + "gyae")
        elif kind == "continue":
            lines.append(prefix + "toa_so")
        else:
            raise HygienicLinkError("Unsupported statement for native source linker: " + kind)
    return lines


def link_source(source: str, *, root: Path = ROOT, filename: str = "<g05-link>") -> str:
    """Return self-contained source; no I/O side effects besides verified reads."""
    root = root.absolute()
    plan = preflight(source, filename=filename, root=root)
    program = parse(source, filename=filename, experimental_modules=True)
    body = [stmt for stmt in program if stmt.kind != "module_import"]
    aliases = {item["alias"]: item["module"] for item in plan["imports"]}
    catalog = {entry["id"]: entry for entry in load_catalog(root / "stdlib/catalog.json", root)}

    # No caller may name a synthesized internal symbol. The guard checks AST
    # identifiers, not comments or literal text.
    for node in walk(body):
        if node.kind == "name" and node.value.startswith(RESERVED_PREFIX):
            raise HygienicLinkError("Application uses reserved internal linker name")
        if node.kind == "function" and node.value[0].startswith(RESERVED_PREFIX):
            raise HygienicLinkError("Application declares reserved internal linker function")
        if node.kind == "function" and any(p.startswith(RESERVED_PREFIX) for p in node.value[1]):
            raise HygienicLinkError("Application declares reserved internal linker parameter")

    parts = []
    for module in plan["load_order"]:
        path = root / ALLOWED[module]
        if _is_linked(path, root) or not path.is_file():
            raise HygienicLinkError("Linked or missing module source")
        data = path.read_bytes().replace(b"\r\n", b"\n")
        if "sha256:" + hashlib.sha256(data).hexdigest() != catalog[module]["content_identity"]:
            raise HygienicLinkError("Module identity changed before emission")
        ast = parse(data.decode("utf-8", "strict"), filename=catalog[module]["source"])
        functions = {stmt.value[0]: RESERVED_PREFIX + module + "_" + stmt.value[0] for stmt in ast}
        for stmt in ast:
            if stmt.kind != "function":
                raise HygienicLinkError("Only function-only modules are supported")
            params = stmt.value[1]
            if any(name in functions for name in params):
                raise HygienicLinkError("Module parameter shadows module function")
            for node in walk(stmt.children):
                if node.kind == "function":
                    raise HygienicLinkError("Nested function declarations inside modules unsupported")
                if node.kind == "assign":
                    target = node.children[0]
                    while target.kind == "index":
                        target = target.children[0]
                    if target.kind == "name" and target.value in functions:
                        raise HygienicLinkError("Module local shadows module function")
                if node.kind == "name" and node.value not in functions and node.value not in params and node.value not in BUILTIN_NAMES:
                    # Locals may have been assigned in the function body, or
                    # the AST may contain a free variable. Reject the latter.
                    locals_ = {inner.children[0].value for inner in walk(stmt.children)
                               if inner.kind == "assign" and inner.children[0].kind == "name"}
                    if node.value not in locals_:
                        raise HygienicLinkError("Module contains unresolved free name: " + node.value)
        parts.extend(_statements(ast, functions, {}, module=True))
        parts.append("")

    parts.extend(_statements(body, {}, aliases, module=False))
    result = "\n".join(parts).rstrip() + "\n"
    if len(result.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise HygienicLinkError("Linked Kasa source exceeds size limit")
    # Check that the native parser's expected non-experimental syntax is valid
    # in the Python reference parser; native verification remains separate.
    parse(result, filename="<g05-linked>")
    return result


def write_linked_source(application: Path, output: Path, *, root: Path = ROOT) -> Path:
    root = root.absolute()
    target_dir = root / "build" / "g05-linked"
    out = output.absolute()
    if out.parent != target_dir or out.suffix != ".kasa" or out.name == ".kasa":
        raise HygienicLinkError("Output must be directly inside build/g05-linked as .kasa")
    if out.exists() or out.is_symlink():
        raise HygienicLinkError("Refusing to overwrite linked source")
    if any(part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction())
           for part in (root, root / "build", target_dir)):
        raise HygienicLinkError("Linked output directory refused")
    if not application.is_file() or application.is_symlink():
        raise HygienicLinkError("Application must be a regular source file")
    payload = application.read_bytes()
    if len(payload) > 50_000:
        raise HygienicLinkError("Application source exceeds size limit")
    linked = link_source(payload.decode("utf-8", "strict"), root=root, filename=str(application))
    target_dir.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(linked)
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        print("Created experimental G0.5 linked source:",
              write_linked_source(args.app, args.output))
    except (KasaError, HygienicLinkError, OSError, UnicodeError, ValueError) as error:
        print("G0.5 link refused: " + str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
