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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# In Docker: /app/geox_mcp_server.py, geox at /app/geox/, so use SCRIPT_DIR
# Locally: /root/geox/geox_mcp_server.py, geox at /root/geox/geox/, so use parent
if os.path.basename(SCRIPT_DIR) == "geox" and os.path.exists(
    os.path.join(SCRIPT_DIR, "geox_mcp_server.py")
):
    # Local dev: geox_mcp_server.py is INSIDE geox/ directory
    PYTHONPATH = os.path.dirname(SCRIPT_DIR)
else:
    # Docker: geox_mcp_server.py is at same level as geox/ directory
    PYTHONPATH = SCRIPT_DIR

os.environ["PYTHONPATH"] = PYTHONPATH
sys.path.insert(0, PYTHONPATH)

from geox.geox_mcp.fastmcp_server import mcp

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
