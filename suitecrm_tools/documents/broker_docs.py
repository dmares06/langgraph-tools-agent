"""Broker document management tools."""

import json
from typing import Optional
from langchain_core.tools import tool
from ..utils import get_supabase_client, get_embedding

@tool
def get_broker_documents(
    document_type: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Get list of general broker documents (contracts, LOIs, lease agreements, etc.).
    
    Args:
        document_type: Filter by type (contract, loi, lease, legal, business_plan, etc.)
        limit: Maximum number of documents to return (default 20)
    
    Returns:
        JSON string with broker document information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("broker_documents").select("*")
        
        if document_type:
            query = query.eq("document_type", document_type)
            
        result = query.limit(limit).order("uploaded_at", desc=True).execute()
        
        return json.dumps({
            "success": True,
            "documents": result.data,
            "count": len(result.data)
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get broker documents: {str(e)}"
        })

@tool
def search_broker_documents(
    query: str,
    document_type: Optional[str] = None,
    match_threshold: float = 0.7,
    limit: int = 5
) -> str:
    """
    Search through broker's general documents using semantic search.
    
    Args:
        query: Search query text (e.g. "termination clause", "payment terms", "renewal options")
        document_type: Filter by document type (contract, loi, lease, etc.)
        match_threshold: Similarity threshold (0.0-1.0, default 0.7)
        limit: Maximum number of results (default 5)
    
    Returns:
        JSON string with matching document chunks and sources
    """
    try:
        supabase = get_supabase_client()
        
        # Check if broker has documents
        doc_check = supabase.table("broker_documents").select("id, filename, document_type")
        if document_type:
            doc_check = doc_check.eq("document_type", document_type)
        doc_check = doc_check.execute()
        
        if not doc_check.data:
            return json.dumps({
                "success": True,
                "message": f"No {'broker' if not document_type else document_type} documents found. Upload documents first to enable search.",
                "results": [],
                "count": 0,
                "suggestion": "Upload broker documents (contracts, LOIs, leases) to search through them"
            })
        
        query_embedding = get_embedding(query)
        
        result = supabase.rpc(
            'match_broker_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'document_type_filter': document_type,
                'match_count': limit
            }
        ).execute()
        
        if not result.data:
            return json.dumps({
                "success": True,
                "message": f"No relevant content found for '{query}' in broker documents.",
                "results": [],
                "count": 0,
                "available_documents": [{"filename": doc["filename"], "type": doc["document_type"]} for doc in doc_check.data],
                "suggestion": f"Try different search terms or browse the {len(doc_check.data)} available documents directly"
            })
        
        formatted_results = []
        for row in result.data:
            doc_result = supabase.table("broker_documents").select("filename, document_type").eq("id", row.get("document_id", "")).execute()
            doc_info = doc_result.data[0] if doc_result.data else {}
            
            formatted_results.append({
                "chunk_text": row["chunk_text"],
                "similarity": round(row["similarity"], 3),
                "source_document": doc_info.get("filename", "Unknown document"),
                "document_type": doc_info.get("document_type", "Unknown type"),
                "metadata": row.get("metadata", {})
            })
        
        return json.dumps({
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "message": f"Found {len(formatted_results)} relevant sections for '{query}'"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Unable to search broker documents: {str(e)}",
            "suggestion": "Check that documents have been processed for search"
        })