from __future__ import annotations

import json
import sys
from datetime import UTC, datetime, timedelta

import pytest

NOW = datetime(2026, 7, 14, 12, 0, tzinfo=UTC)


def write_record(directory, name, ok):
    (directory / f"{name}.json").write_text(json.dumps({"ok": ok}))


def test_newer_failure_invalidates_older_success(load_module, tmp_path):
    module = load_module("03-verification-gate/check_evidence.py")
    write_record(tmp_path, "20260714T115800.000001Z-100", True)
    write_record(tmp_path, "20260714T115900.000001Z-101", False)

    status, message = module.check_latest_evidence(
        tmp_path,
        timedelta(minutes=30),
        now=NOW,
    )

    assert status == 1
    assert "reports failure" in message


def test_stop_hook_requires_newest_record_to_pass(load_module, tmp_path, monkeypatch):
    module = load_module("04-stop-hook/no_completion_without_evidence.py")
    write_record(tmp_path, "20260714T115800.000001Z-100", True)
    write_record(tmp_path, "20260714T115900.000001Z-101", False)

    class FrozenDateTime:
        @classmethod
        def now(cls, tz):
            return NOW

        strptime = datetime.strptime

    monkeypatch.setattr(module, "datetime", FrozenDateTime)

    assert module.latest_ok_evidence(tmp_path, timedelta(minutes=30)) is None


def test_gate_parser_rejects_unsafe_names(load_module):
    module = load_module("03-verification-gate/verify.py")

    with pytest.raises(ValueError, match="gate name"):
        module.parse_gates("../../escape: pytest")


def test_gate_parser_rejects_duplicate_names(load_module):
    module = load_module("03-verification-gate/verify.py")

    with pytest.raises(ValueError, match="duplicate"):
        module.parse_gates("test: pytest\ntest: pytest -q")


def test_gate_parser_accepts_comments_and_commands_with_colons(load_module):
    module = load_module("03-verification-gate/verify.py")

    gates = module.parse_gates("# checks\n\napi: python -c \"print('a:b')\"")

    assert gates == [module.Gate(name="api", command="python -c \"print('a:b')\"")]


@pytest.mark.parametrize("text", ["test pytest", "# only a comment", "test:"])
def test_gate_parser_rejects_incomplete_config(load_module, text):
    module = load_module("03-verification-gate/verify.py")

    with pytest.raises(ValueError):
        module.parse_gates(text)


def test_run_gate_records_success_failure_and_timeout(load_module, tmp_path):
    module = load_module("03-verification-gate/verify.py")

    ok = module.run_gate(
        module.Gate("ok", f'{sys.executable} -c "print(42)"'),
        root=tmp_path,
        evidence_dir=tmp_path,
        run_id="run",
        timeout_seconds=2,
    )
    failed = module.run_gate(
        module.Gate("fail", f'{sys.executable} -c "raise SystemExit(3)"'),
        root=tmp_path,
        evidence_dir=tmp_path,
        run_id="run",
        timeout_seconds=2,
    )
    timed_out = module.run_gate(
        module.Gate("slow", f'{sys.executable} -c "import time; time.sleep(1)"'),
        root=tmp_path,
        evidence_dir=tmp_path,
        run_id="run",
        timeout_seconds=0.01,
    )

    assert (ok.status, ok.exit_code) == ("ok", 0)
    assert (failed.status, failed.exit_code) == ("fail", 3)
    assert (timed_out.status, timed_out.exit_code) == ("fail", 124)
    assert "exceeded" in (tmp_path / timed_out.log).read_text()


def test_atomic_json_replaces_target(load_module, tmp_path):
    module = load_module("03-verification-gate/verify.py")
    target = tmp_path / "record.json"
    target.write_text("old")

    module.write_json_atomic(target, {"ok": True})

    assert json.loads(target.read_text()) == {"ok": True}
    assert list(tmp_path.glob("*.tmp")) == []


def test_check_latest_evidence_handles_success_and_invalid_json(load_module, tmp_path):
    module = load_module("03-verification-gate/check_evidence.py")
    write_record(tmp_path, "20260714T115900Z", True)

    status, _ = module.check_latest_evidence(tmp_path, timedelta(minutes=30), now=NOW)
    assert status == 0

    (tmp_path / "20260714T115959Z.json").write_text("{")
    status, message = module.check_latest_evidence(tmp_path, timedelta(minutes=30), now=NOW)
    assert status == 2
    assert "unreadable" in message


def test_check_latest_evidence_handles_missing_and_stale_directories(load_module, tmp_path):
    module = load_module("03-verification-gate/check_evidence.py")

    missing_status, _ = module.check_latest_evidence(
        tmp_path / "missing", timedelta(minutes=30), now=NOW
    )
    stale_status, _ = module.check_latest_evidence(tmp_path, timedelta(minutes=30), now=NOW)

    assert missing_status == 2
    assert stale_status == 1


def test_verify_main_writes_passing_evidence(load_module, tmp_path, monkeypatch):
    module = load_module("03-verification-gate/verify.py")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    evidence = tmp_path / ".evidence"
    evidence.mkdir()
    (evidence / "gates.txt").write_text(f'check: {sys.executable} -c "print(42)"\n')
    monkeypatch.setattr(module, "__file__", str(scripts / "verify.py"))
    monkeypatch.setattr(module.sys, "argv", ["verify.py"])

    assert module.main() == 0
    records = list(evidence.glob("*.json"))
    assert len(records) == 1
    assert json.loads(records[0].read_text())["ok"] is True


def test_verify_main_reports_missing_gate_file(load_module, tmp_path, monkeypatch):
    module = load_module("03-verification-gate/verify.py")
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    monkeypatch.setattr(module, "__file__", str(scripts / "verify.py"))
    monkeypatch.setattr(module.sys, "argv", ["verify.py"])

    assert module.main() == 2


def test_stop_hook_emits_structured_block_decision(load_module, tmp_path, monkeypatch, capsys):
    module = load_module("04-stop-hook/no_completion_without_evidence.py")
    event = __import__("io").StringIO(json.dumps({"cwd": str(tmp_path)}))
    monkeypatch.setattr(module.sys, "stdin", event)

    assert module.main() == 0
    decision = json.loads(capsys.readouterr().out)
    assert decision["decision"] == "block"


def test_stop_hook_allows_reentry_and_background_work(load_module, monkeypatch):
    module = load_module("04-stop-hook/no_completion_without_evidence.py")

    for event in ({"stop_hook_active": True}, {"background_tasks": [{"id": "1"}]}):
        monkeypatch.setattr(module.sys, "stdin", __import__("io").StringIO(json.dumps(event)))
        assert module.main() == 0
