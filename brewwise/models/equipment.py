from sqlalchemy import Column, String, Text
from brewwise.db.session import Base


class EquipmentModel(Base):
    __tablename__ = "equipment"

    id = Column(String, primary_key=True, index=True)
    category = Column(String, nullable=False, index=True)  # dripper, grinder
    brand = Column(String, nullable=False)
    model = Column(String, nullable=False)
    geometry = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    default_ratio = Column(String, default="1:16")
