"""Universal Query MCP Tool

Provides intelligent cross-backend query execution with automatic routing.
"""

import time
import logging
import traceback
from typing import Any, Dict, List, Optional

try:
    from mcp import types
except ImportError:
    types = None  # MCP not available in test environment

try:
    from ..backends.registry import BackendRegistry
    from ..backends.base import BackendType
    from ..routing import UniversalRouter, classify_intent, extract_keywords
except ImportError:
    from agentic_flywheel.backends.registry import BackendRegistry
    from agentic_flywheel.backends.base import BackendType
    from agentic_flywheel.routing import UniversalRouter, classify_intent, extract_keywords

# Optional integrations
try:
    from ..integrations import (
        trace_mcp_tool,
        get_current_trace_id,
        LangfuseObservation,
        LangfuseScore
    )
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False

logger = logging.getLogger(__name__)

# Global router instance (singleton pattern)
_global_router: Optional[UniversalRouter] = None


def get_router() -> UniversalRouter:
    """Get or create global router instance"""
    global _global_router
    if _global_router is None:
        _global_router = UniversalRouter()
    return _global_router


async def handle_universal_query(name: str, arguments: dict) -> List:
    """
    Universal query handler with intelligent backend routing

    Args:
        name: Tool name (should be 'universal_query')
        arguments: Query arguments containing:
            - question (required): User question
            - intent (optional): Intent override
            - backend (optional): Backend selection ('auto', 'flowise', 'langflow')
            - session_id (optional): Session ID for continuity
            - parameters (optional): Flow-specific parameters
            - include_routing_metadata (optional): Include routing info in response

    Returns:
        List of MCP TextContent objects

    Example:
        result = await handle_universal_query("universal_query", {
            "question": "What is structural tension?",
            "backend": "auto",
            "include_routing_metadata": True
        })
    """
    # Extract arguments
    question = arguments.get("question")
    if not question:
        return [_create_text_content("❌ Error: 'question' parameter is required")]

    backend_pref = arguments.get("backend", "auto")
    session_id = arguments.get("session_id")
    intent_override = arguments.get("intent")
    parameters = arguments.get("parameters", {})
    include_metadata = arguments.get("include_routing_metadata", True)

    # Get trace ID if tracing available
    trace_id = None
    if TRACING_AVAILABLE:
        trace_id = get_current_trace_id()

    # Initialize backend registry
    try:
        registry = BackendRegistry()
        await registry.discover_backends()
    except Exception as e:
        logger.error(f"Failed to initialize backend registry: {e}")
        return [_create_text_content(
            f"❌ Error: Backend system initialization failed.\n\nDetails: {str(e)}"
        )]

    # Get healthy backends
    try:
        available_backends = [b for b in registry.get_all_backends() if await b.health_check()]
    except Exception as e:
        logger.error(f"Failed to get backends: {e}")
        return [_create_text_content(f"❌ Error: Cannot retrieve available backends.\n\nDetails: {str(e)}")]

    if not available_backends:
        return [_create_text_content(
            "❌ Error: No healthy backends available.\n\n"
            "All AI workflow platforms (Flowise, Langflow) are currently offline or unreachable."
        )]

    # Intent classification
    intent = intent_override if intent_override else classify_intent(question)

    if TRACING_AVAILABLE and trace_id:
        await LangfuseObservation.add_intent_classification(
            trace_id, intent, 0.95, extract_keywords(question)
        )

    # Backend selection via router
    router = get_router()

    try:
        routing_decision = await router.select_backend(
            backends=available_backends,
            question=question,
            intent=intent,
            backend_override=backend_pref
        )
    except ValueError as e:
        return [_create_text_content(
            f"❌ Error: Backend selection failed.\n\n{str(e)}\n\n"
            f"Try:\n"
            f"- Rephrasing your question\n"
            f"- Specifying a different backend explicitly\n"
            f"- Checking backend availability"
        )]
    except Exception as e:
        logger.error(f"Routing error: {e}\n{traceback.format_exc()}")
        return [_create_text_content(f"❌ Error: Routing failed unexpectedly.\n\nDetails: {str(e)}")]

    backend = routing_decision.backend
    selected_flow = routing_decision.flow

    if TRACING_AVAILABLE and trace_id:
        await LangfuseObservation.add_flow_selection(
            trace_id,
            selected_flow.backend_specific_id,
            selected_flow.name,
            backend.backend_type.value,
            f"Selected via {routing_decision.method} routing (score: {routing_decision.score:.2f})"
        )

    # Execute flow
    start_time = time.time()

    try:
        result = await backend.execute_flow(
            flow_id=selected_flow.backend_specific_id,
            input_data={"question": question},
            parameters=parameters,
            session_id=session_id
        )

        duration_ms = (time.time() - start_time) * 1000

        if TRACING_AVAILABLE and trace_id:
            await LangfuseObservation.add_execution(
                trace_id,
                {"question": question, "parameters": parameters},
                result,
                duration_ms
            )

            await LangfuseScore.add_latency_score(trace_id, duration_ms)
            await LangfuseScore.add_success_score(trace_id, True)

        # Record performance for future routing
        router.performance_tracker.record(
            backend=backend.backend_type.value,
            intent=intent,
            latency_ms=duration_ms,
            success=True
        )

        # Format response
        response_text = format_universal_response(
            result=result,
            backend=backend.backend_type.value,
            flow_name=selected_flow.name,
            routing_decision=routing_decision,
            duration_ms=duration_ms,
            include_metadata=include_metadata
        )

        return [_create_text_content(response_text)]

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000

        logger.error(f"Flow execution error: {e}\n{traceback.format_exc()}")

        if TRACING_AVAILABLE and trace_id:
            await LangfuseObservation.add_error(
                trace_id,
                type(e).__name__,
                str(e),
                traceback.format_exc()
            )
            await LangfuseScore.add_success_score(trace_id, False, str(e))

        # Record failure
        router.performance_tracker.record(
            backend=backend.backend_type.value,
            intent=intent,
            latency_ms=duration_ms,
            success=False
        )

        # Attempt fallback if available
        if routing_decision.fallback_available and len(routing_decision.all_scores) > 1:
            logger.info(f"Attempting fallback from {backend.backend_type.value}")

            # Get next best backend
            remaining_scores = [s for s in routing_decision.all_scores
                              if s.backend != backend and s.composite_score > 0.0]

            if remaining_scores:
                fallback_score = remaining_scores[0]
                fallback_backend = fallback_score.backend
                fallback_flow = fallback_score.selected_flow

                try:
                    result = await fallback_backend.execute_flow(
                        flow_id=fallback_flow.backend_specific_id,
                        input_data={"question": question},
                        parameters=parameters,
                        session_id=session_id
                    )

                    fallback_duration_ms = (time.time() - start_time) * 1000

                    # Record fallback success
                    router.performance_tracker.record(
                        backend=fallback_backend.backend_type.value,
                        intent=intent,
                        latency_ms=fallback_duration_ms - duration_ms,
                        success=True
                    )

                    response_text = format_universal_response(
                        result=result,
                        backend=fallback_backend.backend_type.value,
                        flow_name=fallback_flow.name,
                        routing_decision=routing_decision,
                        duration_ms=fallback_duration_ms,
                        include_metadata=include_metadata,
                        is_fallback=True,
                        primary_backend=backend.backend_type.value,
                        primary_error=str(e)
                    )

                    return [_create_text_content(response_text)]

                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {fallback_error}")
                    # Continue to error response below

        # All attempts failed
        return [_create_text_content(
            f"❌ Error: Query execution failed on {backend.backend_type.value}.\n\n"
            f"Error: {str(e)}\n\n"
            f"{'No fallback backends available.' if not routing_decision.fallback_available else 'Fallback attempts also failed.'}"
        )]


def format_universal_response(
    result: Dict[str, Any],
    backend: str,
    flow_name: str,
    routing_decision: Any,
    duration_ms: float,
    include_metadata: bool = True,
    is_fallback: bool = False,
    primary_backend: Optional[str] = None,
    primary_error: Optional[str] = None
) -> str:
    """
    Format universal query response with optional metadata

    Args:
        result: Flow execution result
        backend: Backend that handled query
        flow_name: Flow name used
        routing_decision: RoutingDecision object
        duration_ms: Execution duration
        include_metadata: Whether to include routing metadata
        is_fallback: Whether this was a fallback execution
        primary_backend: Primary backend if fallback used
        primary_error: Primary error if fallback used

    Returns:
        Formatted response string
    """
    # Extract main result text
    if isinstance(result, dict):
        response_text = result.get("result", result.get("text", str(result)))
    else:
        response_text = str(result)

    if not include_metadata:
        return response_text

    # Build metadata section
    metadata_lines = [
        "",
        "---",
        "**Routing Info**:"
    ]

    if is_fallback and primary_backend:
        metadata_lines.extend([
            f"- ⚠️ Fallback: {primary_backend} → {backend}",
            f"- Primary Error: {primary_error}",
            f"- Fallback Flow: {flow_name}"
        ])
    else:
        metadata_lines.extend([
            f"- Backend: {backend}",
            f"- Flow: {flow_name}"
        ])

    metadata_lines.extend([
        f"- Selection: {routing_decision.method.title()} (score: {routing_decision.score:.2f})",
        f"- Execution: {duration_ms:.0f}ms",
        f"- Intent: {routing_decision.intent}"
    ])

    # Add top backend scores if available
    if hasattr(routing_decision, 'all_scores') and routing_decision.all_scores:
        metadata_lines.append("")
        metadata_lines.append("**Backend Scores**:")
        for score in routing_decision.all_scores[:3]:  # Top 3
            metadata_lines.append(
                f"- {score.backend.backend_type.value}: {score.composite_score:.2f} "
                f"(match: {score.match_score:.2f}, health: {score.health_score:.2f}, perf: {score.performance_score:.2f})"
            )

    metadata = "\n".join(metadata_lines)

    return f"{response_text}\n{metadata}"


def _create_text_content(text: str):
    """
    Create MCP TextContent object or plain dict if MCP not available

    Args:
        text: Response text

    Returns:
        TextContent object or dict
    """
    if types:
        return types.TextContent(type="text", text=text)
    else:
        # Fallback for testing without MCP
        return {"type": "text", "text": text}
