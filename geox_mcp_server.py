#!/usr/bin/env python3
"""
GEOX MCP Server Entry Point
══════════════════════════════════════════════════════════════════════════════════

FastMCP Cloud deployment entrypoint.
Sets PYTHONPATH correctly for the geox package.

DITEMPA BUKAN DIBERI — Forged, Not Given
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Detection logic for different deployment layouts:
# - Local dev: geox_mcp_server.py is INSIDE geox/ directory (geox repo root)
# - FastMCP Cloud: geox_mcp_server.py is AT SAME LEVEL as geox/ package (/app/)
# - Local Docker: geox_mcp_server.py is INSIDE geox/ directory (/app/geox/)

GEOX_PKG_PATH = os.path.join(SCRIPT_DIR, "geox")
if os.path.isdir(GEOX_PKG_PATH):
    # geox/ package is a sibling of geox_mcp_server.py (FastMCP Cloud layout)
    PYTHONPATH = SCRIPT_DIR
else:
    # geox/ package is the PARENT of geox_mcp_server.py (local dev/Docker)
    GEOX_ROOT = os.path.dirname(SCRIPT_DIR)
    if os.path.isdir(os.path.join(GEOX_ROOT, "geox")):
        PYTHONPATH = GEOX_ROOT
    else:
        PYTHONPATH = SCRIPT_DIR

os.environ["PYTHONPATH"] = PYTHONPATH
sys.path.insert(0, PYTHONPATH)

from geox.geox_mcp.fastmcp_server import mcp

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8081))
    host = os.environ.get("HOST", "0.0.0.0")

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
