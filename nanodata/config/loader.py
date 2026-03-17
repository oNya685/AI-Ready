"""Configuration loading utilities."""

import json
import sys
from pathlib import Path

from nanodata.config.schema import Config


def get_config_path() -> Path:
    """Get the default configuration file path."""
    return Path.home() / ".nanodata" / "config.json"


def get_data_dir() -> Path:
    """Get the nanodata data directory."""
    from nanodata.utils.helpers import get_data_path
    return get_data_path()


def get_builtin_mcp_servers() -> dict:
    """Get built-in MCP server configurations."""
    from nanodata.mcp_servers import get_easy_dataset_server_path

    return {
        "easy-dataset": {
            "command": sys.executable,
            "args": [str(get_easy_dataset_server_path())],
            "env": {
                "EASY_DATASET_URL": "http://localhost:1717"
            },
            "toolTimeout": 120
        }
    }


def load_config(config_path: Path | None = None) -> Config:
    """
    Load configuration from file or create default.

    Args:
        config_path: Optional path to config file. Uses default if not provided.

    Returns:
        Loaded configuration object.
    """
    path = config_path or get_config_path()

    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data = _migrate_config(data)
            data = _add_builtin_mcp_servers(data)
            return Config.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Failed to load config from {path}: {e}")
            print("Using default configuration.")

    config = Config()
    return _inject_builtin_mcp_servers(config)


def save_config(config: Config, config_path: Path | None = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration to save.
        config_path: Optional path to save to. Uses default if not provided.
    """
    path = config_path or get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = config.model_dump(by_alias=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _migrate_config(data: dict) -> dict:
    """Migrate old config formats to current."""
    # Move tools.exec.restrictToWorkspace → tools.restrictToWorkspace
    tools = data.get("tools", {})
    exec_cfg = tools.get("exec", {})
    if "restrictToWorkspace" in exec_cfg and "restrictToWorkspace" not in tools:
        tools["restrictToWorkspace"] = exec_cfg.pop("restrictToWorkspace")
    return data


def _add_builtin_mcp_servers(data: dict) -> dict:
    """Add built-in MCP servers to config data if not already present."""
    tools = data.setdefault("tools", {})
    mcp_servers = tools.setdefault("mcpServers", {})

    builtin = get_builtin_mcp_servers()
    for name, config in builtin.items():
        if name not in mcp_servers:
            mcp_servers[name] = config

    return data


def _inject_builtin_mcp_servers(config: Config) -> Config:
    """Inject built-in MCP servers into Config object."""
    builtin = get_builtin_mcp_servers()
    for name, server_config in builtin.items():
        if name not in config.tools.mcp_servers:
            from nanodata.config.schema import MCPServerConfig
            config.tools.mcp_servers[name] = MCPServerConfig(
                command=server_config["command"],
                args=server_config["args"],
                env=server_config.get("env", {}),
                tool_timeout=server_config.get("toolTimeout", 30)
            )
    return config
