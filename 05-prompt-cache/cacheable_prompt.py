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
from typing import Literal


@dataclass(frozen=True)
class CacheablePrompt:
    """A two-part prompt: a stable cacheable prefix and a dynamic suffix.

    The prefix is marked with `cache_control` so the provider can serve it
    from cache on subsequent turns. Minimum cacheable sizes vary by model;
    consult the provider's current model table before relying on cache hits.
    """

    cacheable_prefix: str
    dynamic_suffix: str = ""
    ttl: Literal["1h"] | None = None

    def __post_init__(self) -> None:
        if not self.cacheable_prefix.strip():
            raise ValueError("cacheable_prefix must not be empty")
        if self.ttl not in (None, "1h"):
            raise ValueError("ttl must be None or '1h'")

    def to_system_blocks(self) -> list[dict[str, object]]:
        cache_control: dict[str, str] = {"type": "ephemeral"}
        if self.ttl:
            cache_control["ttl"] = self.ttl

        blocks: list[dict[str, object]] = [
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
    if turns < 1:
        raise ValueError("turns must be at least 1")
    if cached_tokens < 0 or fresh_tokens_per_turn < 0:
        raise ValueError("token counts must be non-negative")

    naive = turns * (cached_tokens + fresh_tokens_per_turn)
    cached = cached_tokens + turns * fresh_tokens_per_turn
    return {
        "turns": turns,
        "naive_total_tokens": naive,
        "cached_total_tokens": cached,
        "ratio": naive / cached if cached else 0.0,
    }


if __name__ == "__main__":  # pragma: no cover - illustrative console output
    prompt = build_default_prompt(
        project_brief="A small CLI for analyzing JSONL logs. Stack: Python 3.11+, stdlib only.",
        dynamic_context="Current task: add a --since FILTER flag to the report command.",
    )
    blocks = prompt.to_system_blocks()
    print(f"system blocks: {len(blocks)}")
    for i, b in enumerate(blocks):
        cached = "cached" if b.get("cache_control") else "fresh"
        text = b["text"]
        if not isinstance(text, str):
            raise TypeError("system block text must be a string")
        print(f"  [{i}] {cached}: {len(text)} chars")
    print()
    print("Note: this demo prefix may be below the selected model's cache threshold.")
    print("Check the current prompt-caching documentation for model-specific limits.")

    print()
    print("Cache savings illustration:")
    illus = estimate_cache_savings(turns=20, cached_tokens=4000, fresh_tokens_per_turn=300)
    for k, v in illus.items():
        if isinstance(v, float):
            print(f"  {k}: {v:,.2f}")
        else:
            print(f"  {k}: {v:,}")
