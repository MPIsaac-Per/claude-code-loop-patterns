#!/usr/bin/env python3
"""check_evidence: assert recent successful verification evidence exists.

Usage:
    python3 check_evidence.py --max-age-minutes 30

Exits 0 if a `.evidence/<timestamp>.json` from the last N minutes shows ok=true.
Exits non-zero otherwise. Use this in pre-commit hooks, CI guards, or Stop
hooks to enforce 'done means verified.'
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

TIMESTAMP_RE = re.compile(r"^(?P<timestamp>\d{8}T\d{6})(?:\.\d{6})?Z(?:-\d+)?$")


def parse_ts(name: str) -> datetime | None:
    match = TIMESTAMP_RE.fullmatch(name)
    if not match:
        return None
    return datetime.strptime(match.group("timestamp"), "%Y%m%dT%H%M%S").replace(tzinfo=UTC)


def check_latest_evidence(
    evidence_dir: Path,
    max_age: timedelta,
    *,
    now: datetime | None = None,
) -> tuple[int, str]:
    if not evidence_dir.is_dir():
        return 2, f"No evidence directory at {evidence_dir}"

    cutoff = (now or datetime.now(UTC)) - max_age
    candidates: list[tuple[datetime, Path]] = []
    for path in evidence_dir.glob("*.json"):
        ts = parse_ts(path.stem)
        if ts and ts >= cutoff:
            candidates.append((ts, path))

    if not candidates:
        minutes = int(max_age.total_seconds() / 60)
        return 1, f"No evidence in the last {minutes} min."

    latest_ts, latest = max(candidates, key=lambda candidate: (candidate[0], candidate[1].name))
    try:
        record = json.loads(latest.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        return 2, f"Latest evidence at {latest} is unreadable: {exc}"

    if not record.get("ok"):
        return 1, f"Latest evidence at {latest_ts.isoformat()} reports failure."

    return 0, f"Evidence ok at {latest_ts.isoformat()}."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", default=".evidence", type=Path)
    parser.add_argument("--max-age-minutes", type=int, default=30)
    args = parser.parse_args()

    if args.max_age_minutes <= 0:
        parser.error("--max-age-minutes must be greater than zero")

    status, message = check_latest_evidence(
        args.evidence_dir,
        timedelta(minutes=args.max_age_minutes),
    )
    print(message, file=sys.stdout if status == 0 else sys.stderr)
    return status


if __name__ == "__main__":
    sys.exit(main())
