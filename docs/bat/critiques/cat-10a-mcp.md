# Category 10a Critique: MCP Adapter (BAT-103 to BAT-109)

## Test Summary

| Test | Description | Result |
|------|-------------|--------|
| BAT-103 | MCP — Create Note Tool | PARTIAL PASS |
| BAT-104 | MCP — Create Reference Tool | PARTIAL PASS |
| BAT-105 | MCP — Create Task Tool | PARTIAL PASS |
| BAT-106 | MCP — Search Tool | PARTIAL PASS |
| BAT-107 | MCP — Get Document Tool | PARTIAL PASS |
| BAT-108 | MCP — Agent Context Tool | PARTIAL PASS |
| BAT-109 | MCP — Resources and Prompts | PARTIAL PASS |

All tests are PARTIAL PASS because the `mcp` extra is not installed, preventing
end-to-end MCP server testing. However, every `_impl` function was tested directly
and works correctly.

## Architecture Assessment

### The `_impl` Pattern: Excellent Design

The most impressive aspect of the MCP adapter is the `_impl` function pattern.
Every MCP tool, resource, and prompt has two layers:

1. **`_<name>_impl(vault, ...)`** -- Pure business logic, no MCP dependency
2. **`register_tools(server, vault)`** -- Thin FastMCP decorator wrappers

This means:
- All 13 tools are testable without installing the `mcp` package
- The `_impl` functions can be called from any context (scripts, tests, other adapters)
- The MCP transport layer is purely additive -- removing it leaves all logic intact

This is textbook separation of concerns. The `_impl` functions tested in BAT-103
through BAT-108 all returned well-structured `{ok, op, data, warnings}` responses
identical to what the CLI produces.

### Tool Catalog: Well-Organized

The `discover_tools_impl` function (BAT-103, Test 5) reveals a clean 5-category
taxonomy:

- **Discovery** (1): `discover_tools` -- self-describing catalog
- **Creation** (4): `create_note`, `create_reference`, `create_task`, `create_log`
- **Lifecycle** (3): `update_content`, `close_content`, `reweave`
- **Query** (4): `search`, `get_document`, `get_related`, `agent_context`
- **Session** (1): `session_close`

The 13 tools cover the full CRUD lifecycle plus graph operations. The `agent_context`
tool is particularly well-designed -- it tries session-based context first, then
falls back to a QueryService-based aggregate (recent items + search + work queue).

### Resources: Comprehensive

Six URI-based resources provide structured vault context:
- `ztlctl://context` -- Combined identity + methodology + overview
- `ztlctl://self/identity` -- Vault identity document
- `ztlctl://self/methodology` -- Agent methodology
- `ztlctl://overview` -- Counts and recent items
- `ztlctl://work-queue` -- Scored task list
- `ztlctl://topics` -- Topic directories

The URI naming scheme is clean and intuitive.

### Prompts: Actionable

Four workflow prompts provide structured agent instructions:
- `research_session(topic)` -- Step-by-step research workflow
- `knowledge_capture()` -- Knowledge ingestion guidelines
- `vault_orientation()` -- Onboarding with live vault state
- `decision_record(topic)` -- Decision documentation template

The `vault_orientation` prompt is notable because it reads live vault state
(identity, methodology, counts, recent items) to produce a dynamic onboarding
context.

### Transport Options

The `serve` command supports three transports:
- `stdio` (default) -- Sub-millisecond latency for local MCP clients
- `sse` -- Server-Sent Events for network access
- `streamable-http` -- Full HTTP transport for cloud deployments

### Server Setup

The `create_server` function properly:
- Guards against missing `mcp` extra with a clear error message
- Creates a Vault from the working directory
- Initializes the event bus (sync mode)
- Registers all tools, resources, and prompts

## Strengths

1. **Testability without MCP**: The `_impl` pattern is the standout design decision.
   Every tool function works without `mcp` installed. This simplifies testing,
   CI/CD, and alternative integrations.

2. **Consistent response format**: All tools return `{ok, op, data, warnings, error}`
   matching the CLI's ServiceResult format. This means MCP clients get the same
   structured data as CLI users.

3. **Graceful degradation**: The `serve` command exists even without the MCP extra.
   It shows a clear error message instead of crashing.

4. **Self-describing catalog**: The `discover_tools` tool lets MCP clients enumerate
   available tools at runtime, supporting dynamic tool selection by AI agents.

5. **Lazy Vault creation**: The server only creates the Vault when tools are invoked,
   avoiding unnecessary DB connections at startup.

## Weaknesses and Recommendations

1. **Cannot test MCP transport**: Without installing the `mcp` extra, we cannot
   verify that the FastMCP decorators correctly marshal arguments, handle errors,
   and format responses for the MCP protocol. Consider adding a CI job that
   installs `ztlctl[mcp]` and runs integration tests.

2. **No MCP-specific error handling**: The `_to_mcp_response` function converts
   ServiceResult to a dict, but does not use MCP-standard error codes. MCP clients
   expecting JSON-RPC style errors may find the response format non-standard.

3. **Missing tools for some operations**: There is no MCP tool for `check`
   (integrity), `export`, or `graph` operations beyond `get_related`. An agent
   performing vault maintenance would need additional tools.

4. **No tool input validation in MCP layer**: The `_impl` functions rely entirely
   on service-layer validation. Adding MCP-specific input validation (e.g.,
   required fields, type hints) would improve error messages for MCP clients.

5. **Session management gap**: There is a `session_close` tool but no
   `session_start` -- that functionality is split across `create_log` and
   `session_close`. This naming asymmetry could confuse MCP clients.

## Overall Assessment

The MCP adapter is well-designed with excellent separation of concerns. The
`_impl` pattern ensures testability and portability. The tool catalog covers
the core knowledge management workflow, and the resources/prompts provide
rich context for AI agents. The main gap is lack of end-to-end MCP transport
testing, which would require installing the optional `mcp` extra in CI.

**Grade: B+**

The design is strong, but the inability to test the actual MCP transport layer
and some minor gaps in tool coverage prevent a higher grade. The `_impl` pattern
alone elevates this from a typical adapter implementation.
