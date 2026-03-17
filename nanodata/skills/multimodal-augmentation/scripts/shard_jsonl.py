"""
TEMPLATE: JSONL Sharder
INSTRUCTION FOR AGENT:
1) Set INPUT_JSONL, OUTPUT_DIR, SHARD_SIZE.
2) Run via python_exec.
"""

from __future__ import annotations

import json
from pathlib import Path

INPUT_JSONL = "INPUT_PATH.jsonl"
OUTPUT_DIR = "shards"
SHARD_SIZE = 20
MANIFEST_PATH = "shards/manifest.json"


def main() -> None:
    input_path = Path(INPUT_JSONL)
    output_dir = Path(OUTPUT_DIR)
    manifest_path = Path(MANIFEST_PATH)

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    shards = []
    total = 0
    shard_index = 0
    current_lines = []

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            current_lines.append(line)
            total += 1
            if len(current_lines) >= SHARD_SIZE:
                shard_index += 1
                shard_name = f"shard_{shard_index:04d}.jsonl"
                shard_path = output_dir / shard_name
                shard_path.write_text("\n".join(current_lines) + "\n", encoding="utf-8")
                shards.append(shard_name)
                current_lines = []

    if current_lines:
        shard_index += 1
        shard_name = f"shard_{shard_index:04d}.jsonl"
        shard_path = output_dir / shard_name
        shard_path.write_text("\n".join(current_lines) + "\n", encoding="utf-8")
        shards.append(shard_name)

    manifest = {
        "input": str(input_path),
        "output_dir": str(output_dir),
        "shard_size": SHARD_SIZE,
        "total_records": total,
        "total_shards": len(shards),
        "shards": shards,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print("Shard complete")
    print(f"Input: {input_path}")
    print(f"Output dir: {output_dir}")
    print(f"Shards: {len(shards)} | Total records: {total}")
    print(f"Manifest: {manifest_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
