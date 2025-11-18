#!/usr/bin/env python3
"""
Flow Analyzer - Admin Intelligence Tool
Analyzes conversation patterns and flow performance to optimize flowise automation
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import statistics
from collections import defaultdict

try:
    from .db_interface import FlowiseDBInterface, FlowStats, ConversationPattern
except ImportError:
    from db_interface import FlowiseDBInterface, FlowStats, ConversationPattern

logger = logging.getLogger(__name__)

@dataclass
class FlowPerformanceReport:
    """Comprehensive performance report for a specific flow"""
    flow_id: str
    flow_name: str
    performance_score: float
    recommendations: List[str]
    
    # Usage metrics
    total_messages: int
    total_sessions: int
    avg_session_length: float
    user_engagement: float
    
    # Quality metrics
    success_rate: float
    completion_rate: float
    user_satisfaction_indicators: List[str]
    
    # Pattern analysis
    common_patterns: List[str]
    successful_keywords: List[str]
    problematic_patterns: List[str]
    
    # Timing analysis
    peak_usage_hours: List[int]
    avg_response_time: Optional[float]
    session_duration_stats: Dict[str, float]
    
    # Improvement opportunities
    optimization_suggestions: List[str]
    content_gaps: List[str]
    technical_improvements: List[str]

class FlowAnalyzer:
    """Advanced flow intelligence analyzer for admin optimization"""
    
    def __init__(self, database_path: str = "/home/jgi/.flowise/database.sqlite"):
        self.db = FlowiseDBInterface(database_path)
        self.flow_stats = None
        self.conversation_patterns = None
        
    def analyze_all_flows(self) -> Dict[str, FlowPerformanceReport]:
        """Analyze all flows and generate performance reports"""
        logger.info("🔍 Analyzing all flows for performance optimization...")
        
        # Get fresh data
        self.flow_stats = self.db.get_flow_statistics()
        self.conversation_patterns = self.db.extract_conversation_patterns()
        
        reports = {}
        
        # Focus on flows with significant usage
        significant_flows = [
            stat for stat in self.flow_stats 
            if stat.message_count >= 20  # Minimum threshold for meaningful analysis
        ]
        
        logger.info(f"📊 Found {len(significant_flows)} flows with significant usage")
        
        for flow_stat in significant_flows:
            try:
                report = self._analyze_single_flow(flow_stat)
                reports[flow_stat.flow_name] = report
                logger.info(f"✅ Analyzed {flow_stat.flow_name}: {report.performance_score:.2f} score")
            except Exception as e:
                logger.error(f"❌ Failed to analyze {flow_stat.flow_name}: {e}")
        
        return reports
    
    def _analyze_single_flow(self, flow_stat: FlowStats) -> FlowPerformanceReport:
        """Analyze a single flow comprehensively"""
        
        # Get conversation patterns for this flow
        flow_patterns = [
            p for p in self.conversation_patterns 
            if p.flow_id == flow_stat.chatflow_id
        ]
        
        # Usage analysis
        usage_metrics = self._analyze_usage_patterns(flow_stat)
        
        # Quality analysis
        quality_metrics = self._analyze_quality_indicators(flow_stat)
        
        # Content analysis
        content_analysis = self._analyze_content_patterns(flow_stat, flow_patterns)
        
        # Timing analysis
        timing_analysis = self._analyze_timing_patterns(flow_stat)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            flow_stat, usage_metrics, quality_metrics, content_analysis
        )
        
        # Calculate overall performance score
        performance_score = self._calculate_performance_score(
            flow_stat, usage_metrics, quality_metrics, content_analysis
        )
        
        return FlowPerformanceReport(
            flow_id=flow_stat.chatflow_id,
            flow_name=flow_stat.flow_name,
            performance_score=performance_score,
            recommendations=recommendations['high_priority'],
            
            # Usage metrics
            total_messages=flow_stat.message_count,
            total_sessions=flow_stat.session_count,
            avg_session_length=flow_stat.avg_messages_per_session,
            user_engagement=flow_stat.engagement_score,
            
            # Quality metrics
            success_rate=flow_stat.success_score,
            completion_rate=quality_metrics['completion_rate'],
            user_satisfaction_indicators=quality_metrics['satisfaction_indicators'],
            
            # Pattern analysis
            common_patterns=content_analysis['common_patterns'],
            successful_keywords=content_analysis['successful_keywords'],
            problematic_patterns=content_analysis['problematic_patterns'],
            
            # Timing analysis
            peak_usage_hours=timing_analysis['peak_hours'],
            avg_response_time=timing_analysis.get('avg_response_time'),
            session_duration_stats=timing_analysis['duration_stats'],
            
            # Improvement opportunities
            optimization_suggestions=recommendations['optimizations'],
            content_gaps=content_analysis['content_gaps'],
            technical_improvements=recommendations['technical']
        )
    
    def _analyze_usage_patterns(self, flow_stat: FlowStats) -> Dict[str, Any]:
        """Analyze usage patterns for a flow"""
        
        # Get hourly usage distribution
        hourly_query = """
        SELECT strftime('%H', createdDate) as hour, COUNT(*) as count
        FROM chat_message 
        WHERE chatflowid = ?
        GROUP BY strftime('%H', createdDate)
        ORDER BY count DESC
        """
        hourly_usage = self.db._execute_query(hourly_query, (flow_stat.chatflow_id,))
        
        # Session distribution analysis
        session_query = """
        SELECT sessionId, COUNT(*) as message_count,
               MIN(createdDate) as start_time,
               MAX(createdDate) as end_time
        FROM chat_message 
        WHERE chatflowid = ? AND sessionId IS NOT NULL
        GROUP BY sessionId
        """
        session_data = self.db._execute_query(session_query, (flow_stat.chatflow_id,))
        
        session_lengths = [s['message_count'] for s in session_data]
        
        return {
            'peak_hours': [int(h['hour']) for h in hourly_usage[:3]],
            'session_length_distribution': {
                'short_sessions': len([s for s in session_lengths if s <= 2]),
                'medium_sessions': len([s for s in session_lengths if 3 <= s <= 10]),
                'long_sessions': len([s for s in session_lengths if s > 10])
            },
            'session_lengths': session_lengths,
            'total_active_days': len(set([
                datetime.fromisoformat(s['start_time'].replace('Z', '+00:00')).date()
                for s in session_data
            ]))
        }
    
    def _analyze_quality_indicators(self, flow_stat: FlowStats) -> Dict[str, Any]:
        """Analyze quality indicators for a flow"""
        
        # User vs API message ratio analysis
        message_query = """
        SELECT role, COUNT(*) as count, AVG(length(content)) as avg_length
        FROM chat_message 
        WHERE chatflowid = ?
        GROUP BY role
        """
        message_breakdown = self.db._execute_query(message_query, (flow_stat.chatflow_id,))
        
        user_messages = next((m['count'] for m in message_breakdown if m['role'] == 'userMessage'), 0)
        api_messages = next((m['count'] for m in message_breakdown if m['role'] == 'apiMessage'), 0)
        user_avg_length = next((m['avg_length'] for m in message_breakdown if m['role'] == 'userMessage'), 0)
        
        # Session completion analysis (sessions with follow-up)
        completion_query = """
        SELECT sessionId, COUNT(*) as turns
        FROM chat_message 
        WHERE chatflowid = ? AND sessionId IS NOT NULL
        GROUP BY sessionId
        HAVING turns > 2
        """
        completed_sessions = self.db._execute_query(completion_query, (flow_stat.chatflow_id,))
        completion_rate = len(completed_sessions) / max(flow_stat.session_count, 1)
        
        # Look for satisfaction indicators
        satisfaction_indicators = []
        if user_avg_length > 50:
            satisfaction_indicators.append("detailed_user_queries")
        if completion_rate > 0.3:
            satisfaction_indicators.append("high_follow_up_rate")
        if flow_stat.engagement_score > 0.6:
            satisfaction_indicators.append("sustained_engagement")
        
        return {
            'user_api_ratio': user_messages / max(api_messages, 1),
            'completion_rate': completion_rate,
            'avg_user_query_length': user_avg_length,
            'satisfaction_indicators': satisfaction_indicators
        }
    
    def _analyze_content_patterns(self, flow_stat: FlowStats, patterns: List[ConversationPattern]) -> Dict[str, Any]:
        """Analyze content patterns for optimization opportunities"""
        
        # Extract successful keywords from patterns
        successful_keywords = []
        common_patterns = []
        
        for pattern in patterns:
            if pattern.confidence > 0.5:
                successful_keywords.extend(pattern.context_keywords)
                common_patterns.append(pattern.pattern_type)
        
        # Analyze failed or low-engagement conversations
        problematic_query = """
        SELECT content, sessionId
        FROM chat_message 
        WHERE chatflowid = ? 
        AND role = 'userMessage'
        AND sessionId IN (
            SELECT sessionId 
            FROM chat_message 
            WHERE chatflowid = ? AND sessionId IS NOT NULL
            GROUP BY sessionId 
            HAVING COUNT(*) <= 2
        )
        LIMIT 20
        """
        problematic_messages = self.db._execute_query(
            problematic_query, 
            (flow_stat.chatflow_id, flow_stat.chatflow_id)
        )
        
        # Identify potential content gaps
        content_gaps = []
        if flow_stat.engagement_score < 0.4:
            content_gaps.append("low_engagement_content")
        if flow_stat.avg_messages_per_session < 3:
            content_gaps.append("insufficient_follow_up_prompting")
        
        problematic_patterns = []
        for msg in problematic_messages:
            content_lower = msg['content'].lower()
            if any(word in content_lower for word in ['unclear', 'confused', 'wrong', 'error']):
                problematic_patterns.append("confusion_indicators")
            if len(content_lower) < 10:
                problematic_patterns.append("very_short_queries")
        
        return {
            'successful_keywords': list(set(successful_keywords)),
            'common_patterns': list(set(common_patterns)),
            'problematic_patterns': list(set(problematic_patterns)),
            'content_gaps': content_gaps
        }
    
    def _analyze_timing_patterns(self, flow_stat: FlowStats) -> Dict[str, Any]:
        """Analyze timing and response patterns"""
        
        # Session duration analysis
        duration_query = """
        SELECT 
            sessionId,
            MIN(createdDate) as start_time,
            MAX(createdDate) as end_time,
            COUNT(*) as message_count
        FROM chat_message 
        WHERE chatflowid = ? AND sessionId IS NOT NULL
        GROUP BY sessionId
        HAVING message_count > 1
        """
        session_durations = self.db._execute_query(duration_query, (flow_stat.chatflow_id,))
        
        durations_minutes = []
        for session in session_durations:
            start = datetime.fromisoformat(session['start_time'].replace('Z', '+00:00'))
            end = datetime.fromisoformat(session['end_time'].replace('Z', '+00:00'))
            duration = (end - start).total_seconds() / 60
            durations_minutes.append(duration)
        
        # Peak usage hours
        hourly_query = """
        SELECT strftime('%H', createdDate) as hour, COUNT(*) as count
        FROM chat_message 
        WHERE chatflowid = ?
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 3
        """
        peak_hours = [
            int(row['hour']) 
            for row in self.db._execute_query(hourly_query, (flow_stat.chatflow_id,))
        ]
        
        duration_stats = {}
        if durations_minutes:
            duration_stats = {
                'avg_minutes': statistics.mean(durations_minutes),
                'median_minutes': statistics.median(durations_minutes),
                'max_minutes': max(durations_minutes),
                'sessions_analyzed': len(durations_minutes)
            }
        
        return {
            'peak_hours': peak_hours,
            'duration_stats': duration_stats
        }
    
    def _calculate_performance_score(self, 
                                   flow_stat: FlowStats, 
                                   usage_metrics: Dict[str, Any],
                                   quality_metrics: Dict[str, Any],
                                   content_analysis: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-1 scale)"""
        
        # Base scores from flow stats
        engagement_score = flow_stat.engagement_score
        success_score = flow_stat.success_score
        
        # Usage score (based on session distribution and activity)
        usage_score = min(1.0, usage_metrics['total_active_days'] / 30.0)  # 30-day ideal
        
        # Quality score (completion rate and user satisfaction)
        quality_score = quality_metrics['completion_rate']
        
        # Content score (successful patterns vs problematic ones)
        content_score = len(content_analysis['successful_keywords']) / 10.0  # 10 keywords ideal
        content_score = min(1.0, content_score)
        
        # Weighted average
        performance_score = (
            engagement_score * 0.25 +
            success_score * 0.25 +
            usage_score * 0.20 +
            quality_score * 0.15 +
            content_score * 0.15
        )
        
        return min(1.0, performance_score)
    
    def _generate_recommendations(self, 
                                flow_stat: FlowStats, 
                                usage_metrics: Dict[str, Any],
                                quality_metrics: Dict[str, Any],
                                content_analysis: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate actionable recommendations for flow improvement"""
        
        high_priority = []
        optimizations = []
        technical = []
        
        # Engagement recommendations
        if flow_stat.engagement_score < 0.5:
            high_priority.append("Improve follow-up prompting to encourage multi-turn conversations")
            optimizations.append("Add conversation continuation cues to responses")
        
        # Session length recommendations
        if flow_stat.avg_messages_per_session < 3:
            high_priority.append("Enhance initial responses to provide more comprehensive guidance")
            optimizations.append("Include related questions or topics in responses")
        
        # Content gap recommendations
        if 'low_engagement_content' in content_analysis['content_gaps']:
            optimizations.append("Review and update response templates for more engaging content")
        
        if 'insufficient_follow_up_prompting' in content_analysis['content_gaps']:
            optimizations.append("Add explicit follow-up questions to encourage deeper exploration")
        
        # Technical improvements
        if quality_metrics['completion_rate'] < 0.3:
            technical.append("Implement session persistence to maintain context across interactions")
        
        if 'confusion_indicators' in content_analysis['problematic_patterns']:
            technical.append("Add clarification mechanisms for ambiguous queries")
            high_priority.append("Review and improve response clarity and specificity")
        
        # Usage pattern optimizations
        short_sessions = usage_metrics['session_length_distribution']['short_sessions']
        total_sessions = sum(usage_metrics['session_length_distribution'].values())
        
        if short_sessions / max(total_sessions, 1) > 0.7:
            optimizations.append("Implement proactive engagement to extend session length")
        
        # Success score improvements
        if flow_stat.success_score < 0.7:
            high_priority.append("Analyze and address factors contributing to lower success rates")
            technical.append("Implement user feedback collection to identify improvement areas")
        
        return {
            'high_priority': high_priority,
            'optimizations': optimizations,
            'technical': technical
        }
    
    def generate_global_intelligence_report(self) -> Dict[str, Any]:
        """Generate system-wide intelligence report for flow optimization"""
        
        reports = self.analyze_all_flows()
        
        # Overall system metrics
        total_flows = len(reports)
        avg_performance = sum(r.performance_score for r in reports.values()) / max(total_flows, 1)
        
        # Top performing flows
        top_performers = sorted(
            reports.values(), 
            key=lambda x: x.performance_score, 
            reverse=True
        )[:5]
        
        # Flows needing attention
        needs_attention = [
            r for r in reports.values() 
            if r.performance_score < 0.6
        ]
        
        # Common patterns across all flows
        all_successful_keywords = []
        all_recommendations = []
        
        for report in reports.values():
            all_successful_keywords.extend(report.successful_keywords)
            all_recommendations.extend(report.recommendations)
        
        # Most common success keywords
        keyword_counts = defaultdict(int)
        for keyword in all_successful_keywords:
            keyword_counts[keyword] += 1
        
        common_success_patterns = sorted(
            keyword_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        # Most common recommendations
        recommendation_counts = defaultdict(int)
        for rec in all_recommendations:
            recommendation_counts[rec] += 1
        
        common_recommendations = sorted(
            recommendation_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        return {
            'system_overview': {
                'total_flows_analyzed': total_flows,
                'average_performance_score': avg_performance,
                'high_performing_flows': len([r for r in reports.values() if r.performance_score > 0.8]),
                'flows_needing_attention': len(needs_attention)
            },
            'top_performers': [
                {
                    'name': r.flow_name,
                    'score': r.performance_score,
                    'total_messages': r.total_messages,
                    'engagement': r.user_engagement
                }
                for r in top_performers
            ],
            'needs_attention': [
                {
                    'name': r.flow_name,
                    'score': r.performance_score,
                    'key_issues': r.recommendations[:2]
                }
                for r in needs_attention
            ],
            'global_patterns': {
                'most_successful_keywords': [
                    {'keyword': k, 'usage_count': c} 
                    for k, c in common_success_patterns
                ],
                'common_recommendations': [
                    {'recommendation': r, 'frequency': f}
                    for r, f in common_recommendations
                ]
            },
            'optimization_priorities': [
                rec for rec, _ in common_recommendations
            ],
            'analysis_timestamp': datetime.now().isoformat()
        }

def main():
    """CLI interface for flow analysis"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Flowise Flow Analyzer")
    parser.add_argument("--database", default="/home/jgi/.flowise/database.sqlite",
                       help="Path to flowise database")
    parser.add_argument("--flow", help="Analyze specific flow by name")
    parser.add_argument("--global-report", action="store_true", help="Generate global intelligence report")
    parser.add_argument("--export", help="Export analysis to JSON file")
    parser.add_argument("--top", type=int, default=5, help="Show top N performing flows")
    
    args = parser.parse_args()
    
    try:
        analyzer = FlowAnalyzer(args.database)
        
        if args.global_report:
            logger.info("🌍 Generating global intelligence report...")
            report = analyzer.generate_global_intelligence_report()
            
            if args.export:
                with open(args.export, 'w') as f:
                    json.dump(report, f, indent=2, default=str)
                print(f"✅ Global report exported to {args.export}")
            else:
                print(json.dumps(report, indent=2, default=str))
                
        elif args.flow:
            reports = analyzer.analyze_all_flows()
            if args.flow in reports:
                report = reports[args.flow]
                print(f"\n🎯 {report.flow_name} Performance Report")
                print(f"   📊 Performance Score: {report.performance_score:.2f}")
                print(f"   💬 Messages: {report.total_messages} | Sessions: {report.total_sessions}")
                print(f"   🔥 Engagement: {report.user_engagement:.2f}")
                print(f"\n🎯 Top Recommendations:")
                for i, rec in enumerate(report.recommendations[:3], 1):
                    print(f"   {i}. {rec}")
            else:
                print(f"❌ Flow '{args.flow}' not found")
                
        else:
            # Default: show top performing flows
            reports = analyzer.analyze_all_flows()
            
            top_flows = sorted(
                reports.values(),
                key=lambda x: x.performance_score,
                reverse=True
            )[:args.top]
            
            print(f"🏆 Top {len(top_flows)} Performing Flows:")
            for i, report in enumerate(top_flows, 1):
                print(f"{i}. {report.flow_name}")
                print(f"   📊 Score: {report.performance_score:.2f} | 💬 {report.total_messages} msgs | 🔥 {report.user_engagement:.2f} engagement")
                if report.recommendations:
                    print(f"   💡 Key recommendation: {report.recommendations[0]}")
                print()
                
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()