"""G0.3 experimental *syntax study* for import declarations.

This module is deliberately separate from the Kasa tokenizer/parser. It
does not reserve any new Twi word or execute Kasa. English placeholder tokens
are research notation only, NOT planned user-facing syntax.
"""
from __future__ import annotations

from dataclasses import dataclass
import re

# Placeholder DSL used only by grammar contract tests.
# Not accepted by .kasa programs or shipped to browser/native.
_DECL = re.compile(
    r"module[ \t]+([a-z][a-z0-9_]*)[ \t]+alias[ \t]+([A-Za-z_][A-Za-z_0-9]*)\Z",
    re.ASCII,
)
_ACCESS = re.compile(
    r"([A-Za-z_][A-Za-z_0-9]*)\.([A-Za-z_][A-Za-z_0-9]*)\Z",
    re.ASCII,
)
_RESERVED = frozenset({
    "ka", "ma", "sɛ", "anyɛ_saa_a", "mpɛn", "bere_a",
    "dwumadie", "sanma", "awiei", "nokware", "atoro", "hwee",
    "ne", "anaa", "ɛnyɛ", "gyae", "toa_so",
})


class ModuleSyntaxStudyError(ValueError):
    pass


@dataclass(frozen=True)
class ImportDeclaration:
    module_id: str
    alias: str
    line: int


@dataclass(frozen=True)
class ExportAccess:
    alias: str
    member: str


def parse_declarations(source: str) -> tuple[ImportDeclaration, ...]:
    """Parse standalone *study text*; never interpret a real Kasa file.

    Only contiguous declaration lines are supported. Trailing executable
    source is deliberately rejected rather than silently stripped/executed.
    """
    declarations: list[ImportDeclaration] = []
    aliases: set[str] = set()
    modules: set[str] = set()
    for number, raw in enumerate(source.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = _DECL.fullmatch(line)
        if not match:
            raise ModuleSyntaxStudyError(f"Line {number}: invalid experimental module declaration")
        module, alias = match.groups()
        if alias in _RESERVED:
            raise ModuleSyntaxStudyError(f"Line {number}: reserved alias")
        if alias in aliases:
            raise ModuleSyntaxStudyError(f"Line {number}: duplicate alias")
        if module in modules:
            raise ModuleSyntaxStudyError(f"Line {number}: duplicate module")
        aliases.add(alias)
        modules.add(module)
        declarations.append(ImportDeclaration(module, alias, number))
    if not declarations:
        raise ModuleSyntaxStudyError("No module declarations")
    return tuple(declarations)


def parse_export_access(source: str) -> ExportAccess:
    """Require a single explicit namespace and member, no dynamic access."""
    match = _ACCESS.fullmatch(source)
    if not match:
        raise ModuleSyntaxStudyError("Expected alias.member")
    alias, member = match.groups()
    if alias in _RESERVED:
        raise ModuleSyntaxStudyError("Reserved alias")
    return ExportAccess(alias, member)


def check_access(
    declarations: tuple[ImportDeclaration, ...],
    access: ExportAccess,
    exports_by_module: dict[str, list[str]],
) -> str:
    """Static access check only; returns module ID, never a callable."""
    bindings = {decl.alias: decl.module_id for decl in declarations}
    if access.alias not in bindings:
        raise ModuleSyntaxStudyError(f"Unknown module alias: {access.alias}")
    module = bindings[access.alias]
    if module not in exports_by_module:
        raise ModuleSyntaxStudyError(f"Unknown catalog module: {module}")
    if access.member not in exports_by_module[module]:
        raise ModuleSyntaxStudyError(f"Module '{module}' does not export '{access.member}'")
    return module
