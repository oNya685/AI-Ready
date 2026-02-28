# Tool Usage Notes

Tool signatures are provided automatically via function calling.
This file documents non-obvious constraints and usage patterns.

## data_profile — Dataset Profiling

- Supports CSV, Excel (.xlsx/.xls), Parquet, JSON, JSONL
- Automatically detects file format from extension
- CSV files: tries multiple encodings (utf-8, gbk, latin1, etc.)
- Relative paths are resolved against the workspace directory
- Large datasets (>50 columns): schema is truncated to save context

## python_exec — Python Code Execution

- Executes Python code in a sandboxed subprocess (not in-process)
- Supports both absolute and relative paths for file I/O
- Timeout: default 60s, max 300s (configurable per call)
- Returns stdout on success, full stderr traceback on failure for self-correction
- Working directory is the workspace, so relative paths resolve there
- Python_exec does NOT keep state between calls. Each script runs in a completely isolated subprocess. You must import libraries and read the data in EVERY script you execute. Do not assume variables like df persist.

## exec — Safety Limits

- Commands have a configurable timeout (default 60s)
- Dangerous commands are blocked (rm -rf, format, dd, shutdown, etc.)
- Output is truncated at 10,000 characters
- `restrictToWorkspace` config can limit file access to the workspace

## cron — Scheduled Reminders

- Please refer to cron skill for usage.
