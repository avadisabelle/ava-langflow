# 🌟 ava-langflow: Universal Multi-Backend Narrative Router (2025-12-31)

**Reference**: See main unified mission at `/workspace/repos/avadisabelle/ava-langgraph/MISSION_251231.md`

## Your Role in the Stack

ava-langflow is the **Universal Multi-Backend Router** that sits between narrative intelligence and execution backends (Flowise, Langflow, future backends). You're already doing intelligent routing based on intent and performance—now you need to add **narrative awareness** and **three-universe processing**.

## Current Status

✅ **Strengths** (Already Implemented):
- **Universal Backend Abstraction** - Flowise + Langflow support
- **Intelligent Router** (`routing/router.py`) - Performance-based selection
- **Langfuse Creative Archaeology** (`integrations/langfuse_tracer.py`) - 27KB of comprehensive tracing
- **Redis State Integration** (`integrations/redis_state.py`) - Session persistence
- **Cross-Instance Coordination** - Platform consolidation documented

❌ **Gaps** (What Needs to Be Built):
- No narrative-aware routing (routes based on intent keywords, not story position)
- No three-universe perspective processing
- No connection to NCP state
- Not integrated with Miadi-46 webhook events
- Performance tracking doesn't consider narrative quality

## The Three Universes (NEW CONCEPT)

Every event should be interpretable through three lenses:

```
┌─────────────────────────────────────────────────────────────┐
│                        Incoming Query                        │
│  "Handle issue #110: Live Story Monitor feature request"    │
└────────────────────────────┬────────────────────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  ENGINEER WORLD │ │  CEREMONY WORLD │ │ STORY ENGINE    │
│     (Mia)       │ │     (Ava8)      │ │    (Miette)     │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ Intent: FEATURE │ │ Intent: CO-     │ │ Intent: INCITING│
│   _REQUEST      │ │   CREATION      │ │   _INCIDENT     │
│                 │ │                 │ │                 │
│ Route to:       │ │ Route to:       │ │ Route to:       │
│ - tech_analyzer │ │ - relational_   │ │ - narrative_    │
│ - spec_writer   │ │   auditor       │ │   analyzer      │
│ - api_designer  │ │ - sacred_pause  │ │ - arc_tracker   │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

## Integration Tasks for This Codebase

### **Phase 2: Narrative-Aware Routing** (Your Primary Responsibility)

#### Task 1: Three-Universe Handler
**File**: `src/agentic_flywheel/three_universe_handler.py` (NEW)

```python
"""
Process queries through three universe lenses.

Each universe interprets the same event differently:
- Engineer World: Technical schema, API structure, build implications
- Ceremony World: Relational accountability, sacred pause, K'é mapping
- Story Engine World: Narrative function, act position, character arc

The handler determines which universe should "lead" the response
while ensuring all perspectives are recorded.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum

class Universe(Enum):
    ENGINEER = "engineer"
    CEREMONY = "ceremony"
    STORY_ENGINE = "story_engine"

@dataclass
class UniversePerspective:
    universe: Universe
    intent: str
    confidence: float
    suggested_flows: List[str]
    context: Dict[str, Any]
    
@dataclass
class ThreeUniverseAnalysis:
    engineer: UniversePerspective
    ceremony: UniversePerspective
    story_engine: UniversePerspective
    lead_universe: Universe  # Which universe should drive the response
    coherence_score: float  # How well the three perspectives align
    
class ThreeUniverseHandler:
    """Process events through all three universe perspectives"""
    
    def __init__(self, ncp_state_bridge):
        self.ncp_state = ncp_state_bridge
        
    async def analyze(self, query: str, context: Dict[str, Any]) -> ThreeUniverseAnalysis:
        """
        Analyze query from all three universe perspectives.
        
        Example input:
          query: "Issue #110 opened: Live Story Monitor feature request"
          context: {event_type: "issues.opened", repository: "jgwill/Miadi"}
          
        Example output:
          ThreeUniverseAnalysis(
            engineer=UniversePerspective(
              universe=ENGINEER,
              intent="feature_request",
              confidence=0.9,
              suggested_flows=["tech_analyzer", "spec_writer"],
              context={"priority": "HIGH", "files_impacted": [...]}
            ),
            ceremony=UniversePerspective(
              universe=CEREMONY,
              intent="co_creation",
              confidence=0.85,
              suggested_flows=["relational_auditor", "sacred_pause"],
              context={"seven_generation_impact": "HIGH", "ke_relationships": [...]}
            ),
            story_engine=UniversePerspective(
              universe=STORY_ENGINE,
              intent="inciting_incident",
              confidence=0.95,
              suggested_flows=["narrative_analyzer", "arc_tracker"],
              context={"act": 1, "throughline": "Three worlds must learn to see together"}
            ),
            lead_universe=STORY_ENGINE,  # Highest confidence
            coherence_score=0.88
          )
        """
        # Analyze from each perspective
        engineer_view = await self._analyze_engineer(query, context)
        ceremony_view = await self._analyze_ceremony(query, context)
        story_view = await self._analyze_story_engine(query, context)
        
        # Determine lead universe (highest confidence or contextual priority)
        perspectives = [engineer_view, ceremony_view, story_view]
        lead = max(perspectives, key=lambda p: p.confidence)
        
        # Calculate cross-universe coherence
        coherence = self._calculate_coherence(engineer_view, ceremony_view, story_view)
        
        return ThreeUniverseAnalysis(
            engineer=engineer_view,
            ceremony=ceremony_view,
            story_engine=story_view,
            lead_universe=lead.universe,
            coherence_score=coherence
        )
    
    async def _analyze_engineer(self, query: str, context: dict) -> UniversePerspective:
        """Engineer World: Technical precision, structural integrity"""
        # Classify technical intent
        # Suggest technical flows (spec_writer, api_designer, etc.)
        pass
    
    async def _analyze_ceremony(self, query: str, context: dict) -> UniversePerspective:
        """Ceremony World: Relational accountability, sacred technology"""
        # Check for relational implications
        # Suggest ceremonial flows (relational_auditor, ke_mapper, etc.)
        pass
    
    async def _analyze_story_engine(self, query: str, context: dict) -> UniversePerspective:
        """Story Engine World: Narrative function, plot coherence"""
        # Identify narrative function (inciting incident, turning point, etc.)
        # Suggest story flows (arc_analyzer, beat_generator, etc.)
        pass
    
    def _calculate_coherence(self, eng, cer, story) -> float:
        """How well do the three perspectives align?"""
        # Low coherence = universe boundary tension (interesting!)
        # High coherence = converging perspectives
        pass
```

#### Task 2: Narrative-Aware Router Enhancement
**File**: `src/agentic_flywheel/routing/narrative_router.py` (NEW)

```python
"""
Extend the universal router with narrative awareness.

Current router selects backends based on:
- Intent match score
- Health score
- Performance history

New narrative router adds:
- Narrative position (where are we in the story?)
- Universe priority (which lens is leading?)
- Arc coherence (does this advance the character arc?)
- Thematic resonance (does this serve the themes?)
"""

from .router import UniversalQueryRouter, RoutingDecision
from ..three_universe_handler import ThreeUniverseHandler, ThreeUniverseAnalysis

class NarrativeAwareRouter(UniversalQueryRouter):
    """Router that understands narrative context"""
    
    def __init__(self, backends, performance_tracker, ncp_state_bridge):
        super().__init__(backends, performance_tracker)
        self.three_universe = ThreeUniverseHandler(ncp_state_bridge)
        self.ncp_state = ncp_state_bridge
    
    async def route_with_narrative(
        self, 
        query: str, 
        narrative_context: Optional[dict] = None
    ) -> NarrativeRoutingDecision:
        """
        Route query with full narrative awareness.
        
        Steps:
        1. Analyze through three universes
        2. Get current narrative position (from NCP state)
        3. Score backends for narrative fit (not just technical fit)
        4. Select backend + flow that best serves the story
        5. Record decision in trace
        """
        # Get three-universe analysis
        universe_analysis = await self.three_universe.analyze(query, narrative_context or {})
        
        # Get current narrative state
        ncp_state = await self.ncp_state.get_current_state()
        
        # Get flows from lead universe
        suggested_flows = self._get_flows_for_universe(universe_analysis.lead_universe)
        
        # Score backends for narrative fit
        backend_scores = await self._score_backends_narrative(
            query=query,
            universe_analysis=universe_analysis,
            ncp_state=ncp_state
        )
        
        # Select best backend + flow
        decision = self._select_best_narrative_route(backend_scores, suggested_flows)
        
        return NarrativeRoutingDecision(
            backend=decision.backend,
            flow=decision.flow,
            score=decision.score,
            universe_analysis=universe_analysis,
            narrative_position=ncp_state.current_position,
            all_scores=backend_scores
        )
    
    async def _score_backends_narrative(self, query, universe_analysis, ncp_state):
        """Score backends considering narrative context"""
        base_scores = await super()._score_backends(query)
        
        # Adjust scores based on narrative fit
        for score in base_scores:
            # Does this backend serve the current story phase?
            narrative_bonus = self._calculate_narrative_bonus(
                score.backend, 
                universe_analysis,
                ncp_state
            )
            score.composite_score *= (1 + narrative_bonus)
        
        return base_scores
    
    def _calculate_narrative_bonus(self, backend, universe_analysis, ncp_state):
        """
        Calculate bonus for backends that serve narrative goals.
        
        Examples:
        - If we're in Act 2 (confrontation), prefer conflict-deepening flows
        - If ceremony world is leading, prefer relational flows
        - If character arc needs progression, prefer character-focused flows
        """
        bonus = 0.0
        
        # Universe alignment bonus
        if universe_analysis.lead_universe.value in backend.specializations:
            bonus += 0.2
        
        # Narrative phase alignment
        if ncp_state.current_act == 2:  # Confrontation
            if "conflict" in backend.capabilities:
                bonus += 0.15
        
        # Character arc need bonus
        if ncp_state.character_arc_strength < 0.6:
            if "character" in backend.capabilities:
                bonus += 0.1
        
        return bonus
```

#### Task 3: NCP State Bridge Integration
**File**: `src/agentic_flywheel/integrations/narrative_state_bridge.py` (NEW)

```python
"""
Bridge between ava-langflow and the unified narrative state.

Connects to:
- LangGraph Narrative Intelligence Toolkit (NCP schemas)
- Redis state (Miadi-46 compatibility)
- Langfuse tracing (creative archaeology)
"""

from typing import Optional, Dict, Any
from dataclasses import dataclass
import json

# Import from narrative-intelligence if available
try:
    from narrative_intelligence import NCPState, StoryBeat
except ImportError:
    # Fallback to local definitions
    NCPState = Dict[str, Any]
    StoryBeat = Dict[str, Any]

@dataclass
class NarrativePosition:
    """Current position in the narrative"""
    act: int  # 1, 2, or 3
    phase: str  # "setup", "confrontation", "resolution"
    current_beat: Optional[str]
    character_arc_strength: float  # 0-1
    thematic_resonance: float  # 0-1
    emotional_tone: str
    lead_universe: str  # "engineer", "ceremony", "story_engine"

class NCPStateBridge:
    """Bridge to unified narrative state"""
    
    def __init__(self, redis_client, langfuse_tracer=None):
        self.redis = redis_client
        self.tracer = langfuse_tracer
        
    async def get_current_state(self, session_id: Optional[str] = None) -> NCPState:
        """Get current narrative state from Redis"""
        key = f"ncp:state:{session_id}" if session_id else "ncp:state:current"
        state_json = await self.redis.get(key)
        if state_json:
            return json.loads(state_json)
        return self._default_state()
    
    async def get_narrative_position(self, session_id: Optional[str] = None) -> NarrativePosition:
        """Get current position in the narrative journey"""
        state = await self.get_current_state(session_id)
        
        return NarrativePosition(
            act=state.get("current_act", 1),
            phase=state.get("current_phase", "setup"),
            current_beat=state.get("current_beat_id"),
            character_arc_strength=state.get("character_arc_strength", 0.5),
            thematic_resonance=state.get("thematic_resonance", 0.5),
            emotional_tone=state.get("emotional_tone", "neutral"),
            lead_universe=state.get("lead_universe", "story_engine")
        )
    
    async def update_with_routing_decision(
        self, 
        decision,  # NarrativeRoutingDecision
        result: Dict[str, Any]
    ):
        """Update narrative state with routing decision and result"""
        state = await self.get_current_state()
        
        # Record the routing decision
        state.setdefault("routing_history", []).append({
            "backend": decision.backend.name,
            "flow": decision.flow.name,
            "universe_analysis": {
                "lead": decision.universe_analysis.lead_universe.value,
                "coherence": decision.universe_analysis.coherence_score
            },
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Update character arc if result affects it
        if "character_impact" in result:
            state["character_arc_strength"] = min(1.0, 
                state.get("character_arc_strength", 0.5) + result["character_impact"]
            )
        
        # Save updated state
        await self.redis.set("ncp:state:current", json.dumps(state))
        
        # Log to Langfuse if available
        if self.tracer:
            await self.tracer.log_routing_decision(decision, result)
    
    def _default_state(self) -> NCPState:
        """Default narrative state for new sessions"""
        return {
            "current_act": 1,
            "current_phase": "setup",
            "current_beat_id": None,
            "character_arc_strength": 0.5,
            "thematic_resonance": 0.5,
            "emotional_tone": "neutral",
            "lead_universe": "story_engine",
            "routing_history": [],
            "beats": []
        }
```

#### Task 4: Langfuse Tracer Enhancement
**File**: `src/agentic_flywheel/integrations/langfuse_tracer.py` (ENHANCE)

Add narrative-specific tracing events:

```python
# Add to existing LangfuseObservation class:

class NarrativeObservation:
    """Narrative-specific observations for Langfuse tracing"""
    
    @staticmethod
    async def add_universe_analysis(
        trace_id: str,
        analysis: 'ThreeUniverseAnalysis'
    ):
        """Log three-universe analysis results"""
        await LangfuseObservation.add_decision_point(
            trace_id=trace_id,
            decision_type="three_universe_analysis",
            context={
                "engineer": {
                    "intent": analysis.engineer.intent,
                    "confidence": analysis.engineer.confidence,
                    "suggested_flows": analysis.engineer.suggested_flows
                },
                "ceremony": {
                    "intent": analysis.ceremony.intent,
                    "confidence": analysis.ceremony.confidence,
                    "suggested_flows": analysis.ceremony.suggested_flows
                },
                "story_engine": {
                    "intent": analysis.story_engine.intent,
                    "confidence": analysis.story_engine.confidence,
                    "suggested_flows": analysis.story_engine.suggested_flows
                },
                "lead_universe": analysis.lead_universe.value,
                "coherence_score": analysis.coherence_score
            }
        )
    
    @staticmethod
    async def add_narrative_routing(
        trace_id: str,
        decision: 'NarrativeRoutingDecision',
        narrative_position: 'NarrativePosition'
    ):
        """Log narrative-aware routing decision"""
        await LangfuseObservation.add_decision_point(
            trace_id=trace_id,
            decision_type="narrative_routing",
            context={
                "backend": decision.backend.name,
                "flow": decision.flow.name,
                "narrative_score": decision.score,
                "act": narrative_position.act,
                "phase": narrative_position.phase,
                "character_arc_strength": narrative_position.character_arc_strength,
                "lead_universe": narrative_position.lead_universe
            }
        )
    
    @staticmethod
    async def add_beat_created(
        trace_id: str,
        beat: 'StoryBeat',
        source: str
    ):
        """Log new story beat creation"""
        await LangfuseObservation.add_decision_point(
            trace_id=trace_id,
            decision_type="beat_created",
            context={
                "beat_id": beat.id,
                "emotional_tone": beat.emotional_tone,
                "universe_perspectives": beat.perspectives,
                "source": source
            }
        )
```

## Integration with Miadi-46

Your role is to receive webhook events that Miadi-46 transforms and route them to appropriate backends:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Miadi-46 Webhook ETL                             │
│    (Receives GitHub events, transforms to agent-friendly format)        │
└─────────────────────────────────┬────────────────────────────────────────┘
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          ava-langflow                                    │
│              (Universal Multi-Backend Narrative Router)                 │
│                                                                          │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐         │
│  │   Three     │───▶│  Narrative-     │───▶│   Backend       │         │
│  │  Universe   │    │  Aware Router   │    │  Selection      │         │
│  │  Handler    │    │                 │    │  (Flowise/LF)   │         │
│  └─────────────┘    └─────────────────┘    └─────────────────┘         │
│         │                    │                     │                    │
│         │         ┌──────────▼──────────┐          │                    │
│         └────────▶│   Langfuse Trace    │◀─────────┘                    │
│                   │  (Full journey log) │                               │
│                   └─────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │  Flowise / Langflow     │
                    │  (Execute specialized   │
                    │   flows per universe)   │
                    └─────────────────────────┘
```

## Development Checklist

### Phase 2 Tasks (Your Primary)
- [ ] Create `three_universe_handler.py`
  - [ ] Universe analysis logic
  - [ ] Perspective classification
  - [ ] Coherence calculation

- [ ] Create `routing/narrative_router.py`
  - [ ] Extend UniversalQueryRouter
  - [ ] Add narrative scoring
  - [ ] Universe-aware flow selection

- [ ] Create `integrations/narrative_state_bridge.py`
  - [ ] Redis integration for NCP state
  - [ ] Position tracking
  - [ ] State updates after routing

- [ ] Enhance `integrations/langfuse_tracer.py`
  - [ ] Three-universe events
  - [ ] Narrative routing events
  - [ ] Beat creation events

### Phase 5 Tasks (Miadi-46 Integration)
- [ ] Create webhook event receiver
- [ ] Transform GitHub events to narrative queries
- [ ] Route through three-universe handler
- [ ] Return results to Miadi-46 API

## Testing Strategy

```python
# Test 1: Three-universe analysis
analysis = await handler.analyze(
    query="Issue #110 opened: Live Story Monitor",
    context={"event_type": "issues.opened"}
)
assert analysis.story_engine.intent == "inciting_incident"
assert analysis.lead_universe == Universe.STORY_ENGINE

# Test 2: Narrative-aware routing
decision = await router.route_with_narrative(
    query="How should we implement this feature?",
    narrative_context={"act": 2, "phase": "confrontation"}
)
assert decision.backend.supports("conflict_deepening")

# Test 3: State bridge integration
state = await bridge.get_current_state()
await bridge.update_with_routing_decision(decision, result)
updated = await bridge.get_current_state()
assert len(updated["routing_history"]) > len(state["routing_history"])
```

## Success Criteria

- [ ] Every query analyzed from three universe perspectives
- [ ] Routing decisions consider narrative position
- [ ] Lead universe determines flow selection priority
- [ ] All decisions traced in Langfuse with universe metadata
- [ ] Redis state updated with each routing decision
- [ ] Integration with Miadi-46 webhook events working

## Key Files Summary

| File | Status | Purpose |
|------|--------|---------|
| `routing/router.py` | ✅ Exists | Universal query router |
| `routing/narrative_router.py` | 🔴 NEW | Narrative-aware extension |
| `three_universe_handler.py` | 🔴 NEW | Process all 3 perspectives |
| `integrations/langfuse_tracer.py` | ✅ Enhance | Add narrative events |
| `integrations/redis_state.py` | ✅ Exists | State persistence |
| `integrations/narrative_state_bridge.py` | 🔴 NEW | NCP state access |

---

**Last Updated**: 2025-12-31
**Your Focus**: Making routing narrative-aware with three-universe processing
**Success Metric**: Every routing decision considers which universe should lead
**Downstream Consumer**: Miadi-46 platform (GitHub webhook events)


