"""Utility functions and shared resources for SuiteCRE CRM tools."""

from .database import get_supabase_client
from .embeddings import get_openai_client, get_embedding

__all__ = ['get_supabase_client', 'get_openai_client', 'get_embedding']