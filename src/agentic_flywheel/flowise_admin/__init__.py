"""
Flowise Admin Package
Administrative tools for flowise database management, flow analysis, and system configuration
Provides full database access and system administration capabilities
"""

__version__ = "1.0.0"
__author__ = "JGT Team"
__email__ = "jgwill@jgwill.com"

# Import admin modules
from .db_interface import FlowiseDBInterface, ChatMessage, FlowStats, ConversationPattern
try:
    from .flow_analyzer import FlowAnalyzer, FlowPerformanceReport
    from .config_sync import ConfigurationSync
except ImportError:
    # Handle missing dependencies gracefully
    FlowAnalyzer = None
    FlowPerformanceReport = None
    ConfigurationSync = None

__all__ = [
    "FlowiseDBInterface", 
    "ChatMessage", 
    "FlowStats", 
    "ConversationPattern",
    "FlowAnalyzer",
    "FlowPerformanceReport", 
    "ConfigurationSync"
]