import json

from autogen.agentchat.contrib.capabilities.transforms import TextMessageCompressor


class InMemoryCache:
    """Minimal cache with the same get/set interface used by TextMessageCompressor."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value):
        self.store[key] = value


class DummyTextCompressor:
    """Deterministic compressor that makes it easy to observe caching behavior."""

    def __init__(self):
        self.calls = 0

    def compress_text(self, text: str, **kwargs):
        self.calls += 1
        # Return a fixed "compressed" prompt, token counts don't matter for this test.
        return {"compressed_prompt": f"COMPRESSED({text})", "origin_tokens": 10, "compressed_tokens": 5}


def test_text_message_compressor_cache_key_includes_min_tokens_for_set_and_get():
    """
    Review intent: cache key must align with _cache_get and include min_tokens:
      key = f"{json.dumps(content)}_{self._min_tokens}"

    This test verifies runtime behavior: after a transform run, the cache entry must be stored
    under a key that includes the min_tokens suffix.
    """
    cache = InMemoryCache()
    dummy = DummyTextCompressor()

    compressor = TextMessageCompressor(text_compressor=dummy, min_tokens=1, cache=cache)

    content = "hello world"
    messages = [{"role": "user", "content": content}]
    out = compressor.apply_transform(messages)

    assert out[0]["content"] == "COMPRESSED(hello world)", "Sanity check: message should be compressed."

    expected_key = f"{json.dumps(content)}_{compressor._min_tokens}"
    assert (
        expected_key in cache.store
    ), f"Cache key should include min_tokens suffix to align with _cache_get. Expected key '{expected_key}' to exist."

    # Ensure the stored value can be retrieved via the module's own cache-get logic (uses its internal keying).
    cached = compressor._cache_get(content)
    assert cached is not None, "Compressor should be able to read back cached value using its own _cache_get."
    tokens_saved, cached_compressed_json = cached
    assert tokens_saved == 5, "Cached value should preserve tokens_saved as stored by _cache_set."
    assert json.loads(cached_compressed_json) == "COMPRESSED(hello world)", "Cached compressed content should match."