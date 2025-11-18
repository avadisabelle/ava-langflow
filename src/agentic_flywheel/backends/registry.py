#!/usr/bin/env python3
"""
Backend Registry System
Manages discovery, registration, and lifecycle of flow execution backends
"""

import asyncio
import importlib
import logging
from typing import Any, Dict, List, Optional, Type, Set
from pathlib import Path
import json
from dataclasses import asdict

from .base import FlowBackend, BackendType, UniversalFlow, UniversalPerformanceMetrics


logger = logging.getLogger(__name__)


class BackendRegistry:
    """Central registry for managing flow execution backends"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.backends: Dict[BackendType, FlowBackend] = {}
        self.backend_classes: Dict[BackendType, Type[FlowBackend]] = {}
        self.config_path = config_path or "backend_registry.json"
        self._flows_cache: Dict[str, UniversalFlow] = {}
        self._performance_cache: Dict[str, UniversalPerformanceMetrics] = {}
        self._health_status: Dict[BackendType, bool] = {}
    
    async def discover_backends(self) -> None:
        """Auto-discover available backend implementations"""
        logger.info("🔍 Discovering available backends...")
        
        # Look for backend implementations in the backends directory
        backends_dir = Path(__file__).parent
        
        # Import known backends
        await self._import_backend_modules(backends_dir)
        
        # Register discovered backends
        await self._register_discovered_backends()
        
        logger.info(f"✅ Discovered {len(self.backend_classes)} backend types")
    
    async def _import_backend_modules(self, backends_dir: Path) -> None:
        """Import backend modules from the backends directory"""
        for module_file in backends_dir.glob("*.py"):
            if module_file.name in ["__init__.py", "base.py", "registry.py"]:
                continue
            
            module_name = module_file.stem
            try:
                # Dynamic import of backend modules
                module = importlib.import_module(f"backends.{module_name}")
                logger.info(f"📦 Imported backend module: {module_name}")
                
                # Look for backend classes in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, FlowBackend) and 
                        attr != FlowBackend):
                        backend_type = getattr(attr, 'BACKEND_TYPE', None)
                        if backend_type:
                            self.backend_classes[backend_type] = attr
                            logger.info(f"🎯 Registered backend class: {attr.__name__} for {backend_type.value}")
            
            except Exception as e:
                logger.warning(f"⚠️ Failed to import backend module {module_name}: {e}")
    
    async def _register_discovered_backends(self) -> None:
        """Register and initialize discovered backends"""
        for backend_type, backend_class in self.backend_classes.items():
            try:
                # Initialize with default configuration
                backend = backend_class(backend_type)
                self.backends[backend_type] = backend
                logger.info(f"✅ Registered {backend_type.value} backend")
            except Exception as e:
                logger.error(f"❌ Failed to register {backend_type.value} backend: {e}")
    
    async def register_backend(self, backend: FlowBackend) -> None:
        """Manually register a backend instance"""
        self.backends[backend.backend_type] = backend
        await self._update_health_status(backend.backend_type)
        logger.info(f"📋 Manually registered {backend.backend_type.value} backend")
    
    async def connect_backend(self, backend_type: BackendType, config: Optional[Dict[str, Any]] = None) -> bool:
        """Connect to a specific backend"""
        if backend_type not in self.backends:
            logger.error(f"❌ Backend {backend_type.value} not registered")
            return False
        
        backend = self.backends[backend_type]
        if config:
            backend.config.update(config)
        
        try:
            success = await backend.connect()
            await self._update_health_status(backend_type)
            
            if success:
                logger.info(f"🔗 Connected to {backend_type.value} backend")
                # Refresh flows cache for this backend
                await self._refresh_flows_cache(backend_type)
            else:
                logger.error(f"❌ Failed to connect to {backend_type.value} backend")
            
            return success
        except Exception as e:
            logger.error(f"❌ Connection error for {backend_type.value}: {e}")
            return False
    
    async def connect_all_backends(self, configs: Optional[Dict[BackendType, Dict[str, Any]]] = None) -> Dict[BackendType, bool]:
        """Connect to all registered backends"""
        results = {}
        tasks = []
        
        for backend_type in self.backends.keys():
            config = configs.get(backend_type) if configs else None
            task = self.connect_backend(backend_type, config)
            tasks.append((backend_type, task))
        
        for backend_type, task in tasks:
            results[backend_type] = await task
        
        connected_count = sum(results.values())
        logger.info(f"🌐 Connected to {connected_count}/{len(results)} backends")
        
        return results
    
    async def disconnect_backend(self, backend_type: BackendType) -> None:
        """Disconnect from a specific backend"""
        if backend_type not in self.backends:
            return
        
        backend = self.backends[backend_type]
        try:
            await backend.disconnect()
            self._health_status[backend_type] = False
            logger.info(f"🔌 Disconnected from {backend_type.value} backend")
        except Exception as e:
            logger.error(f"❌ Disconnect error for {backend_type.value}: {e}")
    
    async def disconnect_all_backends(self) -> None:
        """Disconnect from all backends"""
        tasks = [self.disconnect_backend(backend_type) for backend_type in self.backends.keys()]
        await asyncio.gather(*tasks, return_exceptions=True)
        logger.info("🔌 Disconnected from all backends")
    
    async def health_check_all(self) -> Dict[BackendType, bool]:
        """Perform health checks on all backends"""
        results = {}
        
        for backend_type, backend in self.backends.items():
            try:
                is_healthy = await backend.health_check()
                results[backend_type] = is_healthy
                self._health_status[backend_type] = is_healthy
            except Exception as e:
                logger.error(f"❌ Health check failed for {backend_type.value}: {e}")
                results[backend_type] = False
                self._health_status[backend_type] = False
        
        healthy_count = sum(results.values())
        logger.info(f"💓 {healthy_count}/{len(results)} backends healthy")
        
        return results
    
    async def _update_health_status(self, backend_type: BackendType) -> None:
        """Update health status for a specific backend"""
        if backend_type in self.backends:
            try:
                backend = self.backends[backend_type]
                is_healthy = await backend.health_check()
                self._health_status[backend_type] = is_healthy
            except:
                self._health_status[backend_type] = False
    
    # Flow Management Across Backends
    async def discover_all_flows(self) -> Dict[BackendType, List[UniversalFlow]]:
        """Discover flows from all connected backends"""
        flows_by_backend = {}
        
        for backend_type, backend in self.backends.items():
            if not backend.is_connected:
                continue
            
            try:
                flows = await backend.discover_flows()
                flows_by_backend[backend_type] = flows
                
                # Update cache
                for flow in flows:
                    self._flows_cache[flow.id] = flow
                
                logger.info(f"🔍 Discovered {len(flows)} flows from {backend_type.value}")
            except Exception as e:
                logger.error(f"❌ Flow discovery failed for {backend_type.value}: {e}")
                flows_by_backend[backend_type] = []
        
        return flows_by_backend
    
    async def get_all_flows(self) -> List[UniversalFlow]:
        """Get all flows from all backends"""
        all_flows = []
        flows_by_backend = await self.discover_all_flows()
        
        for flows in flows_by_backend.values():
            all_flows.extend(flows)
        
        return all_flows
    
    async def find_flow(self, flow_id: str) -> Optional[UniversalFlow]:
        """Find a flow across all backends"""
        # Check cache first
        if flow_id in self._flows_cache:
            return self._flows_cache[flow_id]
        
        # Search across backends
        for backend in self.backends.values():
            if not backend.is_connected:
                continue
            
            try:
                flow = await backend.get_flow(flow_id)
                if flow:
                    self._flows_cache[flow_id] = flow
                    return flow
            except Exception as e:
                logger.warning(f"⚠️ Error searching for flow {flow_id} in {backend.backend_type.value}: {e}")
        
        return None
    
    async def find_best_backend_for_task(self, task_requirements: Dict[str, Any]) -> Optional[BackendType]:
        """Find the optimal backend for a given task"""
        # Simple heuristic-based selection (can be enhanced with ML)
        capabilities = task_requirements.get('capabilities', [])
        preferred_backend = task_requirements.get('preferred_backend')
        
        # If specific backend preferred and available
        if preferred_backend and preferred_backend in self.backends:
            backend = self.backends[preferred_backend]
            if backend.is_connected and self._health_status.get(preferred_backend, False):
                return preferred_backend
        
        # Heuristic selection based on capabilities
        if 'rag' in capabilities or 'retrieval' in capabilities:
            # Langflow is optimized for RAG
            if BackendType.LANGFLOW in self.backends and self._health_status.get(BackendType.LANGFLOW, False):
                return BackendType.LANGFLOW
        
        if 'chat' in capabilities or 'conversation' in capabilities:
            # Flowise is optimized for chat
            if BackendType.FLOWISE in self.backends and self._health_status.get(BackendType.FLOWISE, False):
                return BackendType.FLOWISE
        
        # Default to any healthy backend
        for backend_type, is_healthy in self._health_status.items():
            if is_healthy:
                return backend_type
        
        return None
    
    async def execute_flow_intelligent(self, 
                                     flow_id: str, 
                                     input_data: Any,
                                     parameters: Optional[Dict[str, Any]] = None,
                                     task_hints: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute flow with intelligent backend selection"""
        # Find the flow
        flow = await self.find_flow(flow_id)
        if not flow:
            return {"error": f"Flow {flow_id} not found"}
        
        # Get backend for this flow
        backend = self.backends.get(flow.backend)
        if not backend or not backend.is_connected:
            return {"error": f"Backend {flow.backend.value} not available"}
        
        # Execute the flow
        try:
            result = await backend.execute_flow(flow_id, input_data, parameters)
            
            # Add metadata about execution
            if isinstance(result, dict):
                result['_universal_metadata'] = {
                    'backend_used': flow.backend.value,
                    'flow_id': flow_id,
                    'execution_path': 'intelligent_routing'
                }
            
            return result
        except Exception as e:
            logger.error(f"❌ Flow execution failed: {e}")
            return {"error": f"Flow execution failed: {str(e)}"}
    
    async def _refresh_flows_cache(self, backend_type: BackendType) -> None:
        """Refresh flow cache for a specific backend"""
        backend = self.backends.get(backend_type)
        if backend and backend.is_connected:
            try:
                flows = await backend.discover_flows()
                for flow in flows:
                    self._flows_cache[flow.id] = flow
            except Exception as e:
                logger.error(f"❌ Cache refresh failed for {backend_type.value}: {e}")
    
    # Configuration Management
    def save_config(self) -> None:
        """Save registry configuration to file"""
        config = {
            'backends': {
                backend_type.value: backend.serialize_config()
                for backend_type, backend in self.backends.items()
            },
            'health_status': {
                backend_type.value: status
                for backend_type, status in self._health_status.items()
            }
        }
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"💾 Saved registry configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save config: {e}")
    
    def load_config(self) -> None:
        """Load registry configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Restore health status
            for backend_name, status in config.get('health_status', {}).items():
                backend_type = BackendType(backend_name)
                self._health_status[backend_type] = status
            
            logger.info(f"📂 Loaded registry configuration from {self.config_path}")
        except FileNotFoundError:
            logger.info("📄 No existing config file found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Failed to load config: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive registry status"""
        return {
            'registered_backends': len(self.backends),
            'backend_types': [bt.value for bt in self.backends.keys()],
            'health_status': {bt.value: status for bt, status in self._health_status.items()},
            'connected_backends': sum(1 for b in self.backends.values() if b.is_connected),
            'cached_flows': len(self._flows_cache),
            'available_backend_classes': len(self.backend_classes)
        }
    
    def __str__(self) -> str:
        status = self.get_status()
        return f"BackendRegistry({status['connected_backends']}/{status['registered_backends']} connected, {status['cached_flows']} flows cached)"
    
    def __repr__(self) -> str:
        return f"BackendRegistry(backends={list(self.backends.keys())}, health={self._health_status})"


# Global registry instance
_global_registry: Optional[BackendRegistry] = None


def get_global_registry() -> BackendRegistry:
    """Get the global backend registry instance"""
    global _global_registry
    if _global_registry is None:
        _global_registry = BackendRegistry()
    return _global_registry


async def initialize_global_registry(config_path: Optional[str] = None) -> BackendRegistry:
    """Initialize the global backend registry"""
    global _global_registry
    _global_registry = BackendRegistry(config_path)
    
    # Load existing config
    _global_registry.load_config()
    
    # Discover available backends
    await _global_registry.discover_backends()
    
    return _global_registry