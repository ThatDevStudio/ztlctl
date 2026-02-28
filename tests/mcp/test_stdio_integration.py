"""End-to-end MCP stdio integration tests (requires the mcp extra)."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest

if importlib.util.find_spec("mcp") is None or importlib.util.find_spec("anyio") is None:
    pytest.skip("mcp extra not installed", allow_module_level=True)


def _tool_payload(result: Any) -> dict[str, Any]:
    structured = getattr(result, "structuredContent", None)
    if isinstance(structured, dict):
        return structured

    content = getattr(result, "content", [])
    if content:
        text = getattr(content[0], "text", None)
        if isinstance(text, str):
            return json.loads(text)

    raise AssertionError("Tool result did not expose structured or text content")


def _resource_text(result: Any) -> str:
    contents = getattr(result, "contents", [])
    assert contents, "Resource response did not include contents"
    text = getattr(contents[0], "text", None)
    assert isinstance(text, str), "Resource response did not include text content"
    return text


def _prompt_text(result: Any) -> str:
    messages = getattr(result, "messages", [])
    texts: list[str] = []
    for message in messages:
        content = getattr(message, "content", None)
        text = getattr(content, "text", None)
        if isinstance(text, str):
            texts.append(text)
    return "\n".join(texts)


async def _exercise_stdio_server(config_path: Path) -> None:
    from mcp.client.stdio import stdio_client

    from mcp import ClientSession, StdioServerParameters

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "ztlctl", "--sync", "-c", str(config_path), "serve", "--transport", "stdio"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools = await session.list_tools()
            tool_names = {tool.name for tool in tools.tools}
            assert {"create_note", "get_document", "discover_tools"} <= tool_names

            resources = await session.list_resources()
            resource_uris = {str(resource.uri) for resource in resources.resources}
            assert "ztlctl://overview" in resource_uris
            assert "ztlctl://context" in resource_uris

            prompts = await session.list_prompts()
            prompt_names = {prompt.name for prompt in prompts.prompts}
            assert "vault_orientation" in prompt_names

            create_result = await session.call_tool("create_note", arguments={"title": "MCP Note"})
            create_payload = _tool_payload(create_result)
            assert create_payload["ok"] is True
            created_id = create_payload["data"]["id"]

            get_result = await session.call_tool(
                "get_document",
                arguments={"content_id": created_id},
            )
            get_payload = _tool_payload(get_result)
            assert get_payload["ok"] is True
            assert get_payload["data"]["id"] == created_id

            overview_result = await session.read_resource("ztlctl://overview")
            overview = json.loads(_resource_text(overview_result))
            assert overview["total"] >= 1

            prompt_result = await session.get_prompt("vault_orientation")
            assert _prompt_text(prompt_result).strip()


def test_stdio_transport_end_to_end(tmp_path: Path) -> None:
    import anyio

    config_path = tmp_path / "ztlctl.toml"
    config_path.write_text(
        '[vault]\nname = "mcp-test"\nclient = "vanilla"\n\n[agent]\ntone = "minimal"\n',
        encoding="utf-8",
    )

    anyio.run(_exercise_stdio_server, config_path)
