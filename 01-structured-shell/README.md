# Structured shell wrapper

Most CLIs return either silent success or a wall of stderr. Neither is great for an LLM-driven loop. This wrapper standardizes the failure envelope: exit code, command, stdout/stderr tail, file:line citations, and a small list of diagnostic hints based on the failure pattern.

## Use

```bash
# Human-readable
python3 run_loud.py --tag test pytest -q

# Machine-readable JSON, for downstream tools
python3 run_loud.py --tag build --json npm run build

# Bound a command that may hang
python3 run_loud.py --timeout-seconds 120 --tag test pytest -q
```

The exit code of `run_loud.py` matches the wrapped command, so you can drop it into any pipeline that already checks `$?`.

## Why

Most "user" rows in a Claude Code transcript are tool-result carriers rather than human prompts. Clear tool results give the next loop iteration usable state.

Article references: §1 (the user is not always the user), §5 (errors are the work).
