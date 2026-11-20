"""Deterministic negative-input corpus for G0.5 module compilation.

No fuzz randomness, external packages, native build, or untrusted execution:
every specimen must be rejected before publication of a .kbc file.
"""
from __future__ import annotations

from pathlib import Path
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from compile_g05_modules import CompileError, MAX_INPUT_BYTES, compile_modules
    from link_kasa_modules_hygienic import HygienicLinkError
    from validate_kasa_catalog import CatalogError
finally:
    sys.path.remove(str(ROOT / "scripts"))

from kasa.core import KasaError


CASES: tuple[tuple[str, bytes], ...] = (
    ("invalid-utf8", b"fa math firi stdlib: m\nka \xff\n"),
    ("unknown-module", b"fa untrusted firi stdlib: u\nka u.f(2)\n"),
    ("private-export", b"fa math firi stdlib: m\nka m.not_exported(2)\n"),
    ("late-import", b"ka 2\nfa math firi stdlib: m\n"),
    ("duplicate-import", b"fa math firi stdlib: a\nfa math firi stdlib: b\nka 2\n"),
    ("unknown-import-origin", b"fa math firi external: m\nka m.kasa_abs(-1)\n"),
    ("reserved-internal-symbol", b"fa math firi stdlib: m\nma __kasa_g05_test = 4\n"),
    ("broken-expression", b"fa math firi stdlib: m\nka m.kasa_sum(\n"),
    ("broken-function", b"fa math firi stdlib: m\ndwumadie x(a)\nka a\n"),
    ("oversized-bytes", b"#" * (MAX_INPUT_BYTES + 1)),
    ("unicode-unknown-module", "fa ɔdɔ firi stdlib: d\nka 1\n".encode("utf-8")),
)


@pytest.mark.parametrize("label,payload", CASES, ids=[label for label, _ in CASES])
def test_rejected_inputs_publish_no_bytecode(tmp_path, label, payload):
    application = tmp_path / "input.kasa"
    application.write_bytes(payload)
    output = ROOT / "build" / "g05-compiled" / ("negative-" + uuid.uuid4().hex + ".kbc")
    try:
        # This corpus tests refusal and non-publication, not diagnostic category
        # text or parser-specific messages.
        with pytest.raises((CompileError, KasaError, HygienicLinkError,
                            CatalogError, UnicodeError)):
            compile_modules(application, output)
        assert not output.exists(), f"{label}: invalid source published KBC1"
    finally:
        output.unlink(missing_ok=True)


def test_corpus_is_deterministic_and_bounded():
    assert len(CASES) >= 10
    names = [name for name, _ in CASES]
    assert len(names) == len(set(names))
    assert all(isinstance(data, bytes) and len(data) > 0 for _, data in CASES)
    assert len(CASES[-2][1]) == MAX_INPUT_BYTES + 1
