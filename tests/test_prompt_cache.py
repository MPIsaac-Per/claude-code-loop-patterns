from __future__ import annotations

import pytest


def test_cache_block_is_stable_and_dynamic_suffix_is_uncached(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")
    prompt = module.CacheablePrompt("stable", "per turn", ttl="1h")

    blocks = prompt.to_system_blocks()

    assert blocks[0]["cache_control"] == {"type": "ephemeral", "ttl": "1h"}
    assert "cache_control" not in blocks[1]


def test_invalid_ttl_is_rejected(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    with pytest.raises(ValueError, match="ttl"):
        module.CacheablePrompt("stable", ttl="2h")


@pytest.mark.parametrize(
    ("turns", "cached_tokens", "fresh_tokens"),
    [(0, 1, 1), (1, -1, 1), (1, 1, -1)],
)
def test_cache_estimate_rejects_invalid_inputs(
    load_module,
    turns,
    cached_tokens,
    fresh_tokens,
):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    with pytest.raises(ValueError):
        module.estimate_cache_savings(turns, cached_tokens, fresh_tokens)


def test_default_prompt_separates_project_and_dynamic_context(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    prompt = module.build_default_prompt(
        project_brief="Build a parser.",
        dynamic_context="Current task: parse JSONL.",
    )

    assert "Build a parser." in prompt.cacheable_prefix
    assert "Current task" not in prompt.cacheable_prefix
    assert prompt.dynamic_suffix == "Current task: parse JSONL."


def test_cache_estimate_returns_expected_ratio(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    estimate = module.estimate_cache_savings(2, 100, 10)

    assert estimate["naive_total_tokens"] == 220
    assert estimate["cached_total_tokens"] == 120
    assert estimate["ratio"] == pytest.approx(220 / 120)


def test_empty_cacheable_prefix_is_rejected(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    with pytest.raises(ValueError, match="empty"):
        module.CacheablePrompt("  ")


def test_default_ttl_and_empty_suffix_produce_one_block(load_module):
    module = load_module("05-prompt-cache/cacheable_prompt.py")

    blocks = module.CacheablePrompt("stable").to_system_blocks()

    assert blocks == [
        {
            "type": "text",
            "text": "stable",
            "cache_control": {"type": "ephemeral"},
        }
    ]
