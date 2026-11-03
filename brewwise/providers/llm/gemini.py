import json
import logging
from typing import Any, Optional, Type, TypeVar
from pydantic import BaseModel
from google import genai
from google.genai import types

from brewwise.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, default_model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.default_model = default_model
        self.client = genai.Client(api_key=api_key) if api_key else None

    async def generate_text(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> str:
        if not self.client:
            raise ValueError("Gemini API key is not configured. Please set GOOGLE_API_KEY.")

        chosen_model = model or self.default_model
        config = types.GenerateContentConfig(
            system_instruction=system_instruction
        )
        response = await self.client.aio.models.generate_content(
            model=chosen_model,
            contents=prompt,
            config=config
        )
        return response.text or ""

    async def generate_structured(
        self,
        prompt: str,
        response_schema: Type[T],
        system_instruction: Optional[str] = None,
        model: Optional[str] = None
    ) -> T:
        if not self.client:
            raise ValueError("Gemini API key is not configured. Please set GOOGLE_API_KEY.")

        chosen_model = model or self.default_model
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema
        )
        response = await self.client.aio.models.generate_content(
            model=chosen_model,
            contents=prompt,
            config=config
        )
        text = response.text or "{}"
        try:
            return response_schema.model_validate_json(text)
        except Exception:
            parsed = json.loads(text)
            return response_schema.model_validate(parsed)
