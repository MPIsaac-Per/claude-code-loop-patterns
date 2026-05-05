# Skills

Three Claude Code skills that codify the article's loop rules so the agent invokes them on the right turn. Each skill is a single `SKILL.md` with frontmatter (`name`, `description`) plus instructions in the body.

## Install

Copy any skill folder into one of these locations:

- **Project**: `.claude/skills/<skill-name>/SKILL.md`
- **User**: `~/.claude/skills/<skill-name>/SKILL.md`

Claude Code discovers skills by directory and uses the `description` frontmatter field to decide when to invoke them. Tweak the descriptions for your own project's vocabulary so the right skill fires on the right turn.

## Skills in this repo

| Skill | When it fires | Codifies |
|---|---|---|
| [`verify-before-done`](./verify-before-done) | About to declare a task complete | §10: never let "done" mean "the model says it is done" |
| [`read-before-edit`](./read-before-edit) | About to edit a file in unfamiliar code | §3: most engineering is reading |
| [`loop-failure-triage`](./loop-failure-triage) | A tool call just failed | §5: errors are not edge cases, they are the work |

## Why these three

The article identifies three places where loops most commonly fail: the moment of "done" (§10), the moment of edit (§3), and the moment after a failed tool call (§5). One skill per failure surface, deliberately scoped, so the agent has clear, invokable rules at each decision point instead of a single long instruction file that gets ignored.
