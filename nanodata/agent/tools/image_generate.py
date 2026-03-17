"""Image generation tool (OpenAI-compatible API)."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import httpx

from nanodata.agent.tools.base import Tool


def _resolve_path(path: str, workspace: Path | None = None, allowed_dir: Path | None = None) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute() and workspace:
        p = workspace / p
    resolved = p.resolve()
    if allowed_dir:
        try:
            resolved.relative_to(allowed_dir.resolve())
        except ValueError:
            raise PermissionError(f"Path {path} is outside allowed directory {allowed_dir}")
    return resolved


def _prompt_hash(prompt: str) -> str:
    return hashlib.sha1(prompt.encode("utf-8")).hexdigest()[:12]


def _relative_to_workspace(path: Path, workspace: Path | None) -> str:
    if not workspace:
        return str(path)
    try:
        return str(path.relative_to(workspace))
    except ValueError:
        return str(path)


class ImageGenerateTool(Tool):
    """Generate image(s) from prompt(s) and save to disk."""

    def __init__(self, workspace: Path | None = None, allowed_dir: Path | None = None):
        self._workspace = workspace
        self._allowed_dir = allowed_dir

    @property
    def name(self) -> str:
        return "image_generate"

    @property
    def description(self) -> str:
        return (
            "Generate one or more images from prompt(s) using an OpenAI-compatible image API, "
            "saving the images to disk. Supports batch mode with concurrent requests."
        )

    @property
    def parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt for a single image"},
                "items": {
                    "type": "array",
                    "description": "Batch items with prompts",
                    "items": {
                        "type": "object",
                        "properties": {
                            "prompt": {"type": "string"},
                            "output_path": {"type": "string"},
                        },
                        "required": ["prompt"],
                    },
                },
                "output_dir": {"type": "string", "description": "Directory to save images"},
                "output_path": {"type": "string", "description": "File path for single-image output"},
                "filename_prefix": {"type": "string", "description": "Filename prefix for batch outputs"},
                "model": {"type": "string", "description": "Image model id"},
                "size": {"type": "string", "description": "Image size, e.g. 1024x1024"},
                "response_format": {"type": "string", "description": "url or b64_json"},
                "api_base": {"type": "string", "description": "API base URL"},
                "api_key": {"type": "string", "description": "API key"},
                "endpoint": {"type": "string", "description": "Image generation endpoint"},
                "max_parallel": {"type": "integer", "description": "Max parallel requests", "minimum": 1},
                "timeout_s": {"type": "number", "description": "HTTP timeout in seconds", "minimum": 1},
            },
        }

    async def execute(
        self,
        prompt: str | None = None,
        items: list[dict] | None = None,
        output_dir: str | None = None,
        output_path: str | None = None,
        filename_prefix: str | None = None,
        model: str | None = None,
        size: str | None = None,
        response_format: str | None = None,
        api_base: str | None = None,
        api_key: str | None = None,
        endpoint: str | None = None,
        max_parallel: int = 4,
        timeout_s: float = 60.0,
        **kwargs: Any,
    ) -> str:
        if prompt and items:
            return "Error: Provide either 'prompt' or 'items', not both."
        if not prompt and not items:
            return "Error: Missing 'prompt' or 'items'."

        api_base = api_base or os.environ.get("IMAGE_API_BASE_URL", "https://api.openai.com/v1")
        api_key = api_key or os.environ.get("IMAGE_API_KEY", "")
        model = model or os.environ.get("IMAGE_MODEL", "gpt-image-1")
        size = size or os.environ.get("IMAGE_SIZE", "1024x1024")
        response_format = response_format or os.environ.get("IMAGE_RESPONSE_FORMAT", "url")
        endpoint = endpoint or os.environ.get("IMAGE_ENDPOINT", "/images/generations")

        if not api_key:
            return "Error: IMAGE_API_KEY is required (or pass api_key)."
        if response_format not in {"url", "b64_json"}:
            return "Error: response_format must be 'url' or 'b64_json'."

        if items is None:
            items = [{"prompt": prompt}]
        if output_path and len(items) > 1:
            return "Error: Use output_dir for batch generation (output_path is for single image)."

        resolved_output_dir: Path | None = None
        if output_path:
            out_path = _resolve_path(output_path, self._workspace, self._allowed_dir)
            if out_path.exists() and out_path.is_dir():
                resolved_output_dir = out_path
                output_path = None
            else:
                out_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            resolved_output_dir = _resolve_path(
                output_dir or "generated_images",
                self._workspace,
                self._allowed_dir,
            )
            resolved_output_dir.mkdir(parents=True, exist_ok=True)

        prefix = filename_prefix or "img"
        workspace = self._workspace

        async def _download(client: httpx.AsyncClient, url: str, out_path: Path) -> None:
            resp = await client.get(url, timeout=timeout_s)
            resp.raise_for_status()
            out_path.write_bytes(resp.content)

        async def _generate_one(idx: int, item: dict, client: httpx.AsyncClient, sem: asyncio.Semaphore) -> dict:
            prompt_text = str(item.get("prompt", "")).strip()
            if not prompt_text:
                return {"status": "failed", "error": "Empty prompt", "prompt": ""}

            if output_path:
                out_path = _resolve_path(output_path, self._workspace, self._allowed_dir)
            else:
                out_dir = resolved_output_dir or _resolve_path(
                    output_dir or "generated_images", self._workspace, self._allowed_dir
                )
                out_dir.mkdir(parents=True, exist_ok=True)
                filename = f"{prefix}_{idx:06d}_{_prompt_hash(prompt_text)}.png"
                out_path = out_dir / filename

            payload = {
                "model": model,
                "prompt": prompt_text,
                "size": size,
                "n": 1,
                "response_format": response_format,
            }

            async with sem:
                resp = await client.post(
                    f"{api_base}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=timeout_s,
                )

            if resp.status_code >= 400:
                return {
                    "status": "failed",
                    "error": f"HTTP {resp.status_code}: {resp.text[:500]}",
                    "prompt": prompt_text,
                }

            data = resp.json()
            data_items = data.get("data") or []
            if not data_items:
                return {"status": "failed", "error": "No image data", "prompt": prompt_text}

            item0 = data_items[0]
            if response_format == "b64_json" or "b64_json" in item0:
                b64 = item0.get("b64_json")
                if not b64:
                    return {"status": "failed", "error": "Missing b64_json", "prompt": prompt_text}
                out_path.write_bytes(base64.b64decode(b64))
            else:
                url = item0.get("url")
                if not url:
                    return {"status": "failed", "error": "Missing url", "prompt": prompt_text}
                await _download(client, url, out_path)

            return {
                "status": "success",
                "prompt": prompt_text,
                "image_path": _relative_to_workspace(out_path, workspace),
                "model": model,
                "size": size,
                "response_format": response_format,
            }

        limits = httpx.Limits(max_connections=max_parallel * 2, max_keepalive_connections=max_parallel)
        semaphore = asyncio.Semaphore(max_parallel)
        async with httpx.AsyncClient(limits=limits) as client:
            tasks = [
                _generate_one(i, item, client, semaphore)
                for i, item in enumerate(items, start=1)
            ]
            results = await asyncio.gather(*tasks)

        summary = {
            "count": len(results),
            "success": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "results": results,
        }
        return json.dumps(summary, ensure_ascii=False)
