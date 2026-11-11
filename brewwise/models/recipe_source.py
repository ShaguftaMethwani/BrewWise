import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON, Text, ForeignKey, Integer
from sqlalchemy.orm import relationship

from brewwise.db.session import Base


class RecipeSourceModel(Base):
    __tablename__ = "recipe_sources"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    url = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=True)
    author = Column(String, nullable=True)
    site_name = Column(String, nullable=True)
    raw_content = Column(Text, nullable=True)
    content_hash = Column(String, index=True, nullable=False)

    retrieval_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    publication_date = Column(DateTime, nullable=True)
    is_accessible = Column(Boolean, default=True)
    last_verified = Column(DateTime, nullable=True)
    extraction_method = Column(String, default="curated")
    discovery_context = Column(String, nullable=True)

    # Structured metadata
    coffee_metadata = Column(JSON, nullable=True)  # brand, estate, country, region, process, roast_level
    extracted_recipe = Column(JSON, nullable=True)  # dripper, dose_g, water_g, ratio, temp_c, grind, steps

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    embeddings = relationship("RecipeEmbeddingModel", back_populates="recipe_source", cascade="all, delete-orphan")


class RecipeEmbeddingModel(Base):
    __tablename__ = "recipe_embeddings"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    recipe_source_id = Column(String, ForeignKey("recipe_sources.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_text = Column(Text, nullable=True)
    chunk_index = Column(Integer, default=0)
    embedding = Column(JSON, nullable=False)  # 768-dim float vector stored as JSON array
    embedding_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    recipe_source = relationship("RecipeSourceModel", back_populates="embeddings")
