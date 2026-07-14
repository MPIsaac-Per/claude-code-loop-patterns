# Contributing

## Development setup

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/MPIsaac-Per/claude-code-loop-patterns.git
cd claude-code-loop-patterns
uv sync --locked --dev
```

Run the same checks as CI:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest --cov=. --cov-report=term-missing
uv run pip-audit
```

## Change requirements

- Keep each pattern small enough to inspect without a framework.
- Add tests for behavior changes and failure paths.
- Link the current upstream contract when an example depends on an external API.
- Do not commit secrets, private transcripts, generated evidence, or customer data.
- Update the folder README when behavior or installation changes.

Open an issue before adding a new top-level pattern. Small fixes can go directly to a pull request.

By participating, you agree to follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
