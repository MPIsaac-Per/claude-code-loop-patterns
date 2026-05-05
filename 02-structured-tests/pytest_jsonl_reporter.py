"""pytest_jsonl_reporter: emit structured JSONL test results.

Drop this file into your repo root and register it in conftest.py:

    # conftest.py
    pytest_plugins = ["pytest_jsonl_reporter"]

Or invoke it explicitly:

    pytest -p ./pytest_jsonl_reporter.py --jsonl-out=test-results.jsonl

Emits one JSON object per test with: nodeid, outcome, duration_ms, plus a
`failure` block on failure (short summary, file:line citation, last lines of
the traceback). A final `kind=summary` record carries totals.

The article's point: tests that fail loudly and locally beat tests that bury
the cause in 200 lines of stderr.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from time import time

import pytest


_FILE_LINE_RE = re.compile(r"^(?P<path>[A-Za-z0-9_./\\-]+\.py):(?P<line>\d+)", re.M)


def pytest_addoption(parser):
    group = parser.getgroup("jsonl-reporter")
    group.addoption(
        "--jsonl-out",
        action="store",
        default=None,
        help="Path to write JSONL test results. Default: emit to stdout.",
    )


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    out = config.getoption("--jsonl-out")
    plugin = JsonlPlugin(Path(out) if out else None)
    config.pluginmanager.register(plugin, "jsonl-reporter")


def _first_citation(text: str) -> str | None:
    if not text:
        return None
    m = _FILE_LINE_RE.search(text)
    return f"{m.group('path')}:{m.group('line')}" if m else None


def _short_summary(text: str, max_chars: int = 240) -> str:
    if not text:
        return ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(("E ", "AssertionError", ">")):
            return stripped[:max_chars]
    lines = text.splitlines()
    return lines[0][:max_chars] if lines else ""


class JsonlPlugin:
    def __init__(self, out_path: Path | None):
        self.out_path = out_path
        self.records: list[dict] = []
        self.start = time()

    def pytest_runtest_logreport(self, report):
        if report.when != "call":
            return
        record = {
            "nodeid": report.nodeid,
            "outcome": report.outcome,
            "duration_ms": int(report.duration * 1000),
        }
        if report.failed:
            text = str(report.longrepr) if report.longrepr else ""
            record["failure"] = {
                "summary": _short_summary(text),
                "citation": _first_citation(text),
                "tail": text.splitlines()[-12:] if text else [],
            }
        self.records.append(record)

    def pytest_sessionfinish(self, exitstatus):
        summary = {
            "kind": "summary",
            "duration_ms": int((time() - self.start) * 1000),
            "total": len(self.records),
            "passed": sum(1 for r in self.records if r["outcome"] == "passed"),
            "failed": sum(1 for r in self.records if r["outcome"] == "failed"),
            "skipped": sum(1 for r in self.records if r["outcome"] == "skipped"),
            "exit_status": exitstatus,
        }
        body = "\n".join(json.dumps(r) for r in self.records + [summary])
        if self.out_path:
            self.out_path.write_text(body + "\n")
        else:
            print(body)
