"""Per-store concurrency + leaky-bucket awareness (single instance; Redis in phase 2).

Docs: https://tiendanube.github.io/api-documentation/intro#rate-limiting
Bucket of 40 requests leaking 2 req/s, per store and app.
"""

import asyncio
from collections import defaultdict

import httpx

MAX_CONCURRENT_PER_STORE = 2
LOW_REMAINING_THRESHOLD = 5
LEAK_SECONDS_PER_REQUEST = 0.5

_semaphores: defaultdict[int, asyncio.Semaphore] = defaultdict(
    lambda: asyncio.Semaphore(MAX_CONCURRENT_PER_STORE)
)


def store_semaphore(store_id: int) -> asyncio.Semaphore:
    return _semaphores[store_id]


def _int_header(response: httpx.Response, name: str) -> int | None:
    value = response.headers.get(name)
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None


def throttle_delay(response: httpx.Response) -> float:
    """Seconds to wait before the next request, given the bucket headers."""
    remaining = _int_header(response, "x-rate-limit-remaining")
    if remaining is None or remaining > LOW_REMAINING_THRESHOLD:
        return 0.0
    return (LOW_REMAINING_THRESHOLD - remaining + 1) * LEAK_SECONDS_PER_REQUEST


def retry_after_429(response: httpx.Response, attempt: int) -> float:
    """`x-rate-limit-reset` is milliseconds until the bucket fully empties."""
    reset_ms = _int_header(response, "x-rate-limit-reset")
    if reset_ms is not None and reset_ms > 0:
        return min(reset_ms / 1000, 5.0)
    return min(float(2**attempt) * LEAK_SECONDS_PER_REQUEST, 5.0)
