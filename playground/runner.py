"""Small, testable bridge between the Kasa interpreter and the web playground.

The supplied source is parsed as Kasa, never evaluated as Python. This bridge is
imported by Pyodide in a browser worker and can also be tested using CPython.
"""

from __future__ import annotations

from io import StringIO

from kasa.core import Interpreter, KasaError, parse
from kasa.learning_diagnostics import learning_hint

SOURCE_LIMIT = 50_000
INPUT_LIMIT = 50_000
OUTPUT_LIMIT = 64_000
STEP_LIMIT = 20_000


class OutputLimitError(Exception):
    """Raised when a Kasa program produces more than its output allowance."""


class LimitedOutput:
    """An output sink that caps total stored characters, including newlines."""

    def __init__(self, limit: int = OUTPUT_LIMIT) -> None:
        self.limit = limit
        self.parts: list[str] = []
        self.size = 0

    def write(self, text: str) -> int:
        text = str(text)
        if self.size + len(text) > self.limit:
            raise OutputLimitError(f"Output exceeded the {self.limit:,}-character limit")
        self.parts.append(text)
        self.size += len(text)
        return len(text)

    def getvalue(self) -> str:
        return "".join(self.parts)


def execute_kasa(source: str, input_text: str = "", mode: str = "run", *, learner_language: str = "en") -> dict[str, object]:
    """Run or syntax-check source and return JSON-serializable information.

    Each execution creates a fresh interpreter, so variables never leak from
    one Run click into a subsequent run. Input is provided through a fixed
    string stream. Output and execution are bounded.
    """
    result: dict[str, object] = {"ok": False, "output": "", "error": "", "steps": 0, "mode": mode}
    if learner_language not in {"en", "tw"}:
        result["error"] = "Unsupported learner language"
        return result
    if mode not in {"run", "check"}:
        result["error"] = "Unknown execution mode"
        return result
    if len(source) > SOURCE_LIMIT:
        result["error"] = f"Source exceeds the {SOURCE_LIMIT:,}-character limit"
        return result
    if len(input_text) > INPUT_LIMIT:
        result["error"] = f"Input exceeds the {INPUT_LIMIT:,}-character limit"
        return result

    output = LimitedOutput()
    interpreter: Interpreter | None = None
    try:
        program = parse(source, filename="playground.kasa")
        if mode == "run":
            interpreter = Interpreter(
                filename="playground.kasa",
                stdout=output,  # type: ignore[arg-type]
                stdin=StringIO(input_text),
                max_steps=STEP_LIMIT,
                max_call_depth=48,
            )
            interpreter.run(program)
        result["ok"] = True
        result["output"] = output.getvalue()
    except (KasaError, OutputLimitError) as exc:
        result["error"] = str(exc)
        result["output"] = output.getvalue()
        if isinstance(exc, KasaError) and learner_language == "tw":
            hint = learning_hint(exc, language="tw")
            if hint is not None:
                result["learning_hint"] = hint
    finally:
        if interpreter is not None:
            result["steps"] = interpreter.steps
    return result
