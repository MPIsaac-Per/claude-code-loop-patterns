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
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-4-7",
    system=prompt.to_system_blocks(),
    messages=[{"role": "user", "content": "Begin work."}],
    max_tokens=2048,
)
```

The cacheable prefix is sent with `cache_control={"type": "ephemeral"}` so the provider can cache it. The dynamic suffix is sent as a separate, uncached block, so per-turn values do not bust the cache.

## Caveats from the Anthropic prompt-caching contract

- **Minimum cacheable size.** A prefix only actually caches if it crosses the model's threshold: roughly 4,096 tokens for Opus 4.7, 2,048 for Sonnet 4.6, 1,024 for earlier models. Marking a short prefix with `cache_control` is a silent no-op: the response shows `cache_creation_input_tokens=0`. The example here is small for illustration; in real use the cacheable prefix needs to include enough tool definitions, conventions, and project context to clear the threshold.
- **System must be a list of blocks.** When you set `cache_control` on the system parameter, you cannot pass `system="some string"`. It must be the list-of-blocks form, which `to_system_blocks()` returns.
- **TTL.** Default ephemeral cache is 5 minutes. Pass `ttl="1h"` to opt into the longer 1-hour cache (priced at 2x base input rate). Useful when your loops outlive five minutes between turns.
- **Cache invalidation is byte-exact.** Any change to the cacheable prefix invalidates it, including a date or a request ID. The whole point of the dynamic-suffix split is to keep that prefix byte-stable across turns.
- **Up to 4 cache breakpoints.** The Anthropic API caps explicit `cache_control` markers at 4 per request. This wrapper uses 1.

## Why

The article's eighth lesson: long-running agentic coding depends on context reuse. A 585x cache-read to fresh-input ratio is achievable and changes the economics of long loops. Achieving it requires deliberate prompt structure, not luck.

Article reference: §8 (caching is infrastructure).
