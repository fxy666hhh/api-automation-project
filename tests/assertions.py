"""Shared response assertions used by scenario tests."""

import json
from functools import cache
from pathlib import Path

from jsonschema import Draft202012Validator


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


@cache
def schema_validator(name):
    schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def assert_matches_schema(data, name):
    schema_validator(name).validate(data)


def assert_error(response, status, code):
    assert response.status_code == status
    body = response.json()
    assert body == {"code": code}
    assert_matches_schema(body, "error.json")
