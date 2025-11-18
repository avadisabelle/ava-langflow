#!/usr/bin/env python3
"""
Flowise Flow Adapter

Bridges the gap between existing Flowise flow-registry.yaml flows
and the Universal MCP Server's unified flow abstraction.

Purpose:
- Import real Flowise flows from YAML registry
- Map real flow IDs and intent keywords to UniversalFlow format
- Preserve existing flow configurations and performance metrics
- Enable seamless integration with intelligent routing system

Usage:
    from agentic_flywheel.adapters import FlowiseFlowAdapter

    adapter = FlowiseFlowAdapter()
    universal_flows = await adapter.import_active_flows()
    registry.register_flows(BackendType.FLOWISE, universal_flows)
"""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

from ..backends import UniversalFlow, BackendType

logger = logging.getLogger(__name__)


@dataclass
class FlowiseFlowMetadata:
    """Extended metadata for Flowise flows"""
    success_score: float = 0.8
    engagement_score: float = 0.0
    total_usage: int = 0
    last_analyzed: Optional[str] = None
    auto_discovered: bool = False
    status: str = "active"
    session_format: str = ""
    temperature: float = 0.7
    max_output_tokens: int = 2000


class FlowiseFlowAdapter:
    """
    Adapter for importing and mapping Flowise flows to Universal format

    Handles:
    - YAML registry parsing
    - Active flow filtering (active: 1)
    - Intent keyword mapping
    - Performance metrics extraction
    - Configuration normalization
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize adapter with optional custom registry path

        Args:
            registry_path: Path to flow-registry.yaml (auto-discovers if None)
        """
        self.registry_path = registry_path or self._find_registry()
        self.flows_cache: Dict[str, UniversalFlow] = {}

    def _find_registry(self) -> Optional[Path]:
        """Auto-discover flow registry in known locations"""
        search_paths = [
            Path(__file__).parent.parent / "agentic_flywheel" / "config" / "flow-registry.yaml",
            Path(__file__).parent.parent.parent / "agentic_flywheel" / "config" / "flow-registry.yaml",
            Path.cwd() / "src" / "agentic_flywheel" / "agentic_flywheel" / "config" / "flow-registry.yaml"
        ]

        for path in search_paths:
            if path.exists():
                logger.info(f"📁 Found flow registry: {path}")
                return path

        logger.warning("⚠️  Flow registry not found in standard locations")
        return None

    async def import_active_flows(self) -> List[UniversalFlow]:
        """
        Import all active flows from Flowise registry

        Returns:
            List of UniversalFlow objects for active flows
        """
        if not self.registry_path or not self.registry_path.exists():
            logger.error("❌ Cannot import flows: registry not found")
            return []

        try:
            with open(self.registry_path, 'r') as f:
                registry = yaml.safe_load(f)

            flows = []

            # Import operational flows
            operational_flows = registry.get('operational_flows', {})
            for flow_key, flow_config in operational_flows.items():
                if flow_config.get('active', 0) == 1:
                    universal_flow = self._convert_to_universal(flow_key, flow_config, 'operational')
                    flows.append(universal_flow)
                    self.flows_cache[flow_key] = universal_flow

            # Import routing flows (if active)
            routing_flows = registry.get('routing_flows', {})
            for flow_key, flow_config in routing_flows.items():
                if flow_config.get('active', 0) == 1:
                    universal_flow = self._convert_to_universal(flow_key, flow_config, 'routing')
                    flows.append(universal_flow)
                    self.flows_cache[flow_key] = universal_flow

            logger.info(f"✅ Imported {len(flows)} active flows from Flowise registry")
            return flows

        except Exception as e:
            logger.error(f"❌ Error importing flows: {e}")
            return []

    def _convert_to_universal(
        self,
        flow_key: str,
        flow_config: Dict[str, Any],
        flow_category: str
    ) -> UniversalFlow:
        """
        Convert Flowise flow config to UniversalFlow format

        Args:
            flow_key: Flow identifier key
            flow_config: Flow configuration from YAML
            flow_category: 'operational' or 'routing'

        Returns:
            UniversalFlow object
        """
        # Extract core fields
        flow_id = flow_config['id']
        name = flow_config['name']
        description = flow_config.get('description', '')

        # Extract configuration
        config = flow_config.get('config', {})
        temperature = config.get('temperature', 0.7)
        max_tokens = config.get('maxOutputTokens', 2000)

        # Extract intent keywords
        intent_keywords = flow_config.get('intent_keywords', [])

        # Extract performance metrics
        perf_metrics = flow_config.get('performance_metrics', {})
        metadata = FlowiseFlowMetadata(
            success_score=perf_metrics.get('success_score', 0.8),
            engagement_score=perf_metrics.get('engagement_score', 0.0),
            total_usage=perf_metrics.get('total_usage', 0),
            last_analyzed=flow_config.get('last_analyzed'),
            auto_discovered=flow_config.get('auto_discovered', False),
            status=flow_config.get('status', 'active'),
            session_format=flow_config.get('session_format', ''),
            temperature=temperature,
            max_output_tokens=max_tokens
        )

        # Determine capabilities based on flow characteristics
        capabilities = self._infer_capabilities(flow_config, flow_category)

        # Determine input/output types
        input_types = ["text"]  # All Flowise flows accept text
        output_types = ["text"]
        if config.get('returnSourceDocuments', False):
            output_types.append("structured")

        # Create UniversalFlow
        return UniversalFlow(
            id=f"flowise_{flow_key}",
            name=name,
            description=description,
            backend=BackendType.FLOWISE,
            backend_specific_id=flow_id,
            intent_keywords=intent_keywords,
            capabilities=capabilities,
            input_types=input_types,
            output_types=output_types,
            performance_score=metadata.success_score,
            success_rate=metadata.success_score,  # Use success_score as success_rate
            avg_response_time=0.0,  # Not tracked in YAML
            user_rating=metadata.engagement_score
        )

    def _infer_capabilities(self, flow_config: Dict[str, Any], category: str) -> List[str]:
        """
        Infer flow capabilities from configuration

        Args:
            flow_config: Flow configuration
            category: Flow category

        Returns:
            List of capability strings
        """
        capabilities = ["chat"]  # All flows support chat

        # Infer from category
        if category == "routing":
            capabilities.append("routing")
            capabilities.append("multi-flow")

        # Infer from intent keywords
        keywords = flow_config.get('intent_keywords', [])
        if any(kw in keywords for kw in ['research', 'academic', 'analysis', 'study']):
            capabilities.append("research")
        if any(kw in keywords for kw in ['creative', 'vision', 'goal', 'orientation']):
            capabilities.append("creative")
        if any(kw in keywords for kw in ['code', 'technical', 'programming', 'develop']):
            capabilities.append("technical")
        if any(kw in keywords for kw in ['document', 'search', 'lookup', 'query']):
            capabilities.append("retrieval")
        if any(kw in keywords for kw in ['spiritual', 'faith', 'meaning']):
            capabilities.append("spiritual")

        # Infer from configuration
        config = flow_config.get('config', {})
        if config.get('returnSourceDocuments', False):
            capabilities.append("rag")

        # Infer from description
        description = flow_config.get('description', '').lower()
        if 'rise' in description or 'framework' in description:
            capabilities.append("framework")
        if 'agent' in description or 'prompt' in description:
            capabilities.append("agent-design")

        return list(set(capabilities))  # Remove duplicates

    def get_flow_by_key(self, flow_key: str) -> Optional[UniversalFlow]:
        """Get cached flow by key"""
        return self.flows_cache.get(flow_key)

    def get_flow_statistics(self) -> Dict[str, Any]:
        """Get statistics about imported flows"""
        if not self.flows_cache:
            return {
                'total_flows': 0,
                'by_capability': {},
                'avg_success_score': 0.0,
                'total_usage': 0
            }

        capabilities_count = {}
        total_success = 0.0
        total_usage = 0

        for flow in self.flows_cache.values():
            # Count capabilities
            for cap in flow.capabilities:
                capabilities_count[cap] = capabilities_count.get(cap, 0) + 1

            # Sum metrics
            total_success += flow.success_rate
            # Note: total_usage is not stored in UniversalFlow, so we can't sum it here

        return {
            'total_flows': len(self.flows_cache),
            'by_capability': capabilities_count,
            'avg_success_score': total_success / len(self.flows_cache) if self.flows_cache else 0.0,
            'total_usage': total_usage
        }


async def main():
    """Test flow adapter"""
    adapter = FlowiseFlowAdapter()
    flows = await adapter.import_active_flows()

    print(f"\n{'='*60}")
    print(f"Flowise Flow Adapter - Import Results")
    print(f"{'='*60}\n")

    for flow in flows:
        print(f"✅ {flow.name}")
        print(f"   ID: {flow.backend_specific_id}")
        print(f"   Keywords: {', '.join(flow.intent_keywords[:5])}...")
        print(f"   Capabilities: {', '.join(flow.capabilities)}")
        print()

    stats = adapter.get_flow_statistics()
    print(f"{'='*60}")
    print(f"Statistics:")
    print(f"  Total Flows: {stats['total_flows']}")
    print(f"  Average Success Score: {stats['avg_success_score']:.2f}")
    print(f"  Total Usage: {stats['total_usage']}")
    print(f"  Capabilities Distribution:")
    for cap, count in sorted(stats['by_capability'].items(), key=lambda x: -x[1]):
        print(f"    - {cap}: {count} flows")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
