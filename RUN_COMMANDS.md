# Run Commands

## 1) Enter Project
```bash
cd /Users/doraalkan/Desktop/insta-bot
```

## 2) Create and Activate Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install Dependencies
```bash
pip install -r requirements.txt
```

## 4) Prepare Environment Variables
```bash
cp .env.example .env
```

Load `.env` into current shell:
```bash
set -a
source .env
set +a
```

Check values:
```bash
echo $INSTAGRAM_USERNAME
echo $MAX_CONCURRENCY
echo $REQUESTS_PER_MINUTE
```

## 5) Single Run
```bash
python3 -m insta_bot.cli single shakira
```

## 6) Batch Run (One File)
```bash
python3 -m insta_bot.cli batch --input usernames_100.txt --output batch_results_100.json
```

## 7) Batch Run (Chunk Files)
Chunked input files under `batches/inputs`:
```bash
python3 -m insta_bot.cli batch --input batches/inputs/chunk_00.txt --output batches/outputs/chunk_00.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_01.txt --output batches/outputs/chunk_01.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_02.txt --output batches/outputs/chunk_02.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_03.txt --output batches/outputs/chunk_03.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_04.txt --output batches/outputs/chunk_04.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_05.txt --output batches/outputs/chunk_05.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_06.txt --output batches/outputs/chunk_06.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_07.txt --output batches/outputs/chunk_07.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_08.txt --output batches/outputs/chunk_08.json
python3 -m insta_bot.cli batch --input batches/inputs/chunk_09.txt --output batches/outputs/chunk_09.json
```

Wait between chunks:
```bash
sleep 180
```

## 8) Run All Chunks with Script
```bash
SLEEP_SECONDS=120 ./run_chunks.sh
```

## 9) Clean and Split Username List
Create clean file (valid format + unique):
```bash
awk '/^[A-Za-z0-9._]{1,30}$/' usernames_100.txt | awk '!seen[$0]++' > batches/inputs/usernames_100_clean.txt
```

Split into chunks of 10:
```bash
split -l 10 -d -a 2 batches/inputs/usernames_100_clean.txt batches/inputs/chunk_
for f in batches/inputs/chunk_*; do mv "$f" "$f.txt"; done
```

## 10) Runtime Tuning (Current Shell)
Conservative settings:
```bash
export MAX_CONCURRENCY=1
export REQUESTS_PER_MINUTE=2
export MAX_RETRIES=0
export BACKOFF_BASE_SECONDS=4
```

## 11) Useful Checks
List chunk files:
```bash
ls -1 batches/inputs
```

Check output file:
```bash
ls -lh batches/outputs/chunk_00.json
cat batches/outputs/chunk_00.json
```

## 12) Deactivate Virtual Environment
```bash
deactivate
```
