#!/usr/bin/env python3
"""
KAgent Vision MCP Server

Exposes vision tools over MCP (Model Context Protocol):
  - Camera: list_cameras, vision_start, vision_status, vision_capture, vision_burst, vision_stop
  - Files:  list_images
  - Banana: banana_generate (AI image generation/transformation)
  - Veo:    veo_generate_video (AI video generation)
  - ASL:    asl_understand (American Sign Language interpretation)
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    stream=sys.stderr,
)
log = logging.getLogger("vision_mcp")

try:
    from mcp.server.fastmcp import FastMCP
except Exception:
    from fastmcp import FastMCP  # type: ignore

from .camera import (
    list_cameras,
    vision_start,
    vision_status,
    vision_capture,
    vision_burst,
    vision_stop,
)
from .files import list_images
from .banana import banana_generate
from .veo import veo_generate_video
from .asl import asl_understand

# ---------- Create MCP Server ----------
mcp = FastMCP("KAgent Vision MCP")

# Register camera tools
mcp.tool()(list_cameras)
mcp.tool()(vision_start)
mcp.tool()(vision_status)
mcp.tool()(vision_capture)
mcp.tool()(vision_burst)
mcp.tool()(vision_stop)

# Register file tools
mcp.tool()(list_images)

# Register AI generation tools
mcp.tool()(banana_generate)
mcp.tool()(veo_generate_video)

# Register ASL tools
mcp.tool()(asl_understand)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
