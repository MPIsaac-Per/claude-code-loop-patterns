# Structured pytest reporter

A tiny pytest plugin that emits one JSON object per test result and a final summary, either to stdout or to a file. Failure records include a short summary, the first file:line citation from the traceback, and the last 12 lines of the failure message.

## Use

Drop `pytest_jsonl_reporter.py` into your repo. Either register it via your `conftest.py`:

```python
# conftest.py
pytest_plugins = ["pytest_jsonl_reporter"]
```

or load it explicitly per run:

```bash
pytest -p ./pytest_jsonl_reporter.py --jsonl-out=test-results.jsonl
```

The output stream is one JSON object per line, plus a final `kind=summary` record:

```json
{"nodeid": "tests/test_foo.py::test_bar", "outcome": "failed", "duration_ms": 12,
 "failure": {"summary": "AssertionError: expected 4 got 5",
             "citation": "tests/test_foo.py:42",
             "tail": ["    assert result == 4", "E   AssertionError: ..."]}}
{"kind": "summary", "duration_ms": 412, "total": 47, "passed": 46, "failed": 1, "skipped": 0, "exit_status": 1}
```

## Prior art

This is a deliberately minimal reference, not a replacement for established pytest JSON reporters. For production use, prefer:

- [`pytest-json-report`](https://github.com/numirias/pytest-json-report): the de facto standard, with a richer schema, hooks for custom metadata, and proper documentation.
- [`pytest-common-test-report-json`](https://github.com/infopulse/pytest-common-test-report-json): emits the [Common Test Report Format](https://ctrf.io/) JSON schema.

This file is in the repo because (a) it has zero third-party dependencies beyond pytest itself, (b) it fits in one file you can read in a sitting, and (c) the JSONL stream composes naturally with the evidence harness in [`../03-verification-gate/`](../03-verification-gate). For anything beyond that, swap in `pytest-json-report`.

## Why

The article's fifth lesson: tools that return structured failure beat tools that bury the cause in 200 lines of stderr. A pytest run is one of the most common tool calls an agent makes; making its output legible is a direct loop improvement.

Article reference: §5 (errors are the work).
