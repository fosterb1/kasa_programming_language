/* G1.2.3: run the exact G1.1 source/output corpus in the JavaScript runtime.
 * Metadata is checked against the separate SHA-256 pinned G1 manifest.
 * No claim of native/KBC or actual-browser execution.
 */
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const crypto = require("node:crypto");
const root = path.resolve(__dirname, "..");
const kasa = require("../playground/kasa-runtime.js");
const { loadPinnedG1Modules } = require("../scripts/load_g1_js_modules.cjs");
const contract = JSON.parse(fs.readFileSync(path.join(root, "tests/g1_contract_fixtures.json"), "utf8"));
const g1 = loadPinnedG1Modules();
assert.equal(contract.schema_version, 1);
assert.equal(contract.cases.length, 19);
assert.deepEqual(contract.modules.map(m => m.id).sort(), Object.keys(g1).sort());

let passed = 0;
function check(label, fn) { fn(); console.log("PASS " + label); passed++; }
function execute(source, modules = g1) {
  return kasa.executeKasa(source, "", "run", {experimentalModules: modules});
}
const prelude = "fa math firi stdlib: m\nfa collections firi stdlib: c\n";
for (const item of contract.cases) {
  check("G1 contract: " + item.id, () => {
    // Existing source-only fixtures invoke unqualified names. Route them
    // through explicit aliases, preserving identifiers in strings/comments.
    const mapped = item.source.replace(/\bkasa_(?:min_or|max_or|total|average_or|count_above|first_index|last_index|count_distinct|all_equal)\s*\(/g, (match) => {
      const name = match.slice(0, match.indexOf("(")).trim();
      const alias = g1.math.exports.includes(name) ? "m" : "c";
      return alias + "." + match;
    });
    const result = execute(prelude + mapped);
    assert.equal(result.ok, true, item.id + ": " + result.error);
    assert.equal(result.output, item.output, item.id);
  });
}
check("generation-selected G1 math and collections", () => {
  const r = execute(prelude +
    "ma scores = [40, 60, 80, 90]\n" +
    "ka m.kasa_total(scores)\n" +
    "ka m.kasa_average_or(scores, 0)\n" +
    "ka m.kasa_count_above(scores, 60)\n" +
    "ka c.kasa_count_distinct(scores)\n");
  assert.equal(r.ok, true, r.error);
  assert.equal(r.output, "270\n67.5\n2\n4\n");
});
check("G0 compatibility and unchanged default parser", () => {
  const g0catalog = JSON.parse(fs.readFileSync(path.join(root, "stdlib/catalog.json"), "utf8"));
  const g0 = Object.create(null);
  for (const entry of g0catalog.modules) {
    const source = fs.readFileSync(path.join(root, entry.source), "utf8").replace(/\r\n/g, "\n");
    assert.equal("sha256:" + crypto.createHash("sha256").update(source).digest("hex"), entry.content_identity);
    g0[entry.id] = {source, exports: entry.exports};
  }
  const old = execute("fa math firi stdlib: m\nka m.kasa_sum([1, 2, 3])\n", g0);
  assert.equal(old.ok, true, old.error);
  assert.equal(old.output, "6\n");
  const denied = execute("fa math firi stdlib: m\nka m.kasa_total([1])\n", g0);
  assert.equal(denied.ok, false);
  assert.match(denied.error, /does not export/);
  const normal = kasa.executeKasa("fa math firi stdlib: m\nka m.kasa_total([1])\n");
  assert.equal(normal.ok, false);
});
for (const [label, source, error] of [
  ["private export", prelude + "ka m.kasa_sum([1])\n", /does not export/],
  ["unknown module", "fa unknown firi stdlib: x\nka 1\n", /Unknown catalog module/],
  ["duplicate alias", "fa math firi stdlib: x\nfa collections firi stdlib: x\nka 1\n", /alias reused/],
  ["late import", "ka 1\nfa math firi stdlib: m\n", /precede statements/],
  ["alias rewrite", "fa math firi stdlib: m\nma m = 10\n", /cannot be reassigned/],
]) {
  check("G1 rejected: " + label, () => {
    const r = execute(source);
    assert.equal(r.ok, false);
    assert.match(r.error, error);
    assert.equal(r.output, "");
  });
}
check("G1 source identity tampering rejected by Node loader", () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), "kasa-g1-"));
  try {
    fs.mkdirSync(path.join(dir, "stdlib/g1"), {recursive: true});
    fs.copyFileSync(path.join(root, "stdlib/g1/catalog.json"), path.join(dir, "stdlib/g1/catalog.json"));
    for (const filename of ["math.kasa", "collections.kasa"]) {
      fs.copyFileSync(path.join(root, "stdlib/g1", filename), path.join(dir, "stdlib/g1", filename));
    }
    fs.appendFileSync(path.join(dir, "stdlib/g1/math.kasa"), "\n# altered\n");
    assert.throws(() => loadPinnedG1Modules(dir), /hash mismatch/);
  } finally {
    fs.rmSync(dir, {recursive: true, force: true});
  }
});
console.log(passed + " G1 JavaScript compatibility checks passed");
