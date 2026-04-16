"""
Structured Logging & Observability — JSON-formatted request logs with per-request
latency tracking, intent classification tagging, and aggregate metrics.

Uses loguru for simple structured JSON output.
Fallback: if loguru is not installed, uses stdlib logging.
"""
from __future__ import annotations

import time
import uuid
import statistics
from collections import deque
from typing import Optional

try:
    from loguru import logger as _loguru_logger
    _USE_LOGURU = True
except ImportError:
    import logging as _stdlib_logging
    import json as _json
    _USE_LOGURU = False

# ---------------------------------------------------------------------------
# Internal metrics store (in-memory ring buffer — last 10,000 requests)
# ---------------------------------------------------------------------------
_MAX_LATENCY_SAMPLES = 10_000
_latencies: deque[float] = deque(maxlen=_MAX_LATENCY_SAMPLES)
_total_requests: int = 0
_cache_hits: int = 0
_cache_misses: int = 0
_node2vec_ready: bool = False
_embeddings_ready: bool = False


# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------
def _emit(record: dict):
    """Emit a JSON log line via loguru or stdlib."""
    if _USE_LOGURU:
        _loguru_logger.info(record)
    else:
        import json
        import logging
        logging.getLogger("alumni_search").info(json.dumps(record, default=str))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def log_request(
    endpoint: str,
    query: Optional[str],
    intent: Optional[str],
    latency_ms: float,
    result_count: int,
    cache_hit: bool,
    request_id: Optional[str] = None,
    extra: Optional[dict] = None,
):
    """
    Emit one structured JSON log line per API request.

    Parameters
    ----------
    endpoint    : API path, e.g. "/api/search"
    query       : The raw search query text (may be None for non-search endpoints)
    intent      : Classified intent: "SEMANTIC" | "STRUCTURED" | "GRAPH" | None
    latency_ms  : End-to-end request latency in milliseconds
    result_count: Number of results returned
    cache_hit   : Whether the response was served from cache
    request_id  : UUID for distributed tracing (generated if not supplied)
    extra       : Any additional key-value pairs to include in the log
    """
    global _total_requests, _cache_hits, _cache_misses

    rid = request_id or str(uuid.uuid4())
    _total_requests += 1
    _latencies.append(latency_ms)

    if cache_hit:
        _cache_hits += 1
    else:
        _cache_misses += 1

    record: dict = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "request_id": rid,
        "endpoint": endpoint,
        "query": query,
        "intent": intent,
        "latency_ms": round(latency_ms, 2),
        "result_count": result_count,
        "cache_hit": cache_hit,
    }

    if extra:
        record.update(extra)

    if latency_ms > 500:
        if _USE_LOGURU:
            _loguru_logger.warning(f"[SLOW QUERY] {record}")
        else:
            import logging, json
            logging.getLogger("alumni_search").warning(f"[SLOW QUERY] {json.dumps(record, default=str)}")
    else:
        _emit(record)

    return rid


def set_node2vec_ready(ready: bool):
    """Called by the background Node2Vec thread when embeddings are complete."""
    global _node2vec_ready
    _node2vec_ready = ready


def set_embeddings_ready(ready: bool):
    """Called during startup once SBERT + FAISS are loaded."""
    global _embeddings_ready
    _embeddings_ready = ready


def get_metrics(cache_stats: Optional[dict] = None) -> dict:
    """
    Return aggregate statistics for the /api/metrics endpoint.

    Parameters
    ----------
    cache_stats : Optional stats dict from cache_manager.cache.stats
    """
    if _latencies:
        avg_latency = round(statistics.mean(_latencies), 2)
        sorted_lats = sorted(_latencies)
        p95_idx = min(int(len(sorted_lats) * 0.95), len(sorted_lats) - 1)
        p99_idx = min(int(len(sorted_lats) * 0.99), len(sorted_lats) - 1)
        p95_latency = round(sorted_lats[p95_idx], 2)
        p99_latency = round(sorted_lats[p99_idx], 2)
    else:
        avg_latency = p95_latency = p99_latency = 0.0

    total = _cache_hits + _cache_misses
    hit_rate = round(_cache_hits / total, 4) if total else 0.0

    metrics: dict = {
        "total_requests": _total_requests,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "p99_latency_ms": p99_latency,
        "cache_hit_rate": hit_rate,
        "cache_hits": _cache_hits,
        "cache_misses": _cache_misses,
        "node2vec_ready": _node2vec_ready,
        "embeddings_ready": _embeddings_ready,
    }

    if cache_stats:
        metrics["cache_stats"] = cache_stats

    return metrics
