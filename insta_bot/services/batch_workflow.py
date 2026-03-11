from __future__ import annotations

import asyncio
from typing import Iterable

from insta_bot.domain import FollowerResult
from insta_bot.services.follower_service import FollowerCountService


async def run_batch(
    usernames: Iterable[str],
    service: FollowerCountService,
    concurrency: int,
) -> list[FollowerResult]:
    semaphore = asyncio.Semaphore(concurrency)

    async def worker(username: str) -> FollowerResult:
        async with semaphore:
            return await service.get_count(username)

    tasks = [asyncio.create_task(worker(name)) for name in usernames]
    return await asyncio.gather(*tasks)
