from __future__ import annotations

import json
from types import SimpleNamespace


def report(nodeid, when, outcome, *, duration=0.01, longrepr=None):
    return SimpleNamespace(
        nodeid=nodeid,
        when=when,
        outcome=outcome,
        duration=duration,
        longrepr=longrepr,
        failed=outcome == "failed",
        skipped=outcome == "skipped",
    )


def test_setup_failure_is_emitted_as_test_failure(load_module, tmp_path):
    module = load_module("02-structured-tests/pytest_jsonl_reporter.py")
    output = tmp_path / "nested" / "results.jsonl"
    plugin = module.JsonlPlugin(output)

    plugin.pytest_runtest_logreport(
        report("tests/test_app.py::test_boot", "setup", "failed", longrepr="tests/test_app.py:7")
    )
    plugin.pytest_sessionfinish(1)

    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert records[0]["outcome"] == "failed"
    assert records[0]["failure"]["phase"] == "setup"
    assert records[-1]["failed"] == 1


def test_phases_are_combined_into_one_record(load_module, tmp_path):
    module = load_module("02-structured-tests/pytest_jsonl_reporter.py")
    output = tmp_path / "results.jsonl"
    plugin = module.JsonlPlugin(output)

    for phase in ("setup", "call", "teardown"):
        plugin.pytest_runtest_logreport(report("tests/test_app.py::test_ok", phase, "passed"))
    plugin.pytest_sessionfinish(0)

    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(records) == 2
    assert records[0]["duration_ms"] == 30
    assert records[-1]["passed"] == 1


def test_skip_is_counted(load_module, tmp_path):
    module = load_module("02-structured-tests/pytest_jsonl_reporter.py")
    output = tmp_path / "results.jsonl"
    plugin = module.JsonlPlugin(output)

    plugin.pytest_runtest_logreport(report("tests/test_app.py::test_skip", "setup", "skipped"))
    plugin.pytest_sessionfinish(0)

    records = [json.loads(line) for line in output.read_text().splitlines()]
    assert records[0]["outcome"] == "skipped"
    assert records[-1]["skipped"] == 1


def test_failure_helpers_extract_compact_context(load_module):
    module = load_module("02-structured-tests/pytest_jsonl_reporter.py")
    text = "header\n> assert value == 4\ntests/test_app.py:18: AssertionError"

    assert module._first_citation(text) == "tests/test_app.py:18"
    assert module._short_summary(text) == "> assert value == 4"
    assert module._first_citation("") is None
