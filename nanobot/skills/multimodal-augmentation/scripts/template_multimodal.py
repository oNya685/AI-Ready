"""
TEMPLATE: Multimodal SFT Augmentation (ThreadPool workers, legacy fallback)
INSTRUCTION FOR AGENT:
1) Copy this file.
2) Set INPUT_JSONL, OUTPUT_JSONL, IMAGE_DIR.
3) Customize extract_text/build_image_prompt/build_image_description.
4) Run via python_exec.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_JSONL = os.environ.get("INPUT_JSONL", "INPUT_PATH.jsonl")
OUTPUT_JSONL = os.environ.get("OUTPUT_JSONL", "OUTPUT_PATH_multimodal.jsonl")
IMAGE_DIR = os.environ.get("IMAGE_DIR", "generated_images")

BATCH_SIZE = 10           # records per worker
MAX_WORKERS = 4           # number of workers (threads)
MAX_RETRIES = 2
RETRY_BACKOFF_S = 2.0

MAX_PROMPT_CHARS = 800
MAX_DESC_CHARS = 240
RESUME_EXISTING = True

# Image API (OpenAI-compatible)
IMAGE_API_BASE_URL = os.environ.get("IMAGE_API_BASE_URL", "https://api.openai.com/v1")
IMAGE_API_KEY = os.environ.get("IMAGE_API_KEY", "")
IMAGE_MODEL = os.environ.get("IMAGE_MODEL", "gpt-image-1")
IMAGE_SIZE = os.environ.get("IMAGE_SIZE", "1024x1024")
IMAGE_RESPONSE_FORMAT = os.environ.get("IMAGE_RESPONSE_FORMAT", "url")  # url | b64_json
IMAGE_ENDPOINT = os.environ.get("IMAGE_ENDPOINT", "/images/generations")

IMAGE_PROMPT_PREFIX = os.environ.get(
    "IMAGE_PROMPT_PREFIX",
    "High-quality, detailed, realistic illustration. Scene: ",
)
IMAGE_PROMPT_SUFFIX = os.environ.get("IMAGE_PROMPT_SUFFIX", "")

IMAGE_DRY_RUN = os.environ.get("IMAGE_DRY_RUN", "0").lower() in {"1", "true", "yes"}

# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class Result:
    index: int
    record: dict
    status: str
    error: str | None


# ============================================================
# TEXT EXTRACTION + PROMPT BUILDING
# ============================================================

def extract_text(record: dict) -> str:
    """Extract QA text from common dataset schemas."""
    if not isinstance(record, dict):
        return ""

    # Alpaca-style
    if "instruction" in record:
        instruction = str(record.get("instruction", "")).strip()
        input_text = str(record.get("input", "")).strip()
        output_text = str(record.get("output", "")).strip()
        parts = [instruction]
        if input_text:
            parts.append(f"Input: {input_text}")
        if output_text:
            parts.append(f"Answer: {output_text}")
        return "\n".join(p for p in parts if p).strip()

    # ShareGPT-style
    for key in ("conversations", "messages"):
        convos = record.get(key)
        if isinstance(convos, list) and convos:
            human = None
            assistant = None
            for msg in convos:
                if not isinstance(msg, dict):
                    continue
                role = (msg.get("from") or msg.get("role") or "").lower()
                content = msg.get("value") or msg.get("content") or ""
                content = str(content).strip()
                if not content:
                    continue
                if role in {"human", "user"} and human is None:
                    human = content
                elif role in {"assistant", "gpt"} and assistant is None:
                    assistant = content
            if human or assistant:
                parts = []
                if human:
                    parts.append(f"Question: {human}")
                if assistant:
                    parts.append(f"Answer: {assistant}")
                return "\n".join(parts).strip()

    # Generic fallbacks
    for key in ("prompt", "question", "input", "text"):
        if key in record and record.get(key):
            return str(record.get(key)).strip()
    for key in ("response", "answer", "output"):
        if key in record and record.get(key):
            return str(record.get(key)).strip()

    return ""


def build_image_prompt(text: str, record: dict) -> str:
    """Build a descriptive prompt for image generation."""
    base = text.strip().replace("\n", " ")
    if not base:
        base = "generic illustrative scene related to the dataset"
    if len(base) > MAX_PROMPT_CHARS:
        base = base[:MAX_PROMPT_CHARS].rstrip()
    return f"{IMAGE_PROMPT_PREFIX}{base}{IMAGE_PROMPT_SUFFIX}".strip()


def build_image_description(text: str) -> str:
    """Build a short description for the generated image."""
    desc = text.strip().replace("\n", " ")
    if not desc:
        desc = "Auto-generated image based on the QA pair."
    if len(desc) > MAX_DESC_CHARS:
        desc = desc[: MAX_DESC_CHARS - 3].rstrip() + "..."
    return desc


# ============================================================
# IMAGE GENERATION
# ============================================================

def _make_image_filename(index: int, prompt: str) -> str:
    digest = hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]
    return f"img_{index:06d}_{digest}.png"


def _relative_path(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)
def _download_url(client: httpx.Client, url: str, out_path: Path) -> None:
    with client.stream("GET", url, timeout=60.0) as resp:
        resp.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in resp.iter_bytes():
                f.write(chunk)


def _generate_image(client: httpx.Client, prompt: str, out_path: Path) -> None:
    headers = {
        "Authorization": f"Bearer {IMAGE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": IMAGE_MODEL,
        "prompt": prompt,
        "size": IMAGE_SIZE,
        "n": 1,
        "response_format": IMAGE_RESPONSE_FORMAT,
    }

    resp = client.post(
        f"{IMAGE_API_BASE_URL}{IMAGE_ENDPOINT}",
        headers=headers,
        json=payload,
        timeout=60.0,
    )

    if resp.status_code >= 400:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:500]}")

    data = resp.json()
    items = data.get("data") or []
    if not items:
        raise RuntimeError("No image data returned by API")

    item = items[0]
    if IMAGE_RESPONSE_FORMAT == "b64_json" or "b64_json" in item:
        b64 = item.get("b64_json")
        if not b64:
            raise RuntimeError("Missing b64_json in response")
        out_path.write_bytes(base64.b64decode(b64))
        return

    url = item.get("url")
    if not url:
        raise RuntimeError("Missing url in response")

    _download_url(client, url, out_path)


# ============================================================
# worker POOL (workers)
# ============================================================

def _process_record(
    index: int,
    record: dict,
    image_dir: Path,
    base_dir: Path,
    client: httpx.Client,
) -> Result:
    text = extract_text(record)
    prompt = build_image_prompt(text, record)
    description = build_image_description(text)

    filename = _make_image_filename(index, prompt)
    image_path = image_dir / filename

    # Resume if already present
    if RESUME_EXISTING:
        existing = record.get("multimodal")
        if isinstance(existing, dict) and existing.get("image_path"):
            existing_path = Path(existing.get("image_path"))
            if not existing_path.is_absolute():
                existing_path = base_dir / existing_path
            if existing_path.exists():
                existing["status"] = existing.get("status") or "skipped"
                record["multimodal"] = existing
                return Result(index=index, record=record, status="skipped", error=None)

    if image_path.exists() and RESUME_EXISTING:
        record["multimodal"] = {
            "image_path": _relative_path(image_path, base_dir),
            "image_prompt": prompt,
            "image_description": description,
            "model": IMAGE_MODEL,
            "status": "skipped",
        }
        return Result(index=index, record=record, status="skipped", error=None)

    if IMAGE_DRY_RUN:
        record["multimodal"] = {
            "image_path": _relative_path(image_path, base_dir),
            "image_prompt": prompt,
            "image_description": description,
            "model": IMAGE_MODEL,
            "status": "dry_run",
        }
        return Result(index=index, record=record, status="dry_run", error=None)

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            _generate_image(client, prompt, image_path)
            record["multimodal"] = {
                "image_path": _relative_path(image_path, base_dir),
                "image_prompt": prompt,
                "image_description": description,
                "model": IMAGE_MODEL,
                "status": "success",
            }
            return Result(index=index, record=record, status="success", error=None)
        except Exception as exc:
            last_error = str(exc)
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_BACKOFF_S * (2 ** attempt))
                continue
            break

    record["multimodal"] = {
        "image_path": None,
        "image_prompt": prompt,
        "image_description": description,
        "model": IMAGE_MODEL,
        "status": "failed",
        "error": last_error,
    }
    return Result(index=index, record=record, status="failed", error=last_error)


def _process_batch(
    batch: list[tuple[int, dict]],
    worker_id: int,
    image_dir: Path,
    base_dir: Path,
) -> list[Result]:
    results: list[Result] = []
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)
    with httpx.Client(limits=limits) as client:
        print(f"[worker {worker_id}] Processing {len(batch)} records...")
        for index, record in batch:
            results.append(_process_record(index, record, image_dir, base_dir, client))
    return results


# ============================================================
# MAIN
# ============================================================

def _read_jsonl(path: Path) -> Iterable[tuple[int, dict]]:
    with open(path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            yield idx, json.loads(line)


def _chunked(items: list[tuple[int, dict]], size: int) -> list[list[tuple[int, dict]]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def main() -> None:
    input_path = Path(INPUT_JSONL)
    output_path = Path(OUTPUT_JSONL)
    base_dir = output_path.resolve().parent
    image_dir = Path(IMAGE_DIR)
    if not image_dir.is_absolute():
        image_dir = base_dir / image_dir

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if not IMAGE_DRY_RUN and not IMAGE_API_KEY:
        raise RuntimeError("IMAGE_API_KEY is required unless IMAGE_DRY_RUN=1")

    image_dir.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading dataset from {input_path}...")
    print(f"[INFO] Output will be saved to {output_path}")
    print(f"[INFO] Images will be saved to {image_dir}")
    print(f"[INFO] workers: {MAX_WORKERS} workers, batch size {BATCH_SIZE}")

    success = failed = skipped = dry_run = 0

    buffer: list[tuple[int, dict]] = []
    chunk_size = max(BATCH_SIZE * MAX_WORKERS, BATCH_SIZE)

    with open(output_path, "w", encoding="utf-8") as out:
        for item in _read_jsonl(input_path):
            buffer.append(item)
            if len(buffer) >= chunk_size:
                results = _process_chunk(buffer, image_dir, base_dir)
                for result in results:
                    out.write(json.dumps(result.record, ensure_ascii=False) + "\n")
                    if result.status == "success":
                        success += 1
                    elif result.status == "failed":
                        failed += 1
                    elif result.status == "dry_run":
                        dry_run += 1
                    else:
                        skipped += 1
                buffer.clear()

        if buffer:
            results = _process_chunk(buffer, image_dir, base_dir)
            for result in results:
                out.write(json.dumps(result.record, ensure_ascii=False) + "\n")
                if result.status == "success":
                    success += 1
                elif result.status == "failed":
                    failed += 1
                elif result.status == "dry_run":
                    dry_run += 1
                else:
                    skipped += 1

    print("=" * 60)
    print("Multimodal augmentation complete")
    print(f"Total: {success + failed + skipped + dry_run}")
    print(f"Success: {success} | Failed: {failed} | Skipped: {skipped} | Dry-run: {dry_run}")
    print(f"Output: {output_path}")
    print(f"Images: {image_dir}")
    print("=" * 60)


def _process_chunk(
    records: list[tuple[int, dict]],
    image_dir: Path,
    base_dir: Path,
) -> list[Result]:
    batches = _chunked(records, BATCH_SIZE)
    results: list[Result] = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        for i, batch in enumerate(batches, start=1):
            futures.append(
                executor.submit(_process_batch, batch, i, image_dir, base_dir)
            )
        for future in as_completed(futures):
            results.extend(future.result())
    results.sort(key=lambda r: r.index)
    return results


if __name__ == "__main__":
    main()





