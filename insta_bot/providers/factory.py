from insta_bot.config import AppConfig
from insta_bot.errors import ConfigurationError
from insta_bot.providers.browserbase_provider import BrowserbaseProvider
from insta_bot.providers.base import FollowerProvider
from insta_bot.providers.instaloader_provider import InstaloaderProvider


SUPPORTED_PROVIDERS = {"instaloader", "browserbase"}


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
        )

    raise ConfigurationError(
        f"Unsupported provider '{config.provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
    )
