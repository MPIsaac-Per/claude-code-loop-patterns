---
name: read-before-edit
description: Forces context-gathering before code mutation. Reads the file, finds call sites, reads adjacent tests, and checks config before any non-trivial edit.
when_to_use: Trigger before any non-trivial Edit or Write on a file you have not read this session, or whenever you catch yourself drafting an edit from memory or pattern-matching from a similar codebase.
allowed-tools: Read Grep Glob
---

# Read Before Edit

The article's third lesson: **most engineering is reading.** The model that patches fastest is rarely the one you want; the one that builds enough context first usually produces a smaller, correct diff with fewer follow-ups.

## The rule

Before any non-trivial edit:

1. **Read the file you intend to change**, end to end if it is small (under 300 lines), or the relevant section plus its imports otherwise.
2. **Find the call sites.** Grep for the function or symbol you are touching to see who calls it and what they expect.
3. **Read the closest test file.** If one exists, the tests document the contract. Edits that break tests usually break the contract.
4. **Check the config.** If behavior is configurable, find where the config is loaded and what the defaults are.

## What counts as non-trivial

- Adding a new branch to a conditional
- Changing a function signature or return type
- Modifying error handling
- Touching shared state, caches, or globals
- Editing migrations, schemas, or types
- Anything in code you did not write today

A pure rename, a typo fix in a string, or adding a missing comma is trivial. Edit freely.

## What this is not

Not ceremony. Not "read everything in the repo." Bounded, purposeful reading: file, callers, tests, config. Usually four to ten reads. Stop when you have enough mental model to predict what your edit will do and what tests it will affect.

## When to invoke

Trigger this skill whenever:

- You are about to call Edit or Write on a file you have not yet read in this session
- You catch yourself drafting an edit from memory or pattern-matching from a similar codebase
- You are touching a function whose call sites or tests you cannot name
- You are tempted to "fix" surrounding code that was not part of the original task
