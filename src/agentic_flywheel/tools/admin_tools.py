"""Admin Intelligence MCP Tools

Wraps the existing flowise_admin layer to provide MCP-accessible analytics.
"""

import json
import logging
from typing import Any, Dict, List, Optional

try:
    from mcp import types
except ImportError:
    types = None

logger = logging.getLogger(__name__)


async def handle_flowise_admin_dashboard(name: str, arguments: dict) -> List:
    """
    Get comprehensive analytics dashboard

    Args:
        name: Tool name
        arguments: Empty dict (no parameters)

    Returns:
        List of MCP TextContent with dashboard data
    """
    try:
        from ..flowise_admin.db_interface import FlowiseDBInterface

        db = FlowiseDBInterface()
        dashboard_data = db.get_admin_dashboard_data()

        # Enhance with recommendations
        recommendations = _generate_dashboard_recommendations(dashboard_data)
        dashboard_data['recommendations'] = recommendations

        return [_create_text_content(json.dumps(dashboard_data, indent=2))]

    except ImportError as e:
        logger.error(f"FloWise admin module not available: {e}")
        return [_create_text_content(
            "❌ Error: Flowise admin modules not available.\\n\\n"
            "The admin intelligence features require the flowise_admin package."
        )]

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return [_create_text_content(
            f"❌ Error: Dashboard unavailable.\\n\\nDetails: {str(e)}\\n\\n"
            "Check database connection and permissions."
        )]


async def handle_flowise_analyze_flow(name: str, arguments: dict) -> List:
    """
    Analyze performance metrics for a specific flow

    Args:
        name: Tool name
        arguments: flow_id (required), include_samples (optional)

    Returns:
        List of MCP TextContent with flow analysis
    """
    try:
        flow_id = arguments.get("flow_id")
        if not flow_id:
            return [_create_text_content("❌ Error: 'flow_id' parameter is required")]

        include_samples = arguments.get("include_samples", False)

        from ..flowise_admin.flow_analyzer import FlowAnalyzer

        analyzer = FlowAnalyzer()
        analysis = analyzer.analyze_flow_performance(flow_id, include_samples=include_samples)

        # Enhance with optimization suggestions
        suggestions = _generate_optimization_suggestions(analysis)
        analysis['optimization_suggestions'] = suggestions

        return [_create_text_content(json.dumps(analysis, indent=2))]

    except ImportError as e:
        logger.error(f"Flow analyzer not available: {e}")
        return [_create_text_content(
            "❌ Error: Flow analyzer not available.\\n\\n"
            "Check flowise_admin installation."
        )]

    except Exception as e:
        logger.error(f"Flow analysis error: {e}")
        return [_create_text_content(
            f"❌ Error: Flow analysis failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_flowise_discover_flows(name: str, arguments: dict) -> List:
    """
    Discover flows from database with usage analytics

    Args:
        name: Tool name
        arguments: min_messages (optional), include_inactive (optional), sort_by (optional)

    Returns:
        List of MCP TextContent with discovered flows
    """
    try:
        min_messages = arguments.get("min_messages", 10)
        include_inactive = arguments.get("include_inactive", False)
        sort_by = arguments.get("sort_by", "usage")

        from ..flowise_admin.config_sync import ConfigSync

        sync = ConfigSync()
        flows_data = sync.discover_active_flows(
            min_messages=min_messages,
            include_inactive=include_inactive
        )

        # Sort flows
        if sort_by == "usage":
            flows_data['flows'].sort(key=lambda x: x.get('message_count', 0), reverse=True)
        elif sort_by == "success_rate":
            flows_data['flows'].sort(key=lambda x: x.get('success_score', 0), reverse=True)
        elif sort_by == "engagement":
            flows_data['flows'].sort(key=lambda x: x.get('engagement_score', 0), reverse=True)
        elif sort_by == "recent":
            flows_data['flows'].sort(key=lambda x: x.get('last_used', ''), reverse=True)

        # Generate recommendations
        recommendations = _generate_flow_recommendations(flows_data)
        flows_data['recommendations'] = recommendations

        return [_create_text_content(json.dumps(flows_data, indent=2))]

    except ImportError as e:
        logger.error(f"Config sync not available: {e}")
        return [_create_text_content(
            "❌ Error: Configuration sync module not available."
        )]

    except Exception as e:
        logger.error(f"Flow discovery error: {e}")
        return [_create_text_content(
            f"❌ Error: Flow discovery failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_flowise_sync_config(name: str, arguments: dict) -> List:
    """
    Sync flow registry with database-discovered flows

    Args:
        name: Tool name
        arguments: dry_run (optional), auto_add_flows (optional), remove_inactive (optional)

    Returns:
        List of MCP TextContent with sync results
    """
    try:
        dry_run = arguments.get("dry_run", True)
        auto_add_flows = arguments.get("auto_add_flows", False)
        remove_inactive = arguments.get("remove_inactive", False)

        from ..flowise_admin.config_sync import ConfigSync

        sync = ConfigSync()
        sync_result = sync.sync_configurations(
            dry_run=dry_run,
            auto_add=auto_add_flows,
            remove_inactive=remove_inactive
        )

        return [_create_text_content(json.dumps(sync_result, indent=2))]

    except ImportError as e:
        logger.error(f"Config sync not available: {e}")
        return [_create_text_content(
            "❌ Error: Configuration sync module not available."
        )]

    except Exception as e:
        logger.error(f"Config sync error: {e}")
        return [_create_text_content(
            f"❌ Error: Configuration sync failed.\\n\\nDetails: {str(e)}\\n\\n"
            "If this is a write operation, ensure you have file system permissions."
        )]


async def handle_flowise_export_metrics(name: str, arguments: dict) -> List:
    """
    Export flow performance metrics

    Args:
        name: Tool name
        arguments: format (optional), flows (optional), include_messages (optional)

    Returns:
        List of MCP TextContent with exported metrics
    """
    try:
        export_format = arguments.get("format", "json")
        flows = arguments.get("flows", [])
        include_messages = arguments.get("include_messages", False)

        from ..flowise_admin.flow_analyzer import FlowAnalyzer

        analyzer = FlowAnalyzer()
        export_data = analyzer.export_flow_configurations(
            format=export_format,
            flows=flows,
            include_messages=include_messages
        )

        if export_format == "json":
            return [_create_text_content(json.dumps(export_data, indent=2))]
        elif export_format == "csv":
            # CSV is returned as text
            return [_create_text_content(export_data)]
        else:
            return [_create_text_content(f"❌ Error: Unsupported format '{export_format}'")]

    except ImportError as e:
        logger.error(f"Flow analyzer not available: {e}")
        return [_create_text_content(
            "❌ Error: Flow analyzer not available."
        )]

    except Exception as e:
        logger.error(f"Export error: {e}")
        return [_create_text_content(
            f"❌ Error: Metrics export failed.\\n\\nDetails: {str(e)}"
        )]


async def handle_flowise_pattern_analysis(name: str, arguments: dict) -> List:
    """
    Analyze conversation patterns for optimization insights

    Args:
        name: Tool name
        arguments: flow_id (optional), limit (optional), pattern_type (optional)

    Returns:
        List of MCP TextContent with pattern analysis
    """
    try:
        flow_id = arguments.get("flow_id")
        limit = arguments.get("limit", 100)
        pattern_type = arguments.get("pattern_type", "all")

        from ..flowise_admin.db_interface import FlowiseDBInterface

        db = FlowiseDBInterface()
        patterns = db.analyze_message_patterns(
            flow_id=flow_id,
            limit=limit,
            pattern_type=pattern_type
        )

        # Generate recommendations from patterns
        recommendations = _generate_pattern_recommendations(patterns)
        patterns['recommendations'] = recommendations

        return [_create_text_content(json.dumps(patterns, indent=2))]

    except ImportError as e:
        logger.error(f"DB interface not available: {e}")
        return [_create_text_content(
            "❌ Error: Database interface not available."
        )]

    except Exception as e:
        logger.error(f"Pattern analysis error: {e}")
        return [_create_text_content(
            f"❌ Error: Pattern analysis failed.\\n\\nDetails: {str(e)}"
        )]


# Recommendation Engines

def _generate_dashboard_recommendations(data: Dict) -> List[str]:
    """Generate actionable insights from dashboard data"""
    recommendations = []

    # High engagement flows
    top_flows = data.get('top_flows', [])[:3]
    if top_flows and len(top_flows) > 0:
        top_flow = top_flows[0]
        recommendations.append(
            f"{top_flow.get('name', 'Top flow')} shows high engagement - "
            f"consider expanding similar flows"
        )

    # Low usage detection
    all_flows = data.get('flows', [])
    if all_flows:
        low_usage = [f for f in all_flows if f.get('message_count', 0) < 10]
        if len(low_usage) > 0:
            recommendations.append(
                f"{len(low_usage)} flow(s) show low usage - "
                f"review relevance or discoverability"
            )

    # Success rate analysis
    overall_success = data.get('overall_metrics', {}).get('success_rate')
    if overall_success is not None:
        if overall_success < 0.7:
            recommendations.append(
                f"Overall success rate is low ({overall_success:.0%}) - "
                f"review flow prompts and responses"
            )
        elif overall_success > 0.9:
            recommendations.append(
                f"Excellent success rate ({overall_success:.0%}) - "
                f"system performing well"
            )

    if not recommendations:
        recommendations.append("System metrics look healthy - continue monitoring")

    return recommendations


def _generate_optimization_suggestions(analysis: Dict) -> List[str]:
    """Generate optimization suggestions from flow analysis"""
    suggestions = []

    perf = analysis.get('performance', {})

    # Response time suggestions
    avg_time = perf.get('avg_response_time_seconds', 0)
    if avg_time > 5.0:
        suggestions.append(f"Response time is high ({avg_time:.1f}s) - consider optimization or caching")
    elif avg_time < 2.0:
        suggestions.append(f"Response time is excellent ({avg_time:.1f}s avg)")

    # Success score suggestions
    success_score = perf.get('avg_success_score', 0)
    if success_score > 0.9:
        suggestions.append(f"High success score ({success_score:.2f}) suggests strong flow design")
    elif success_score < 0.7:
        suggestions.append(f"Low success score ({success_score:.2f}) - review flow prompt and examples")

    # Usage patterns
    total_messages = analysis.get('total_messages', 0)
    if total_messages > 100:
        suggestions.append("High usage flow - consider caching for frequently asked questions")
    elif total_messages < 10:
        suggestions.append("Low usage - review discoverability or marketing")

    if not suggestions:
        suggestions.append("Flow performing within normal parameters")

    return suggestions


def _generate_flow_recommendations(flows_data: Dict) -> Dict[str, List[str]]:
    """Generate recommendations from flow discovery"""
    flows = flows_data.get('flows', [])

    high_performers = []
    needs_attention = []
    suggested_removals = []

    for flow in flows:
        message_count = flow.get('message_count', 0)
        success_score = flow.get('success_score', 0)
        flow_id = flow.get('id', 'unknown')

        if success_score > 0.85 and message_count > 50:
            high_performers.append(flow_id)
        elif success_score < 0.6 or message_count < 5:
            needs_attention.append(flow_id)
        if message_count == 0:
            suggested_removals.append(flow_id)

    return {
        "high_performers": high_performers,
        "needs_attention": needs_attention,
        "suggested_removals": suggested_removals
    }


def _generate_pattern_recommendations(patterns: Dict) -> List[str]:
    """Generate recommendations from pattern analysis"""
    recommendations = []

    # Question type analysis
    question_types = patterns.get('patterns', {}).get('question_types', {})
    if question_types:
        most_common = max(question_types.items(), key=lambda x: x[1])[0]
        recommendations.append(
            f"Most common question type is '{most_common}' - "
            f"optimize flow for this pattern"
        )

    # Success factors
    success_factors = patterns.get('patterns', {}).get('success_factors', [])
    if len(success_factors) > 0:
        recommendations.append("Leverage success factors: " + success_factors[0])

    # Failure modes
    failure_modes = patterns.get('patterns', {}).get('failure_modes', [])
    if len(failure_modes) > 0:
        recommendations.append("Address failure mode: " + failure_modes[0])

    if not recommendations:
        recommendations.append("Insufficient data for pattern-based recommendations")

    return recommendations


def _create_text_content(text: str):
    """Create MCP TextContent object or plain dict if MCP not available"""
    if types:
        return types.TextContent(type="text", text=text)
    else:
        return {"type": "text", "text": text}
