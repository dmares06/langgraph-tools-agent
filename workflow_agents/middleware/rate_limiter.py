# workflow_agents/middleware/rate_limiter.py
"""
Rate limiting middleware for workflow agents.
Prevents abuse and manages API costs using Redis.
"""

import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Optional
import logging
from fastapi import HTTPException

from workflow_agents.constants import RATE_LIMITS

logger = logging.getLogger(__name__)


class RateLimitExceeded(HTTPException):
    """Custom exception for rate limit violations."""
    def __init__(self, message: str, reset_in_seconds: int):
        super().__init__(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": message,
                "reset_in_seconds": reset_in_seconds,
                "retry_after": reset_in_seconds
            },
            headers={"Retry-After": str(reset_in_seconds)}
        )


class WorkflowRateLimiter:
    """
    Redis-based rate limiter for workflow operations.
    
    Tracks different action types per user with configurable limits.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Initialize rate limiter.
        
        Args:
            redis_url: Redis connection string
        """
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        
    async def connect(self):
        """Establish Redis connection."""
        if not self.redis_client:
            self.redis_client = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Connected to Redis for rate limiting")
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
            logger.info("Disconnected from Redis")
    
    async def check_and_increment(
        self,
        user_id: str,
        action: str,
        custom_limit: Optional[int] = None,
        custom_window_hours: Optional[int] = None
    ) -> int:
        """
        Check if user has exceeded rate limit and increment counter.
        
        Args:
            user_id: User's UUID
            action: Action type (workflow_create, workflow_validate, etc.)
            custom_limit: Override default limit
            custom_window_hours: Override default window
            
        Returns:
            Current count for this action
            
        Raises:
            RateLimitExceeded: If limit exceeded
        """
        await self.connect()
        
        # Get rate limit config
        if action not in RATE_LIMITS:
            logger.warning(f"No rate limit defined for action: {action}")
            return 0
        
        config = RATE_LIMITS[action]
        limit = custom_limit or config["limit"]
        
        # Handle different window types
        if "window_hours" in config:
            window_seconds = (custom_window_hours or config["window_hours"]) * 3600
        elif "window_minutes" in config:
            window_seconds = config["window_minutes"] * 60
        else:
            window_seconds = 3600  # Default 1 hour
        
        # Redis key
        key = f"rate_limit:{user_id}:{action}"
        
        # Increment counter
        current = await self.redis_client.incr(key)
        
        # Set expiry on first increment
        if current == 1:
            await self.redis_client.expire(key, window_seconds)
        
        # Check if limit exceeded
        if current > limit:
            ttl = await self.redis_client.ttl(key)
            minutes = max(1, ttl // 60)
            
            message = config["message"].format(
                count=limit,
                minutes=minutes
            )
            
            logger.warning(
                f"Rate limit exceeded for user {user_id}, action {action}. "
                f"Count: {current}/{limit}, Reset in: {ttl}s"
            )
            
            raise RateLimitExceeded(message, ttl)
        
        logger.debug(
            f"Rate limit check passed for user {user_id}, action {action}. "
            f"Count: {current}/{limit}"
        )
        
        return current
    
    async def get_remaining(
        self,
        user_id: str,
        action: str
    ) -> dict:
        """
        Get remaining quota for an action.
        
        Args:
            user_id: User's UUID
            action: Action type
            
        Returns:
            Dict with limit, current, remaining, reset_in_seconds
        """
        await self.connect()
        
        if action not in RATE_LIMITS:
            return {
                "limit": 0,
                "current": 0,
                "remaining": 0,
                "reset_in_seconds": 0
            }
        
        config = RATE_LIMITS[action]
        limit = config["limit"]
        key = f"rate_limit:{user_id}:{action}"
        
        current = await self.redis_client.get(key)
        current = int(current) if current else 0
        
        ttl = await self.redis_client.ttl(key)
        ttl = ttl if ttl > 0 else 0
        
        return {
            "limit": limit,
            "current": current,
            "remaining": max(0, limit - current),
            "reset_in_seconds": ttl
        }
    
    async def reset_user_limits(self, user_id: str):
        """
        Reset all rate limits for a user.
        Useful for testing or admin overrides.
        
        Args:
            user_id: User's UUID
        """
        await self.connect()
        
        pattern = f"rate_limit:{user_id}:*"
        keys = []
        
        async for key in self.redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.redis_client.delete(*keys)
            logger.info(f"Reset {len(keys)} rate limit keys for user {user_id}")
    
    async def get_user_stats(self, user_id: str) -> dict:
        """
        Get all rate limit stats for a user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict mapping action types to their stats
        """
        await self.connect()
        
        stats = {}
        for action in RATE_LIMITS.keys():
            stats[action] = await self.get_remaining(user_id, action)
        
        return stats


# Global rate limiter instance
_rate_limiter: Optional[WorkflowRateLimiter] = None


async def get_rate_limiter() -> WorkflowRateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    
    if _rate_limiter is None:
        from workflow_agents.config import config
        _rate_limiter = WorkflowRateLimiter(config.redis_url)
        await _rate_limiter.connect()
    
    return _rate_limiter


async def check_rate_limit(
    user_id: str,
    action: str,
    custom_limit: Optional[int] = None
) -> int:
    """
    Convenience function to check rate limit.
    
    Args:
        user_id: User's UUID
        action: Action type
        custom_limit: Optional custom limit
        
    Returns:
        Current count
        
    Raises:
        RateLimitExceeded: If limit exceeded
    """
    limiter = await get_rate_limiter()
    return await limiter.check_and_increment(user_id, action, custom_limit)