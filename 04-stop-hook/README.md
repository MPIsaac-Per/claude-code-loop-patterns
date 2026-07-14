# Stop hook: no completion without evidence

A Claude Code Stop hook that blocks completion unless the newest recent verification record passed. Pairs with [`../03-verification-gate/`](../03-verification-gate).

## Install

1. Copy `no_completion_without_evidence.py` somewhere stable, for example `~/.claude/hooks/no_completion_without_evidence.py`.
2. Make it executable: `chmod +x no_completion_without_evidence.py`.
3. Add the entry from `settings.example.json` to your project `.claude/settings.json` or user `~/.claude/settings.json`.

The hook reads the JSON event from stdin, checks `.evidence/`, and:

- exits 0 to allow Stop
- emits `{"decision":"block","reason":"..."}` with exit 0 to block Stop

When blocked, Claude receives the reason and can run verification before retrying.

## Tune

The two knobs are at the top of the file:

- `MAX_AGE_MINUTES`: how recent the evidence has to be (default 30)
- `EVIDENCE_DIR_NAME`: where to look under the session working directory (default `.evidence`)

For a stricter posture, drop max-age to 5 minutes; for a looser one, raise to 60.

## Notes from the Claude Code hook contract

- **Stop has no `matcher`.** The Stop event always fires; per the docs, "if you add a `matcher` field to these events, it is silently ignored." The `settings.example.json` here omits it accordingly.
- **Reentrancy guard.** The hook reads `stop_hook_active` from the event JSON. When true, Claude is already inside a blocked Stop attempt and the hook allows stopping.
- **Background work.** The hook allows Stop while `background_tasks` or `session_crons` remain active because that event is not a final completion boundary.
- **Cwd resolution.** The hook resolves `.evidence/` under `event["cwd"]`, not the hook script's own working directory, so it finds verification artifacts in the project root the session is using.
- **Structured decision.** The implementation returns the documented JSON decision shape on stdout.
- **Newest run wins.** A newer failed or malformed record invalidates an older successful record.

Contract reference: [Claude Code hooks](https://code.claude.com/docs/en/hooks).

## Why

The hook turns verification from a convention into an enforced completion condition.

Article reference: §10 (plausible completion).
