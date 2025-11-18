#!/usr/bin/env python3
"""
Universal Flow Backend Interface
Defines the contract that all flow execution backends must implement
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime


class BackendType(Enum):
    """Supported backend types"""
    FLOWISE = "flowise"
    LANGFLOW = "langflow" 
    CUSTOM = "custom"


class FlowStatus(Enum):
    """Universal flow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class UniversalFlow:
    """Platform-agnostic flow definition"""
    id: str
    name: str
    description: str
    backend: BackendType
    backend_specific_id: str  # The actual ID used by the backend
    
    # Flow characteristics
    intent_keywords: List[str]
    capabilities: List[str]  # e.g., ["chat", "rag", "code_generation", "orchestration"]
    input_types: List[str]   # e.g., ["text", "file", "json"]
    output_types: List[str]  # e.g., ["text", "structured", "stream"]
    
    # Performance and optimization
    performance_score: float = 0.0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    user_rating: float = 0.0
    
    # Configuration
    default_parameters: Dict[str, Any] = None
    required_parameters: List[str] = None
    optional_parameters: Dict[str, Any] = None
    
    # Metadata
    created_at: datetime = None
    updated_at: datetime = None
    version: str = "1.0.0"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.default_parameters is None:
            self.default_parameters = {}
        if self.required_parameters is None:
            self.required_parameters = []
        if self.optional_parameters is None:
            self.optional_parameters = {}
        if self.tags is None:
            self.tags = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass
class UniversalSession:
    """Platform-agnostic session management"""
    id: str
    backend: BackendType
    backend_session_id: str  # Backend-specific session ID
    
    # Session state
    status: FlowStatus = FlowStatus.PENDING
    current_flow_id: Optional[str] = None
    context: Dict[str, Any] = None
    history: List[Dict[str, Any]] = None
    
    # Session metadata
    created_at: datetime = None
    updated_at: datetime = None
    expires_at: Optional[datetime] = None
    user_id: Optional[str] = None
    
    # Performance tracking
    total_queries: int = 0
    successful_queries: int = 0
    total_response_time: float = 0.0
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.history is None:
            self.history = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()


@dataclass  
class UniversalPerformanceMetrics:
    """Universal performance analytics across backends"""
    backend: BackendType
    flow_id: str
    
    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time: float = 0.0
    median_execution_time: float = 0.0
    
    # Quality metrics
    user_satisfaction: float = 0.0
    completion_rate: float = 0.0
    error_rate: float = 0.0
    
    # Usage patterns
    peak_usage_times: List[str] = None
    common_parameters: Dict[str, Any] = None
    failure_patterns: List[str] = None
    
    # Optimization recommendations
    recommendations: List[str] = None
    optimization_score: float = 0.0
    
    def __post_init__(self):
        if self.peak_usage_times is None:
            self.peak_usage_times = []
        if self.common_parameters is None:
            self.common_parameters = {}
        if self.failure_patterns is None:
            self.failure_patterns = []
        if self.recommendations is None:
            self.recommendations = []


class FlowBackend(ABC):
    """Abstract base class for all flow execution backends"""
    
    def __init__(self, backend_type: BackendType, config: Dict[str, Any] = None):
        self.backend_type = backend_type
        self.config = config or {}
        self._connection = None
        self._is_connected = False
    
    @property
    def name(self) -> str:
        """Human-readable backend name"""
        return self.backend_type.value.capitalize()
    
    @property
    def is_connected(self) -> bool:
        """Check if backend is connected and available"""
        return self._is_connected
    
    # Connection Management
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the backend"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the backend"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Verify backend is healthy and responsive"""
        pass
    
    # Flow Discovery and Management
    @abstractmethod
    async def discover_flows(self) -> List[UniversalFlow]:
        """Discover and catalog all available flows from the backend"""
        pass
    
    @abstractmethod
    async def get_flow(self, flow_id: str) -> Optional[UniversalFlow]:
        """Retrieve a specific flow by its universal ID"""
        pass
    
    @abstractmethod
    async def create_flow(self, flow_definition: Dict[str, Any]) -> UniversalFlow:
        """Create a new flow in the backend"""
        pass
    
    @abstractmethod
    async def update_flow(self, flow_id: str, updates: Dict[str, Any]) -> UniversalFlow:
        """Update an existing flow"""
        pass
    
    @abstractmethod
    async def delete_flow(self, flow_id: str) -> bool:
        """Delete a flow from the backend"""
        pass
    
    # Flow Execution
    @abstractmethod
    async def execute_flow(self, 
                          flow_id: str,
                          input_data: Any,
                          parameters: Optional[Dict[str, Any]] = None,
                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute a flow with given input and parameters"""
        pass
    
    @abstractmethod
    async def stream_flow(self,
                         flow_id: str,
                         input_data: Any,
                         parameters: Optional[Dict[str, Any]] = None,
                         session_id: Optional[str] = None):
        """Execute a flow with streaming response"""
        pass
    
    # Session Management
    @abstractmethod
    async def create_session(self, flow_id: str, config: Optional[Dict[str, Any]] = None) -> UniversalSession:
        """Create a new session for flow execution"""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[UniversalSession]:
        """Retrieve session information"""
        pass
    
    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> UniversalSession:
        """Update session state"""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """Delete/close a session"""
        pass
    
    @abstractmethod
    async def list_sessions(self, flow_id: Optional[str] = None) -> List[UniversalSession]:
        """List active sessions, optionally filtered by flow"""
        pass
    
    # Performance and Analytics
    @abstractmethod
    async def get_performance_metrics(self, flow_id: str) -> UniversalPerformanceMetrics:
        """Get performance analytics for a flow"""
        pass
    
    @abstractmethod
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get overall backend system metrics"""
        pass
    
    @abstractmethod
    async def analyze_usage_patterns(self, flow_id: Optional[str] = None) -> Dict[str, Any]:
        """Analyze usage patterns for optimization"""
        pass
    
    # Configuration and Parameters
    @abstractmethod
    async def validate_parameters(self, flow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate parameters against flow requirements"""
        pass
    
    @abstractmethod
    async def get_parameter_schema(self, flow_id: str) -> Dict[str, Any]:
        """Get parameter schema for a flow"""
        pass
    
    # Utility Methods
    def to_universal_flow(self, backend_flow: Any) -> UniversalFlow:
        """Convert backend-specific flow to universal format"""
        raise NotImplementedError("Subclasses must implement to_universal_flow")
    
    def from_universal_flow(self, universal_flow: UniversalFlow) -> Any:
        """Convert universal flow to backend-specific format"""
        raise NotImplementedError("Subclasses must implement from_universal_flow")
    
    def serialize_config(self) -> Dict[str, Any]:
        """Serialize backend configuration for storage"""
        return {
            'backend_type': self.backend_type.value,
            'config': self.config,
            'is_connected': self.is_connected
        }
    
    @classmethod
    def deserialize_config(cls, config_data: Dict[str, Any]) -> 'FlowBackend':
        """Deserialize backend configuration"""
        backend_type = BackendType(config_data['backend_type'])
        return cls(backend_type, config_data['config'])
    
    def __str__(self) -> str:
        return f"{self.name} Backend ({'Connected' if self.is_connected else 'Disconnected'})"
    
    def __repr__(self) -> str:
        return f"FlowBackend(type={self.backend_type.value}, connected={self.is_connected})"


# Utility functions for type conversion
def flow_to_dict(flow: UniversalFlow) -> Dict[str, Any]:
    """Convert UniversalFlow to dictionary"""
    return {
        'id': flow.id,
        'name': flow.name,
        'description': flow.description,
        'backend': flow.backend.value,
        'backend_specific_id': flow.backend_specific_id,
        'intent_keywords': flow.intent_keywords,
        'capabilities': flow.capabilities,
        'input_types': flow.input_types,
        'output_types': flow.output_types,
        'performance_score': flow.performance_score,
        'success_rate': flow.success_rate,
        'avg_response_time': flow.avg_response_time,
        'user_rating': flow.user_rating,
        'default_parameters': flow.default_parameters,
        'required_parameters': flow.required_parameters,
        'optional_parameters': flow.optional_parameters,
        'created_at': flow.created_at.isoformat() if flow.created_at else None,
        'updated_at': flow.updated_at.isoformat() if flow.updated_at else None,
        'version': flow.version,
        'tags': flow.tags
    }


def dict_to_flow(data: Dict[str, Any]) -> UniversalFlow:
    """Convert dictionary to UniversalFlow"""
    return UniversalFlow(
        id=data['id'],
        name=data['name'],
        description=data['description'],
        backend=BackendType(data['backend']),
        backend_specific_id=data['backend_specific_id'],
        intent_keywords=data['intent_keywords'],
        capabilities=data['capabilities'],
        input_types=data['input_types'],
        output_types=data['output_types'],
        performance_score=data.get('performance_score', 0.0),
        success_rate=data.get('success_rate', 0.0),
        avg_response_time=data.get('avg_response_time', 0.0),
        user_rating=data.get('user_rating', 0.0),
        default_parameters=data.get('default_parameters', {}),
        required_parameters=data.get('required_parameters', []),
        optional_parameters=data.get('optional_parameters', {}),
        created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
        updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
        version=data.get('version', '1.0.0'),
        tags=data.get('tags', [])
    )