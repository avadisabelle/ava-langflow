#!/usr/bin/env python3
"""
Flowise Database Interface - Admin Layer
Provides intelligent access to local flowise SQLite databases with full admin capabilities
"""

import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import uuid
from pathlib import Path
import sys
import os

# Import working flowise manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
try:
    from flowise_manager import FlowiseManager, FlowConfig
except ImportError:
    FlowiseManager = None
    FlowConfig = None

logger = logging.getLogger(__name__)

@dataclass
class ChatMessage:
    """Represents a chat message from flowise database"""
    id: str
    role: str
    chatflowid: str
    content: str
    created_date: datetime
    session_id: Optional[str] = None
    source_documents: Optional[str] = None
    used_tools: Optional[str] = None
    chat_id: Optional[str] = None
    memory_type: Optional[str] = None
    agent_reasoning: Optional[str] = None
    artifacts: Optional[str] = None

@dataclass
class FlowStats:
    """Statistics about a specific chatflow"""
    chatflow_id: str
    flow_name: str
    message_count: int
    session_count: int
    first_message: datetime
    last_message: datetime
    avg_messages_per_session: float
    most_active_session: Optional[str] = None
    success_score: float = 0.0
    engagement_score: float = 0.0

@dataclass
class ConversationPattern:
    """Represents a conversation pattern extracted from chat data"""
    pattern_type: str
    flow_id: str
    flow_name: str
    confidence: float
    examples: List[str]
    success_indicators: List[str]
    context_keywords: List[str]
    usage_frequency: int = 0

class FlowiseDBInterface:
    """Admin-level interface for accessing flowise SQLite databases with full capabilities"""
    
    def __init__(self, database_path: str = "/home/jgi/.flowise/database.sqlite"):
        self.database_path = Path(database_path)
        
        # Initialize flow manager for live integration
        self.flow_manager = None
        if FlowiseManager:
            try:
                self.flow_manager = FlowiseManager()
                logger.info("✅ Integrated with working FlowiseManager")
            except Exception as e:
                logger.warning(f"⚠️ FlowiseManager integration failed: {e}")
        
        # Flow ID to name mapping (will be populated from both DB and live manager)
        self.flow_id_mapping = {
            "7d405a51-968d-4467-9ae6-d49bf182cdf9": "creative-orientation",
            "896f7eed-342e-4596-9429-6fb9b5fbd91b": "faith2story",
            "2f4dd89f-af8a-4606-bba7-219f32ade711": "coaia4RISE",
            "aad975b2-289f-4acc-acc0-f19f4cfcb013": "miadi46code",
        }
        
        # Update mapping from live flow manager if available
        if self.flow_manager:
            for name, config in self.flow_manager.flows.items():
                if hasattr(config, 'id'):
                    self.flow_id_mapping[config.id] = name
        
        if not self.database_path.exists():
            raise FileNotFoundError(f"Database not found: {database_path}")
            
        logger.info(f"✅ FlowiseDBInterface initialized with database: {database_path}")
    
    def _execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a query and return results as list of dictionaries"""
        try:
            with sqlite3.connect(self.database_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Database query error: {e}")
            return []
    
    def get_flow_statistics(self) -> List[FlowStats]:
        """Get comprehensive statistics for all chatflows with enhanced analytics"""
        query = """
        SELECT 
            chatflowid,
            COUNT(*) as message_count,
            COUNT(DISTINCT sessionId) as session_count,
            MIN(createdDate) as first_message,
            MAX(createdDate) as last_message,
            AVG(length(content)) as avg_content_length,
            COUNT(CASE WHEN role = 'userMessage' THEN 1 END) as user_messages,
            COUNT(CASE WHEN role = 'apiMessage' THEN 1 END) as api_messages
        FROM chat_message 
        WHERE sessionId IS NOT NULL
        GROUP BY chatflowid
        ORDER BY message_count DESC
        """
        
        results = self._execute_query(query)
        stats = []
        
        for row in results:
            # Calculate enhanced metrics
            avg_msgs = row['message_count'] / max(row['session_count'], 1)
            
            # Get most active session for this flow
            most_active_session = self._get_most_active_session(row['chatflowid'])
            
            # Calculate success score (based on user engagement)
            success_score = self._calculate_success_score(row)
            
            # Calculate engagement score (multi-turn conversations)
            engagement_score = self._calculate_engagement_score(row['chatflowid'])
            
            # Get flow name
            flow_name = self.flow_id_mapping.get(row['chatflowid'], 'unknown')
            
            stats.append(FlowStats(
                chatflow_id=row['chatflowid'],
                flow_name=flow_name,
                message_count=row['message_count'],
                session_count=row['session_count'],
                first_message=datetime.fromisoformat(row['first_message'].replace('Z', '+00:00')),
                last_message=datetime.fromisoformat(row['last_message'].replace('Z', '+00:00')),
                avg_messages_per_session=avg_msgs,
                most_active_session=most_active_session,
                success_score=success_score,
                engagement_score=engagement_score
            ))
        
        return stats
    
    def _calculate_success_score(self, row: Dict[str, Any]) -> float:
        """Calculate success score based on conversation quality indicators"""
        try:
            # Base metrics
            user_msg_ratio = row['user_messages'] / max(row['message_count'], 1)
            avg_content_length = row.get('avg_content_length', 0)
            session_diversity = row['session_count'] / max(row['message_count'], 1)
            
            # Weighted scoring
            score = (
                user_msg_ratio * 0.4 +  # Higher user engagement = better
                min(avg_content_length / 200, 1.0) * 0.3 +  # Reasonable response length
                min(session_diversity * 10, 1.0) * 0.3  # Multiple sessions indicate utility
            )
            
            return min(score, 1.0)
        except:
            return 0.0
    
    def _calculate_engagement_score(self, chatflow_id: str) -> float:
        """Calculate engagement score based on multi-turn conversations"""
        query = """
        SELECT AVG(turn_count) as avg_turns, COUNT(*) as total_sessions
        FROM (
            SELECT sessionId, COUNT(*) as turn_count 
            FROM chat_message 
            WHERE chatflowid = ? AND sessionId IS NOT NULL 
            GROUP BY sessionId
        )
        """
        results = self._execute_query(query, (chatflow_id,))
        
        if results and results[0]['avg_turns']:
            avg_turns = results[0]['avg_turns']
            # Score based on average conversation length (2+ turns is good)
            return min((avg_turns - 1) / 5.0, 1.0)  # Normalize to 0-1 scale
        
        return 0.0
    
    def _get_most_active_session(self, chatflow_id: str) -> Optional[str]:
        """Get the session with most messages for a given chatflow"""
        query = """
        SELECT sessionId, COUNT(*) as msg_count 
        FROM chat_message 
        WHERE chatflowid = ? AND sessionId IS NOT NULL 
        GROUP BY sessionId 
        ORDER BY msg_count DESC 
        LIMIT 1
        """
        results = self._execute_query(query, (chatflow_id,))
        return results[0]['sessionId'] if results else None
    
    def get_recent_conversations(self, limit: int = 10, flow_id: Optional[str] = None) -> List[ChatMessage]:
        """Get recent conversation messages with optional flow filtering"""
        where_clause = "WHERE 1=1"
        params = []
        
        if flow_id:
            where_clause += " AND chatflowid = ?"
            params.append(flow_id)
        
        query = f"""
        SELECT 
            id, role, chatflowid, content, createdDate, sessionId,
            sourceDocuments, usedTools, chatId, memoryType, 
            agentReasoning, artifacts
        FROM chat_message 
        {where_clause}
        ORDER BY createdDate DESC 
        LIMIT ?
        """
        params.append(limit)
        
        results = self._execute_query(query, tuple(params))
        messages = []
        
        for row in results:
            messages.append(ChatMessage(
                id=row['id'],
                role=row['role'],
                chatflowid=row['chatflowid'],
                content=row['content'],
                created_date=datetime.fromisoformat(row['createdDate'].replace('Z', '+00:00')),
                session_id=row.get('sessionId'),
                source_documents=row.get('sourceDocuments'),
                used_tools=row.get('usedTools'),
                chat_id=row.get('chatId'),
                memory_type=row.get('memoryType'),
                agent_reasoning=row.get('agentReasoning'),
                artifacts=row.get('artifacts')
            ))
        
        return messages
    
    def extract_conversation_patterns(self, flow_id: Optional[str] = None) -> List[ConversationPattern]:
        """Extract patterns from successful conversations for flow enhancement"""
        patterns = []
        
        # Get flow statistics for context
        flow_stats = self.get_flow_statistics()
        stats_by_id = {stat.chatflow_id: stat for stat in flow_stats}
        
        # Focus on high-performing flows
        high_performing_flows = [
            stat for stat in flow_stats 
            if stat.success_score > 0.6 and stat.message_count > 10
        ]
        
        for flow_stat in high_performing_flows:
            if flow_id and flow_stat.chatflow_id != flow_id:
                continue
                
            patterns.extend(self._extract_flow_specific_patterns(flow_stat))
        
        return patterns
    
    def _extract_flow_specific_patterns(self, flow_stat: FlowStats) -> List[ConversationPattern]:
        """Extract patterns for a specific high-performing flow"""
        patterns = []
        
        # Get successful conversations for this flow
        query = """
        SELECT content, role, sessionId, createdDate
        FROM chat_message 
        WHERE chatflowid = ?
        AND role = 'userMessage'
        AND length(content) > 20
        ORDER BY createdDate DESC
        LIMIT 100
        """
        
        results = self._execute_query(query, (flow_stat.chatflow_id,))
        
        if flow_stat.flow_name == "creative-orientation":
            patterns.extend(self._extract_creative_orientation_patterns(results, flow_stat))
        elif flow_stat.flow_name == "faith2story":
            patterns.extend(self._extract_faith_story_patterns(results, flow_stat))
        elif flow_stat.flow_name == "miadi46code":
            patterns.extend(self._extract_coding_patterns(results, flow_stat))
        
        # Always extract general engagement patterns
        patterns.extend(self._extract_engagement_patterns(flow_stat))
        
        return patterns
    
    def _extract_creative_orientation_patterns(self, messages: List[Dict], flow_stat: FlowStats) -> List[ConversationPattern]:
        """Extract patterns from creative orientation conversations"""
        vision_keywords = []
        outcome_keywords = []
        structural_keywords = []
        
        for row in messages:
            content_lower = row['content'].lower()
            
            if any(word in content_lower for word in ['vision', 'want to create', 'goal', 'dream', 'aspire']):
                vision_keywords.append(row['content'][:100])
            
            if any(word in content_lower for word in ['outcome', 'achieve', 'result', 'accomplish']):
                outcome_keywords.append(row['content'][:100])
            
            if any(word in content_lower for word in ['tension', 'current reality', 'desired', 'advancement']):
                structural_keywords.append(row['content'][:100])
        
        patterns = []
        
        if vision_keywords:
            patterns.append(ConversationPattern(
                pattern_type="vision_creation",
                flow_id=flow_stat.chatflow_id,
                flow_name=flow_stat.flow_name,
                confidence=min(len(vision_keywords) / 20.0, 1.0),
                examples=vision_keywords[:5],
                success_indicators=["clear vision articulation", "outcome focus"],
                context_keywords=["vision", "create", "goal", "dream", "aspire"],
                usage_frequency=len(vision_keywords)
            ))
        
        if outcome_keywords:
            patterns.append(ConversationPattern(
                pattern_type="outcome_focus",
                flow_id=flow_stat.chatflow_id,
                flow_name=flow_stat.flow_name,
                confidence=min(len(outcome_keywords) / 20.0, 1.0),
                examples=outcome_keywords[:5],
                success_indicators=["outcome clarity", "action orientation"],
                context_keywords=["outcome", "achieve", "result", "accomplish"],
                usage_frequency=len(outcome_keywords)
            ))
        
        return patterns
    
    def _extract_faith_story_patterns(self, messages: List[Dict], flow_stat: FlowStats) -> List[ConversationPattern]:
        """Extract patterns from faith story conversations"""
        narrative_patterns = []
        experience_patterns = []
        
        for row in messages:
            content_lower = row['content'].lower()
            
            if any(word in content_lower for word in ['story', 'experience', 'journey', 'path']):
                narrative_patterns.append(row['content'][:100])
            
            if any(word in content_lower for word in ['faith', 'spiritual', 'grace', 'meaning', 'purpose']):
                experience_patterns.append(row['content'][:100])
        
        patterns = []
        
        if narrative_patterns:
            patterns.append(ConversationPattern(
                pattern_type="narrative_transformation",
                flow_id=flow_stat.chatflow_id,
                flow_name=flow_stat.flow_name,
                confidence=min(len(narrative_patterns) / 20.0, 1.0),
                examples=narrative_patterns[:5],
                success_indicators=["story structure", "personal connection"],
                context_keywords=["story", "experience", "journey", "path"],
                usage_frequency=len(narrative_patterns)
            ))
        
        return patterns
    
    def _extract_coding_patterns(self, messages: List[Dict], flow_stat: FlowStats) -> List[ConversationPattern]:
        """Extract patterns from coding-related conversations"""
        implementation_patterns = []
        problem_solving_patterns = []
        
        for row in messages:
            content_lower = row['content'].lower()
            
            if any(word in content_lower for word in ['implement', 'code', 'build', 'create', 'develop']):
                implementation_patterns.append(row['content'][:100])
            
            if any(word in content_lower for word in ['debug', 'fix', 'error', 'issue', 'problem']):
                problem_solving_patterns.append(row['content'][:100])
        
        patterns = []
        
        if implementation_patterns:
            patterns.append(ConversationPattern(
                pattern_type="code_implementation",
                flow_id=flow_stat.chatflow_id,
                flow_name=flow_stat.flow_name,
                confidence=min(len(implementation_patterns) / 15.0, 1.0),
                examples=implementation_patterns[:5],
                success_indicators=["clear requirements", "implementation focus"],
                context_keywords=["implement", "code", "build", "create", "develop"],
                usage_frequency=len(implementation_patterns)
            ))
        
        return patterns
    
    def _extract_engagement_patterns(self, flow_stat: FlowStats) -> List[ConversationPattern]:
        """Extract engagement patterns for any flow"""
        patterns = []
        
        if flow_stat.engagement_score > 0.7:
            patterns.append(ConversationPattern(
                pattern_type="high_engagement",
                flow_id=flow_stat.chatflow_id,
                flow_name=flow_stat.flow_name,
                confidence=flow_stat.engagement_score,
                examples=[f"Session {flow_stat.most_active_session}" if flow_stat.most_active_session else "Multi-turn conversations"],
                success_indicators=["extended dialogue", "iterative refinement"],
                context_keywords=["follow-up", "clarification", "deeper", "more"],
                usage_frequency=flow_stat.session_count
            ))
        
        return patterns
    
    def get_admin_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for admin interface"""
        # Get basic statistics
        flow_stats = self.get_flow_statistics()
        patterns = self.extract_conversation_patterns()
        
        # Calculate overall system health
        total_messages = sum(stat.message_count for stat in flow_stats)
        avg_success_score = sum(stat.success_score for stat in flow_stats) / len(flow_stats) if flow_stats else 0
        
        # Recent activity analysis
        recent_query = """
        SELECT DATE(createdDate) as date, COUNT(*) as messages, COUNT(DISTINCT sessionId) as sessions
        FROM chat_message 
        WHERE createdDate >= date('now', '-7 days')
        GROUP BY DATE(createdDate)
        ORDER BY date DESC
        """
        recent_activity = self._execute_query(recent_query)
        
        # Live integration status
        live_status = {
            "flowise_manager_connected": self.flow_manager is not None,
            "flows_in_manager": len(self.flow_manager.flows) if self.flow_manager else 0,
            "database_flows": len(flow_stats)
        }
        
        return {
            'system_health': {
                'total_messages': total_messages,
                'total_flows': len(flow_stats),
                'avg_success_score': avg_success_score,
                'top_performing_flows': [
                    {
                        'name': stat.flow_name,
                        'success_score': stat.success_score,
                        'engagement_score': stat.engagement_score,
                        'message_count': stat.message_count
                    }
                    for stat in sorted(flow_stats, key=lambda x: x.success_score, reverse=True)[:5]
                ]
            },
            'flow_statistics': [asdict(stat) for stat in flow_stats],
            'conversation_patterns': [asdict(pattern) for pattern in patterns],
            'recent_activity': recent_activity,
            'live_integration': live_status,
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def search_conversations(self, search_term: str, flow_id: Optional[str] = None, limit: int = 20) -> List[ChatMessage]:
        """Search conversation content for specific terms"""
        where_clause = "WHERE content LIKE ?"
        params = [f"%{search_term}%"]
        
        if flow_id:
            where_clause += " AND chatflowid = ?"
            params.append(flow_id)
        
        query = f"""
        SELECT 
            id, role, chatflowid, content, createdDate, sessionId,
            sourceDocuments, usedTools, chatId, memoryType, 
            agentReasoning, artifacts
        FROM chat_message 
        {where_clause}
        ORDER BY createdDate DESC 
        LIMIT ?
        """
        params.append(limit)
        
        results = self._execute_query(query, tuple(params))
        messages = []
        
        for row in results:
            messages.append(ChatMessage(
                id=row['id'],
                role=row['role'], 
                chatflowid=row['chatflowid'],
                content=row['content'],
                created_date=datetime.fromisoformat(row['createdDate'].replace('Z', '+00:00')),
                session_id=row.get('sessionId'),
                source_documents=row.get('sourceDocuments'),
                used_tools=row.get('usedTools'),
                chat_id=row.get('chatId'),
                memory_type=row.get('memoryType'),
                agent_reasoning=row.get('agentReasoning'),
                artifacts=row.get('artifacts')
            ))
        
        return messages

def main():
    """CLI interface for admin database analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flowise Admin Database Interface")
    parser.add_argument("--database", default="/home/jgi/.flowise/database.sqlite", 
                       help="Path to flowise database")
    parser.add_argument("--dashboard", action="store_true", help="Show admin dashboard")
    parser.add_argument("--flows", action="store_true", help="Show flow statistics")
    parser.add_argument("--patterns", action="store_true", help="Extract conversation patterns")
    parser.add_argument("--search", help="Search conversations for term")
    parser.add_argument("--export", help="Export analysis to JSON file")
    
    args = parser.parse_args()
    
    try:
        db = FlowiseDBInterface(args.database)
        
        if args.dashboard:
            dashboard = db.get_admin_dashboard_data()
            if args.export:
                with open(args.export, 'w') as f:
                    json.dump(dashboard, f, indent=2, default=str)
                print(f"✅ Dashboard exported to {args.export}")
            else:
                print(json.dumps(dashboard, indent=2, default=str))
        
        elif args.flows:
            stats = db.get_flow_statistics()
            for stat in stats[:10]:
                print(f"\n🔥 Flow: {stat.flow_name} ({stat.chatflow_id[:8]}...)")
                print(f"   📊 Messages: {stat.message_count} | Sessions: {stat.session_count}")
                print(f"   🎯 Success: {stat.success_score:.2f} | Engagement: {stat.engagement_score:.2f}")
                print(f"   📅 Active: {stat.first_message.strftime('%Y-%m-%d')} → {stat.last_message.strftime('%Y-%m-%d')}")
        
        elif args.patterns:
            patterns = db.extract_conversation_patterns()
            for pattern in patterns:
                print(f"\n🧠 Pattern: {pattern.pattern_type}")
                print(f"   📈 Flow: {pattern.flow_name} | Confidence: {pattern.confidence:.2f}")
                print(f"   🔑 Keywords: {', '.join(pattern.context_keywords)}")
                print(f"   📝 Usage: {pattern.usage_frequency} times")
        
        elif args.search:
            messages = db.search_conversations(args.search)
            for msg in messages[:5]:
                flow_name = db.flow_id_mapping.get(msg.chatflowid, 'unknown')
                print(f"\n[{msg.created_date.strftime('%Y-%m-%d %H:%M')}] {flow_name}")
                print(f"   {msg.role}: {msg.content[:150]}...")
        
        else:
            # Default: show system summary
            dashboard = db.get_admin_dashboard_data()
            health = dashboard['system_health']
            print(f"📊 Flowise Admin Dashboard")
            print(f"   💬 Total Messages: {health['total_messages']:,}")
            print(f"   🔄 Active Flows: {health['total_flows']}")
            print(f"   🎯 Avg Success Score: {health['avg_success_score']:.2f}")
            print(f"   🔗 Live Integration: {dashboard['live_integration']['flowise_manager_connected']}")
            print(f"\n🏆 Top Performing Flows:")
            for flow in health['top_performing_flows'][:3]:
                print(f"   • {flow['name']}: {flow['success_score']:.2f} success, {flow['message_count']} msgs")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()