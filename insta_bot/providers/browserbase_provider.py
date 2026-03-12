from __future__ import annotations

import json
import re
from threading import Lock

from insta_bot.errors import ConfigurationError, ProviderError, RateLimitError
from insta_bot.providers.base import FollowerProvider


class BrowserbaseProvider(FollowerProvider):
    def __init__(
        self,
        cdp_url: str,
        profile_url_template: str,
        timeout_ms: int,
    ) -> None:
        if not cdp_url:
            raise ConfigurationError("BROWSERBASE_CDP_URL cannot be empty for browserbase provider.")

        self._cdp_url = cdp_url
        self._profile_url_template = profile_url_template
        self._timeout_ms = timeout_ms

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
            raise ConfigurationError(
                "Playwright is not installed. Run: pip install -r requirements.txt"
            ) from exc

        try:
            self._playwright_cm = sync_playwright()
            self._playwright = self._playwright_cm.start()
            self._browser = self._playwright.chromium.connect_over_cdp(self._cdp_url)
            self._context = self._browser.contexts[0] if self._browser.contexts else self._browser.new_context()
        except Exception as exc:
            self.close()
            raise ProviderError(f"Failed to connect Browserbase CDP: {exc}") from exc

    def _extract_follower_count(self, html: str) -> int:
        json_count = re.search(r'"edge_followed_by"\s*:\s*\{\s*"count"\s*:\s*(\d+)', html)
        if json_count:
            return int(json_count.group(1))

        meta = re.search(r'content="([^"]*?)\s+Followers', html, re.IGNORECASE)
        if meta:
            parsed = self._parse_human_number(meta.group(1))
            if parsed is not None:
                return parsed

        for raw_json in re.findall(r'<script type="application/ld\+json">(.+?)</script>', html, re.DOTALL):
            try:
                payload = json.loads(raw_json)
            except Exception:
                continue

            count = self._find_ldjson_follower_count(payload)
            if count is not None:
                return count

        raise ProviderError("Could not parse follower count from page content.")

    def _parse_human_number(self, raw: str) -> int | None:
        cleaned = raw.strip().replace(",", "").replace(" ", "")
        match = re.match(r"^(\d+(?:\.\d+)?)([KMB]?)$", cleaned, re.IGNORECASE)
        if not match:
            # Fallback: keep only digits if no suffix parsing matched.
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

    def _find_ldjson_follower_count(self, payload: object) -> int | None:
        if isinstance(payload, dict):
            if payload.get("@type") == "Person":
                stats = payload.get("interactionStatistic")
                if isinstance(stats, list):
                    for item in stats:
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name", "")).lower()
                        if "follow" in name:
                            raw = str(item.get("userInteractionCount", ""))
                            parsed = self._parse_human_number(raw)
                            if parsed is not None:
                                return parsed
            for value in payload.values():
                found = self._find_ldjson_follower_count(value)
                if found is not None:
                    return found
        elif isinstance(payload, list):
            for value in payload:
                found = self._find_ldjson_follower_count(value)
                if found is not None:
                    return found
        return None

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
                    raise ProviderError("Instagram login wall detected on Browserbase session.")

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
