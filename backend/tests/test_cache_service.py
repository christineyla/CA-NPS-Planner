from __future__ import annotations

from app.services import cache


class _FakeRedis:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self.storage.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self.storage[key] = value


def test_cache_round_trip(monkeypatch) -> None:
    fake = _FakeRedis()
    monkeypatch.setattr(cache, "get_redis_client", lambda: fake)

    cache.set_cached_value("parks:1:forecast", {"week": 1}, ttl_seconds=60)
    result = cache.get_cached_value("parks:1:forecast")

    assert result == {"week": 1}


def test_cache_ttl_falls_back_to_default(monkeypatch) -> None:
    monkeypatch.setenv("REDIS_CACHE_TTL_SECONDS", "bad-value")

    assert cache.get_cache_ttl_seconds() == cache.DEFAULT_CACHE_TTL_SECONDS
