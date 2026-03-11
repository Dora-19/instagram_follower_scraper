from abc import ABC, abstractmethod


class FollowerProvider(ABC):
    @abstractmethod
    def get_follower_count(self, username: str) -> int:
        """Fetch follower count for a public profile."""

    @abstractmethod
    def close(self) -> None:
        """Clean up provider resources."""
