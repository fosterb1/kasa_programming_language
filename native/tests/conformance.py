"""Native bytecode VM conformance against Kasa's Python reference.

Run after building: python native/tests/conformance.py build/kasa-native
The Python interpreter is used only by this TEST HARNESS, never by the native executable.
"""
from __future__ import annotations

import io
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from kasa.core import Interpreter, KasaError, parse  # noqa: E402

BINARY = pathlib.Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "build" / "kasa-native"
sys.argv = sys.argv[:1]
REMAINDER_FIXTURES = json.loads(
    (ROOT / "tests" / "conformance_remainder.json").read_text(encoding="utf-8")
)
NUMERIC_COMPARISON_FIXTURES = json.loads(
    (ROOT / "tests" / "conformance_numeric_comparisons.json").read_text(encoding="utf-8")
)
SOURCE_LOCATION_FIXTURES = json.loads(
    (ROOT / "tests" / "conformance_source_locations.json").read_text(encoding="utf-8")
)


CASES = {
    "hello": ('ka "Maakye, Ghana!"', ''),
    "variable": ('ma edin="Ama"\nka "Maakye, "+edin\nka 9', ''),
    "arithmetic": ('ka (2 + 3) * 4\nka -3 + 10\nka 8 % 3\nka 14 / 7', ''),
    "unicode": ('ma ɛdin="Kɔfi"\nma ɔman="Ghana"\nka ɛdin + " - " + ɔman', ''),
    "supplementary_identifier": ('ma 𐐀=3\nka 𐐀', ''),
    "twi_supplementary_identifier": ('ma ɛ𐐀=5\nka ɛ𐐀', ''),
    "boolean": ('ka nokware\nka atoro\nka hwee\nka ɛnyɛ atoro', ''),
    "boolean_short_circuit": ('ka atoro ne (1 / 0 == 0)\nka nokware anaa (1 / 0 == 0)', ''),
    "if_else": ('ma mfe=15\nsɛ mfe>=18 a\nka "Adult"\nanyɛ_saa_a\nka "Young"\nawiei', ''),
    "nested_if": ('sɛ nokware a\nsɛ atoro a\nka 1\nanyɛ_saa_a\nka 2\nawiei\nawiei', ''),
    "while": ('ma n=1\nbere_a n<=5\nka n*n\nma n=n+1\nawiei', ''),
    "repeat": ('mpɛn 3\nka "Kasa"\nawiei\nmpɛn 0\nka "never"\nawiei', ''),
    "continue_break": ('ma n=0\nmpɛn 8\nma n=n+1\nsɛ n==2 a\ntoa_so\nawiei\nsɛ n==5 a\ngyae\nawiei\nka n\nawiei', ''),
    "nested_repeat": ('mpɛn 2\nmpɛn 3\nka "x"\nawiei\nawiei', ''),
    "function": ('dwumadie fa_bi(a,b)\nsanma a+b\nawiei\nka fa_bi(4,6)', ''),
    "recursion": ('dwumadie fact(n)\nsɛ n<=1 a\nsanma 1\nawiei\nsanma n*fact(n-1)\nawiei\nka fact(6)', ''),
    "lexical_scope": ('ma x=10\ndwumadie test()\nma x=20\nka x\nawiei\ntest()\nka x', ''),
    "nested_lists": ('ma a=[10,[20,30]]\nka a[1][0]\nma a[1][1]=99\nka a[1][1]\nka tentɛn(a)', ''),
    "lists": ('ma a=[1,2,3]\nma a[1]=88\nka a[1]\nka tentɛn(a)', ''),
    "converted": ('ka nsɛm(nokware)\nka nsɛm(hwee)\nka nɔma("12")+3\nka tentɛn("Ghana")', ''),
    "input": ('ka "Wo din de sɛn?"\nma edin=bisa()\nka "Akwaaba, "+edin','Akosua\n'),
    "prompt_input": ('ma edin=bisa("Wo din de sɛn? ")\nka "Akwaaba, "+edin', 'Akosua\n'),
    "empty_prompt": ('ka bisa("")', 'Akosua\n'),
    "large_exact_integer_comparison": ('ka 9007199254740992 == 9007199254740993\nka 9007199254740992 < 9007199254740993', ''),
    "comments_crlf": ('# example\r\nka "Hello" # comment\r\n', ''),
    "nested_function": ('dwumadie outer(n)\ndwumadie inner(m)\nsanma m*2\nawiei\nsanma inner(n)\nawiei\nka outer(5)', ''),
}
ERROR_CASES = {
    "name_error": ('ka unknown', "NameError"),
    "zero_division": ('ka 5/0', "ZeroDivisionError"),
    "bool_arithmetic": ('ka nokware+1', "TypeError"),
    "bad_condition": ('sɛ 3 a\nka "x"\nawiei', "TypeError"),
    "invalid_index": ('ka [1][2]', "IndexError"),
    "break_outside_loop": ('gyae', "SyntaxError"),
    "return_outside_function": ('sanma 1', "SyntaxError"),
    "missing_end": ('mpɛn 3\nka "x"', "SyntaxError"),
    "extra_end": ('awiei', "SyntaxError"),
    "unclosed_string": ('ka "hi', "SyntaxError"),
    "type_mismatch": ('ka 1 + "a"', "TypeError"),
    "too_large_integer": ('ka 9223372036854775807 + 1', "ResourceError"),
    "infinite_loop": ('bere_a nokware\nawiei', "ResourceError"),
    "bad_repeat_count": ('mpɛn -1\nka 1\nawiei', "TypeError"),
    "nonboolean_not": ('ka ɛnyɛ 1', "TypeError"),
    "bad_conversion": ('ka nɔma("hello")', "TypeError"),
    "bad_input_prompt_type": ('ka bisa(42)', "TypeError"),
    "bad_input_prompt_arity": ('ka bisa("one", "two")', "TypeError"),
}


def run_native(source: str, input_text: str = "", mode: str = "run") -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as folder:
        name = pathlib.Path(folder) / "test.kasa"
        name.write_text(source, encoding="utf-8")
        return subprocess.run([str(BINARY), mode, str(name)], input=input_text, text=True,
                              capture_output=True, timeout=5, check=False)



def run_native_serialized(source: str, input_text: str = "") -> tuple[
    subprocess.CompletedProcess[str],
    subprocess.CompletedProcess[str] | None,
    subprocess.CompletedProcess[str] | None,
]:
    """Compile Kasa source to KBC1, validate it, then execute it in the native VM.

    All three processes complete before the temporary directory is removed.
    A failing earlier stage is reported; later stages are never falsely executed.
    """
    with tempfile.TemporaryDirectory() as folder:
        source_path = pathlib.Path(folder) / "test.kasa"
        bytecode_path = pathlib.Path(folder) / "test.kbc"
        source_path.write_text(source, encoding="utf-8")
        compiled = subprocess.run(
            [str(BINARY), "compile", str(source_path), "-o", str(bytecode_path)],
            text=True, capture_output=True, timeout=5, check=False,
        )
        if compiled.returncode != 0:
            return compiled, None, None
        checked = subprocess.run(
            [str(BINARY), "check-bytecode", str(bytecode_path)],
            text=True, capture_output=True, timeout=5, check=False,
        )
        if checked.returncode != 0:
            return compiled, checked, None
        executed = subprocess.run(
            [str(BINARY), "run-bytecode", str(bytecode_path)],
            input=input_text, text=True, capture_output=True, timeout=5, check=False,
        )
        return compiled, checked, executed


def run_python(source: str, input_text: str = "") -> str:
    buffer=io.StringIO()
    Interpreter(stdout=buffer,stdin=io.StringIO(input_text)).run(parse(source))
    return buffer.getvalue()


class Conformance(unittest.TestCase):
    def test_native_version(self):
        p=subprocess.run([str(BINARY),"--version"],capture_output=True,text=True,check=True)
        self.assertIn("Kasa Native",p.stdout)

    def test_all_success_cases(self):
        for title,(source,provided) in CASES.items():
            with self.subTest(title=title):
                expected=run_python(source,provided)
                actual=run_native(source,provided)
                self.assertEqual(actual.returncode,0,actual.stderr)
                self.assertEqual(actual.stdout,expected)

    def test_kbc1_success_cases_against_python_reference(self):
        """Verify Python output survives source -> KBC1 -> native execution."""
        for title, (source, supplied_input) in CASES.items():
            with self.subTest(title=title):
                expected = run_python(source, supplied_input)
                compiled, checked, executed = run_native_serialized(source, supplied_input)
                self.assertEqual(compiled.returncode, 0, (title, compiled.stderr))
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, (title, checked.stderr))
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, (title, executed.stderr))
                self.assertEqual(executed.stdout, expected)

    def test_kbc1_shared_remainder_against_python_reference(self):
        for fixture in REMAINDER_FIXTURES["cases"]:
            with self.subTest(name=fixture["name"]):
                expected = fixture["expected_stdout"]
                self.assertEqual(run_python(fixture["source"]), expected)
                compiled, checked, executed = run_native_serialized(fixture["source"])
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_mixed_numeric_comparison_against_python(self):
        for fixture in NUMERIC_COMPARISON_FIXTURES["cases"]:
            with self.subTest(name=fixture["name"]):
                expected=fixture["expected_stdout"]
                self.assertEqual(run_python(fixture["source"]), expected)
                native=run_native(fixture["source"])
                self.assertEqual(native.returncode, 0, native.stderr)
                self.assertEqual(native.stdout, expected)

    def test_mixed_numeric_comparison_in_kbc1(self):
        for fixture in NUMERIC_COMPARISON_FIXTURES["cases"]:
            with self.subTest(name=fixture["name"]):
                expected=fixture["expected_stdout"]
                compiled, checked, executed=run_native_serialized(fixture["source"])
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_decimal_display_source_and_kbc1_against_python(self):
        fixtures = json.loads(
            (ROOT / "tests" / "conformance_decimal_display.json").read_text(encoding="utf-8")
        )["cases"]
        for fixture in fixtures:
            with self.subTest(name=fixture["name"]):
                source = fixture["source"]
                expected = fixture["expected_stdout"]
                self.assertEqual(run_python(source), expected)
                direct = run_native(source)
                self.assertEqual(direct.returncode, 0, direct.stderr)
                self.assertEqual(direct.stdout, expected)
                compiled, checked, executed = run_native_serialized(source)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_kbc1_runtime_error_categories(self):
        # Syntax errors must be rejected at compilation, rather than being
        # serialized. Runtime errors should survive safe KBC1 round-tripping.
        names = (
            "name_error", "zero_division", "bool_arithmetic", "bad_condition",
            "invalid_index", "type_mismatch", "bad_repeat_count",
            "nonboolean_not", "bad_conversion", "bad_input_prompt_type",
            "bad_input_prompt_arity",
        )
        for name in names:
            with self.subTest(name=name):
                source, category = ERROR_CASES[name]
                compiled, checked, executed = run_native_serialized(source)
                self.assertEqual(compiled.returncode, 0, (name, compiled.stderr))
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, (name, checked.stderr))
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 1, (name, executed.stderr))
                self.assertIn(category, executed.stderr)

    def test_kbc1_invalid_source_never_serialized(self):
        # Parsing/lexing errors must fail at compilation, before any .kbc
        # artifact can reach the loader or VM.
        for fixture in SOURCE_LOCATION_FIXTURES["cases"]:
            with self.subTest(name=fixture["name"]):
                compiled, checked, executed = run_native_serialized(fixture["source"])
                self.assertEqual(compiled.returncode, 1, compiled.stderr)
                self.assertIn(fixture["category"], compiled.stderr)
                self.assertIn(
                    f"test.kasa:{fixture['line']}:{fixture['column']}:",
                    compiled.stderr,
                )
                self.assertIsNone(checked)
                self.assertIsNone(executed)

    def test_all_error_cases(self):
        for title,(source,category) in ERROR_CASES.items():
            with self.subTest(title=title):
                actual=run_native(source)
                self.assertEqual(actual.returncode,1,(title,actual.stderr))
                self.assertIn(category,actual.stderr)
                self.assertRegex(actual.stderr,r"test\.kasa:\d+:\d+:")

    def test_shared_remainder_values(self):
        for fixture in REMAINDER_FIXTURES["cases"]:
            with self.subTest(name=fixture["name"]):
                expected=fixture["expected_stdout"]
                self.assertEqual(run_python(fixture["source"]), expected)
                actual=run_native(fixture["source"])
                self.assertEqual(actual.returncode, 0, actual.stderr)
                self.assertEqual(actual.stdout, expected)

    def test_shared_remainder_errors(self):
        for fixture in REMAINDER_FIXTURES["errors"]:
            with self.subTest(name=fixture["name"]):
                with self.assertRaises(KasaError) as err:
                    run_python(fixture["source"])
                self.assertEqual(err.exception.category, fixture["category"])
                actual=run_native(fixture["source"])
                self.assertEqual(actual.returncode, 1, actual.stderr)
                self.assertIn(fixture["category"], actual.stderr)

    def test_unicode_source_coordinates(self):
        for case in SOURCE_LOCATION_FIXTURES["cases"]:
            with self.subTest(name=case["name"]):
                try:
                    parse(case["source"], filename="test.kasa")
                except KasaError as error:
                    self.assertEqual(error.category, case["category"])
                    self.assertEqual((error.token.line, error.token.column),
                                     (case["line"], case["column"]))
                else:
                    self.fail(f"Python accepted invalid source: {case['name']}")
                actual = run_native(case["source"], mode="check")
                self.assertEqual(actual.returncode, 1, actual.stderr)
                location = f"test.kasa:{case['line']}:{case['column']}: {case['category']}:"
                self.assertIn(location, actual.stderr)


    def test_crlf_input_source_and_kbc1(self):
        """Native stdin must normalize CRLF exactly as Python and JS."""
        cases = json.loads(
            (ROOT / "tests" / "conformance_crlf_input.json").read_text(encoding="utf-8")
        )["cases"]
        for case in cases:
            with self.subTest(name=case["name"]):
                source, stdin, expected = case["source"], case["stdin"], case["expected_stdout"]
                self.assertEqual(run_python(source, stdin), expected)
                direct = run_native(source, stdin)
                self.assertEqual(direct.returncode, 0, direct.stderr)
                self.assertEqual(direct.stdout, expected)
                compiled, checked, executed = run_native_serialized(source, stdin)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_native_int64_minimum_source_and_kbc1(self):
        """The signed 64-bit minimum must survive source parsing and KBC1."""
        cases = json.loads(
            (ROOT / "tests" / "conformance_int64_boundary.json").read_text(encoding="utf-8")
        )["cases"]
        for case in cases:
            with self.subTest(name=case["name"]):
                source, expected = case["source"], case["expected_stdout"]
                self.assertEqual(run_python(source), expected)
                direct = run_native(source)
                self.assertEqual(direct.returncode, 0, direct.stderr)
                self.assertEqual(direct.stdout, expected)
                compiled, checked, executed = run_native_serialized(source)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_native_int64_minimum_overflow_stays_guarded(self):
        """An integer lower than int64_min still cannot be represented natively."""
        for source in ('ka -9223372036854775809', 'ka -9223372036854775808 - 1'):
            with self.subTest(source=source):
                direct = run_native(source)
                self.assertNotEqual(direct.returncode, 0)
                self.assertIn(": ResourceError:", direct.stderr)

    def test_numeric_text_conversion_source_and_kbc1(self):
        """Numeric text must use Kasa's ASCII grammar on all runtimes."""
        cases = json.loads(
            (ROOT / "tests" / "conformance_numeric_conversion.json").read_text(encoding="utf-8")
        )["cases"]
        for case in cases:
            with self.subTest(name=case["name"]):
                source = case["source"]
                expected = case.get("expected_stdout")
                if expected is not None:
                    self.assertEqual(run_python(source), expected)
                else:
                    with self.assertRaises(KasaError) as caught:
                        run_python(source)
                    self.assertEqual(caught.exception.category, case["error_category"])
                direct = run_native(source)
                compiled, checked, executed = run_native_serialized(source)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                for execution in (direct, executed):
                    self.assertEqual(execution.returncode == 0, expected is not None, execution.stderr)
                    if expected is not None:
                        self.assertEqual(execution.stdout, expected)
                    else:
                        self.assertIn(f": {case['error_category']}:", execution.stderr)

    def test_native_numeric_text_overflow_is_resource_error(self):
        """Native int64 conversion overflow must not masquerade as invalid syntax."""
        source = 'ka nɔma("9223372036854775808")'
        for execution in (run_native(source), run_native_serialized(source)[2]):
            self.assertIsNotNone(execution)
            self.assertNotEqual(execution.returncode, 0)
            self.assertIn(": ResourceError:", execution.stderr)

    def test_unicode_output_budget_source_and_kbc1(self):
        """Run the same Unicode limits through Python, native source and KBC1."""
        from kasa.core import KasaError

        fixtures = json.loads(
            (ROOT / "tests" / "conformance_output_budget.json").read_text(encoding="utf-8")
        )["cases"]
        for case in fixtures:
            with self.subTest(case=case["name"]):
                source, stdin = case["source"], case["stdin"]
                output = io.StringIO()
                try:
                    Interpreter(stdout=output, stdin=io.StringIO(stdin)).run(parse(source))
                except KasaError as error:
                    self.assertFalse(case["expected_ok"])
                    self.assertEqual(error.category, case["error_category"])
                else:
                    self.assertTrue(case["expected_ok"])
                self.assertEqual(len(output.getvalue()), case["expected_stdout_characters"])

                direct = run_native(source, stdin)
                compiled, checked, executed = run_native_serialized(source, stdin)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)

                for result in (direct, executed):
                    self.assertEqual(result.returncode == 0, case["expected_ok"], result.stderr)
                    self.assertEqual(len(result.stdout), case["expected_stdout_characters"])
                    if not case["expected_ok"]:
                        self.assertIn(f": {case['error_category']}:", result.stderr)

    def test_amount_reconciliation_reference_and_kbc1(self):
        """Amount-only lesson must match Python in native source and serialized KBC1."""
        corpus = json.loads(
            (ROOT / "tests" / "conformance_reconciliation.json").read_text(encoding="utf-8")
        )["cases"]
        template = (ROOT / "examples/bank_reconciliation_matching.kasa").read_text(encoding="utf-8")
        for case in corpus:
            with self.subTest(name=case["name"]):
                source = template
                for label, original in (
                    ("bank", "[5000, 7000, 5000, 12000]"),
                    ("ledger", "[5000, 5000, 9000, 7000]"),
                ):
                    before = f"ma {label} = {original}"
                    self.assertEqual(source.count(before), 1)
                    source = source.replace(
                        before, f"ma {label} = [" + ", ".join(map(str, case[label])) + "]"
                    )
                expected = case["expected_stdout"]
                self.assertEqual(run_python(source), expected)
                direct = run_native(source)
                self.assertEqual(direct.returncode, 0, direct.stderr)
                self.assertEqual(direct.stdout, expected)
                compiled, checked, executed = run_native_serialized(source)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                self.assertIsNotNone(checked)
                self.assertEqual(checked.returncode, 0, checked.stderr)
                self.assertIsNotNone(executed)
                self.assertEqual(executed.returncode, 0, executed.stderr)
                self.assertEqual(executed.stdout, expected)

    def test_syntax_check_never_executes(self):
        p=run_native('ka 1/0\nka "not executed"','', 'check')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(p.stdout,"")

    def test_disassembly_is_bytecode_not_python(self):
        p=run_native('ka 2 + 3 * 4','', 'disasm')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("CONST",p.stdout)
        self.assertIn("MUL",p.stdout)
        self.assertIn("ADD",p.stdout)
        self.assertIn("PRINT",p.stdout)
        self.assertNotIn("import",p.stdout)

    def test_bundled_kasa_examples(self):
        for file in sorted([*(ROOT/'examples').glob('*.kasa'), *(ROOT/'native'/'examples').glob('*.kasa')]):
            with self.subTest(example=file.name):
                src=file.read_text(encoding='utf-8')
                p=run_native(src)
                self.assertEqual(p.returncode,0,(file.name,p.stderr))
                self.assertEqual(p.stdout,run_python(src))

    def test_no_python_runtime_dependency_in_native_source(self):
        content=(ROOT/'native'/'src'/'main.cpp').read_text()
        self.assertNotIn('Py_Initialize',content)
        self.assertNotIn('system(',content)
        self.assertNotIn('popen(',content)
        self.assertNotIn('eval(',content)


if __name__=='__main__':
    unittest.main(verbosity=2)
