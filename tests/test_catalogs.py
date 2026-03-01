"""Tests for shared public-surface catalogs."""

from __future__ import annotations

from ztlctl.catalogs import (
    mcp_prompt_catalog,
    mcp_resource_catalog,
    mcp_tool_catalog,
    workflow_asset_manifest,
)


def test_shared_catalogs_are_non_empty() -> None:
    assert len(mcp_tool_catalog()) >= 1
    assert len(mcp_resource_catalog()) >= 1
    assert len(mcp_prompt_catalog()) >= 1


def test_workflow_manifest_references_known_surfaces() -> None:
    manifest = workflow_asset_manifest()
    tool_names = {entry["name"] for entry in mcp_tool_catalog()}
    resource_uris = {entry["uri"] for entry in mcp_resource_catalog()}
    prompt_names = {entry["name"] for entry in mcp_prompt_catalog()}

    for client_spec in manifest["clients"].values():
        for file_spec in client_spec["files"]:
            for tool_name in file_spec.get("tools", []):
                assert tool_name in tool_names
            for resource_uri in file_spec.get("resources", []):
                assert resource_uri in resource_uris
            for prompt_name in file_spec.get("prompts", []):
                assert prompt_name in prompt_names
