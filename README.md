# Instagram Follower Count Bot (Modular)

A modular Python project that fetches Instagram follower counts with a pluggable provider architecture.

## Scope
- Input: Instagram username
- Output: follower count
- Supports single and batch workflows
- Designed for extension (add new providers like browser automation adapters)

## Architecture
- `insta_bot/providers`: provider interface + implementations
- `insta_bot/services`: business logic and batch workflow
- `insta_bot/infra`: technical utilities (rate limiter)
- `insta_bot/cli.py`: entrypoint for single/batch commands

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set environment variables from `.env.example` in your shell.

## Usage
Single lookup:
```bash
python3 -m insta_bot.cli single nasa
```

Batch lookup:
```bash
python3 -m insta_bot.cli batch --input usernames_example.txt --output batch_results.json
```

Show archived runs:
```bash
python3 -m insta_bot.cli runs --limit 20
```

Each batch run is archived automatically under `runs/<run_id>/`:
- `usernames.txt`: exact input snapshot used in that run
- `results.json`: run output payload
- `run_meta.json`: parameters + summary
- `runs/index.jsonl`: append-only history for all runs

Username validation:
- Only `A-Z`, `a-z`, `0-9`, `.` and `_` are accepted
- Max length: 30
- Invalid usernames are skipped and stored as failed rows in output JSON

## High Volume Workflow (e.g. 1000 usernames)
1. Prepare `usernames_1000.txt` with one username per line.
2. Start conservatively:
   - `MAX_CONCURRENCY=3`
   - `REQUESTS_PER_MINUTE=20`
3. Run batch mode and check error rate.
4. Increase gradually:
   - concurrency by +1
   - requests/minute by +5
5. Keep retries enabled (`MAX_RETRIES >= 3`).
6. Monitor failures and tune rate/backoff.

## Extending with New Integrations
To integrate with tools like browser automation:
1. Add a class implementing `FollowerProvider` in `insta_bot/providers/`.
2. Register it in `create_provider` inside `insta_bot/providers/factory.py`.
3. Set `PROVIDER=<new_provider_name>`.

## Notes
Use only accounts and access patterns that comply with platform terms and applicable law.
