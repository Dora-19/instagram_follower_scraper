from insta_bot.config import AppConfig
from insta_bot.errors import ConfigurationError
from insta_bot.providers.base import FollowerProvider
from insta_bot.providers.instaloader_provider import InstaloaderProvider


SUPPORTED_PROVIDERS = {"instaloader"}


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

    raise ConfigurationError(
        f"Unsupported provider '{config.provider}'. Supported: {sorted(SUPPORTED_PROVIDERS)}"
    )
