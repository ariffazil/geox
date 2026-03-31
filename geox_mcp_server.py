"""
geox_mcp_server.py — Hardened GEOX MCP Server for arifOS
DITEMPA BUKAN DIBERI

This server provides multimodal geological intelligence tools anchored in the
arifOS Trinity sovereignty model (F1-F13).
"""

import asyncio
import json
import logging
from typing import List, Union

from mcp.server import Server
from mcp.server.types import (
    Tool,
    TextContent,
    ImageContent,
)
from mcp.server.stdio import stdio_server

# Unified Architecture v0.3.2 structure
from arifos.geox import HardenedGeoxAgent
from arifos.geox.TOOLS.seismic.visual_tools import extract_seismic_views

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("geox_mcp")

# Initialize Hardened Agent
agent = HardenedGeoxAgent(session_id="GEOX_PRODUCTION_SOVEREIGN")

# Create MCP Server
app = Server("geox-hardened")

@app.list_tools()
async def list_tools() -> List[Tool]:
    """Expose registered geological tools including multimodal visual extraction."""
    tools = []
    
    # 1. Multimodal Visual Extraction (Encoder/Metabolizer Stage)
    tools.append(Tool(
        name="geox_extract_seismic_views",
        description="Extract 2-3 contrast-variant images (base64) of a seismic section to 'ignite' multimodal LLM vision. Hits F9/F11.",
        inputSchema={
            "type": "object",
            "properties": {
                "seismic_data": {"type": "string", "description": "Path to seismic file (SEGY, PNG, or TIFF)."}
            },
            "required": ["seismic_data"]
        }
    ))
    
    # 2. Band A: Structural Interpretation Orchestrator
    tools.append(Tool(
        name="geox_interpret_single_line",
        description="Governed structural interpretation of 2D seismic with Contrast Canon audit record. Hits 999_SEAL.",
        inputSchema={
            "type": "object",
            "properties": {
                "seismic_data": {"type": "string", "description": "Raster or SEGY data path/reference"},
                "data_type": {"enum": ["segy", "raster"], "description": "Specify input fidelity"},
                "context": {"type": "object", "description": "Optional geological context (basin, setting)"}
            },
            "required": ["seismic_data", "data_type"]
        }
    ))
    
    # 3. Discovery Tool Delegation
    for name, tool_instance in agent.registry._tools.items():
         if name in ["SingleLineInterpreter", "ExtractSeismicViews"]: continue
         tools.append(Tool(
             name=name,
             description=tool_instance.description,
             inputSchema={"type": "object", "properties": {}}
         ))
    
    return tools

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> List[Union[TextContent, ImageContent]]:
    """Execute tools with multimodal response support (base64 images) and governance gates."""
    
    if name == "geox_extract_seismic_views":
         variants = await extract_seismic_views(arguments.get("seismic_data", ""))
         content = []
         for v in variants:
              content.append(TextContent(type="text", text=f"Variant: {v['label']}"))
              content.append(ImageContent(type="image", data=v["base64"], mimeType=v["mimeType"]))
         return content
    
    # Delegate standard tools to the hardened agent
    envelope = await agent.execute_tool(name, arguments)
    
    # Format constitutional response
    header = "VERDICT: SEALED ✅"
    if envelope.get("verdict") == "888_HOLD":
        header = "WARNING: 888_HOLD 🛑 [SOVEREIGN APPROVAL REQUIRED]"
    elif envelope.get("verdict") == "QUALIFY":
        header = "VERDICT: QUALIFY ⚠️ [CONDITIONAL RELIABILITY]"
    elif envelope.get("verdict") == "VOID":
        header = "VERDICT: VOID ❌ [NON-COMPLIANT]"

    text = f"{header}\n\n"
    text += f"EXPLANATION: {envelope.get('explanation', 'No explanation.')}\n\n"
    text += "RESULT PAYLOAD (JSON Audit Record):\n"
    text += json.dumps(envelope.get('payload', {}), indent=2)
    
    # Telemetry and Branding
    text += f"\n\n---\nGEOX v{envelope.get('version', '0.3.2')} | G-Score: {envelope.get('metrics', {}).get('genius_score')} | delta_S: {envelope.get('metrics', {}).get('delta_s')}"
    text += f"\nSeal Status: {envelope.get('metrics', {}).get('geox_eureka', {}).get('verdict')} | Floors: {envelope.get('floors', [])} | DITEMPA BUKAN DIBERI"
    
    return [TextContent(type="text", text=text)]

async def main():
    logger.info("Starting sovereign multimodal GEOX MCP server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
