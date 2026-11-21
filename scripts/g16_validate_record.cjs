/* G1.6 independent JavaScript implementation of host-side typed record checks.
 * Not exposed as Kasa syntax/builtins or browser worker imports.
 */
"use strict";

const TYPE_NAMES = new Set(["integer", "text", "boolean"]);
const NAME = /^[A-Za-z_][A-Za-z0-9_]*$/u;
const MAX_FIELDS = 32;
const MAX_TEXT = 1024;

function validateSchema(schema) {
  if (!Array.isArray(schema) || schema.length > MAX_FIELDS)
    throw new Error("Schema must be a list of at most 32 fields");
  const seen = new Set();
  for (const field of schema) {
    if (!field || typeof field !== "object" || Array.isArray(field)
        || Object.keys(field).sort().join(",") !== "name,required,type")
      throw new Error("Each field must have exactly name, type, required");
    if (typeof field.name !== "string" || !NAME.test(field.name) || seen.has(field.name))
      throw new Error("Invalid or duplicate field name");
    if (typeof field.type !== "string" || !TYPE_NAMES.has(field.type)
        || typeof field.required !== "boolean")
      throw new Error("Invalid field type or required flag");
    seen.add(field.name);
  }
  return schema;
}

function validateRecord(schema, record) {
  const fields = validateSchema(schema);
  if (!Array.isArray(record) || record.length !== fields.length)
    return {ok: false, code: "INVALID_SHAPE", field: null};
  for (let i = 0; i < fields.length; i++) {
    const {name, type, required} = fields[i];
    const value = record[i];
    if (value === null) {
      if (required) return {ok: false, code: "REQUIRED", field: name};
      continue;
    }
    const valid = type === "integer"
      ? typeof value === "number" && Number.isSafeInteger(value)
      : type === "text"
      ? typeof value === "string" && [...value].length <= MAX_TEXT
      : typeof value === "boolean";
    if (!valid) return {ok: false, code: "INVALID_TYPE", field: name};
  }
  return {ok: true, code: "OK", field: null};
}
module.exports = {validateSchema, validateRecord};
