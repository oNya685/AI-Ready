"""
TEMPLATE: AI-Ready Data-to-Text Conversion Script
INSTRUCTION FOR AGENT:
1. COPY THIS ENTIRE CODE. DO NOT run it in chunks. `python_exec` does NOT keep state (variables like `df` will be lost between calls). You must run the full script at once.
2. Replace 'INPUT_PATH' with the actual data path.
3. Replace the Mapping Dictionaries to translate foreign/obscure categorical values into natural language.
4. Design the 'NARRATIVE_TEMPLATE' to form a coherent, highly readable text paragraph for each row.
5. Map the DataFrame columns in `format_record()`.
6. Execute the script to generate both .md and .jsonl files.
"""

import pandas as pd
import numpy as np
import sys
import os
import json
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
INPUT_PATH = "INPUT_PATH_HERE"              # Agent: Replace with actual source file
OUTPUT_MD = "output_corpus.md"              # Agent: Rename appropriately (e.g., experiment_logs.md)
OUTPUT_JSONL = "output_corpus.jsonl"        # Agent: Rename appropriately (e.g., experiment_logs.jsonl)

# ============================================================
# SEMANTIC MAPPING & TRANSLATION (Agent Fills This)
# ============================================================
# Agent: Use dictionaries to translate English categories/status codes into the target language.
# Example: STATUS_MAP = {1: "成功", 0: "失败", "nan": "未知"}
STATUS_MAP = {}
CATEGORY_MAP = {}

# ============================================================
# NARRATIVE TEMPLATE (Agent Designs This)
# ============================================================
# Agent: Design a natural language template. 
# It should read like a fluid report, not just a key-value list.
# For example:
NARRATIVE_TEMPLATE = """
### 记录档案 {record_id}
**时间**: {date} | **类别**: {category} | **状态**: {status}

**详情描述**:
本条记录显示，在 {date} 进行的操作中，被归类为 {category}。
最终的操作状态为：{status}。

**附加备注**: {notes}
---
"""

def safe_value(val, default="未记录"):
    """Safely convert a value to string, handling NaN and None."""
    if pd.isna(val) or val is None or str(val).strip() == "":
        return default
    if isinstance(val, float):
        if val == int(val):
            return str(int(val))
    return str(val)

def format_record(row, index):
    """
    Agent: Extract columns, apply semantic mapping, and format into AI-Ready payload.
    Returns a dictionary suitable for JSONL and the Markdown string.
    """
    # 1. Extract and Clean Values (Agent: Change column names here)
    record_id = safe_value(row.get("id", f"R-{index:04d}"))
    date = safe_value(row.get("date", "未知时间"))
    
    raw_category = safe_value(row.get("category", "未知"))
    category = CATEGORY_MAP.get(raw_category, raw_category) # Translate if in map
    
    raw_status = safe_value(row.get("status", "未知"))
    status = STATUS_MAP.get(raw_status, raw_status) # Translate if in map
    
    notes = safe_value(row.get("notes", "无附加说明"))
    
    # 2. Generate Natural Language Narrative
    narrative = NARRATIVE_TEMPLATE.format(
        record_id=record_id,
        date=date,
        category=category,
        status=status,
        notes=notes
    )
    
    # 3. Construct JSONL Payload (Rich Metadata + Narrative)
    json_payload = {
        "doc_id": record_id,
        "metadata": {
            "date": date,
            "category": category,
            "status": status
        },
        "text": narrative.strip().replace("---\n", "") # The text for LLM training
    }
    
    return narrative, json_payload

def convert_to_text():
    print(f"[INFO] Loading data from {INPUT_PATH}...")
    
    try:
        if INPUT_PATH.endswith('.csv'):
            df = pd.read_csv(INPUT_PATH)
        elif INPUT_PATH.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(INPUT_PATH)
        elif INPUT_PATH.endswith('.parquet'):
            df = pd.read_parquet(INPUT_PATH)
        else:
            df = pd.read_csv(INPUT_PATH)
    except Exception as e:
        print(f"[FATAL] Failed to load data: {e}")
        sys.exit(1)

    print(f"[INFO] Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    md_sections =[f"# AI-Ready 语义语料库\n**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n**源文件**: {os.path.basename(INPUT_PATH)}\n**记录数**: {len(df)}\n\n---\n"]
    jsonl_records =[]
    
    success_count = 0
    for idx, row in df.iterrows():
        try:
            narrative, payload = format_record(row, idx)
            md_sections.append(narrative)
            jsonl_records.append(json.dumps(payload, ensure_ascii=False))
            success_count += 1
        except Exception as e:
            print(f"[WARN] Failed to format row {idx}: {e}")
            md_sections.append(f"<!-- Error processing row {idx} -->\n\n")

    # Save Markdown
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write("\n".join(md_sections))
    print(f"[SUCCESS] Saved Markdown Document to {OUTPUT_MD}")
    
    # Save JSONL
    with open(OUTPUT_JSONL, 'w', encoding='utf-8') as f:
        f.write("\n".join(jsonl_records))
    print(f"[SUCCESS] Saved JSONL Dataset to {OUTPUT_JSONL}")
    
    print(f"[INFO] Successfully converted {success_count}/{len(df)} records.")

if __name__ == "__main__":
    convert_to_text()