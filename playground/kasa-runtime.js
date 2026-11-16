/* Kasa browser runtime: standalone Twi-first tokenizer, parser and interpreter.
 * Deliberately contains no eval(), Function(), network access, or Python runtime.
 * Behavior is modeled on src/kasa/core.py (the reference implementation).
 * This file can run in a Web Worker and be tested with Node.js.
 */
"use strict";

(function (root) {
  const KEYWORDS = Object.freeze({
    ka: "PRINT", ma: "ASSIGN", "sɛ": "IF", anyɛ_saa_a: "ELSE",
    "mpɛn": "REPEAT", bere_a: "WHILE", dwumadie: "FUNCTION",
    sanma: "RETURN", awiei: "END", nokware: "TRUE", atoro: "FALSE",
    hwee: "NONE", ne: "AND", anaa: "OR", "ɛnyɛ": "NOT",
    gyae: "BREAK", toa_so: "CONTINUE",
  });
  const OPS = new Set(["==", "!=", "<=", ">=", "+", "-", "*", "/", "%", "<", ">", "=", "(", ")", "[", "]", ","]);
  const BP = { OR: 10, AND: 20, "==": 30, "!=": 30, "<": 40, "<=": 40, ">": 40, ">=": 40, "+": 50, "-": 50, "*": 60, "/": 60, "%": 60 };
  const COMPARISONS = new Set(["<", "<=", ">", ">=", "==", "!="]);
  const SOURCE_LIMIT = 50_000;
  const INPUT_LIMIT = 50_000;
  const OUTPUT_LIMIT = 64_000;
  const STEP_LIMIT = 20_000;
  const MAX_DEPTH = 48;
  const MAX_LIST_SIZE = 10_000;
  const MAX_TEXT_SIZE = 1_000_000;
  const FILENAME = "playground.kasa";
  const literal = (kind, token, value = null, children = []) => ({ kind, token, value, children });
  const length = s => [...s].length;

  class KasaError extends Error {
    constructor(category, message, token) {
      super(`${FILENAME}:${token.line}:${token.column}: ${category}: ${message}`);
      this.name = category;
      this.category = category;
    }
  }
  const syntax = (message, token) => { throw new KasaError("SyntaxError", message, token); };

  function tokenize(source) {
    source = source.replace(/\r\n?/g, "\n");
    const tokens = [];
    let i = 0, line = 1, column = 1;
    function advance() {
      const c = source[i++];
      if (c === "\n") { line++; column = 1; }
      else column++;
      return c;
    }
    const tok = (kind, text, ln, col) => ({ kind, text, line: ln, column: col });
    while (i < source.length) {
      const ch = source[i], ln = line, col = column;
      if (ch === " " || ch === "\t") { advance(); continue; }
      if (ch === "#") { while (i < source.length && source[i] !== "\n") advance(); continue; }
      if (ch === "\n") { advance(); tokens.push(tok("NEWLINE", "\n", ln, col)); continue; }
      if (ch === '"') {
        advance(); let text = "";
        while (i < source.length && source[i] !== '"' && source[i] !== "\n") {
          let c = advance();
          if (c === "\\") {
            if (i >= source.length || source[i] === "\n") syntax("Unterminated string escape", tok("STRING", "", ln, col));
            const e = advance(), escapes = { n: "\n", r: "\r", t: "\t", "\\": "\\", '"': '"' };
            if (!Object.hasOwn(escapes, e)) syntax(`Unsupported escape \\${e}`, tok("STRING", "", ln, col));
            c = escapes[e];
          }
          text += c;
        }
        if (i >= source.length || source[i] !== '"') syntax("Unterminated string", tok("STRING", "", ln, col));
        advance(); tokens.push(tok("STRING", text, ln, col)); continue;
      }
      if (/[0-9]/.test(ch)) {
        let digits = ""; while (i < source.length && /[0-9]/.test(source[i])) digits += advance();
        let kind = "INTEGER";
        if (source[i] === "." && /[0-9]/.test(source[i + 1] || "")) {
          kind = "DECIMAL"; digits += advance();
          while (i < source.length && /[0-9]/.test(source[i])) digits += advance();
        }
        if (digits.length > 1000) syntax("Numeric literal is too long", tok(kind, "", ln, col));
        tokens.push(tok(kind, digits, ln, col)); continue;
      }
      if (/[\p{L}_]/u.test(ch)) {
        let word = "";
        while (i < source.length && /[\p{L}\p{N}_]/u.test(source[i])) word += advance();
        tokens.push(tok(KEYWORDS[word] || "NAME", word, ln, col)); continue;
      }
      const pair = source.slice(i, i + 2);
      if (OPS.has(pair)) { advance(); advance(); tokens.push(tok(pair, pair, ln, col)); continue; }
      if (OPS.has(ch)) { advance(); tokens.push(tok(ch, ch, ln, col)); continue; }
      syntax(`Unexpected character '${ch}'`, tok("INVALID", ch, ln, col));
    }
    tokens.push(tok("EOF", "", line, column));
    return tokens;
  }

  class Parser {
    constructor(tokens) { this.tokens = tokens; this.pos = 0; }
    get current() { return this.tokens[this.pos]; }
    match(kind) {
      if (this.current.kind !== kind) return null;
      return this.tokens[this.pos++];
    }
    expect(kind, desc = kind) {
      const token = this.match(kind);
      if (!token) this.fail(`Expected ${desc}, found ${this.current.text || "end of file"}`);
      return token;
    }
    fail(msg, at = this.current) { syntax(msg, at); }
    newlines() { while (this.match("NEWLINE")) {} }
    endLine() { if (this.current.kind !== "EOF") this.expect("NEWLINE", "a new line"); }
    parse() { const body = this.block(new Set(["EOF"])); this.expect("EOF"); return body; }
    block(stop) {
      const body = []; this.newlines();
      while (!stop.has(this.current.kind)) {
        if (this.current.kind === "EOF") this.fail("Missing 'awiei' before end of file");
        if (this.current.kind === "END" || this.current.kind === "ELSE") this.fail(`Unexpected block delimiter '${this.current.text}'`);
        body.push(this.statement()); this.newlines();
      }
      return body;
    }
    statement() {
      const t = this.current;
      if (this.match("PRINT")) { const expr = this.expression(); this.endLine(); return literal("print", t, null, [expr]); }
      if (this.match("ASSIGN")) {
        const target = this.expression();
        if (!(["name", "index"].includes(target.kind)) || (target.kind === "index" && !this.assignableIndex(target))) {
          this.fail("The target of 'ma' must be a variable or list index", target.token);
        }
        this.expect("=", "'=' in an assignment"); const expr = this.expression(); this.endLine();
        return literal("assign", t, null, [target, expr]);
      }
      if (this.match("IF")) {
        const condition = this.expression();
        const marker = this.expect("NAME", "'a' after the condition");
        if (marker.text !== "a") this.fail("Expected 'a' after the condition", marker);
        this.endLine(); const yes = this.block(new Set(["ELSE", "END"]));
        let no = [];
        if (this.match("ELSE")) { this.endLine(); no = this.block(new Set(["END"])); }
        this.expect("END", "'awiei' to close the conditional"); this.endLine();
        return literal("if", t, null, [condition, yes, no]);
      }
      if (this.match("REPEAT")) {
        const count = this.expression(); this.endLine();
        const body = this.block(new Set(["END"])); this.expect("END", "'awiei' to close the repetition"); this.endLine();
        return literal("repeat", t, null, [count, body]);
      }
      if (this.match("WHILE")) {
        const condition = this.expression(); this.endLine();
        const body = this.block(new Set(["END"])); this.expect("END", "'awiei' to close the loop"); this.endLine();
        return literal("while", t, null, [condition, body]);
      }
      if (this.match("FUNCTION")) {
        const name = this.expect("NAME", "a function name"); this.expect("(");
        const params = [];
        if (this.current.kind !== ")") {
          while (true) {
            const param = this.expect("NAME", "a parameter name").text;
            if (params.includes(param)) this.fail(`Duplicate parameter '${param}'`);
            params.push(param);
            if (!this.match(",")) break;
          }
        }
        this.expect(")"); this.endLine();
        const body = this.block(new Set(["END"])); this.expect("END", "'awiei' to close the function"); this.endLine();
        return literal("function", t, [name.text, params], [body]);
      }
      if (this.match("RETURN")) {
        const expr = ["NEWLINE", "EOF"].includes(this.current.kind) ? null : this.expression();
        this.endLine(); return literal("return", t, null, [expr]);
      }
      if (this.match("BREAK")) { this.endLine(); return literal("break", t); }
      if (this.match("CONTINUE")) { this.endLine(); return literal("continue", t); }
      const expr = this.expression(); this.endLine(); return literal("expression", t, null, [expr]);
    }
    assignableIndex(node) {
      while (node.kind === "index") node = node.children[0];
      return node.kind === "name";
    }
    expression(minBP = 0) {
      const t = this.current;
      let left;
      if (this.match("-")) left = literal("unary", t, "-", [this.expression(70)]);
      else if (this.match("NOT")) left = literal("unary", t, "NOT", [this.expression(70)]);
      else if (this.match("INTEGER")) left = literal("literal", t, BigInt(t.text));
      else if (this.match("DECIMAL")) {
        const value = Number(t.text);
        if (!Number.isFinite(value)) this.fail("Numeric literal exceeds the supported range", t);
        left = literal("literal", t, makeFloat(value));
      }
      else if (this.match("STRING")) left = literal("literal", t, t.text);
      else if (this.match("TRUE")) left = literal("literal", t, true);
      else if (this.match("FALSE")) left = literal("literal", t, false);
      else if (this.match("NONE")) left = literal("literal", t, null);
      else if (this.match("NAME")) left = literal("name", t, t.text);
      else if (this.match("(")) { left = this.expression(); this.expect(")", "')'"); }
      else if (this.match("[")) {
        const items = [];
        if (this.current.kind !== "]") {
          while (true) {
            items.push(this.expression());
            if (!this.match(",")) break;
          }
        }
        this.expect("]", "']'"); left = literal("list", t, null, items);
      } else this.fail("Expected a value or expression");
      while (true) {
        const op = this.current;
        if (op.kind === "(" && 80 >= minBP) {
          this.pos++; const args = [];
          if (this.current.kind !== ")") {
            while (true) { args.push(this.expression()); if (!this.match(",")) break; }
          }
          this.expect(")", "')' after arguments"); left = literal("call", op, null, [left, args]); continue;
        }
        if (op.kind === "[" && 80 >= minBP) {
          this.pos++; const index = this.expression(); this.expect("]", "']' after the index");
          left = literal("index", op, null, [left, index]); continue;
        }
        const bp = Object.hasOwn(BP, op.kind) ? BP[op.kind] : -1;
        if (bp < minBP) break;
        if (COMPARISONS.has(op.kind) && left.kind === "binary" && COMPARISONS.has(left.value))
          this.fail("Comparison chaining is not supported; use 'ne'", op);
        this.pos++; const right = this.expression(bp + 1);
        left = literal("binary", op, op.kind, [left, right]);
      }
      return left;
    }
  }

  class FloatValue { constructor(value) { this.value = value; } }
  const makeFloat = value => new FloatValue(value);
  const isNumber = value => typeof value === "bigint" || value instanceof FloatValue;
  const toNumber = value => typeof value === "bigint" ? Number(value) : value.value;
  function display(value) {
    if (value === null) return "hwee";
    if (value === true) return "nokware";
    if (value === false) return "atoro";
    if (typeof value === "bigint") return value.toString();
    if (value instanceof FloatValue) {
      const text = String(value.value);
      return Number.isInteger(value.value) && !text.includes("e") ? `${text}.0` : text;
    }
    if (typeof value === "string") return value;
    if (Array.isArray(value)) return "[" + value.map(item => typeof item === "string" ? "'" + item.replace(/\\/g, "\\\\").replace(/'/g, "\\'") + "'" : display(item)).join(", ") + "]";
    if (value?.__kind === "function") return `<dwumadie ${value.name}>`;
    if (value?.__kind === "builtin") return `<built-in ${value.name}>`;
    return String(value);
  }
  function equal(a, b) {
    if (isNumber(a) && isNumber(b)) {
      if (typeof a === "bigint" && typeof b === "bigint") return a === b;
      return toNumber(a) === toNumber(b);
    }
    if (a === null || b === null || typeof a === "boolean" || typeof b === "boolean") return a === b;
    if (Array.isArray(a) && Array.isArray(b)) return a.length === b.length && a.every((v, i) => equal(v, b[i]));
    return a === b;
  }
  class Environment {
    constructor(parent = null) { this.parent = parent; this.values = new Map(); }
    get(name) { if (this.values.has(name)) return [true, this.values.get(name)]; return this.parent?.get(name) || [false, null]; }
  }
  class Signal { constructor(type, value = null) { this.type = type; this.value = value; } }
  class OutputLimitError extends Error { constructor() { super(`Output exceeded the ${OUTPUT_LIMIT.toLocaleString("en-US")}-character limit`); } }

  class Interpreter {
    constructor(inputText) {
      this.globals = new Environment(); this.steps = 0; this.callDepth = 0; this.loopDepth = 0;
      this.output = "";
      this.inputs = inputText.match(/[^\n]*\n|[^\n]+$/g) || [];
      this.inputCursor = 0;
    }
    error(tok, cat, msg) { throw new KasaError(cat, msg, tok); }
    tick(tok) { if (++this.steps > STEP_LIMIT) this.error(tok, "ResourceError", `Execution limit (${STEP_LIMIT} steps) exceeded`); }
    check(value, tok) {
      if (typeof value === "string" && length(value) > MAX_TEXT_SIZE || Array.isArray(value) && value.length > MAX_LIST_SIZE) this.error(tok, "ResourceError", "Value exceeds the size limit");
      if (typeof value === "bigint" && value.toString(2).replace("-", "").length > 16_384) this.error(tok, "ResourceError", "Integer exceeds supported size limit");
      if (value instanceof FloatValue && !Number.isFinite(value.value)) this.error(tok, "ResourceError", "Numeric result exceeds supported range");
      return value;
    }
    outputLine(value) {
      const line = display(value) + "\n";
      if (this.output.length + line.length > OUTPUT_LIMIT) throw new OutputLimitError();
      this.output += line;
    }
    boolean(value, tok) { if (typeof value !== "boolean") this.error(tok, "TypeError", "Condition must be 'nokware' or 'atoro'"); return value; }
    number(value, tok) { if (!isNumber(value)) this.error(tok, "TypeError", "Expected a number (not text or a Boolean)"); return value; }
    validIndex(list, index, tok) {
      if (!Array.isArray(list)) this.error(tok, "TypeError", "Indexing requires a list");
      if (typeof index !== "bigint") this.error(tok, "TypeError", "List index must be an integer");
      if (index < 0n || index >= BigInt(list.length)) this.error(tok, "IndexError", "List index is outside its range");
      return Number(index);
    }
    run(body) { this.block(body, this.globals); }
    block(body, env) { for (const node of body) this.execute(node, env); }
    execute(s, env) {
      this.tick(s.token);
      switch (s.kind) {
        case "print": return this.outputLine(this.eval(s.children[0], env));
        case "assign": {
          const [target, valueNode] = s.children, value = this.eval(valueNode, env);
          if (target.kind === "name") env.values.set(target.value, value);
          else {
            const list = this.eval(target.children[0], env);
            const index = this.eval(target.children[1], env);
            list[this.validIndex(list, index, target.token)] = value;
          }
          return;
        }
        case "if": {
          const [cond, yes, no] = s.children;
          return this.block(this.boolean(this.eval(cond, env), s.token) ? yes : no, env);
        }
        case "repeat": {
          const [countNode, body] = s.children, count = this.eval(countNode, env);
          if (typeof count !== "bigint" || count < 0n) this.error(s.token, "TypeError", "'mpɛn' requires a non-negative integer count");
          this.loopDepth++;
          try {
            for (let n = 0n; n < count; n++) {
              this.tick(s.token);
              try { this.block(body, env); }
              catch (e) { if (e instanceof Signal && e.type === "continue") continue; if (e instanceof Signal && e.type === "break") break; throw e; }
            }
          } finally { this.loopDepth--; }
          return;
        }
        case "while": {
          const [cond, body] = s.children;
          this.loopDepth++;
          try {
            while (this.boolean(this.eval(cond, env), s.token)) {
              try { this.block(body, env); }
              catch (e) { if (e instanceof Signal && e.type === "continue") continue; if (e instanceof Signal && e.type === "break") break; throw e; }
            }
          } finally { this.loopDepth--; }
          return;
        }
        case "function": {
          const [name, params] = s.value;
          env.values.set(name, { __kind: "function", name, params, body: s.children[0], closure: env }); return;
        }
        case "return": {
          if (this.callDepth === 0) this.error(s.token, "SyntaxError", "'sanma' can only appear inside a function");
          throw new Signal("return", s.children[0] !== null ? this.eval(s.children[0], env) : null);
        }
        case "break": {
          if (this.loopDepth === 0) this.error(s.token, "SyntaxError", "'gyae' can only appear inside a loop");
          throw new Signal("break");
        }
        case "continue": {
          if (this.loopDepth === 0) this.error(s.token, "SyntaxError", "'toa_so' can only appear inside a loop");
          throw new Signal("continue");
        }
        case "expression": return void this.eval(s.children[0], env);
        default: this.error(s.token, "RuntimeError", "Unsupported statement");
      }
    }
    eval(e, env) {
      this.tick(e.token);
      switch (e.kind) {
        case "literal": return this.check(e.value, e.token);
        case "name": {
          const [found, value] = env.get(e.value);
          if (found) return value;
          if (["bisa", "tentɛn", "nɔma", "nsɛm"].includes(e.value)) return { __kind: "builtin", name: e.value };
          this.error(e.token, "NameError", `Unknown name '${e.value}'`);
        }
        case "list": {
          if (e.children.length > MAX_LIST_SIZE) this.error(e.token, "ResourceError", "List is too large");
          return e.children.map(item => this.eval(item, env));
        }
        case "index": {
          const list = this.eval(e.children[0], env), index = this.eval(e.children[1], env);
          return list[this.validIndex(list, index, e.token)];
        }
        case "unary": {
          const value = this.eval(e.children[0], env);
          if (e.value === "NOT") return !this.boolean(value, e.token);
          this.number(value, e.token);
          return this.check(typeof value === "bigint" ? -value : makeFloat(-value.value), e.token);
        }
        case "binary": {
          const [left, right] = e.children, op = e.value, a = this.eval(left, env);
          if (op === "AND") return !this.boolean(a, e.token) ? false : this.boolean(this.eval(right, env), e.token);
          if (op === "OR") return this.boolean(a, e.token) ? true : this.boolean(this.eval(right, env), e.token);
          const b = this.eval(right, env);
          if (op === "==") return equal(a, b);
          if (op === "!=") return !equal(a, b);
          if (op === "+" && typeof a === "string" && typeof b === "string") return this.check(a + b, e.token);
          this.number(a, e.token); this.number(b, e.token);
          if (["<", "<=", ">", ">="].includes(op)) {
            const x = typeof a === "bigint" && typeof b === "bigint" ? a : toNumber(a);
            const y = typeof a === "bigint" && typeof b === "bigint" ? b : toNumber(b);
            return op === "<" ? x < y : op === "<=" ? x <= y : op === ">" ? x > y : x >= y;
          }
          if ((op === "/" || op === "%") && (b === 0n || b instanceof FloatValue && b.value === 0)) this.error(e.token, "ZeroDivisionError", "Cannot divide by zero");
          if (op === "%" && (typeof a !== "bigint" || typeof b !== "bigint")) this.error(e.token, "TypeError", "Remainder requires two integers");
          let result;
          if (op === "/") result = makeFloat(toNumber(a) / toNumber(b));
          else if (typeof a === "bigint" && typeof b === "bigint") {
            if (op === "+") result = a + b;
            else if (op === "-") result = a - b;
            else if (op === "*") result = a * b;
            else if (op === "%") result = a % b;
          } else {
            const x = toNumber(a), y = toNumber(b);
            if (op === "+") result = makeFloat(x + y);
            else if (op === "-") result = makeFloat(x - y);
            else if (op === "*") result = makeFloat(x * y);
          }
          return this.check(result, e.token);
        }
        case "call": {
          const [funcNode, argNodes] = e.children;
          const func = this.eval(funcNode, env), args = argNodes.map(arg => this.eval(arg, env));
          if (func?.__kind === "builtin") return this.builtin(func.name, args, e.token);
          if (func?.__kind !== "function") this.error(e.token, "TypeError", "This value cannot be called as a function");
          if (args.length !== func.params.length) this.error(e.token, "TypeError", `'${func.name}' expects ${func.params.length} arguments, got ${args.length}`);
          if (this.callDepth >= MAX_DEPTH) this.error(e.token, "ResourceError", "Function call depth exceeded");
          const local = new Environment(func.closure);
          func.params.forEach((param, i) => local.values.set(param, args[i]));
          this.callDepth++;
          const callerLoopDepth = this.loopDepth;
          this.loopDepth = 0;
          try {
            try { this.block(func.body, local); }
            catch (sig) { if (sig instanceof Signal && sig.type === "return") return sig.value; throw sig; }
            return null;
          } finally { this.loopDepth = callerLoopDepth; this.callDepth--; }
        }
        default: this.error(e.token, "RuntimeError", "Unsupported expression");
      }
    }
    builtin(name, args, tok) {
      const expected = name === "bisa" ? 0 : 1;
      if (args.length !== expected) this.error(tok, "TypeError", `'${name}' expects ${expected} arguments, got ${args.length}`);
      if (name === "bisa") {
        if (this.inputCursor >= this.inputs.length) this.error(tok, "InputError", "No more input is available");
        return this.check(this.inputs[this.inputCursor++].replace(/[\r\n]+$/g, ""), tok);
      }
      const value = args[0];
      if (name === "tentɛn") {
        if (!Array.isArray(value) && typeof value !== "string") this.error(tok, "TypeError", "'tentɛn' requires text or a list");
        return BigInt(Array.isArray(value) ? value.length : length(value));
      }
      if (name === "nsɛm") return this.check(display(value), tok);
      if (name === "nɔma") {
        if (isNumber(value)) return value;
        if (typeof value !== "string" || !/^[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)$/.test(value.trim()))
          this.error(tok, "TypeError", "'nɔma' requires a number or numeric text");
        if (value.trim().length > 1000) this.error(tok, "ResourceError", "Numeric value is too large");
        const text = value.trim(), result = text.includes(".") ? makeFloat(Number(text)) : BigInt(text);
        return this.check(result, tok);
      }
      this.error(tok, "NameError", `Unknown built-in '${name}'`);
    }
  }

  function executeKasa(source, input = "", mode = "run") {
    const result = { ok: false, output: "", error: "", steps: 0, mode };
    if (mode !== "run" && mode !== "check") { result.error = "Unknown execution mode"; return result; }
    if (length(source) > SOURCE_LIMIT) { result.error = `Source exceeds the ${SOURCE_LIMIT.toLocaleString("en-US")}-character limit`; return result; }
    if (length(input) > INPUT_LIMIT) { result.error = `Input exceeds the ${INPUT_LIMIT.toLocaleString("en-US")}-character limit`; return result; }
    let runtime;
    try {
      const program = new Parser(tokenize(source)).parse();
      if (mode === "run") { runtime = new Interpreter(input); runtime.run(program); result.output = runtime.output; }
      result.ok = true;
    } catch (err) {
      result.error = err instanceof Error ? err.message : "Unexpected interpreter error";
      if (runtime) result.output = runtime.output;
    } finally {
      if (runtime) result.steps = runtime.steps;
    }
    return result;
  }
  const API = Object.freeze({ executeKasa, tokenize, parse: source => new Parser(tokenize(source)).parse() });
  root.KasaRuntime = API;
  if (typeof module !== "undefined" && module.exports) module.exports = API;
})(typeof self !== "undefined" ? self : globalThis);
