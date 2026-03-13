from __future__ import annotations

import re

import requests

from insta_bot.errors import ConfigurationError, ProviderError
from insta_bot.providers.base import FollowerProvider

_SERP_API_URL = "https://serpapi.com/search.json"

_MULTIPLIERS = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}


def _parse_abbrev(value: str) -> int:
    """Convert '1.2M', '234K', or '1,234,567' to an int."""
    value = value.strip().replace(",", "")
    match = re.fullmatch(r"([\d.]+)([KMB]?)", value, re.IGNORECASE)
    if not match:
        raise ValueError(f"Cannot parse: {value!r}")
    num = float(match.group(1))
    suffix = match.group(2).upper()
    return int(num * _MULTIPLIERS.get(suffix, 1))


def _find_followers_in_text(text: str) -> int | None:
    """Extract follower count from a SERP snippet string.

    Google snippets for Instagram profiles typically look like:
    '234K Followers, 180 Following, 1,234 Posts — See Instagram photos...'
    """
    m = re.search(r"([\d,\.]+[KMB]?)\s+Followers", text, re.IGNORECASE)
    if m:
        try:
            return _parse_abbrev(m.group(1))
        except ValueError:
            pass
    return None


class SerpProvider(FollowerProvider):
    """Fetches follower counts by querying SerpAPI for Google SERP snippets.

    Never contacts Instagram directly — works by reading the follower count
    that Google bakes into cached meta-description snippets.
    """

    def __init__(self, api_key: str, timeout: int = 10) -> None:
        if not api_key:
            raise ConfigurationError(
                "SERP_API_KEY is required for the serp provider."
            )
        self._api_key = api_key
        self._timeout = timeout
        self._session = requests.Session()

    def get_follower_count(self, username: str) -> int:
        params = {
            "engine": "google",
            "q": f"instagram.com/{username}",
            "api_key": self._api_key,
            "num": 5,
        }
        try:
            resp = self._session.get(_SERP_API_URL, params=params, timeout=self._timeout)
        except requests.RequestException as exc:
            raise ProviderError(
                f"SERP API request failed for @{username}: {exc}"
            ) from exc

        if resp.status_code != 200:
            raise ProviderError(
                f"SERP API returned HTTP {resp.status_code} for @{username}"
            )

        data = resp.json()

        # Check for API-level errors returned in the JSON body.
        if "error" in data:
            raise ProviderError(f"SERP API error for @{username}: {data['error']}")

        # Search through organic result snippets.
        for result in data.get("organic_results", []):
            for field in ("snippet", "description", "title"):
                count = _find_followers_in_text(result.get(field, ""))
                if count is not None:
                    return count

        raise ProviderError(
            f"No follower count found in SERP results for @{username}. "
            "The account may be private or Google has not indexed a snippet with follower data."
        )

    def close(self) -> None:
        self._session.close()
