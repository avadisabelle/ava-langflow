"""
Universal Flow Platform - Backend Abstraction Layer
Provides unified interfaces for multiple flow execution engines
"""

from .base import FlowBackend, UniversalFlow, UniversalSession, UniversalPerformanceMetrics
from .registry import BackendRegistry

__all__ = [
    'FlowBackend',
    'UniversalFlow', 
    'UniversalSession',
    'UniversalPerformanceMetrics',
    'BackendRegistry'
]