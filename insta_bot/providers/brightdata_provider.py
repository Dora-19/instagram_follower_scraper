from __future__ import annotations

import re
from pathlib import Path
from threading import Lock

from insta_bot.errors import ConfigurationError, ProviderError, RateLimitError
from insta_bot.providers.base import FollowerProvider


class BrightDataProvider(FollowerProvider):
    def __init__(
        self,
        cdp_url: str,
        profile_url_template: str,
        timeout_ms: int,
        storage_state_path: Path | None = None,
    ) -> None:
        if not cdp_url:
            raise ConfigurationError("BRIGHTDATA_CDP_URL cannot be empty for brightdata provider.")

        self._cdp_url = cdp_url
        self._profile_url_template = profile_url_template
        self._timeout_ms = timeout_ms
        self._storage_state_path = storage_state_path

        self._playwright_cm = None
        self._playwright = None
        self._browser = None
        self._context = None
        self._lock = Lock()

    def _ensure_connected(self) -> None:
        if self._context is not None:
            return

        try:
            from playwright.sync_api import sync_playwright
        except Exception as exc:
            raise ConfigurationError("Playwright is not installed. Run: pip install -r requirements.txt") from exc

        try:
            self._playwright_cm = sync_playwright()
            self._playwright = self._playwright_cm.start()
            self._browser = self._playwright.chromium.connect_over_cdp(self._cdp_url)

            storage_state_arg = None
            if self._storage_state_path and self._storage_state_path.exists():
                storage_state_arg = str(self._storage_state_path)

            self._context = self._browser.new_context(storage_state=storage_state_arg)
        except Exception as exc:
            self.close()
            raise ProviderError(f"Failed to connect Bright Data CDP: {exc}") from exc

    def bootstrap_login_state(self) -> None:
        with self._lock:
            self._ensure_connected()
            page = None
            try:
                page = self._context.new_page()
                page.goto(
                    "https://www.instagram.com/accounts/login/",
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                print("Login page is open in remote browser. Complete login, then press Enter here.")
                input()

                if self._storage_state_path is None:
                    raise ConfigurationError("BRIGHTDATA_STORAGE_STATE is not configured.")

                self._storage_state_path.parent.mkdir(parents=True, exist_ok=True)
                self._context.storage_state(path=str(self._storage_state_path))
                print(f"Saved storage state: {self._storage_state_path}")
            except Exception as exc:
                raise ProviderError(f"Failed to bootstrap Bright Data login state: {exc}") from exc
            finally:
                if page is not None:
                    page.close()

    def _parse_human_number(self, raw: str) -> int | None:
        cleaned = raw.strip().replace(",", "").replace(" ", "")
        match = re.match(r"^(\d+(?:\.\d+)?)([KMB]?)$", cleaned, re.IGNORECASE)
        if not match:
            digits = re.sub(r"[^0-9]", "", raw)
            return int(digits) if digits else None

        number = float(match.group(1))
        suffix = match.group(2).upper()
        factor = 1
        if suffix == "K":
            factor = 1_000
        elif suffix == "M":
            factor = 1_000_000
        elif suffix == "B":
            factor = 1_000_000_000
        return int(number * factor)

    def _extract_follower_count(self, html: str) -> int:
        meta_match = re.search(
            r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']',
            html,
            re.IGNORECASE,
        )
        if not meta_match:
            raise ProviderError("Could not find og:description meta tag.")

        content = meta_match.group(1)
        follower_match = re.search(r"([\d\.,]+[BMK]?)\s+Followers", content, re.IGNORECASE)
        if not follower_match:
            raise ProviderError("Could not parse follower count from og:description.")

        parsed = self._parse_human_number(follower_match.group(1))
        if parsed is None:
            raise ProviderError("Follower count format is not supported.")
        return parsed

    def get_follower_count(self, username: str) -> int:
        with self._lock:
            self._ensure_connected()
            page = None
            try:
                page = self._context.new_page()
                page.goto(
                    self._profile_url_template.format(username=username),
                    wait_until="domcontentloaded",
                    timeout=self._timeout_ms,
                )
                page.wait_for_timeout(1500)
                html = page.content()
                current_url = page.url.lower()

                if "Please wait a few minutes before you try again." in html:
                    raise RateLimitError("Instagram asked to wait before retrying.")
                if "/accounts/login" in current_url:
                    raise ProviderError(
                        "Instagram login wall detected. Refresh auth state with: "
                        "python3 -m insta_bot.cli brightdata-login"
                    )

                return self._extract_follower_count(html)
            except RateLimitError:
                raise
            except Exception as exc:
                raise ProviderError(f"Failed to fetch follower count for {username}: {exc}") from exc
            finally:
                if page is not None:
                    page.close()

    def close(self) -> None:
        if self._context is not None:
            try:
                self._context.close()
            except Exception:
                pass
            finally:
                self._context = None

        if self._browser is not None:
            try:
                self._browser.close()
            except Exception:
                pass
            finally:
                self._browser = None

        if self._playwright_cm is not None:
            try:
                self._playwright_cm.stop()
            except Exception:
                pass
            finally:
                self._playwright_cm = None
                self._playwright = None
