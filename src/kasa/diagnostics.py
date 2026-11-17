"""Optional beginner-oriented error explanation for the Kasa reference CLI.

The human-facing messages are teaching aids; semantic error categories are
unchanged, so native and browser conformance checks remain meaningful.
"""

from __future__ import annotations

from .core import KasaError


def _hint(error: KasaError) -> str:
    """Return actionable guidance using valid Kasa syntax, never guessed fixes."""
    message = error.message.lower()
    category = error.category

    if category == "NameError":
        return "A name is being used before it is defined. Create it first: ma edin = \"Ama\". Check spelling, too."
    if category == "ZeroDivisionError":
        return "A divisor cannot be zero. Check the expression after / or % before calculating."
    if category == "IndexError":
        return "List positions start at 0. Check the index and compare it with tentɛn(your_list)."
    if category == "TypeError":
        if message.startswith("condition must") or message.startswith("condition needs"):
            return "A condition needs nokware or atoro (true or false). Try a comparison such as mfe >= 18."
        return "Check the types used together. Use nɔma(text) to convert numeric text, or nsɛm(value) to produce text."
    if category == "SyntaxError":
        if "awiei" in message or "end of file" in message or "block" in message:
            return "Finish each sɛ, mpɛn, bere_a, or dwumadie block with awiei on its own line."
        if "unterminated string" in message or "string escape" in message:
            return 'A text value needs matching double quotes, for example: ka "Maakye!".'
        if "assignment" in message or "target" in message:
            return "To assign a variable, write ma edin = \"Ama\". The left side must be a name or list position."
        return "Check the Kasa statement and punctuation. For example, printing text is: ka \"Maakye!\"."
    if category == "ResourceError":
        return "The program reached a safety limit. Check repeated loops, recursion, large lists and large numbers."
    return "Check the highlighted expression, then run the program again."


def _safe_line(source_line: str) -> str:
    """Make a short terminal-safe code preview without printing control sequences."""
    return "".join(ch if ch.isprintable() else " " for ch in source_line.expandtabs(4))


def explain_error(error: KasaError, source: str, *, max_width: int = 140) -> str:
    """Format a source frame and hint for CLI opt-in explain mode.

    Source columns are Unicode scalar positions in the reference lexer; the
    caret is approximate when terminal display widths differ (e.g. emoji).
    """
    # Error text may include a user-controlled filename; never emit terminal escapes.
    original = "".join(ch if ch.isprintable() else "?" for ch in str(error))
    out = [original]
    source_lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    line = error.token.line
    column = error.token.column
    if 1 <= line <= len(source_lines) and column >= 1:
        raw = source_lines[line - 1]
        safe = _safe_line(raw)
        # Limit terminal output, displaying a window around the location.
        point = min(max(0, column - 1), len(raw))
        left = max(0, point - max_width // 2)
        end = min(len(raw), max(left + max_width, point + 1))
        if end - left > max_width:
            left = end - max_width
        snippet = safe[left:end]
        # Python source columns count code points, but TAB expands on display.
        # The length of the displayed prefix determines the caret position.
        before = _safe_line(raw[:point])[len(_safe_line(raw[:left])):]
        prefix = "..." if left else ""
        suffix = "..." if end < len(safe) else ""
        gutter = f" {line} | "
        out.append(gutter + prefix + snippet + suffix)
        out.append(" " * (len(gutter) + len(prefix) + len(before)) + "^")
    out.append("Help: " + _hint(error))
    return "\n".join(out)
