from __future__ import annotations

import logging

from insta_bot.errors import ProviderError
from insta_bot.providers.base import FollowerProvider

logger = logging.getLogger(__name__)


class ChainedProvider(FollowerProvider):
    """Tries the primary provider first; on ProviderError falls back to secondary."""

    def __init__(self, primary: FollowerProvider, fallback: FollowerProvider) -> None:
        self._primary = primary
        self._fallback = fallback

    def get_follower_count(self, username: str) -> int:
        try:
            return self._primary.get_follower_count(username)
        except ProviderError as exc:
            logger.warning(
                "Primary provider failed for @%s (%s) — trying fallback.", username, exc
            )
            return self._fallback.get_follower_count(username)

    def close(self) -> None:
        self._primary.close()
        self._fallback.close()
