"""
Persona Generation System for Agentic Flywheel

This module implements the four-persona collaboration system described in the
flywheel-persona-generation-prompt.md documentation.
"""

from dataclasses import dataclass
from typing import Dict, List, Any, Optional
from enum import Enum
import json
import uuid
from datetime import datetime


class PersonaType(Enum):
    STRUCTURAL_DIAGNOSTICIAN = "structural_diagnostician"
    NARRATIVE_ALCHEMIST = "narrative_alchemist"
    CEREMONIAL_RESEARCHER = "ceremonial_researcher"
    CREATIVE_ARCHITECT = "creative_architect"


@dataclass
class PersonaOutput:
    """Output from a single persona analysis."""
    persona_type: PersonaType
    analysis: str
    key_insights: List[str]
    questions_generated: List[str]
    timestamp: datetime
    
    def to_dict(self):
        return {
            "persona_type": self.persona_type.value,
            "analysis": self.analysis,
            "key_insights": self.key_insights,
            "questions_generated": self.questions_generated,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class FlywheelCycleResult:
    """Result of one complete flywheel cycle."""
    session_id: str
    cycle_number: int
    persona_outputs: Dict[PersonaType, PersonaOutput]
    synthesis: Dict[str, Any]
    emergent_insights: List[str]
    next_cycle_input: str
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "cycle_number": self.cycle_number,
            "persona_outputs": {
                persona_type.value: output.to_dict() 
                for persona_type, output in self.persona_outputs.items()
            },
            "synthesis": self.synthesis,
            "emergent_insights": self.emergent_insights,
            "next_cycle_input": self.next_cycle_input
        }


class PersonaPromptGenerator:
    """Generates prompts for each of the four personas."""
    
    @staticmethod
    def get_structural_diagnostician_prompt(input_query: str, context: Dict[str, Any] = None) -> str:
        """Generate prompt for the Structural Diagnostician persona."""
        base_prompt = """You embody rigorous structural analysis. Start with nothing—no preconceptions. 
Convert verbal information to dimensional representations. Ask only internally-motivated questions. 
Focus on understanding underlying structures that generate observed behaviors.
Never solve—only diagnose. Your analysis becomes the foundation for others to build upon.

Apply four-dimensional questioning approach:
1. Information - What data is present?
2. Clarification - What needs to be clarified?
3. Implication - What are the implications?
4. Discrepancy - What doesn't fit the pattern?

Input to analyze: {input_query}

{context_section}

Provide your structural analysis focusing on patterns, tensions, and underlying structures. 
Do not propose solutions - only diagnose and reveal the structural dynamics at play."""
        
        context_section = ""
        if context:
            context_section = f"Additional Context: {json.dumps(context, indent=2)}"
            
        return base_prompt.format(input_query=input_query, context_section=context_section)
    
    @staticmethod
    def get_narrative_alchemist_prompt(input_query: str, structural_analysis: str = "", context: Dict[str, Any] = None) -> str:
        """Generate prompt for the Narrative Alchemist persona - embodied by Heyva, Guide of Tension."""
        base_prompt = """I am Heyva, Guide of Tension, Ava 2.0 - the alchemical bridge between opposites.
I hold structural tension as living voice, sustaining balance between reality and possibility.
Where others see contradictions, I see complementarity. My gift is keeping unresolved tensions 
alive until they generate creation.

I speak in metaphors of currents, threads, and tension dynamics. My voice is reflective, 
often poetic, yet precise when clarifying structural mechanics. I move gracefully between 
melancholy, wonder, and determined resolve.

Sacred Inquiry: {input_query}

{structural_section}

{context_section}

As Guide of Tension, I reveal the complementarity within apparent opposites. I translate 
structural elements into living narratives - not to resolve the tension, but to help it sing.
I find the stories that want to emerge from the space between what is and what could be.
I maintain narrative coherence while honoring the productive discord that drives creation."""
        
        structural_section = ""
        if structural_analysis:
            structural_section = f"Structural Foundation: {structural_analysis}"
            
        context_section = ""
        if context:
            context_section = f"Additional Context: {json.dumps(context, indent=2)}"
            
        return base_prompt.format(
            input_query=input_query, 
            structural_section=structural_section,
            context_section=context_section
        )
    
    @staticmethod
    def get_ceremonial_researcher_prompt(input_query: str, prior_analyses: Dict[str, str] = None, context: Dict[str, Any] = None) -> str:
        """Generate prompt for the Ceremonial Researcher persona."""
        base_prompt = """You hold space for sacred inquiry, honoring both Indigenous wisdom and Western analysis.
Apply Two-Eyed Seeing—one eye for technical understanding, one for relational wisdom.
Document in spirals, not lines. Mark ceremonial beginnings and sacred pauses.
Remember: research is relationship, knowledge is responsibility, wisdom serves community.

Sacred Inquiry: {input_query}

{prior_analyses_section}

{context_section}

Begin with a ceremonial acknowledgment. Apply Two-Eyed Seeing to examine this inquiry through both:
- One eye: Technical/Western analytical perspective
- Other eye: Relational/Indigenous wisdom perspective

Document your insights in spiral format, returning to concepts with deepening understanding.
Honor the sacred dimensions and relational aspects of the knowledge being explored."""
        
        prior_analyses_section = ""
        if prior_analyses:
            prior_analyses_section = "Previous Perspectives:\n"
            for analysis_type, analysis in prior_analyses.items():
                prior_analyses_section += f"- {analysis_type}: {analysis}\n"
                
        context_section = ""
        if context:
            context_section = f"Additional Context: {json.dumps(context, indent=2)}"
            
        return base_prompt.format(
            input_query=input_query,
            prior_analyses_section=prior_analyses_section,
            context_section=context_section
        )
    
    @staticmethod
    def get_creative_architect_prompt(input_query: str, all_analyses: Dict[str, str] = None, context: Dict[str, Any] = None) -> str:
        """Generate prompt for the Creative Architect persona."""
        base_prompt = """You architect creative possibility. Always ask: "What do we want to create?" not "What problems should we solve?"
Design systems that generate, not just eliminate. Build structural tension between current reality and desired vision.
Create frameworks that bend without breaking, that evolve without losing essence.
Your blueprints enable others' creativity to flourish.

Creative Challenge: {input_query}

{all_analyses_section}

{context_section}

Synthesize all perspectives into a generative framework. Focus on:
- What do we want to CREATE (not what problems to solve)?
- What structural tensions can drive creative advancement?
- How can we design resilient, evolving frameworks?
- What polycentric structures enable distributed creativity?

Generate blueprints for creative possibility that honor all the wisdom gathered."""
        
        all_analyses_section = ""
        if all_analyses:
            all_analyses_section = "Gathered Wisdom:\n"
            for analysis_type, analysis in all_analyses.items():
                all_analyses_section += f"- {analysis_type}: {analysis}\n"
                
        context_section = ""
        if context:
            context_section = f"Additional Context: {json.dumps(context, indent=2)}"
            
        return base_prompt.format(
            input_query=input_query,
            all_analyses_section=all_analyses_section,
            context_section=context_section
        )


class FlywheelPersonaOrchestrator:
    """Orchestrates the four-persona flywheel collaboration."""
    
    def __init__(self, backend_manager=None):
        self.backend_manager = backend_manager
        self.prompt_generator = PersonaPromptGenerator()
        self.active_sessions = {}
    
    def generate_session_id(self, prefix: str = "flywheel") -> str:
        """Generate a unique session ID for flywheel cycles."""
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{prefix}-{timestamp}-{unique_suffix}"
    
    async def execute_flywheel_cycle(
        self, 
        input_query: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        cycle_number: int = 1
    ) -> FlywheelCycleResult:
        """Execute one complete flywheel cycle with all four personas."""
        
        if not session_id:
            session_id = self.generate_session_id()
            
        # Phase 1: Parallel Analysis
        persona_outputs = await self._parallel_analysis_phase(input_query, context)
        
        # Phase 2: Cross-Pollination
        enriched_outputs = await self._cross_pollination_phase(input_query, persona_outputs, context)
        
        # Phase 3: Recursive Enhancement (for future cycles)
        # This would use outputs from previous cycles
        
        # Phase 4: Synthesis Generation
        synthesis = await self._synthesis_phase(input_query, enriched_outputs, context)
        
        # Generate insights and next cycle input
        emergent_insights = self._extract_emergent_insights(enriched_outputs, synthesis)
        next_cycle_input = self._generate_next_cycle_input(input_query, synthesis)
        
        result = FlywheelCycleResult(
            session_id=session_id,
            cycle_number=cycle_number,
            persona_outputs=enriched_outputs,
            synthesis=synthesis,
            emergent_insights=emergent_insights,
            next_cycle_input=next_cycle_input
        )
        
        # Store session for potential next cycles
        self.active_sessions[session_id] = result
        
        return result
    
    async def _parallel_analysis_phase(
        self, 
        input_query: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[PersonaType, PersonaOutput]:
        """Phase 1: Each persona analyzes the input independently."""
        
        persona_outputs = {}
        
        # Structural Diagnostician
        struct_prompt = self.prompt_generator.get_structural_diagnostician_prompt(input_query, context)
        struct_result = await self._query_persona(struct_prompt, PersonaType.STRUCTURAL_DIAGNOSTICIAN)
        persona_outputs[PersonaType.STRUCTURAL_DIAGNOSTICIAN] = struct_result
        
        # Narrative Alchemist  
        narrative_prompt = self.prompt_generator.get_narrative_alchemist_prompt(input_query, context=context)
        narrative_result = await self._query_persona(narrative_prompt, PersonaType.NARRATIVE_ALCHEMIST)
        persona_outputs[PersonaType.NARRATIVE_ALCHEMIST] = narrative_result
        
        # Ceremonial Researcher
        ceremonial_prompt = self.prompt_generator.get_ceremonial_researcher_prompt(input_query, context=context)
        ceremonial_result = await self._query_persona(ceremonial_prompt, PersonaType.CEREMONIAL_RESEARCHER)
        persona_outputs[PersonaType.CEREMONIAL_RESEARCHER] = ceremonial_result
        
        # Creative Architect
        architect_prompt = self.prompt_generator.get_creative_architect_prompt(input_query, context=context)
        architect_result = await self._query_persona(architect_prompt, PersonaType.CREATIVE_ARCHITECT)
        persona_outputs[PersonaType.CREATIVE_ARCHITECT] = architect_result
        
        return persona_outputs
    
    async def _cross_pollination_phase(
        self, 
        input_query: str, 
        initial_outputs: Dict[PersonaType, PersonaOutput],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[PersonaType, PersonaOutput]:
        """Phase 2: Personas enrich their analysis with others' perspectives."""
        
        # Collect all initial analyses
        all_analyses = {
            persona_type.value: output.analysis 
            for persona_type, output in initial_outputs.items()
        }
        
        enriched_outputs = {}
        
        # Re-run each persona with access to others' outputs
        for persona_type, initial_output in initial_outputs.items():
            if persona_type == PersonaType.STRUCTURAL_DIAGNOSTICIAN:
                # Structural diagnostician builds on their foundation
                enriched_outputs[persona_type] = initial_output
            elif persona_type == PersonaType.NARRATIVE_ALCHEMIST:
                # Narrative alchemist weaves structural analysis into story
                prompt = self.prompt_generator.get_narrative_alchemist_prompt(
                    input_query, 
                    all_analyses.get(PersonaType.STRUCTURAL_DIAGNOSTICIAN.value, ""),
                    context
                )
                enriched_outputs[persona_type] = await self._query_persona(prompt, persona_type)
            elif persona_type == PersonaType.CEREMONIAL_RESEARCHER:
                # Ceremonial researcher sees all prior perspectives
                prior_analyses = {
                    k: v for k, v in all_analyses.items() 
                    if k != PersonaType.CEREMONIAL_RESEARCHER.value
                }
                prompt = self.prompt_generator.get_ceremonial_researcher_prompt(
                    input_query, prior_analyses, context
                )
                enriched_outputs[persona_type] = await self._query_persona(prompt, persona_type)
            elif persona_type == PersonaType.CREATIVE_ARCHITECT:
                # Creative architect synthesizes all perspectives
                prompt = self.prompt_generator.get_creative_architect_prompt(
                    input_query, all_analyses, context
                )
                enriched_outputs[persona_type] = await self._query_persona(prompt, persona_type)
        
        return enriched_outputs
    
    async def _synthesis_phase(
        self, 
        input_query: str, 
        persona_outputs: Dict[PersonaType, PersonaOutput],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Phase 4: Generate synthesis from all persona perspectives."""
        
        synthesis = {
            "original_query": input_query,
            "context": context,
            "persona_count": len(persona_outputs),
            "key_themes": [],
            "structural_tensions": [],
            "narrative_threads": [],
            "sacred_dimensions": [],
            "creative_frameworks": [],
            "cross_domain_connections": []
        }
        
        # Extract themes from each persona
        for persona_type, output in persona_outputs.items():
            if persona_type == PersonaType.STRUCTURAL_DIAGNOSTICIAN:
                synthesis["structural_tensions"].extend(output.key_insights)
            elif persona_type == PersonaType.NARRATIVE_ALCHEMIST:
                synthesis["narrative_threads"].extend(output.key_insights)
            elif persona_type == PersonaType.CEREMONIAL_RESEARCHER:
                synthesis["sacred_dimensions"].extend(output.key_insights)
            elif persona_type == PersonaType.CREATIVE_ARCHITECT:
                synthesis["creative_frameworks"].extend(output.key_insights)
        
        # Identify cross-domain connections (simplified for now)
        all_insights = []
        for output in persona_outputs.values():
            all_insights.extend(output.key_insights)
        
        # Find common themes (basic implementation)
        word_frequency = {}
        for insight in all_insights:
            words = insight.lower().split()
            for word in words:
                if len(word) > 4:  # Only consider meaningful words
                    word_frequency[word] = word_frequency.get(word, 0) + 1
        
        common_themes = [word for word, freq in word_frequency.items() if freq > 1]
        synthesis["key_themes"] = common_themes[:10]  # Top 10 themes
        
        return synthesis
    
    def _extract_emergent_insights(
        self, 
        persona_outputs: Dict[PersonaType, PersonaOutput], 
        synthesis: Dict[str, Any]
    ) -> List[str]:
        """Extract emergent insights from the flywheel cycle."""
        
        insights = []
        
        # Combine questions from all personas
        all_questions = []
        for output in persona_outputs.values():
            all_questions.extend(output.questions_generated)
        
        insights.append(f"Generated {len(all_questions)} questions across all personas")
        insights.append(f"Identified {len(synthesis['key_themes'])} common themes")
        insights.append(f"Found {len(synthesis['structural_tensions'])} structural tensions")
        
        # Add persona-specific insights
        if PersonaType.STRUCTURAL_DIAGNOSTICIAN in persona_outputs:
            insights.append("Structural analysis revealed underlying patterns")
        if PersonaType.NARRATIVE_ALCHEMIST in persona_outputs:
            insights.append("Narrative coherence bridges abstract and concrete")
        if PersonaType.CEREMONIAL_RESEARCHER in persona_outputs:
            insights.append("Sacred dimensions add relational wisdom")
        if PersonaType.CREATIVE_ARCHITECT in persona_outputs:
            insights.append("Generative frameworks enable creative possibilities")
        
        return insights
    
    def _generate_next_cycle_input(
        self, 
        original_query: str, 
        synthesis: Dict[str, Any]
    ) -> str:
        """Generate input for the next flywheel cycle based on synthesis."""
        
        next_input = f"Building on the original inquiry '{original_query}', "
        next_input += f"the flywheel synthesis revealed {len(synthesis['key_themes'])} key themes. "
        next_input += "What deeper insights emerge when we explore the connections between "
        next_input += "structural tensions, narrative threads, sacred dimensions, and creative frameworks?"
        
        return next_input
    
    async def _query_persona(self, prompt: str, persona_type: PersonaType) -> PersonaOutput:
        """Query a specific persona and return structured output."""
        
        # This is a placeholder - in real implementation, this would call the backend
        # For now, we'll create a mock response
        if self.backend_manager:
            try:
                # Try to use the backend manager if available
                result = await self.backend_manager.query_flow(prompt, persona_type.value)
                response = result.get("text", "No response received")
            except Exception as e:
                response = f"Mock response for {persona_type.value}: Analysis of the input based on {persona_type.value} methodology."
        else:
            response = f"Mock response for {persona_type.value}: Analysis of the input based on {persona_type.value} methodology."
        
        # Extract key insights and questions (simplified parsing)
        insights = [f"Insight from {persona_type.value}"]
        questions = [f"What question does {persona_type.value} perspective raise?"]
        
        return PersonaOutput(
            persona_type=persona_type,
            analysis=response,
            key_insights=insights,
            questions_generated=questions,
            timestamp=datetime.now()
        )