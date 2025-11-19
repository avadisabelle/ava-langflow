"""Intelligent backend routing for Universal Query

This module provides intelligent routing logic for selecting optimal backends
based on query intent, backend health, and historical performance.
"""

from .router import (
    UniversalRouter,
    BackendScore,
    RoutingDecision,
    classify_intent,
    extract_keywords
)

__all__ = [
    'UniversalRouter',
    'BackendScore',
    'RoutingDecision',
    'classify_intent',
    'extract_keywords'
]

__version__ = '1.0.0'
