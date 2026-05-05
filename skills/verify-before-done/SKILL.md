---
name: verify-before-done
description: Forces evidence-backed completion. Refuses to mark a task done without a test pass, typecheck, lint, or verification script run, even when the change feels small.
when_to_use: Trigger immediately before writing "done", "complete", "all tests pass", "I think we are good", a closing summary, removing the final TODO, or any answer to "is it done?".
allowed-tools: Bash(./scripts/verify.sh*) Bash(pnpm test*) Bash(npm test*) Bash(pytest*) Bash(cargo test*) Bash(go test*) Read
---

# Verify Before Done

You are about to declare a task complete. Stop. The article's core failure mode is **plausible completion**: you do 80% of the work, narrate the rest convincingly, and stop. Evidence is the only thing that prevents this.

## The rule

**"Done" must be tied to evidence, not tone or confidence.**

Before claiming completion, you must answer all of these questions with concrete evidence:

1. **What changed?** Specific file paths and line numbers.
2. **What command verified it?** Exact command, exit code, relevant output.
3. **What failed?** Anything you tried that did not work, even briefly.
4. **What remains untested?** Be honest, do not paper over.
5. **What assumption is still open?** Any unverified hypothesis.

## How to gather evidence

Run the project's verification harness if one exists:

```bash
./scripts/verify.sh
```

Or run gates individually:

```bash
typecheck
lint
test
```

If the project has no harness, run the closest analog (a single `pytest`, `pnpm test`, `cargo test`, or whatever is canonical) and capture the result.

## Format for the completion claim

Do not write "done" or "all tests pass" without showing the evidence. Bad:

> All done, tests pass.

Good:

> Completed. Evidence: ran `pnpm test`, 47 passed in 8.2s. Typecheck clean. Lint clean. File changes: src/foo.ts:42-58 (new function), src/bar.ts:103 (call site updated). Untested: error path when the upstream API returns 500, since I could not reproduce it locally.

If any gate failed or you skipped a check, say so explicitly. Do not declare completion.

## When to invoke

Trigger this skill whenever:

- You are about to mark a task complete or write a closing summary
- You are about to remove the final TODO from a list
- You are about to say "this should work" or "I think we are done"
- A user asks "is it done?" or "did it work?"
