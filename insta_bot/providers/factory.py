from insta_bot.config import AppConfig
from insta_bot.errors import ConfigurationError
from insta_bot.providers.brightdata_provider import BrightDataProvider
from insta_bot.providers.browserbase_provider import BrowserbaseProvider
from insta_bot.providers.base import FollowerProvider
from insta_bot.providers.chained_provider import ChainedProvider
from insta_bot.providers.instaloader_provider import InstaloaderProvider
from insta_bot.providers.serp_provider import SerpProvider
from insta_bot.providers.socialblade_provider import SocialBladeProvider


SUPPORTED_PROVIDERS = {
    "instaloader",
    "browserbase",
    "brightdata",
    "socialblade",
    "serp",
    "socialblade+serp",
}


def create_provider(config: AppConfig) -> FollowerProvider:
    if config.provider == "instaloader":
        if not config.instagram_username:
            raise ConfigurationError(
                "INSTAGRAM_USERNAME cannot be empty. Session loading depends on it."
            )
        return InstaloaderProvider(
            login_username=config.instagram_username,
            login_password=config.instagram_password,
            session_file=config.session_path,
        )

    if config.provider == "browserbase":
        return BrowserbaseProvider(
            cdp_url=config.browserbase_cdp_url,
            profile_url_template=config.browserbase_profile_url_template,
            timeout_ms=config.browserbase_timeout_ms,
            storage_state_path=config.browserbase_storage_state_path,
        )

    if config.provider == "brightdata":
        return BrightDataProvider(
            cdp_url=config.brightdata_cdp_url,
            profile_url_template=config.brightdata_profile_url_template,
            timeout_ms=config.brightdata_timeout_ms,
            storage_state_path=config.brightdata_storage_state_path,
        )

    if config.provider == "socialblade":
        return SocialBladeProvider(
            delay_seconds=config.socialblade_delay_seconds,
            timeout=config.socialblade_timeout,
            rest_every=config.socialblade_rest_every,
            rest_seconds=config.socialblade_rest_seconds,
        )

    if config.provider == "serp":
        return SerpProvider(
            api_key=config.serp_api_key,
            timeout=config.serp_timeout,
        )

    if config.provider == "socialblade+serp":
        return ChainedProvider(
            primary=SocialBladeProvider(
                delay_seconds=config.socialblade_delay_seconds,
                timeout=config.socialblade_timeout,
                rest_every=config.socialblade_rest_every,
                rest_seconds=config.socialblade_rest_seconds,
            ),
            fallback=SerpProvider(
                api_key=config.serp_api_key,
                timeout=config.serp_timeout,
            ),
        )

    raise ConfigurationError(
        f"Unsupported provider '{config.provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
    )
