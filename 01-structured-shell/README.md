# Structured shell wrapper

Most CLIs return either silent success or a wall of stderr. Neither is great for an LLM-driven loop. This wrapper standardizes the failure envelope: exit code, command, stdout/stderr tail, file:line citations, and a small list of diagnostic hints based on the failure pattern.

## Use

```bash
# Human-readable
python3 run_loud.py --tag test pytest -q

# Machine-readable JSON, for downstream tools
python3 run_loud.py --tag build --json npm run build
```

The exit code of `run_loud.py` matches the wrapped command, so you can drop it into any pipeline that already checks `$?`.

## Why

The article's first lesson: most "user" rows in a Claude Code transcript are tool-result carriers, not human prompts. Improving those tool results is the highest-leverage thing you can do for a long-running agent.

Article references: §1 (the user is not always the user), §5 (errors are the work).
