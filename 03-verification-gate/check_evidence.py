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
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


def parse_ts(name: str) -> datetime | None:
    try:
        return datetime.strptime(name, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-dir", default=".evidence", type=Path)
    parser.add_argument("--max-age-minutes", type=int, default=30)
    args = parser.parse_args()

    if not args.evidence_dir.is_dir():
        print(f"No evidence directory at {args.evidence_dir}", file=sys.stderr)
        return 2

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=args.max_age_minutes)
    candidates: list[tuple[datetime, Path]] = []
    for path in args.evidence_dir.glob("*.json"):
        ts = parse_ts(path.stem)
        if ts and ts >= cutoff:
            candidates.append((ts, path))

    if not candidates:
        print(f"No evidence in the last {args.max_age_minutes} min.", file=sys.stderr)
        return 1

    candidates.sort(reverse=True)
    latest_ts, latest = candidates[0]
    try:
        record = json.loads(latest.read_text())
    except json.JSONDecodeError as exc:
        print(f"Latest evidence at {latest} is unreadable: {exc}", file=sys.stderr)
        return 2

    if not record.get("ok"):
        print(f"Latest evidence at {latest_ts.isoformat()} reports failure.", file=sys.stderr)
        return 1

    print(f"Evidence ok at {latest_ts.isoformat()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
