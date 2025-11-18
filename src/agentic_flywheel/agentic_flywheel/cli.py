#!/usr/bin/env python3
"""CLI interface for Agentic Flywheel
Dynamic flow management using flow-registry.yaml
"""
import sys
import os


import click
import json
import yaml
import webbrowser

from pathlib import Path
from agentic_flywheel.config_manager import FlowiseManager

def load_flow_registry():
    """Load flows from flow-registry.yaml"""
    # Try package-bundled config first, then fallback to development location
    registry_paths = [
        Path(__file__).parent / "config" / "flow-registry.yaml",  # Package location
        Path(__file__).parent.parent / "flow-registry.yaml"       # Development location
    ]
    
    for registry_path in registry_paths:
        if registry_path.exists():
            with open(registry_path, 'r') as f:
                return yaml.safe_load(f), registry_path
    
    click.echo(f"❌ Flow registry not found. Searched:", err=True)
    for path in registry_paths:
        click.echo(f"   - {path}", err=True)
    sys.exit(1)

def _get_registry_and_path():
    registry, registry_path = load_flow_registry()
    return registry, registry_path

@click.group()
@click.version_option()
def main():
    """Agentic Flywheel - Dynamic Flowise automation with YAML-based flow registry"""
    pass

@main.command()
@click.argument('question')
@click.option('--intent', help='Specify flow intent (use list-flows to see available)')
@click.option('--session-id', help='Session ID for conversation continuity')
@click.option('--flow-override', help='Override automatic flow selection with specific flow ID')
@click.option('--temperature', type=float, help='Override temperature setting')
@click.option('--max-tokens', type=int, help='Override max output tokens')
@click.option('--base-url', help='Flowise server URL (overrides registry config)')
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
def query(question, intent, session_id, flow_override, temperature, max_tokens, base_url, verbose):
    """Query Flowise with intelligent flow selection"""
    
    registry, registry_path = _get_registry_and_path()
    url = base_url or registry['metadata']['base_url']
    manager = FlowiseManager(base_url=url, flow_registry_path=registry_path)
    
    # Build configuration overrides
    config_override = {}
    if temperature is not None:
        config_override["temperature"] = temperature
    if max_tokens is not None:
        config_override["maxOutputTokens"] = max_tokens
    
    # Execute query
    result = manager.adaptive_query(
        question=question,
        intent=intent,
        session_id=session_id,
        flow_override=flow_override,
        config_override=config_override if config_override else None
    )
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    # Extract and display response
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)
    
    if verbose and "_metadata" in result:
        click.echo("\n" + "="*50)
        click.echo("METADATA:")
        click.echo(json.dumps(result["_metadata"], indent=2))

@main.command(name="list-flows")
@click.option('--all', is_flag=True, help='Show all flows including inactive ones')
def list_flows(all):
    """List available flows from registry"""
    registry = load_flow_registry()
    
    click.echo("🔄 OPERATIONAL FLOWS:")
    for flow_key, flow_config in registry.get('operational_flows', {}).items():
        # Filter by active flag unless --all is specified
        if not all and flow_config.get('active', 0) != 1:
            continue
            
        status = flow_config.get('status', 'unknown')
        active = flow_config.get('active', 0)
        status_icon = "✅" if status == "active" and active == 1 else "🚧" if status == "conceptual" else "📁" if status == "archived" else "❓"
        click.echo(f"  {status_icon} {flow_key}: {flow_config['name']}")
        click.echo(f"     ID: {flow_config['id']}")
        click.echo(f"     Keywords: {', '.join(flow_config['intent_keywords'])}")
        if all:
            click.echo(f"     Status: {status}, Active: {active}")
        click.echo()
    
    click.echo("🔀 ROUTING FLOWS:")
    for flow_key, flow_config in registry.get('routing_flows', {}).items():
        # Filter by active flag unless --all is specified
        if not all and flow_config.get('active', 0) != 1:
            continue
            
        status = flow_config.get('status', 'unknown')
        active = flow_config.get('active', 0)
        status_icon = "✅" if status == "active" and active == 1 else "🚧" if status == "conceptual" else "📁" if status == "archived" else "❓"
        click.echo(f"  {status_icon} {flow_key}: {flow_config['name']}")
        click.echo(f"     ID: {flow_config['id']}")
        click.echo(f"     Keywords: {', '.join(flow_config['intent_keywords'])}")
        if all:
            click.echo(f"     Status: {status}, Active: {active}")
        click.echo()

@main.command(name="test-connection")
@click.option('--base-url', help='Flowise server URL (overrides registry config)')
def test_connection(base_url):
    """Test connection to Flowise server"""
    registry, registry_path = _get_registry_and_path()
    url = base_url or registry['metadata']['base_url']
    
    manager = FlowiseManager(base_url=url, flow_registry_path=registry_path)
    if manager.test_connection():
        click.echo(f"✅ Connection to {url} successful")
    else:
        click.echo(f"❌ Unable to connect to {url}", err=True)
        sys.exit(1)

@main.command(name="flow")
@click.argument('flow_name')
@click.argument('question')
@click.option('--session-id', help='Session ID for conversation continuity')
def flow(flow_name, question, session_id):
    """Query specific flow by name from registry"""
    registry, registry_path = _get_registry_and_path()
    
    # Find flow in registry
    all_flows = {**registry.get('operational_flows', {}), **registry.get('routing_flows', {})}
    if flow_name not in all_flows:
        click.echo(f"❌ Flow '{flow_name}' not found in registry", err=True)
        click.echo("Available active flows:")
        for name, config in all_flows.items():
            if config.get('active', 0) == 1:
                click.echo(f"  - {name}")
        sys.exit(1)
    
    manager = FlowiseManager(base_url=registry['metadata']['base_url'], flow_registry_path=registry_path)
    result = manager.adaptive_query(question, intent=flow_name, session_id=session_id)
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)

@main.command(name="add-flow")
@click.argument('new_flow_id')
@click.argument('flow_name')
@click.argument('description')
@click.option('--keywords', help='Comma-separated intent keywords')
@click.option('--temperature', type=float, default=0.7, help='Default temperature')
def add_flow(new_flow_id, flow_name, description, keywords, temperature):
    """Add new flow to registry"""
    registry_path = Path(__file__).parent.parent / "flow-registry.yaml"
    registry = load_flow_registry()
    
    # Create flow key from name
    flow_key = flow_name.lower().replace(' ', '-').replace('_', '-')
    
    # Build new flow config
    new_flow = {
        'id': new_flow_id,
        'name': flow_name,
        'description': description,
        'purpose': f"Purpose for {flow_name}",
        'session_format': f"chat:{flow_key}:{{uuid}}",
        'config': {
            'temperature': temperature,
            'maxOutputTokens': 2000,
            'rephrasePrompt': f"Transform this into a {flow_name.lower()} inquiry: {{question}}",
            'responsePrompt': f"Provide guidance for {flow_name.lower()}: {{context}}"
        },
        'intent_keywords': keywords.split(',') if keywords else [flow_key],
        'status': 'active'
    }
    
    # Add to operational flows
    if 'operational_flows' not in registry:
        registry['operational_flows'] = {}
    registry['operational_flows'][flow_key] = new_flow
    
    # Save back to file
    with open(registry_path, 'w') as f:
        yaml.dump(registry, f, default_flow_style=False, sort_keys=False)
    
    click.echo(f"✅ Added flow '{flow_key}' to registry")
    click.echo(f"   ID: {new_flow_id}")
    click.echo(f"   Keywords: {', '.join(new_flow['intent_keywords'])}")

# Quick flow shortcuts
@main.command(name="creative")
@click.argument('question')
@click.option('--session-id', help='Session ID for conversation continuity')
def creative_shortcut(question, session_id):
    """Quick access to creative-orientation flow"""
    registry, registry_path = _get_registry_and_path()
    manager = FlowiseManager(base_url=registry['metadata']['base_url'], flow_registry_path=registry_path)
    result = manager.adaptive_query(question, intent="creative-orientation", session_id=session_id)
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)

@main.command(name="faith")
@click.argument('question')
@click.option('--session-id', help='Session ID for conversation continuity')
def faith_shortcut(question, session_id):
    """Quick access to faith2story flow"""
    registry, registry_path = _get_registry_and_path()
    manager = FlowiseManager(base_url=registry['metadata']['base_url'], flow_registry_path=registry_path)
    result = manager.adaptive_query(question, intent="faith2story", session_id=session_id)
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)

@main.command(name="research")
@click.argument('question')
@click.option('--session-id', help='Session ID for conversation continuity')
def research_shortcut(question, session_id):
    registry, registry_path = _get_registry_and_path()
    manager = FlowiseManager(base_url=registry['metadata']['base_url'], flow_registry_path=registry_path)
    result = manager.adaptive_query(question, intent="co-agentic-academic-research", session_id=session_id)
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)

@main.command(name="miadi")
@click.argument('question')
@click.option('--session-id', help='Session ID for conversation continuity')
def miadi_shortcut(question, session_id):
    """Quick access to miadi46code flow"""
    registry, registry_path = _get_registry_and_path()
    manager = FlowiseManager(base_url=registry['metadata']['base_url'], flow_registry_path=registry_path)
    result = manager.adaptive_query(question, intent="miadi46code", session_id=session_id)
    
    if "error" in result:
        click.echo(f"❌ Error: {result['error']}", err=True)
        sys.exit(1)
    
    response_text = result.get("text") or result.get("answer") or str(result)
    click.echo(response_text)

@main.command(name="browse")
@click.argument('flow_name', required=False)
@click.option('--base-url', help='Flowise server URL (overrides registry config)')
@click.option('--list', 'list_flows', is_flag=True, help='List available flows for browsing')
@click.option('--canvas', is_flag=True, help='Open in edit mode (canvas) instead of chat mode')
@click.option('--all', is_flag=True, help='Show all flows including inactive ones')
def browse_flow(flow_name, base_url, list_flows, canvas, all):
    """Open flow in browser using pattern: base_url/chatbot/flow_id or base_url/canvas/flow_id"""
    registry, _ = _get_registry_and_path()
    url = base_url or registry['metadata']['base_url']

    # Determine URL pattern based on canvas flag
    url_pattern = "canvas" if canvas else "chatbot"
    mode_description = "edit mode (canvas)" if canvas else "chat mode"

    # List flows if requested
    if list_flows:
        click.echo(f"🌐 Flows available for browsing ({mode_description}):")
        all_flows = {**registry.get('operational_flows', {}), **registry.get('routing_flows', {})}
        for flow_key, flow_config in all_flows.items():
            # Filter by active flag unless --all is specified
            if not all and flow_config.get('active', 0) != 1:
                continue

            status = flow_config.get('status', 'unknown')
            active = flow_config.get('active', 0)
            status_icon = "✅" if status == "active" and active == 1 else "🚧" if status == "conceptual" else "📁" if status == "archived" else "❓"
            click.echo(f"  {status_icon} {flow_key}: {flow_config['name']}")
            browse_url = f"{url}/{url_pattern}/{flow_config['id']}"
            click.echo(f"     URL: {browse_url}")
            click.echo()
        return

    if not flow_name:
        click.echo("❌ Please specify a flow name or use --list to see available flows", err=True)
        click.echo("Usage: jgt-flowise browse <flow_name>")
        click.echo("       jgt-flowise browse --list")
        sys.exit(1)

    # Find flow in registry
    all_flows = {**registry.get('operational_flows', {}), **registry.get('routing_flows', {})}
    if flow_name not in all_flows:
        click.echo(f"❌ Flow '{flow_name}' not found in registry", err=True)
        click.echo("Available active flows:")
        for name, config in all_flows.items():
            if config.get('active', 0) == 1:
                click.echo(f"  - {name}")
        click.echo("\nUse 'jgt-flowise browse --list' for detailed URLs")
        click.echo("Use 'jgt-flowise browse --list --all' to see all flows including inactive ones")
        sys.exit(1)

    flow_config = all_flows[flow_name]
    flow_id = flow_config['id']
    browse_url = f"{url}/{url_pattern}/{flow_id}"

    click.echo(f"🌐 Opening {flow_config['name']} in browser ({mode_description})...")
    click.echo(f"   Flow: {flow_name}")
    click.echo(f"   URL: {browse_url}")

    try:
        webbrowser.open(browse_url)
        click.echo("✅ Browser opened successfully!")
    except Exception as e:
        click.echo(f"❌ Failed to open browser: {e}", err=True)
        click.echo(f"📋 Copy this URL manually: {browse_url}")

main.add_command(browse_flow, name="open")
main.add_command(browse_flow, name="web")

if __name__ == "__main__":
    main()
