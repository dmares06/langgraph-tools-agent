"""Embedding utilities for document search."""

import os
from typing import List
from openai import OpenAI

def get_openai_client() -> OpenAI:
    """Get OpenAI client for embeddings."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable.")
    return OpenAI(api_key=api_key)

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for text."""
    try:
        client = get_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        raise Exception(f"Failed to get embedding: {str(e)}")