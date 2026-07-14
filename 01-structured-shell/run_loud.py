#!/usr/bin/env python3
"""run_loud: run a shell command and produce legible structured output.

Most CLIs return one of:
  - 0 and stdout (silent success, easy)
  - non-zero and noisy stderr (hard to parse, often pages long)

This wrapper standardizes the failure envelope so a downstream agent (or
human) can extract: command, exit_code, stdout/stderr tails, file:line
citations, and diagnostic hints. Pass any command:

    python3 run_loud.py pytest -q
    python3 run_loud.py --json pytest -q
    python3 run_loud.py --tag build npm run build

Designed to be cheap, readable, and friendly to both eyes and parsers.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field

FILE_LINE_RE = re.compile(
    r"(?P<path>[A-Za-z0-9_./\\-]+\.[A-Za-z0-9]+):(?P<line>\d+)(?::(?P<col>\d+))?"
)


@dataclass
class RunResult:
    command: list[str]
    exit_code: int
    duration_ms: int
    tag: str | None
    stdout_tail: list[str]
    stderr_tail: list[str]
    file_line_citations: list[str] = field(default_factory=list)
    diagnostic_hints: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def tail(text: str, n: int) -> list[str]:
    if not text or n <= 0:
        return []
    return text.splitlines()[-n:]


def extract_citations(text: str, limit: int = 8) -> list[str]:
    seen: list[str] = []
    for m in FILE_LINE_RE.finditer(text or ""):
        cite = f"{m.group('path')}:{m.group('line')}"
        if cite not in seen:
            seen.append(cite)
            if len(seen) >= limit:
                break
    return seen


def make_hints(stderr: str, exit_code: int) -> list[str]:
    hints: list[str] = []
    if exit_code == 127:
        hints.append("exit 127: command not found. Check PATH or install the tool.")
    if exit_code == 126:
        hints.append("exit 126: command not executable. Check file permissions.")
    if exit_code == 130:
        hints.append("exit 130: interrupted (Ctrl-C). Re-run if unintentional.")
    if exit_code == 124:
        hints.append(
            "exit 124: command timed out. Raise the timeout or inspect the command for a hang."
        )
    lower = (stderr or "").lower()
    if "permission denied" in lower:
        hints.append("Permission denied detected. Check file ownership or sudo.")
    if "no such file or directory" in lower:
        hints.append("Missing file or directory referenced. Check path and cwd.")
    if "address already in use" in lower:
        hints.append("Port already bound. Find the holder with `lsof -i:<port>`.")
    if "cannot find module" in lower or "modulenotfounderror" in lower:
        hints.append("Missing dependency. Check installer (pip, pnpm, uv) and lockfile.")
    if "401" in lower or "unauthorized" in lower:
        hints.append("Auth failure. Re-issue the token or refresh credentials before retry.")
    if "429" in lower or "rate limit" in lower:
        hints.append("Rate limited. Back off before retry; do not loop on this.")
    return hints


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def run(
    command: list[str],
    tag: str | None,
    tail_lines: int,
    timeout_seconds: float | None = 300,
) -> RunResult:
    started = time.monotonic()
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
        exit_code = proc.returncode
        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
    except FileNotFoundError as exc:
        exit_code = 127
        stderr = str(exc)
        stdout = ""
    except PermissionError as exc:
        exit_code = 126
        stderr = str(exc)
        stdout = ""
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stderr = _as_text(exc.stderr)
        stdout = _as_text(exc.stdout)
        stderr = f"{stderr}\nCommand exceeded {timeout_seconds:g} seconds.".lstrip()
    duration_ms = int((time.monotonic() - started) * 1000)

    return RunResult(
        command=command,
        exit_code=exit_code,
        duration_ms=duration_ms,
        tag=tag,
        stdout_tail=tail(stdout, tail_lines),
        stderr_tail=tail(stderr, tail_lines),
        file_line_citations=extract_citations(stderr + "\n" + stdout),
        diagnostic_hints=make_hints(stderr, exit_code),
    )


def render_human(r: RunResult) -> str:
    status = "OK" if r.ok else f"FAIL (exit {r.exit_code})"
    lines = [
        f"[{r.tag or 'run'}] {shlex.join(r.command)}",
        f"  status: {status}  duration: {r.duration_ms} ms",
    ]
    if r.file_line_citations:
        lines.append(f"  citations: {', '.join(r.file_line_citations)}")
    if r.diagnostic_hints:
        lines.append("  hints:")
        for h in r.diagnostic_hints:
            lines.append(f"    - {h}")
    if not r.ok and r.stderr_tail:
        lines.append("  stderr (tail):")
        for line in r.stderr_tail:
            lines.append(f"    {line}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a command with structured output.")
    parser.add_argument("--tag", help="Optional label for this run, e.g. test, build.")
    parser.add_argument(
        "--json", action="store_true", help="Emit JSON to stdout instead of human-readable text."
    )
    parser.add_argument(
        "--tail-lines", type=int, default=30, help="Lines of stdout/stderr to keep in the tail."
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=300,
        help="Kill the command after this many seconds. Default: 300.",
    )
    parser.add_argument("command", nargs=argparse.REMAINDER, help="Command and args to run.")
    args = parser.parse_args()

    if not args.command:
        parser.error("no command given")
    if args.tail_lines < 0:
        parser.error("--tail-lines must be zero or greater")
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be greater than zero")

    result = run(
        args.command,
        tag=args.tag,
        tail_lines=args.tail_lines,
        timeout_seconds=args.timeout_seconds,
    )

    if args.json:
        print(json.dumps(asdict(result), indent=2))
    else:
        stream = sys.stdout if result.ok else sys.stderr
        print(render_human(result), file=stream)

    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
