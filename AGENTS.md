# Claude Code loop patterns

## Working agreement

Complete the requested work through verification. Make reasonable local decisions and ask only when a missing answer changes the outcome; continue independent work while waiting. Preserve user edits and carry outstanding requests across interruptions.

Use the tools and model actually available in this session. Skills supply task guidance within the user's scope and existing authorization. Keep simple work local. When delegation is authorized and useful, give workers bounded ownership, keep at most three active across the whole task, and inspect and integrate their results.

Run checks relevant to the change plus required repository gates. Broaden testing only for new changes, failures, or unresolved risk. Report the result, evidence, and actual limits in concise plain prose. Commits, pushes, publishing, messages, credential changes, and destructive actions need authorization covering the action; do not request it again when already given. Do not add agent or model attribution.

## Repository context

This repository contains Python reference implementations and Claude Code workflow samples. Editing a sample does not activate its Stop hook or make its verification ceremony the workflow for this session. Keep the Claude runtime contracts and historical research claims intact unless the task changes them.

Each numbered example should remain usable on its own with the Python standard library. Use synthetic inputs and temporary output directories; do not inspect personal session logs for routine verification.

## Verification

Python 3.11+; install development tools with `uv sync --locked --dev` when needed. Run relevant `uv run pytest` cases during development. The CI gates include `uv run ruff check .`, `uv run ruff format --check .`, the targeted mypy command in `.github/workflows/ci.yml`, and `uv run pytest --cov=. --cov-report=term-missing`. Apply them to relevant code changes; prose edits need reference checks.
