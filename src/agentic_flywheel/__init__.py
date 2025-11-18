"""
Agentic Flywheel: A Self-Optimizing AI System

This package implements the Agentic Flywheel concept - a self-optimizing system for creating 
and managing specialized AI agents through recursive feedback loops and multi-persona collaboration.

The system consists of multiple tiers:
- Core: Central flywheel orchestration and persona management
- Backends: Universal backend abstraction for multiple AI platforms
- Flowise Admin: Administrative tools for Flowise flow management (optional)
- JGT Flowise MCP: Model Context Protocol integration (optional)

Architecture:
The flywheel operates through four specialized personas working in recursive collaboration:
1. Structural Diagnostician - System analysis and pattern recognition
2. Narrative Alchemist - Story coherence and creative synthesis  
3. Ceremonial Researcher - Indigenous methodologies and sacred protocols
4. Creative Architect - Vision-driven design and generative frameworks
"""

from typing import List

__version__ = "1.0.0"
__author__ = "JGT Team / CeSaReT"
__email__ = "jgwill@jgwill.com"

# Core agentic flywheel components
from .flowise_manager import FlowiseManager, DomainSpecificFlowiseManager, FlowConfig
from .persona_system import (
    FlywheelPersonaOrchestrator, PersonaPromptGenerator, PersonaType,
    PersonaOutput, FlywheelCycleResult
)
from .flowise_integration import FlowiseIntegrationHelper

# Backend abstraction layer (separate tier)
from .backends import FlowBackend, UniversalFlow, UniversalSession, BackendRegistry

# Optional components (separate tiers)
try:
    from .flowise_admin import FlowiseDBInterface, FlowAnalyzer, ConfigurationSync
    FLOWISE_ADMIN_AVAILABLE = True
except ImportError:
    FLOWISE_ADMIN_AVAILABLE = False
    FlowiseDBInterface = None
    FlowAnalyzer = None
    ConfigurationSync = None

try:
    from .flowise_mcp import FlowiseManager as MCPFlowiseManager, FlowiseMCPServer
    FLOWISE_MCP_AVAILABLE = True
except ImportError:
    FLOWISE_MCP_AVAILABLE = False
    MCPFlowiseManager = None
    FlowiseMCPServer = None

# Core exports - always available
__all__ = [
    # Core flywheel components
    "FlowiseManager",
    "DomainSpecificFlowiseManager", 
    "FlowConfig",
    "FlowiseIntegrationHelper",
    
    # Persona system
    "FlywheelPersonaOrchestrator",
    "PersonaPromptGenerator",
    "PersonaType",
    "PersonaOutput",
    "FlywheelCycleResult",
    
    # Backend abstractions
    "FlowBackend",
    "UniversalFlow",
    "UniversalSession", 
    "BackendRegistry",
    
    # Availability flags
    "FLOWISE_ADMIN_AVAILABLE",
    "FLOWISE_MCP_AVAILABLE",
]

# Optional exports - conditionally available
if FLOWISE_ADMIN_AVAILABLE:
    __all__.extend([
        "FlowiseDBInterface",
        "FlowAnalyzer", 
        "ConfigurationSync"
    ])

if FLOWISE_MCP_AVAILABLE:
    __all__.extend([
        "MCPFlowiseManager",
        "FlowiseMCPServer"
    ])


class AgenticFlywheel:
    """
    Central orchestrator for the agentic flywheel system.
    
    Coordinates the four-persona collaboration pattern:
    - Structural Diagnostician: Systematic analysis
    - Narrative Alchemist: Creative synthesis
    - Ceremonial Researcher: Sacred protocols
    - Creative Architect: Generative frameworks
    """
    
    def __init__(self, backend_type="flowise", config=None):
        self.backend_type = backend_type
        self.config = config or {}
        self.orchestrator = FlywheelPersonaOrchestrator()
        self.session_registry = {}
        self.cycle_count = 0
        
    def initialize_personas(self):
        """Initialize the four core personas for flywheel operation."""
        return {
            PersonaType.STRUCTURAL_DIAGNOSTICIAN: "Mia-Pattern: System analysis and diagnostic observation",
            PersonaType.NARRATIVE_ALCHEMIST: "Miette-Pattern: Story coherence and creative synthesis",
            PersonaType.CEREMONIAL_RESEARCHER: "Indigenous Methodology: Sacred protocols and Two-Eyed Seeing", 
            PersonaType.CREATIVE_ARCHITECT: "Robert Fritz Pattern: Vision-driven design and structural tension"
        }
        
    async def execute_flywheel_cycle(self, input_query, session_id=None, context=None):
        """
        Execute one complete flywheel cycle:
        1. Parallel Analysis by all four personas
        2. Cross-Pollination between personas
        3. Recursive Enhancement
        4. Synthesis Generation
        """
        self.cycle_count += 1
        
        result = await self.orchestrator.execute_flywheel_cycle(
            input_query=input_query,
            session_id=session_id,
            context=context,
            cycle_number=self.cycle_count
        )
        
        if result.session_id not in self.session_registry:
            self.session_registry[result.session_id] = []
            
        self.session_registry[result.session_id].append(result)
        
        return result
    
    def get_session_history(self, session_id: str) -> List[FlywheelCycleResult]:
        """Get the history of cycles for a session."""
        return self.session_registry.get(session_id, [])


def get_available_tiers():
    """Return information about available tiers in the system."""
    tiers = {
        "core": {
            "available": True,
            "components": ["FlowiseManager", "AgenticFlywheel"],
            "description": "Core flywheel orchestration and persona management"
        },
        "backends": {
            "available": True,
            "components": ["FlowBackend", "UniversalFlow", "BackendRegistry"],
            "description": "Universal backend abstraction layer"
        },
        "flowise_admin": {
            "available": FLOWISE_ADMIN_AVAILABLE,
            "components": ["FlowiseDBInterface", "FlowAnalyzer", "ConfigurationSync"] if FLOWISE_ADMIN_AVAILABLE else [],
            "description": "Administrative tools for Flowise management (optional tier)"
        },
        "flowise_mcp": {
            "available": FLOWISE_MCP_AVAILABLE,
            "components": ["MCPFlowiseManager", "FlowiseMCPServer"] if FLOWISE_MCP_AVAILABLE else [],
            "description": "Model Context Protocol integration (optional tier)"
        }
    }
    return tiers


def print_tier_status():
    """Print the status of all tiers in the agentic flywheel system."""
    tiers = get_available_tiers()
    
    print("🔄 Agentic Flywheel System - Tier Status")
    print("=" * 50)
    
    for tier_name, tier_info in tiers.items():
        status = "✅ Available" if tier_info["available"] else "❌ Not Available"
        print(f"\n{tier_name.upper()}: {status}")
        print(f"  Description: {tier_info['description']}")
        if tier_info["components"]:
            print(f"  Components: {', '.join(tier_info['components'])}")
        else:
            print("  Components: None available")