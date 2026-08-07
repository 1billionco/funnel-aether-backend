"""
API Endpoints for Brand Voice Training & Retrieval.
Enhanced with quality analysis, document management, and multi-language support.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from typing import List
from uuid import UUID

from app.schemas.brand_voice import (
    BrandProfileCreate,
    BrandProfileResponse,
    BrandDocumentUpload,
    BrandVoiceTrainingStatus,
    BrandContextRequest,
    BrandContextResponse,
    BrandDocumentResponse,
    BrandAnalysisResponse
)
from app.services.brand_voice.service import BrandVoiceService
from app.db.session import get_db
from app.models.brand_voice import BrandProfile, BrandDocument
from sqlalchemy.orm import Session

router = APIRouter(prefix="/brand-voice", tags=["Brand Voice"])

# For MVP we use a simple dependency. In production this would come from auth
def get_current_user_id() -> str:
    return "demo_user_001"  # Temporary for development


@router.post("/profile", response_model=BrandProfileResponse)
def create_brand_profile(
    profile_data: BrandProfileCreate,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create or update the brand profile metadata."""
    service = BrandVoiceService()
    profile = service.create_or_update_brand_profile(
        user_id=user_id,
        brand_data=profile_data.model_dump()
    )
    return profile


@router.post("/upload", response_model=BrandVoiceTrainingStatus)
def upload_brand_documents(
    documents: List[BrandDocumentUpload],
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Upload brand documents (guidelines, tone examples, past content).
    This trains the AI on your unique brand voice using RAG.
    
    Enhanced features:
    - Multi-language document support
    - Quality scoring based on document diversity
    - Automatic recommendations for improvement
    """
    if not documents:
        raise HTTPException(status_code=400, detail="At least one document is required")

    service = BrandVoiceService()

    # Get or create brand profile
    profile = service.create_or_update_brand_profile(
        user_id=user_id,
        brand_data={"brand_name": documents[0].title.split()[0] if documents else "My Brand"}
    )

    # Convert to format expected by service
    docs_for_training = [
        {
            "title": doc.title,
            "content": doc.content,
            "document_type": doc.document_type,
            "language": doc.language,
            "source_url": doc.source_url,
            "file_name": doc.file_name
        }
        for doc in documents
    ]

    result = service.upload_and_train(
        brand_id=profile.id,
        documents=docs_for_training
    )

    return {
        "brand_id": profile.id,
        "documents_processed": result["documents_processed"],
        "total_chunks": result["total_chunks"],
        "training_quality_score": result["training_quality_score"],
        "status": result["status"],
        "message": result["message"]
    }


@router.post("/context", response_model=BrandContextResponse)
def get_brand_context_for_generation(
    request: BrandContextRequest,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Retrieve relevant brand voice context.
    This should be called before generating any content so the AI stays on-brand.
    
    Enhanced features:
    - Language-aware retrieval for multi-language content generation
    - Confidence scoring based on training quality
    - Recommendations for improving brand voice
    """
    service = BrandVoiceService()

    # Get the user's brand profile
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(
            status_code=404, 
            detail="No brand profile found. Please create a profile and upload documents first."
        )

    context = service.get_brand_context(
        brand_id=profile.id,
        query=request.query,
        max_chunks=request.max_chunks,
        language=request.language
    )

    return context


@router.get("/profile", response_model=BrandProfileResponse)
def get_my_brand_profile(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Get current user's brand profile and training status."""
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No brand profile found")
    return profile


@router.get("/analysis", response_model=BrandAnalysisResponse)
def analyze_brand_voice_quality(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Analyze brand voice training quality.
    Returns scores, strengths, and actionable recommendations.
    """
    service = BrandVoiceService()
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No brand profile found")
    
    analysis = service.analyze_brand_voice(db=db, brand_id=profile.id)
    return analysis


@router.get("/documents", response_model=List[BrandDocumentResponse])
def list_brand_documents(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """List all brand documents for the current user."""
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No brand profile found")
    
    query = db.query(BrandDocument).filter(BrandDocument.brand_profile_id == profile.id)
    if not include_inactive:
        query = query.filter(BrandDocument.is_active == True)
    
    documents = query.order_by(BrandDocument.created_at.desc()).all()
    return documents


@router.delete("/documents/{document_id}")
def delete_brand_document(
    document_id: UUID,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """
    Soft-delete a brand document (set is_active=False).
    This allows recovery if needed and maintains historical data.
    """
    profile = db.query(BrandProfile).filter(BrandProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="No brand profile found")
    
    document = db.query(BrandDocument).filter(
        BrandDocument.id == document_id,
        BrandDocument.brand_profile_id == profile.id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    document.is_active = False
    db.commit()
    
    return {"message": f"Document '{document.title}' has been deactivated", "document_id": str(document_id)}
