"""
In-Memory LRU Cache with TTL — no Redis required for single-worker deployments.

Cache keys:
  search:{sha256(query+filters+page)}  → result list, TTL=300s
  embedding:{sha256(text)}             → numpy array,  TTL=3600s
  graph_score:{sha256(query)}          → score dict,   TTL=300s

Multi-worker note: Each Uvicorn worker maintains its own independent LRU.
For multi-process deployments, upgrade to Redis (P3 item in the roadmap).
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any, Optional


class _CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, ttl: float):
        self.value = value
        self.expires_at = time.monotonic() + ttl


class LRUCache:
    """
    Thread-safe LRU cache with per-entry TTL eviction.

    Parameters
    ----------
    maxsize : int
        Maximum number of entries before LRU eviction kicks in.
    default_ttl : float
        Default time-to-live in seconds for entries without an explicit TTL.
    """

    def __init__(self, maxsize: int = 1000, default_ttl: float = 300.0):
        self._maxsize = maxsize
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, _CacheEntry] = OrderedDict()

        # Stats
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Optional[Any]:
        """Return cached value or None on miss/expiry."""
        entry = self._cache.get(key)
        if entry is None:
            self._misses += 1
            return None

        if time.monotonic() > entry.expires_at:
            # Expired — remove and count as miss
            self._cache.pop(key, None)
            self._misses += 1
            return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Store a value under key with optional TTL."""
        effective_ttl = ttl if ttl is not None else self._default_ttl

        if key in self._cache:
            self._cache.move_to_end(key)
        self._cache[key] = _CacheEntry(value, effective_ttl)

        # Evict LRU entries if over capacity
        while len(self._cache) > self._maxsize:
            self._cache.popitem(last=False)
            self._evictions += 1

    def invalidate(self, key: str):
        """Remove a single key from the cache."""
        self._cache.pop(key, None)

    def clear(self):
        """Flush the entire cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    @property
    def stats(self) -> dict:
        total = self._hits + self._misses
        hit_rate = round(self._hits / total, 4) if total else 0.0
        return {
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "size": len(self._cache),
            "maxsize": self._maxsize,
            "hit_rate": hit_rate,
        }

    # ------------------------------------------------------------------
    # Key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_search_key(query: str, filters: dict, page: int, limit: int) -> str:
        raw = f"{query}|{sorted(filters.items())}|{page}|{limit}"
        return "search:" + hashlib.sha256(raw.encode()).hexdigest()

    @staticmethod
    def make_embedding_key(text: str) -> str:
        return "embedding:" + hashlib.sha256(text.encode()).hexdigest()

    @staticmethod
    def make_graph_score_key(query: str) -> str:
        return "graph_score:" + hashlib.sha256(query.encode()).hexdigest()


# ------------------------------------------------------------------
# Module-level singleton (imported by main.py)
# ------------------------------------------------------------------
cache = LRUCache(maxsize=1000, default_ttl=300.0)
