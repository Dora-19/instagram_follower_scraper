import asyncio

from insta_bot.cli import build_service
from insta_bot.config import AppConfig


async def main() -> int:
    config = AppConfig.from_env()
    service = build_service(config)

    for username in ["instagram", "nasa", "natgeo"]:
        result = await service.get_count(username)
        if result.success:
            print(f"@{username}: {result.followers}")
        else:
            print(f"@{username}: ERROR -> {result.error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
