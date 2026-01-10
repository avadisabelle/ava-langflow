#!/usr/bin/env python3
"""
Tests for Admin Intelligence MCP Tools
"""

import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

import pytest
import json
from unittest.mock import AsyncMock, Mock, patch

from agentic_flywheel.tools.admin_tools import (
    handle_flowise_admin_dashboard,
    handle_flowise_analyze_flow,
    handle_flowise_discover_flows,
    handle_flowise_sync_config,
    handle_flowise_export_metrics,
    handle_flowise_pattern_analysis
)


# Test Fixtures

@pytest.fixture
def mock_dashboard_data():
    """Mock dashboard data"""
    return {
        "total_messages": 4506,
        "total_flows": 7,
        "date_range": {
            "start": "2024-01-01",
            "end": "2025-11-18"
        },
        "top_flows": [
            {
                "id": "csv2507",
                "name": "Creative Orientation",
                "message_count": 118,
                "avg_success_score": 0.92,
                "avg_engagement": 0.88
            },
            {
                "id": "faith2story2507",
                "name": "Faith2Story",
                "message_count": 60,
                "avg_success_score": 0.85,
                "avg_engagement": 0.82
            }
        ],
        "flows": [
            {"id": "csv2507", "message_count": 118},
            {"id": "faith2story2507", "message_count": 60},
            {"id": "low_usage_flow", "message_count": 5}
        ],
        "overall_metrics": {
            "success_rate": 0.85,
            "avg_response_time_seconds": 2.3,
            "total_sessions": 342
        }
    }


@pytest.fixture
def mock_flow_analysis():
    """Mock flow analysis data"""
    return {
        "flow_id": "csv2507",
        "flow_name": "Creative Orientation",
        "total_messages": 118,
        "date_range": {"start": "2024-01-15", "end": "2025-11-18"},
        "performance": {
            "avg_success_score": 0.92,
            "avg_engagement": 0.88,
            "avg_response_time_seconds": 2.1,
            "success_rate": 0.95
        },
        "patterns": {
            "common_questions": [
                "What is structural tension?",
                "How do I create desired outcomes?"
            ],
            "peak_usage_hours": [14, 15, 16],
            "avg_conversation_length": 3.2
        }
    }


@pytest.fixture
def mock_discovered_flows():
    """Mock discovered flows data"""
    return {
        "discovered_flows": 7,
        "active_flows": 5,
        "inactive_flows": 2,
        "flows": [
            {
                "id": "csv2507",
                "name": "Creative Orientation",
                "message_count": 118,
                "success_score": 0.92,
                "engagement_score": 0.88,
                "last_used": "2025-11-18T10:00:00Z",
                "status": "active"
            },
            {
                "id": "low_usage_flow",
                "name": "Low Usage",
                "message_count": 3,
                "success_score": 0.50,
                "engagement_score": 0.45,
                "last_used": "2025-10-01T10:00:00Z",
                "status": "inactive"
            }
        ]
    }


# Dashboard Tests

@pytest.mark.asyncio
async def test_flowise_admin_dashboard_success(mock_dashboard_data):
    """Test successful dashboard retrieval"""
    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.get_admin_dashboard_data.return_value = mock_dashboard_data
        mock_db_class.return_value = mock_db

        result = await handle_flowise_admin_dashboard("flowise_admin_dashboard", {})

        assert len(result) == 1
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["total_messages"] == 4506
        assert data["total_flows"] == 7
        assert "recommendations" in data
        assert len(data["recommendations"]) > 0


@pytest.mark.asyncio
async def test_flowise_admin_dashboard_import_error():
    """Test dashboard when admin module unavailable"""
    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface', side_effect=ImportError("Module not found")):
        result = await handle_flowise_admin_dashboard("flowise_admin_dashboard", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "not available" in response_text.lower()


@pytest.mark.asyncio
async def test_flowise_admin_dashboard_database_error():
    """Test dashboard with database error"""
    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.get_admin_dashboard_data.side_effect = Exception("Database connection failed")
        mock_db_class.return_value = mock_db

        result = await handle_flowise_admin_dashboard("flowise_admin_dashboard", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "unavailable" in response_text.lower()
        assert "database" in response_text.lower()


# Flow Analysis Tests

@pytest.mark.asyncio
async def test_flowise_analyze_flow_success(mock_flow_analysis):
    """Test successful flow analysis"""
    with patch('agentic_flywheel.tools.admin_tools.FlowAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.analyze_flow_performance.return_value = mock_flow_analysis
        mock_analyzer_class.return_value = mock_analyzer

        arguments = {"flow_id": "csv2507", "include_samples": False}
        result = await handle_flowise_analyze_flow("flowise_analyze_flow", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["flow_id"] == "csv2507"
        assert data["total_messages"] == 118
        assert "optimization_suggestions" in data
        assert len(data["optimization_suggestions"]) > 0


@pytest.mark.asyncio
async def test_flowise_analyze_flow_missing_param():
    """Test flow analysis with missing flow_id"""
    result = await handle_flowise_analyze_flow("flowise_analyze_flow", {})

    response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
    assert "required" in response_text.lower()


@pytest.mark.asyncio
async def test_flowise_analyze_flow_with_samples(mock_flow_analysis):
    """Test flow analysis with sample inclusion"""
    with patch('agentic_flywheel.tools.admin_tools.FlowAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.analyze_flow_performance.return_value = mock_flow_analysis
        mock_analyzer_class.return_value = mock_analyzer

        arguments = {"flow_id": "csv2507", "include_samples": True}
        result = await handle_flowise_analyze_flow("flowise_analyze_flow", arguments)

        # Verify include_samples was passed
        mock_analyzer.analyze_flow_performance.assert_called_once_with(
            "csv2507", include_samples=True
        )


# Flow Discovery Tests

@pytest.mark.asyncio
async def test_flowise_discover_flows_success(mock_discovered_flows):
    """Test successful flow discovery"""
    with patch('agentic_flywheel.tools.admin_tools.ConfigSync') as mock_sync_class:
        mock_sync = Mock()
        mock_sync.discover_active_flows.return_value = mock_discovered_flows
        mock_sync_class.return_value = mock_sync

        result = await handle_flowise_discover_flows("flowise_discover_flows", {})

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["discovered_flows"] == 7
        assert data["active_flows"] == 5
        assert "recommendations" in data


@pytest.mark.asyncio
async def test_flowise_discover_flows_with_filters(mock_discovered_flows):
    """Test flow discovery with filters"""
    with patch('agentic_flywheel.tools.admin_tools.ConfigSync') as mock_sync_class:
        mock_sync = Mock()
        mock_sync.discover_active_flows.return_value = mock_discovered_flows
        mock_sync_class.return_value = mock_sync

        arguments = {
            "min_messages": 20,
            "include_inactive": True,
            "sort_by": "success_rate"
        }
        result = await handle_flowise_discover_flows("flowise_discover_flows", arguments)

        # Verify parameters were passed
        mock_sync.discover_active_flows.assert_called_once_with(
            min_messages=20,
            include_inactive=True
        )


@pytest.mark.asyncio
async def test_flowise_discover_flows_sorting(mock_discovered_flows):
    """Test flow discovery sorting options"""
    with patch('agentic_flywheel.tools.admin_tools.ConfigSync') as mock_sync_class:
        mock_sync = Mock()
        mock_sync.discover_active_flows.return_value = mock_discovered_flows
        mock_sync_class.return_value = mock_sync

        # Test sorting by usage (default)
        result = await handle_flowise_discover_flows("flowise_discover_flows", {"sort_by": "usage"})
        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        # First flow should have highest message count
        assert data["flows"][0]["message_count"] >= data["flows"][-1]["message_count"]


# Config Sync Tests

@pytest.mark.asyncio
async def test_flowise_sync_config_dry_run():
    """Test config sync in dry run mode"""
    mock_sync_result = {
        "dry_run": True,
        "changes_detected": 3,
        "changes": [
            {"type": "add", "flow_id": "new_flow", "reason": "High usage but not in registry"},
            {"type": "update", "flow_id": "csv2507", "field": "description"},
            {"type": "remove", "flow_id": "unused_flow", "reason": "Zero usage"}
        ],
        "applied": False,
        "backup_created": False
    }

    with patch('agentic_flywheel.tools.admin_tools.ConfigSync') as mock_sync_class:
        mock_sync = Mock()
        mock_sync.sync_configurations.return_value = mock_sync_result
        mock_sync_class.return_value = mock_sync

        arguments = {"dry_run": True}
        result = await handle_flowise_sync_config("flowise_sync_config", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["dry_run"] is True
        assert data["changes_detected"] == 3
        assert data["applied"] is False


@pytest.mark.asyncio
async def test_flowise_sync_config_with_options():
    """Test config sync with various options"""
    with patch('agentic_flywheel.tools.admin_tools.ConfigSync') as mock_sync_class:
        mock_sync = Mock()
        mock_sync.sync_configurations.return_value = {"dry_run": False, "applied": True}
        mock_sync_class.return_value = mock_sync

        arguments = {
            "dry_run": False,
            "auto_add_flows": True,
            "remove_inactive": True
        }
        result = await handle_flowise_sync_config("flowise_sync_config", arguments)

        # Verify all parameters were passed
        mock_sync.sync_configurations.assert_called_once_with(
            dry_run=False,
            auto_add=True,
            remove_inactive=True
        )


# Export Metrics Tests

@pytest.mark.asyncio
async def test_flowise_export_metrics_json():
    """Test metrics export in JSON format"""
    mock_export = {
        "export_date": "2025-11-18T12:00:00Z",
        "format": "json",
        "flows_included": 7,
        "data": [
            {
                "flow_id": "csv2507",
                "flow_name": "Creative Orientation",
                "total_messages": 118,
                "avg_success_score": 0.92
            }
        ]
    }

    with patch('agentic_flywheel.tools.admin_tools.FlowAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.export_flow_configurations.return_value = mock_export
        mock_analyzer_class.return_value = mock_analyzer

        arguments = {"format": "json"}
        result = await handle_flowise_export_metrics("flowise_export_metrics", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["format"] == "json"
        assert data["flows_included"] == 7


@pytest.mark.asyncio
async def test_flowise_export_metrics_csv():
    """Test metrics export in CSV format"""
    mock_csv = "flow_id,flow_name,total_messages,avg_success_score\ncsv2507,Creative Orientation,118,0.92"

    with patch('agentic_flywheel.tools.admin_tools.FlowAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.export_flow_configurations.return_value = mock_csv
        mock_analyzer_class.return_value = mock_analyzer

        arguments = {"format": "csv"}
        result = await handle_flowise_export_metrics("flowise_export_metrics", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        assert "csv2507" in response_text
        assert "Creative Orientation" in response_text


@pytest.mark.asyncio
async def test_flowise_export_metrics_specific_flows():
    """Test metrics export for specific flows"""
    with patch('agentic_flywheel.tools.admin_tools.FlowAnalyzer') as mock_analyzer_class:
        mock_analyzer = Mock()
        mock_analyzer.export_flow_configurations.return_value = {"data": []}
        mock_analyzer_class.return_value = mock_analyzer

        arguments = {
            "format": "json",
            "flows": ["csv2507", "faith2story2507"],
            "include_messages": True
        }
        result = await handle_flowise_export_metrics("flowise_export_metrics", arguments)

        # Verify specific flows were requested
        mock_analyzer.export_flow_configurations.assert_called_once_with(
            format="json",
            flows=["csv2507", "faith2story2507"],
            include_messages=True
        )


# Pattern Analysis Tests

@pytest.mark.asyncio
async def test_flowise_pattern_analysis_success():
    """Test successful pattern analysis"""
    mock_patterns = {
        "analyzed_messages": 100,
        "flow_id": "csv2507",
        "patterns": {
            "question_types": {
                "definition_seeking": 45,
                "how_to": 32,
                "example_request": 18
            },
            "success_factors": [
                "Questions about 'structural tension' have 95% success rate"
            ],
            "failure_modes": [
                "Vague questions result in lower success"
            ]
        }
    }

    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.analyze_message_patterns.return_value = mock_patterns
        mock_db_class.return_value = mock_db

        arguments = {"flow_id": "csv2507", "limit": 100}
        result = await handle_flowise_pattern_analysis("flowise_pattern_analysis", arguments)

        response_text = result[0]["text"] if isinstance(result[0], dict) else result[0].text
        data = json.loads(response_text)

        assert data["flow_id"] == "csv2507"
        assert data["analyzed_messages"] == 100
        assert "recommendations" in data


@pytest.mark.asyncio
async def test_flowise_pattern_analysis_all_flows():
    """Test pattern analysis for all flows"""
    mock_patterns = {
        "analyzed_messages": 500,
        "patterns": {"question_types": {}}
    }

    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.analyze_message_patterns.return_value = mock_patterns
        mock_db_class.return_value = mock_db

        # No flow_id means analyze all flows
        result = await handle_flowise_pattern_analysis("flowise_pattern_analysis", {"limit": 500})

        # Verify no flow_id was passed
        mock_db.analyze_message_patterns.assert_called_once()
        call_args = mock_db.analyze_message_patterns.call_args
        assert call_args[1]['flow_id'] is None


@pytest.mark.asyncio
async def test_flowise_pattern_analysis_pattern_types():
    """Test pattern analysis with specific pattern types"""
    with patch('agentic_flywheel.tools.admin_tools.FlowiseDBInterface') as mock_db_class:
        mock_db = Mock()
        mock_db.analyze_message_patterns.return_value = {"patterns": {}}
        mock_db_class.return_value = mock_db

        arguments = {
            "flow_id": "csv2507",
            "limit": 100,
            "pattern_type": "success_factors"
        }
        result = await handle_flowise_pattern_analysis("flowise_pattern_analysis", arguments)

        # Verify pattern_type was passed
        mock_db.analyze_message_patterns.assert_called_once_with(
            flow_id="csv2507",
            limit=100,
            pattern_type="success_factors"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
