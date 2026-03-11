from insta_bot.config import AppConfig
from insta_bot.providers.factory import create_provider


def main() -> int:
    config = AppConfig.from_env()
    provider = create_provider(config)
    # Trigger authentication once so session file is created or validated.
    provider.get_follower_count(config.instagram_username)
    print(f"Session is ready: {config.session_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
