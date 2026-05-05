"""cacheable_prompt: compose system prompts with cache-friendly structure.

Long agentic loops depend on context reuse via the prompt cache. The cache
only helps if the cached prefix is byte-stable across turns. Most teams
accidentally invalidate the cache by interpolating dynamic data (timestamps,
request IDs, today's date, the user's name) into the cached block.

This module gives you a tiny pattern that keeps the cacheable prefix stable
and isolates dynamic content into a labeled dynamic suffix.

Use with anthropic.Anthropic().messages.create(system=...) by passing the
output of `to_system_blocks()`.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class CacheablePrompt:
    """A two-part prompt: a stable cacheable prefix and a dynamic suffix.

    The prefix is marked with `cache_control` so the provider can serve it
    from cache on subsequent turns. Note that the prefix only actually caches
    if it meets the model's minimum token threshold (roughly 4,096 tokens for
    Opus 4.7, 2,048 for Sonnet 4.6, 1,024 for earlier models). Marking a
    short prefix with cache_control is a no-op, not an error: the response
    will show cache_creation_input_tokens=0 and cache_read_input_tokens=0.
    """

    cacheable_prefix: str
    dynamic_suffix: str = ""
    ttl: str | None = None  # None = default 5min ephemeral cache. "1h" = extended cache.

    def to_system_blocks(self) -> list[dict]:
        cache_control: dict = {"type": "ephemeral"}
        if self.ttl:
            cache_control["ttl"] = self.ttl

        blocks: list[dict] = [
            {
                "type": "text",
                "text": self.cacheable_prefix,
                "cache_control": cache_control,
            }
        ]
        if self.dynamic_suffix:
            blocks.append({"type": "text", "text": self.dynamic_suffix})
        return blocks


def build_default_prompt(*, project_brief: str, dynamic_context: str = "") -> CacheablePrompt:
    """Compose a system prompt for a long-running engineering agent.

    The cacheable prefix contains everything that does not change per turn:
    role, conventions, tool descriptions, project brief, working agreements.
    The dynamic suffix carries per-turn data: current task, recent
    observations, timestamps. Anything date-dependent must live in the suffix
    or it will bust the cache on every turn.
    """
    cacheable_prefix = textwrap.dedent(
        f"""
        You are a software engineering agent operating inside a long-running
        loop. Your job is to make verifiable progress on the current task.

        Working agreements:
          - Read before you edit.
          - Prefer structured tool output over prose.
          - Never claim done without verification evidence.
          - Keep diffs small and reviewable.
          - Treat tool failures as steering signals, not edge cases.

        Project brief:
        {project_brief.strip()}

        Tools you have are described separately by the runtime.
        """
    ).strip()

    return CacheablePrompt(
        cacheable_prefix=cacheable_prefix,
        dynamic_suffix=dynamic_context.strip(),
    )


def estimate_cache_savings(
    turns: int, cached_tokens: int, fresh_tokens_per_turn: int
) -> dict[str, int | float]:
    """Rough back-of-envelope for what caching buys you.

    Educational only; actual billing depends on provider rules. Returns a
    dict with the total tokens billed under naive (re-send everything) and
    cached (send the prefix once, replay via cache thereafter) strategies.
    """
    naive = turns * (cached_tokens + fresh_tokens_per_turn)
    cached = cached_tokens + turns * fresh_tokens_per_turn
    return {
        "turns": turns,
        "naive_total_tokens": naive,
        "cached_total_tokens": cached,
        "ratio": naive / cached if cached else 0.0,
    }


if __name__ == "__main__":
    prompt = build_default_prompt(
        project_brief="A small CLI for analyzing JSONL logs. Stack: Python 3.11+, stdlib only.",
        dynamic_context="Current task: add a --since FILTER flag to the report command.",
    )
    blocks = prompt.to_system_blocks()
    print(f"system blocks: {len(blocks)}")
    for i, b in enumerate(blocks):
        cached = "cached" if b.get("cache_control") else "fresh"
        print(f"  [{i}] {cached}: {len(b['text'])} chars")
    print()
    print("Note: this demo prefix is far below the per-model cache threshold")
    print("(roughly 4,096 tokens for Opus 4.7). The shape is correct; in")
    print("real use the prefix needs to be large enough to actually cache.")

    print()
    print("Cache savings illustration:")
    illus = estimate_cache_savings(turns=20, cached_tokens=4000, fresh_tokens_per_turn=300)
    for k, v in illus.items():
        if isinstance(v, float):
            print(f"  {k}: {v:,.2f}")
        else:
            print(f"  {k}: {v:,}")
