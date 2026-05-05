# claude-code-loop-patterns

Companion code for **What I Learned From 245,306 Claude Code Tool Calls**.

The article's argument: Claude Code is not a chat product with tools attached, it is an operating loop, and the new high-leverage skill is loop design. This repo is a small cookbook of working loop primitives. Drop any folder into your own project as a starting point.

## Code samples

| Folder | Pattern | Article section |
|---|---|---|
| [`01-structured-shell/`](./01-structured-shell) | A shell wrapper that emits structured success/failure with file:line citations and diagnostic hints. | §1, §5 |
| [`02-structured-tests/`](./02-structured-tests) | A pytest plugin that emits one JSONL line per test, with structured failure data. | §5 |
| [`03-verification-gate/`](./03-verification-gate) | A verification harness that runs gates and writes evidence files for downstream "done" enforcement. | §10, §11 |
| [`04-stop-hook/`](./04-stop-hook) | A Claude Code Stop hook that blocks completion when no recent verification evidence exists. | §10 |
| [`05-prompt-cache/`](./05-prompt-cache) | A prompt builder that keeps the cacheable prefix byte-stable and isolates dynamic content. | §8 |

## Skills

The [`skills/`](./skills) directory ships three Claude Code skills that codify the loop rules so the agent invokes them on the right turn:

| Skill | When it fires |
|---|---|
| [`verify-before-done`](./skills/verify-before-done) | About to declare a task complete (§10) |
| [`read-before-edit`](./skills/read-before-edit) | About to edit a file you have not read (§3) |
| [`loop-failure-triage`](./skills/loop-failure-triage) | A tool call just failed (§5) |

## Run

Each sample is self-contained. Most use only the Python standard library (3.10+).

```bash
git clone https://github.com/MPIsaac-Per/claude-code-loop-patterns
cd claude-code-loop-patterns
python3 01-structured-shell/run_loud.py --tag test pytest -q
```

## What is and isn't novel here

Most of these patterns have prior art. The contribution of this repo is the composition: a small set of primitives that compose into a verifiable, auditable agent loop without any framework.

- **Genuinely novel composition**: the Stop-hook-plus-evidence-file integration in `04-stop-hook` (refusing to allow Stop until a recent verified run exists), and the three-skill loop-discipline set in `skills/` (one skill per failure surface from the article: done, edit, fail).
- **Reference implementations of known patterns**: `01-structured-shell/run_loud.py` (subprocess wrappers like this exist in many forms; this one specializes the failure envelope for LLM consumption); `02-structured-tests/pytest_jsonl_reporter.py` (`pytest-json-report` is more mature, see that folder's README); `05-prompt-cache/cacheable_prompt.py` (the cache-friendly system prompt pattern is documented in the official Anthropic prompt-caching guide; this is a small convenience wrapper that exposes the TTL knob).
- **Validated against current docs**: the hook contract (matcher rules, exit codes, `stop_hook_active` reentrancy), the skill frontmatter (`name`, `description`, `when_to_use`, `allowed-tools`), and the `cache_control` shape were taken from the live Claude Code and Anthropic docs at time of writing, not assumed from training data.

## License

MIT.
