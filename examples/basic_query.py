#!/usr/bin/env python3
"""
Basic Query Example - Agentic Flywheel v2.0.0

Demonstrates how to use the universal_query tool with intelligent routing.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agentic_flywheel.tools import handle_universal_query


async def main():
    """Run example queries"""

    print("=" * 60)
    print("Agentic Flywheel - Basic Query Example")
    print("=" * 60)
    print()

    # Check environment
    flowise_url = os.getenv("FLOWISE_BASE_URL")
    langflow_url = os.getenv("LANGFLOW_BASE_URL")

    if not flowise_url or not langflow_url:
        print("❌ Error: Backend URLs not configured")
        print("Please set FLOWISE_BASE_URL and LANGFLOW_BASE_URL")
        print()
        print("Example:")
        print("  export FLOWISE_BASE_URL=http://localhost:3000")
        print("  export LANGFLOW_BASE_URL=http://localhost:7860")
        return

    print(f"✅ Flowise: {flowise_url}")
    print(f"✅ Langflow: {langflow_url}")
    print()

    # Example 1: Creative question (should route to Flowise)
    print("Example 1: Creative Question")
    print("-" * 60)

    result1 = await handle_universal_query("universal_query", {
        "question": "What is structural tension and how does it relate to creative orientation?",
        "backend": "auto",
        "include_routing_metadata": True
    })

    print("Question: What is structural tension?")
    print()
    print("Response:")
    response_text = result1[0]["text"] if isinstance(result1[0], dict) else result1[0].text
    print(response_text)
    print()
    print()

    # Example 2: Technical question (should route to Langflow)
    print("Example 2: Technical Question")
    print("-" * 60)

    result2 = await handle_universal_query("universal_query", {
        "question": "How do I optimize a Python function for better performance?",
        "backend": "auto",
        "include_routing_metadata": True
    })

    print("Question: How do I optimize a Python function?")
    print()
    print("Response:")
    response_text = result2[0]["text"] if isinstance(result2[0], dict) else result2[0].text
    print(response_text)
    print()
    print()

    # Example 3: With session continuity
    print("Example 3: Session Continuity")
    print("-" * 60)

    session_id = "example_session_123"

    result3a = await handle_universal_query("universal_query", {
        "question": "Let's discuss my project goals.",
        "backend": "auto",
        "session_id": session_id
    })

    print(f"Session: {session_id}")
    print("First message: Let's discuss my project goals.")
    print()

    result3b = await handle_universal_query("universal_query", {
        "question": "Can you remind me what we just discussed?",
        "backend": "auto",
        "session_id": session_id
    })

    print("Follow-up: Can you remind me what we just discussed?")
    print()
    print("Response:")
    response_text = result3b[0]["text"] if isinstance(result3b[0], dict) else result3b[0].text
    print(response_text)
    print()
    print()

    # Example 4: Force specific backend
    print("Example 4: Force Specific Backend")
    print("-" * 60)

    result4 = await handle_universal_query("universal_query", {
        "question": "Any question",
        "backend": "flowise",  # Force Flowise
        "include_routing_metadata": True
    })

    print("Backend: flowise (forced)")
    print("Question: Any question")
    print()
    print("Response:")
    response_text = result4[0]["text"] if isinstance(result4[0], dict) else result4[0].text
    print(response_text)
    print()

    print("=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
