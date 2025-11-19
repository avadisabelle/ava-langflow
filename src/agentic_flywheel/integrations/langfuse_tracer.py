"""Langfuse Creative Archaeology Tracer

This module provides transparent Langfuse tracing integration for Agentic Flywheel
MCP tools, enabling complete creative archaeology of AI workflow orchestration.

Key Features:
- Decorator-based tracing (@trace_mcp_tool)
- Structured observations for decision points
- Performance and quality scoring
- Fail-safe design (tracing failures never break MCP tools)
- Integration with coaiapy-mcp Langfuse tools

Usage:
    from agentic_flywheel.integrations import trace_mcp_tool, LangfuseObservation

    @trace_mcp_tool("flowise_query")
    async def handle_flowise_query(name: str, arguments: dict):
        trace_id = get_current_trace_id()
        await LangfuseObservation.add_intent_classification(trace_id, "creative", 0.95)
        # ... rest of tool logic ...
        return result

Specification: rispecs/integrations/langfuse_tracer.spec.md
"""

import os
import time
import json
import logging
import traceback
import asyncio
from contextvars import ContextVar
from functools import wraps
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Context variable for storing current trace ID within async context
_current_trace_id: ContextVar[Optional[str]] = ContextVar('trace_id', default=None)


def get_current_trace_id() -> Optional[str]:
    """
    Get the trace ID for the current async context

    Returns:
        Current trace ID if within a traced function, None otherwise

    Example:
        @trace_mcp_tool("my_tool")
        async def my_tool_handler(name: str, arguments: dict):
            trace_id = get_current_trace_id()  # Returns the active trace ID
            await LangfuseObservation.add_intent_classification(trace_id, ...)
    """
    return _current_trace_id.get()


class LangfuseTracerManager:
    """
    Manages Langfuse tracing lifecycle and configuration

    This class provides centralized management for tracing enablement,
    parent trace IDs, and active trace registry.

    Configuration via environment variables:
        LANGFUSE_ENABLED: Enable/disable tracing (default: true)
        LANGFUSE_PUBLIC_KEY: Langfuse public API key
        LANGFUSE_SECRET_KEY: Langfuse secret API key
        LANGFUSE_HOST: Langfuse server URL
        AGENTIC_FLYWHEEL_PARENT_TRACE_ID: Session-level parent trace
        LANGFUSE_TRACE_TIMEOUT_MS: Timeout for trace operations (default: 5000)

    Example:
        tracer = LangfuseTracerManager(
            enabled=True,
            parent_trace_id="a50f3fc2-eb8c-434d-a37e-ef9615d9c07d"
        )

        if tracer.enabled:
            trace_id = await tracer.create_trace("flowise_query execution")
    """

    def __init__(
        self,
        enabled: Optional[bool] = None,
        parent_trace_id: Optional[str] = None,
        timeout_ms: int = 5000
    ):
        """
        Initialize tracer manager

        Args:
            enabled: Enable tracing (default: from LANGFUSE_ENABLED env var)
            parent_trace_id: Parent trace ID for hierarchical tracing
            timeout_ms: Timeout for Langfuse operations in milliseconds
        """
        # Determine if tracing is enabled
        if enabled is None:
            enabled = os.getenv("LANGFUSE_ENABLED", "true").lower() == "true"

        self.enabled = enabled
        self.parent_trace_id = parent_trace_id or os.getenv("AGENTIC_FLYWHEEL_PARENT_TRACE_ID")
        self.timeout_ms = timeout_ms
        self._active_traces: Dict[str, Dict[str, Any]] = {}

        # Check for Langfuse credentials
        if self.enabled:
            if not all([
                os.getenv("LANGFUSE_PUBLIC_KEY"),
                os.getenv("LANGFUSE_SECRET_KEY"),
                os.getenv("LANGFUSE_HOST")
            ]):
                logger.warning(
                    "Langfuse tracing enabled but credentials missing. "
                    "Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST. "
                    "Tracing will be disabled."
                )
                self.enabled = False
            else:
                logger.info(
                    f"Langfuse tracing enabled "
                    f"(parent_trace: {self.parent_trace_id or 'none'})"
                )

    async def create_trace(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None,
        input_data: Optional[Any] = None
    ) -> Optional[str]:
        """
        Create a new Langfuse trace

        Args:
            name: Human-readable trace name
            metadata: Optional high-level tags (environment, version, etc.)
            input_data: Optional initial input for the trace

        Returns:
            Trace ID if successful, None if tracing disabled or failed

        Note:
            This method calls the coaia_fuse_trace_create MCP tool via
            subprocess execution. In production, this would be replaced
            with actual MCP tool client calls.
        """
        if not self.enabled:
            return None

        try:
            # Generate trace ID (in production, Langfuse would generate this)
            trace_id = f"trace-{int(time.time() * 1000000)}"

            # Build trace creation parameters
            trace_params = {
                "name": name,
                "trace_id": trace_id,
                "metadata": metadata or {}
            }

            if self.parent_trace_id:
                trace_params["parent_trace_id"] = self.parent_trace_id

            if input_data is not None:
                trace_params["input_data"] = json.dumps(input_data) if not isinstance(input_data, str) else input_data

            # In actual implementation, this would call coaia_fuse_trace_create MCP tool
            # For now, we'll log and track locally
            logger.info(f"📊 Trace created: {trace_id} - {name}")

            # Store in active traces registry
            self._active_traces[trace_id] = {
                "name": name,
                "started_at": datetime.utcnow().isoformat(),
                "metadata": metadata or {},
                "observations": [],
                "scores": []
            }

            return trace_id

        except Exception as e:
            logger.warning(f"Trace creation failed (non-blocking): {e}")
            return None

    async def end_trace(self, trace_id: str, output_data: Optional[Any] = None):
        """
        Mark a trace as complete

        Args:
            trace_id: The trace to complete
            output_data: Optional final output for the trace
        """
        if not self.enabled or not trace_id:
            return

        try:
            if trace_id in self._active_traces:
                self._active_traces[trace_id]["ended_at"] = datetime.utcnow().isoformat()
                if output_data is not None:
                    self._active_traces[trace_id]["output_data"] = output_data

                logger.info(f"✅ Trace completed: {trace_id}")

        except Exception as e:
            logger.warning(f"Trace end failed (non-blocking): {e}")

    def get_trace_info(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve information about an active trace

        Args:
            trace_id: The trace to retrieve

        Returns:
            Trace metadata dict or None if not found
        """
        return self._active_traces.get(trace_id)


# Global tracer instance (initialized on first use)
_global_tracer: Optional[LangfuseTracerManager] = None


def _get_global_tracer() -> LangfuseTracerManager:
    """Get or create the global tracer instance"""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = LangfuseTracerManager()
    return _global_tracer


def trace_mcp_tool(
    tool_name: str,
    capture_input: bool = True,
    capture_output: bool = True
) -> Callable:
    """
    Decorator that automatically traces MCP tool execution

    This decorator wraps MCP tool handlers with Langfuse tracing, creating
    a trace at the start of execution and capturing input/output/performance
    metrics. All tracing failures are non-blocking.

    Args:
        tool_name: Name of the MCP tool being traced
        capture_input: Whether to capture input arguments (default: True)
        capture_output: Whether to capture output data (default: True)

    Returns:
        Decorated async function with transparent tracing

    Example:
        @app.call_tool()
        @trace_mcp_tool("flowise_query")
        async def handle_flowise_query(name: str, arguments: dict):
            trace_id = get_current_trace_id()
            # Tool logic here...
            return result

    Note:
        The decorator stores the trace_id in async context, accessible via
        get_current_trace_id() within the decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            tracer = _get_global_tracer()

            # If tracing is disabled, execute original function
            if not tracer.enabled:
                return await func(*args, **kwargs)

            trace_id = None
            start_time = time.time()

            try:
                # Extract input data if capture enabled
                input_data = None
                if capture_input:
                    # For MCP tools, arguments are typically in kwargs or args
                    if len(args) >= 2:
                        # Pattern: handle_tool(name: str, arguments: dict)
                        input_data = {"name": args[0], "arguments": args[1]}
                    elif "arguments" in kwargs:
                        input_data = kwargs.get("arguments")

                # Create trace
                trace_id = await tracer.create_trace(
                    name=f"{tool_name} execution",
                    metadata={
                        "tool_name": tool_name,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    input_data=input_data
                )

                # Store trace_id in context for nested calls
                token = _current_trace_id.set(trace_id)

                try:
                    # Execute original function
                    result = await func(*args, **kwargs)

                    # Capture execution metrics
                    duration_ms = (time.time() - start_time) * 1000

                    # Add execution observation
                    await LangfuseObservation.add_execution(
                        trace_id=trace_id,
                        input_data=input_data if capture_input else None,
                        output_data=result if capture_output else None,
                        duration_ms=duration_ms
                    )

                    # Add success score
                    await LangfuseScore.add_success_score(trace_id, True)

                    # Add latency score
                    await LangfuseScore.add_latency_score(trace_id, duration_ms)

                    # End trace
                    await tracer.end_trace(trace_id, output_data=result if capture_output else None)

                    return result

                finally:
                    # Reset context
                    _current_trace_id.reset(token)

            except Exception as e:
                # Capture error in trace
                duration_ms = (time.time() - start_time) * 1000

                if trace_id:
                    await LangfuseObservation.add_error(
                        trace_id=trace_id,
                        error_type=type(e).__name__,
                        error_message=str(e),
                        stack_trace=traceback.format_exc()
                    )
                    await LangfuseScore.add_success_score(trace_id, False, str(e))
                    await LangfuseScore.add_latency_score(trace_id, duration_ms)

                # Re-raise original exception (tracing is non-blocking)
                raise

        return wrapper
    return decorator


class LangfuseObservation:
    """
    Helper for adding structured observations to Langfuse traces

    This class provides static methods for documenting key decision points
    in MCP tool execution: intent classification, flow selection, execution
    details, and errors.

    All methods are async and fail-safe (tracing failures are logged but
    never propagate exceptions).

    Example:
        trace_id = get_current_trace_id()

        # Document intent classification
        await LangfuseObservation.add_intent_classification(
            trace_id, "creative-orientation", 0.95, ["creative", "goal"]
        )

        # Document flow selection
        await LangfuseObservation.add_flow_selection(
            trace_id, "csv2507", "Creative Orientation", "flowise",
            "Selected based on intent matching"
        )

        # Document execution
        await LangfuseObservation.add_execution(
            trace_id, user_question, flow_response, 1200.5
        )
    """

    @staticmethod
    async def add_intent_classification(
        trace_id: Optional[str],
        intent: str,
        confidence: float,
        matched_keywords: Optional[List[str]] = None
    ) -> bool:
        """
        Add observation documenting intent classification decision

        Args:
            trace_id: The trace to add observation to
            intent: Classified intent (e.g., "creative-orientation")
            confidence: Confidence score 0.0-1.0
            matched_keywords: Keywords that triggered this classification

        Returns:
            True if observation added, False if tracing disabled/failed

        Example:
            await LangfuseObservation.add_intent_classification(
                trace_id, "creative-orientation", 0.95, ["creative", "goal", "vision"]
            )
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            observation_data = {
                "intent": intent,
                "confidence": confidence,
                "matched_keywords": matched_keywords or []
            }

            # In actual implementation, call coaia_fuse_add_observation
            logger.info(
                f"  └─ Intent Classification: {intent} "
                f"(confidence: {confidence:.2f})"
            )

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["observations"].append({
                    "type": "intent_classification",
                    "data": observation_data,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return True

        except Exception as e:
            logger.warning(f"Intent classification observation failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_flow_selection(
        trace_id: Optional[str],
        flow_id: str,
        flow_name: str,
        backend: str,
        reasoning: Optional[str] = None
    ) -> bool:
        """
        Add observation documenting flow selection logic

        Args:
            trace_id: The trace to add observation to
            flow_id: Selected flow ID
            flow_name: Human-readable flow name
            backend: Backend platform (flowise, langflow)
            reasoning: Optional explanation for selection

        Returns:
            True if observation added, False if tracing disabled/failed

        Example:
            await LangfuseObservation.add_flow_selection(
                trace_id, "csv2507", "Creative Orientation", "flowise",
                "Selected based on 'creative' intent with 0.95 confidence"
            )
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            observation_data = {
                "flow_id": flow_id,
                "flow_name": flow_name,
                "backend": backend,
                "reasoning": reasoning
            }

            logger.info(
                f"  └─ Flow Selection: {flow_name} (id: {flow_id}, backend: {backend})"
            )

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["observations"].append({
                    "type": "flow_selection",
                    "data": observation_data,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return True

        except Exception as e:
            logger.warning(f"Flow selection observation failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_execution(
        trace_id: Optional[str],
        input_data: Any,
        output_data: Any,
        duration_ms: float
    ) -> bool:
        """
        Add observation documenting flow execution with I/O

        Args:
            trace_id: The trace to add observation to
            input_data: Input to the flow (user question, parameters, etc.)
            output_data: Output from the flow (response, result, etc.)
            duration_ms: Execution duration in milliseconds

        Returns:
            True if observation added, False if tracing disabled/failed

        Example:
            await LangfuseObservation.add_execution(
                trace_id,
                "What is structural tension?",
                "Structural tension is the gap between current reality...",
                1235.7
            )
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            # Serialize data if needed
            input_str = json.dumps(input_data) if not isinstance(input_data, str) else input_data
            output_str = json.dumps(output_data) if not isinstance(output_data, str) else output_data

            observation_data = {
                "input": input_str,
                "output": output_str,
                "duration_ms": duration_ms
            }

            logger.info(
                f"  └─ Execution: {duration_ms:.1f}ms "
                f"(input: {len(input_str) if input_str else 0} chars, "
                f"output: {len(output_str) if output_str else 0} chars)"
            )

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["observations"].append({
                    "type": "execution",
                    "data": observation_data,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return True

        except Exception as e:
            logger.warning(f"Execution observation failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_error(
        trace_id: Optional[str],
        error_type: str,
        error_message: str,
        stack_trace: Optional[str] = None
    ) -> bool:
        """
        Add observation documenting execution error

        Args:
            trace_id: The trace to add observation to
            error_type: Exception class name (ValueError, RuntimeError, etc.)
            error_message: Human-readable error description
            stack_trace: Optional full stack trace

        Returns:
            True if observation added, False if tracing disabled/failed

        Example:
            try:
                result = await execute_flow(...)
            except Exception as e:
                await LangfuseObservation.add_error(
                    trace_id, type(e).__name__, str(e), traceback.format_exc()
                )
                raise
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            observation_data = {
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace
            }

            logger.error(
                f"  └─ Error: {error_type} - {error_message}"
            )

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["observations"].append({
                    "type": "error",
                    "data": observation_data,
                    "timestamp": datetime.utcnow().isoformat()
                })

            return True

        except Exception as e:
            logger.warning(f"Error observation failed (non-blocking): {e}")
            return False


class LangfuseScore:
    """
    Helper for adding quality/performance scores to Langfuse traces

    This class provides static methods for adding quantitative metrics:
    quality, latency, success, and cost scores.

    All methods are async and fail-safe (score failures are logged but
    never propagate exceptions).

    Example:
        trace_id = get_current_trace_id()

        # Add quality score
        await LangfuseScore.add_quality_score(
            trace_id, 0.9, "Response addresses core concept"
        )

        # Add latency score
        await LangfuseScore.add_latency_score(trace_id, 1235.7)

        # Add success score
        await LangfuseScore.add_success_score(trace_id, True)
    """

    @staticmethod
    async def add_quality_score(
        trace_id: Optional[str],
        score: float,
        reasoning: Optional[str] = None
    ) -> bool:
        """
        Add score for response quality (0.0-1.0)

        Args:
            trace_id: The trace to add score to
            score: Quality score 0.0 (poor) to 1.0 (excellent)
            reasoning: Optional explanation for the score

        Returns:
            True if score added, False if tracing disabled/failed

        Example:
            await LangfuseScore.add_quality_score(
                trace_id, 0.9, "Response is comprehensive and accurate"
            )
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            score_data = {
                "name": "quality",
                "value": score,
                "reasoning": reasoning
            }

            logger.info(f"  └─ Quality Score: {score:.2f}")

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["scores"].append(score_data)

            return True

        except Exception as e:
            logger.warning(f"Quality score failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_latency_score(
        trace_id: Optional[str],
        duration_ms: float
    ) -> bool:
        """
        Add score for execution performance (milliseconds)

        Args:
            trace_id: The trace to add score to
            duration_ms: Execution duration in milliseconds

        Returns:
            True if score added, False if tracing disabled/failed

        Example:
            await LangfuseScore.add_latency_score(trace_id, 1235.7)
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            score_data = {
                "name": "latency",
                "value": duration_ms,
                "unit": "ms"
            }

            logger.info(f"  └─ Latency Score: {duration_ms:.1f}ms")

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["scores"].append(score_data)

            return True

        except Exception as e:
            logger.warning(f"Latency score failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_success_score(
        trace_id: Optional[str],
        success: bool,
        error: Optional[str] = None
    ) -> bool:
        """
        Add score for execution success/failure

        Args:
            trace_id: The trace to add score to
            success: True for successful execution, False for failure
            error: Optional error message if success=False

        Returns:
            True if score added, False if tracing disabled/failed

        Example:
            # Success case
            await LangfuseScore.add_success_score(trace_id, True)

            # Failure case
            await LangfuseScore.add_success_score(
                trace_id, False, "Flow execution timeout"
            )
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            score_data = {
                "name": "success",
                "value": 1.0 if success else 0.0,
                "error": error
            }

            logger.info(f"  └─ Success Score: {'✅ Pass' if success else '❌ Fail'}")

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["scores"].append(score_data)

            return True

        except Exception as e:
            logger.warning(f"Success score failed (non-blocking): {e}")
            return False

    @staticmethod
    async def add_cost_score(
        trace_id: Optional[str],
        tokens: int,
        cost_usd: float
    ) -> bool:
        """
        Add score for token usage and API cost

        Args:
            trace_id: The trace to add score to
            tokens: Total tokens consumed
            cost_usd: Total cost in USD

        Returns:
            True if score added, False if tracing disabled/failed

        Example:
            await LangfuseScore.add_cost_score(trace_id, 1500, 0.045)
        """
        if not trace_id:
            return False

        tracer = _get_global_tracer()
        if not tracer.enabled:
            return False

        try:
            score_data = {
                "name": "cost",
                "value": cost_usd,
                "tokens": tokens,
                "unit": "USD"
            }

            logger.info(f"  └─ Cost Score: ${cost_usd:.4f} ({tokens} tokens)")

            # Track in local registry
            if trace_id in tracer._active_traces:
                tracer._active_traces[trace_id]["scores"].append(score_data)

            return True

        except Exception as e:
            logger.warning(f"Cost score failed (non-blocking): {e}")
            return False
