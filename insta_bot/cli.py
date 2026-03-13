from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import replace
from datetime import datetime
from pathlib import Path

INPUTS_DIR = Path("inputs")
OUTPUTS_DIR = Path("outputs")


def _default_output(input_file: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return OUTPUTS_DIR / f"{input_file.stem}_{timestamp}.json"

from insta_bot.config import AppConfig
from insta_bot.errors import AppError
from insta_bot.infra.rate_limiter import SlidingWindowRateLimiter
from insta_bot.providers.brightdata_provider import BrightDataProvider
from insta_bot.providers.browserbase_provider import BrowserbaseProvider
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
        type=Path,
        default=None,
        help="Text file with one username per line (default: inputs/*.txt if only one file exists)",
    )
    batch.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output JSON path (default: outputs/<input_stem>_<timestamp>.json)",
    )

    subparsers.add_parser(
        "browserbase-login",
        help="Open Instagram login on Browserbase and save storage_state file",
    )
    subparsers.add_parser(
        "brightdata-login",
        help="Open Instagram login on Bright Data browser and save storage_state file",
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

    # Force no app-level retries in batch mode to reduce retry spam under rate limiting.
    batch_config = replace(config, max_retries=0)
    service = build_service(batch_config)
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
            input_file = args.input
            if input_file is None:
                txt_files = list(INPUTS_DIR.glob("*.txt"))
                if len(txt_files) == 1:
                    input_file = txt_files[0]
                elif len(txt_files) == 0:
                    print(f"ERROR: no .txt files found in {INPUTS_DIR}/")
                    return 1
                else:
                    names = ", ".join(f.name for f in txt_files)
                    print(f"ERROR: multiple input files found — specify one with --input: {names}")
                    return 1
            output_file = args.output or _default_output(input_file)
            OUTPUTS_DIR.mkdir(exist_ok=True)
            return asyncio.run(run_batch_mode(input_file, output_file, config))

        if args.command == "browserbase-login":
            provider = BrowserbaseProvider(
                cdp_url=config.browserbase_cdp_url,
                profile_url_template=config.browserbase_profile_url_template,
                timeout_ms=config.browserbase_timeout_ms,
                storage_state_path=config.browserbase_storage_state_path,
            )
            provider.bootstrap_login_state()
            provider.close()
            return 0

        if args.command == "brightdata-login":
            provider = BrightDataProvider(
                cdp_url=config.brightdata_cdp_url,
                profile_url_template=config.brightdata_profile_url_template,
                timeout_ms=config.brightdata_timeout_ms,
                storage_state_path=config.brightdata_storage_state_path,
            )
            provider.bootstrap_login_state()
            provider.close()
            return 0
    except AppError as exc:
        print(f"ERROR: {exc}")
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
