---
name: loop-failure-triage
description: Structured triage after a tool call fails. Distinguishes test failure from environment, permission, not-found, and rate-limit failure, and avoids blind retry.
when_to_use: Trigger immediately after any tool call returns is_error=true, exits non-zero, returns 4xx or 5xx, times out, or contains "error", "exception", "failed", "401", "403", "404", "429", or "timeout" in its output.
allowed-tools: Read Grep Bash
---

# Loop Failure Triage

The article's fifth lesson: **errors are not edge cases, they are the work.** The best loops are not the ones with no errors; they are the ones where errors become high-quality steering signals. This skill keeps you from doing the dumb thing after a failure.

## The rule

When a tool call fails, before retrying, answer these four questions:

1. **What kind of failure?**
   - **Test failure**: a real defect in the code under test
   - **Environment failure**: missing dep, wrong PATH, port in use, expired token
   - **Permission failure**: 401, 403, sudo, file mode
   - **Not-found failure**: 404, missing file, wrong path
   - **Rate or timeout failure**: 429, network slowness, CI throttle

   Different categories need different responses. Do not retry a 401 the same way you retry a flaky test.

2. **What is the file:line citation?** If the error mentions one, name it. That is where to look first.

3. **What was the exact command?** If you are about to retry, can you make it more narrowly scoped? A failing `pnpm test` should usually become `pnpm test path/to/specific.test.ts` on the next attempt. A failing `pytest` should become `pytest tests/test_thing.py::test_case`.

4. **What changed since the last success?** If you just edited code, the failure is probably yours. If you have not edited code, suspect environment.

## What not to do

- **Do not blind-retry.** Identical command, identical inputs, expecting different output. That burns tool calls and proves nothing.
- **Do not paper over.** Wrapping a failure in try/except and pretending it succeeded is a violation of the "done" rule.
- **Do not change unrelated code** to "fix" a failure whose cause you have not located. That replaces one bug with two.
- **Do not loop on auth failures.** A 401 will keep being a 401 until credentials change. Surface it.

## What to do

- **Test failures**: read the test, read the code under test, read the failure citation, propose one minimal hypothesis, then verify.
- **Environment failures**: check the prereq (binary, env var, port, lock file), fix the environment, then retry the same command unchanged.
- **Permission failures**: stop. Permission errors waste tool calls if you keep going. Surface the auth issue to the user.
- **Not-found**: confirm the path is right and the cwd is right before assuming the resource is missing.
- **Rate or timeout**: back off, do not retry immediately, and consider whether the call needs to be smaller.

## When to invoke

Trigger this skill whenever:

- A tool call returned `is_error: true` or a non-zero exit code
- A test, build, lint, or typecheck failed
- An HTTP call returned 4xx or 5xx
- A subprocess produced "error", "exception", "failed", "timeout", or "rate limit" in its output
- A `Bash` call exited with anything other than 0
