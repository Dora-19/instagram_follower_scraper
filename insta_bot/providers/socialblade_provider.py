from __future__ import annotations

import random
import re
import time

from curl_cffi import requests
from bs4 import BeautifulSoup

from insta_bot.errors import ProviderError
from insta_bot.providers.base import FollowerProvider

# curl_cffi handles TLS fingerprinting automatically via impersonate=.
# No custom headers needed — it sends a real Chrome header set.
_IMPERSONATE = "chrome110"

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


def _extract_count(html: str) -> int | None:
    soup = BeautifulSoup(html, "html.parser")

    # Strategy 1: find any text node containing "Followers" and look at an
    # adjacent sibling element for the numeric value.
    for node in soup.find_all(string=re.compile(r"\bFollowers\b", re.I)):
        parent = node.find_parent()
        if parent is None:
            continue
        prev = parent.find_previous_sibling()
        if prev:
            candidate = prev.get_text(strip=True)
            if re.match(r"^[\d,\.]+[KMB]?$", candidate, re.I):
                try:
                    return _parse_abbrev(candidate)
                except ValueError:
                    pass

    # Strategy 2: raw-HTML regex – handles layouts where the number and label
    # sit in adjacent tags.
    for pattern in (
        r"([\d,\.]+[KMB]?)\s*</[^>]+>\s*(?:<[^>]+>\s*)*Followers",
        r"Followers\s*</[^>]+>\s*(?:<[^>]+>\s*)*([\d,\.]+[KMB]?)",
        r"([\d,\.]+[KMB]?)\s+Followers",
    ):
        m = re.search(pattern, html, re.IGNORECASE)
        if m:
            try:
                return _parse_abbrev(m.group(1))
            except ValueError:
                pass

    return None


class SocialBladeProvider(FollowerProvider):
    def __init__(
        self,
        delay_seconds: float = 2.0,
        timeout: int = 15,
        rest_every: int = 50,
        rest_seconds: float = 45.0,
    ) -> None:
        self._delay = delay_seconds
        self._timeout = timeout
        self._rest_every = rest_every      # take a long pause every N requests
        self._rest_seconds = rest_seconds  # duration of that pause
        self._request_count = 0
        self._session = requests.Session(impersonate=_IMPERSONATE)

    def get_follower_count(self, username: str) -> int:
        # Long rest every N requests to avoid sustained-volume detection.
        if self._request_count > 0 and self._request_count % self._rest_every == 0:
            rest = random.uniform(self._rest_seconds * 0.8, self._rest_seconds * 1.2)
            print(f"[socialblade] Taking a {rest:.0f}s rest after {self._request_count} requests...")
            time.sleep(rest)

        url = f"https://socialblade.com/instagram/user/{username.lower()}"
        try:
            resp = self._session.get(url, timeout=self._timeout)
        except Exception as exc:
            raise ProviderError(
                f"Social Blade request failed for @{username}: {exc}"
            ) from exc

        self._request_count += 1

        if resp.status_code == 404:
            raise ProviderError(f"@{username} not found on Social Blade (404)")
        if resp.status_code != 200:
            raise ProviderError(
                f"Social Blade returned HTTP {resp.status_code} for @{username}"
            )

        count = _extract_count(resp.text)
        if count is None:
            raise ProviderError(
                f"Could not parse follower count from Social Blade for @{username}. "
                "The page may be behind a Cloudflare challenge or the layout changed."
            )

        # Jittered delay: ±50% of base so requests don't arrive at robotic intervals.
        jitter = random.uniform(self._delay * 0.5, self._delay * 1.5)
        time.sleep(jitter)
        return count

    def close(self) -> None:
        self._session.close()
