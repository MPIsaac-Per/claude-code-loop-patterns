from __future__ import annotations

import sys


def test_tail_zero_returns_no_lines(load_module):
    module = load_module("01-structured-shell/run_loud.py")

    assert module.tail("one\ntwo", 0) == []


def test_missing_command_returns_shell_compatible_code(load_module):
    module = load_module("01-structured-shell/run_loud.py")

    result = module.run(["command-that-does-not-exist-42"], None, 10)

    assert result.exit_code == 127
    assert result.diagnostic_hints[0].startswith("exit 127")


def test_timeout_is_reported(load_module):
    module = load_module("01-structured-shell/run_loud.py")

    result = module.run(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        "test",
        10,
        timeout_seconds=0.01,
    )

    assert result.exit_code == 124
    assert "timed out" in result.diagnostic_hints[0]


def test_human_output_shell_quotes_arguments(load_module):
    module = load_module("01-structured-shell/run_loud.py")
    result = module.RunResult(
        command=["printf", "%s", "two words"],
        exit_code=0,
        duration_ms=1,
        tag=None,
        stdout_tail=[],
        stderr_tail=[],
    )

    assert "'two words'" in module.render_human(result)


def test_success_captures_output_and_citations(load_module):
    module = load_module("01-structured-shell/run_loud.py")

    result = module.run(
        [sys.executable, "-c", "print('tests/test_app.py:42:7')"],
        "test",
        5,
    )

    assert result.ok
    assert result.stdout_tail == ["tests/test_app.py:42:7"]
    assert result.file_line_citations == ["tests/test_app.py:42"]


def test_diagnostic_patterns_are_detected(load_module):
    module = load_module("01-structured-shell/run_loud.py")
    stderr = "Permission denied\nModuleNotFoundError\nHTTP 429 rate limit"

    hints = module.make_hints(stderr, 126)

    assert len(hints) == 4
    assert any("dependency" in hint for hint in hints)


def test_main_emits_json_and_returns_wrapped_status(load_module, monkeypatch, capsys):
    module = load_module("01-structured-shell/run_loud.py")
    monkeypatch.setattr(
        module.sys,
        "argv",
        ["run_loud.py", "--json", sys.executable, "-c", "print('ok')"],
    )

    status = module.main()

    assert status == 0
    assert '"exit_code": 0' in capsys.readouterr().out
