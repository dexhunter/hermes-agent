#!/usr/bin/env python3
"""Token-count baseline for tools.delegation_output_schema.append_output_contract.

Counts the child context block with the repo tokenizer
(agent.model_metadata.estimate_tokens_rough). The schema is an 80-metric
structured report, the kind of output_schema delegate_task pastes into the
child prompt. Prints that token count (deterministic).
"""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.model_metadata import estimate_tokens_rough
from tools.delegation_output_schema import append_output_contract

_CONTEXT = "Investigate the retry budget and return the structured report."
_METRICS = 80


def _report_schema() -> dict:
    properties = {}
    for i in range(_METRICS):
        properties[f"metric_{i}"] = {
            "type": "object",
            "description": (
                f"Metric {i} collected from the child task, including the unit, "
                "the window, and the caveats the parent must preserve."
            ),
            "properties": {
                "name": {"type": "string", "description": "Stable metric name."},
                "value": {"type": "number", "description": "Numeric value in the declared unit."},
                "unit": {"type": "string", "description": "Unit such as ms, bytes, or ratio."},
                "notes": {"type": "string", "description": "Caveats that must survive into the parent summary."},
            },
            "required": ["name", "value", "unit"],
        }
    return {
        "type": "object",
        "description": "Final structured report the child must emit as its only message.",
        "properties": properties,
        "required": [f"metric_{i}" for i in range(0, _METRICS, 4)],
    }


def main() -> None:
    schema = _report_schema()
    block = append_output_contract(_CONTEXT, schema)
    if "OUTPUT CONTRACT" not in block or '"metric_0"' not in block or _CONTEXT not in block:
        raise SystemExit("output contract is missing the heading, context, or schema")
    # Warmup, then the reported count. estimate_tokens_rough is pure.
    estimate_tokens_rough(block)
    print(estimate_tokens_rough(append_output_contract(_CONTEXT, schema)))


if __name__ == "__main__":
    main()
