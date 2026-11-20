"""Lexer, recursive-descent parser and bounded tree-walking interpreter for Kasa."""

from __future__ import annotations

import math
import re
import sys
from dataclasses import dataclass, field
from typing import TextIO

KEYWORDS = {
    "ka": "PRINT", "ma": "ASSIGN", "sɛ": "IF", "anyɛ_saa_a": "ELSE",
    "mpɛn": "REPEAT", "bere_a": "WHILE", "dwumadie": "FUNCTION",
    "sanma": "RETURN", "awiei": "END", "nokware": "TRUE",
    "atoro": "FALSE", "hwee": "NONE", "ne": "AND", "anaa": "OR",
    "ɛnyɛ": "NOT", "gyae": "BREAK", "toa_so": "CONTINUE",
}
OPERATORS = {"==", "!=", "<=", ">=", "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", "[", "]", ","}
BINDING_POWER = {"OR": 10, "AND": 20, "==": 30, "!=": 30, "<": 40, "<=": 40, ">": 40, ">=": 40,
                 "+": 50, "-": 50, "*": 60, "/": 60, "%": 60}
COMPARISONS = {"<", "<=", ">", ">=", "==", "!="}
# Auditable vocabulary: see docs/keyword_evidence.json before adding Twi built-ins.
BUILTIN_NAMES = frozenset({"bisa", "tentɛn", "nɔma", "nsɛm"})
MAX_OUTPUT_CHARACTERS = 64_000
MAX_CONTAINER_SIZE = 10_000
MAX_STRING_SIZE = 1_000_000


@dataclass(frozen=True)
class Token:
    kind: str
    text: str
    line: int
    column: int


class KasaError(Exception):
    """A diagnosed source error, with a useful location and category."""

    def __init__(self, category: str, message: str, token: Token, filename: str):
        self.category = category
        self.message = message
        self.token = token
        self.filename = filename
        super().__init__(f"{filename}:{token.line}:{token.column}: {category}: {message}")


def tokenize(source: str, filename: str = "<input>", *, experimental_modules: bool = False) -> list[Token]:
    """Tokenize Unicode Kasa input without executing arbitrary host code."""
    source = source.replace("\r\n", "\n").replace("\r", "\n")
    result: list[Token] = []
    i = 0
    line = col = 1

    def advance() -> str:
        nonlocal i, line, col
        character = source[i]
        i += 1
        if character == "\n":
            line += 1
            col = 1
        else:
            col += 1
        return character

    while i < len(source):
        ch = source[i]
        if ch in " \t":
            advance()
            continue
        start_line, start_col = line, col
        if ch == "#":
            while i < len(source) and source[i] != "\n":
                advance()
            continue
        if ch == "\n":
            advance()
            result.append(Token("NEWLINE", "\n", start_line, start_col))
            continue
        if ch == '"':
            advance()
            text = []
            while i < len(source) and source[i] not in ('"', "\n"):
                c = advance()
                if c == "\\":
                    if i >= len(source) or source[i] == "\n":
                        raise KasaError("SyntaxError", "Unterminated string escape", Token("STRING", "", start_line, start_col), filename)
                    escaped = advance()
                    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"'}
                    if escaped not in escapes:
                        raise KasaError("SyntaxError", f"Unsupported escape \\{escaped}", Token("STRING", "", start_line, start_col), filename)
                    c = escapes[escaped]
                text.append(c)
            if i >= len(source) or source[i] != '"':
                raise KasaError("SyntaxError", "Unterminated string", Token("STRING", "", start_line, start_col), filename)
            advance()
            result.append(Token("STRING", "".join(text), start_line, start_col))
            continue
        if ch.isdigit() and ch.isascii():
            digits = []
            while i < len(source) and source[i] in "0123456789":
                digits.append(advance())
            kind = "INTEGER"
            if i + 1 < len(source) and source[i] == "." and source[i + 1] in "0123456789":
                kind = "DECIMAL"
                digits.append(advance())
                while i < len(source) and source[i] in "0123456789":
                    digits.append(advance())
            if len(digits) > 1000:
                raise KasaError("SyntaxError", "Numeric literal is too long", Token(kind, "", start_line, start_col), filename)
            result.append(Token(kind, "".join(digits), start_line, start_col))
            continue
        if ch.isalpha() or ch == "_":
            chars = []
            while i < len(source) and (source[i].isalnum() or source[i] == "_"):
                chars.append(advance())
            word = "".join(chars)
            if not word.isidentifier():
                raise KasaError("SyntaxError", f"Invalid identifier '{word}'", Token("NAME", word, start_line, start_col), filename)
            result.append(Token(KEYWORDS.get(word, "NAME"), word, start_line, start_col))
            continue
        pair = source[i:i + 2]
        if len(pair) == 2 and pair in OPERATORS:
            advance()
            advance()
            result.append(Token(pair, pair, start_line, start_col))
            continue
        if ch in OPERATORS or (experimental_modules and ch in "@:."):
            advance()
            result.append(Token(ch, ch, start_line, start_col))
            continue
        raise KasaError("SyntaxError", f"Unexpected character {ch!r}", Token("INVALID", ch, start_line, start_col), filename)
    result.append(Token("EOF", "", line, col))
    return result


@dataclass(frozen=True)
class Node:
    kind: str
    token: Token
    value: object = None
    children: tuple = ()


class Parser:
    """Recursive descent for statements; Pratt parsing for expressions."""

    def __init__(self, tokens: list[Token], filename: str = "<input>", *, experimental_modules: bool = False):
        self.experimental_modules = experimental_modules
        self.tokens = tokens
        self.filename = filename
        self.pos = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.pos]

    def match(self, kind: str) -> Token | None:
        if self.current.kind == kind:
            tok = self.current
            self.pos += 1
            return tok
        return None

    def expect(self, kind: str, description: str | None = None) -> Token:
        token = self.match(kind)
        if token is None:
            self.fail(f"Expected {description or kind}, found {self.current.text or 'end of file'}")
        return token

    def fail(self, message: str, at: Token | None = None) -> None:
        raise KasaError("SyntaxError", message, at or self.current, self.filename)

    def newlines(self) -> None:
        while self.match("NEWLINE"):
            pass

    def end_line(self) -> None:
        if self.current.kind == "EOF":
            return
        self.expect("NEWLINE", "a new line")

    def parse(self) -> list[Node]:
        body = self.block({"EOF"})
        self.expect("EOF")
        return body

    def block(self, stop: set[str]) -> list[Node]:
        body: list[Node] = []
        self.newlines()
        while self.current.kind not in stop:
            if self.current.kind == "EOF":
                self.fail("Missing 'awiei' before end of file")
            if self.current.kind in {"END", "ELSE"}:
                self.fail(f"Unexpected block delimiter '{self.current.text}'")
            body.append(self.statement())
            self.newlines()
        return body

    def statement(self) -> Node:
        tok = self.current
        # Punctuation-only opt-in prototype; no unreviewed Twi keyword.
        if self.experimental_modules and self.match("@"):
            module = self.expect("NAME", "catalog module ID")
            self.expect(":", "':' between module and alias")
            # Reserved Kasa keywords tokenize to their own kinds, so reject
            # them explicitly here instead of reporting a generic missing NAME.
            if self.current.kind in set(KEYWORDS.values()):
                self.fail("Reserved module alias: " + self.current.text, self.current)
            alias = self.expect("NAME", "module alias")
            self.end_line()
            return Node("module_import", tok, value=(module.text, alias.text))
        if self.match("PRINT"):
            expr = self.expression()
            self.end_line()
            return Node("print", tok, children=(expr,))
        if self.match("ASSIGN"):
            target = self.expression()
            if target.kind not in {"name", "index"} or (target.kind == "index" and not self.assignable_index(target)):
                self.fail("The target of 'ma' must be a variable or list index", target.token)
            self.expect("=", "'=' in an assignment")
            expr = self.expression()
            self.end_line()
            return Node("assign", tok, children=(target, expr))
        if self.match("IF"):
            cond = self.expression()
            marker = self.expect("NAME", "'a' after the condition")
            if marker.text != "a":
                self.fail("Expected 'a' after the condition", marker)
            self.end_line()
            yes = self.block({"ELSE", "END"})
            no: list[Node] = []
            if self.match("ELSE"):
                self.end_line()
                no = self.block({"END"})
            self.expect("END", "'awiei' to close the conditional")
            self.end_line()
            return Node("if", tok, children=(cond, yes, no))
        if self.match("REPEAT"):
            count = self.expression()
            self.end_line()
            body = self.block({"END"})
            self.expect("END", "'awiei' to close the repetition")
            self.end_line()
            return Node("repeat", tok, children=(count, body))
        if self.match("WHILE"):
            cond = self.expression()
            self.end_line()
            body = self.block({"END"})
            self.expect("END", "'awiei' to close the loop")
            self.end_line()
            return Node("while", tok, children=(cond, body))
        if self.match("FUNCTION"):
            name = self.expect("NAME", "a function name")
            self.expect("(")
            params: list[str] = []
            if self.current.kind != ")":
                while True:
                    param = self.expect("NAME", "a parameter name").text
                    if param in params:
                        self.fail(f"Duplicate parameter '{param}'")
                    params.append(param)
                    if not self.match(","):
                        break
            self.expect(")")
            self.end_line()
            body = self.block({"END"})
            self.expect("END", "'awiei' to close the function")
            self.end_line()
            return Node("function", tok, value=(name.text, params), children=(body,))
        if self.match("RETURN"):
            expr = None if self.current.kind in ("NEWLINE", "EOF") else self.expression()
            self.end_line()
            return Node("return", tok, children=(expr,))
        if self.match("BREAK"):
            self.end_line()
            return Node("break", tok)
        if self.match("CONTINUE"):
            self.end_line()
            return Node("continue", tok)
        expr = self.expression()
        self.end_line()
        return Node("expression", tok, children=(expr,))

    def assignable_index(self, node: Node) -> bool:
        while node.kind == "index":
            node = node.children[0]
        return node.kind == "name"

    def expression(self, min_bp: int = 0) -> Node:
        tok = self.current
        if self.match("-"):
            left = Node("unary", tok, value="-", children=(self.expression(70),))
        elif self.match("NOT"):
            left = Node("unary", tok, value="NOT", children=(self.expression(70),))
        elif self.match("INTEGER"):
            left = Node("literal", tok, value=int(tok.text))
        elif self.match("DECIMAL"):
            val = float(tok.text)
            if not math.isfinite(val):
                self.fail("Numeric literal exceeds the supported range", tok)
            left = Node("literal", tok, value=val)
        elif self.match("STRING"):
            left = Node("literal", tok, value=tok.text)
        elif self.match("TRUE"):
            left = Node("literal", tok, value=True)
        elif self.match("FALSE"):
            left = Node("literal", tok, value=False)
        elif self.match("NONE"):
            left = Node("literal", tok, value=None)
        elif self.match("NAME"):
            left = Node("name", tok, value=tok.text)
        elif self.match("("):
            left = self.expression()
            self.expect(")", "')'")
        elif self.match("["):
            items: list[Node] = []
            if self.current.kind != "]":
                while True:
                    items.append(self.expression())
                    if not self.match(","):
                        break
            self.expect("]", "']'")
            left = Node("list", tok, children=tuple(items))
        else:
            self.fail("Expected a value or expression")

        while True:
            tok = self.current
            if self.experimental_modules and tok.kind == "." and 80 >= min_bp:
                if left.kind != "name":
                    self.fail("Only a module alias may precede '.'", tok)
                self.pos += 1
                member = self.expect("NAME", "an exported function name")
                left = Node("module_member", tok, value=member.text, children=(left,))
                continue
            if tok.kind == "(" and 80 >= min_bp:
                self.pos += 1
                args: list[Node] = []
                if self.current.kind != ")":
                    while True:
                        args.append(self.expression())
                        if not self.match(","):
                            break
                self.expect(")", "')' after arguments")
                left = Node("call", tok, children=(left, tuple(args)))
                continue
            if tok.kind == "[" and 80 >= min_bp:
                self.pos += 1
                index = self.expression()
                self.expect("]", "']' after the index")
                left = Node("index", tok, children=(left, index))
                continue
            bp = BINDING_POWER.get(tok.kind, -1)
            if bp < min_bp:
                break
            if tok.kind in COMPARISONS and left.kind == "binary" and left.value in COMPARISONS:
                self.fail("Comparison chaining is not supported; use 'ne'", tok)
            self.pos += 1
            right = self.expression(bp + 1)
            left = Node("binary", tok, value=tok.kind, children=(left, right))
        return left


def parse(source: str, filename: str = "<input>", *, experimental_modules: bool = False) -> list[Node]:
    """Parse source without executing any statements.

    Experimental module punctuation is opt-in and not Kasa stable syntax.
    """
    return Parser(tokenize(source, filename, experimental_modules=experimental_modules),
                  filename, experimental_modules=experimental_modules).parse()


@dataclass
class Environment:
    values: dict[str, object] = field(default_factory=dict)
    parent: Environment | None = None

    def get(self, name: str) -> tuple[bool, object]:
        if name in self.values:
            return True, self.values[name]
        if self.parent is not None:
            return self.parent.get(name)
        return False, None


@dataclass(frozen=True)
class UserFunction:
    name: str
    parameters: tuple[str, ...]
    body: list[Node]
    closure: Environment


@dataclass(frozen=True)
class Builtin:
    name: str


class ReturnSignal(Exception):
    def __init__(self, value: object):
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


def display(value: object) -> str:
    """Format Kasa values without leaking host-language representations."""
    if value is None:
        return "hwee"
    if value is True:
        return "nokware"
    if value is False:
        return "atoro"
    if isinstance(value, list):
        return "[" + ", ".join(repr(v) if isinstance(v, str) else display(v) for v in value) + "]"
    if isinstance(value, UserFunction):
        return f"<dwumadie {value.name}>"
    if isinstance(value, Builtin):
        return f"<built-in {value.name}>"
    return str(value)


def equal(a: object, b: object) -> bool:
    if type(a) in (int, float) and type(b) in (int, float):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


class Interpreter:
    """Kasa runtime with lexical scopes and bounded execution."""

    def __init__(self, filename: str = "<input>", stdout: TextIO | None = None,
                 stdin: TextIO | None = None, max_steps: int = 100_000, max_call_depth: int = 64):
        self.filename = filename
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stdin = stdin if stdin is not None else sys.stdin
        self.globals = Environment()
        self.max_steps = max_steps
        self.max_call_depth = max_call_depth
        self.steps = 0
        self.output_characters = 0
        self.call_depth = 0
        self.loop_depth = 0

    def error(self, token: Token, category: str, message: str) -> None:
        raise KasaError(category, message, token, self.filename)

    def tick(self, token: Token) -> None:
        self.steps += 1
        if self.steps > self.max_steps:
            self.error(token, "ResourceError", f"Execution limit ({self.max_steps} steps) exceeded")

    def run(self, program: list[Node], filename: str | None = None) -> None:
        if filename is not None:
            self.filename = filename
        self.steps = 0
        self.output_characters = 0
        self.execute_block(program, self.globals)

    def write_output(self, text: str, token: Token, *, flush: bool = False) -> None:
        # Kasa output limits are Unicode code points, including newlines.
        # Check before writing, so a failed operation emits no partial text.
        length = len(text)
        if length > MAX_OUTPUT_CHARACTERS - self.output_characters:
            self.error(token, "ResourceError", "Output exceeded the 64,000-character limit")
        self.stdout.write(text)
        self.output_characters += length
        if flush:
            self.stdout.flush()

    def execute_block(self, body: list[Node], env: Environment) -> None:
        for stmt in body:
            self.execute(stmt, env)

    def strict_boolean(self, value: object, token: Token) -> bool:
        if type(value) is not bool:
            self.error(token, "TypeError", "Condition must be 'nokware' or 'atoro'")
        return value

    def require_number(self, value: object, token: Token) -> int | float:
        if type(value) not in (int, float):
            self.error(token, "TypeError", "Expected a number (not text or a Boolean)")
        return value

    def check_allocation(self, value: object, token: Token) -> object:
        if isinstance(value, (str, list)) and len(value) > (MAX_STRING_SIZE if isinstance(value, str) else MAX_CONTAINER_SIZE):
            self.error(token, "ResourceError", "Value exceeds the size limit")
        if type(value) is int and value.bit_length() > 16384:
            self.error(token, "ResourceError", "Integer exceeds supported size limit")
        if type(value) is float and not math.isfinite(value):
            self.error(token, "ResourceError", "Numeric result exceeds supported range")
        return value

    def execute(self, stmt: Node, env: Environment) -> None:
        self.tick(stmt.token)
        kind = stmt.kind
        if kind == "print":
            self.write_output(display(self.evaluate(stmt.children[0], env)) + "\n", stmt.token)
        elif kind == "assign":
            target, expr = stmt.children
            value = self.evaluate(expr, env)
            if target.kind == "name":
                env.values[target.value] = value
            else:
                collection = self.evaluate(target.children[0], env)
                index = self.evaluate(target.children[1], env)
                self.valid_index(collection, index, target.token)
                collection[index] = value
        elif kind == "if":
            condition, yes, no = stmt.children
            branch = yes if self.strict_boolean(self.evaluate(condition, env), stmt.token) else no
            self.execute_block(branch, env)
        elif kind == "repeat":
            count_expr, body = stmt.children
            count = self.evaluate(count_expr, env)
            if type(count) is not int or count < 0:
                self.error(stmt.token, "TypeError", "'mpɛn' requires a non-negative integer count")
            self.loop_depth += 1
            try:
                for _ in range(count):
                    self.tick(stmt.token)
                    try:
                        self.execute_block(body, env)
                    except ContinueSignal:
                        continue
                    except BreakSignal:
                        break
            finally:
                self.loop_depth -= 1
        elif kind == "while":
            condition, body = stmt.children
            self.loop_depth += 1
            try:
                while self.strict_boolean(self.evaluate(condition, env), stmt.token):
                    try:
                        self.execute_block(body, env)
                    except ContinueSignal:
                        continue
                    except BreakSignal:
                        break
            finally:
                self.loop_depth -= 1
        elif kind == "function":
            name, params = stmt.value
            env.values[name] = UserFunction(name, tuple(params), stmt.children[0], env)
        elif kind == "return":
            if self.call_depth == 0:
                self.error(stmt.token, "SyntaxError", "'sanma' can only appear inside a function")
            raise ReturnSignal(self.evaluate(stmt.children[0], env) if stmt.children[0] is not None else None)
        elif kind == "break":
            if self.loop_depth == 0:
                self.error(stmt.token, "SyntaxError", "'gyae' can only appear inside a loop")
            raise BreakSignal()
        elif kind == "continue":
            if self.loop_depth == 0:
                self.error(stmt.token, "SyntaxError", "'toa_so' can only appear inside a loop")
            raise ContinueSignal()
        elif kind == "expression":
            self.evaluate(stmt.children[0], env)
        else:
            self.error(stmt.token, "RuntimeError", "Unsupported statement")

    def valid_index(self, collection: object, index: object, token: Token) -> None:
        if not isinstance(collection, list):
            self.error(token, "TypeError", "Indexing requires a list")
        if type(index) is not int:
            self.error(token, "TypeError", "List index must be an integer")
        if not 0 <= index < len(collection):
            self.error(token, "IndexError", "List index is outside its range")

    def evaluate(self, expr: Node, env: Environment) -> object:
        self.tick(expr.token)
        kind = expr.kind
        if kind == "literal":
            return self.check_allocation(expr.value, expr.token)
        if kind == "name":
            present, value = env.get(expr.value)
            if present:
                return value
            if expr.value in BUILTIN_NAMES:
                return Builtin(expr.value)
            self.error(expr.token, "NameError", f"Unknown name '{expr.value}'")
        if kind == "list":
            if len(expr.children) > MAX_CONTAINER_SIZE:
                self.error(expr.token, "ResourceError", "List is too large")
            return [self.evaluate(item, env) for item in expr.children]
        if kind == "index":
            collection = self.evaluate(expr.children[0], env)
            index = self.evaluate(expr.children[1], env)
            self.valid_index(collection, index, expr.token)
            return collection[index]
        if kind == "unary":
            value = self.evaluate(expr.children[0], env)
            if expr.value == "NOT":
                return not self.strict_boolean(value, expr.token)
            return self.check_allocation(-self.require_number(value, expr.token), expr.token)
        if kind == "binary":
            left_expr, right_expr = expr.children
            left = self.evaluate(left_expr, env)
            op = expr.value
            if op == "AND":
                if not self.strict_boolean(left, expr.token):
                    return False
                return self.strict_boolean(self.evaluate(right_expr, env), expr.token)
            if op == "OR":
                if self.strict_boolean(left, expr.token):
                    return True
                return self.strict_boolean(self.evaluate(right_expr, env), expr.token)
            right = self.evaluate(right_expr, env)
            if op in ("==", "!="):
                answer = equal(left, right)
                return answer if op == "==" else not answer
            if op == "+" and isinstance(left, str) and isinstance(right, str):
                return self.check_allocation(left + right, expr.token)
            a = self.require_number(left, expr.token)
            b = self.require_number(right, expr.token)
            if op in ("<", "<=", ">", ">="):
                return {"<": lambda: a < b, "<=": lambda: a <= b, ">": lambda: a > b, ">=": lambda: a >= b}[op]()
            if op in ("/", "%") and b == 0:
                self.error(expr.token, "ZeroDivisionError", "Cannot divide by zero")
            if op == "%" and (type(a) is not int or type(b) is not int):
                self.error(expr.token, "TypeError", "Remainder requires two integers")
            try:
                answer = {"+": lambda: a + b, "-": lambda: a - b, "*": lambda: a * b,
                          "/": lambda: a / b, "%": lambda: a % b}[op]()
            except (OverflowError, ValueError):
                self.error(expr.token, "ResourceError", "Numeric operation exceeded supported range")
            return self.check_allocation(answer, expr.token)
        if kind == "call":
            function_expr, arg_exprs = expr.children
            callee = self.evaluate(function_expr, env)
            args = [self.evaluate(arg, env) for arg in arg_exprs]
            if isinstance(callee, Builtin):
                return self.call_builtin(callee.name, args, expr.token)
            if not isinstance(callee, UserFunction):
                self.error(expr.token, "TypeError", "This value cannot be called as a function")
            if len(args) != len(callee.parameters):
                self.error(expr.token, "TypeError", f"'{callee.name}' expects {len(callee.parameters)} arguments, got {len(args)}")
            if self.call_depth >= self.max_call_depth:
                self.error(expr.token, "ResourceError", "Function call depth exceeded")
            local = Environment(dict(zip(callee.parameters, args)), callee.closure)
            self.call_depth += 1
            caller_loop_depth = self.loop_depth
            self.loop_depth = 0
            try:
                try:
                    self.execute_block(callee.body, local)
                except ReturnSignal as ret:
                    return ret.value
                return None
            finally:
                self.loop_depth = caller_loop_depth
                self.call_depth -= 1
        self.error(expr.token, "RuntimeError", "Unsupported expression")

    def call_builtin(self, name: str, args: list[object], token: Token) -> object:
        if name == "bisa":
            if len(args) > 1:
                self.error(token, "TypeError", f"'bisa' expects 0 or 1 arguments, got {len(args)}")
            if args:
                if not isinstance(args[0], str):
                    self.error(token, "TypeError", "'bisa' prompt must be text")
                self.check_allocation(args[0], token)
                self.write_output(args[0], token, flush=True)
            line = self.stdin.readline()
            if line == "":
                self.error(token, "InputError", "No more input is available")
            return self.check_allocation(line.rstrip("\r\n"), token)
        if len(args) != 1:
            self.error(token, "TypeError", f"'{name}' expects 1 argument, got {len(args)}")
        value = args[0]
        if name == "tentɛn":
            if not isinstance(value, (str, list)):
                self.error(token, "TypeError", "'tentɛn' requires text or a list")
            return len(value)
        if name == "nsɛm":
            return self.check_allocation(display(value), token)
        if name == "nɔma":
            if type(value) in (int, float):
                return value
            if not isinstance(value, str) or not re.fullmatch(r"[+-]?(?:\d+(?:\.\d+)?|\.\d+)", value.strip(), flags=re.ASCII):
                self.error(token, "TypeError", "'nɔma' requires a number or numeric text")
            text = value.strip()
            if len(text) > 1000:
                self.error(token, "ResourceError", "Numeric value is too large")
            number = float(text) if "." in text else int(text)
            return self.check_allocation(number, token)
        self.error(token, "NameError", f"Unknown built-in '{name}'")
