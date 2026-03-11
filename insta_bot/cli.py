from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from insta_bot.config import AppConfig
from insta_bot.errors import AppError
from insta_bot.infra.rate_limiter import SlidingWindowRateLimiter
from insta_bot.providers.factory import create_provider
from insta_bot.services.batch_workflow import run_batch
from insta_bot.services.follower_service import FollowerCountService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="instagram-follower-bot",
        description="Fetch Instagram follower counts with pluggable providers.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Fetch follower count for one username")
    single.add_argument("username", help="Target Instagram username")

    batch = subparsers.add_parser("batch", help="Fetch follower counts for many usernames")
    batch.add_argument(
        "--input",
        required=True,
        type=Path,
        help="Text file with one username per line",
    )
    batch.add_argument(
        "--output",
        type=Path,
        default=Path("batch_results.json"),
        help="Output JSON file path",
    )

    return parser


def build_service(config: AppConfig) -> FollowerCountService:
    provider = create_provider(config)
    limiter = SlidingWindowRateLimiter(max_requests=config.requests_per_minute)
    return FollowerCountService(
        provider=provider,
        rate_limiter=limiter,
        max_retries=config.max_retries,
        backoff_base_seconds=config.backoff_base_seconds,
    )


async def run_single(username: str, config: AppConfig) -> int:
    service = build_service(config)
    result = await service.get_count(username)
    if result.success:
        print(result.followers)
        return 0

    print(f"ERROR: {result.error}")
    return 1


async def run_batch_mode(input_file: Path, output_file: Path, config: AppConfig) -> int:
    if not input_file.exists():
        print(f"ERROR: input file not found: {input_file}")
        return 1

    usernames = [
        line.strip()
        for line in input_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    if not usernames:
        print("ERROR: input file is empty")
        return 1

    service = build_service(config)
    results = await run_batch(
        usernames=usernames,
        service=service,
        concurrency=config.max_concurrency,
    )

    payload = [
        {
            "username": item.username,
            "followers": item.followers,
            "success": item.success,
            "attempts": item.attempts,
            "elapsed_ms": item.elapsed_ms,
            "error": item.error,
        }
        for item in results
    ]

    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    success_count = sum(1 for item in results if item.success)
    print(f"Completed: {success_count}/{len(results)} succeeded. Output: {output_file}")
    return 0 if success_count == len(results) else 2


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config = AppConfig.from_env()

    try:
        if args.command == "single":
            return asyncio.run(run_single(args.username, config))

        if args.command == "batch":
            return asyncio.run(run_batch_mode(args.input, args.output, config))
    except AppError as exc:
        print(f"ERROR: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
