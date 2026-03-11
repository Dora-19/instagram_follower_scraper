from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable

from insta_bot.config import AppConfig
from insta_bot.domain import FollowerResult


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def persist_batch_run(
    input_file: Path,
    results: Iterable[FollowerResult],
    config: AppConfig,
) -> dict[str, Path | int | str]:
    runs_root = config.runs_root_path
    run_id = _timestamp()
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    usernames_copy = run_dir / "usernames.txt"
    usernames_copy.write_text(input_file.read_text(encoding="utf-8"), encoding="utf-8")

    result_list = list(results)
    results_file = run_dir / "results.json"
    results_file.write_text(
        json.dumps([asdict(item) for item in result_list], indent=2),
        encoding="utf-8",
    )

    success_count = sum(1 for item in result_list if item.success)
    fail_count = len(result_list) - success_count

    run_meta = {
        "run_id": run_id,
        "created_at_utc": datetime.now(UTC).isoformat(),
        "input_source": str(input_file.resolve()),
        "input_snapshot": str(usernames_copy.resolve()),
        "results_file": str(results_file.resolve()),
        "total": len(result_list),
        "success": success_count,
        "failed": fail_count,
        "provider": config.provider,
        "max_concurrency": config.max_concurrency,
        "requests_per_minute": config.requests_per_minute,
        "max_retries": config.max_retries,
        "backoff_base_seconds": config.backoff_base_seconds,
    }

    meta_file = run_dir / "run_meta.json"
    meta_file.write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    index_file = runs_root / "index.jsonl"
    with index_file.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(run_meta) + "\n")

    return {
        "run_id": run_id,
        "run_dir": run_dir.resolve(),
        "results_file": results_file.resolve(),
        "meta_file": meta_file.resolve(),
        "success": success_count,
        "total": len(result_list),
    }
