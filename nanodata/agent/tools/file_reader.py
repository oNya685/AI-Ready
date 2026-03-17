"""File reader tools for reading specific line ranges."""

from pathlib import Path
from typing import Any

from nanodata.agent.tools.base import Tool


class ReadFileLinesTool(Tool):
    """Tool to read specific line ranges from a file."""

    def __init__(self, workspace: Path | None = None, allowed_dir: Path | None = None):
        self._workspace = workspace
        self._allowed_dir = allowed_dir

    def _resolve_path(self, path: str) -> Path:
        """Resolve path against workspace (if relative) and enforce directory restriction."""
        p = Path(path).expanduser()
        if not p.is_absolute() and self._workspace:
            p = self._workspace / p
        resolved = p.resolve()
        if self._allowed_dir:
            try:
                resolved.relative_to(self._allowed_dir.resolve())
            except ValueError:
                raise PermissionError(f"Path {path} is outside allowed directory {self._allowed_dir}")
        return resolved

    @property
    def name(self) -> str:
        return "read_file_lines"

    @property
    def description(self) -> str:
        return "Read specific line ranges from a file. Returns lines with line numbers."

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The file path to read"
                },
                "start_line": {
                    "type": "integer",
                    "description": "Starting line number (1-indexed, default: 1)",
                    "minimum": 1,
                    "default": 1
                },
                "end_line": {
                    "type": "integer",
                    "description": "Ending line number (inclusive, default: 50)",
                    "minimum": 1,
                    "default": 50
                },
                "max_line_length": {
                    "type": "integer",
                    "description": "Maximum characters per line before truncation (default: 500)",
                    "minimum": 10,
                    "default": 500
                }
            },
            "required": ["file_path"]
        }

    async def execute(
        self,
        file_path: str,
        start_line: int = 1,
        end_line: int = 50,
        max_line_length: int = 500,
        **kwargs: Any
    ) -> str:
        try:
            resolved_path = self._resolve_path(file_path)

            if not resolved_path.exists():
                return f"Error: File not found: {file_path}"

            if not resolved_path.is_file():
                return f"Error: Not a file: {file_path}"

            # Try to read as UTF-8 text
            try:
                with open(resolved_path, "r", encoding="utf-8") as f:
                    all_lines = f.readlines()
            except UnicodeDecodeError:
                return "[ERROR] This is a binary file. Cannot read as text. Please write a Python script using libraries like h5py or netCDF4 to inspect its structure."

            # Handle 1-indexed to 0-indexed conversion
            start_idx = max(0, start_line - 1)
            end_idx = min(len(all_lines), end_line)

            if start_idx >= len(all_lines):
                return f"Error: Start line {start_line} exceeds file length ({len(all_lines)} lines)"

            result_lines = []
            for i in range(start_idx, end_idx):
                line_num = i + 1  # Convert back to 1-indexed for output
                line_content = all_lines[i]

                # Handle lines that might not end with newline
                if line_content.endswith("\n"):
                    line_content = line_content[:-1]

                # Truncate if line exceeds max_line_length
                if len(line_content) > max_line_length:
                    truncated = line_content[:max_line_length] + f" ... [Truncated: original length {len(line_content)}]"
                    result_lines.append(f"Line {line_num}: {truncated}")
                else:
                    result_lines.append(f"Line {line_num}: {line_content}")

            if not result_lines:
                return f"No lines in range {start_line}-{end_line} (file has {len(all_lines)} lines)"

            return "\n".join(result_lines)

        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {str(e)}"