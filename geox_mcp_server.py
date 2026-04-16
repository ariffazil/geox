#!/usr/bin/env python3
"""
GEOX MCP Server Entry Point
═══════════════════════════════════════════════════════════════════════════════

FastMCP Cloud deployment entrypoint.
Sets PYTHONPATH correctly for the geox package.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

import os
import sys

# Get the parent directory (where geox/ is located)
# geox_mcp_server.py is at /root/geox/geox_mcp_server.py
# So parent is /root, which contains geox/ package
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(SCRIPT_DIR)

# Set PYTHONPATH so 'geox' package is found
os.environ["PYTHONPATH"] = PARENT_DIR

# Now we can import the geox module
sys.path.insert(0, PARENT_DIR)

from geox.mcp.fastmcp_server import mcp

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8081))
    host = os.environ.get("HOST", "127.0.0.1")

    print(f"Starting GEOX MCP Server on {host}:{port}")
    print(f"PYTHONPATH={os.environ.get('PYTHONPATH')}")

    app = mcp.streamable_http_app()
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        proxy_headers=True,
    )
