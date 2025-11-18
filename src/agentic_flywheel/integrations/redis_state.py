#!/usr/bin/env python3
"""
Redis State Persistence for Agentic Flywheel

Provides session state persistence and execution caching via Redis (coaia-mcp tools).
Enables cross-session conversation continuity.

Usage:
    from agentic_flywheel.integrations import RedisSessionManager

    redis_mgr = RedisSessionManager(enabled=True, ttl_seconds=604800)
    await redis_mgr.save_session(session)
    restored = await redis_mgr.load_session(session_id)

Specification: rispecs/integrations/redis_state.spec.md
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional
from dataclasses import asdict
from datetime import datetime

from ..backends import UniversalSession, BackendType, FlowStatus

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis connection and persistence configuration"""

    @staticmethod
    def from_env() -> Dict[str, Any]:
        """
        Load Redis configuration from environment variables

        Environment Variables:
            REDIS_STATE_ENABLED: Enable state persistence (default: true)
            REDIS_SESSION_TTL_SECONDS: Session TTL (default: 604800 = 7 days)
            REDIS_EXECUTION_TTL_SECONDS: Execution result TTL (default: 86400 = 1 day)
            REDIS_KEY_PREFIX: Key prefix (default: agentic_flywheel)
            REDIS_HOST: Redis host (default: localhost)
            REDIS_PORT: Redis port (default: 6379)

        Returns:
            Configuration dictionary
        """
        return {
            'enabled': os.getenv('REDIS_STATE_ENABLED', 'true').lower() == 'true',
            'session_ttl': int(os.getenv('REDIS_SESSION_TTL_SECONDS', '604800')),  # 7 days
            'execution_ttl': int(os.getenv('REDIS_EXECUTION_TTL_SECONDS', '86400')),  # 1 day
            'key_prefix': os.getenv('REDIS_KEY_PREFIX', 'agentic_flywheel'),
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379'))
        }


class RedisSessionManager:
    """
    Manages session state persistence via Redis

    Provides save/load/delete/list operations for UniversalSession objects.
    Wraps coaia-mcp Redis tools (coaia_tash, coaia_fetch, etc.)
    """

    def __init__(
        self,
        enabled: bool = True,
        ttl_seconds: int = 604800,  # 7 days
        key_prefix: str = "agentic_flywheel"
    ):
        """
        Initialize session manager

        Args:
            enabled: Whether persistence is enabled
            ttl_seconds: Default TTL for session data (seconds)
            key_prefix: Redis key prefix
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix

    def _make_session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.key_prefix}:session:{session_id}"

    def _serialize_session(self, session: UniversalSession) -> str:
        """
        Serialize session to JSON string

        Args:
            session: UniversalSession to serialize

        Returns:
            JSON string
        """
        data = {
            '_schema_version': '1.0',
            'id': session.id,
            'backend': session.backend.value,
            'backend_session_id': session.backend_session_id,
            'status': session.status.value if session.status else None,
            'current_flow_id': session.current_flow_id,
            'context': session.context,
            'history': session.history,
            'metadata': {
                'created_at': session.created_at.isoformat() if hasattr(session, 'created_at') and session.created_at else None,
                'last_active': datetime.now().isoformat()
            }
        }
        return json.dumps(data)

    def _deserialize_session(self, json_str: str) -> UniversalSession:
        """
        Deserialize JSON string to UniversalSession

        Args:
            json_str: JSON string

        Returns:
            UniversalSession object
        """
        data = json.loads(json_str)

        # Reconstruct UniversalSession
        return UniversalSession(
            id=data['id'],
            backend=BackendType(data['backend']),
            backend_session_id=data['backend_session_id'],
            status=FlowStatus(data['status']) if data.get('status') else FlowStatus.IDLE,
            current_flow_id=data.get('current_flow_id'),
            context=data.get('context', {}),
            history=data.get('history', [])
        )

    async def _call_coaia_tash(self, key: str, data: str, ttl: int) -> bool:
        """
        Call coaia_tash MCP tool to store data in Redis

        Args:
            key: Redis key
            data: Data to store (JSON string)
            ttl: Time-to-live in seconds

        Returns:
            True if successful, False otherwise

        Note:
            In production, this calls the actual coaia_tash MCP tool.
            In tests, this is mocked.
        """
        # This is a placeholder for MCP tool call
        # In production, would use MCP client:
        # result = await mcp_client.call_tool("coaia_tash", {"key": key, "data": data, "ttl": ttl})
        logger.info(f"coaia_tash called: key={key}, ttl={ttl}, size={len(data)} bytes")
        return True

    async def _call_coaia_fetch(self, key: str) -> Optional[str]:
        """
        Call coaia_fetch MCP tool to retrieve data from Redis

        Args:
            key: Redis key

        Returns:
            Data string if found, None otherwise
        """
        logger.info(f"coaia_fetch called: key={key}")
        return None  # Placeholder - mocked in tests

    async def _call_coaia_list(self, pattern: str) -> List[str]:
        """
        Call coaia_list MCP tool to list keys matching pattern

        Args:
            pattern: Redis key pattern (supports wildcards)

        Returns:
            List of matching keys
        """
        logger.info(f"coaia_list called: pattern={pattern}")
        return []  # Placeholder - mocked in tests

    async def _call_coaia_drop(self, key: str) -> bool:
        """
        Call coaia_drop MCP tool to delete key from Redis

        Args:
            key: Redis key

        Returns:
            True if deleted, False otherwise
        """
        logger.info(f"coaia_drop called: key={key}")
        return True  # Placeholder - mocked in tests

    async def save_session(self, session: UniversalSession) -> bool:
        """
        Save session state to Redis

        Args:
            session: UniversalSession to save

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.enabled:
            logger.debug("Redis persistence disabled, skipping save")
            return False

        try:
            key = self._make_session_key(session.id)
            data = self._serialize_session(session)

            success = await self._call_coaia_tash(key, data, self.ttl_seconds)

            if success:
                logger.info(f"Session saved: {session.id}")
            else:
                logger.warning(f"Session save failed: {session.id}")

            return success

        except Exception as e:
            logger.error(f"Error saving session {session.id}: {e}")
            return False  # Fail gracefully

    async def load_session(self, session_id: str) -> Optional[UniversalSession]:
        """
        Load session state from Redis

        Args:
            session_id: Session ID to load

        Returns:
            UniversalSession if found, None otherwise
        """
        if not self.enabled:
            logger.debug("Redis persistence disabled, skipping load")
            return None

        try:
            key = self._make_session_key(session_id)
            data = await self._call_coaia_fetch(key)

            if data is None:
                logger.debug(f"Session not found: {session_id}")
                return None

            session = self._deserialize_session(data)
            logger.info(f"Session loaded: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
            return None  # Fail gracefully

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_session_key(session_id)
            success = await self._call_coaia_drop(key)

            if success:
                logger.info(f"Session deleted: {session_id}")
            else:
                logger.warning(f"Session delete failed: {session_id}")

            return success

        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False

    async def list_sessions(self, pattern: str = "*") -> List[str]:
        """
        List all stored session IDs matching pattern

        Args:
            pattern: Session ID pattern (supports wildcards)

        Returns:
            List of session IDs
        """
        if not self.enabled:
            return []

        try:
            key_pattern = f"{self.key_prefix}:session:{pattern}"
            keys = await self._call_coaia_list(key_pattern)

            # Extract session IDs from keys
            session_ids = [
                key.replace(f"{self.key_prefix}:session:", "")
                for key in keys
            ]

            logger.info(f"Listed {len(session_ids)} sessions")
            return session_ids

        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return []


class RedisExecutionCache:
    """
    Caches flow execution results in Redis

    Provides caching for individual execution results and execution history.
    """

    def __init__(
        self,
        enabled: bool = True,
        ttl_seconds: int = 86400,  # 1 day
        key_prefix: str = "agentic_flywheel"
    ):
        """
        Initialize execution cache

        Args:
            enabled: Whether caching is enabled
            ttl_seconds: Default TTL for cached data (seconds)
            key_prefix: Redis key prefix
        """
        self.enabled = enabled
        self.ttl_seconds = ttl_seconds
        self.key_prefix = key_prefix

    def _make_execution_key(self, execution_id: str) -> str:
        """Generate Redis key for execution result"""
        return f"{self.key_prefix}:execution:{execution_id}"

    def _make_history_key(self, session_id: str, flow_id: str) -> str:
        """Generate Redis key for execution history"""
        return f"{self.key_prefix}:history:{session_id}:{flow_id}"

    async def _call_coaia_tash(self, key: str, data: str, ttl: int) -> bool:
        """Wrapper for coaia_tash (same as RedisSessionManager)"""
        logger.info(f"coaia_tash called: key={key}, ttl={ttl}")
        return True

    async def _call_coaia_fetch(self, key: str) -> Optional[str]:
        """Wrapper for coaia_fetch"""
        logger.info(f"coaia_fetch called: key={key}")
        return None

    async def cache_result(self, execution_id: str, result: Dict[str, Any]) -> bool:
        """
        Cache flow execution result

        Args:
            execution_id: Unique execution ID
            result: Execution result dictionary

        Returns:
            True if cached, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_execution_key(execution_id)
            data = json.dumps({
                'execution_id': execution_id,
                'result': result,
                'cached_at': datetime.now().isoformat()
            })

            success = await self._call_coaia_tash(key, data, self.ttl_seconds)

            if success:
                logger.info(f"Execution result cached: {execution_id}")

            return success

        except Exception as e:
            logger.error(f"Error caching execution result: {e}")
            return False

    async def get_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached execution result

        Args:
            execution_id: Execution ID to retrieve

        Returns:
            Cached result if found, None otherwise
        """
        if not self.enabled:
            return None

        try:
            key = self._make_execution_key(execution_id)
            data = await self._call_coaia_fetch(key)

            if data is None:
                return None

            cached = json.loads(data)
            return cached.get('result')

        except Exception as e:
            logger.error(f"Error retrieving cached result: {e}")
            return None

    async def cache_flow_history(
        self,
        session_id: str,
        flow_id: str,
        executions: List[Dict[str, Any]]
    ) -> bool:
        """
        Cache execution history for a session/flow combination

        Args:
            session_id: Session ID
            flow_id: Flow ID
            executions: List of execution records

        Returns:
            True if cached, False otherwise
        """
        if not self.enabled:
            return False

        try:
            key = self._make_history_key(session_id, flow_id)
            data = json.dumps({
                'session_id': session_id,
                'flow_id': flow_id,
                'executions': executions,
                'cached_at': datetime.now().isoformat()
            })

            success = await self._call_coaia_tash(key, data, self.ttl_seconds)

            if success:
                logger.info(f"Flow history cached: {session_id}/{flow_id}")

            return success

        except Exception as e:
            logger.error(f"Error caching flow history: {e}")
            return False


__all__ = [
    'RedisSessionManager',
    'RedisExecutionCache',
    'RedisConfig'
]
