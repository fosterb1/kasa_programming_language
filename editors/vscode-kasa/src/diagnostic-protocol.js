"use strict";

const path = require('node:path');

/** Parse one versioned Kasa CLI diagnostic. Reject unknown/malformed records. */
function parseKasaDiagnostic(stderr, expectedFile) {
  if (typeof stderr !== 'string' || stderr.length > 128 * 1024) return null;
  let value;
  try { value = JSON.parse(stderr.trim()); } catch { return null; }
  if (!value || Array.isArray(value) || typeof value !== 'object') return null;
  if (value.schema_version !== 1 ||
      typeof value.category !== 'string' || !value.category ||
      typeof value.message !== 'string' || !value.message ||
      typeof value.file !== 'string' || !value.file) return null;
  if (path.normalize(value.file) !== path.normalize(expectedFile)) return null;
  const coordinate = (n) => Number.isSafeInteger(n) && n >= 1;
  const hasLocation = coordinate(value.line) && coordinate(value.column);
  if (!hasLocation && !(value.category === 'FileError' &&
                         value.line === null && value.column === null)) return null;
  return {
    category: value.category, message: value.message,
    line: hasLocation ? value.line : null,
    column: hasLocation ? value.column : null,
  };
}
module.exports = { parseKasaDiagnostic };
