"""Built-in MCP Servers for NanoBot."""

from pathlib import Path

MCP_SERVERS_DIR = Path(__file__).parent


def get_easy_dataset_server_path() -> Path:
    """Get the path to the Easy Dataset MCP server script."""
    return MCP_SERVERS_DIR / "easy_dataset_server.py"
