#!/usr/bin/env python3
"""Run configured verification gates and write one atomic evidence record."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

GATE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


@dataclass(frozen=True)
class Gate:
    name: str
    command: str


@dataclass(frozen=True)
class GateResult:
    name: str
    status: str
    exit_code: int
    duration_ms: int
    log: str


def parse_gates(text: str) -> list[Gate]:
    gates: list[Gate] = []
    seen: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"line {line_number}: expected '<name>: <command>'")
        name, command = (part.strip() for part in line.split(":", 1))
        if not GATE_NAME_RE.fullmatch(name):
            raise ValueError(f"line {line_number}: gate name must match {GATE_NAME_RE.pattern!r}")
        if name in seen:
            raise ValueError(f"line {line_number}: duplicate gate name {name!r}")
        if not command:
            raise ValueError(f"line {line_number}: gate command is empty")
        seen.add(name)
        gates.append(Gate(name=name, command=command))
    if not gates:
        raise ValueError("no gates are configured")
    return gates


def write_json_atomic(path: Path, payload: dict[str, object]) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")
        temporary_path = Path(handle.name)
    os.replace(temporary_path, path)


def run_gate(
    gate: Gate,
    *,
    root: Path,
    evidence_dir: Path,
    run_id: str,
    timeout_seconds: float,
) -> GateResult:
    log_name = f"{run_id}-{gate.name}.log"
    log_path = evidence_dir / log_name
    started = time.monotonic()
    exit_code = 0
    status = "ok"
    with log_path.open("w", encoding="utf-8") as log:
        try:
            completed = subprocess.run(
                gate.command,
                cwd=root,
                shell=True,
                executable=os.environ.get("SHELL", "/bin/sh"),
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            exit_code = completed.returncode
        except subprocess.TimeoutExpired:
            exit_code = 124
            log.write(f"\nGate exceeded {timeout_seconds:g} seconds.\n")
        if exit_code != 0:
            status = "fail"
    return GateResult(
        name=gate.name,
        status=status,
        exit_code=exit_code,
        duration_ms=int((time.monotonic() - started) * 1000),
        log=log_name,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--gate-timeout-seconds",
        type=float,
        default=600,
        help="Per-gate timeout. Default: 600.",
    )
    args = parser.parse_args()
    if args.gate_timeout_seconds <= 0:
        parser.error("--gate-timeout-seconds must be greater than zero")

    root = Path(__file__).resolve().parent.parent
    evidence_dir = root / ".evidence"
    gates_file = evidence_dir / "gates.txt"
    if not gates_file.is_file():
        print(
            f"No gates file at {gates_file}. Copy gates.example.txt to get started.",
            file=sys.stderr,
        )
        return 2

    try:
        gates = parse_gates(gates_file.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"Invalid gates file: {exc}", file=sys.stderr)
        return 2

    evidence_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC)
    run_id = f"{timestamp.strftime('%Y%m%dT%H%M%S.%fZ')}-{os.getpid()}"
    results = [
        run_gate(
            gate,
            root=root,
            evidence_dir=evidence_dir,
            run_id=run_id,
            timeout_seconds=args.gate_timeout_seconds,
        )
        for gate in gates
    ]
    ok = all(result.status == "ok" for result in results)
    output_path = evidence_dir / f"{run_id}.json"
    write_json_atomic(
        output_path,
        {
            "schema_version": 1,
            "timestamp": timestamp.isoformat(),
            "ok": ok,
            "gates": [asdict(result) for result in results],
        },
    )

    print(f"Evidence: {output_path}")
    if ok:
        print("All gates passed.")
        return 0
    print("One or more gates failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
