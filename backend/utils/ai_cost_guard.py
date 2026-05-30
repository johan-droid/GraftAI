"""
AI Cost Guard - Prevents AI token abuse and optimizes LLM usage

Implements intelligent controls for:
- Token usage limits and throttling
- Prompt optimization and caching
- Model selection based on cost/benefit
- Abuse detection and prevention
"""
import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import wraps

from backend.core.redis import get_redis_client

logger = logging.getLogger(__name__)

@dataclass
class AIUsageProfile:
    """User AI usage profile for cost optimization"""
    user_id: str
    tier: str
    daily_limit: int
    current_usage: int
    hourly_usage: int
    last_reset: datetime
    avg_tokens_per_request: float
    preferred_model: str
    cost_sensitivity: str

class AICostGuard:
    """Intelligent AI cost control and optimization"""
    MODEL_COSTS = {"groq-llama3-70b": 0.5, "groq-llama3-8b": 0.1, "openai-gpt4o": 5.0, "openai-gpt3.5-turbo": 0.5, "claude-3-haiku": 0.25, "claude-3-sonnet": 3.0}
    CHARS_PER_TOKEN = 4
    RESPONSE_TOKEN_MULTIPLIER = 0.3
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_TOKENS_PER_HOUR = 10000
    SUSPICIOUS_PATTERN_THRESHOLD = 0.8

    def __init__(self):
        self.redis_client = None
        self.usage_cache_key = "ai_usage:"
        self.abuse_cache_key = "ai_abuse:"
        self.prompt_cache_key = "prompt_cache:"

    async def initialize(self):
        """Initialize Redis client"""
        try:
            self.redis_client = await get_redis_client()
        except Exception as e:
            logger.warning("Redis not available for AI cost guard: %s", e)

    async def estimate_tokens(self, text: str) -> int:
        """Estimate token count from text"""
        if not text:
            return 0
        return max(1, len(text) // self.CHARS_PER_TOKEN)

    async def estimate_cost(self, prompt_tokens: int, model: str, response_tokens: int | None=None) -> float:
        """Estimate cost for AI request"""
        if response_tokens is None:
            response_tokens = int(prompt_tokens * self.RESPONSE_TOKEN_MULTIPLIER)
        total_tokens = prompt_tokens + response_tokens
        cost_per_million = self.MODEL_COSTS.get(model, self.MODEL_COSTS["groq-llama3-70b"])
        return total_tokens / 1000000 * cost_per_million

    async def select_optimal_model(self, prompt: str, user_profile: AIUsageProfile, task_complexity: str="medium") -> str:
        """Select the most cost-effective model for the task"""
        await self.estimate_tokens(prompt)
        if user_profile.cost_sensitivity == "high":
            if task_complexity == "simple":
                return "groq-llama3-8b"
            return "groq-llama3-70b"
        if user_profile.cost_sensitivity == "medium":
            if task_complexity == "simple":
                return "groq-llama3-8b"
            if task_complexity == "medium":
                return "groq-llama3-70b"
            return "openai-gpt4o"
        if task_complexity in ["simple", "medium"]:
            return "groq-llama3-70b"
        return "openai-gpt4o"

    async def check_usage_limits(self, user_id: str, estimated_tokens: int) -> tuple[bool, str]:
        """Check if user is within usage limits"""
        if not self.redis_client:
            return (True, "Redis not available")
        now = datetime.now(UTC)
        hour_key = f"{self.usage_cache_key}{user_id}:hour:{now.strftime('%Y%m%d%H')}"
        try:
            hourly_usage = await self.redis_client.get(hour_key) or 0
            hourly_usage = int(hourly_usage)
            if hourly_usage + estimated_tokens > self.MAX_TOKENS_PER_HOUR:
                return (False, f"Hourly token limit exceeded: {hourly_usage} + {estimated_tokens} > {self.MAX_TOKENS_PER_HOUR}")
            await self.redis_client.setex(hour_key, 3600, hourly_usage + estimated_tokens)
        except Exception as e:
            logger.exception("Error checking hourly limits: %s", e)
        minute_key = f"{self.usage_cache_key}{user_id}:minute:{now.strftime('%Y%m%d%H%M')}"
        try:
            requests_per_minute = await self.redis_client.get(minute_key) or 0
            requests_per_minute = int(requests_per_minute)
            if requests_per_minute >= self.MAX_REQUESTS_PER_MINUTE:
                return (False, f"Rate limit exceeded: {requests_per_minute} requests/minute")
            await self.redis_client.setex(minute_key, 60, requests_per_minute + 1)
        except Exception as e:
            logger.exception("Error checking rate limits: %s", e)
        return (True, "Within limits")

    async def detect_abuse_patterns(self, user_id: str, prompt: str) -> tuple[bool, str]:
        """Detect potential abuse patterns"""
        if not self.redis_client:
            return (False, "Redis not available")
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
        pattern_key = f"{self.abuse_cache_key}{user_id}:patterns"
        try:
            await self.redis_client.hincrby(pattern_key, prompt_hash, 1)
            await self.redis_client.expire(pattern_key, 3600)
            patterns = await self.redis_client.hgetall(pattern_key)
            total_requests = sum(int(count) for count in patterns.values())
            if len(patterns) == 1 and total_requests > 10:
                return (True, "Suspicious: Repeated identical prompts")
            if total_requests > self.MAX_REQUESTS_PER_MINUTE * 2:
                return (True, "Suspicious: Excessive request volume")
        except Exception as e:
            logger.exception("Error detecting abuse patterns: %s", e)
        return (False, "No abuse detected")

    async def optimize_prompt(self, prompt: str, model: str) -> str:
        """Optimize prompt for cost efficiency"""
        optimized = " ".join(prompt.split())
        max_tokens = {"groq-llama3-8b": 8000, "groq-llama3-70b": 8000, "openai-gpt4o": 128000, "openai-gpt3.5-turbo": 16000}.get(model, 8000)
        current_tokens = await self.estimate_tokens(optimized)
        if current_tokens > max_tokens:
            max_chars = max_tokens * self.CHARS_PER_TOKEN
            optimized = optimized[:max_chars] + "..."
        return optimized

    async def get_cached_response(self, prompt_hash: str) -> str | None:
        """Get cached AI response for identical prompts"""
        if not self.redis_client:
            return None
        try:
            cached = await self.redis_client.get(f"{self.prompt_cache_key}{prompt_hash}")
            return cached.decode() if cached else None
        except Exception as e:
            logger.exception("Error getting cached response: %s", e)
            return None

    async def cache_response(self, prompt_hash: str, response: str, ttl: int=3600):
        """Cache AI response for future use"""
        if not self.redis_client:
            return
        try:
            await self.redis_client.setex(f"{self.prompt_cache_key}{prompt_hash}", ttl, response)
        except Exception as e:
            logger.exception("Error caching response: %s", e)

    async def get_user_profile(self, user_id: str, tier: str="free") -> AIUsageProfile:
        """Get or create user AI usage profile"""
        if not self.redis_client:
            return AIUsageProfile(user_id=user_id, tier=tier, daily_limit=10 if tier == "free" else 200, current_usage=0, hourly_usage=0, last_reset=datetime.now(UTC), avg_tokens_per_request=150, preferred_model="groq-llama3-70b", cost_sensitivity="medium")
        profile_key = f"{self.usage_cache_key}{user_id}:profile"
        try:
            profile_data = await self.redis_client.hgetall(profile_key)
            if profile_data:
                return AIUsageProfile(user_id=user_id, tier=profile_data.get("tier", tier), daily_limit=int(profile_data.get("daily_limit", 10)), current_usage=int(profile_data.get("current_usage", 0)), hourly_usage=int(profile_data.get("hourly_usage", 0)), last_reset=datetime.fromisoformat(profile_data["last_reset"]), avg_tokens_per_request=float(profile_data.get("avg_tokens", 150)), preferred_model=profile_data.get("preferred_model", "groq-llama3-70b"), cost_sensitivity=profile_data.get("cost_sensitivity", "medium"))
        except Exception as e:
            logger.exception("Error getting user profile: %s", e)
        daily_limits = {"free": 10, "pro": 200, "elite": 2000, "enterprise": 1000000}
        return AIUsageProfile(user_id=user_id, tier=tier, daily_limit=daily_limits.get(tier, 10), current_usage=0, hourly_usage=0, last_reset=datetime.now(UTC), avg_tokens_per_request=150, preferred_model="groq-llama3-70b", cost_sensitivity="medium")

    async def update_user_profile(self, profile: AIUsageProfile):
        """Update user usage profile"""
        if not self.redis_client:
            return
        profile_key = f"{self.usage_cache_key}{profile.user_id}:profile"
        try:
            await self.redis_client.hset(profile_key, {"tier": profile.tier, "daily_limit": profile.daily_limit, "current_usage": profile.current_usage, "hourly_usage": profile.hourly_usage, "last_reset": profile.last_reset.isoformat(), "avg_tokens": str(profile.avg_tokens_per_request), "preferred_model": profile.preferred_model, "cost_sensitivity": profile.cost_sensitivity})
            await self.redis_client.expire(profile_key, 7 * 24 * 3600)
        except Exception as e:
            logger.exception("Error updating user profile: %s", e)
ai_cost_guard = AICostGuard()

def ai_cost_control(tier: str="free", task_complexity: str="medium"):
    """Decorator for AI cost control and optimization"""

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            await ai_cost_guard.initialize()
            user_id = kwargs.get("user_id") or getattr(args[0] if args else None, "user_id", "anonymous")
            prompt = kwargs.get("prompt", "") or getattr(args[0] if args else None, "prompt", "")
            if not prompt:
                return await func(*args, **kwargs)
            user_profile = await ai_cost_guard.get_user_profile(user_id, tier)
            estimated_tokens = await ai_cost_guard.estimate_tokens(prompt)
            within_limits, limit_message = await ai_cost_guard.check_usage_limits(user_id, estimated_tokens)
            if not within_limits:
                msg = f"AI usage limit exceeded: {limit_message}"
                raise Exception(msg)
            is_abuse, abuse_message = await ai_cost_guard.detect_abuse_patterns(user_id, prompt)
            if is_abuse:
                logger.warning("AI abuse detected for user %s: %s", user_id, abuse_message)
                msg = f"Abuse detected: {abuse_message}"
                raise Exception(msg)
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
            cached_response = await ai_cost_guard.get_cached_response(prompt_hash)
            if cached_response:
                logger.info("Cache hit for user %s", user_id)
                return {"response": cached_response, "cached": True}
            optimal_model = await ai_cost_guard.select_optimal_model(prompt, user_profile, task_complexity)
            optimized_prompt = await ai_cost_guard.optimize_prompt(prompt, optimal_model)
            kwargs["prompt"] = optimized_prompt
            kwargs["model"] = optimal_model
            result = await func(*args, **kwargs)
            if isinstance(result, dict) and "response" in result:
                await ai_cost_guard.cache_response(prompt_hash, result["response"])
            actual_tokens = getattr(result, "tokens_used", estimated_tokens)
            user_profile.hourly_usage += actual_tokens
            user_profile.current_usage += actual_tokens
            user_profile.avg_tokens_per_request = (user_profile.avg_tokens_per_request + actual_tokens) / 2
            await ai_cost_guard.update_user_profile(user_profile)
            cost = await ai_cost_guard.estimate_cost(estimated_tokens, optimal_model)
            logger.info("AI request for user %s: %s tokens, $%s cost", user_id, estimated_tokens, cost)
            return result
        return wrapper
    return decorator

async def implement_ai_cost_controls():
    """Initialize AI cost control systems"""
    await ai_cost_guard.initialize()
    logger.info("AI cost guard initialized")
