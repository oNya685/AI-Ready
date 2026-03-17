"""Data profiling tool for analyzing datasets."""

import json
import os
from pathlib import Path
from typing import Any

import pandas as pd

from nanodata.agent.tools.base import Tool


class DataProfileTool(Tool):
    """Profile a dataset file (CSV, Excel, Parquet) and return structured metadata."""

    name = "data_profile"
    description = (
        "Analyze a local dataset file (CSV, Excel, Parquet) and return its schema, "
        "statistics, and sample data. Use this before processing any dataset."
    )
    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the data file. Supports both absolute paths (e.g., /home/user/data.csv, D:\\data.csv) and relative paths (e.g., data.csv, ./data.csv). Relative paths are resolved against your workspace directory.",
            }
        },
        "required": ["file_path"],
    }

    def __init__(self, workspace: Path | None = None):
        self._workspace = workspace

    async def execute(self, file_path: str, **kwargs: Any) -> str:
        """
        Profile a dataset file and return structured information.

        Args:
            file_path: Path to the data file.

        Returns:
            Markdown formatted string with dataset profile information.
        """
        try:
            # Resolve file path: relative paths are resolved against workspace
            path = Path(file_path).expanduser()
            if not path.is_absolute() and self._workspace:
                path = self._workspace / path
            path = path.resolve()

            # Check if file exists
            if not path.exists():
                return f"Error: File not found at `{file_path}` (resolved to `{path}`)"

            if not path.is_file():
                return f"Error: Path is not a file: `{file_path}`"

            # Detect file type and read
            suffix = path.suffix.lower()
            df, read_info = self._read_file(path, suffix)

            if df is None:
                return f"Error: Failed to read file. {read_info}"

            # Build profile
            profile = self._build_profile(df, path, read_info)

            return profile

        except Exception as e:
            return f"Error profiling data: {str(e)}"

    def _read_file(self, path: Path, suffix: str) -> tuple[pd.DataFrame | None, str]:
        """
        Read file based on extension with fallback encodings.

        Returns:
            Tuple of (DataFrame or None, info message)
        """
        try:
            if suffix == ".csv":
                return self._read_csv(path)
            elif suffix in [".xlsx", ".xls"]:
                df = pd.read_excel(path)
                return df, f"Read as Excel ({suffix})"
            elif suffix == ".parquet":
                df = pd.read_parquet(path)
                return df, f"Read as Parquet ({suffix})"
            elif suffix == ".json":
                df = pd.read_json(path)
                return df, f"Read as JSON ({suffix})"
            elif suffix == ".jsonl":
                df = pd.read_json(path, lines=True)
                return df, f"Read as JSON Lines ({suffix})"
            else:
                # Try CSV as fallback
                return self._read_csv(path)
        except Exception as e:
            return None, str(e)

    def _read_csv(self, path: Path) -> tuple[pd.DataFrame | None, str]:
        """Read CSV with encoding fallback."""
        encodings = ["utf-8", "utf-8-sig", "gbk", "gb2312", "latin1", "cp1252"]
        errors = []

        for encoding in encodings:
            try:
                df = pd.read_csv(path, encoding=encoding)
                return df, f"Read as CSV (encoding: {encoding})"
            except UnicodeDecodeError as e:
                errors.append(f"{encoding}: {e}")
                continue
            except Exception as e:
                errors.append(f"{encoding}: {e}")
                break

        return None, f"Failed to read CSV with encodings: {'; '.join(errors)}"

    def _build_profile(self, df: pd.DataFrame, path: Path, read_info: str) -> str:
        """Build markdown profile of the dataset."""
        lines = []

        # Header
        lines.append(f"# Data Profile: `{path.name}`")
        lines.append("")
        lines.append(f"- **Full Path**: `{path}`")
        lines.append(f"- **File Size**: {self._format_file_size(path.stat().st_size)}")
        lines.append(f"- **Read Method**: {read_info}")
        lines.append("")

        # Basic stats
        total_rows = len(df)
        total_cols = len(df.columns)
        lines.append("## Basic Statistics")
        lines.append("")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Total Rows | {total_rows:,} |")
        lines.append(f"| Total Columns | {total_cols:,} |")
        lines.append(f"| Memory Usage | {self._format_memory(df.memory_usage(deep=True).sum())} |")
        lines.append("")

        # Column schema
        lines.append("## Column Schema")
        lines.append("")

        # Truncate if too many columns
        truncated = False
        display_cols = list(df.columns)
        if total_cols > 50:
            display_cols = display_cols[:50]
            truncated = True

        lines.append(f"| # | Column Name | Data Type | Non-Null Count | Null % | Unique Values |")
        lines.append(f"|---|-------------|-----------|----------------|--------|---------------|")

        for idx, col in enumerate(display_cols, 1):
            dtype = str(df[col].dtype)
            non_null = df[col].notna().sum()
            null_pct = (df[col].isna().sum() / total_rows) * 100
            unique = df[col].nunique()

            lines.append(
                f"| {idx} | `{col}` | `{dtype}` | {non_null:,} | {null_pct:.1f}% | {unique:,} |"
            )

        if truncated:
            lines.append("")
            lines.append(
                "> **Warning**: Truncated to 50 columns to save context window. "
                f"({total_cols - 50} columns omitted)"
            )

        lines.append("")

        # Sample data
        lines.append("## Sample Data (First 5 Rows)")
        lines.append("")

        sample_df = df[display_cols].head(5)

        # Build markdown table
        header = "| " + " | ".join(f"`{c}`" for c in sample_df.columns) + " |"
        separator = "|" + "|".join("---" for _ in sample_df.columns) + "|"

        lines.append(header)
        lines.append(separator)

        for _, row in sample_df.iterrows():
            row_values = []
            for val in row:
                if pd.isna(val):
                    row_values.append("*null*")
                else:
                    # Truncate long strings
                    val_str = str(val)
                    if len(val_str) > 100:
                        val_str = val_str[:97] + "..."
                    row_values.append(val_str.replace("|", "\\|").replace("\n", " "))
            lines.append("| " + " | ".join(row_values) + " |")

        if truncated:
            lines.append("")
            lines.append("> Sample data only shows the first 50 columns (see warning above).")

        lines.append("")

        # Data type summary
        lines.append("## Data Type Summary")
        lines.append("")
        dtype_counts = df.dtypes.value_counts()
        for dtype, count in dtype_counts.items():
            lines.append(f"- `{dtype}`: {count} column(s)")

        return "\n".join(lines)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.2f} PB"

    def _format_memory(self, size_bytes: int) -> str:
        """Format memory usage in human readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.2f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
