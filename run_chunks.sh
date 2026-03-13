#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="batches/inputs"
OUTPUT_DIR="batches/outputs"
SLEEP_SECONDS="${SLEEP_SECONDS:-120}"

mkdir -p "$OUTPUT_DIR"

for input in "$INPUT_DIR"/chunk_*.txt; do
  base="$(basename "$input" .txt)"
  output="$OUTPUT_DIR/${base}.json"

  echo "Running $input -> $output"
  python3 -m insta_bot.cli batch --input "$input" --output "$output" || true

  echo "Sleeping ${SLEEP_SECONDS}s..."
  sleep "$SLEEP_SECONDS"
done

echo "Done. Outputs in $OUTPUT_DIR"
