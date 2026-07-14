# Cache-friendly prompt assembly

Most teams accidentally invalidate the prompt cache by interpolating per-turn data (timestamps, request IDs, today's date) into the cached system prompt. This module gives you a tiny pattern that keeps the cacheable prefix byte-stable and isolates dynamic content into a labeled suffix.

## Use

```python
from cacheable_prompt import build_default_prompt

prompt = build_default_prompt(
    project_brief="A CLI for analyzing JSONL logs. Stack: Python 3.11+.",
    dynamic_context="Current task: add a --since FILTER flag to the report command.",
)

# Pass to the Anthropic SDK as the system parameter:
import os
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model=os.environ["ANTHROPIC_MODEL"],
    system=prompt.to_system_blocks(),
    messages=[{"role": "user", "content": "Begin work."}],
    max_tokens=2048,
)
```

The cacheable prefix is sent with `cache_control={"type": "ephemeral"}` so the provider can cache it. The dynamic suffix is sent as a separate, uncached block, so per-turn values do not bust the cache.

## Caveats from the Anthropic prompt-caching contract

- **Minimum cacheable size.** Thresholds vary by model and can change as new models ship. Check the [current prompt-caching model table](https://platform.claude.com/docs/en/build-with-claude/prompt-caching). A short prefix marked with `cache_control` is accepted but produces no cache read or creation tokens.
- **System must be a list of blocks.** When you set `cache_control` on the system parameter, you cannot pass `system="some string"`. It must be the list-of-blocks form, which `to_system_blocks()` returns.
- **TTL.** The default ephemeral cache is 5 minutes. Pass `ttl="1h"` for the supported extended cache. Check current pricing before using the extended TTL at scale.
- **Cache invalidation is byte-exact.** Any change to the cacheable prefix invalidates it, including a date or a request ID. The whole point of the dynamic-suffix split is to keep that prefix byte-stable across turns.
- **Up to 4 cache breakpoints.** The Anthropic API caps explicit `cache_control` markers at 4 per request. This wrapper uses 1.

## Why

The article's eighth lesson: long-running agentic coding depends on context reuse. A 585x cache-read to fresh-input ratio is achievable and changes the economics of long loops. Achieving it requires deliberate prompt structure, not luck.

Article reference: §8 (caching is infrastructure).
