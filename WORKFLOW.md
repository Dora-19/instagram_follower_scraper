# High-Volume Workflow (1000+ Usernames)

## Objective
Fetch follower counts for many usernames without overloading requests.

## Constraints
- Requests can fail due to temporary blocks, login issues, network instability, or target profile access limitations.
- Higher concurrency does not always improve throughput when request limits are reached.

## Recommended Rollout
1. Baseline run (100 usernames)
   - `MAX_CONCURRENCY=3`
   - `REQUESTS_PER_MINUTE=20`
   - `MAX_RETRIES=3`
2. Observe output JSON
   - Success ratio
   - Error patterns
   - Average elapsed time
3. Scale stepwise to 1000 usernames
   - Increase `MAX_CONCURRENCY` by 1 per run
   - Increase `REQUESTS_PER_MINUTE` by 5 per run
4. Stop scaling when error ratio rises above 5-10%.
5. Keep settings one step below the instability threshold.

## Runtime Command
```bash
MAX_CONCURRENCY=5 \
REQUESTS_PER_MINUTE=30 \
MAX_RETRIES=3 \
BACKOFF_BASE_SECONDS=2 \
INSTAGRAM_USERNAME=your_username \
INSTAGRAM_PASSWORD=your_password \
python3 -m insta_bot.cli batch --input usernames_1000.txt --output batch_results.json
```

## Interpretation
- If most errors are transient/rate related, decrease concurrency first.
- If failures persist across retries, decrease requests per minute.
- If login/session errors appear, refresh session with `session_bootstrap.py`.

## Extensibility Path
To support a new integration (for example browser-driven retrieval):
1. Implement `FollowerProvider` interface.
2. Register the provider in `insta_bot/providers/factory.py`.
3. Set `PROVIDER=<new_provider_name>`.
