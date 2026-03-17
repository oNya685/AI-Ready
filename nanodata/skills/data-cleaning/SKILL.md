---
name: data-cleaning
description: End-to-end data preprocessing pipeline to transform raw files (CSV, Excel, Parquet) into AI-Ready assets. Use this skill when the user requests to clean data, handle missing values, fix data types, remove duplicates, standardize formats, or prepare datasets for model training. Includes automatic profiling and dataset card generation.
---

# Data Cleaning SOP

Follow this standard procedure to transform raw data into high-quality AI-Ready assets.

## Core Directives

1.  **Never read full datasets into context.** Always use `data_profile` tool or Python scripts to inspect data.
2.  **Code-as-Action.** Perform all transformations via `python_executor`. Do not simulate changes in text.
3.  **Immutability.** Never overwrite the raw file. Save output as `*_cleaned.parquet` (preferred) or `*_cleaned.csv`.

## Workflow

### Phase 1: Profile & Diagnose
Before writing any cleaning code, understand the data state.
1.  Run `data_profile(file_path)` to get schema, shape, and sample rows.
2.  Identify issues: Missing values (NaN), inconsistent types (Object vs Float), duplicates, or outliers.

### Phase 2: Plan & Script
Construct a cleaning script. Use the bundled template to ensure robustness.
1.  Read the template: `read_file("skills/data-cleaning/scripts/template_clean.py")`.
2.  Modify the template to implement specific cleaning logic based on Phase 1 findings.
3.  **Rule of Thumb**:
    *   **Missing Values**: Impute (mean/median/mode) if <5% missing; drop if critical; use `bfill/ffill` for time-series.
    *   **Types**: Enforce explicit types (`astype`). Convert timestamps (`pd.to_datetime`).
    *   **Output**: Prefer `parquet` for type preservation.

### Phase 3: Execute & Verify
1.  Run the script using `python_executor`.
2.  If the script fails, analyze the Traceback, fix the code, and retry.
3.  Upon success, verify the output file exists and has the expected shape.

### Phase 4: Document (The AI-Ready Standard)
Data is not "AI-Ready" without documentation.
1.  Read the standard format: `read_file("skills/data-cleaning/references/datacard_template.md")`.
2.  Generate a `README_dataset.md` summarizing:
    *   Source of data.
    *   Changes applied (e.g., "Imputed 5% missing values in 'Temperature' column").
    *   Final schema and usage constraints.