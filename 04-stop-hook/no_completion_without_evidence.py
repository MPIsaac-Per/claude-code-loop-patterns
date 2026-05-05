#!/usr/bin/env python3
"""Stop hook: block completion if no recent verification evidence.

Wire this into your Claude Code settings.json under hooks.Stop. The hook
reads the JSON event from stdin (per the Claude Code hook contract), checks
.evidence/ for a recent ok=true verification, and:

  - exits 0 to allow Stop
  - exits 2 with a stderr message to block Stop and surface the reason

When blocked, Claude sees the stderr text and is expected to run verification
before retrying.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


MAX_AGE_MINUTES = 30
EVIDENCE_DIR_NAME = ".evidence"


def parse_ts(name: str) -> datetime | None:
    try:
        return datetime.strptime(name, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def latest_ok_evidence(evidence_dir: Path, max_age: timedelta) -> Path | None:
    if not evidence_dir.is_dir():
        return None
    cutoff = datetime.now(timezone.utc) - max_age
    candidates: list[tuple[datetime, Path]] = []
    for path in evidence_dir.glob("*.json"):
        ts = parse_ts(path.stem)
        if ts and ts >= cutoff:
            candidates.append((ts, path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    for _, path in candidates:
        try:
            record = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if record.get("ok"):
            return path
    return None


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

    # Resolve .evidence under the session's cwd, not the hook script's cwd,
    # so verification artifacts are found in the project root the user is
    # actually working in.
    cwd = Path(event.get("cwd") or ".")
    evidence_dir = cwd / EVIDENCE_DIR_NAME

    evidence = latest_ok_evidence(evidence_dir, timedelta(minutes=MAX_AGE_MINUTES))
    if evidence:
        return 0

    print(
        f"No verification evidence in the last {MAX_AGE_MINUTES} minutes "
        f"under {evidence_dir}. Run ./scripts/verify.sh and confirm all "
        f"gates pass before completing.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
