"""
SQLAlchemy models for Brand Voice module.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


class BrandProfile(Base):
    __tablename__ = "brand_profiles"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)  # For MVP - later will be proper FK to User
    brand_name = Column(String(100), nullable=False)
    industry = Column(String(100), nullable=True)
    target_audience = Column(Text, nullable=True)
    key_values = Column(Text, nullable=True)
    do_not_use = Column(Text, nullable=True)

    is_trained = Column(Boolean, default=False)
    document_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to documents (for future expansion)
    documents = relationship("BrandDocument", back_populates="brand_profile", cascade="all, delete-orphan")


class BrandDocument(Base):
    __tablename__ = "brand_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey("brand_profiles.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), default="guidelines")
    content = Column(Text, nullable=False)  # Original content
    chunk_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    brand_profile = relationship("BrandProfile", back_populates="documents")
