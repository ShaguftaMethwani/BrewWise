import logging
from brewwise.services.vision.base import VisionProvider
from brewwise.schemas.scan import CoffeeProfileDraftCompact, ExtractedFieldCompact

logger = logging.getLogger(__name__)


class MockVisionProvider(VisionProvider):
    """
    Offline/Demo vision extractor when GOOGLE_API_KEY is not configured.
    Provides realistic specialty coffee profiles to allow seamless testing of the full workflow.
    """

    async def extract_coffee_profile(
        self,
        image_bytes: bytes,
        content_type: str = "image/jpeg"
    ) -> CoffeeProfileDraftCompact:
        logger.info("Using MockVisionProvider to extract coffee bag metadata")

        return CoffeeProfileDraftCompact(
            brand=ExtractedFieldCompact(v="Subko Specialty Coffee Co.", c=0.98),
            name=ExtractedFieldCompact(v="Project Sankalp Lot 42", c=0.95),
            estate=ExtractedFieldCompact(v="Ratnagiri Estate", c=0.92),
            country=ExtractedFieldCompact(v="India", c=0.99),
            region=ExtractedFieldCompact(v="Chikmagalur, Karnataka", c=0.94),
            varietal=ExtractedFieldCompact(v="Red Catuai, Sln 795", c=0.89),
            process=ExtractedFieldCompact(v="Anaerobic Natural", c=0.95),
            roast=ExtractedFieldCompact(v="Light Roast", c=0.92),
            roast_date=ExtractedFieldCompact(v="2026-10-28", c=0.98),
            notes=ExtractedFieldCompact(v="Passion Fruit, Dried Cranberries, Wild Honey, Cacao", c=0.91),
            altitude=ExtractedFieldCompact(v="1420m", c=0.88),
            dose=ExtractedFieldCompact(v="15g", c=0.85),
            extra=[],
            is_coffee_bag=True,
            rejection_reason=None
        )
