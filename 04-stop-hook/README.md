# Stop hook: no completion without evidence

A Claude Code Stop hook that blocks completion if no recent successful verification evidence exists. Pairs with [`../03-verification-gate/`](../03-verification-gate).

## Install

1. Copy `no_completion_without_evidence.py` somewhere stable, for example `~/.claude/hooks/no_completion_without_evidence.py`.
2. Make it executable: `chmod +x no_completion_without_evidence.py`.
3. Add the entry from `settings.example.json` to your project `.claude/settings.json` or user `~/.claude/settings.json`.

The hook reads the JSON event from stdin (per the Claude Code hook contract), checks `.evidence/` for a recent ok=true verification, and:

- exits 0 to allow Stop
- exits 2 with a stderr message to block Stop and surface the reason

When blocked, Claude sees the stderr text and is expected to run verification before retrying.

## Tune

The two knobs are at the top of the file:

- `MAX_AGE_MINUTES`: how recent the evidence has to be (default 30)
- `EVIDENCE_DIR`: where to look (default `.evidence`)

For a stricter posture, drop max-age to 5 minutes; for a looser one, raise to 60.

## Notes from the Claude Code hook contract

- **Stop has no `matcher`.** The Stop event always fires; per the docs, "if you add a `matcher` field to these events, it is silently ignored." The `settings.example.json` here omits it accordingly.
- **Reentrancy guard.** The hook reads `stop_hook_active` from the event JSON. When true (Claude is already inside a blocked Stop attempt), the hook allows stopping. Without this guard a project that never produces evidence would block forever.
- **Cwd resolution.** The hook resolves `.evidence/` under `event["cwd"]`, not the hook script's own working directory, so it finds verification artifacts in the project root the session is using.
- **Two ways to block.** This implementation uses exit code 2 with stderr (the portable path). The equivalent JSON-on-stdout form is `{"decision": "block", "reason": "..."}` returned with exit 0. Either is supported.

## Why

The article's tenth lesson made concrete: the loop should not be allowed to end on vibes. The evidence is the receipt; the hook is the bouncer.

Article reference: §10 (plausible completion).
