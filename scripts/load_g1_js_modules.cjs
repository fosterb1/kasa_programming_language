/* G1.2.3: trusted, local Node-side G1 metadata verification for JS conformance.
 * This is NOT a browser source loader or an arbitrary package resolver.
 */
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");

const ROOT = path.resolve(__dirname, "..");
const EXPECTED = Object.freeze({
  math: Object.freeze({ source: "stdlib/g1/math.kasa", exports: ["kasa_min_or", "kasa_max_or", "kasa_total", "kasa_average_or", "kasa_count_above"] }),
  collections: Object.freeze({ source: "stdlib/g1/collections.kasa", exports: ["kasa_first_index", "kasa_last_index", "kasa_count_distinct", "kasa_all_equal"] }),
});
function canonicalSource(raw) {
  if (raw.includes("\r") && raw.replace(/\r\n/g, "").includes("\r")) throw new Error("Unsupported G1 source line endings");
  return raw.replace(/\r\n/g, "\n");
}
function loadPinnedG1Modules(root = ROOT) {
  const catalogFile = path.join(root, "stdlib/g1/catalog.json");
  const catalog = JSON.parse(fs.readFileSync(catalogFile, "utf8"));
  if (catalog.schema_version !== 1 || catalog.library_generation !== "G1" ||
      catalog.status !== "experimental_manifest_only" ||
      !Array.isArray(catalog.modules) || catalog.modules.length !== 2 ||
      Object.keys(catalog).sort().join(",") !== "library_generation,modules,schema_version,status") {
    throw new Error("Unsupported G1 module catalog");
  }
  const out = Object.create(null);
  for (const entry of catalog.modules) {
    if (!entry || !Object.hasOwn(EXPECTED, entry.id) || Object.hasOwn(out, entry.id))
      throw new Error("Duplicate or unknown G1 module");
    const expected = EXPECTED[entry.id];
    if (Object.keys(entry).sort().join(",") !== "content_identity,dependencies,exports,id,source" ||
        entry.source !== expected.source ||
        JSON.stringify(entry.exports) !== JSON.stringify(expected.exports) ||
        JSON.stringify(entry.dependencies) !== "[]" ||
        !/^sha256:[0-9a-f]{64}$/.test(entry.content_identity)) {
      throw new Error("Invalid G1 reviewed exports, dependencies or source identity");
    }
    const file = path.join(root, expected.source);
    const realRoot = fs.realpathSync(root);
    const realFile = fs.realpathSync(file);
    if (realFile !== path.join(realRoot, expected.source)) {
      throw new Error("G1 source must be a real, non-linked reviewed path");
    }
    const source = canonicalSource(fs.readFileSync(file, "utf8"));
    if (Buffer.byteLength(source, "utf8") > 50_000) throw new Error("G1 source exceeds limit");
    const digest = "sha256:" + crypto.createHash("sha256").update(source, "utf8").digest("hex");
    if (digest !== entry.content_identity) throw new Error("G1 source hash mismatch: " + entry.id);
    out[entry.id] = Object.freeze({ source, exports: Object.freeze([...entry.exports]) });
  }
  if (Object.keys(out).length !== 2) throw new Error("Missing G1 module");
  return Object.freeze(out);
}
module.exports = { loadPinnedG1Modules };
