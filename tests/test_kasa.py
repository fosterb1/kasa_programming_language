"""Interpreter regressions and acceptance tests for the 0.1 milestone."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

import pytest

from kasa import Interpreter, KasaError, parse, tokenize

ROOT = Path(__file__).resolve().parents[1]


def run(source: str, stdin: str = "", limit: int = 10_000) -> str:
    out = io.StringIO()
    Interpreter(stdout=out, stdin=io.StringIO(stdin), max_steps=limit).run(parse(source))
    return out.getvalue()


@pytest.mark.parametrize(("source", "expected"), [
    ('ka "Maakye, Ghana!"', "Maakye, Ghana!\n"),
    ('ka 42\nka nokware\nka atoro\nka hwee', "42\nnokware\natoro\nhwee\n"),
    ('ka 2 + 3 * 4\nka (2 + 3) * 4', "14\n20\n"),
    ('ma x = 10\nma x = x + 5\nka x', "15\n"),
    ('ka 12 / 4\nka 7 % 3', "3.0\n1\n"),
    ('ka ɛnyɛ nokware\nka nokware ne atoro\nka nokware anaa atoro', "atoro\natoro\nnokware\n"),
    ('ka atoro ne (1 / 0 == 0)\nka nokware anaa (1 / 0 == 0)', "atoro\nnokware\n"),
    ('sɛ 5 > 2 a\n  ka "yes"\nanyɛ_saa_a\n  ka "no"\nawiei', "yes\n"),
    ('mpɛn 3\n ka "x"\nawiei', "x\nx\nx\n"),
    ('ma n = 1\nbere_a n <= 3\nka n\nma n = n + 1\nawiei', "1\n2\n3\n"),
    ('dwumadie fa_bi(a,b)\n sanma a+b\nawiei\nka fa_bi(2,7)', "9\n"),
    ('ma xs=[10,20,30]\nka xs[0]\nma xs[1]=99\nka xs[1]\nka tentɛn(xs)', "10\n99\n3\n"),
    ('ma ɛdin="Ama"\nma ɔman="Ghana"\nka ɛdin+" - "+ɔman', "Ama - Ghana\n"),
    ('ka nɔma("12") + 3\nka nsɛm(nokware)', "15\nnokware\n"),
    ('ka bisa()', 'Ama\n'),
    ('ma edin = bisa("Wo din de sɛn? ")\nka "Akwaaba, " + edin', 'Wo din de sɛn? Akwaaba, Ama\n'),
    ('ka bisa("")', 'Ama\n'),
    ('ka 1 # inline comment\n# line\nka "# is text"', '1\n# is text\n'),
    ('ka "a\\nb"', 'a\nb\n'),
    ('ma a = 1\nka a', '1\n'),
    ('ma xs=[1,[2,3]]\nka xs[1][0]', '2\n'),
    ('ka 1 == nokware\nka [1] == [nokware]', 'atoro\natoro\n'),
    ('ka 1 + -2', '-1\n'),
])
def test_programs(source: str, expected: str) -> None:
    assert run(source, stdin="Ama\n") == expected


def test_scope_and_recursion() -> None:
    source = '''ma x = 10
    dwumadie test()
        ma x = 20
        ka x
    awiei
    test()
    ka x
    dwumadie fact(n)
        sɛ n <= 1 a
            sanma 1
        awiei
        sanma n * fact(n - 1)
    awiei
    ka fact(5)
    '''
    assert run(source) == "20\n10\n120\n"


def test_break_continue_nested() -> None:
    source = '''ma count=0
    mpɛn 5
        ma count=count+1
        sɛ count == 2 a
            toa_so
        awiei
        sɛ count == 4 a
            gyae
        awiei
        ka count
    awiei'''
    assert run(source) == "1\n3\n"


@pytest.mark.parametrize("source,category", [
    ('ka missing', 'NameError'),
    ('ka 1 / 0', 'ZeroDivisionError'),
    ('ka 1 + "a"', 'TypeError'),
    ('ka nokware + 1', 'TypeError'),
    ('ka 4 % 1.2', 'TypeError'),
    ('sɛ 1 a\nka "x"\nawiei', 'TypeError'),
    ('mpɛn -1\nka 1\nawiei', 'TypeError'),
    ('mpɛn 1.5\nka 1\nawiei', 'TypeError'),
    ('ka [1][2]', 'IndexError'),
    ('ka [1][atoro]', 'TypeError'),
    ('ka nɔma("nah")', 'TypeError'),
    ('gyae', 'SyntaxError'),
    ('toa_so', 'SyntaxError'),
    ('sanma 3', 'SyntaxError'),
    ('ka foo(2)', 'NameError'),
    ('ka tentɛn(1)', 'TypeError'),
    ('ka bisa(1)', 'TypeError'),
    ('ka bisa("One", "Two")', 'TypeError'),
    ('ka "unterminated', 'SyntaxError'),
    ('ka 5 & 3', 'SyntaxError'),
    ('sɛ nokware a\n  ka 1', 'SyntaxError'),
    ('awiei', 'SyntaxError'),
    ('anyɛ_saa_a', 'SyntaxError'),
    ('ka 1 < 2 < 3', 'SyntaxError'),
    ('ma 1 = 2', 'SyntaxError'),
    ('ma [1,2][0]=8', 'SyntaxError'),
    ('dwumadie f(a,a)\nka a\nawiei', 'SyntaxError'),
])
def test_errors(source: str, category: str) -> None:
    with pytest.raises(KasaError) as info:
        run(source)
    assert info.value.category == category
    assert "<input>:" in str(info.value)


def test_infinite_loop_is_bounded() -> None:
    with pytest.raises(KasaError, match="Execution limit"):
        run("bere_a nokware\nawiei", limit=50)


def test_call_depth_is_bounded() -> None:
    source = "dwumadie f()\n sanma f()\nawiei\nka f()"
    with pytest.raises(KasaError, match="call depth"):
        run(source)


def test_lexing_unicode_locations_and_crlf() -> None:
    tokens = tokenize('ma ɛdin = "Kɔfi"\r\nka ɛdin\r\n')
    assert [t.kind for t in tokens[:5]] == ["ASSIGN", "NAME", "=", "STRING", "NEWLINE"]
    assert tokens[5].line == 2 and tokens[5].column == 1


def test_check_only_parses_not_executes() -> None:
    path = ROOT / "examples" / "hello.kasa"
    cmd = [sys.executable, "-m", "kasa", "check", str(path)]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0
    assert result.stdout == ""


def test_cli_run_and_invalid_file() -> None:
    cmd = [sys.executable, "-m", "kasa", "run", str(ROOT / "examples" / "hello.kasa")]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    assert result.returncode == 0 and result.stdout == "Maakye, Ghana!\n"
    missing = subprocess.run([sys.executable, "-m", "kasa", "run", "missing.kasa"], capture_output=True, text=True, check=False)
    assert missing.returncode == 2 and "cannot read" in missing.stderr


def test_all_examples() -> None:
    expected = {
        "hello.kasa": "Maakye, Ghana!\n",
        "conditions.kasa": "Maakye, Ama\n",
        "functions.kasa": "10\n",
        "loops.kasa": "1\n2\n3\nMeda wo ase\nMeda wo ase\n",
        "lists.kasa": "99\n3\n",
    }
    for name, output in expected.items():
        assert run((ROOT / "examples" / name).read_text(encoding="utf-8")) == output


def test_runtime_keeps_global_environment_between_repl_inputs() -> None:
    out = io.StringIO()
    runtime = Interpreter(stdout=out)
    runtime.run(parse("ma ɛdin = 'Ama'".replace("'", '"')))
    runtime.run(parse("ka ɛdin"))
    assert out.getvalue() == "Ama\n"


def test_oversized_integer_is_bounded() -> None:
    source = "ma x=1000000000000000000000000000000000000000\nmpɛn 100\n  ma x=x*x\nawiei"
    with pytest.raises(KasaError, match="Integer exceeds"):
        run(source)


def test_repl_multiline_function() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "kasa", "repl"],
        input="dwumadie b()\nka 9\nawiei\nb()\nquit\n",
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0
    assert "9\n" in completed.stdout
