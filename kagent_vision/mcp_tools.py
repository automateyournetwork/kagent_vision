"""
MCP tool wiring for KAgent Vision.

Connects the agent to the Vision MCP server which provides camera control,
image generation, video generation, and ASL interpretation tools.

Set MCP_LOCAL=1 to use stdio mode (spawns the MCP server as a subprocess).
This is required on macOS for webcam access since Docker can't pass through
the camera device.
"""

import os
import sys
import re
from typing import List, Optional, Union

from google.adk.tools.mcp_tool.mcp_toolset import (
    MCPToolset,
    StreamableHTTPConnectionParams,
)

# MCP Server configuration
_MCP_SERVERS = [
    {
        "name": "vision-mcp",
        "type": "command",
    },
]


def _resolve_env_vars(value: str) -> str:
    """Resolve ${VAR_NAME} environment variable references in a string."""
    def replace_var(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))
    return re.sub(r"\$\{([^}]+)\}", replace_var, value)


def _is_local_mode() -> bool:
    return os.environ.get("MCP_LOCAL", "").strip() in ("1", "true", "yes")


def get_mcp_tools(
    server_names: Optional[List[str]] = None,
    server_filters: Optional[dict] = None,
    global_filter: Optional[Union[list, object]] = None,
) -> List[MCPToolset]:
    """Get MCP tools from configured servers with optional filtering.

    Args:
        server_names: Optional list of server names to include.
        server_filters: Optional dict mapping server names to tool name lists
                        for per-server filtering.
        global_filter: Optional filter to apply to all servers.

    Returns:
        List of MCPToolset instances.
    """
    servers = _MCP_SERVERS

    if server_names is not None:
        servers = [s for s in servers if s.get("name") in server_names]

    local = _is_local_mode()

    toolsets = []
    for server in servers:
        server_name = server["name"]

        predicate = None
        if server_filters and server_name in server_filters:
            predicate = server_filters[server_name]
        elif global_filter is not None:
            predicate = global_filter

        if local and server["type"] == "command":
            # Stdio mode: spawn MCP server as a subprocess for direct
            # hardware access (webcam, etc.)
            from google.adk.tools.mcp_tool.mcp_session_manager import (
                StdioConnectionParams,
            )
            from mcp import StdioServerParameters

            connection_params = StdioConnectionParams(
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=["-m", "vision_mcp"],
                    env={**os.environ},
                ),
                timeout=600,
            )
        else:
            # HTTP mode: connect to docker-compose service
            if server["type"] == "command":
                url = f"http://{server_name}:3000/mcp"
            else:
                url = server.get("url", "")

            headers = {}
            if "headers" in server and server["headers"]:
                for key, value in server["headers"].items():
                    headers[key] = _resolve_env_vars(value)

            if headers:
                connection_params = StreamableHTTPConnectionParams(
                    url=url, headers=headers
                )
            else:
                connection_params = StreamableHTTPConnectionParams(url=url)

        if predicate is not None:
            toolsets.append(
                MCPToolset(connection_params=connection_params, tool_filter=predicate)
            )
        else:
            toolsets.append(MCPToolset(connection_params=connection_params))

    return toolsets
