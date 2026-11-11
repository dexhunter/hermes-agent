#!/usr/bin/env python3
"""Peak-memory baseline for tools.read_extract._extract_docx.

Builds a long .docx (one paragraph per section, stdlib extractor only) and
prints tracemalloc's peak bytes for one call after a warmup parse. The
document is built before tracing so the peak is the extractor's.
"""
from __future__ import annotations

import gc
import sys
import tracemalloc
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from tools.read_extract import _extract_docx

_PARAGRAPHS = 8000
_SENTENCE = (
    "The quarterly report describes the migration of the billing service and its retry budget. "
)


def _write_docx(path: Path) -> None:
    sentence = (_SENTENCE * 3)[:100]
    parts = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body>',
    ]
    for i in range(_PARAGRAPHS):
        text = f"{sentence}Section {i}."
        parts.append(f'<w:p><w:r><w:t xml:space="preserve">{text}</w:t></w:r></w:p>')
    parts.append("</w:body></w:document>")
    xml = "".join(parts).encode("utf-8")
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("word/document.xml", xml)


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
    with TemporaryDirectory(prefix="osspr-docx-") as tmp:
        path = Path(tmp) / "report.docx"
        _write_docx(path)
        extracted = _extract_docx(str(path))
        if "quarterly report" not in extracted or len(extracted) < 100_000:
            raise SystemExit("docx extraction did not return the expected text")
        print(_peak(lambda: _extract_docx(str(path))))


if __name__ == "__main__":
    main()
