import logging
from sqlalchemy.future import select
from brewwise.db.session import AsyncSessionLocal
from brewwise.models.equipment import EquipmentModel
from brewwise.services.equipment.catalogue import SEED_DRIPPERS, SEED_GRINDERS

logger = logging.getLogger(__name__)


async def seed_equipment():
    async with AsyncSessionLocal() as session:
        for item in SEED_DRIPPERS + SEED_GRINDERS:
            result = await session.execute(select(EquipmentModel).where(EquipmentModel.id == item.id))
            existing = result.scalar_one_or_none()
            if not existing:
                model = EquipmentModel(
                    id=item.id,
                    category=item.category,
                    brand=item.brand,
                    model=item.model,
                    geometry=item.geometry,
                    description=item.description,
                    default_ratio=item.default_ratio
                )
                session.add(model)
        await session.commit()
        logger.info("Equipment catalogue seeded successfully.")
