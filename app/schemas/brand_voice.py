"""
Pydantic schemas for Brand Voice module.
Enhanced with multi-language support, quality metrics, and better document tracking.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import json


class BrandDocumentUpload(BaseModel):
    """Schema for uploading brand documents (text content for MVP)."""
    title: str = Field(..., min_length=1, max_length=200, description="Title of the document (e.g. 'Brand Guidelines 2025')")
    content: str = Field(..., min_length=50, description="Full text content of the brand document")
    document_type: str = Field(
        default="guidelines",
        description="Type of document: guidelines, tone_examples, past_content, website_copy, social_posts, email_templates, ad_copy, blog_posts"
    )
    language: str = Field(default="en", max_length=10, description="ISO language code (e.g., 'en', 'es', 'fr')")
    source_url: Optional[str] = Field(None, max_length=500, description="Source URL if scraped from web")
    file_name: Optional[str] = Field(None, max_length=200, description="Original filename if uploaded")


class BrandProfileCreate(BaseModel):
    """Create or update brand profile."""
    brand_name: str = Field(..., min_length=2, max_length=100)
    industry: Optional[str] = None
    target_audience: Optional[str] = None
    key_values: Optional[str] = None  # comma separated or JSON string for MVP
    do_not_use: Optional[str] = None  # words/phrases to avoid
    
    # Enhanced fields for better brand voice control
    tone_descriptors: Optional[str] = Field(None, description="Comma-separated tone descriptors (e.g., 'professional, witty, empathetic')")
    writing_style: Optional[str] = Field(None, max_length=50, description="Writing style: conversational, formal, technical, etc.")
    brand_personality: Optional[str] = Field(None, description="Brand personality archetype (e.g., 'friendly expert', 'bold innovator')")
    
    # Multi-language support (dissertation requirement for global SMEs)
    primary_language: str = Field(default="en", max_length=10, description="Primary language ISO code")
    supported_languages: Optional[str] = Field(None, description="JSON array of supported language codes")
    
    @validator('supported_languages', pre=True)
    def validate_supported_languages(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return json.dumps(v)
        return v


class BrandProfileResponse(BaseModel):
    """Response schema for brand profile."""
    id: UUID
    brand_name: str
    industry: Optional[str]
    target_audience: Optional[str]
    key_values: Optional[str]
    do_not_use: Optional[str]
    
    # Enhanced fields
    tone_descriptors: Optional[str]
    writing_style: Optional[str]
    brand_personality: Optional[str]
    primary_language: str
    supported_languages: Optional[str]
    
    is_trained: bool
    document_count: int
    total_chunks: int
    training_quality_score: int
    last_training_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrandVoiceTrainingStatus(BaseModel):
    """Status after uploading/training documents."""
    brand_id: UUID
    documents_processed: int
    total_chunks: int
    training_quality_score: int
    status: str = "success"
    message: str = "Brand voice training completed successfully. AI will now generate content in your voice."


class BrandContextRequest(BaseModel):
    """Request to retrieve relevant brand context for generation."""
    query: str = Field(..., min_length=5, description="What are you generating? (e.g. 'Instagram caption for new product launch')")
    max_chunks: int = Field(default=5, ge=1, le=10)
    language: Optional[str] = Field(None, max_length=10, description="Target language for content generation")


class BrandContextResponse(BaseModel):
    """Relevant brand context retrieved via RAG."""
    brand_name: str
    relevant_chunks: List[str]
    tone_instructions: str
    restrictions: Optional[str] = None
    confidence: float = Field(default=0.85, description="How well the brand voice is trained")
    primary_language: str
    recommended_document_types: List[str] = Field(default_factory=list, description="Suggested document types to improve training")


class BrandDocumentResponse(BaseModel):
    """Response schema for individual brand document."""
    id: UUID
    title: str
    document_type: str
    chunk_count: int
    language: str
    is_active: bool
    relevance_score: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class BrandAnalysisResponse(BaseModel):
    """Analysis of brand voice training quality."""
    brand_id: UUID
    overall_score: int
    document_diversity_score: int
    content_coverage_score: int
    strengths: List[str]
    recommendations: List[str]
    missing_document_types: List[str]
