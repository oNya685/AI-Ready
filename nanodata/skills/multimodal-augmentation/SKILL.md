---
name: multimodal-augmentation
description: Generate images for existing SFT datasets (JSON/JSONL) to build multimodal fine-tuning data; use when you need to add image prompts, descriptions, and saved image files for each QA pair or conversation, via SubAgents + image_generate tool.
---

# Multimodal Dataset Augmentation (SubAgent Workflow)

Use this skill to attach image prompts and generated images to each QA pair in a dataset.

## Phase 1: Profile and Schema Check

1. Run `data_profile(file_path)` on the JSON/JSONL dataset to confirm schema and fields.
2. Identify which fields represent the QA pair:
   - Alpaca: `instruction`, `input`, `output`
   - ShareGPT: `conversations` or `messages`
   - Other: `prompt`, `response`, `question`, `answer`, `text`

## Phase 2: Shard the Dataset (Python)

Shard the JSONL into small files so each SubAgent reads only 10–20 lines.

1. Read: `nanodata/skills/multimodal-augmentation/scripts/shard_jsonl.py`
2. Set `INPUT_JSONL`, `OUTPUT_DIR`, and `SHARD_SIZE`
3. Run via `python_exec`

This produces:
- `shards/manifest.json`
- `shards/shard_0001.jsonl`, `shards/shard_0002.jsonl`, ...

## Phase 3: Spawn SubAgents

For each shard, spawn a SubAgent using `spawn`.
Each SubAgent should:

1. `read_file` its shard file
2. Build prompt/description per record
3. Call `image_generate` **in batch** (pass `items` list)
4. Write output shard JSONL with `multimodal` fields

Recommended SubAgent task template:

```
Process shard: shards/shard_0001.jsonl
- Read file
- For each record, extract QA text and build image prompt + description
- Call image_generate with items=[{prompt, output_path}, ...] and max_parallel=4
- Write output to shards_out/shard_0001_out.jsonl
```

## Phase 4: Merge Outputs

Merge all output shards into a single dataset:

1. Read: `nanodata/skills/multimodal-augmentation/scripts/merge_jsonl.py`
2. Set `INPUT_DIR` and `OUTPUT_JSONL`
3. Run via `python_exec`

## Phase 5: Verify

Confirm that:

- `OUTPUT_JSONL` is created
- each record includes a `multimodal` object:
  - `image_description`
  - `image_prompt`
  - `image_path`
- images are saved under your chosen output directory

## Tool Notes

- `image_generate` supports batch mode and concurrent requests (`max_parallel`).
- Use `output_path` for a single image or `output_dir` for batch runs.

## Optional Fallback

If SubAgents are unavailable, you can use the legacy single-process script at:
`nanodata/skills/multimodal-augmentation/scripts/template_multimodal.py`

