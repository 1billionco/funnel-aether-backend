"""
SQLAlchemy models for Funnel Aether.
Import all models here to ensure they are registered with the Base metadata.
"""

from app.models.brand_voice import BrandProfile, BrandDocument

__all__ = ["BrandProfile", "BrandDocument"]
