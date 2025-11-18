#!/usr/bin/env python3
"""
CLI tool for testing the Agentic Flywheel persona system
"""

import asyncio
import click
import json
from . import AgenticFlywheel, PersonaPromptGenerator, PersonaType, FlowiseIntegrationHelper


@click.group()
def cli():
    """Agentic Flywheel CLI - Test the persona system"""
    pass


@cli.command()
@click.argument('query')
@click.option('--session-id', help='Optional session ID')
@click.option('--context', help='JSON context string')
@click.option('--output', help='Output file for results')
def cycle(query, session_id, context, output):
    """Execute a complete flywheel cycle with all four personas."""
    
    async def run_cycle():
        flywheel = AgenticFlywheel()
        
        # Parse context if provided
        context_dict = None
        if context:
            try:
                context_dict = json.loads(context)
            except json.JSONDecodeError:
                click.echo("❌ Invalid JSON in context parameter", err=True)
                return
        
        click.echo(f"🔄 Starting flywheel cycle for: {query}")
        click.echo("=" * 60)
        
        result = await flywheel.execute_flywheel_cycle(
            input_query=query,
            session_id=session_id,
            context=context_dict
        )
        
        click.echo(f"✅ Cycle completed!")
        click.echo(f"Session ID: {result.session_id}")
        click.echo(f"Cycle Number: {result.cycle_number}")
        click.echo()
        
        # Display persona outputs
        for persona_type, persona_output in result.persona_outputs.items():
            click.echo(f"🎭 {persona_type.value.upper()}:")
            click.echo(f"   Analysis: {persona_output.analysis[:200]}...")
            click.echo(f"   Key Insights: {len(persona_output.key_insights)}")
            click.echo(f"   Questions: {len(persona_output.questions_generated)}")
            click.echo()
        
        # Display synthesis
        click.echo("🔗 SYNTHESIS:")
        click.echo(f"   Key Themes: {result.synthesis.get('key_themes', [])}")
        click.echo(f"   Emergent Insights: {len(result.emergent_insights)}")
        click.echo()
        
        # Display emergent insights
        click.echo("💡 EMERGENT INSIGHTS:")
        for insight in result.emergent_insights:
            click.echo(f"   - {insight}")
        click.echo()
        
        click.echo(f"🔄 Next Cycle Input: {result.next_cycle_input}")
        
        # Save to file if requested
        if output:
            with open(output, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
            click.echo(f"💾 Results saved to {output}")
    
    asyncio.run(run_cycle())


@cli.command() 
def personas():
    """List all available personas with their descriptions."""
    flywheel = AgenticFlywheel()
    personas = flywheel.initialize_personas()
    
    click.echo("🎭 Available Personas:")
    click.echo("=" * 50)
    
    for persona_type, description in personas.items():
        click.echo(f"\n{persona_type.value.upper()}")
        click.echo(f"Description: {description}")
        
        # Show prompt sample
        generator = PersonaPromptGenerator()
        if persona_type == PersonaType.STRUCTURAL_DIAGNOSTICIAN:
            sample_prompt = generator.get_structural_diagnostician_prompt("sample query")
        elif persona_type == PersonaType.NARRATIVE_ALCHEMIST:
            sample_prompt = generator.get_narrative_alchemist_prompt("sample query")
        elif persona_type == PersonaType.CEREMONIAL_RESEARCHER:
            sample_prompt = generator.get_ceremonial_researcher_prompt("sample query")
        elif persona_type == PersonaType.CREATIVE_ARCHITECT:
            sample_prompt = generator.get_creative_architect_prompt("sample query")
        
        click.echo(f"Sample prompt: {sample_prompt[:150]}...")


@cli.command()
@click.argument('persona_name')
@click.argument('query')
def persona(persona_name, query):
    """Test a single persona with a query."""
    
    try:
        persona_type = PersonaType(persona_name.lower())
    except ValueError:
        click.echo(f"❌ Invalid persona: {persona_name}")
        click.echo("Available personas: structural_diagnostician, narrative_alchemist, ceremonial_researcher, creative_architect")
        return
    
    generator = PersonaPromptGenerator()
    
    if persona_type == PersonaType.STRUCTURAL_DIAGNOSTICIAN:
        prompt = generator.get_structural_diagnostician_prompt(query)
    elif persona_type == PersonaType.NARRATIVE_ALCHEMIST:
        prompt = generator.get_narrative_alchemist_prompt(query)
    elif persona_type == PersonaType.CEREMONIAL_RESEARCHER:
        prompt = generator.get_ceremonial_researcher_prompt(query)
    elif persona_type == PersonaType.CREATIVE_ARCHITECT:
        prompt = generator.get_creative_architect_prompt(query)
    
    click.echo(f"🎭 {persona_type.value.upper()} PROMPT:")
    click.echo("=" * 60)
    click.echo(prompt)


@cli.command()
def tiers():
    """Show available system tiers."""
    from agentic_flywheel import print_tier_status
    print_tier_status()


@cli.command()
@click.option('--test-connection', is_flag=True, help='Test connection to Flowise server')
@click.option('--query', help='Query the example flow')
@click.option('--max-messages', default=5, help='Maximum messages for the flow')
def flowise(test_connection, query, max_messages):
    """Test integration with user's Flowise server at beagle-emerging-gnu.ngrok-free.app."""
    
    async def run_flowise_test():
        helper = FlowiseIntegrationHelper()
        
        if test_connection:
            click.echo("🔗 Testing connection to beagle-emerging-gnu.ngrok-free.app...")
            result = await helper.test_connection()
            click.echo(f"Status: {result['status']}")
            if result['status'] == 'connected':
                click.echo(f"✅ Connected! Flows available: {result.get('flows_available', 'Unknown')}")
            else:
                click.echo(f"❌ Connection failed: {result.get('message', 'Unknown error')}")
        
        if query:
            click.echo(f"\n🚀 Querying example flow with: '{query}'")
            result = await helper.query_example_flow(query, max_messages)
            click.echo(f"Status: {result['status']}")
            if result['status'] == 'success':
                response_text = result['response'].get('text', 'No text response')
                click.echo(f"✅ Response: {response_text[:300]}...")
            else:
                click.echo(f"❌ Query failed: {result.get('message', 'Unknown error')}")
        
        if not test_connection and not query:
            click.echo("Use --test-connection to test server connection")
            click.echo("Use --query 'your question' to query the example flow")
    
    asyncio.run(run_flowise_test())


if __name__ == '__main__':
    cli()