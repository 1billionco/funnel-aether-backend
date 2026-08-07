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
    
    # Enhanced fields for better brand voice control
    tone_descriptors = Column(Text, nullable=True)  # e.g., "professional, witty, empathetic"
    writing_style = Column(String(50), nullable=True)  # e.g., "conversational", "formal", "technical"
    brand_personality = Column(Text, nullable=True)  # e.g., "friendly expert", "bold innovator"
    
    # Multi-language support (dissertation requirement for global SMEs)
    primary_language = Column(String(10), default="en")  # ISO language code
    supported_languages = Column(Text, nullable=True)  # JSON array of supported languages

    is_trained = Column(Boolean, default=False)
    document_count = Column(Integer, default=0)
    total_chunks = Column(Integer, default=0)  # Track total embedded chunks
    
    # Training quality metrics
    training_quality_score = Column(Integer, default=0)  # 0-100 score based on document diversity
    last_training_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to documents (for future expansion)
    documents = relationship("BrandDocument", back_populates="brand_profile", cascade="all, delete-orphan")


class BrandDocument(Base):
    __tablename__ = "brand_documents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_profile_id = Column(PG_UUID(as_uuid=True), ForeignKey("brand_profiles.id"), nullable=False)
    
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), default="guidelines")  # guidelines, tone_examples, past_content, website_copy, social_posts, email_templates, ad_copy, blog_posts
    content = Column(Text, nullable=False)  # Original content
    chunk_count = Column(Integer, default=0)
    
    # Enhanced tracking for better RAG retrieval
    language = Column(String(10), default="en")  # Document language
    source_url = Column(String(500), nullable=True)  # If scraped from web
    file_name = Column(String(200), nullable=True)  # Original filename if uploaded
    
    # Quality & usage tracking
    relevance_score = Column(Integer, default=100)  # How often this doc is retrieved (higher = more relevant)
    last_retrieved_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)  # Can be deactivated without deletion

    created_at = Column(DateTime, default=datetime.utcnow)

    brand_profile = relationship("BrandProfile", back_populates="documents")
