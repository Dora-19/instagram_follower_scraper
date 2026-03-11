from __future__ import annotations

import json
from pathlib import Path


def tail_runs(index_file: Path, limit: int = 10) -> list[dict]:
    if not index_file.exists():
        return []

    lines = index_file.read_text(encoding="utf-8").splitlines()
    selected = lines[-limit:]
    return [json.loads(line) for line in selected if line.strip()]
