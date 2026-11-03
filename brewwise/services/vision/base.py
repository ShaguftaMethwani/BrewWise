from abc import ABC, abstractmethod
from brewwise.schemas.scan import CoffeeProfileDraftCompact


class VisionProvider(ABC):
    @abstractmethod
    async def extract_coffee_profile(
        self,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> CoffeeProfileDraftCompact:
        pass
