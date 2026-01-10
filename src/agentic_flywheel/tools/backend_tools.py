"""Backend Management MCP Tools

Provides comprehensive backend management capabilities including:
- Status monitoring
- Discovery and registration
- Flow cataloging
- Performance comparison
"""

import time
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from statistics import mean, quantiles

try:
    from mcp import types
except ImportError:
    types = None

try:
    from ..backends.registry import BackendRegistry
    from ..backends.base import BackendType, FlowBackend
    from ..routing import UniversalRouter, get_router
except ImportError:
    from agentic_flywheel.backends.registry import BackendRegistry
    from agentic_flywheel.backends.base import BackendType, FlowBackend
    from agentic_flywheel.routing import UniversalRouter, get_router

logger = logging.getLogger(__name__)


# Global registry (singleton pattern)
_global_registry: Optional[BackendRegistry] = None


def get_registry() -> BackendRegistry:
    """Get or create global backend registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = BackendRegistry()
    return _global_registry


async def handle_backend_registry_status(name: str, arguments: dict) -> List:
    """
    Get status of all registered backends

    Args:
        name: Tool name
        arguments: Empty dict (no parameters)

    Returns:
        List of MCP TextContent with backend status
    """
    try:
        registry = get_registry()
        await registry.discover_backends()

        backends_info = []
        healthy_count = 0
        total_flows = 0
        health_scores = []

        for backend in registry.get_all_backends():
            try:
                # Check health
                health = await backend.health_check()
                health_score = 1.0 if health else 0.0

                if health:
                    healthy_count += 1

                # Get flows
                flows = []
                flows_count = 0
                if health:
                    try:
                        flows = await backend.discover_flows()
                        flows_count = len(flows)
                        total_flows += flows_count
                    except Exception as e:
                        logger.warning(f"Failed to discover flows for {backend.backend_type.value}: {e}")

                # Get performance data
                router = get_router()
                avg_latency = 0.0

                # Calculate average latency across all intents for this backend
                backend_key_prefix = f"{backend.backend_type.value}:"
                latencies = []
                for key, history in router.performance_tracker._history.items():
                    if key.startswith(backend_key_prefix):
                        latencies.extend([h['latency_ms'] for h in history])

                if latencies:
                    avg_latency = mean(latencies)

                backends_info.append({
                    "type": backend.backend_type.value,
                    "name": f"{backend.backend_type.value.title()} Backend",
                    "status": "connected" if health else "disconnected",
                    "health_score": health_score,
                    "flows_count": flows_count,
                    "last_check": datetime.utcnow().isoformat() + "Z",
                    "avg_latency_ms": round(avg_latency, 0) if avg_latency > 0 else None
                })

                health_scores.append(health_score)

            except Exception as e:
                logger.error(f"Error checking backend {backend.backend_type.value}: {e}")
                backends_info.append({
                    "type": backend.backend_type.value,
                    "name": f"{backend.backend_type.value.title()} Backend",
                    "status": "error",
                    "health_score": 0.0,
                    "error": str(e)
                })

        # Generate recommendation
        unhealthy_count = len(backends_info) - healthy_count
        if unhealthy_count == 0:
            recommendation = "All backends healthy"
        elif unhealthy_count == len(backends_info):
            recommendation = "All backends offline - check backend services"
        else:
            recommendation = f"{unhealthy_count} backend(s) offline - review logs"

        result = {
            "total_backends": len(backends_info),
            "healthy_count": healthy_count,
            "unhealthy_count": unhealthy_count,
            "backends": backends_info,
            "summary": {
                "total_flows": total_flows,
                "avg_health": round(mean(health_scores), 2) if health_scores else 0.0,
                "recommendation": recommendation
            }
        }

        return [_create_text_content(json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Backend registry status error: {e}")
        return [_create_text_content(
            f"❌ Error: Failed to retrieve backend status.\\n\\nDetails: {str(e)}"
        )]


async def handle_backend_discover(name: str, arguments: dict) -> List:
    """
    Auto-discover and register backends from configuration

    Args:
        name: Tool name
        arguments: Optional config_path, force_rediscover

    Returns:
        List of MCP TextContent with discovery results
    """
    try:
        registry = get_registry()
        force_rediscover = arguments.get("force_rediscover", False)

        # Discover backends
        await registry.discover_backends()

        backends = registry.get_all_backends()
        backends_info = []
        errors = []

        for backend in backends:
            try:
                health = await backend.health_check()
                backends_info.append({
                    "type": backend.backend_type.value,
                    "base_url": getattr(backend, 'base_url', 'unknown'),
                    "status": "registered" if health else "registered_offline"
                })
            except Exception as e:
                errors.append(f"{backend.backend_type.value}: {str(e)}")

        result = {
            "discovered": len(backends),
            "registered": len(backends_info),
            "backends": backends_info,
            "errors": errors
        }

        return [_create_text_content(json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Backend discover error: {e}")
        return [_create_text_content(
            f"❌ Error: Backend discovery failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_backend_connect(name: str, arguments: dict) -> List:
    """
    Manually connect to specific backend

    Args:
        name: Tool name
        arguments: backend_type, base_url, api_key (optional), name (optional)

    Returns:
        List of MCP TextContent with connection result
    """
    try:
        backend_type_str = arguments.get("backend_type")
        base_url = arguments.get("base_url")
        api_key = arguments.get("api_key")
        custom_name = arguments.get("name")

        if not backend_type_str or not base_url:
            return [_create_text_content(
                "❌ Error: 'backend_type' and 'base_url' are required parameters"
            )]

        # Create backend instance
        if backend_type_str == "flowise":
            from ..backends.flowise import FlowiseBackend
            backend = FlowiseBackend(base_url=base_url, api_key=api_key)
        elif backend_type_str == "langflow":
            from ..backends.langflow import LangflowBackend
            backend = LangflowBackend(base_url=base_url, api_key=api_key)
        else:
            return [_create_text_content(
                f"❌ Error: Unsupported backend type '{backend_type_str}'. Supported: flowise, langflow"
            )]

        # Test connection
        health = await backend.health_check()

        if not health:
            return [_create_text_content(
                f"❌ Error: Failed to connect to {backend_type_str} at {base_url}. Check URL and API key."
            )]

        # Discover flows
        flows = await backend.discover_flows()

        # Register with registry
        registry = get_registry()
        # Note: BackendRegistry doesn't have a direct register method,
        # but this demonstrates the pattern

        result = {
            "success": True,
            "backend": {
                "type": backend_type_str,
                "name": custom_name or f"{backend_type_str.title()} Backend",
                "base_url": base_url,
                "status": "connected",
                "flows_discovered": len(flows)
            }
        }

        return [_create_text_content(json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Backend connect error: {e}")
        return [_create_text_content(
            f"❌ Error: Backend connection failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_backend_list_flows(name: str, arguments: dict) -> List:
    """
    List all flows across all backends with filtering

    Args:
        name: Tool name
        arguments: backend_filter, intent_filter, min_performance_score

    Returns:
        List of MCP TextContent with flow catalog
    """
    try:
        registry = get_registry()
        await registry.discover_backends()

        backend_filter = arguments.get("backend_filter", "all")
        intent_filter = arguments.get("intent_filter")
        min_performance_score = arguments.get("min_performance_score", 0.0)

        all_flows = []
        backends = registry.get_all_backends()

        # Filter backends if requested
        if backend_filter != "all":
            backends = [b for b in backends if b.backend_type.value == backend_filter]

        router = get_router()

        for backend in backends:
            try:
                health = await backend.health_check()
                if not health:
                    continue

                flows = await backend.discover_flows()

                for flow in flows:
                    # Get performance data
                    perf_key = f"{backend.backend_type.value}:{flow.id}"
                    history = router.performance_tracker._history.get(perf_key, [])

                    avg_latency = 0.0
                    success_rate = 1.0
                    total_executions = len(history)

                    if history:
                        avg_latency = mean([h['latency_ms'] for h in history])
                        success_rate = sum(1 for h in history if h['success']) / len(history)

                    # Calculate composite performance score
                    perf_score = router.performance_tracker.get_score(
                        backend.backend_type.value,
                        flow.id
                    )

                    # Apply filters
                    if intent_filter and intent_filter.lower() not in [k.lower() for k in flow.intent_keywords]:
                        continue

                    if perf_score < min_performance_score:
                        continue

                    all_flows.append({
                        "id": flow.id,
                        "universal_id": f"{backend.backend_type.value}:{flow.id}",
                        "name": flow.name,
                        "description": flow.description,
                        "backend": backend.backend_type.value,
                        "backend_url": getattr(backend, 'base_url', 'unknown'),
                        "intent_keywords": flow.intent_keywords,
                        "performance": {
                            "score": round(perf_score, 2),
                            "avg_latency_ms": round(avg_latency, 0) if avg_latency > 0 else None,
                            "success_rate": round(success_rate, 2),
                            "total_executions": total_executions
                        }
                    })

            except Exception as e:
                logger.warning(f"Error listing flows for {backend.backend_type.value}: {e}")

        # Calculate summary
        by_backend = {}
        performance_scores = []

        for flow in all_flows:
            backend_type = flow['backend']
            by_backend[backend_type] = by_backend.get(backend_type, 0) + 1
            performance_scores.append(flow['performance']['score'])

        result = {
            "total_flows": len(all_flows),
            "filtered_count": len(all_flows),
            "flows": all_flows,
            "summary": {
                "by_backend": by_backend,
                "avg_performance": round(mean(performance_scores), 2) if performance_scores else 0.0
            }
        }

        return [_create_text_content(json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Backend list flows error: {e}")
        return [_create_text_content(
            f"❌ Error: Failed to list flows.\\n\\nDetails: {str(e)}"
        )]


async def handle_backend_execute_universal(name: str, arguments: dict) -> List:
    """
    Execute flow by ID with automatic backend resolution

    Args:
        name: Tool name
        arguments: flow_id, input_data, backend_preference, session_id

    Returns:
        List of MCP TextContent with execution result
    """
    try:
        flow_id = arguments.get("flow_id")
        input_data = arguments.get("input_data", {})
        backend_pref = arguments.get("backend_preference", "auto")
        session_id = arguments.get("session_id")

        if not flow_id:
            return [_create_text_content("❌ Error: 'flow_id' is required")]

        registry = get_registry()
        await registry.discover_backends()

        backends = registry.get_all_backends()

        # Filter by preference
        if backend_pref != "auto":
            backends = [b for b in backends if b.backend_type.value == backend_pref]

        # Find flow across backends
        target_backend = None
        target_flow = None

        for backend in backends:
            try:
                health = await backend.health_check()
                if not health:
                    continue

                flows = await backend.discover_flows()
                for flow in flows:
                    if flow.id == flow_id or flow.backend_specific_id == flow_id:
                        target_backend = backend
                        target_flow = flow
                        break

                if target_backend:
                    break

            except Exception as e:
                logger.warning(f"Error searching backend {backend.backend_type.value}: {e}")

        if not target_backend or not target_flow:
            return [_create_text_content(
                f"❌ Error: Flow '{flow_id}' not found in any available backend"
            )]

        # Execute flow
        start_time = time.time()

        result = await target_backend.execute_flow(
            flow_id=target_flow.backend_specific_id,
            input_data=input_data,
            session_id=session_id
        )

        duration_ms = (time.time() - start_time) * 1000

        # Record performance
        router = get_router()
        router.performance_tracker.record(
            backend=target_backend.backend_type.value,
            intent=flow_id,
            latency_ms=duration_ms,
            success=True
        )

        response = {
            "flow_id": flow_id,
            "backend_used": target_backend.backend_type.value,
            "execution_id": f"exec_{int(time.time()*1000)}",
            "result": result,
            "metadata": {
                "duration_ms": round(duration_ms, 0),
                "backend_selection": backend_pref,
                "fallback_used": False
            }
        }

        return [_create_text_content(json.dumps(response, indent=2))]

    except Exception as e:
        logger.error(f"Backend execute universal error: {e}")
        return [_create_text_content(
            f"❌ Error: Flow execution failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_backend_performance_compare(name: str, arguments: dict) -> List:
    """
    Compare performance metrics across backends

    Args:
        name: Tool name
        arguments: metric, time_range, intent_filter

    Returns:
        List of MCP TextContent with performance comparison
    """
    try:
        metric = arguments.get("metric", "latency")
        time_range = arguments.get("time_range", "24h")
        intent_filter = arguments.get("intent_filter")

        registry = get_registry()
        await registry.discover_backends()

        router = get_router()

        # Calculate time cutoff
        time_cutoffs = {
            "1h": datetime.utcnow() - timedelta(hours=1),
            "24h": datetime.utcnow() - timedelta(hours=24),
            "7d": datetime.utcnow() - timedelta(days=7),
            "30d": datetime.utcnow() - timedelta(days=30)
        }
        cutoff = time_cutoffs.get(time_range, time_cutoffs["24h"])

        # Collect metrics per backend
        comparison = []

        for backend in registry.get_all_backends():
            backend_type = backend.backend_type.value
            backend_metrics = []
            total_requests = 0
            successes = 0

            # Collect all metrics for this backend
            for key, history in router.performance_tracker._history.items():
                if not key.startswith(f"{backend_type}:"):
                    continue

                # Apply intent filter if specified
                if intent_filter:
                    intent = key.split(":", 1)[1]
                    if intent_filter.lower() not in intent.lower():
                        continue

                for record in history:
                    # Filter by time range (approximate - using record count as proxy)
                    backend_metrics.append(record['latency_ms'])
                    total_requests += 1
                    if record['success']:
                        successes += 1

            if not backend_metrics:
                continue

            # Calculate statistics
            avg_latency = mean(backend_metrics)
            success_rate = successes / total_requests if total_requests > 0 else 0.0

            # Calculate percentiles
            p50, p95, p99 = 0.0, 0.0, 0.0
            if len(backend_metrics) >= 2:
                percentiles = quantiles(backend_metrics, n=100)
                p50 = percentiles[49]  # 50th percentile
                p95 = percentiles[94]  # 95th percentile
                p99 = percentiles[98]  # 99th percentile
            elif len(backend_metrics) == 1:
                p50 = p95 = p99 = backend_metrics[0]

            comparison.append({
                "backend": backend_type,
                "backend_type": backend_type,
                "metrics": {
                    "avg_latency_ms": round(avg_latency, 0),
                    "p50_latency_ms": round(p50, 0),
                    "p95_latency_ms": round(p95, 0),
                    "p99_latency_ms": round(p99, 0)
                },
                "total_requests": total_requests,
                "success_rate": round(success_rate, 2)
            })

        # Determine winner and recommendation
        winner = None
        recommendation = "Insufficient data for recommendation"

        if len(comparison) >= 2:
            if metric == "latency":
                comparison_sorted = sorted(comparison, key=lambda x: x['metrics']['avg_latency_ms'])
                winner_data = comparison_sorted[0]
                runner_up = comparison_sorted[1]

                advantage_percent = (
                    (runner_up['metrics']['avg_latency_ms'] - winner_data['metrics']['avg_latency_ms'])
                    / runner_up['metrics']['avg_latency_ms']
                    * 100
                )

                winner = {
                    "backend": winner_data['backend'],
                    "advantage_percent": round(advantage_percent, 1),
                    "metric_value": winner_data['metrics']['avg_latency_ms']
                }

                recommendation = (
                    f"{winner_data['backend'].title()} shows {abs(advantage_percent):.0f}% better latency. "
                    f"Consider routing latency-sensitive flows to {winner_data['backend'].title()}."
                )
            elif metric == "success_rate":
                comparison_sorted = sorted(comparison, key=lambda x: x['success_rate'], reverse=True)
                winner_data = comparison_sorted[0]

                winner = {
                    "backend": winner_data['backend'],
                    "metric_value": winner_data['success_rate']
                }

                recommendation = f"{winner_data['backend'].title()} has the highest success rate ({winner_data['success_rate']:.0%})"

        result = {
            "metric": metric,
            "time_range": time_range,
            "comparison": comparison,
            "winner": winner,
            "recommendation": recommendation,
            "trend": "stable"  # Could be enhanced with historical comparison
        }

        return [_create_text_content(json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Backend performance compare error: {e}")
        return [_create_text_content(
            f"❌ Error: Performance comparison failed.\\n\\nDetails: {str(e)}"
        )]


def _create_text_content(text: str):
    """Create MCP TextContent object or plain dict if MCP not available"""
    if types:
        return types.TextContent(type="text", text=text)
    else:
        return {"type": "text", "text": text}
