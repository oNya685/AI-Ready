---
name: data-to-text
description: Convert structured data (CSV/Parquet/Excel) into semantic, readable text documents or experimental reports for LLM fine-tuning. Use when the user wants to transform tabular data into natural language narratives, generate training corpus, or create AI-Ready text documents from datasets. Output is Markdown format ready for further processing.
---

# Data-to-Text Transformation

Transform structured tabular data into semantic, LLM-friendly text documents.

## Core Directives

1. **Semantic Inference First.** Before converting, understand what each column represents. Infer meaning from column names, values, and context.
2. **Natural Language Templates.** Design text templates that connect data points into coherent narratives, not just key-value dumps.
3. **Handle Missing Gracefully.** Replace NaN with contextually appropriate placeholders (e.g., "未记录", "N/A", "unknown").

## Workflow

### Phase 1: Profile & Semantic Inference

1. Run `data_profile(file_path)` to understand the schema and sample data.
2. For each column, infer its semantic meaning:
   - `temp_c` → "Temperature in Celsius"
   - `exp_id` → "Experiment Identifier"
   - `result_mg` → "Result measurement in milligrams"
3. Identify the document type: Is this an experimental log? A survey response? A time-series record?

### Phase 2: Template Design

Design a natural language template for a single row. The template should:

- Use complete sentences with proper grammar
- Connect related fields logically
- Handle optional/missing fields gracefully
- Maintain consistent tone and style

**Example Template:**
```
## 实验 {exp_id}

**日期**: {date}
**操作员**: {operator}

在温度 {temp_c}°C 条件下，进行了 {reaction_type} 反应。
反应持续 {duration_min} 分钟，最终产率为 {yield_pct}%。

**备注**: {notes}
```

### Phase 3: Script Generation

1. Read the template: `read_file("skills/data-to-text/scripts/template_to_text.py")`
2. Modify the `ROW_TEMPLATE` string with your designed template
3. Update the column mapping in the script
4. Run via `python_exec`

### Phase 4: Execute & Verify

1. Execute the script using `python_exec`
2. If errors occur, analyze the traceback and fix
3. Verify the output `.md` file exists and contains properly formatted text

### Phase 5: Quality Check

Review the generated document:
- Are all records converted?
- Is the language natural and readable?
- Are missing values handled appropriately?
- Is the format consistent?

## Output Format

Default output: `{source_filename}_corpus.md`

Each row becomes a section in the Markdown document, separated by horizontal rules or headers.

## Next Steps

The generated Markdown document is **AI-Ready**. To convert it into an LLM fine-tuning dataset:

→ Use the `sft-dataset` skill to generate QA pairs and export in Alpaca/ShareGPT format.

## Complete Example

Input: `experiments.csv` (100 rows of experimental records)

```
1. data_profile("experiments.csv")
   → Understand schema: exp_id, date, temp_c, reaction_type, yield_pct, notes

2. Design template:
   ## 实验 {exp_id}
   日期: {date}
   在 {temp_c}°C 下进行 {reaction_type} 反应...

3. python_exec(template_script)
   → Generate experiments_corpus.md

4. Verify output:
   - 100 experiment reports
   - Natural language format
   - Ready for SFT processing
```

Output: `experiments_corpus.md` (AI-Ready document)
