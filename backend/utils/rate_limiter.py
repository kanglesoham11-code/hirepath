"""
Shared async rate limiter for GitHub API calls.

Stays under 25 search calls per 60-second window.
On 403/429, waits for retry-after or x-ratelimit-reset.
Max concurrency: 2 simultaneous requests.
"""
from __future__ import annotations

import asyncio
import logging
import time
from collections import deque

logger = logging.getLogger("hirepath.rate_limiter")


class RateLimiter:
    """Sliding-window rate limiter.

    Args:
        max_calls: Maximum number of calls allowed per window.
        window_seconds: Length of the sliding window in seconds.
        max_concurrency: Maximum concurrent requests.
    """

    def __init__(
        self,
        max_calls: int = 25,
        window_seconds: float = 60.0,
        max_concurrency: int = 2,
    ):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._timestamps: deque[float] = deque()
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a call slot is available."""
        await self._semaphore.acquire()
        while True:
            wait_time = 0.0
            async with self._lock:
                now = time.monotonic()
                # Purge timestamps older than the window
                while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.max_calls:
                    self._timestamps.append(now)
                    return

                # Window full: calculate wait time until oldest exits window
                wait_time = self._timestamps[0] + self.window_seconds - now + 0.05
                logger.info(f"Rate limiter: waiting {wait_time:.1f}s (window full)")

            self._semaphore.release()
            await asyncio.sleep(wait_time)
            await self._semaphore.acquire()

    def release(self) -> None:
        """Release the concurrency semaphore after the request completes."""
        self._semaphore.release()

    async def __aenter__(self) -> "RateLimiter":
        await self.acquire()
        return self

    async def __aexit__(self, *exc) -> None:
        self.release()

    def calls_in_window(self) -> int:
        """Return the number of calls currently in the sliding window."""
        now = time.monotonic()
        while self._timestamps and self._timestamps[0] <= now - self.window_seconds:
            self._timestamps.popleft()
        return len(self._timestamps)

    async def handle_rate_limit_response(self, status_code: int, headers: dict) -> None:
        """Handle 403 or 429 responses by sleeping until the reset time."""
        if status_code not in (403, 429):
            return

        retry_after = headers.get("retry-after")
        reset_time = headers.get("x-ratelimit-reset")

        wait = 60.0  # Default wait
        if retry_after:
            try:
                wait = float(retry_after) + 1
            except ValueError:
                pass
        elif reset_time:
            try:
                wait = max(0, float(reset_time) - time.time()) + 1
            except ValueError:
                pass

        wait = min(wait, 300)  # Cap at 5 minutes
        logger.warning(f"Rate limited ({status_code}). Waiting {wait:.0f}s")
        await asyncio.sleep(wait)


# Shared global limiter for GitHub search calls
_github_search_limiter: RateLimiter | None = None


def get_github_search_limiter() -> RateLimiter:
    """Get or create the shared GitHub search rate limiter."""
    global _github_search_limiter
    if _github_search_limiter is None:
        _github_search_limiter = RateLimiter(max_calls=25, window_seconds=60.0, max_concurrency=2)
    return _github_search_limiter


def reset_github_search_limiter() -> None:
    """Reset the limiter (for testing)."""
    global _github_search_limiter
    _github_search_limiter = None
