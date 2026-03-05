---
name: sft-dataset
description: Transform AI-Ready documents (Markdown) into LLM fine-tuning datasets using Easy Dataset. Use when the user wants to generate SFT training data from existing documents, create QA pairs from text, or prepare datasets for model fine-tuning. Requires Easy Dataset service running.
---

# SFT Dataset Generation

Transform AI-Ready documents into supervised fine-tuning (SFT) datasets using Easy Dataset.

## Prerequisites

1. Easy Dataset service running at `http://localhost:1717`
2. AI-Ready Markdown documents ready for processing

> Note: The `easy-dataset` MCP server is built into NanoBot and automatically available.

## Workflow

### Phase 1: Setup Project

Create a new project for this dataset:

```
mcp_easy_dataset_create_project(name="项目名称")
```

Returns: `{"id": "project_id", ...}`

Save the `project_id` for subsequent steps.

### Phase 2: Configure Model

Configure an LLM for question and answer generation:

```
mcp_easy_dataset_configure_model(
    project_id="...",
    provider_id="openai",
    endpoint="https://api.openai.com/v1",
    api_key="sk-...",
    model_name="gpt-4o"
)
```

Common providers: `openai`, `ollama`, `zhipu`, `qwen`, `deepseek`

### Phase 3: Upload Documents

Upload Markdown or PDF files:

```
mcp_easy_dataset_upload_file(
    project_id="...",
    file_path="path/to/document.md"
)
```

Returns: `{"fileId": "...", "fileName": "...", ...}`

### Phase 4: Split Text

Split documents into semantic chunks:

```
mcp_easy_dataset_split_text(
    project_id="...",
    file_names=["document.md"],
    model="gpt-4o",
    language="zh"
)
```

Returns: `{"totalChunks": N, "chunks": [...], "tags": [...]}`

### Phase 5: Generate Questions

Generate questions from text chunks:

```
mcp_easy_dataset_generate_questions(
    project_id="...",
    model="gpt-4o",
    language="zh"
)
```

Optionally specify `chunk_ids` to generate questions for specific chunks.

Returns: `{"results": [...], "totalSuccess": N, ...}`

### Phase 6: Generate Answers

Generate answers for each question:

First, list questions to get IDs:

```
mcp_easy_dataset_list_questions(project_id="...")
```

Then generate answer for each question:

```
mcp_easy_dataset_generate_answer(
    project_id="...",
    question_id="...",
    model="gpt-4o",
    language="zh"
)
```

### Phase 7: Review & Export

Review generated QA pairs:

```
mcp_easy_dataset_list_datasets(
    project_id="...",
    page=1,
    size=20
)
```

Export in desired format:

```
mcp_easy_dataset_export_dataset(
    project_id="...",
    format="alpaca",
    status="confirmed"
)
```

Supported formats:
- `alpaca`: `{"instruction": "...", "input": "...", "output": "..."}`
- `sharegpt`: `{"conversations": [...]}`
- `multilingual-thinking`: Chain-of-thought format

## Output

JSON/JSONL file containing QA pairs ready for LLM fine-tuning.

## Complete Example

Input: `experiments_corpus.md` (AI-Ready document from data-to-text skill)

```
1. mcp_easy_dataset_create_project(name="实验数据SFT")
   → project_id: "abc123"

2. mcp_easy_dataset_configure_model(
     project_id="abc123",
     provider_id="openai",
     model_name="gpt-4o"
   )

3. mcp_easy_dataset_upload_file(
     project_id="abc123",
     file_path="experiments_corpus.md"
   )
   → fileId: "file001"

4. mcp_easy_dataset_split_text(
     project_id="abc123",
     file_names=["experiments_corpus.md"],
     model="gpt-4o"
   )
   → 15 chunks created

5. mcp_easy_dataset_generate_questions(
     project_id="abc123",
     model="gpt-4o"
   )
   → 30 questions generated

6. For each question_id:
   mcp_easy_dataset_generate_answer(
     project_id="abc123",
     question_id=question_id,
     model="gpt-4o"
   )

7. mcp_easy_dataset_export_dataset(
     project_id="abc123",
     format="alpaca"
   )
   → Download: experiments_corpus_alpaca.json
```

Result: Ready-to-use SFT dataset for fine-tuning domain-specific LLMs.

## Tips

- **Batch Processing**: Generate answers for multiple questions in sequence
- **Quality Control**: Review generated QA pairs before export
- **Language**: Set `language` parameter to match document language (`zh`, `en`, etc.)
- **Model Selection**: Use capable models (GPT-4, Claude) for better QA quality
