"""
TEMPLATE: JSONL Merge
INSTRUCTION FOR AGENT:
1) Set INPUT_DIR and OUTPUT_JSONL.
2) Run via python_exec.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

INPUT_DIR = "shards_out"
OUTPUT_JSONL = "OUTPUT_PATH_multimodal.jsonl"
MANIFEST_PATH = ""  # optional: path to shards/manifest.json


def _sorted_shards(paths: list[Path]) -> list[Path]:
    def _key(p: Path) -> tuple[int, str]:
        m = re.search(r"shard_(\d+)", p.name)
        return (int(m.group(1)) if m else 10**9, p.name)
    return sorted(paths, key=_key)


def main() -> None:
    input_dir = Path(INPUT_DIR)
    output_path = Path(OUTPUT_JSONL)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input dir not found: {input_dir}")

    shard_files: list[Path] = []
    if MANIFEST_PATH:
        manifest = json.loads(Path(MANIFEST_PATH).read_text(encoding="utf-8"))
        shard_files = [input_dir / name.replace(".jsonl", "_out.jsonl") for name in manifest.get("shards", [])]
    else:
        shard_files = list(input_dir.glob("*.jsonl"))

    shard_files = _sorted_shards([p for p in shard_files if p.exists()])
    if not shard_files:
        raise FileNotFoundError("No shard outputs found")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = 0
    with open(output_path, "w", encoding="utf-8") as out:
        for shard in shard_files:
            for line in shard.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line:
                    continue
                out.write(line + "\n")
                total += 1

    print("=" * 60)
    print("Merge complete")
    print(f"Input dir: {input_dir}")
    print(f"Output: {output_path}")
    print(f"Total records: {total}")
    print("=" * 60)


if __name__ == "__main__":
    main()
