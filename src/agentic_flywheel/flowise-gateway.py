#!/usr/bin/env python3
"""
Flowise HTTP Gateway
Provides REST API access to flowise automation capabilities for any agent or system
"""

import asyncio
import json
import logging
import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

# Try to import our flowise modules
try:
    import sys
    sys.path.append(os.path.dirname(__file__))
    from flowise_manager import FlowiseManager, FlowConfig, DomainSpecificFlowiseManager, DomainContext
except ImportError as e:
    logging.warning(f"Could not import flowise modules: {e}")
    FlowiseManager = None
    FlowConfig = None
    DomainSpecificFlowiseManager = None
    DomainContext = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class FlowRequest(BaseModel):
    question: str = Field(..., description="Question to ask the flow")
    session_id: Optional[str] = Field(None, description="Session ID for context continuity")
    intent: Optional[str] = Field(None, description="Explicit intent for flow selection")
    config_override: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")

class RouteRequest(BaseModel):
    question: str = Field(..., description="Question to route automatically")
    auto_detect: bool = Field(True, description="Auto-detect optimal flow")
    session_id: Optional[str] = Field(None, description="Session ID")
    confidence_threshold: float = Field(0.6, description="Minimum confidence for routing")

class SessionRequest(BaseModel):
    flow_type: str = Field(..., description="Flow type for session")
    workspace: Optional[str] = Field(None, description="Workspace context")
    ttl: Optional[int] = Field(3600, description="Session TTL in seconds")

class DomainRequest(BaseModel):
    question: str = Field(..., description="Question to ask with domain context")
    domain_name: str = Field(..., description="Domain name for specialization")
    domain_description: str = Field(..., description="Domain description")
    context_type: str = Field("general", description="Context type: technical, cultural, strategic, general")
    stack_info: Optional[Dict[str, Any]] = Field(None, description="Technical stack information")
    cultural_info: Optional[Dict[str, Any]] = Field(None, description="Cultural context information")
    specialized_keywords: Optional[List[str]] = Field(None, description="Domain-specific keywords")
    session_id: Optional[str] = Field(None, description="Session ID for context continuity")
    config_override: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")

class FlowResponse(BaseModel):
    success: bool
    response: str
    metadata: Dict[str, Any]
    session_id: str
    timestamp: str

class RouteResponse(BaseModel):
    success: bool
    selected_flow: str
    confidence: float
    response: str
    alternatives: List[str]
    session_id: str

class SessionResponse(BaseModel):
    session_id: str
    flow_type: str
    created_at: str
    expires_at: str

class FlowListResponse(BaseModel):
    flows: Dict[str, Dict[str, Any]]
    total_count: int

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime: str
    flows_available: int

# Global state
app = FastAPI(
    title="Flowise Automation Gateway",
    description="REST API gateway for creative-oriented flowise automation",
    version="1.0.0"
)

# CORS middleware for web access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global flowise manager
flowise_manager: Optional[FlowiseManager] = None
app_start_time = datetime.now()
active_sessions: Dict[str, Dict[str, Any]] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize the flowise manager on startup"""
    global flowise_manager
    
    logger.info("🚀 Starting Flowise Gateway...")
    
    try:
        if FlowiseManager:
            flowise_manager = FlowiseManager()
            logger.info("✅ Flowise manager initialized")
        else:
            logger.error("❌ FlowiseManager not available")
    except Exception as e:
        logger.error(f"❌ Failed to initialize flowise manager: {e}")

def generate_session_id(flow_type: str = "session") -> str:
    """Generate a unique session ID"""
    return f"chat:{flow_type}:{str(uuid.uuid4())}"

def get_session_info(session_id: str) -> Dict[str, Any]:
    """Get or create session information"""
    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "request_count": 0
        }
    
    active_sessions[session_id]["last_used"] = datetime.now().isoformat()
    active_sessions[session_id]["request_count"] += 1
    
    return active_sessions[session_id]

@app.get("/", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    uptime = datetime.now() - app_start_time
    
    if flowise_manager:
        flows_count = len(flowise_manager.flows)
    else:
        flows_count = 0
    
    return HealthResponse(
        status="healthy" if flowise_manager else "degraded",
        version="1.0.0",
        uptime=str(uptime),
        flows_available=flows_count
    )

@app.get("/api/v1/flows", response_model=FlowListResponse)
async def list_flows():
    """List available flowise flows"""
    if not flowise_manager:
        raise HTTPException(status_code=503, detail="Flowise manager not available")
    
    flows_info = flowise_manager.list_flows()
    
    return FlowListResponse(
        flows=flows_info,
        total_count=len(flows_info)
    )

@app.post("/api/v1/flows/{flow_name}", response_model=FlowResponse)
async def query_flow(flow_name: str, request: FlowRequest):
    """Query a specific flow"""
    if not flowise_manager:
        raise HTTPException(status_code=503, detail="Flowise manager not available")
    
    # Generate session ID if not provided
    session_id = request.session_id or generate_session_id(flow_name)
    
    # Update session tracking
    session_info = get_session_info(session_id)
    
    try:
        # Execute query
        result = flowise_manager.adaptive_query(
            question=request.question,
            intent=flow_name if flow_name in flowise_manager.flows else request.intent,
            session_id=session_id,
            config_override=request.config_override
        )
        
        # Extract response text
        response_text = result.get("text", result.get("answer", str(result)))
        
        # Build metadata
        metadata = result.get("_metadata", {})
        metadata.update({
            "gateway_session_info": session_info,
            "request_timestamp": datetime.now().isoformat()
        })
        
        return FlowResponse(
            success=True,
            response=response_text,
            metadata=metadata,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error querying flow {flow_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Flow query failed: {str(e)}")

@app.post("/api/v1/route", response_model=RouteResponse)
async def route_query(request: RouteRequest):
    """Automatically route query to optimal flow"""
    if not flowise_manager:
        raise HTTPException(status_code=503, detail="Flowise manager not available")
    
    # Generate session ID if not provided
    session_id = request.session_id or generate_session_id("auto")
    
    # Update session tracking
    get_session_info(session_id)
    
    try:
        # Classify intent and get confidence scores
        detected_intent = flowise_manager.classify_intent(request.question)
        
        # Get all possible flows for alternatives
        all_flows = list(flowise_manager.flows.keys())
        alternatives = [f for f in all_flows if f != detected_intent]
        
        # Execute query with detected intent
        result = flowise_manager.adaptive_query(
            question=request.question,
            intent=detected_intent,
            session_id=session_id
        )
        
        # Extract response
        response_text = result.get("text", result.get("answer", str(result)))
        
        return RouteResponse(
            success=True,
            selected_flow=detected_intent,
            confidence=0.8,  # Simplified confidence score
            response=response_text,
            alternatives=alternatives,
            session_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Error routing query: {e}")
        raise HTTPException(status_code=500, detail=f"Query routing failed: {str(e)}")

@app.post("/api/v1/sessions", response_model=SessionResponse)
async def create_session(request: SessionRequest):
    """Create a new session"""
    session_id = generate_session_id(request.flow_type)
    
    # Store session info
    session_info = {
        "created_at": datetime.now().isoformat(),
        "flow_type": request.flow_type,
        "workspace": request.workspace,
        "ttl": request.ttl,
        "request_count": 0
    }
    
    active_sessions[session_id] = session_info
    
    return SessionResponse(
        session_id=session_id,
        flow_type=request.flow_type,
        created_at=session_info["created_at"],
        expires_at=datetime.now().isoformat()  # Simplified expiration
    )

@app.get("/api/v1/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session information"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return active_sessions[session_id]

@app.delete("/api/v1/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    del active_sessions[session_id]
    return {"message": "Session deleted successfully"}

@app.get("/api/v1/sessions")
async def list_sessions():
    """List all active sessions"""
    return {
        "sessions": active_sessions,
        "total_count": len(active_sessions)
    }

# Convenience endpoints for common flows
@app.post("/api/v1/creative")
async def creative_orientation(request: FlowRequest):
    """Quick access to creative orientation flow"""
    return await query_flow("creative-orientation", request)

@app.post("/api/v1/faith")
async def faith_story(request: FlowRequest):
    """Quick access to faith2story flow"""
    return await query_flow("faith2story", request)

@app.post("/api/v1/auto")
async def auto_route(request: RouteRequest):
    """Auto-route with simplified interface"""
    return await route_query(request)

@app.post("/api/v1/domain", response_model=FlowResponse)
async def domain_query(request: DomainRequest):
    """Query with domain specialization and context injection"""
    if not DomainSpecificFlowiseManager:
        raise HTTPException(status_code=503, detail="Domain specialization not available")
    
    try:
        # Create domain context
        domain_context = DomainContext(
            name=request.domain_name,
            description=request.domain_description,
            stack_info=request.stack_info,
            cultural_info=request.cultural_info,
            specialized_keywords=request.specialized_keywords
        )
        
        # Initialize domain-specific manager
        domain_manager = DomainSpecificFlowiseManager(domain_context=domain_context)
        
        # Generate session ID if not provided
        session_id = request.session_id or generate_session_id(f"domain-{request.domain_name.lower().replace(' ', '-')}")
        
        # Update session tracking
        session_info = get_session_info(session_id)
        
        # Execute contextualized query
        result = domain_manager.contextualized_query(
            question=request.question,
            context_type=request.context_type,
            session_id=session_id,
            config_override=request.config_override
        )
        
        # Extract response text
        response_text = result.get("text", result.get("answer", str(result)))
        
        # Build metadata with domain info
        metadata = result.get("_metadata", {})
        metadata.update({
            "domain_context": {
                "name": request.domain_name,
                "context_type": request.context_type,
                "has_stack_info": request.stack_info is not None,
                "has_cultural_info": request.cultural_info is not None,
                "specialized_keywords_count": len(request.specialized_keywords) if request.specialized_keywords else 0
            },
            "gateway_session_info": session_info,
            "request_timestamp": datetime.now().isoformat()
        })
        
        return FlowResponse(
            success=True,
            response=response_text,
            metadata=metadata,
            session_id=session_id,
            timestamp=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error in domain query: {e}")
        raise HTTPException(status_code=500, detail=f"Domain query failed: {str(e)}")

# Batch processing endpoint
@app.post("/api/v1/batch")
async def batch_query(requests: List[FlowRequest]):
    """Process multiple requests in batch"""
    if not flowise_manager:
        raise HTTPException(status_code=503, detail="Flowise manager not available")
    
    results = []
    
    for req in requests[:10]:  # Limit batch size
        try:
            session_id = req.session_id or generate_session_id("batch")
            result = flowise_manager.adaptive_query(
                question=req.question,
                intent=req.intent,
                session_id=session_id,
                config_override=req.config_override
            )
            
            results.append({
                "success": True,
                "response": result.get("text", result.get("answer", str(result))),
                "session_id": session_id
            })
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e),
                "session_id": req.session_id or "unknown"
            })
    
    return {"results": results, "processed_count": len(results)}

def main():
    """Main entry point for the gateway"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flowise HTTP Gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument("--workers", type=int, default=1, help="Number of worker processes")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--log-level", default="info", help="Log level")
    
    args = parser.parse_args()
    
    logger.info(f"🌐 Starting Flowise Gateway on {args.host}:{args.port}")
    logger.info(f"📋 API documentation: http://{args.host}:{args.port}/docs")
    
    uvicorn.run(
        "flowise_gateway:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main()