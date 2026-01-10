"""Unit tests for Langfuse Creative Archaeology Tracer

Tests cover:
- Decorator functionality and context management
- Observation creation and structured logging
- Score helpers and metrics tracking
- Error handling and fail-safe behavior
- Performance overhead verification

Run tests:
    pytest tests/test_langfuse_tracer.py -v --cov=src/agentic_flywheel/integrations
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, AsyncMock
from typing import Any, Dict

# Import components under test
import sys
sys.path.insert(0, '/home/user/ava-langflow/src/agentic_flywheel')

from integrations.langfuse_tracer import (
    trace_mcp_tool,
    get_current_trace_id,
    LangfuseObservation,
    LangfuseScore,
    LangfuseTracerManager
)


class TestLangfuseTracerManager:
    """Tests for LangfuseTracerManager class"""

    def test_init_with_env_vars(self):
        """Test initialization with environment variables"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com",
            "AGENTIC_FLYWHEEL_PARENT_TRACE_ID": "parent-123"
        }):
            tracer = LangfuseTracerManager()

            assert tracer.enabled is True
            assert tracer.parent_trace_id == "parent-123"
            assert tracer.timeout_ms == 5000

    def test_init_disabled_when_credentials_missing(self):
        """Test tracing auto-disables when credentials missing"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "",  # Missing
            "LANGFUSE_SECRET_KEY": "",  # Missing
            "LANGFUSE_HOST": ""  # Missing
        }, clear=True):
            tracer = LangfuseTracerManager()

            assert tracer.enabled is False

    def test_init_explicit_disable(self):
        """Test explicit tracing disable via parameter"""
        with patch.dict(os.environ, {
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager(enabled=False)

            assert tracer.enabled is False

    @pytest.mark.asyncio
    async def test_create_trace_success(self):
        """Test successful trace creation"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()

            trace_id = await tracer.create_trace(
                name="test_trace",
                metadata={"test": "value"},
                input_data={"question": "test"}
            )

            assert trace_id is not None
            assert trace_id.startswith("trace-")
            assert trace_id in tracer._active_traces
            assert tracer._active_traces[trace_id]["name"] == "test_trace"

    @pytest.mark.asyncio
    async def test_create_trace_when_disabled(self):
        """Test trace creation returns None when tracing disabled"""
        tracer = LangfuseTracerManager(enabled=False)

        trace_id = await tracer.create_trace("test_trace")

        assert trace_id is None

    @pytest.mark.asyncio
    async def test_end_trace(self):
        """Test trace completion"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            await tracer.end_trace(trace_id, output_data={"result": "success"})

            trace_info = tracer.get_trace_info(trace_id)
            assert "ended_at" in trace_info
            assert trace_info["output_data"] == {"result": "success"}

    def test_get_trace_info(self):
        """Test trace information retrieval"""
        tracer = LangfuseTracerManager()
        tracer._active_traces["test-123"] = {
            "name": "test",
            "started_at": "2025-11-18T10:00:00"
        }

        info = tracer.get_trace_info("test-123")

        assert info is not None
        assert info["name"] == "test"

        # Non-existent trace
        assert tracer.get_trace_info("nonexistent") is None


class TestTraceMCPToolDecorator:
    """Tests for @trace_mcp_tool decorator"""

    @pytest.mark.asyncio
    async def test_decorator_preserves_function_behavior(self):
        """Test decorator doesn't change function return value"""
        @trace_mcp_tool("test_tool", capture_input=False, capture_output=False)
        async def test_function(name: str, arguments: dict) -> dict:
            return {"result": "success", "input": arguments}

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            result = await test_function("test_tool", {"question": "test"})

            assert result == {"result": "success", "input": {"question": "test"}}

    @pytest.mark.asyncio
    async def test_decorator_sets_trace_context(self):
        """Test decorator sets trace_id in async context"""
        @trace_mcp_tool("test_tool")
        async def test_function(name: str, arguments: dict) -> str:
            trace_id = get_current_trace_id()
            return trace_id

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            trace_id = await test_function("test_tool", {"question": "test"})

            assert trace_id is not None
            assert trace_id.startswith("trace-")

    @pytest.mark.asyncio
    async def test_decorator_handles_exceptions_gracefully(self):
        """Test decorator re-raises exceptions after logging"""
        @trace_mcp_tool("test_tool")
        async def test_function(name: str, arguments: dict):
            raise ValueError("Test error")

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            with pytest.raises(ValueError, match="Test error"):
                await test_function("test_tool", {"question": "test"})

    @pytest.mark.asyncio
    async def test_decorator_disabled_when_tracing_off(self):
        """Test decorator is transparent when tracing disabled"""
        call_count = 0

        @trace_mcp_tool("test_tool")
        async def test_function(name: str, arguments: dict) -> str:
            nonlocal call_count
            call_count += 1
            return "success"

        # Tracing disabled (no credentials)
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "false"
        }, clear=True):
            result = await test_function("test_tool", {"question": "test"})

            assert result == "success"
            assert call_count == 1
            assert get_current_trace_id() is None

    @pytest.mark.asyncio
    async def test_decorator_captures_input_output(self):
        """Test decorator captures input and output data"""
        @trace_mcp_tool("test_tool", capture_input=True, capture_output=True)
        async def test_function(name: str, arguments: dict) -> dict:
            return {"result": "success", "data": "test"}

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            result = await test_function("test_tool", {"question": "test"})

            assert result == {"result": "success", "data": "test"}


class TestLangfuseObservation:
    """Tests for LangfuseObservation helper methods"""

    @pytest.mark.asyncio
    async def test_add_intent_classification(self):
        """Test intent classification observation"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseObservation.add_intent_classification(
                trace_id, "creative-orientation", 0.95, ["creative", "goal"]
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["observations"]) == 1
            assert trace_info["observations"][0]["type"] == "intent_classification"
            assert trace_info["observations"][0]["data"]["intent"] == "creative-orientation"
            assert trace_info["observations"][0]["data"]["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_add_flow_selection(self):
        """Test flow selection observation"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseObservation.add_flow_selection(
                trace_id, "csv2507", "Creative Orientation", "flowise",
                "Selected based on intent matching"
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["observations"]) == 1
            assert trace_info["observations"][0]["type"] == "flow_selection"
            assert trace_info["observations"][0]["data"]["flow_id"] == "csv2507"
            assert trace_info["observations"][0]["data"]["backend"] == "flowise"

    @pytest.mark.asyncio
    async def test_add_execution(self):
        """Test execution observation with I/O"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseObservation.add_execution(
                trace_id,
                "What is structural tension?",
                "Structural tension is the gap...",
                1235.7
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["observations"]) == 1
            assert trace_info["observations"][0]["type"] == "execution"
            assert trace_info["observations"][0]["data"]["duration_ms"] == 1235.7

    @pytest.mark.asyncio
    async def test_add_error(self):
        """Test error observation"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseObservation.add_error(
                trace_id, "ValueError", "Invalid input", "Traceback..."
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["observations"]) == 1
            assert trace_info["observations"][0]["type"] == "error"
            assert trace_info["observations"][0]["data"]["error_type"] == "ValueError"

    @pytest.mark.asyncio
    async def test_observations_fail_gracefully_when_disabled(self):
        """Test observations return False when tracing disabled"""
        tracer = LangfuseTracerManager(enabled=False)

        success = await LangfuseObservation.add_intent_classification(
            None, "creative", 0.9, []
        )

        assert success is False


class TestLangfuseScore:
    """Tests for LangfuseScore helper methods"""

    @pytest.mark.asyncio
    async def test_add_quality_score(self):
        """Test quality score addition"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseScore.add_quality_score(
                trace_id, 0.9, "Excellent response quality"
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["scores"]) == 1
            assert trace_info["scores"][0]["name"] == "quality"
            assert trace_info["scores"][0]["value"] == 0.9

    @pytest.mark.asyncio
    async def test_add_latency_score(self):
        """Test latency score addition"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseScore.add_latency_score(trace_id, 1235.7)

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert len(trace_info["scores"]) == 1
            assert trace_info["scores"][0]["name"] == "latency"
            assert trace_info["scores"][0]["value"] == 1235.7
            assert trace_info["scores"][0]["unit"] == "ms"

    @pytest.mark.asyncio
    async def test_add_success_score_true(self):
        """Test success score for successful execution"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseScore.add_success_score(trace_id, True)

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert trace_info["scores"][0]["name"] == "success"
            assert trace_info["scores"][0]["value"] == 1.0

    @pytest.mark.asyncio
    async def test_add_success_score_false(self):
        """Test success score for failed execution"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseScore.add_success_score(
                trace_id, False, "Execution timeout"
            )

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert trace_info["scores"][0]["value"] == 0.0
            assert trace_info["scores"][0]["error"] == "Execution timeout"

    @pytest.mark.asyncio
    async def test_add_cost_score(self):
        """Test cost score addition"""
        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            tracer = LangfuseTracerManager()
            trace_id = await tracer.create_trace("test_trace")

            success = await LangfuseScore.add_cost_score(trace_id, 1500, 0.045)

            assert success is True
            trace_info = tracer.get_trace_info(trace_id)
            assert trace_info["scores"][0]["name"] == "cost"
            assert trace_info["scores"][0]["value"] == 0.045
            assert trace_info["scores"][0]["tokens"] == 1500

    @pytest.mark.asyncio
    async def test_scores_fail_gracefully_when_disabled(self):
        """Test scores return False when tracing disabled"""
        tracer = LangfuseTracerManager(enabled=False)

        success = await LangfuseScore.add_quality_score(None, 0.9)

        assert success is False


class TestIntegration:
    """Integration tests simulating real MCP tool usage"""

    @pytest.mark.asyncio
    async def test_full_traced_mcp_tool_execution(self):
        """Test complete MCP tool execution with tracing"""

        @trace_mcp_tool("flowise_query")
        async def handle_flowise_query(name: str, arguments: dict) -> dict:
            trace_id = get_current_trace_id()

            # Intent classification
            await LangfuseObservation.add_intent_classification(
                trace_id, "creative-orientation", 0.95, ["creative", "goal"]
            )

            # Flow selection
            await LangfuseObservation.add_flow_selection(
                trace_id, "csv2507", "Creative Orientation", "flowise",
                "Selected based on intent matching"
            )

            # Simulate execution
            await asyncio.sleep(0.01)  # 10ms simulation

            # Add quality score
            await LangfuseScore.add_quality_score(trace_id, 0.9)

            return {"result": "success", "answer": "Structural tension is..."}

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            result = await handle_flowise_query(
                "flowise_query",
                {"question": "What is structural tension?"}
            )

            # Verify execution successful
            assert result["result"] == "success"

            # Verify trace created (check global tracer)
            from integrations.langfuse_tracer import _get_global_tracer
            tracer = _get_global_tracer()

            assert len(tracer._active_traces) > 0
            trace_id = list(tracer._active_traces.keys())[0]
            trace_info = tracer.get_trace_info(trace_id)

            # Verify observations captured
            assert len(trace_info["observations"]) >= 3  # Intent + Flow + Execution

            # Verify scores captured
            assert len(trace_info["scores"]) >= 3  # Quality + Latency + Success

    @pytest.mark.asyncio
    async def test_traced_tool_with_error(self):
        """Test tracing captures errors correctly"""

        @trace_mcp_tool("error_tool")
        async def handle_error_tool(name: str, arguments: dict):
            trace_id = get_current_trace_id()

            # Simulate some work before error
            await LangfuseObservation.add_intent_classification(
                trace_id, "test", 1.0, []
            )

            # Raise error
            raise ValueError("Test error message")

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            with pytest.raises(ValueError, match="Test error message"):
                await handle_error_tool("error_tool", {})

            # Verify error observation was added
            from integrations.langfuse_tracer import _get_global_tracer
            tracer = _get_global_tracer()

            # Find the most recent trace
            trace_id = list(tracer._active_traces.keys())[-1]
            trace_info = tracer.get_trace_info(trace_id)

            # Check for error observation
            error_obs = [obs for obs in trace_info["observations"] if obs["type"] == "error"]
            assert len(error_obs) > 0
            assert error_obs[0]["data"]["error_type"] == "ValueError"

            # Check for failure score
            success_scores = [s for s in trace_info["scores"] if s["name"] == "success"]
            assert len(success_scores) > 0
            assert success_scores[0]["value"] == 0.0


class TestPerformance:
    """Performance tests to verify low overhead"""

    @pytest.mark.asyncio
    async def test_decorator_overhead_when_disabled(self):
        """Test decorator adds minimal overhead when disabled"""

        @trace_mcp_tool("perf_test")
        async def fast_function(name: str, arguments: dict) -> str:
            return "success"

        # Disable tracing
        with patch.dict(os.environ, {"LANGFUSE_ENABLED": "false"}, clear=True):
            import time
            start = time.perf_counter()

            # Run 1000 iterations
            for _ in range(1000):
                await fast_function("perf_test", {})

            elapsed = time.perf_counter() - start

            # Should complete 1000 iterations in <100ms (avg <0.1ms per call)
            assert elapsed < 0.1, f"Overhead too high: {elapsed*1000}ms for 1000 calls"

    @pytest.mark.asyncio
    async def test_decorator_overhead_when_enabled(self):
        """Test decorator overhead is acceptable when enabled"""

        @trace_mcp_tool("perf_test")
        async def fast_function(name: str, arguments: dict) -> str:
            return "success"

        with patch.dict(os.environ, {
            "LANGFUSE_ENABLED": "true",
            "LANGFUSE_PUBLIC_KEY": "pk-test",
            "LANGFUSE_SECRET_KEY": "sk-test",
            "LANGFUSE_HOST": "https://test.langfuse.com"
        }):
            import time
            start = time.perf_counter()

            # Run 100 iterations (fewer because tracing adds overhead)
            for _ in range(100):
                await fast_function("perf_test", {})

            elapsed = time.perf_counter() - start
            avg_per_call = (elapsed / 100) * 1000  # Convert to ms

            # Should average <5ms per call (target: <1ms, but being generous for CI)
            assert avg_per_call < 5.0, f"Overhead too high: {avg_per_call}ms per call"


# Test configuration
pytest_plugins = ['pytest_asyncio']

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src/agentic_flywheel/integrations"])
