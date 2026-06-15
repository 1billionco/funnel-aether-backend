"""
Pydantic schemas for Brand Voice module.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID


class BrandDocumentUpload(BaseModel):
    """Schema for uploading brand documents (text content for MVP)."""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the document (e.g. 'Brand Guidelines 2025')")
    content: str = Field(..., min_length=50, description="Full text content of the brand document")
    document_type: str = Field(
        default="guidelines",
        description="Type of document: guidelines, tone_examples, past_content, website_copy, etc."
    )


class BrandProfileCreate(BaseModel):
    """Create or update brand profile."""
    brand_name: str = Field(..., min_length=2, max_length=100)
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    key_values: Optional[str] = None  # comma separated or JSON string for MVP
    do_not_use: Optional[str] = None  # words/phrases to avoid


class BrandProfileResponse(BaseModel):
    """Response schema for brand profile."""
    id: UUID
    brand_name: str
    industry: Optional[str]
    target_audience: Optional[str]
    key_values: Optional[str]
    do_not_use: Optional[str]
    is_trained: bool
    document_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandVoiceTrainingStatus(BaseModel):
    """Status after uploading/training documents."""
    brand_id: UUID
    documents_processed: int
    total_chunks: int
    status: str = "success"
    message: str = "Brand voice training completed successfully. AI will now generate content in your voice."


class BrandContextRequest(BaseModel):
    """Request to retrieve relevant brand context for generation."""
    query: str = Field(..., min_length=5, description="What are you generating? (e.g. 'Instagram caption for new product launch')")
    max_chunks: int = Field(default=5, ge=1, le=10)


class BrandContextResponse(BaseModel):
    """Relevant brand context retrieved via RAG."""
    brand_name: str
    relevant_chunks: List[str]
    tone_instructions: str
    restrictions: Optional[str] = None
    confidence: float = Field(default=0.85, description="How well the brand voice is trained")
