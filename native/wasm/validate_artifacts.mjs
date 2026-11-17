/** Verify a real WebAssembly binary was generated (not a magic-header stub).
 * Usage: node native/wasm/validate_artifacts.mjs
 * This checks compilation and static linkage, not browser initialization.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const moduleFile=path.join(project,'playground/native/kasa-native.wasm');
const glueFile=path.join(project,'playground/native/kasa-native.js');
const binary=await fs.readFile(moduleFile);
if (binary.length<4096) throw new Error('WASM binary is suspiciously small; not a real compiled Kasa VM');
const compiled=await WebAssembly.compile(binary);
const glue=await fs.readFile(glueFile,'utf8');
if (!glue.includes('createKasaModule')) throw new Error('Emscripten glue does not define createKasaModule');
const exports=WebAssembly.Module.exports(compiled).map(x=>x.name);
const imports=WebAssembly.Module.imports(compiled);
if (exports.length===0) throw new Error('WASM file has no exports');
console.log('WASM compilation verified:', binary.length, 'bytes,', exports.length, 'exports,', imports.length, 'imports');
console.log('Note: true browser end-to-end smoke testing is still required.');
