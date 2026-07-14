#!/usr/bin/env python3
"""Stop hook: block completion if no recent verification evidence.

Wire this into your Claude Code settings.json under hooks.Stop. The hook
reads the JSON event from stdin, checks .evidence/ for a recent successful
verification, and returns a structured block decision when the latest record
failed, is malformed, or is stale.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

MAX_AGE_MINUTES = 30
EVIDENCE_DIR_NAME = ".evidence"
TIMESTAMP_RE = re.compile(r"^(?P<timestamp>\d{8}T\d{6})(?:\.\d{6})?Z(?:-\d+)?$")


def parse_ts(name: str) -> datetime | None:
    match = TIMESTAMP_RE.fullmatch(name)
    if not match:
        return None
    return datetime.strptime(match.group("timestamp"), "%Y%m%dT%H%M%S").replace(tzinfo=UTC)


def latest_ok_evidence(evidence_dir: Path, max_age: timedelta) -> Path | None:
    if not evidence_dir.is_dir():
        return None
    cutoff = datetime.now(UTC) - max_age
    candidates: list[tuple[datetime, Path]] = []
    for path in evidence_dir.glob("*.json"):
        ts = parse_ts(path.stem)
        if ts and ts >= cutoff:
            candidates.append((ts, path))
    if not candidates:
        return None
    _, path = max(candidates, key=lambda candidate: (candidate[0], candidate[1].name))
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return path if record.get("ok") is True else None


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        event = {}

    # Reentrancy guard. Per the Claude Code hook contract, when this hook
    # blocks Stop and the agent then triggers another Stop, the second event
    # carries stop_hook_active=true. Allow that one through to avoid an
    # infinite block loop.
    if event.get("stop_hook_active"):
        return 0

    # A Stop event can arrive while background work remains active. It is not
    # a completion boundary until those tasks and scheduled callbacks finish.
    if event.get("background_tasks") or event.get("session_crons"):
        return 0

    # Resolve .evidence under the session's cwd, not the hook script's cwd,
    # so verification artifacts are found in the project root the user is
    # actually working in.
    cwd = Path(event.get("cwd") or ".")
    evidence_dir = cwd / EVIDENCE_DIR_NAME

    evidence = latest_ok_evidence(evidence_dir, timedelta(minutes=MAX_AGE_MINUTES))
    if evidence:
        return 0

    reason = (
        f"The latest verification evidence under {evidence_dir} is missing, stale, "
        f"malformed, or failed. Run ./scripts/verify.sh and confirm all gates pass "
        f"within {MAX_AGE_MINUTES} minutes before completing."
    )
    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
