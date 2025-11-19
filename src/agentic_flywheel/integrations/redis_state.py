"""Redis State Persistence for Session Continuity

Provides persistent session storage via Redis for cross-session conversation continuity.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from dataclasses import asdict
from datetime import datetime

try:
    import redis.asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("redis package not available - Redis persistence will be disabled")

try:
    from ..backends.base import UniversalSession, FlowStatus, BackendType
except ImportError:
    from agentic_flywheel.backends.base import UniversalSession, FlowStatus, BackendType

logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis configuration from environment"""

    @staticmethod
    def from_env() -> Dict[str, Any]:
        """Load Redis config from environment variables"""
        return {
            'enabled': os.getenv('REDIS_ENABLED', 'true').lower() == 'true',
            'ttl_seconds': int(os.getenv('REDIS_TTL_SECONDS', '604800')),  # 7 days default
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', '6379'))
        }


class RedisSessionManager:
    """Manages session state persistence via Redis"""

    def __init__(
        self,
        enabled: bool = True,
        ttl_seconds: int = 604800,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Initialize Redis session manager

        Args:
            enabled: Enable Redis persistence
            ttl_seconds: Time-to-live for sessions (default: 7 days)
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.ttl_seconds = ttl_seconds
        self._key_prefix = "agentic_flywheel:session:"
        self._redis: Optional[aioredis.Redis] = None
        self._host = host
        self._port = port
        self._db = db
        self._password = password

        if not REDIS_AVAILABLE and enabled:
            logger.warning("Redis persistence requested but redis package not available")
            self.enabled = False
        elif not self.enabled:
            logger.info("Redis session persistence disabled")

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        """Get or create Redis connection"""
        if not self.enabled:
            return None

        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    f"redis://{self._host}:{self._port}/{self._db}",
                    password=self._password,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
                # Test connection
                await self._redis.ping()
                logger.info(f"Connected to Redis at {self._host}:{self._port}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
                self.enabled = False
                return None

        return self._redis

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def save_session(self, session: UniversalSession) -> bool:
        """
        Save session state to Redis

        Args:
            session: Session to persist

        Returns:
            True if saved, False if disabled or failed
        """
        if not self.enabled:
            return False

        redis = await self._get_redis()
        if not redis:
            return False

        try:
            # Serialize session to JSON
            session_data = {
                'id': session.id,
                'backend': session.backend.value,
                'backend_session_id': session.backend_session_id,
                'status': session.status.value,
                'current_flow_id': session.current_flow_id,
                'context': session.context,
                'history': session.history,
                'metadata': getattr(session, 'metadata', {}),
                'created_at': getattr(session, 'created_at', datetime.utcnow().isoformat()),
                'last_active': datetime.utcnow().isoformat()
            }

            # Save to Redis with TTL
            key = f"{self._key_prefix}{session.id}"
            await redis.setex(
                key,
                self.ttl_seconds,
                json.dumps(session_data, default=str)
            )
            logger.info(f"Saved session {session.id} to Redis (TTL: {self.ttl_seconds}s)")
            return True

        except Exception as e:
            logger.warning(f"Failed to save session to Redis (non-blocking): {e}")
            return False

    async def load_session(self, session_id: str) -> Optional[UniversalSession]:
        """
        Load session state from Redis

        Args:
            session_id: Session ID to load

        Returns:
            UniversalSession if found, None otherwise
        """
        if not self.enabled:
            return None

        redis = await self._get_redis()
        if not redis:
            return None

        try:
            key = f"{self._key_prefix}{session_id}"
            data_str = await redis.get(key)

            if not data_str:
                logger.debug(f"Session {session_id} not found in Redis")
                return None

            # Deserialize from JSON
            session_data = json.loads(data_str)

            # Reconstruct UniversalSession
            session = UniversalSession(
                id=session_data['id'],
                backend=BackendType(session_data['backend']),
                backend_session_id=session_data.get('backend_session_id'),
                status=FlowStatus(session_data['status']),
                current_flow_id=session_data.get('current_flow_id'),
                context=session_data.get('context', {}),
                history=session_data.get('history', [])
            )

            # Restore metadata if it exists
            if 'metadata' in session_data:
                session.metadata = session_data['metadata']
            if 'created_at' in session_data:
                session.created_at = session_data['created_at']

            logger.info(f"Loaded session {session_id} from Redis")
            return session

        except Exception as e:
            logger.warning(f"Failed to load session from Redis (non-blocking): {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete session from Redis

        Args:
            session_id: Session to delete

        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False

        redis = await self._get_redis()
        if not redis:
            return False

        try:
            key = f"{self._key_prefix}{session_id}"
            result = await redis.delete(key)
            if result > 0:
                logger.info(f"Deleted session {session_id} from Redis")
                return True
            else:
                logger.debug(f"Session {session_id} not found for deletion")
                return False

        except Exception as e:
            logger.warning(f"Failed to delete session from Redis: {e}")
            return False

    async def list_sessions(self, pattern: str = "*") -> List[str]:
        """
        List stored session IDs

        Args:
            pattern: Key pattern to match

        Returns:
            List of session IDs
        """
        if not self.enabled:
            return []

        redis = await self._get_redis()
        if not redis:
            return []

        try:
            # Use SCAN for safe iteration
            search_pattern = f"{self._key_prefix}{pattern}"
            session_ids = []

            cursor = 0
            while True:
                cursor, keys = await redis.scan(cursor, match=search_pattern, count=100)
                for key in keys:
                    # Extract session ID from key
                    session_id = key.replace(self._key_prefix, "")
                    session_ids.append(session_id)

                if cursor == 0:
                    break

            logger.debug(f"Found {len(session_ids)} sessions matching pattern '{pattern}'")
            return session_ids

        except Exception as e:
            logger.warning(f"Failed to list sessions from Redis: {e}")
            return []


class RedisExecutionCache:
    """Caches flow execution results"""

    def __init__(
        self,
        enabled: bool = True,
        ttl_seconds: int = 3600,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None
    ):
        """
        Initialize execution cache

        Args:
            enabled: Enable Redis caching
            ttl_seconds: Time-to-live for cached results (default: 1 hour)
            host: Redis host
            port: Redis port
            db: Redis database number
            password: Redis password (optional)
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.ttl_seconds = ttl_seconds
        self._key_prefix = "agentic_flywheel:execution:"
        self._redis: Optional[aioredis.Redis] = None
        self._host = host
        self._port = port
        self._db = db
        self._password = password

        if not REDIS_AVAILABLE and enabled:
            logger.warning("Redis caching requested but redis package not available")
            self.enabled = False

    async def _get_redis(self) -> Optional[aioredis.Redis]:
        """Get or create Redis connection"""
        if not self.enabled:
            return None

        if self._redis is None:
            try:
                self._redis = await aioredis.from_url(
                    f"redis://{self._host}:{self._port}/{self._db}",
                    password=self._password,
                    decode_responses=True,
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
                await self._redis.ping()
            except Exception as e:
                logger.warning(f"Failed to connect to Redis for caching: {e}")
                self.enabled = False
                return None

        return self._redis

    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def cache_result(self, execution_id: str, result: Dict[str, Any]) -> bool:
        """
        Cache flow execution result

        Args:
            execution_id: Unique execution ID
            result: Execution result to cache

        Returns:
            True if cached, False otherwise
        """
        if not self.enabled:
            return False

        redis = await self._get_redis()
        if not redis:
            return False

        try:
            key = f"{self._key_prefix}{execution_id}"
            await redis.setex(
                key,
                self.ttl_seconds,
                json.dumps(result, default=str)
            )
            logger.debug(f"Cached execution {execution_id}")
            return True

        except Exception as e:
            logger.warning(f"Failed to cache execution result: {e}")
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

        redis = await self._get_redis()
        if not redis:
            return None

        try:
            key = f"{self._key_prefix}{execution_id}"
            data_str = await redis.get(key)

            if not data_str:
                logger.debug(f"Execution {execution_id} not found in cache")
                return None

            result = json.loads(data_str)
            logger.debug(f"Retrieved cached execution {execution_id}")
            return result

        except Exception as e:
            logger.warning(f"Failed to retrieve cached result: {e}")
            return None
