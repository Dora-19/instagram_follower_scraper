from __future__ import annotations

from pathlib import Path

import instaloader

from insta_bot.errors import ConfigurationError, ProviderError
from insta_bot.providers.base import FollowerProvider


class InstaloaderProvider(FollowerProvider):
    def __init__(
        self,
        login_username: str,
        login_password: str,
        session_file: Path,
    ) -> None:
        self._loader = instaloader.Instaloader()
        self._login_username = login_username
        self._login_password = login_password
        self._session_file = session_file
        self._is_authenticated = False

    def _authenticate_if_needed(self) -> None:
        if self._is_authenticated:
            return

        if self._session_file.exists():
            try:
                self._loader.load_session_from_file(
                    self._login_username,
                    filename=str(self._session_file),
                )
                self._is_authenticated = True
                return
            except Exception as exc:
                raise ProviderError(f"Failed to load session file: {exc}") from exc

        if not self._login_username or not self._login_password:
            raise ConfigurationError(
                "Session file not found. Set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD."
            )

        try:
            self._loader.login(self._login_username, self._login_password)
            self._loader.save_session_to_file(filename=str(self._session_file))
            self._is_authenticated = True
        except Exception as exc:
            raise ProviderError(f"Instagram login failed: {exc}") from exc

    def get_follower_count(self, username: str) -> int:
        self._authenticate_if_needed()
        try:
            profile = instaloader.Profile.from_username(self._loader.context, username)
            return int(profile.followers)
        except Exception as exc:
            raise ProviderError(f"Failed to fetch follower count for {username}: {exc}") from exc

    def close(self) -> None:
        return None
