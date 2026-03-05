"""Easy Dataset MCP Server - Exposes Easy Dataset API as MCP tools."""

import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

DEFAULT_BASE_URL = "http://localhost:1717"

server = Server("easy-dataset")


def get_base_url() -> str:
    """Get Easy Dataset base URL from environment or default."""
    return os.environ.get("EASY_DATASET_URL", DEFAULT_BASE_URL)


async def api_request(
    method: str,
    path: str,
    json_data: dict | None = None,
    params: dict | None = None,
    content: bytes | None = None,
    headers: dict | None = None,
) -> dict:
    """Make HTTP request to Easy Dataset API."""
    base_url = get_base_url()
    url = f"{base_url}{path}"

    async with httpx.AsyncClient(timeout=120.0) as client:
        if method == "GET":
            response = await client.get(url, params=params)
        elif method == "POST":
            if content is not None:
                response = await client.post(url, content=content, headers=headers or {})
            else:
                response = await client.post(url, json=json_data)
        elif method == "DELETE":
            if json_data:
                import json as json_module
                response = await client.request(
                    "DELETE",
                    url,
                    params=params,
                    content=json_module.dumps(json_data).encode('utf-8'),
                    headers={"Content-Type": "application/json"}
                )
            else:
                response = await client.delete(url, params=params)
        else:
            raise ValueError(f"Unsupported method: {method}")

        if response.status_code >= 400:
            return {"error": f"HTTP {response.status_code}: {response.text}"}

        return response.json()


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        Tool(
            name="create_project",
            description="Create a new Easy Dataset project. Returns project ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Project name"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="list_projects",
            description="List all Easy Dataset projects.",
            inputSchema={"type": "object", "properties": {}},
        ),
        Tool(
            name="get_project",
            description="Get project details by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="delete_project",
            description="Delete a project by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="upload_file",
            description="Upload a file (Markdown or PDF) to a project. Returns file ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "file_path": {"type": "string", "description": "Local file path to upload"},
                },
                "required": ["project_id", "file_path"],
            },
        ),
        Tool(
            name="list_files",
            description="List files in a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "page": {"type": "integer", "description": "Page number (default 1)"},
                    "page_size": {"type": "integer", "description": "Page size (default 10)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="delete_file",
            description="Delete a file from a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "file_id": {"type": "string", "description": "File ID to delete"},
                },
                "required": ["project_id", "file_id"],
            },
        ),
        Tool(
            name="split_text",
            description="Split uploaded files into text chunks using AI. Requires a configured model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "file_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of file names to split (must be uploaded first)",
                    },
                    "model": {"type": "string", "description": "Model config ID or modelId (optional, auto-selects if not specified or invalid)"},
                    "language": {"type": "string", "description": "Language for AI processing: 'zh' (default) or 'en'"},
                },
                "required": ["project_id", "file_names"],
            },
        ),
        Tool(
            name="list_chunks",
            description="List text chunks in a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="generate_questions",
            description="Generate questions from text chunks using AI. Submits a task for async processing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "chunk_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of chunk IDs (optional, uses all if empty)",
                    },
                    "model": {"type": "string", "description": "Model config ID or modelId (optional, auto-selects if not specified)"},
                    "language": {"type": "string", "description": "Language (default: zh-CN)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_questions",
            description="List questions in a project (question tree).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="generate_answer",
            description="Generate answer for a single question using AI.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "question_id": {"type": "string", "description": "Question ID"},
                    "model": {"type": "string", "description": "Model ID for answer generation"},
                    "language": {"type": "string", "description": "Language (default: zh)"},
                },
                "required": ["project_id", "question_id", "model"],
            },
        ),
        Tool(
            name="generate_answers_batch",
            description="Generate answers for all questions in batch using AI. Submits a task for async processing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "model": {"type": "string", "description": "Model config ID or modelId (optional, auto-selects if not specified)"},
                    "language": {"type": "string", "description": "Language (default: zh-CN)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="clean_data",
            description="Clean data for text chunks using AI. Submits a task for async processing to remove noise and improve quality.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "chunk_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of chunk IDs to clean (optional, cleans all if empty)",
                    },
                    "model": {"type": "string", "description": "Model config ID or modelId (optional, auto-selects if not specified)"},
                    "language": {"type": "string", "description": "Language (default: zh-CN)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="evaluate_datasets",
            description="Evaluate dataset quality using AI. Submits a task for async processing to assess all un-evaluated QA pairs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "model": {"type": "string", "description": "Model config ID or modelId (optional, auto-selects if not specified)"},
                    "language": {"type": "string", "description": "Language (default: zh-CN)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="list_datasets",
            description="List generated datasets (QA pairs) in a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "page": {"type": "integer", "description": "Page number (default 1)"},
                    "size": {"type": "integer", "description": "Page size (default 10)"},
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="export_dataset",
            description="Export dataset in specified format (alpaca, sharegpt, etc.).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "format": {
                        "type": "string",
                        "description": "Export format: alpaca, sharegpt, multilingual-thinking",
                        "default": "alpaca",
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status: confirmed, unconfirmed, or all",
                    },
                    "system_prompt": {
                        "type": "string",
                        "description": "Custom system prompt (optional)",
                    },
                },
                "required": ["project_id"],
            },
        ),
        Tool(
            name="configure_model",
            description="Configure a model provider for the project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "provider_id": {"type": "string", "description": "Provider ID (e.g., openai, ollama)"},
                    "endpoint": {"type": "string", "description": "API endpoint URL"},
                    "api_key": {"type": "string", "description": "API key"},
                    "model_name": {"type": "string", "description": "Model name/ID"},
                },
                "required": ["project_id", "provider_id", "model_name"],
            },
        ),
        Tool(
            name="list_model_configs",
            description="List model configurations for a project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                },
                "required": ["project_id"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Execute a tool call."""
    try:
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def execute_tool(name: str, args: dict[str, Any]) -> dict:
    """Execute the actual tool logic."""

    if name == "create_project":
        return await api_request("POST", "/api/projects", json_data={
            "name": args["name"],
            "description": args.get("description", f"Project: {args['name']}")
        })

    elif name == "list_projects":
        return await api_request("GET", "/api/projects")

    elif name == "get_project":
        return await api_request("GET", f"/api/projects/{args['project_id']}")

    elif name == "delete_project":
        return await api_request("DELETE", f"/api/projects/{args['project_id']}")

    elif name == "upload_file":
        project_id = args["project_id"]
        file_path = Path(args["file_path"])

        if not file_path.exists():
            return {"error": f"File not found: {file_path}"}

        content = file_path.read_bytes()
        file_name = file_path.name

        # Encode filename for HTTP header (RFC 5987)
        encoded_file_name = quote(file_name, safe='')

        return await api_request(
            "POST",
            f"/api/projects/{project_id}/files",
            content=content,
            headers={"x-file-name": encoded_file_name},
        )

    elif name == "list_files":
        project_id = args["project_id"]
        params = {"page": args.get("page", 1), "pageSize": args.get("page_size", 10)}
        return await api_request("GET", f"/api/projects/{project_id}/files", params=params)

    elif name == "delete_file":
        project_id = args["project_id"]
        file_id = args["file_id"]
        return await api_request(
            "DELETE",
            f"/api/projects/{project_id}/files",
            params={"fileId": file_id, "domainTreeAction": "revise"},
            json_data={"model": {}, "language": "中文"},
        )

    elif name == "split_text":
        project_id = args["project_id"]

        file_names = args.get("file_names", [])

        # Get file list from API to find file IDs
        files_result = await api_request("GET", f"/api/projects/{project_id}/files", params={"page": 1, "pageSize": 100})
        files_map = {f["fileName"]: f for f in files_result.get("data", [])}

        # Build file objects with fileName and fileId
        file_objects = []
        for fn in file_names:
            file_info = files_map.get(fn)
            if file_info:
                file_objects.append({"fileName": fn, "fileId": file_info["id"]})
            else:
                file_objects.append({"fileName": fn})

        # Get model configuration
        model_config_id = args.get("model", "")
        model_configs = await api_request("GET", f"/api/projects/{project_id}/model-config")
        model_config = None

        # First try to find by ID or modelId if specified
        if model_config_id:
            for mc in model_configs.get("data", []):
                if mc["id"] == model_config_id or mc["modelId"] == model_config_id:
                    model_config = mc
                    break

        # If not found or no API key, find a working model with API key
        if not model_config or not model_config.get("apiKey"):
            for mc in model_configs.get("data", []):
                if mc.get("apiKey") and mc.get("modelId"):
                    model_config = mc
                    break

        if not model_config:
            return {"error": f"No working model configuration found. Please configure a model with API key first."}

        json_data = {
            "fileNames": file_objects,
            "model": model_config,
            "language": args.get("language", "zh"),
        }
        return await api_request("POST", f"/api/projects/{project_id}/split", json_data=json_data)

    elif name == "list_chunks":
        return await api_request("GET", f"/api/projects/{args['project_id']}/split")

    elif name == "generate_questions":
        project_id = args["project_id"]

        model_configs = await api_request("GET", f"/api/projects/{project_id}/model-config")
        model_config = None
        model_id = args.get("model", "")

        if model_id:
            for mc in model_configs.get("data", []):
                if mc["id"] == model_id or mc["modelId"] == model_id:
                    model_config = mc
                    break

        if not model_config or not model_config.get("apiKey"):
            for mc in model_configs.get("data", []):
                if mc.get("apiKey") and mc.get("modelId"):
                    model_config = mc
                    break

        if not model_config:
            return {"error": "No working model configuration found. Please configure a model with API key first."}

        json_data = {
            "taskType": "question-generation",
            "modelInfo": model_config,
            "language": args.get("language", "zh-CN"),
            "detail": "批量生成问题任务",
        }
        if args.get("chunk_ids"):
            json_data["chunkIds"] = args["chunk_ids"]

        return await api_request("POST", f"/api/projects/{project_id}/tasks", json_data=json_data)

    elif name == "list_questions":
        return await api_request("GET", f"/api/projects/{args['project_id']}/questions/tree")

    elif name == "generate_answer":
        project_id = args["project_id"]
        json_data = {
            "questionId": args["question_id"],
            "model": args["model"],
            "language": args.get("language", "zh"),
        }
        return await api_request("POST", f"/api/projects/{project_id}/datasets", json_data=json_data)

    elif name == "generate_answers_batch":
        project_id = args["project_id"]

        model_configs = await api_request("GET", f"/api/projects/{project_id}/model-config")
        model_config = None
        model_id = args.get("model", "")

        if model_id:
            for mc in model_configs.get("data", []):
                if mc["id"] == model_id or mc["modelId"] == model_id:
                    model_config = mc
                    break

        if not model_config or not model_config.get("apiKey"):
            for mc in model_configs.get("data", []):
                if mc.get("apiKey") and mc.get("modelId"):
                    model_config = mc
                    break

        if not model_config:
            return {"error": "No working model configuration found. Please configure a model with API key first."}

        json_data = {
            "taskType": "answer-generation",
            "modelInfo": model_config,
            "language": args.get("language", "zh-CN"),
        }

        return await api_request("POST", f"/api/projects/{project_id}/tasks", json_data=json_data)

    elif name == "clean_data":
        project_id = args["project_id"]

        model_configs = await api_request("GET", f"/api/projects/{project_id}/model-config")
        model_config = None
        model_id = args.get("model", "")

        if model_id:
            for mc in model_configs.get("data", []):
                if mc["id"] == model_id or mc["modelId"] == model_id:
                    model_config = mc
                    break

        if not model_config or not model_config.get("apiKey"):
            for mc in model_configs.get("data", []):
                if mc.get("apiKey") and mc.get("modelId"):
                    model_config = mc
                    break

        if not model_config:
            return {"error": "No working model configuration found. Please configure a model with API key first."}

        json_data = {
            "taskType": "data-cleaning",
            "modelInfo": model_config,
            "language": args.get("language", "zh-CN"),
            "detail": "批量数据清洗任务",
        }

        if args.get("chunk_ids"):
            json_data["note"] = {"chunkIds": args["chunk_ids"]}

        return await api_request("POST", f"/api/projects/{project_id}/tasks", json_data=json_data)

    elif name == "evaluate_datasets":
        project_id = args["project_id"]

        model_configs = await api_request("GET", f"/api/projects/{project_id}/model-config")
        model_config = None
        model_id = args.get("model", "")

        if model_id:
            for mc in model_configs.get("data", []):
                if mc["id"] == model_id or mc["modelId"] == model_id:
                    model_config = mc
                    break

        if not model_config or not model_config.get("apiKey"):
            for mc in model_configs.get("data", []):
                if mc.get("apiKey") and mc.get("modelId"):
                    model_config = mc
                    break

        if not model_config:
            return {"error": "No working model configuration found. Please configure a model with API key first."}

        json_data = {
            "model": model_config,
            "language": args.get("language", "zh-CN"),
        }

        return await api_request("POST", f"/api/projects/{project_id}/datasets/batch-evaluate", json_data=json_data)

    elif name == "list_datasets":
        project_id = args["project_id"]
        params = {"page": args.get("page", 1), "size": args.get("size", 10)}
        return await api_request("GET", f"/api/projects/{project_id}/datasets", params=params)

    elif name == "export_dataset":
        project_id = args["project_id"]
        json_data = {
            "format": args.get("format", "alpaca"),
        }
        if args.get("status"):
            json_data["status"] = args["status"]
        if args.get("system_prompt"):
            json_data["systemPrompt"] = args["system_prompt"]
        return await api_request("POST", f"/api/projects/{project_id}/datasets/export", json_data=json_data)

    elif name == "configure_model":
        project_id = args["project_id"]
        model_name = args["model_name"]
        provider_id = args["provider_id"]

        # Build complete model config with all required fields
        json_data = {
            "providerId": provider_id,
            "providerName": provider_id,  # Use providerId as providerName if not specified
            "modelName": model_name,
            "modelId": model_name,  # API requires both modelId and modelName
            "endpoint": args.get("endpoint", ""),
            "apiKey": args.get("api_key", ""),
            "type": "text",
            "temperature": 0.7,
            "maxTokens": 8192,
            "topP": 0.9,
            "topK": 0,
            "status": 1,
        }
        return await api_request("POST", f"/api/projects/{project_id}/model-config", json_data=json_data)

    elif name == "list_model_configs":
        return await api_request("GET", f"/api/projects/{args['project_id']}/model-config")

    else:
        return {"error": f"Unknown tool: {name}"}


async def run_server():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    """Entry point."""
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
