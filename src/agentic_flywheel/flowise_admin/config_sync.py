#!/usr/bin/env python3
"""
Configuration Sync - Admin Tool
Synchronizes database reality with flow configurations and enables intelligent updates
"""

import json
import logging
import yaml
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import sys
import os

# Import admin modules
try:
    from .db_interface import FlowiseDBInterface, FlowStats
    from .flow_analyzer import FlowAnalyzer, FlowPerformanceReport
except ImportError:
    from db_interface import FlowiseDBInterface, FlowStats
    from flow_analyzer import FlowAnalyzer, FlowPerformanceReport

# Import working flowise manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from flowise_manager import FlowiseManager, FlowConfig
except ImportError:
    FlowiseManager = None
    FlowConfig = None

logger = logging.getLogger(__name__)

@dataclass
class ConfigSyncReport:
    """Report of configuration synchronization results"""
    timestamp: str
    flows_discovered: int
    flows_updated: int
    flows_added: int
    flows_removed: int
    performance_improvements: List[str]
    sync_issues: List[str]
    recommendations: List[str]

class ConfigurationSync:
    """Synchronizes database insights with configuration files for optimal performance"""
    
    def __init__(self, 
                 database_path: str = "/home/jgi/.flowise/database.sqlite",
                 config_base_path: str = "/a/src/api/flowise"):
        self.db = FlowiseDBInterface(database_path)
        self.analyzer = FlowAnalyzer(database_path)
        self.config_base_path = Path(config_base_path)
        
        # Configuration file paths
        self.flow_registry_path = self.config_base_path / "flow-registry.yaml"
        self.global_config_path = self.config_base_path / "global-config-template.yaml"
        
        # Initialize flowise manager for live integration
        self.flow_manager = None
        if FlowiseManager:
            try:
                self.flow_manager = FlowiseManager()
                logger.info("✅ Connected to live FlowiseManager for sync")
            except Exception as e:
                logger.warning(f"⚠️ FlowiseManager connection failed: {e}")
        
    def discover_active_flows(self) -> Dict[str, Dict[str, Any]]:
        """Discover actively used flows from database analysis"""
        logger.info("🔍 Discovering active flows from database...")
        
        flow_stats = self.db.get_flow_statistics()
        
        # Filter for meaningful flows (enough usage to be worth configuring)
        active_flows = {}
        
        for stat in flow_stats:
            if stat.message_count >= 10:  # Minimum threshold
                # Get patterns for this flow
                patterns = self.db.extract_conversation_patterns(stat.chatflow_id)
                
                # Extract keywords from patterns
                keywords = set()
                for pattern in patterns:
                    keywords.update(pattern.context_keywords)
                
                # Determine flow type based on usage patterns
                flow_type = self._classify_flow_type(stat, patterns)
                
                active_flows[stat.chatflow_id] = {
                    'id': stat.chatflow_id,
                    'name': stat.flow_name,
                    'discovered_name': self._generate_flow_name(stat, patterns),
                    'type': flow_type,
                    'message_count': stat.message_count,
                    'session_count': stat.session_count,
                    'success_score': stat.success_score,
                    'engagement_score': stat.engagement_score,
                    'keywords': list(keywords)[:15],  # Limit keywords
                    'last_used': stat.last_message,
                    'status': 'active' if stat.message_count >= 50 else 'testing'
                }
        
        logger.info(f"✅ Discovered {len(active_flows)} active flows")
        return active_flows
    
    def _classify_flow_type(self, stat: FlowStats, patterns: List) -> str:
        """Classify the type of flow based on usage patterns"""
        
        # Check for specific pattern types
        pattern_types = [p.pattern_type for p in patterns]
        
        if 'vision_creation' in pattern_types or 'outcome_focus' in pattern_types:
            return 'operational'  # Direct user interaction
        elif 'narrative_transformation' in pattern_types:
            return 'operational'  # Story creation
        elif 'code_implementation' in pattern_types:
            return 'operational'  # Coding assistance
        elif stat.engagement_score > 0.8:
            return 'operational'  # High engagement = user-facing
        else:
            return 'routing'  # Lower engagement might be routing/orchestration
    
    def _generate_flow_name(self, stat: FlowStats, patterns: List) -> str:
        """Generate a meaningful flow name based on patterns"""
        
        if stat.flow_name != 'unknown':
            return stat.flow_name
        
        # Try to infer from patterns
        pattern_types = [p.pattern_type for p in patterns]
        keywords = set()
        for p in patterns:
            keywords.update(p.context_keywords[:3])  # Top keywords
        
        if 'vision_creation' in pattern_types:
            return 'creative-vision-flow'
        elif 'narrative_transformation' in pattern_types:
            return 'story-creation-flow'
        elif 'code_implementation' in pattern_types:
            return 'code-assistance-flow'
        elif keywords:
            # Generate name from top keywords
            top_keywords = sorted(keywords)[:2]
            return '-'.join(top_keywords) + '-flow'
        else:
            return f'flow-{stat.chatflow_id[:8]}'
    
    def sync_flow_registry(self, dry_run: bool = True) -> ConfigSyncReport:
        """Synchronize the flow registry with database discoveries"""
        logger.info("🔄 Synchronizing flow registry with database reality...")
        
        # Discover active flows
        active_flows = self.discover_active_flows()
        
        # Load current registry
        current_registry = self._load_flow_registry()
        
        # Track changes
        flows_added = 0
        flows_updated = 0
        flows_removed = 0
        sync_issues = []
        performance_improvements = []
        
        # Update operational flows section
        if 'operational_flows' not in current_registry:
            current_registry['operational_flows'] = {}
        
        existing_flow_ids = set()
        for flow_data in current_registry['operational_flows'].values():
            existing_flow_ids.add(flow_data.get('id', ''))
        
        # Add/update discovered flows
        for flow_id, flow_data in active_flows.items():
            flow_key = self._generate_flow_key(flow_data['discovered_name'])
            
            if flow_id not in existing_flow_ids:
                # New flow discovered
                new_flow_config = self._create_flow_config(flow_data)
                current_registry['operational_flows'][flow_key] = new_flow_config
                flows_added += 1
                logger.info(f"➕ Added new flow: {flow_data['discovered_name']}")
                
            else:
                # Update existing flow with database insights
                existing_config = self._find_existing_flow_config(current_registry, flow_id)
                if existing_config:
                    updated = self._update_flow_config(existing_config[1], flow_data)
                    if updated:
                        flows_updated += 1
                        performance_improvements.append(f"Updated {flow_data['discovered_name']} with usage insights")
        
        # Generate performance-based optimizations
        performance_reports = self.analyzer.analyze_all_flows()
        for flow_name, report in performance_reports.items():
            if report.performance_score < 0.6:
                config = self._find_flow_config_by_name(current_registry, flow_name)
                if config:
                    self._apply_performance_optimizations(config[1], report)
                    performance_improvements.append(f"Applied optimizations to {flow_name}")
        
        # Save updated registry
        if not dry_run:
            self._save_flow_registry(current_registry)
            logger.info("💾 Flow registry updated successfully")
        else:
            logger.info("🔍 Dry run completed - no changes written")
        
        recommendations = self._generate_sync_recommendations(active_flows, current_registry)
        
        return ConfigSyncReport(
            timestamp=datetime.now().isoformat(),
            flows_discovered=len(active_flows),
            flows_updated=flows_updated,
            flows_added=flows_added,
            flows_removed=flows_removed,
            performance_improvements=performance_improvements,
            sync_issues=sync_issues,
            recommendations=recommendations
        )
    
    def _load_flow_registry(self) -> Dict[str, Any]:
        """Load current flow registry configuration"""
        try:
            with open(self.flow_registry_path, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            logger.warning("Flow registry not found, creating new one")
            return {
                'metadata': {
                    'version': '1.0.0',
                    'created': datetime.now().isoformat(),
                    'description': 'Auto-generated flow registry from database analysis'
                },
                'operational_flows': {},
                'routing_flows': {}
            }
    
    def _save_flow_registry(self, registry: Dict[str, Any]) -> None:
        """Save flow registry configuration"""
        # Update metadata
        if 'metadata' not in registry:
            registry['metadata'] = {}
        
        registry['metadata']['updated'] = datetime.now().isoformat()
        registry['metadata']['auto_sync'] = True
        
        with open(self.flow_registry_path, 'w') as f:
            yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
    
    def _generate_flow_key(self, flow_name: str) -> str:
        """Generate a consistent flow key from name"""
        return flow_name.lower().replace(' ', '-').replace('_', '-')
    
    def _create_flow_config(self, flow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new flow configuration from database insights"""
        
        # Generate prompts based on keywords and patterns
        keywords = flow_data['keywords']
        rephrase_prompt = f"Transform this into a {flow_data['discovered_name'].replace('-', ' ')} inquiry: {{question}}"
        
        if 'creative' in keywords or 'vision' in keywords:
            response_prompt = "Guide using creative orientation principles focusing on desired outcomes: {context}"
        elif 'story' in keywords or 'narrative' in keywords:
            response_prompt = "Help create meaningful narrative content: {context}"
        elif 'code' in keywords or 'technical' in keywords:
            response_prompt = "Provide technical guidance for implementation: {context}"
        else:
            response_prompt = f"Provide helpful guidance for {flow_data['discovered_name'].replace('-', ' ')}: {{context}}"
        
        # Determine optimal temperature based on flow type
        temperature = 0.7  # Default
        if 'creative' in keywords:
            temperature = 0.8  # Higher creativity
        elif 'technical' in keywords or 'code' in keywords:
            temperature = 0.3  # More deterministic
        
        return {
            'id': flow_data['id'],
            'name': flow_data['discovered_name'].replace('-', ' ').title(),
            'description': f"Auto-discovered flow with {flow_data['message_count']} messages and {flow_data['success_score']:.1f} success score",
            'purpose': f"Handles queries related to {', '.join(keywords[:5])}",
            'session_format': f"chat:{self._generate_flow_key(flow_data['discovered_name'])}:{{uuid}}",
            'config': {
                'temperature': temperature,
                'maxOutputTokens': 2000,
                'rephrasePrompt': rephrase_prompt,
                'responsePrompt': response_prompt
            },
            'intent_keywords': keywords,
            'status': flow_data['status'],
            'auto_discovered': True,
            'last_analyzed': datetime.now().isoformat(),
            'performance_metrics': {
                'success_score': flow_data['success_score'],
                'engagement_score': flow_data['engagement_score'],
                'total_usage': flow_data['message_count']
            }
        }
    
    def _find_existing_flow_config(self, registry: Dict[str, Any], flow_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find existing flow config by ID"""
        for section in ['operational_flows', 'routing_flows']:
            if section in registry:
                for flow_key, config in registry[section].items():
                    if config.get('id') == flow_id:
                        return (flow_key, config)
        return None
    
    def _find_flow_config_by_name(self, registry: Dict[str, Any], flow_name: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Find existing flow config by name"""
        for section in ['operational_flows', 'routing_flows']:
            if section in registry:
                for flow_key, config in registry[section].items():
                    if config.get('name', '').lower() == flow_name.lower():
                        return (flow_key, config)
        return None
    
    def _update_flow_config(self, config: Dict[str, Any], flow_data: Dict[str, Any]) -> bool:
        """Update existing flow config with database insights"""
        updated = False
        
        # Update performance metrics
        if 'performance_metrics' not in config:
            config['performance_metrics'] = {}
            
        old_success = config['performance_metrics'].get('success_score', 0)
        new_success = flow_data['success_score']
        
        if abs(new_success - old_success) > 0.1:  # Significant change
            config['performance_metrics']['success_score'] = new_success
            config['performance_metrics']['engagement_score'] = flow_data['engagement_score']
            config['performance_metrics']['total_usage'] = flow_data['message_count']
            config['last_analyzed'] = datetime.now().isoformat()
            updated = True
        
        # Update keywords if significantly different
        current_keywords = set(config.get('intent_keywords', []))
        new_keywords = set(flow_data['keywords'])
        
        if len(new_keywords - current_keywords) >= 3:  # 3+ new keywords
            # Add new keywords but preserve existing ones
            config['intent_keywords'] = list(current_keywords | new_keywords)[:20]  # Limit size
            updated = True
        
        return updated
    
    def _apply_performance_optimizations(self, config: Dict[str, Any], report: FlowPerformanceReport) -> None:
        """Apply performance-based optimizations to flow config"""
        
        if 'config' not in config:
            config['config'] = {}
        
        # Adjust temperature based on engagement
        if report.user_engagement < 0.4:
            # Low engagement - try more creative responses
            current_temp = config['config'].get('temperature', 0.7)
            config['config']['temperature'] = min(current_temp + 0.1, 0.9)
        
        # Add follow-up prompts for low session length
        if report.avg_session_length < 3:
            response_prompt = config['config'].get('responsePrompt', '')
            if 'follow-up' not in response_prompt.lower():
                config['config']['responsePrompt'] = response_prompt + "\n\nSuggest related questions to explore further."
        
        # Update based on successful patterns
        if report.successful_keywords:
            current_keywords = set(config.get('intent_keywords', []))
            new_keywords = set(report.successful_keywords[:5])  # Top 5
            config['intent_keywords'] = list(current_keywords | new_keywords)[:20]
        
        # Mark as optimized
        config['performance_optimized'] = datetime.now().isoformat()
    
    def _generate_sync_recommendations(self, active_flows: Dict[str, Any], registry: Dict[str, Any]) -> List[str]:
        """Generate recommendations for configuration improvements"""
        recommendations = []
        
        # High-usage flows without proper configuration
        high_usage_flows = [
            f for f in active_flows.values() 
            if f['message_count'] > 100 and f['success_score'] < 0.7
        ]
        
        if high_usage_flows:
            recommendations.append(f"Review configuration for {len(high_usage_flows)} high-usage flows with low success scores")
        
        # Flows with no keywords
        no_keyword_flows = [
            f for f in active_flows.values()
            if len(f['keywords']) < 3
        ]
        
        if no_keyword_flows:
            recommendations.append(f"Add more specific keywords to {len(no_keyword_flows)} flows for better intent classification")
        
        # Performance optimization opportunities
        global_report = self.analyzer.generate_global_intelligence_report()
        if global_report['system_overview']['average_performance_score'] < 0.7:
            recommendations.append("System-wide performance below target - consider implementing common optimization patterns")
        
        return recommendations
    
    def export_configuration_for_mcp(self, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Export optimized configuration for MCP server integration"""
        
        # Get performance-optimized flows
        active_flows = self.discover_active_flows()
        performance_reports = self.analyzer.analyze_all_flows()
        
        # Filter for user-facing flows (high performance, good engagement)
        mcp_flows = {}
        
        for flow_id, flow_data in active_flows.items():
            flow_name = flow_data['discovered_name']
            
            # Only include flows that are suitable for user access
            if (flow_data['success_score'] > 0.6 and 
                flow_data['engagement_score'] > 0.3 and
                flow_data['message_count'] > 20):
                
                # Get performance insights
                report = performance_reports.get(flow_data['name'])
                
                mcp_config = {
                    'id': flow_id,
                    'name': flow_data['name'],
                    'description': f"Optimized flow for {', '.join(flow_data['keywords'][:3])}",
                    'intent_keywords': flow_data['keywords'][:10],  # Limit for MCP
                    'success_metrics': {
                        'success_score': flow_data['success_score'],
                        'engagement_score': flow_data['engagement_score'],
                        'recommended_for_users': True
                    }
                }
                
                if report:
                    mcp_config['optimization_applied'] = report.recommendations[:2]
                
                mcp_flows[self._generate_flow_key(flow_name)] = mcp_config
        
        mcp_export = {
            'mcp_compatible_flows': mcp_flows,
            'export_timestamp': datetime.now().isoformat(),
            'total_flows_exported': len(mcp_flows),
            'selection_criteria': {
                'min_success_score': 0.6,
                'min_engagement_score': 0.3,
                'min_message_count': 20
            },
            'recommended_tools': [
                'flowise_query',
                'flowise_route',
                'flowise_session_info'
            ]
        }
        
        if target_path:
            with open(target_path, 'w') as f:
                json.dump(mcp_export, f, indent=2, default=str)
            logger.info(f"✅ MCP configuration exported to {target_path}")
        
        return mcp_export

def main():
    """CLI interface for configuration sync"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flowise Configuration Sync")
    parser.add_argument("--database", default="/home/jgi/.flowise/database.sqlite",
                       help="Path to flowise database")
    parser.add_argument("--config-path", default="/a/src/api/flowise",
                       help="Path to configuration files")
    parser.add_argument("--discover", action="store_true", help="Discover active flows")
    parser.add_argument("--sync", action="store_true", help="Sync flow registry")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no changes)")
    parser.add_argument("--export-mcp", help="Export MCP-compatible configuration to file")
    parser.add_argument("--report", help="Export sync report to JSON file")
    
    args = parser.parse_args()
    
    try:
        sync = ConfigurationSync(args.database, args.config_path)
        
        if args.discover:
            flows = sync.discover_active_flows()
            print(f"🔍 Discovered {len(flows)} active flows:")
            for flow_id, flow_data in flows.items():
                print(f"  • {flow_data['discovered_name']}: {flow_data['message_count']} msgs, {flow_data['success_score']:.2f} success")
        
        elif args.sync:
            report = sync.sync_flow_registry(dry_run=args.dry_run)
            
            print(f"🔄 Sync Results:")
            print(f"  📊 Flows discovered: {report.flows_discovered}")
            print(f"  ➕ Flows added: {report.flows_added}")
            print(f"  🔄 Flows updated: {report.flows_updated}")
            print(f"  🎯 Performance improvements: {len(report.performance_improvements)}")
            
            if report.recommendations:
                print(f"\n💡 Recommendations:")
                for rec in report.recommendations:
                    print(f"  • {rec}")
            
            if args.report:
                with open(args.report, 'w') as f:
                    json.dump(asdict(report), f, indent=2, default=str)
                print(f"📄 Report saved to {args.report}")
        
        elif args.export_mcp:
            config = sync.export_configuration_for_mcp(args.export_mcp)
            print(f"✅ Exported {config['total_flows_exported']} MCP-compatible flows")
            
        else:
            # Default: show discovery summary
            flows = sync.discover_active_flows()
            print(f"📈 Configuration Sync Summary:")
            print(f"  🔍 Active flows discovered: {len(flows)}")
            
            high_performers = [f for f in flows.values() if f['success_score'] > 0.8]
            needs_attention = [f for f in flows.values() if f['success_score'] < 0.6]
            
            print(f"  🏆 High performers: {len(high_performers)}")
            print(f"  ⚠️  Needs attention: {len(needs_attention)}")
            print(f"\nUse --sync to synchronize configurations")
            
    except Exception as e:
        print(f"❌ Sync failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()