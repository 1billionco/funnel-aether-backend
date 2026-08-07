"""
Brand Voice Service - Core RAG logic for Funnel Aether.
This is the heart of the human-AI hybrid experience.

Enhanced features:
- Multi-language support for global SMEs (UK, Nigeria, and beyond)
- Quality scoring based on document diversity and coverage
- Smart recommendations for improving brand voice training
- Usage tracking for continuous improvement
"""

import os
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
import json

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.brand_voice import BrandProfile, BrandDocument

settings = get_settings()


# Document type weights for quality scoring
DOCUMENT_TYPE_WEIGHTS = {
    "guidelines": 1.5,      # Most important
    "tone_examples": 1.3,   # Very important for voice
    "past_content": 1.2,    # Shows actual usage
    "website_copy": 1.1,    # Official voice
    "social_posts": 1.0,    # Casual voice
    "email_templates": 1.0, # Professional voice
    "ad_copy": 0.9,         # Marketing voice
    "blog_posts": 0.9       # Long-form voice
}

REQUIRED_DOCUMENT_TYPES = ["guidelines", "tone_examples", "past_content"]
RECOMMENDED_DOCUMENT_TYPES = list(DOCUMENT_TYPE_WEIGHTS.keys())


class BrandVoiceService:
    """
    Handles brand voice training and context retrieval using RAG.
    Designed so that every generation can pull relevant brand voice context.
    
    Key improvements for dissertation requirements:
    - Supports multiple languages for international SMEs
    - Provides quality metrics to ensure effective AI training
    - Offers actionable recommendations for improvement
    - Tracks usage patterns to optimize retrieval
    """

    def __init__(self):
        self.settings = settings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=150,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        # Initialize embeddings based on configured provider
        if self.settings.DEFAULT_LLM_PROVIDER == "openai":
            self.embeddings = OpenAIEmbeddings(openai_api_key=self.settings.OPENAI_API_KEY)
        else:
            # Default to OpenAI embeddings as fallback (Anthropic doesn't have official embeddings)
            # For production, consider using a dedicated embedding provider
            try:
                self.embeddings = OpenAIEmbeddings(openai_api_key=self.settings.OPENAI_API_KEY)
            except Exception:
                # Fallback - in real app we would use a local embedding model
                from langchain_community.embeddings import FakeEmbeddings
                self.embeddings = FakeEmbeddings(size=1536)

    def _get_vectorstore(self, brand_id: UUID) -> Chroma:
        """Get or create a Chroma collection specific to this brand."""
        persist_dir = os.path.join(self.settings.CHROMA_PERSIST_DIRECTORY, str(brand_id))
        os.makedirs(persist_dir, exist_ok=True)
        
        return Chroma(
            collection_name=settings.BRAND_VOICE_COLLECTION,
            embedding_function=self.embeddings,
            persist_directory=persist_dir
        )

    def create_or_update_brand_profile(
        self, 
        user_id: str, 
        brand_data: dict
    ) -> BrandProfile:
        """Create or update brand profile metadata."""
        db = SessionLocal()
        try:
            profile = db.query(BrandProfile).filter(
                BrandProfile.user_id == user_id
            ).first()

            if profile:
                for key, value in brand_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.updated_at = datetime.utcnow()
            else:
                profile = BrandProfile(user_id=user_id, **brand_data)
                db.add(profile)

            db.commit()
            db.refresh(profile)
            return profile
        finally:
            db.close()

    def upload_and_train(
        self,
        brand_id: UUID,
        documents: List[dict]  # list of {"title": str, "content": str, "document_type": str, ...}
    ) -> dict:
        """
        Upload brand documents, chunk them, embed, and store in vector DB.
        This trains the brand voice.
        
        Enhanced with:
        - Quality scoring based on document diversity
        - Multi-language support
        - Usage tracking initialization
        """
        vectorstore = self._get_vectorstore(brand_id)
        db = SessionLocal()
        
        total_chunks = 0
        document_types_added = set()

        try:
            brand_profile = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
            if not brand_profile:
                raise ValueError("Brand profile not found")

            for doc in documents:
                # Create LangChain document
                lc_doc = LCDocument(
                    page_content=doc["content"],
                    metadata={
                        "title": doc["title"],
                        "document_type": doc.get("document_type", "guidelines"),
                        "brand_id": str(brand_id),
                        "language": doc.get("language", "en")
                    }
                )
                
                # Split into chunks
                chunks = self.text_splitter.split_documents([lc_doc])
                total_chunks += len(chunks)
                document_types_added.add(doc.get("document_type", "guidelines"))

                # Add to vectorstore
                if chunks:
                    vectorstore.add_documents(chunks)

                # Save document record in DB
                brand_doc = BrandDocument(
                    brand_profile_id=brand_id,
                    title=doc["title"],
                    document_type=doc.get("document_type", "guidelines"),
                    content=doc["content"][:5000],  # store first 5000 chars
                    chunk_count=len(chunks),
                    language=doc.get("language", "en"),
                    source_url=doc.get("source_url"),
                    file_name=doc.get("file_name")
                )
                db.add(brand_doc)

            # Update brand profile
            brand_profile.document_count = db.query(BrandDocument).filter(
                BrandDocument.brand_profile_id == brand_id
            ).count()
            brand_profile.total_chunks = db.query(BrandDocument).filter(
                BrandDocument.brand_profile_id == brand_id
            ).with_entities(BrandDocument.chunk_count).all()
            brand_profile.total_chunks = sum([c[0] for c in brand_profile.total_chunks])
            brand_profile.is_trained = True
            brand_profile.updated_at = datetime.utcnow()
            brand_profile.last_training_at = datetime.utcnow()
            
            # Calculate and set quality score
            quality_score = self._calculate_quality_score(db, brand_id)
            brand_profile.training_quality_score = quality_score

            db.commit()

            # Persist Chroma
            vectorstore.persist()

            return {
                "status": "success",
                "documents_processed": len(documents),
                "total_chunks": total_chunks,
                "training_quality_score": quality_score,
                "message": "Brand voice successfully trained. The AI will now respect your tone, values, and restrictions."
            }

        finally:
            db.close()

    def get_brand_context(
        self, 
        brand_id: UUID, 
        query: str, 
        max_chunks: int = 5,
        language: Optional[str] = None
    ) -> dict:
        """
        Retrieve relevant brand voice context using semantic search.
        This is called before any content generation.
        
        Enhanced with:
        - Language-aware retrieval for multi-language support
        - Usage tracking to improve future retrieval
        - Recommendations for improving training
        """
        vectorstore = self._get_vectorstore(brand_id)
        db = SessionLocal()

        try:
            brand_profile = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
            if not brand_profile or not brand_profile.is_trained:
                return {
                    "brand_name": brand_profile.brand_name if brand_profile else "Unknown",
                    "relevant_chunks": [],
                    "tone_instructions": "No brand voice has been trained yet. Please upload brand guidelines first.",
                    "restrictions": None,
                    "confidence": 0.1,
                    "primary_language": brand_profile.primary_language if brand_profile else "en",
                    "recommended_document_types": RECOMMENDED_DOCUMENT_TYPES[:3]
                }

            # Semantic search in vectorstore
            results = vectorstore.similarity_search(query, k=max_chunks * 2)  # Get more for filtering
            
            # Filter by language if specified, otherwise use brand's primary language
            target_language = language or brand_profile.primary_language or "en"
            
            # Prioritize documents in the target language
            filtered_results = []
            for doc in results:
                if doc.metadata.get("language", "en") == target_language:
                    filtered_results.append(doc)
            
            # If not enough in target language, fill with others
            if len(filtered_results) < max_chunks:
                for doc in results:
                    if doc not in filtered_results and len(filtered_results) < max_chunks:
                        filtered_results.append(doc)
            
            relevant_chunks = [doc.page_content for doc in filtered_results[:max_chunks]]
            
            # Update relevance scores for retrieved documents
            self._update_document_relevance(db, [doc.metadata.get("title") for doc in filtered_results[:max_chunks]])

            # Build tone instructions
            tone_instructions = self._build_tone_instructions(brand_profile)
            
            # Get recommendations for improvement
            recommendations = self._get_training_recommendations(db, brand_id)

            return {
                "brand_name": brand_profile.brand_name,
                "relevant_chunks": relevant_chunks,
                "tone_instructions": tone_instructions,
                "restrictions": brand_profile.do_not_use,
                "confidence": min(0.95, 0.6 + (brand_profile.training_quality_score / 200)),  # Scale to 0.6-0.95
                "primary_language": brand_profile.primary_language,
                "recommended_document_types": recommendations
            }

        finally:
            db.close()

    def _build_tone_instructions(self, profile: BrandProfile) -> str:
        """Construct clear instructions for the LLM based on the brand profile."""
        instructions = f"You are writing in the voice of {profile.brand_name}."

        if profile.industry:
            instructions += f" This is a {profile.industry} brand."
        if profile.target_audience:
            instructions += f" Target audience: {profile.target_audience}."
        if profile.tone_descriptors:
            instructions += f" Tone: {profile.tone_descriptors}."
        if profile.writing_style:
            instructions += f" Writing style: {profile.writing_style}."
        if profile.brand_personality:
            instructions += f" Brand personality: {profile.brand_personality}."
        if profile.key_values:
            instructions += f" Core values: {profile.key_values}."
        if profile.do_not_use:
            instructions += f" Never use these words or tones: {profile.do_not_use}."

        instructions += " Match the tone, style, and personality from the provided brand examples exactly. Keep the voice consistent, professional yet approachable."
        return instructions
    
    def _calculate_quality_score(self, db: SessionLocal, brand_id: UUID) -> int:
        """
        Calculate training quality score (0-100) based on:
        - Document diversity (different types)
        - Content coverage (total chunks)
        - Required document types present
        """
        documents = db.query(BrandDocument).filter(
            BrandDocument.brand_profile_id == brand_id,
            BrandDocument.is_active == True
        ).all()
        
        if not documents:
            return 0
        
        # Document type diversity (40 points max)
        doc_types = set(doc.document_type for doc in documents)
        type_diversity_score = min(40, len(doc_types) * 5)
        
        # Check for required types (20 points)
        required_present = sum(1 for t in REQUIRED_DOCUMENT_TYPES if t in doc_types)
        required_score = (required_present / len(REQUIRED_DOCUMENT_TYPES)) * 20
        
        # Content volume (30 points max) - based on total chunks
        total_chunks = sum(doc.chunk_count for doc in documents)
        volume_score = min(30, (total_chunks / 50) * 30)  # 50 chunks = max score
        
        # Document count (10 points max)
        count_score = min(10, len(documents) * 2)  # 5 docs = max score
        
        overall_score = int(type_diversity_score + required_score + volume_score + count_score)
        return min(100, overall_score)
    
    def _get_training_recommendations(self, db: SessionLocal, brand_id: UUID) -> List[str]:
        """Get list of recommended document types to improve training quality."""
        documents = db.query(BrandDocument).filter(
            BrandDocument.brand_profile_id == brand_id,
            BrandDocument.is_active == True
        ).all()
        
        existing_types = set(doc.document_type for doc in documents)
        missing_recommended = [t for t in RECOMMENDED_DOCUMENT_TYPES if t not in existing_types]
        
        # Return top 3 missing types, prioritizing required ones
        priority_order = REQUIRED_DOCUMENT_TYPES + [t for t in missing_recommended if t not in REQUIRED_DOCUMENT_TYPES]
        return [t for t in priority_order if t in missing_recommended][:3]
    
    def _update_document_relevance(self, db: SessionLocal, titles: List[str]) -> None:
        """Update relevance scores for retrieved documents."""
        if not titles:
            return
        
        try:
            db.query(BrandDocument).filter(
                BrandDocument.title.in_(titles)
            ).update({
                BrandDocument.relevance_score: BrandDocument.relevance_score + 1,
                BrandDocument.last_retrieved_at: datetime.utcnow()
            }, synchronize_session=False)
            db.commit()
        except Exception:
            db.rollback()
    
    def analyze_brand_voice(self, db: SessionLocal, brand_id: UUID) -> dict:
        """
        Comprehensive analysis of brand voice training quality.
        Returns detailed insights for improving the brand voice.
        """
        brand_profile = db.query(BrandProfile).filter(BrandProfile.id == brand_id).first()
        if not brand_profile:
            raise ValueError("Brand profile not found")
        
        documents = db.query(BrandDocument).filter(
            BrandDocument.brand_profile_id == brand_id,
            BrandDocument.is_active == True
        ).all()
        
        if not documents:
            return {
                "brand_id": brand_id,
                "overall_score": 0,
                "document_diversity_score": 0,
                "content_coverage_score": 0,
                "strengths": [],
                "recommendations": ["Upload your first brand document to get started"],
                "missing_document_types": RECOMMENDED_DOCUMENT_TYPES[:5]
            }
        
        # Calculate scores
        doc_types = set(doc.document_type for doc in documents)
        total_chunks = sum(doc.chunk_count for doc in documents)
        
        diversity_score = min(100, len(doc_types) * 12)  # Max at ~8 types
        coverage_score = min(100, (total_chunks / 100) * 100)  # Max at 100 chunks
        
        overall_score = int((diversity_score * 0.4) + (coverage_score * 0.6))
        
        # Identify strengths
        strengths = []
        if len(documents) >= 5:
            strengths.append(f"Good document variety ({len(documents)} documents)")
        if total_chunks >= 50:
            strengths.append(f"Substantial content coverage ({total_chunks} chunks)")
        if all(t in doc_types for t in REQUIRED_DOCUMENT_TYPES):
            strengths.append("All essential document types present")
        if brand_profile.tone_descriptors:
            strengths.append("Clear tone descriptors defined")
        if brand_profile.brand_personality:
            strengths.append("Well-defined brand personality")
        
        # Generate recommendations
        recommendations = []
        missing_types = self._get_training_recommendations(db, brand_id)
        if missing_types:
            recommendations.append(f"Add these document types: {', '.join(missing_types)}")
        if total_chunks < 30:
            recommendations.append("Upload more content to improve AI understanding")
        if not brand_profile.tone_descriptors:
            recommendations.append("Define tone descriptors (e.g., 'professional, friendly, authoritative')")
        if not brand_profile.target_audience:
            recommendations.append("Specify your target audience for better targeting")
        
        return {
            "brand_id": brand_id,
            "overall_score": overall_score,
            "document_diversity_score": diversity_score,
            "content_coverage_score": coverage_score,
            "strengths": strengths if strengths else ["Getting started - upload your first document"],
            "recommendations": recommendations,
            "missing_document_types": missing_types
        }
