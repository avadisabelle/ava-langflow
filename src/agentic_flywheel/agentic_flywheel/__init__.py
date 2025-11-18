"""
JGT Flowise MCP - MCP-enabled Flowise automation with intelligent flow management
"""

__version__ = "1.1.0"
__author__ = "JGT Team"
__email__ = "jgwill@jgwill.com"

from .config_manager import FlowiseManager
from .mcp_server import FlowiseMCPServer

__all__ = ["FlowiseManager", "FlowiseMCPServer"]