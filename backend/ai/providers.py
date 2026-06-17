"""
LLM Provider abstraction with Router and Circuit Breaker.
"""
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from backend.utils.logger import get_logger

logger = get_logger(__name__)

_GROQ_NOT_INITIALIZED = "Groq client not initialized"
_OPENAI_NOT_INITIALIZED = "OpenAI client not initialized"
_NO_FALLBACK = "Circuit breaker open and no fallback configured"


@dataclass
class ProviderResponse:
    content: str
    tokens_used: int = 0


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self, messages: list[dict[str, str]], require_json: bool = False, **kwargs: Any
    ) -> ProviderResponse:
        ...

    @abstractmethod
    async def complete_stream(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> Any:
        ...


class GroqProvider(LLMProvider):
    def __init__(self, model: str = "llama-3.3-70b-versatile"):
        self.model = model
        self.client = None
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                from groq import AsyncGroq
                self.client = AsyncGroq(api_key=api_key)
                logger.info("GroqProvider initialized with model: %s", model)
            except Exception as e:
                logger.warning("Failed to initialize Groq client: %s", e)

    async def complete(
        self, messages: list[dict[str, str]], require_json: bool = False, **kwargs: Any
    ) -> ProviderResponse:
        if self.client is None:
            raise RuntimeError(_GROQ_NOT_INITIALIZED)
        response_format = {"type": "json_object"} if require_json else None
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=0.2 if require_json else 0.7,
            **kwargs,
        )
        content = None
        tokens = 0
        try:
            choice = completion.choices[0]
            content = getattr(choice, "message", {}).get("content") if isinstance(choice, dict) else getattr(choice.message, "content", None)
        except Exception:
            try:
                content = completion.choices[0]["message"]["content"]
            except Exception:
                content = getattr(completion, "text", None) or ""
        try:
            tokens = getattr(completion, "usage", {}).get("total_tokens", 0) if isinstance(completion, dict) else getattr(completion.usage, "total_tokens", 0)
        except Exception:
            tokens = 0
        return ProviderResponse(content=content or "", tokens_used=int(tokens))

    async def complete_stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError(_GROQ_NOT_INITIALIZED)
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.7,
            **kwargs,
        )


class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.client = None
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=api_key)
                logger.info("OpenAIProvider initialized with model: %s", model)
            except Exception as e:
                logger.warning("Failed to initialize OpenAI client: %s", e)

    async def complete(
        self, messages: list[dict[str, str]], require_json: bool = False, **kwargs: Any
    ) -> ProviderResponse:
        if self.client is None:
            raise RuntimeError(_OPENAI_NOT_INITIALIZED)
        response_format = {"type": "json_object"} if require_json else None
        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            response_format=response_format,
            temperature=0.2 if require_json else 0.7,
            **kwargs,
        )
        content = completion.choices[0].message.content or ""
        tokens = getattr(completion, "usage", None)
        total_tokens = tokens.total_tokens if tokens else 0
        return ProviderResponse(content=content, tokens_used=total_tokens)

    async def complete_stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        if self.client is None:
            raise RuntimeError(_OPENAI_NOT_INITIALIZED)
        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            stream=True,
            temperature=0.7,
            **kwargs,
        )


class CircuitOpenError(RuntimeError):
    ...


class LLMRouter:
    def __init__(
        self,
        primary: LLMProvider,
        fallback: LLMProvider | None = None,
        failure_threshold: int = 3,
        recovery_timeout: int = 30,
    ):
        self.primary = primary
        self.fallback = fallback
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.circuit_open = False
        self.last_failure_time = 0.0

    async def complete(
        self, messages: list[dict[str, str]], require_json: bool = False, **kwargs: Any
    ) -> ProviderResponse:
        if self.circuit_open:
            if time.monotonic() - self.last_failure_time > self.recovery_timeout:
                logger.info("Circuit breaker resetting — trying primary provider")
                self.circuit_open = False
                self.failure_count = 0
            elif self.fallback:
                logger.warning("Circuit open — using fallback provider")
                return await self.fallback.complete(messages, require_json=require_json, **kwargs)
            else:
                raise CircuitOpenError(_NO_FALLBACK)
        try:
            response = await self.primary.complete(messages, require_json=require_json, **kwargs)
            self.failure_count = 0
            return response
        except Exception as e:
            self.failure_count += 1
            logger.warning("Primary provider failed (%d/%d): %s", self.failure_count, self.failure_threshold, e)
            if self.failure_count >= self.failure_threshold:
                self.circuit_open = True
                self.last_failure_time = time.monotonic()
                logger.exception("Circuit breaker opened after %d failures", self.failure_count)
            if self.fallback:
                logger.info("Falling back to secondary provider")
                return await self.fallback.complete(messages, require_json=require_json, **kwargs)
            raise

    async def complete_stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Any:
        try:
            return await self.primary.complete_stream(messages, **kwargs)
        except Exception as e:
            logger.warning("Primary streaming failed: %s", e)
            if self.fallback:
                return await self.fallback.complete_stream(messages, **kwargs)
            raise


def create_llm_router() -> LLMRouter:
    primary = GroqProvider(model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"))
    fallback = None
    if os.getenv("OPENAI_API_KEY"):
        fallback = OpenAIProvider(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    else:
        logger.info("OPENAI_API_KEY not set — no fallback provider configured")
    return LLMRouter(primary=primary, fallback=fallback, failure_threshold=3, recovery_timeout=30)
