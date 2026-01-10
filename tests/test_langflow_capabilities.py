#!/usr/bin/env python3
"""
Tests for Langflow Backend Capability Inference

Verifies that the Langflow backend can intelligently infer:
- Intent keywords from flow structure
- Capabilities from graph nodes
- Input/output types from components
"""

import pytest
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from agentic_flywheel.backends.langflow import LangflowBackend
from agentic_flywheel.backends import BackendType


class TestLangflowCapabilityInference:
    """Test intelligent capability inference from Langflow flow structures"""

    def test_rag_flow_detection(self):
        """Test detection of RAG capabilities from flow structure"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        # Mock flow with vector store and retriever
        mock_flow = {
            "id": "rag_flow_123",
            "name": "Document RAG Flow",
            "description": "Retrieval augmented generation with vector search",
            "data": {
                "nodes": [
                    {"type": "VectorStoreRetriever", "data": {}},
                    {"type": "ChatLLM", "data": {}},
                    {"type": "EmbeddingNode", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify RAG capabilities detected
        assert "rag" in universal_flow.capabilities
        assert "retrieval" in universal_flow.capabilities
        assert "chat" in universal_flow.capabilities

        # Verify intent keywords
        assert "rag" in universal_flow.intent_keywords
        assert "search" in universal_flow.intent_keywords

    def test_agent_flow_detection(self):
        """Test detection of agent capabilities"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "agent_flow_456",
            "name": "Autonomous Agent",
            "description": "Agent with tool use capabilities",
            "data": {
                "nodes": [
                    {"type": "AgentNode", "data": {}},
                    {"type": "ToolNode", "data": {}},
                    {"type": "LLMNode", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify agent capabilities
        assert "agent" in universal_flow.capabilities
        assert "autonomous" in universal_flow.capabilities
        assert "tool-use" in universal_flow.capabilities

        # Verify intent keywords
        assert "agent" in universal_flow.intent_keywords
        assert "tools" in universal_flow.intent_keywords

    def test_code_execution_detection(self):
        """Test detection of code execution capabilities"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "code_flow_789",
            "name": "Code Analysis Flow",
            "description": "Generate and execute Python code for analysis",
            "data": {
                "nodes": [
                    {"type": "PythonCodeNode", "data": {}},
                    {"type": "LLMNode", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify code execution capabilities
        assert "code-execution" in universal_flow.capabilities
        assert "chat" in universal_flow.capabilities

        # Verify intent keywords
        assert "code" in universal_flow.intent_keywords
        assert "generation" in universal_flow.intent_keywords

    def test_multi_capability_flow(self):
        """Test flow with multiple capabilities"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "complex_flow_999",
            "name": "Complex Multi-Step Agent",
            "description": "Multi-step agent with RAG, tools, and memory",
            "data": {
                "nodes": [
                    {"type": "AgentNode", "data": {}},
                    {"type": "VectorStoreRetriever", "data": {}},
                    {"type": "ToolNode", "data": {}},
                    {"type": "MemoryBuffer", "data": {}},
                    {"type": "LLMNode", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify all capabilities detected
        assert "agent" in universal_flow.capabilities
        assert "autonomous" in universal_flow.capabilities
        assert "rag" in universal_flow.capabilities
        assert "retrieval" in universal_flow.capabilities
        assert "tool-use" in universal_flow.capabilities
        assert "memory" in universal_flow.capabilities
        assert "multi-step" in universal_flow.capabilities
        assert "chat" in universal_flow.capabilities

    def test_input_output_type_detection(self):
        """Test detection of special input/output types"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "io_flow_111",
            "name": "Multi-Modal Flow",
            "description": "Flow with file and structured I/O",
            "data": {
                "nodes": [
                    {"type": "FileInputNode", "data": {}},
                    {"type": "ImageProcessorNode", "data": {}},
                    {"type": "JSONOutputNode", "data": {}},
                    {"type": "StreamingOutput", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify input types
        assert "text" in universal_flow.input_types  # Default
        assert "file" in universal_flow.input_types
        assert "image" in universal_flow.input_types
        assert "json" in universal_flow.input_types

        # Verify output types
        assert "text" in universal_flow.output_types  # Default
        assert "structured" in universal_flow.output_types
        assert "stream" in universal_flow.output_types

    def test_intent_keyword_extraction_from_name(self):
        """Test intent keyword extraction from flow name and description"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "qa_flow_222",
            "name": "Question Answering System",
            "description": "Chat-based QA with document retrieval and summary",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify keywords extracted from text
        assert "question" in universal_flow.intent_keywords
        assert "chat" in universal_flow.intent_keywords
        assert "rag" in universal_flow.intent_keywords
        assert "summarize" in universal_flow.intent_keywords

    def test_minimal_flow_defaults(self):
        """Test that minimal flows get sensible defaults"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "minimal_flow_333",
            "name": "Simple Flow",
            "description": "Basic flow",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify defaults
        assert "chat" in universal_flow.capabilities  # Always includes chat
        assert "text" in universal_flow.input_types  # Always accepts text
        assert "text" in universal_flow.output_types  # Always produces text
        assert universal_flow.backend == BackendType.LANGFLOW
        assert universal_flow.backend_specific_id == "minimal_flow_333"
        assert universal_flow.id == "langflow_minimal_flow_333"

    def test_streaming_flow_detection(self):
        """Test detection of streaming capabilities from description"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "stream_flow_444",
            "name": "Streaming Chat",
            "description": "Streaming response generation for real-time chat",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        # Verify streaming capability detected from description
        assert "streaming" in universal_flow.capabilities


class TestLangflowIntentClassification:
    """Test intent classification for routing purposes"""

    def test_creative_intent_detection(self):
        """Test detection of creative/generation intents"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "creative_flow",
            "name": "Creative Story Generator",
            "description": "Generate creative stories and narratives",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        assert "generation" in universal_flow.intent_keywords

    def test_analysis_intent_detection(self):
        """Test detection of analysis intents"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "analysis_flow",
            "name": "Data Analyzer",
            "description": "Analyze and evaluate data patterns",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        assert "analysis" in universal_flow.intent_keywords

    def test_translation_intent_detection(self):
        """Test detection of translation intents"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        mock_flow = {
            "id": "translation_flow",
            "name": "Language Translator",
            "description": "Translate text between languages",
            "data": {"nodes": []}
        }

        universal_flow = backend.to_universal_flow(mock_flow)

        assert "translation" in universal_flow.intent_keywords


@pytest.mark.asyncio
class TestLangflowIntegrationWithUniversalQuery:
    """Test Langflow integration with universal query routing"""

    async def test_langflow_flow_routing(self):
        """Test that Langflow flows are properly routed based on capabilities"""
        backend = LangflowBackend(base_url="http://localhost:7860")

        # Create mock RAG flow
        rag_flow = {
            "id": "rag_test_flow",
            "name": "Document Search",
            "description": "Search documents using RAG",
            "data": {
                "nodes": [
                    {"type": "VectorStoreRetriever", "data": {}},
                    {"type": "ChatLLM", "data": {}}
                ]
            }
        }

        universal_flow = backend.to_universal_flow(rag_flow)

        # Verify flow can be matched for RAG queries
        assert "rag" in universal_flow.capabilities
        assert "search" in universal_flow.intent_keywords
        assert universal_flow.backend == BackendType.LANGFLOW

        # This flow should match queries like:
        # "Search the documents for information about X"
        # "Find references to Y in the knowledge base"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
