#!/usr/bin/env python3
"""Agentic Flywheel Flowise Manager
Provides programmatic access to flowise with adaptive configuration
"""

import json
import requests
import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import logging
import yaml
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class FlowConfig:
    """Configuration for a specific flowise flow"""
    id: str
    name: str
    description: str
    default_config: Dict[str, Any]
    intent_keywords: List[str]

class FlowiseManager:
    """Agentic Flywheel Flowise Manager"""
    
    def __init__(self, base_url: str = "https://beagle-emerging-gnu.ngrok-free.app", flow_registry_path: Optional[str] = None):
        self.base_url = base_url
        self.flow_registry_path = flow_registry_path
        self.flows: Dict[str, FlowConfig] = {}
        self._load_flows_from_registry()

    def _load_flows_from_registry(self):
        """Load flows from flow-registry.yaml"""
        registry_paths = []
        if self.flow_registry_path:
            registry_paths.append(Path(self.flow_registry_path))
        
        # Fallback to package-bundled config, then development location
        registry_paths.append(Path(__file__).parent / "config" / "flow-registry.yaml")
        registry_paths.append(Path(__file__).parent.parent / "flow-registry.yaml") # Development location
        
        loaded = False
        for registry_path in registry_paths:
            if registry_path.exists():
                try:
                    with open(registry_path, 'r') as f:
                        registry = yaml.safe_load(f)
                    
                    self.flows = {}
                    for flow_type in ['operational_flows', 'routing_flows']:
                        for flow_key, flow_config in registry.get(flow_type, {}).items():
                            # Only load active flows for FlowiseManager
                            if flow_config.get('active', 0) == 1:
                                self.flows[flow_key] = FlowConfig(
                                    id=flow_config['id'],
                                    name=flow_config['name'],
                                    description=flow_config['description'],
                                    default_config=flow_config.get('config', {}),
                                    intent_keywords=flow_config.get('intent_keywords', [])
                                )
                    logger.info(f"✅ Loaded {len(self.flows)} active flows from YAML registry: {registry_path}")
                    loaded = True
                    break
                except Exception as e:
                    logger.error(f"❌ Failed to load flows from {registry_path}: {e}")
                    continue
        
        if not loaded:
            logger.warning("❌ Flow registry not found. No flows loaded.")

    def generate_session_id(self, prefix: str = "session") -> str:
        """Generate unique session ID"""
        timestamp = int(time.time())
        unique_suffix = str(uuid.uuid4())[:8]
        return f"{prefix}-{timestamp}-{unique_suffix}"
    
    def classify_intent(self, question: str):
        """Classify user intent based on question content"""
        question_lower = question.lower()
        
        # Score each flow based on keyword matches
        scores = {}
        for flow_name, flow_config in self.flows.items():
            score = sum(1 for keyword in flow_config.intent_keywords 
                       if keyword in question_lower)
            scores[flow_name] = score
        
        # Return the flow with highest score, default to creative-orientation
        best_flow = max(scores.items(), key=lambda x: x[1])
        return best_flow[0] if best_flow[1] > 0 else "creative-orientation"
    
    def adaptive_query(self, 
                      question: str, 
                      intent: Optional[str] = None,
                      session_id: Optional[str] = None,
                      flow_override: Optional[str] = None,
                      config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Intelligently route and configure flowise query
        """
        # Determine flow and configuration
        if flow_override:
            flow_config = self._get_flow_by_id(flow_override)
            if not flow_config:
                logger.warning(f"Flow override '{flow_override}' not found, using intent-based selection")
                flow_config = self._select_flow_by_intent(question, intent)
        else:
            flow_config = self._select_flow_by_intent(question, intent)
        
        # Generate session ID if not provided
        if not session_id:
            session_id = self.generate_session_id(flow_config.name.lower().replace(" ", "-"))
        
        # Build configuration
        config = flow_config.default_config.copy()
        config["sessionId"] = session_id
        
        # Apply any configuration overrides
        if config_override:
            config.update(config_override)
        
        # Build payload
        payload = {
            "question": question,
            "overrideConfig": config
        }
        
        logger.info(f"Using flow: {flow_config.name} ({flow_config.id})")
        logger.info(f"Session ID: {session_id}")
        logger.debug(f"Configuration: {json.dumps(config, indent=2)}")
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/prediction/{flow_config.id}",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Add metadata to response
            result["_metadata"] = {
                "flow_used": flow_config.name,
                "flow_id": flow_config.id,
                "session_id": session_id,
                "intent_detected": self.classify_intent(question),
                "config_used": config
            }
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return {
                "error": str(e),
                "flow_attempted": flow_config.name,
                "session_id": session_id
            }
    
    def _get_flow_by_id(self, flow_id: str) -> Optional[FlowConfig]:
        """Get flow configuration by ID"""
        for flow_config in self.flows.values():
            if flow_config.id == flow_id:
                return flow_config
        return None
    
    def _select_flow_by_intent(self, question: str, intent: Optional[str]) -> FlowConfig:
        """Select flow based on intent or question analysis"""
        if intent and intent in self.flows:
            return self.flows[intent]
        
        # Auto-classify intent
        detected_intent = self.classify_intent(question)
        return self.flows[detected_intent]
    
    def list_flows(self) -> Dict[str, Dict[str, Any]]:
        """List available flows with their configurations"""
        return {
            name: {
                "id": config.id,
                "name": config.name,
                "description": config.description,
                "intent_keywords": config.intent_keywords,
                "default_config": config.default_config
            }
            for name, config in self.flows.items()
        }
    
    def test_connection(self) -> bool:
        """Test connection to flowise server"""
        try:
            # Try a simple request to detect server availability
            test_payload = {"question": "test"}
            test_flow = list(self.flows.values())[0]
            
            response = requests.post(
                f"{self.base_url}/api/v1/prediction/{test_flow.id}",
                json=test_payload,
                timeout=5
            )
            return response.status_code in [200, 400, 422]  # Accept various response codes
        except:
            return False

def main():
    """CLI interface for flowise manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Intelligent Flowise Configuration Manager")
    parser.add_argument("question", help="Question to ask flowise")
    parser.add_argument("--intent", choices=["creative-orientation", "faith2story", "technical-analysis", "document-qa"], 
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
    
    manager = FlowiseManager(base_url=args.base_url)
    
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

@dataclass
class DomainContext:
    """Context information for domain-specific interactions"""
    name: str
    description: str
    stack_info: Optional[Dict[str, Any]] = None
    cultural_info: Optional[Dict[str, Any]] = None
    technical_constraints: Optional[List[str]] = None
    specialized_keywords: Optional[List[str]] = None

class ContextBuilder:
    """Build rich context for domain-specific queries"""
    
    @staticmethod
    def build_technical_context(stack_info: Dict[str, Any], feature: str) -> str:
        """Build technical implementation context"""
        stack_details = []
        for key, value in stack_info.items():
            if isinstance(value, list):
                stack_details.append(f"- {key}: {', '.join(value)}")
            else:
                stack_details.append(f"- {key}: {value}")
        
        return f"""
        Technical Implementation Request: {feature}
        
        Current Stack:
        {chr(10).join(stack_details)}
        """
    
    @staticmethod
    def build_cultural_context(domain_info: Dict[str, Any], topic: str) -> str:
        """Build culturally sensitive content context"""
        cultural_details = []
        for key, value in domain_info.items():
            cultural_details.append(f"- {key}: {value}")
        
        return f"""
        Cultural Content Request for topic: "{topic}"
        
        Domain Context:
        {chr(10).join(cultural_details)}
        
        Requirements:
        - Ensure cultural sensitivity and accuracy
        - Provide appropriate context and background
        - Create engaging, respectful content
        """
    
    @staticmethod
    def build_strategic_context(domain_info: Dict[str, Any], focus_area: str) -> str:
        """Build strategic planning context"""
        return f"""
        Strategic Analysis Request: {focus_area}
        
        Domain: {domain_info.get('name', 'Unknown')}
        Description: {domain_info.get('description', 'No description provided')}
        
        Context: {domain_info.get('strategic_context', 'No additional context')}
        """

class DomainSpecificFlowiseManager(FlowiseManager):
    """Extended FlowiseManager with domain expertise and enhanced capabilities"""
    
    def __init__(self, base_url: str = "https://beagle-emerging-gnu.ngrok-free.app", domain_context: Optional[DomainContext] = None):
        super().__init__(base_url)
        self.domain_context = domain_context
        self.working_flows_cache = None
        self.context_builder = ContextBuilder()
        
        # Add domain-specific keywords to intent classification if provided
        if domain_context and domain_context.specialized_keywords:
            self._enhance_intent_keywords(domain_context.specialized_keywords)
    
    def _enhance_intent_keywords(self, specialized_keywords: List[str]):
        """Add domain-specific keywords to existing flows"""
        # Distribute specialized keywords across flows based on relevance
        for flow_name, flow_config in self.flows.items():
            if flow_name == "technical-analysis":
                flow_config.intent_keywords.extend([kw for kw in specialized_keywords if any(tech in kw.lower() for tech in ["implement", "code", "system", "api", "database"])])
            elif flow_name == "creative-orientation":
                flow_config.intent_keywords.extend([kw for kw in specialized_keywords if any(creative in kw.lower() for creative in ["vision", "strategic", "improve", "enhance", "design"])])
            elif flow_name == "faith2story":
                flow_config.intent_keywords.extend([kw for kw in specialized_keywords if any(content in kw.lower() for content in ["content", "story", "cultural", "lesson", "narrative"])])
    
    def discover_working_flows(self) -> Dict[str, bool]:
        """Test all flows to identify which ones are operational"""
        if self.working_flows_cache is not None:
            return self.working_flows_cache
        
        logger.info("Discovering working flows...")
        working_flows = {}
        
        for flow_name, flow_config in self.flows.items():
            is_working = self.test_flow(flow_config.id)
            working_flows[flow_name] = is_working
            
            if is_working:
                logger.info(f"✅ Flow '{flow_name}' is operational")
            else:
                logger.warning(f"❌ Flow '{flow_name}' is not responding")
        
        self.working_flows_cache = working_flows
        return working_flows
    
    def test_flow(self, flow_id: str) -> bool:
        """Test specific flow ID for functionality"""
        try:
            test_payload = {"question": "test connectivity"}
            response = requests.post(
                f"{self.base_url}/api/v1/prediction/{flow_id}",
                json=test_payload,
                timeout=10
            )
            # Consider various response codes as "working"
            return response.status_code in [200, 400, 422, 500]  # Even 500 means server is responding
        except Exception as e:
            logger.debug(f"Flow test failed for {flow_id}: {e}")
            return False
    
    def get_working_flows(self) -> Dict[str, FlowConfig]:
        """Get only the flows that are currently operational"""
        working_status = self.discover_working_flows()
        return {
            name: config for name, config in self.flows.items() 
            if working_status.get(name, False)
        }
    
    def contextualized_query(self,
                           question: str,
                           context_type: str = "general",
                           intent: Optional[str] = None,
                           session_id: Optional[str] = None,
                           config_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query with automatic domain context injection"""
        
        if not self.domain_context:
            # Fall back to regular adaptive_query if no domain context
            return self.adaptive_query(question, intent, session_id, config_override)
        
        # Build contextualized question based on context type
        if context_type == "technical" and self.domain_context.stack_info:
            contextualized_question = self.context_builder.build_technical_context(
                self.domain_context.stack_info, question
            )
        elif context_type == "cultural" and self.domain_context.cultural_info:
            contextualized_question = self.context_builder.build_cultural_context(
                self.domain_context.cultural_info, question
            )
        elif context_type == "strategic":
            domain_info = {
                "name": self.domain_context.name,
                "description": self.domain_context.description,
                "strategic_context": getattr(self.domain_context, 'strategic_context', 'General strategic analysis')
            }
            contextualized_question = self.context_builder.build_strategic_context(
                domain_info, question
            )
        else:
            # General context injection
            context_prefix = f"Domain: {self.domain_context.name}\nDescription: {self.domain_context.description}\n\nQuery: "
            contextualized_question = context_prefix + question
        
        # Generate domain-specific session ID if not provided
        if not session_id and hasattr(self, 'domain_context') and self.domain_context:
            domain_name = self.domain_context.name.lower().replace(" ", "-")
            session_id = self.generate_session_id(f"{domain_name}-{context_type}")
        
        return self.adaptive_query(
            question=contextualized_question,
            intent=intent,
            session_id=session_id,
            config_override=config_override
        )
    
    def classify_intent_with_context(self, question: str) -> str:
        """Enhanced intent classification with domain context"""
        # Use base classification first
        base_intent = self.classify_intent(question)
        
        # If we have domain context, we can enhance the classification
        if self.domain_context and self.domain_context.specialized_keywords:
            question_lower = question.lower()
            
            # Check for domain-specific patterns
            domain_score = sum(1 for keyword in self.domain_context.specialized_keywords 
                             if keyword.lower() in question_lower)
            
            # If domain keywords are present, we might adjust the intent
            if domain_score > 0:
                # Prefer technical-analysis for implementation questions in technical domains
                if any(tech in question_lower for tech in ["implement", "code", "how to", "api", "database"]):
                    return "technical-analysis"
                # Prefer creative-orientation for strategic questions
                elif any(strategy in question_lower for strategy in ["improve", "enhance", "strategy", "vision", "goals"]):
                    return "creative-orientation"
        
        return base_intent
    
    def get_domain_specialized_flows(self) -> Dict[str, FlowConfig]:
        """Get flows that are most relevant to the current domain"""
        if not self.domain_context:
            return self.flows
        
        # Score flows based on domain relevance
        scored_flows = {}
        for name, config in self.flows.items():
            relevance_score = 0
            
            # Check keyword overlap with domain
            if self.domain_context.specialized_keywords:
                keyword_overlap = set(config.intent_keywords) & set(self.domain_context.specialized_keywords)
                relevance_score += len(keyword_overlap)
            
            # Add manual relevance scoring based on domain type
            if "technical" in self.domain_context.description.lower() and name == "technical-analysis":
                relevance_score += 3
            elif "creative" in self.domain_context.description.lower() and name == "creative-orientation":
                relevance_score += 3
            elif "cultural" in self.domain_context.description.lower() and name == "faith2story":
                relevance_score += 3
            
            if relevance_score > 0:
                scored_flows[name] = config
        
        return scored_flows if scored_flows else self.flows

if __name__ == "__main__":
    main()