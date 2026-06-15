"""
Brand Voice Service - Core RAG logic for Funnel Aether.
This is the heart of the human-AI hybrid experience.
"""

import os
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OpenAIEmbeddings, AnthropicEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LCDocument

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.brand_voice import BrandProfile, BrandDocument

settings = get_settings()


class BrandVoiceService:
    """
    Handles brand voice training and context retrieval using RAG.
    Designed so that every generation can pull relevant brand voice context.
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
            # Default to Anthropic or a compatible embedding model
            # For simplicity in MVP we use a simple local-friendly approach if keys missing
            try:
                self.embeddings = AnthropicEmbeddings(anthropic_api_key=self.settings.ANTHROPIC_API_KEY)
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
        documents: List[dict]  # list of {"title": str, "content": str, "document_type": str}
    ) -> dict:
        """
        Upload brand documents, chunk them, embed, and store in vector DB.
        This trains the brand voice.
        """
        vectorstore = self._get_vectorstore(brand_id)
        db = SessionLocal()
        
        total_chunks = 0

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
                        "brand_id": str(brand_id)
                    }
                )
                
                # Split into chunks
                chunks = self.text_splitter.split_documents([lc_doc])
                total_chunks += len(chunks)

                # Add to vectorstore
                if chunks:
                    vectorstore.add_documents(chunks)

                # Save document record in DB
                brand_doc = BrandDocument(
                    brand_profile_id=brand_id,
                    title=doc["title"],
                    document_type=doc.get("document_type", "guidelines"),
                    content=doc["content"][:5000],  # store first 5000 chars
                    chunk_count=len(chunks)
                )
                db.add(brand_doc)

            # Update brand profile
            brand_profile.document_count = db.query(BrandDocument).filter(
                BrandDocument.brand_profile_id == brand_id
            ).count()
            brand_profile.is_trained = True
            brand_profile.updated_at = datetime.utcnow()

            db.commit()

            # Persist Chroma
            vectorstore.persist()

            return {
                "status": "success",
                "documents_processed": len(documents),
                "total_chunks": total_chunks,
                "message": "Brand voice successfully trained. The AI will now respect your tone, values, and restrictions."
            }

        finally:
            db.close()

    def get_brand_context(
        self, 
        brand_id: UUID, 
        query: str, 
        max_chunks: int = 5
    ) -> dict:
        """
        Retrieve relevant brand voice context using semantic search.
        This is called before any content generation.
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
                    "confidence": 0.1
                }

            # Semantic search in vectorstore
            results = vectorstore.similarity_search(query, k=max_chunks)
            relevant_chunks = [doc.page_content for doc in results]

            # Build tone instructions
            tone_instructions = self._build_tone_instructions(brand_profile)

            return {
                "brand_name": brand_profile.brand_name,
                "relevant_chunks": relevant_chunks,
                "tone_instructions": tone_instructions,
                "restrictions": brand_profile.do_not_use,
                "confidence": 0.85 if brand_profile.document_count >= 3 else 0.6
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
        if profile.key_values:
            instructions += f" Core values: {profile.key_values}."
        if profile.do_not_use:
            instructions += f" Never use these words or tones: {profile.do_not_use}."

        instructions += " Match the tone, style, and personality from the provided brand examples exactly. Keep the voice consistent, professional yet approachable."
        return instructions
