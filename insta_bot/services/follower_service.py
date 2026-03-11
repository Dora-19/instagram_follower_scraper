from __future__ import annotations

import asyncio
import random
import time

from insta_bot.domain import FollowerResult
from insta_bot.errors import AppError
from insta_bot.infra.rate_limiter import SlidingWindowRateLimiter
from insta_bot.providers.base import FollowerProvider


class FollowerCountService:
    def __init__(
        self,
        provider: FollowerProvider,
        rate_limiter: SlidingWindowRateLimiter,
        max_retries: int,
        backoff_base_seconds: float,
    ) -> None:
        self._provider = provider
        self._rate_limiter = rate_limiter
        self._max_retries = max_retries
        self._backoff_base_seconds = backoff_base_seconds

    async def get_count(self, username: str) -> FollowerResult:
        started = time.monotonic()
        last_error: str | None = None

        for attempt in range(1, self._max_retries + 2):
            try:
                await self._rate_limiter.acquire()
                followers = await asyncio.to_thread(self._provider.get_follower_count, username)
                elapsed_ms = int((time.monotonic() - started) * 1000)
                return FollowerResult(
                    username=username,
                    followers=followers,
                    success=True,
                    attempts=attempt,
                    elapsed_ms=elapsed_ms,
                )
            except AppError as exc:
                last_error = str(exc)
            except Exception as exc:
                last_error = f"Unexpected error: {exc}"

            if attempt <= self._max_retries:
                backoff = self._backoff_base_seconds * (2 ** (attempt - 1))
                jitter = random.uniform(0, 0.2 * backoff)
                await asyncio.sleep(backoff + jitter)

        elapsed_ms = int((time.monotonic() - started) * 1000)
        return FollowerResult(
            username=username,
            followers=None,
            success=False,
            attempts=self._max_retries + 1,
            elapsed_ms=elapsed_ms,
            error=last_error,
        )
