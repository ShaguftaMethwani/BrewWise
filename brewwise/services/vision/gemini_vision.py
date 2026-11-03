import json
import logging
from pathlib import Path
from typing import Optional
from google import genai
from google.genai import types

from brewwise.services.vision.base import VisionProvider
from brewwise.schemas.scan import CoffeeProfileDraftCompact

logger = logging.getLogger(__name__)


class GeminiVisionProvider(VisionProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        self.client = genai.Client(api_key=api_key) if api_key else None

        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "v1" / "extract_coffee.j2"
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text(encoding="utf-8")
        else:
            self.system_prompt = "Extract coffee bag details into the compact schema. If not a coffee bag, set is_coffee_bag=false."

    async def extract_coffee_profile(
        self,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> CoffeeProfileDraftCompact:
        if not self.client:
            raise ValueError("Gemini API key is required for Vision extraction. Set GOOGLE_API_KEY.")

        image_part = types.Part.from_bytes(data=image_bytes, mime_type=content_type)
        config = types.GenerateContentConfig(
            system_instruction=self.system_prompt,
            response_mime_type="application/json",
            response_schema=CoffeeProfileDraftCompact
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=[image_part, "Extract the coffee bag metadata from this image."],
            config=config
        )

        text = response.text or "{}"
        try:
            return CoffeeProfileDraftCompact.model_validate_json(text)
        except Exception:
            parsed = json.loads(text)
            return CoffeeProfileDraftCompact.model_validate(parsed)
