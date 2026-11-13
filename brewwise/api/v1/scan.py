import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from brewwise.config import settings
from brewwise.dependencies import get_coffee_extractor
from brewwise.services.vision.extractor import CoffeeBagExtractor
from brewwise.schemas.coffee_profile import CoffeeProfileDraft
from brewwise.services.identity.confidence import calculate_overall_confidence
from brewwise.db.session import get_db
from brewwise.models.coffee_profile import CoffeeProfileModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan", tags=["Scan"])

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}


def sniff_image_type(data: bytes) -> Optional[str]:
    """Identifies JPEG / PNG / WebP from magic bytes; returns None for anything else."""
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


@router.post("", response_model=CoffeeProfileDraft)
async def scan_coffee_bag(
    file: UploadFile = File(...),
    extractor: CoffeeBagExtractor = Depends(get_coffee_extractor),
    db: AsyncSession = Depends(get_db)
):
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file.content_type}'. Please upload JPEG, PNG, or WebP images."
        )

    # Read at most one byte past the limit so oversized uploads are not buffered in full
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    image_bytes = await file.read(max_bytes + 1)
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"Image exceeds maximum permitted size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    # Trust the file's actual signature, not the client-supplied Content-Type header
    sniffed_type = sniff_image_type(image_bytes)
    if sniffed_type is None:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid JPEG, PNG, or WebP image."
        )

    # If Vision provider is not configured (e.g. no Gemini API key set yet), provide informative error or mock draft
    try:
        draft = await extractor.extract(
            image_bytes=image_bytes,
            filename=file.filename or "bag.jpg",
            content_type=sniffed_type
        )
    except ValueError as ve:
        # e.g., missing API key
        raise HTTPException(status_code=503, detail=str(ve))
    except Exception as e:
        logger.exception("Failed to extract coffee profile from image")
        raise HTTPException(status_code=500, detail=f"Vision extraction failed: {str(e)}")

    if not draft.is_coffee_bag:
        raise HTTPException(
            status_code=422,
            detail=draft.rejection_reason or "This does not appear to be a coffee bag."
        )

    # Persist in DB (check if already saved via cache)
    existing = await db.get(CoffeeProfileModel, draft.id)
    if not existing:
        overall_conf = calculate_overall_confidence(draft)
        db_profile = CoffeeProfileModel(
            id=draft.id,
            brand=draft.brand.value,
            product_name=draft.product_name.value,
            country=draft.country.value,
            region=draft.region.value,
            estate=draft.estate.value,
            varietal=draft.varietal.value,
            process=draft.process.value,
            roast_level=draft.roast_level.value,
            roast_date=draft.roast_date.value,
            tasting_notes=draft.tasting_notes.value,
            altitude=draft.altitude.value,
            image_url=draft.image_url,
            confidence=overall_conf,
            raw_metadata=draft.model_dump(mode="json")
        )
        db.add(db_profile)
        await db.commit()

    return draft
