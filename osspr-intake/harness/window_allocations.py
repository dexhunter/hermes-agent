#!/usr/bin/env python3
"""Allocation baseline for agent.repetition_guard._window_count_dominated.

The stream watch judges at most a 64KB tail. Text that is not a repetition
loop still materializes one 60-character key per offset. Prints the number
of live allocations attributed to repetition_guard.py at the function's
return (warmup discarded).
"""
from __future__ import annotations

import gc
import sys
import tracemalloc
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.repetition_guard import _window_count_dominated

# Same shape as tests/agent/test_repetition_guard.py::test_long_legitimate_text_not_flagged,
# cut to the stream tail the watch actually scans (_STREAM_TAIL_CHARS).
_TAIL = 64_000


def _unique_tail(n: int = _TAIL) -> str:
    parts: list[str] = []
    size = 0
    i = 0
    while size < n:
        piece = (
            f"Sentence number {i} describes a distinct topic with unique words "
            f"such as quasar-{i} and nebula-{i} to keep every window distinct. "
        )
        parts.append(piece)
        size += len(piece)
        i += 1
    return "".join(parts)[:n]


TEXT = _unique_tail()
_CODE = _window_count_dominated.__code__
_FILTER = tracemalloc.Filter(True, "*repetition_guard.py")


def allocation_count() -> int:
    gc.collect()
    tracemalloc.start()
    tracemalloc.clear_traces()
    holder: dict[str, int] = {}

    def tracer(frame, event, arg):
        if event == "return" and frame.f_code is _CODE:
            snap = tracemalloc.take_snapshot().filter_traces([_FILTER])
            holder["n"] = sum(stat.count for stat in snap.statistics("lineno"))
        return tracer

    sys.settrace(tracer)
    try:
        dominated = _window_count_dominated(TEXT, len(TEXT))
    finally:
        sys.settrace(None)
        tracemalloc.stop()
    if dominated is not False:
        raise SystemExit("unique tail was flagged as repetition-dominated")
    if "n" not in holder:
        raise SystemExit("allocation snapshot missed the return")
    return holder["n"]


def main() -> None:
    allocation_count()  # warmup: linecache / first-trace noise
    print(allocation_count())


if __name__ == "__main__":
    main()
