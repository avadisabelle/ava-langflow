#!/usr/bin/env python3
"""
Universal Query MCP Tool

Provides intelligent routing across multiple AI workflow backends (Flowise, Langflow, etc.)
with automatic backend selection based on intent, health, and performance.

Usage:
    handler = UniversalQueryHandler(backend_registry)
    result = await handler.execute_query(
        question="Help me analyze this code",
        backend="auto"  # or "flowise", "langflow"
    )

Specification: rispecs/mcp_tools/universal_query.spec.md
"""

import logging
import time
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

from ..backends import (
    FlowBackend,
    BackendType,
    UniversalFlow,
    BackendRegistry
)

logger = logging.getLogger(__name__)


# Intent categories for classification
INTENT_CATEGORIES = {
    'creative-orientation': [
        'creative', 'vision', 'goal', 'tension', 'structural tension',
        'desired outcome', 'current reality', 'rise'
    ],
    'technical-analysis': [
        'code', 'debug', 'error', 'function', 'bug', 'analyze code',
        'technical', 'implementation', 'algorithm'
    ],
    'structural-thinking': [
        'architecture', 'design', 'pattern', 'system', 'structure',
        'framework', 'model', 'abstraction'
    ],
    'rag-retrieval': [
        'document', 'find', 'search', 'retrieve', 'lookup', 'knowledge',
        'information', 'database', 'query'
    ],
    'data-processing': [
        'transform', 'process', 'etl', 'data', 'analyze', 'aggregate',
        'filter', 'parse'
    ],
    'conversation': [
        'chat', 'talk', 'discuss', 'help', 'question', 'tell me'
    ]
}

# Backend capability scores for each intent
BACKEND_CAPABILITIES = {
    BackendType.LANGFLOW: {
        'rag-retrieval': 1.0,
        'data-processing': 0.9,
        'conversation': 0.7,
        'technical-analysis': 0.8,
        'structural-thinking': 0.7,
        'creative-orientation': 0.6
    },
    BackendType.FLOWISE: {
        'conversation': 1.0,
        'creative-orientation': 0.9,
        'structural-thinking': 0.8,
        'technical-analysis': 0.7,
        'rag-retrieval': 0.7,
        'data-processing': 0.6
    }
}


@dataclass
class RoutingDecision:
    """Represents a backend routing decision with metadata"""
    backend: FlowBackend
    flow: UniversalFlow
    score: float
    breakdown: Dict[str, float]
    intent: str
    intent_confidence: float


class NoBackendsAvailable(Exception):
    """Raised when no healthy backends are available"""
    pass


def classify_intent(question: str) -> Tuple[str, float]:
    """
    Classify user intent from question text using keyword matching

    Args:
        question: User's question/prompt

    Returns:
        (intent_category, confidence_score)
    """
    question_lower = question.lower()

    # Score each intent category
    intent_scores = {}
    for intent, keywords in INTENT_CATEGORIES.items():
        # Count matching keywords
        matches = sum(1 for keyword in keywords if keyword in question_lower)
        # Normalize by number of keywords in category
        score = matches / len(keywords) if keywords else 0
        intent_scores[intent] = score

    # Get best match
    if not intent_scores or max(intent_scores.values()) == 0:
        return ('conversation', 0.5)  # Default to conversation

    best_intent = max(intent_scores.items(), key=lambda x: x[1])

    # Calculate confidence based on score distribution
    intent, score = best_intent
    # Normalize confidence: 0-1 match rate → 0.5-0.95 confidence
    confidence = 0.5 + (score * 0.45)

    return (intent, min(confidence, 0.95))


def calculate_flow_match_score(
    flows: List[UniversalFlow],
    intent: str,
    confidence: float
) -> float:
    """
    Calculate how well flows match the intent

    Args:
        flows: Available flows from backend
        intent: Classified intent
        confidence: Intent classification confidence

    Returns:
        Flow match score (0.0 - 1.0)
    """
    if not flows:
        return 0.0

    # Check for exact intent matches
    exact_matches = [f for f in flows if intent in f.intent_keywords]
    if exact_matches:
        return 1.0

    # Check for partial matches (any keyword overlap)
    partial_matches = [
        f for f in flows
        if any(keyword in f.intent_keywords for keyword in INTENT_CATEGORIES.get(intent, []))
    ]
    if partial_matches:
        return 0.7

    # General purpose flows available
    if flows:
        return 0.3

    return 0.0


def get_capability_score(backend: FlowBackend, intent: str) -> float:
    """
    Get backend's capability score for the given intent

    Args:
        backend: Backend to score
        intent: Intent category

    Returns:
        Capability score (0.0 - 1.0)
    """
    capabilities = BACKEND_CAPABILITIES.get(backend.backend_type, {})
    return capabilities.get(intent, 0.5)  # Default to neutral


class UniversalQueryHandler:
    """
    Handles universal query execution with intelligent backend routing
    """

    def __init__(
        self,
        backend_registry: BackendRegistry,
        enable_fallback: bool = True,
        default_timeout: float = 30.0
    ):
        """
        Initialize handler

        Args:
            backend_registry: Backend registry for discovering backends
            enable_fallback: Whether to enable fallback to secondary backends
            default_timeout: Default execution timeout in seconds
        """
        self.registry = backend_registry
        self.enable_fallback = enable_fallback
        self.default_timeout = default_timeout
        self._performance_cache: Dict[BackendType, Dict[str, float]] = {}

    async def execute_query(
        self,
        question: str,
        intent_override: Optional[str] = None,
        backend_override: Optional[str] = None,
        session_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Execute query with intelligent backend routing

        Args:
            question: User's question/prompt
            intent_override: Optional explicit intent (overrides classification)
            backend_override: Optional backend selection ("auto" or backend name)
            session_id: Optional session ID for continuity
            parameters: Optional flow parameters
            timeout: Optional execution timeout

        Returns:
            Query result with metadata
        """
        start_time = time.time()
        timeout = timeout or self.default_timeout

        try:
            # Classify intent (unless overridden)
            if intent_override and intent_override != "auto":
                intent = intent_override
                intent_confidence = 1.0
            else:
                intent, intent_confidence = classify_intent(question)

            logger.info(f"Classified intent: {intent} (confidence: {intent_confidence:.2f})")

            # Select backend
            if backend_override and backend_override != "auto":
                # Explicit backend selection
                routing = await self._select_explicit_backend(
                    backend_override, question, intent, intent_confidence
                )
            else:
                # Intelligent routing
                routing = await self._select_optimal_backend(
                    question, intent, intent_confidence
                )

            # Execute on selected backend
            result = await self._execute_on_backend(
                routing=routing,
                question=question,
                session_id=session_id,
                parameters=parameters,
                timeout=timeout,
                attempt=1
            )

            # Add routing metadata
            execution_time_ms = int((time.time() - start_time) * 1000)
            result['_mcp_metadata'] = {
                'backend_used': routing.backend.backend_type.value,
                'flow_id': routing.flow.id,
                'flow_name': routing.flow.name,
                'routing_score': routing.score,
                'routing_breakdown': routing.breakdown,
                'intent_classified': routing.intent,
                'intent_confidence': routing.intent_confidence,
                'execution_time_ms': execution_time_ms,
                'fallback_used': False,
                'attempt': 1
            }

            # Cache performance metrics
            self._update_performance_cache(
                routing.backend.backend_type,
                success=True,
                latency_ms=execution_time_ms
            )

            return result

        except Exception as e:
            logger.error(f"Query execution failed: {e}")

            # Try fallback if enabled
            if self.enable_fallback:
                return await self._execute_with_fallback(
                    question, intent, intent_confidence, session_id, parameters, timeout, start_time
                )
            else:
                return {
                    'error': str(e),
                    'backend_used': None,
                    'fallback_used': False
                }

    async def _select_explicit_backend(
        self,
        backend_name: str,
        question: str,
        intent: str,
        intent_confidence: float
    ) -> RoutingDecision:
        """Select explicitly requested backend"""
        try:
            backend_type = BackendType(backend_name)
        except ValueError:
            raise ValueError(f"Invalid backend: {backend_name}")

        # Get backend from registry
        if backend_type not in self.registry.backends:
            raise ValueError(f"Backend {backend_name} not registered")

        backend = self.registry.backends[backend_type]

        if not backend.is_connected:
            raise ValueError(f"Backend {backend_name} not connected")

        # Get flows and select best match
        flows = await backend.discover_flows()
        flow = self._select_best_flow(flows, question, intent)

        return RoutingDecision(
            backend=backend,
            flow=flow,
            score=1.0,  # Explicit selection = full confidence
            breakdown={'explicit': 1.0},
            intent=intent,
            intent_confidence=intent_confidence
        )

    async def _select_optimal_backend(
        self,
        question: str,
        intent: str,
        intent_confidence: float
    ) -> RoutingDecision:
        """
        Select optimal backend using scoring algorithm

        Returns:
            RoutingDecision with selected backend and metadata
        """
        # Get all connected backends
        connected_backends = [
            backend for backend in self.registry.backends.values()
            if backend.is_connected
        ]

        if not connected_backends:
            raise NoBackendsAvailable("No connected backends available")

        # Score each backend
        backend_scores = []

        for backend in connected_backends:
            try:
                # Get flows from backend
                flows = await backend.discover_flows()
                matching_flows = [
                    f for f in flows
                    if intent in f.intent_keywords
                ]

                # Calculate component scores
                flow_match = calculate_flow_match_score(flows, intent, intent_confidence)
                health = 1.0 if await backend.health_check() else 0.0
                performance = self._get_cached_performance(backend.backend_type)
                capability = get_capability_score(backend, intent)

                # Combined score (weights from spec)
                total_score = (
                    flow_match * 0.4 +
                    health * 0.3 +
                    performance * 0.2 +
                    capability * 0.1
                )

                # Select best flow
                flow = self._select_best_flow(flows, question, intent)

                backend_scores.append({
                    'backend': backend,
                    'flow': flow,
                    'score': total_score,
                    'breakdown': {
                        'flow_match': flow_match,
                        'health': health,
                        'performance': performance,
                        'capability': capability
                    }
                })

                logger.info(
                    f"Backend {backend.backend_type.value} score: {total_score:.2f} "
                    f"(flow:{flow_match:.2f}, health:{health:.2f}, "
                    f"perf:{performance:.2f}, cap:{capability:.2f})"
                )

            except Exception as e:
                logger.warning(f"Failed to score backend {backend.backend_type.value}: {e}")
                continue

        if not backend_scores:
            raise NoBackendsAvailable("No backends could be scored")

        # Select highest scoring backend
        best = max(backend_scores, key=lambda x: x['score'])

        return RoutingDecision(
            backend=best['backend'],
            flow=best['flow'],
            score=best['score'],
            breakdown=best['breakdown'],
            intent=intent,
            intent_confidence=intent_confidence
        )

    def _select_best_flow(
        self,
        flows: List[UniversalFlow],
        question: str,
        intent: str
    ) -> UniversalFlow:
        """
        Select best flow from available flows

        Args:
            flows: Available flows
            question: User question
            intent: Classified intent

        Returns:
            Best matching flow
        """
        if not flows:
            # Create a default flow placeholder
            return UniversalFlow(
                id="default",
                name="Default Flow",
                description="Default flow",
                backend=BackendType.FLOWISE,
                backend_specific_id="default",
                intent_keywords=[intent],
                capabilities=[],
                input_types=["text"],
                output_types=["text"]
            )

        # Prefer flows with matching intent
        matching = [f for f in flows if intent in f.intent_keywords]
        if matching:
            return matching[0]

        # Fall back to first available flow
        return flows[0]

    async def _execute_on_backend(
        self,
        routing: RoutingDecision,
        question: str,
        session_id: Optional[str],
        parameters: Optional[Dict[str, Any]],
        timeout: float,
        attempt: int
    ) -> Dict[str, Any]:
        """Execute query on selected backend"""
        backend = routing.backend
        flow = routing.flow

        logger.info(
            f"Executing on {backend.backend_type.value} "
            f"(flow: {flow.name}, attempt: {attempt})"
        )

        # Execute flow
        result = await backend.execute_flow(
            flow_id=flow.backend_specific_id,
            input_data={"question": question},
            parameters=parameters or {},
            session_id=session_id
        )

        # Check for errors in result
        if isinstance(result, dict) and 'error' in result:
            raise Exception(result['error'])

        return result

    async def _execute_with_fallback(
        self,
        question: str,
        intent: str,
        intent_confidence: float,
        session_id: Optional[str],
        parameters: Optional[Dict[str, Any]],
        timeout: float,
        start_time: float
    ) -> Dict[str, Any]:
        """Execute with fallback to secondary backends"""
        logger.info("Primary backend failed, attempting fallback...")

        # Get all backends ranked by score
        try:
            connected_backends = [
                b for b in self.registry.backends.values()
                if b.is_connected
            ]

            # Try each backend in order
            last_error = None
            for attempt, backend in enumerate(connected_backends, start=1):
                try:
                    flows = await backend.discover_flows()
                    flow = self._select_best_flow(flows, question, intent)

                    routing = RoutingDecision(
                        backend=backend,
                        flow=flow,
                        score=0.5,  # Lower confidence for fallback
                        breakdown={'fallback': 1.0},
                        intent=intent,
                        intent_confidence=intent_confidence
                    )

                    result = await self._execute_on_backend(
                        routing=routing,
                        question=question,
                        session_id=session_id,
                        parameters=parameters,
                        timeout=timeout,
                        attempt=attempt
                    )

                    # Success with fallback
                    execution_time_ms = int((time.time() - start_time) * 1000)
                    result['_mcp_metadata'] = {
                        'backend_used': backend.backend_type.value,
                        'flow_id': flow.id,
                        'flow_name': flow.name,
                        'routing_score': 0.5,
                        'intent_classified': intent,
                        'intent_confidence': intent_confidence,
                        'execution_time_ms': execution_time_ms,
                        'fallback_used': True,
                        'attempt': attempt
                    }

                    logger.info(f"Fallback successful on {backend.backend_type.value}")
                    return result

                except Exception as e:
                    last_error = e
                    logger.warning(f"Fallback attempt {attempt} failed: {e}")
                    continue

            # All backends failed
            return {
                'error': 'All backends failed',
                'attempts': len(connected_backends),
                'last_error': str(last_error),
                'backends_tried': [b.backend_type.value for b in connected_backends]
            }

        except Exception as e:
            return {
                'error': f'Fallback failed: {str(e)}',
                'fallback_used': True
            }

    def _get_cached_performance(self, backend_type: BackendType) -> float:
        """Get cached performance score for backend (0.0 - 1.0)"""
        if backend_type not in self._performance_cache:
            return 0.7  # Default neutral performance

        metrics = self._performance_cache[backend_type]

        # Simple performance score based on success rate
        # Could be enhanced with latency, quality, etc.
        success_rate = metrics.get('success_rate', 0.7)
        return success_rate

    def _update_performance_cache(
        self,
        backend_type: BackendType,
        success: bool,
        latency_ms: int
    ):
        """Update performance cache with execution results"""
        if backend_type not in self._performance_cache:
            self._performance_cache[backend_type] = {
                'total': 0,
                'successes': 0,
                'success_rate': 0.7
            }

        cache = self._performance_cache[backend_type]
        cache['total'] += 1
        if success:
            cache['successes'] += 1

        # Update rolling success rate
        cache['success_rate'] = cache['successes'] / cache['total']
