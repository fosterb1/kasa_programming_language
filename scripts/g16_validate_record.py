"""G1.6 experimental host-side validation of positional record data.

This validates external *data before Kasa execution*. It is NOT a Kasa
builtin, a sandbox, a serializer, or a native C++ type system.
"""
from __future__ import annotations

import re

TYPES = frozenset({"integer", "text", "boolean"})
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z", re.ASCII)
MAX_FIELDS = 32
MAX_TEXT = 1024
SAFE_INT_MIN = -(1 << 53) + 1
SAFE_INT_MAX = (1 << 53) - 1


class ValidationContractError(ValueError):
    """Invalid application-authored schema, not a record validation error."""


def validate_schema(schema: object) -> tuple[dict, ...]:
    if type(schema) is not list or len(schema) > MAX_FIELDS:
        raise ValidationContractError("Schema must be a list of at most 32 fields")
    seen: set[str] = set()
    validated = []
    for field in schema:
        if type(field) is not dict or set(field) != {"name", "type", "required"}:
            raise ValidationContractError("Each field must have exactly name, type, required")
        name, kind, required = field["name"], field["type"], field["required"]
        if type(name) is not str or not NAME.fullmatch(name) or name in seen:
            raise ValidationContractError("Invalid or duplicate field name")
        if type(kind) is not str or kind not in TYPES or type(required) is not bool:
            raise ValidationContractError("Invalid field type or required flag")
        seen.add(name)
        validated.append(field.copy())
    return tuple(validated)


def validate_record(schema: object, record: object) -> dict:
    """Return a stable small result; fail at first invalid field, in schema order.

    A null value is accepted only for fields with required=false. Empty string
    and zero are present; no type coercion is performed. Numeric inputs must be JSON-safe integers;
    decimal values are intentionally excluded until a portable tagged format.
    """
    fields = validate_schema(schema)
    if type(record) is not list or len(record) != len(fields):
        return {"ok": False, "code": "INVALID_SHAPE", "field": None}
    for spec, value in zip(fields, record):
        name, kind = spec["name"], spec["type"]
        if value is None:
            if spec["required"]:
                return {"ok": False, "code": "REQUIRED", "field": name}
            continue
        valid = (
            (kind == "integer" and type(value) is int and SAFE_INT_MIN <= value <= SAFE_INT_MAX)
            or (kind == "text" and type(value) is str and len(value) <= MAX_TEXT)
            or (kind == "boolean" and type(value) is bool)
        )
        if not valid:
            return {"ok": False, "code": "INVALID_TYPE", "field": name}
    return {"ok": True, "code": "OK", "field": None}
