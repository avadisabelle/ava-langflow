#!/usr/bin/env python3
"""
JGT Flowise MCP Server Launcher
This script reliably launches the MCP server as an asynchronous application.
"""

import asyncio
import argparse
import os

# Ensure the package is in the Python path
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agentic_flywheel.mcp_server import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="JGT Flowise MCP Server Launcher")
    parser.add_argument("--config", type=str, required=True, help="Path to the Flowise MCP configuration JSON file.")
    args = parser.parse_args()

    try:
        asyncio.run(main(config_file_path=args.config))
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
