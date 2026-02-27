"""Python code execution tool for data processing."""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from nanobot.agent.tools.base import Tool


class PythonDataExecTool(Tool):
    """Execute Python code in a subprocess for data processing."""

    name = "python_exec"
    description = (
        "Execute Python code in a sandboxed subprocess. "
        "Use this to process data with pandas, numpy, etc. "
        "Returns stdout on success or stderr traceback on failure for self-correction."
    )
    parameters = {
        "type": "object",
        "properties": {
            "script_code": {
                "type": "string",
                "description": "Python code to execute. Supports both absolute paths (e.g., /home/user/data.csv) and relative paths (e.g., data.csv, ./data.csv). Relative paths are resolved against the workspace directory.",
            },
            "timeout": {
                "type": "integer",
                "description": "Maximum execution time in seconds. Default is 60 seconds.",
                "default": 60,
                "minimum": 1,
                "maximum": 300,
            }
        },
        "required": ["script_code"],
    }

    def __init__(self, workspace: Path | None = None, timeout: int = 60):
        self._workspace = workspace or Path.cwd()
        self._timeout = timeout

    async def execute(self, script_code: str, timeout: int = 60, **kwargs: Any) -> str:
        """
        Execute Python code in a subprocess.

        Args:
            script_code: Python code string to execute.
            timeout: Maximum execution time in seconds (default: 60).

        Returns:
            Execution result with stdout or stderr traceback.
        """
        # Create temporary file for the script
        script_path = None
        try:
            # Write script to temp file in system temp directory
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                delete=False,
                encoding="utf-8",
            ) as f:
                f.write(script_code)
                script_path = f.name

            # Build command: run python with the script
            # Use the same python executable to ensure environment consistency
            import sys

            cmd = [sys.executable, script_path]

            # Set up environment with UTF-8 encoding for consistent output handling
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"

            # Execute in subprocess
            # Working directory is workspace, so relative paths in script resolve to workspace
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(self._workspace),
                env=env,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
            except asyncio.TimeoutError:
                # Kill the process on timeout
                process.kill()
                try:
                    await asyncio.wait_for(process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    pass
                return f"Execution Failed.\nError Traceback:\nTimeout: Script execution exceeded {timeout} seconds"

            # Decode outputs
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Log outputs for debugging
            logger.debug("python_exec: script_path={}", script_path)
            logger.debug("python_exec: return_code={}", process.returncode)
            if stdout_text:
                logger.debug("python_exec: stdout=\n{}", stdout_text)
            if stderr_text:
                logger.debug("python_exec: stderr=\n{}", stderr_text)

            # Check return code
            if process.returncode == 0:
                # Success
                output = stdout_text.strip() if stdout_text.strip() else "(no output)"
                return f"Execution Successful.\nOutput:\n{output}"
            else:
                # Failure - return stderr for self-correction
                error_msg = stderr_text.strip() if stderr_text.strip() else "(unknown error)"
                return f"Execution Failed.\nError Traceback:\n{error_msg}"

        except Exception as e:
            return f"Execution Failed.\nError Traceback:\n{str(e)}"

        finally:
            # Clean up temp file
            if script_path and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception:
                    pass
