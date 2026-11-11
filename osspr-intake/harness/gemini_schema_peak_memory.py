#!/usr/bin/env python3
"""Peak-memory baseline for agent.gemini_schema.prepare_gemini_tool_parameters.

A large no-$ref tool schema (500 object groups, 20 fields each) stands in
for one big MCP/OpenAPI function declaration prepared on a Gemini request.
Prints tracemalloc peak bytes of one call after warmup. The schema object
is built before tracing.
"""
from __future__ import annotations

import gc
import sys
import tracemalloc
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.gemini_schema import prepare_gemini_tool_parameters

_GROUPS = 500
_FIELDS = 20


def _schema() -> dict:
    properties = {}
    for i in range(_GROUPS):
        nested = {
            f"f{j}": {
                "type": "string",
                "description": f"Field {j} of group {i} carried unchanged on the wire.",
                "minLength": 1,
                "maxLength": 240,
            }
            for j in range(_FIELDS)
        }
        properties[f"g{i}"] = {
            "type": "object",
            "description": f"Parameter group {i} from the upstream OpenAPI document.",
            "properties": nested,
            "required": [f"f{j}" for j in range(0, _FIELDS, 4)],
        }
    return {
        "type": "object",
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "properties": properties,
        "required": ["g0"],
    }


def _peak(fn) -> int:
    gc.collect()
    tracemalloc.start()
    try:
        tracemalloc.clear_traces()
        tracemalloc.reset_peak()
        fn()
        _current, peak = tracemalloc.get_traced_memory()
        return int(peak)
    finally:
        tracemalloc.stop()


def main() -> None:
    schema = _schema()
    prepared = prepare_gemini_tool_parameters(schema)
    if schema.get("$schema") is None or len(prepared.get("properties") or {}) != _GROUPS:
        raise SystemExit("prepare_gemini_tool_parameters changed the caller's schema or dropped groups")
    if "$schema" in prepared:
        raise SystemExit("root $schema was not dropped")
    print(_peak(lambda: prepare_gemini_tool_parameters(schema)))


if __name__ == "__main__":
    main()
