#!/usr/bin/env python3
"""Agentic Flywheel Configuration Manager
Provides programmatic access to flowise with adaptive configuration
"""

import json
import requests
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
from agentic_flywheel.flowise_manager import FlowiseManager, FlowConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """CLI interface for Agentic Flywheel Configuration Manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Flowise Configuration Manager")
    parser.add_argument("question", help="Question to ask flowise")
    parser.add_argument("--intent", choices=["creative-orientation", "faith2story", "technical-analysis", "document-qa", "miadi46code"], 
                       help="Specify intent explicitly")
    parser.add_argument("--session-id", help="Session ID for conversation continuity")
    parser.add_argument("--flow-override", help="Override automatic flow selection with specific flow ID")
    parser.add_argument("--temperature", type=float, help="Override temperature setting")
    parser.add_argument("--max-tokens", type=int, help="Override max output tokens")
    parser.add_argument("--base-url", default="http://localhost:3222", help="Flowise server URL")
    parser.add_argument("--list-flows", action="store_true", help="List available flows")
    parser.add_argument("--test-connection", action="store_true", help="Test connection to flowise")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    registry = load_flow_registry()
    registry_path = registry.get('metadata', {}).get('registry_path')

    manager = FlowiseManager(base_url=args.base_url, flow_registry_path=registry_path)
    
    if args.list_flows:
        flows = manager.list_flows()
        print(json.dumps(flows, indent=2))
        return
    
    if args.test_connection:
        if manager.test_connection():
            print("✅ Connection to flowise server successful")
        else:
            print("❌ Unable to connect to flowise server")
        return
    
    # Build configuration overrides
    config_override = {}
    if args.temperature is not None:
        config_override["temperature"] = args.temperature
    if args.max_tokens is not None:
        config_override["maxOutputTokens"] = args.max_tokens
    
    # Execute query
    result = manager.adaptive_query(
        question=args.question,
        intent=args.intent,
        session_id=args.session_id,
        flow_override=args.flow_override,
        config_override=config_override if config_override else None
    )
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
        return
    
    # Extract and display response
    response_text = result.get("text") or result.get("answer") or str(result)
    print(response_text)
    
    if args.verbose and "_metadata" in result:
        print("\n" + "="*50)
        print("METADATA:")
        print(json.dumps(result["_metadata"], indent=2))

if __name__ == "__main__":
    main()