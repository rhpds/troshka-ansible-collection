"""Tests for Troshka connection plugin module stdout coercion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "plugins" / "connection"))

from troshka import _coerce_ansible_module_stdout  # noqa: E402


def test_valid_json_passes_through():
    payload = '{"changed": true, "rc": 0}'
    assert _coerce_ansible_module_stdout(payload) == payload.encode()


def test_python_repr_dict_converts_to_json():
    repr_text = (
        "{'changed': False, 'stdout': 'skipped', 'stderr': '', 'rc': 0, "
        "'msg': \"Did not run command since '/tmp/foo' exists\"}"
    )
    out = _coerce_ansible_module_stdout(repr_text)
    parsed = json.loads(out)
    assert parsed["changed"] is False
    assert parsed["rc"] == 0


def test_multiline_output_uses_trailing_repr_line():
    repr_line = "{'changed': True, 'rc': 0}"
    raw = f"Last login: Sun Aug 30 2026\n\n{repr_line}\n"
    out = _coerce_ansible_module_stdout(raw)
    assert json.loads(out)["changed"] is True


def test_plain_text_left_unchanged():
    raw = "hello world\n"
    assert _coerce_ansible_module_stdout(raw) == raw.encode()
