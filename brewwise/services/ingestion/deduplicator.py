import hashlib
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from brewwise.models.recipe_source import RecipeSourceModel


class Deduplicator:
    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Computes a SHA-256 hash of normalized text."""
        normalized = " ".join(text.lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    async def find_existing(
        content_hash: str,
        url: Optional[str],
        db: AsyncSession
    ) -> Optional[RecipeSourceModel]:
        """Checks if a recipe with this content hash or URL already exists in DB."""
        if url:
            stmt = select(RecipeSourceModel).where(RecipeSourceModel.url == url)
            res = await db.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing

        stmt = select(RecipeSourceModel).where(RecipeSourceModel.content_hash == content_hash)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()
