#!/usr/bin/env python3
"""
Flowise Backend Implementation
Integrates existing flowise_admin intelligence with universal backend interface
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Add parent directories to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from backends.base import FlowBackend, BackendType, UniversalFlow, UniversalSession, UniversalPerformanceMetrics, FlowStatus

# Import existing flowise admin components
try:
    from flowise_admin import FlowiseDBInterface, FlowAnalyzer, ConfigurationSync
    from flowise_manager import FlowiseManager
    FLOWISE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Flowise admin components not available: {e}")
    FlowiseDBInterface = None
    FlowAnalyzer = None
    ConfigurationSync = None
    FlowiseManager = None
    FLOWISE_AVAILABLE = False


logger = logging.getLogger(__name__)


class FlowiseBackend(FlowBackend):
    """Flowise backend implementation using existing admin intelligence"""
    
    BACKEND_TYPE = BackendType.FLOWISE
    
    def __init__(self, backend_type: BackendType = BackendType.FLOWISE, config: Dict[str, Any] = None):
        super().__init__(backend_type, config)
        
        # Flowise-specific components
        self.db_interface = None
        self.flow_analyzer = None
        self.config_sync = None
        self.flowise_manager = None
        
        # Universal mappings
        self._flow_id_mapping: Dict[str, str] = {}  # universal_id -> flowise_id
        self._session_mapping: Dict[str, str] = {}  # universal_session_id -> flowise_session_id
        
        # Initialize if components are available
        if FLOWISE_AVAILABLE:
            self._initialize_components()
    
    def _initialize_components(self):
        """Initialize Flowise admin components"""
        try:
            if FlowiseManager:
                self.flowise_manager = FlowiseManager()
                logger.info("✅ FlowiseManager initialized")
            
            if FlowiseDBInterface:
                self.db_interface = FlowiseDBInterface()
                logger.info("✅ FlowiseDBInterface initialized")
            
            if FlowAnalyzer:
                self.flow_analyzer = FlowAnalyzer()
                logger.info("✅ FlowAnalyzer initialized")
            
            if ConfigurationSync:
                self.config_sync = ConfigurationSync()
                logger.info("✅ ConfigurationSync initialized")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Flowise components: {e}")
    
    # Connection Management
    async def connect(self) -> bool:
        """Establish connection to Flowise backend"""
        if not FLOWISE_AVAILABLE:
            logger.error("❌ Flowise components not available")
            return False
        
        try:
            # Test connection through flowise manager
            if self.flowise_manager:
                connection_test = self.flowise_manager.test_connection()
                if connection_test:
                    self._is_connected = True
                    logger.info("🔗 Connected to Flowise backend")
                    return True
            
            # Fallback: test database connection
            if self.db_interface:
                dashboard = self.db_interface.get_admin_dashboard_data()
                if dashboard:
                    self._is_connected = True
                    logger.info("🔗 Connected to Flowise via database")
                    return True
            
            logger.error("❌ Failed to connect to Flowise backend")
            return False
            
        except Exception as e:
            logger.error(f"❌ Flowise connection error: {e}")
            return False
    
    async def disconnect(self) -> None:
        """Close connection to Flowise backend"""
        self._is_connected = False
        logger.info("🔌 Disconnected from Flowise backend")
    
    async def health_check(self) -> bool:
        """Verify Flowise backend is healthy"""
        if not FLOWISE_AVAILABLE or not self._is_connected:
            return False
        
        try:
            # Test through flowise manager if available
            if self.flowise_manager:
                return self.flowise_manager.test_connection()
            
            # Test database interface
            if self.db_interface:
                dashboard = self.db_interface.get_admin_dashboard_data()
                return dashboard is not None
            
            return False
        except:
            return False
    
    # Flow Discovery and Management
    async def discover_flows(self) -> List[UniversalFlow]:
        """Discover flows from Flowise using admin intelligence"""
        if not self._is_connected or not self.config_sync:
            return []
        
        try:
            # Get flows from admin configuration sync
            active_flows = self.config_sync.discover_active_flows()
            mcp_export = self.config_sync.export_configuration_for_mcp()
            
            universal_flows = []
            
            for flow_key, flow_data in mcp_export['mcp_compatible_flows'].items():
                # Convert to universal format
                universal_flow = self._convert_to_universal_flow(flow_key, flow_data)
                universal_flows.append(universal_flow)
                
                # Update mapping
                self._flow_id_mapping[universal_flow.id] = flow_data['id']
            
            logger.info(f"🔍 Discovered {len(universal_flows)} Flowise flows")
            return universal_flows
            
        except Exception as e:
            logger.error(f"❌ Flowise flow discovery failed: {e}")
            return []
    
    def _convert_to_universal_flow(self, flow_key: str, flow_data: Dict[str, Any]) -> UniversalFlow:
        """Convert Flowise flow data to universal format"""
        # Extract performance metrics from flow data
        metrics = flow_data.get('success_metrics', {})
        
        return UniversalFlow(
            id=f"flowise_{flow_key}",  # Universal ID
            name=flow_data.get('name', flow_key),
            description=flow_data.get('description', f"Flowise flow: {flow_key}"),
            backend=BackendType.FLOWISE,
            backend_specific_id=flow_data['id'],  # Original Flowise ID
            
            # Flow characteristics
            intent_keywords=flow_data.get('intent_keywords', []),
            capabilities=['chat', 'conversation', 'llm'],  # Flowise capabilities
            input_types=['text'],
            output_types=['text'],
            
            # Performance metrics
            performance_score=metrics.get('success_score', 0.0),
            success_rate=metrics.get('success_score', 0.0),
            avg_response_time=0.0,  # Would need to be calculated from usage data
            user_rating=metrics.get('engagement_score', 0.0),
            
            # Configuration
            default_parameters={},
            required_parameters=[],
            optional_parameters={},
            
            # Metadata
            created_at=datetime.now(),
            updated_at=datetime.now(),
            version="1.0.0",
            tags=['flowise', 'admin_curated']
        )
    
    async def get_flow(self, flow_id: str) -> Optional[UniversalFlow]:
        """Retrieve a specific flow by universal ID"""
        flows = await self.discover_flows()
        for flow in flows:
            if flow.id == flow_id:
                return flow
        return None
    
    async def create_flow(self, flow_definition: Dict[str, Any]) -> UniversalFlow:
        """Create a new flow in Flowise (not implemented - requires Flowise API)"""
        raise NotImplementedError("Flow creation requires Flowise API integration")
    
    async def update_flow(self, flow_id: str, updates: Dict[str, Any]) -> UniversalFlow:
        """Update an existing flow (not implemented - requires Flowise API)"""
        raise NotImplementedError("Flow updates require Flowise API integration")
    
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow (not implemented - requires Flowise API)"""
        raise NotImplementedError("Flow deletion requires Flowise API integration")
    
    # Flow Execution
    async def execute_flow(self, 
                          flow_id: str,
                          input_data: Any,
                          parameters: Optional[Dict[str, Any]] = None,
                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a Flowise flow"""
        if not self._is_connected or not self.flowise_manager:
            return {"error": "Flowise backend not connected"}
        
        try:
            # Get Flowise flow ID
            flowise_flow_id = self._flow_id_mapping.get(flow_id)
            if not flowise_flow_id:
                # Try to extract from universal ID
                if flow_id.startswith("flowise_"):
                    flow_key = flow_id[8:]  # Remove "flowise_" prefix
                    flowise_flow_id = self._get_flowise_id_from_key(flow_key)
            
            if not flowise_flow_id:
                return {"error": f"Flow ID {flow_id} not found in Flowise"}
            
            # Convert session ID if provided
            flowise_session_id = None
            if session_id:
                flowise_session_id = self._session_mapping.get(session_id, session_id)
            
            # Execute using flowise manager
            result = self.flowise_manager.adaptive_query(
                question=str(input_data),
                intent=flow_key if 'flow_key' in locals() else None,
                session_id=flowise_session_id
            )
            
            # Add universal metadata
            if isinstance(result, dict):
                result['_universal_metadata'] = {
                    'backend': 'flowise',
                    'flow_id': flow_id,
                    'flowise_flow_id': flowise_flow_id,
                    'execution_time': datetime.now().isoformat()
                }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Flowise flow execution failed: {e}")
            return {"error": f"Execution failed: {str(e)}"}
    
    def _get_flowise_id_from_key(self, flow_key: str) -> Optional[str]:
        """Get Flowise ID from flow key using config sync"""
        if not self.config_sync:
            return None
        
        try:
            active_flows = self.config_sync.discover_active_flows()
            return active_flows.get(flow_key, {}).get('id')
        except:
            return None
    
    async def stream_flow(self,
                         flow_id: str,
                         input_data: Any,
                         parameters: Optional[Dict[str, Any]] = None,
                         session_id: Optional[str] = None):
        """Execute flow with streaming (not implemented - requires streaming API)"""
        # For now, return regular execution as single yield
        result = await self.execute_flow(flow_id, input_data, parameters, session_id)
        yield result
    
    # Session Management
    async def create_session(self, flow_id: str, config: Optional[Dict[str, Any]] = None) -> UniversalSession:
        """Create a new session for flow execution"""
        import uuid
        
        universal_session_id = f"flowise_session_{uuid.uuid4().hex[:8]}"
        flowise_session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        # Store mapping
        self._session_mapping[universal_session_id] = flowise_session_id
        
        return UniversalSession(
            id=universal_session_id,
            backend=BackendType.FLOWISE,
            backend_session_id=flowise_session_id,
            status=FlowStatus.PENDING,
            current_flow_id=flow_id,
            context=config or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def get_session(self, session_id: str) -> Optional[UniversalSession]:
        """Retrieve session information (basic implementation)"""
        flowise_session_id = self._session_mapping.get(session_id)
        if not flowise_session_id:
            return None
        
        # Return basic session info (would need Flowise session API for full info)
        return UniversalSession(
            id=session_id,
            backend=BackendType.FLOWISE,
            backend_session_id=flowise_session_id,
            status=FlowStatus.PENDING,  # Would need to query actual status
            updated_at=datetime.now()
        )
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> UniversalSession:
        """Update session state"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Apply updates
        for key, value in updates.items():
            if hasattr(session, key):
                setattr(session, key, value)
        
        session.updated_at = datetime.now()
        return session
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete/close a session"""
        if session_id in self._session_mapping:
            del self._session_mapping[session_id]
            return True
        return False
    
    async def list_sessions(self, flow_id: Optional[str] = None) -> List[UniversalSession]:
        """List active sessions"""
        sessions = []
        for universal_id, flowise_id in self._session_mapping.items():
            session = await self.get_session(universal_id)
            if session:
                sessions.append(session)
        return sessions
    
    # Performance and Analytics
    async def get_performance_metrics(self, flow_id: str) -> UniversalPerformanceMetrics:
        """Get performance analytics using existing flow analyzer"""
        if not self.flow_analyzer:
            return UniversalPerformanceMetrics(
                backend=BackendType.FLOWISE,
                flow_id=flow_id
            )
        
        try:
            # Get analysis from existing flow analyzer
            reports = self.flow_analyzer.analyze_all_flows()
            
            # Find flow by universal ID (extract key)
            flow_key = flow_id.replace("flowise_", "") if flow_id.startswith("flowise_") else flow_id
            
            if flow_key in reports:
                report = reports[flow_key]
                
                return UniversalPerformanceMetrics(
                    backend=BackendType.FLOWISE,
                    flow_id=flow_id,
                    total_executions=report.total_messages,
                    successful_executions=int(report.total_messages * report.performance_score),
                    failed_executions=report.total_messages - int(report.total_messages * report.performance_score),
                    avg_execution_time=0.0,  # Would need timing data
                    median_execution_time=0.0,
                    user_satisfaction=report.user_engagement,
                    completion_rate=report.performance_score,
                    error_rate=1.0 - report.performance_score,
                    recommendations=report.recommendations,
                    optimization_score=report.performance_score
                )
            
        except Exception as e:
            logger.error(f"❌ Failed to get performance metrics: {e}")
        
        return UniversalPerformanceMetrics(
            backend=BackendType.FLOWISE,
            flow_id=flow_id
        )
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall Flowise system metrics"""
        if not self.db_interface:
            return {}
        
        try:
            dashboard = self.db_interface.get_admin_dashboard_data()
            return {
                'total_messages': dashboard['system_health']['total_messages'],
                'total_flows': dashboard['system_health']['total_flows'],
                'avg_success_score': dashboard['system_health']['avg_success_score'],
                'flowise_manager_connected': dashboard['live_integration']['flowise_manager_connected'],
                'backend': 'flowise'
            }
        except Exception as e:
            logger.error(f"❌ Failed to get system metrics: {e}")
            return {}
    
    async def analyze_usage_patterns(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze usage patterns using existing analytics"""
        if not self.flow_analyzer:
            return {}
        
        try:
            reports = self.flow_analyzer.analyze_all_flows()
            
            if flow_id:
                # Specific flow analysis
                flow_key = flow_id.replace("flowise_", "") if flow_id.startswith("flowise_") else flow_id
                if flow_key in reports:
                    report = reports[flow_key]
                    return {
                        'flow_id': flow_id,
                        'usage_patterns': {
                            'total_usage': report.total_messages,
                            'performance_score': report.performance_score,
                            'user_engagement': report.user_engagement,
                            'patterns': report.pattern_insights
                        }
                    }
            else:
                # System-wide analysis
                return {
                    'total_flows_analyzed': len(reports),
                    'avg_performance': sum(r.performance_score for r in reports.values()) / len(reports),
                    'avg_engagement': sum(r.user_engagement for r in reports.values()) / len(reports),
                    'top_performing_flows': [
                        {'id': f"flowise_{k}", 'score': v.performance_score}
                        for k, v in sorted(reports.items(), key=lambda x: x[1].performance_score, reverse=True)[:5]
                    ]
                }
        except Exception as e:
            logger.error(f"❌ Usage pattern analysis failed: {e}")
            return {}
    
    # Configuration and Parameters
    async def validate_parameters(self, flow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters (basic implementation)"""
        # Basic validation - would need flow schema for full validation
        return {
            'valid': True,
            'errors': [],
            'warnings': []
        }
    
    async def get_parameter_schema(self, flow_id: str) -> Dict[str, Any]:
        """Get parameter schema (basic implementation)"""
        return {
            'type': 'object',
            'properties': {},
            'required': []
        }
    
    # Utility Methods
    def to_universal_flow(self, backend_flow: Any) -> UniversalFlow:
        """Convert Flowise flow to universal format"""
        if isinstance(backend_flow, dict):
            return self._convert_to_universal_flow(backend_flow.get('name', 'unknown'), backend_flow)
        raise NotImplementedError("Flow conversion not implemented for this type")
    
    def from_universal_flow(self, universal_flow: UniversalFlow) -> Any:
        """Convert universal flow to Flowise format"""
        return {
            'id': universal_flow.backend_specific_id,
            'name': universal_flow.name,
            'description': universal_flow.description,
            'keywords': universal_flow.intent_keywords
        }