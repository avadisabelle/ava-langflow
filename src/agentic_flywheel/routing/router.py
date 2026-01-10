"""Universal Query Router

Intelligent backend selection based on query intent, backend health,
and historical performance metrics.
"""

import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from datetime import datetime

try:
    from ..backends.base import FlowBackend, UniversalFlow, BackendType
except ImportError:
    from agentic_flywheel.backends.base import FlowBackend, UniversalFlow, BackendType

logger = logging.getLogger(__name__)


@dataclass
class BackendScore:
    """Score components for a single backend"""
    backend: FlowBackend
    match_score: float = 0.0
    health_score: float = 0.0
    performance_score: float = 0.0
    composite_score: float = 0.0
    matching_flows: List[UniversalFlow] = field(default_factory=list)
    selected_flow: Optional[UniversalFlow] = None


@dataclass
class RoutingDecision:
    """Complete routing decision with metadata"""
    backend: FlowBackend
    flow: UniversalFlow
    score: float
    intent: str
    method: str  # 'intelligent' or 'explicit'
    all_scores: List[BackendScore]
    fallback_available: bool


class PerformanceTracker:
    """Track backend performance history for routing decisions"""

    def __init__(self, max_history: int = 100):
        """
        Initialize performance tracker

        Args:
            max_history: Maximum number of records per backend:intent pair
        """
        self.max_history = max_history
        # key: "backend_type:intent" -> deque of performance records
        self._history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))

    def record(
        self,
        backend: str,
        intent: str,
        latency_ms: float,
        success: bool,
        metadata: Optional[Dict] = None
    ):
        """
        Record backend performance

        Args:
            backend: Backend type (e.g., 'flowise', 'langflow')
            intent: Query intent classification
            latency_ms: Execution latency in milliseconds
            success: Whether execution succeeded
            metadata: Optional additional metadata
        """
        key = f"{backend}:{intent}"
        record = {
            "timestamp": time.time(),
            "latency_ms": latency_ms,
            "success": success,
            "metadata": metadata or {}
        }
        self._history[key].append(record)
        logger.debug(f"Recorded performance: {backend}:{intent} - {latency_ms}ms ({'success' if success else 'failure'})")

    def get_score(self, backend: str, intent: str) -> float:
        """
        Calculate performance score for backend+intent pair

        Args:
            backend: Backend type
            intent: Query intent

        Returns:
            Score from 0.0 (poor) to 1.0 (excellent)
        """
        key = f"{backend}:{intent}"
        history = self._history.get(key, [])

        if not history:
            return 0.5  # Neutral score if no history

        # Consider last 10 executions for recency
        recent = list(history)[-10:]

        # Calculate success rate
        success_count = sum(1 for r in recent if r["success"])
        success_rate = success_count / len(recent)

        # Calculate average latency (normalize to 0-1 scale)
        avg_latency = sum(r["latency_ms"] for r in recent) / len(recent)
        # 5000ms = 0.0 score, 0ms = 1.0 score
        latency_score = max(0.0, 1.0 - (avg_latency / 5000))

        # Weighted combination (success matters more)
        return (success_rate * 0.7) + (latency_score * 0.3)


class UniversalRouter:
    """
    Intelligent router for universal query execution

    Selects optimal backend based on:
    - Flow match quality (50%)
    - Backend health (30%)
    - Historical performance (20%)
    """

    # Scoring weights
    WEIGHT_MATCH = 0.5
    WEIGHT_HEALTH = 0.3
    WEIGHT_PERFORMANCE = 0.2

    def __init__(self, performance_tracker: Optional[PerformanceTracker] = None):
        """
        Initialize router

        Args:
            performance_tracker: Performance tracking instance (creates new if None)
        """
        self.performance_tracker = performance_tracker or PerformanceTracker()
        self._flow_cache: Dict[str, Tuple[float, List[UniversalFlow]]] = {}
        self._cache_ttl = 60.0  # Cache TTL in seconds

    async def select_backend(
        self,
        backends: List[FlowBackend],
        question: str,
        intent: Optional[str] = None,
        backend_override: Optional[str] = None
    ) -> RoutingDecision:
        """
        Select optimal backend for query execution

        Args:
            backends: Available backends to choose from
            question: User question
            intent: Optional intent override (auto-classified if None)
            backend_override: Optional explicit backend selection

        Returns:
            RoutingDecision with selected backend and metadata

        Raises:
            ValueError: If no suitable backend found
        """
        if not backends:
            raise ValueError("No backends available for routing")

        # Classify intent if not provided
        if not intent:
            intent = classify_intent(question)

        # Handle explicit backend override
        if backend_override and backend_override != "auto":
            backend = self._find_backend_by_type(backends, backend_override)
            if not backend:
                raise ValueError(f"Backend '{backend_override}' not found in available backends")

            # Get flows for validation
            flows = await self._get_flows_cached(backend)
            matching_flows = [f for f in flows if intent in f.intent_keywords]

            if not matching_flows:
                logger.warning(f"Explicit backend '{backend_override}' has no flows for intent '{intent}'")
                # Still allow it, use first available flow
                selected_flow = flows[0] if flows else None
            else:
                selected_flow = matching_flows[0]

            if not selected_flow:
                raise ValueError(f"Backend '{backend_override}' has no available flows")

            return RoutingDecision(
                backend=backend,
                flow=selected_flow,
                score=1.0,
                intent=intent,
                method="explicit",
                all_scores=[],
                fallback_available=len(backends) > 1
            )

        # Intelligent routing
        scores = await self._score_all_backends(backends, intent)

        if not scores:
            raise ValueError(f"No backends have flows matching intent '{intent}'")

        # Sort by composite score (highest first)
        scores.sort(key=lambda x: x.composite_score, reverse=True)
        best = scores[0]

        if best.composite_score == 0.0:
            raise ValueError(f"All backends scored 0.0 for intent '{intent}' (no matching flows)")

        return RoutingDecision(
            backend=best.backend,
            flow=best.selected_flow,
            score=best.composite_score,
            intent=intent,
            method="intelligent",
            all_scores=scores,
            fallback_available=len(scores) > 1
        )

    async def _score_all_backends(
        self,
        backends: List[FlowBackend],
        intent: str
    ) -> List[BackendScore]:
        """
        Score all backends for the given intent

        Args:
            backends: Backends to score
            intent: Query intent

        Returns:
            List of BackendScore objects
        """
        scores = []

        for backend in backends:
            try:
                score = await self._score_backend(backend, intent)
                scores.append(score)
            except Exception as e:
                logger.warning(f"Failed to score backend {backend.backend_type.value}: {e}")
                # Create zero score for failed backend
                scores.append(BackendScore(
                    backend=backend,
                    match_score=0.0,
                    health_score=0.0,
                    performance_score=0.0,
                    composite_score=0.0
                ))

        return scores

    async def _score_backend(self, backend: FlowBackend, intent: str) -> BackendScore:
        """
        Calculate composite score for a single backend

        Args:
            backend: Backend to score
            intent: Query intent

        Returns:
            BackendScore object with all scoring components
        """
        # Get flows (with caching)
        flows = await self._get_flows_cached(backend)

        # Match score
        match_score, matching_flows, selected_flow = self._calculate_match_score(flows, intent)

        # Health score
        health_score = await self._calculate_health_score(backend)

        # Performance score
        perf_score = self._calculate_performance_score(backend.backend_type.value, intent)

        # Composite score
        composite = (
            (match_score * self.WEIGHT_MATCH) +
            (health_score * self.WEIGHT_HEALTH) +
            (perf_score * self.WEIGHT_PERFORMANCE)
        )

        return BackendScore(
            backend=backend,
            match_score=match_score,
            health_score=health_score,
            performance_score=perf_score,
            composite_score=composite,
            matching_flows=matching_flows,
            selected_flow=selected_flow
        )

    def _calculate_match_score(
        self,
        flows: List[UniversalFlow],
        intent: str
    ) -> Tuple[float, List[UniversalFlow], Optional[UniversalFlow]]:
        """
        Calculate flow match score for intent

        Args:
            flows: Available flows
            intent: Target intent

        Returns:
            Tuple of (score, matching_flows, best_flow)
            Score: 0.0 (no match) to 1.0 (perfect match)
        """
        if not flows:
            return (0.0, [], None)

        # Find flows with matching intent keywords
        matching_flows = [f for f in flows if intent in f.intent_keywords]

        if not matching_flows:
            return (0.0, [], None)

        # Select best flow (most specific = most keywords)
        best_flow = max(matching_flows, key=lambda f: len(f.intent_keywords))

        # Score based on keyword specificity
        # More keywords = more specialized = higher score
        specificity = min(len(best_flow.intent_keywords) / 10, 1.0)

        # Base score for having a match + specificity bonus
        score = 0.5 + (specificity * 0.5)  # Range: 0.5 to 1.0

        return (score, matching_flows, best_flow)

    async def _calculate_health_score(self, backend: FlowBackend) -> float:
        """
        Calculate backend health score

        Args:
            backend: Backend to check

        Returns:
            1.0 if healthy, 0.0 if unhealthy
        """
        try:
            is_healthy = await backend.health_check()
            return 1.0 if is_healthy else 0.0
        except Exception as e:
            logger.warning(f"Health check failed for {backend.backend_type.value}: {e}")
            return 0.0

    def _calculate_performance_score(self, backend_type: str, intent: str) -> float:
        """
        Calculate performance score from historical data

        Args:
            backend_type: Backend type string (e.g., 'flowise')
            intent: Query intent

        Returns:
            Score from 0.0 (poor) to 1.0 (excellent)
        """
        return self.performance_tracker.get_score(backend_type, intent)

    async def _get_flows_cached(self, backend: FlowBackend) -> List[UniversalFlow]:
        """
        Get backend flows with caching

        Args:
            backend: Backend to query

        Returns:
            List of flows
        """
        cache_key = backend.backend_type.value
        cached = self._flow_cache.get(cache_key)

        # Check cache validity
        if cached:
            timestamp, flows = cached
            if (time.time() - timestamp) < self._cache_ttl:
                return flows

        # Cache miss or expired - fetch fresh
        try:
            flows = await backend.discover_flows()
            self._flow_cache[cache_key] = (time.time(), flows)
            return flows
        except Exception as e:
            logger.error(f"Failed to discover flows for {backend.backend_type.value}: {e}")
            return []

    def _find_backend_by_type(
        self,
        backends: List[FlowBackend],
        backend_type: str
    ) -> Optional[FlowBackend]:
        """
        Find backend by type string

        Args:
            backends: Available backends
            backend_type: Type string ('flowise', 'langflow', etc.)

        Returns:
            Matching backend or None
        """
        for backend in backends:
            if backend.backend_type.value.lower() == backend_type.lower():
                return backend
        return None


# Intent classification utilities

def classify_intent(question: str) -> str:
    """
    Classify query intent from question text

    Args:
        question: User question

    Returns:
        Intent classification string

    Note:
        This is a simple keyword-based classifier.
        Can be replaced with LLM-based classification for better accuracy.
    """
    question_lower = question.lower()

    # Intent patterns (order matters - more specific first)
    patterns = {
        "creative-orientation": [
            "structural tension", "desired outcome", "creative", "vision",
            "goal", "dream", "aspire", "create", "want to create"
        ],
        "technical-analysis": [
            "code", "debug", "error", "implement", "function", "class",
            "programming", "technical", "analyze code", "fix bug"
        ],
        "document-qa": [
            "document", "file", "search", "find", "lookup", "what does",
            "where is", "information about", "explain"
        ],
        "code-review": [
            "review", "refactor", "improve", "optimize", "best practice",
            "code quality", "performance"
        ]
    }

    # Check each pattern
    for intent, keywords in patterns.items():
        for keyword in keywords:
            if keyword in question_lower:
                return intent

    # Default fallback
    return "general"


def extract_keywords(question: str) -> List[str]:
    """
    Extract relevant keywords from question

    Args:
        question: User question

    Returns:
        List of extracted keywords
    """
    # Simple word extraction (can be enhanced with NLP)
    question_lower = question.lower()

    # Remove common words
    stop_words = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                  "what", "how", "when", "where", "why", "who", "which"}

    # Split into words
    words = question_lower.split()

    # Filter stop words and short words
    keywords = [w for w in words if w not in stop_words and len(w) > 3]

    return keywords[:10]  # Limit to 10 keywords
