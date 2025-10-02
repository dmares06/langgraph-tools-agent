"""Listing document management tools."""

import json
from langchain_core.tools import tool
from ..utils import get_supabase_client, get_embedding

@tool
def get_listing_documents(listing_id: str) -> str:
    """
    Get list of documents uploaded for a specific listing.

    Args:
        listing_id: ID of the listing to get documents for

    Returns:
        JSON string with document information
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("listing_documents").select("*").eq("listing_id", listing_id).execute()
        
        return_json = json.dumps({
            "success": True,
            "documents": result.data,
            "count": len(result.data),
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Failed to get listing documents: {str(e)}"
        })
    
    return return_json

@tool 
def search_listing_documents(
    listing_id: str,
    query: str,
    match_threshold: float = 0.7,
    limit: int = 5,
) -> str:
    """
    Search through listing documents using semantic search.

    Args: 
        listing_id: ID of the listing to search documents for
        query: Search query text (e.g. 'renewal terms', 'square footage', 'amenities', 'cap rate', etc.)
        match_threshold: Similarity threshold (0.0-1.0, default 0.7)
        limit: Maximum number of documents to return (default 5)

    Returns:
        JSON string with matching document chunks and sources results
    """
    try:
        supabase = get_supabase_client()
        doc_check = supabase.table("listing_documents").select("id, filename").eq("listing_id", listing_id).execute()
        
        if not doc_check.data:
            return_json = json.dumps({
                "success": True,
                "message": f"No documents found for listing {listing_id}",
                "results": [],
                "count": 0,
                "suggestion": "Upload listing documents (leases, appraisals, financial reports) to search through them."
            })
        else:
            query_embedding = get_embedding(query)

            result = supabase.rpc(
                'match_documents',
                {
                    "query_embedding": query_embedding,
                    "match_threshold": match_threshold,
                    "match_count": limit,
                    "listing_id": listing_id,
                }
            ).execute()

            if not result.data:
                return_json = json.dumps({
                    "success": True,
                    "message": f"No relevant content for '{query}' in listing documents. Try different search terms or check if documents contain this information.",
                    "results": [],
                    "count": 0,
                    "available_documents": [doc["filename"] for doc in doc_check.data],
                    "suggestion": f"Try searching for related terms or browse the {len(doc_check.data)} available documents in your listing."
                })
            else:
                formatted_results = []
                for row in result.data:
                    doc_result = supabase.table("listing_documents").select("filename, document_type").eq("id", row.get("document_id", "")).execute()
                    doc_info = doc_result.data[0] if doc_result.data else {}

                    formatted_results.append({
                        "chunk_text": row["chunk_text"],
                        "similarity": round(row["similarity"], 3),
                        "chunk_type": row.get("chunk_type"),
                        "source_document": doc_info.get("filename", "Unknown document"),
                        "metadata": row.get("metadata", {}),
                    })

                return_json = json.dumps({
                    "success": True,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "query": query,
                    "listing_id": listing_id,
                    "message": f"Found {len(formatted_results)} relevant sections for '{query}' in listing documents.",
                }, default=str)
                
        return return_json

    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to search listing documents: {str(e)}",
            "query": query,
            "listing_id": listing_id,
            "suggestion": "Check that the listing ID is correct and documents have processed for search."
        })
        return return_json