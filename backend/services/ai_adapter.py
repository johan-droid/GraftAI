"""
AI Provider Adapter - Abstraction layer to prevent LLM vendor lock-in.
Supports OpenAI, Anthropic, Groq, and local models.
"""
import os
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class AIProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    LOCAL = "local"
    AUTO = "auto"

class LLMInterface(ABC):
    @abstractmethod
    async def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        response_format: Optional[str] = None
    ) -> str:
        pass

class OpenAIAdapter(LLMInterface):
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model

    async def chat_completion(self, messages, temperature=0.2, response_format=None):
        extra_args = {}
        if response_format == "json":
            extra_args["response_format"] = {"type": "json_object"}
            
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            **extra_args
        )
        return response.choices[0].message.content

class GroqAdapter(LLMInterface):
    def __init__(self, api_key: str, model: str = "llama3-70b-8192"):
        from groq import AsyncGroq
        self.client = AsyncGroq(api_key=api_key)
        self.model = model

    async def chat_completion(self, messages, temperature=0.2, response_format=None):
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content

class AIAdapter:
    """The main gateway for all AI calls in GraftAI."""
    
    def __init__(self):
        self.provider_type = AIProvider(os.getenv("AI_PROVIDER", "auto").lower())
        self._adapter: Optional[LLMInterface] = None
        self._init_adapter()

    def _init_adapter(self):
        if self.provider_type == AIProvider.GROQ or (self.provider_type == AIProvider.AUTO and os.getenv("GROQ_API_KEY")):
            self._adapter = GroqAdapter(os.getenv("GROQ_API_KEY"))
            logger.info("AI Gateway: Using Groq (Llama 3)")
        elif self.provider_type == AIProvider.OPENAI or (self.provider_type == AIProvider.AUTO and os.getenv("OPENAI_API_KEY")):
            self._adapter = OpenAIAdapter(os.getenv("OPENAI_API_KEY"))
            logger.info("AI Gateway: Using OpenAI (GPT-4)")
        else:
            logger.warning("AI Gateway: No provider configured. Falling back to mock/local.")

    async def get_chat_response(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.2,
        response_format: Optional[str] = None
    ) -> str:
        if not self._adapter:
            return "AI provider not configured."
        
        try:
            return await self._adapter.chat_completion(messages, temperature, response_format)
        except Exception as e:
            logger.error(f"AI Gateway Error: {e}")
            raise

# Global singleton
ai_gateway = AIAdapter()
