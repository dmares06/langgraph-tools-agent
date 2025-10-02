"""Document analysis for OM/BOV creation."""

import json
from langchain_core.tools import tool
from ..utils import get_supabase_client, get_embedding

@tool
def analyze_listing_documents(listing_id: str, analysis_focus: str = "comprehensive") -> str:
    """
    Analyze uploaded listing documents to extract key information for OM/BOV creation.

    Args:
        listing_id: ID of the listing to analyze
        analysis_focus: Type of analysis ("financial", "legal", "physical", "comprehensive")

    Returns:
        JSON string with extracted listing insights and data points
    """
    try:
        supabase = get_supabase_client()

        listing_result = supabase.table("listings").select("*").eq("id", listing_id).execute()
        if not listing_result.data:
            return_json = json.dumps({
                "success": False,
                "error": f"Listing not found. Check the listing ID and try again: {listing_id}"
            })
            return return_json

        listing_info = listing_result.data[0]

        docs_result = supabase.table("listing_documents").select("*").eq("listing_id", listing_id).execute()

        if not docs_result.data:
            return_json = json.dumps({
                "success": True,
                "message": "No documents found to analyze. Upload documents first.",
                "listing_title": listing_info.get("title"),
                "suggestion": "Upload lease agreements, LOIs, financials, surveys, or appraisals to enable analysis."
            })
            return return_json

        analysis_queries = {
            "financial": [
                "rental income", "NOI", "cap rate", "operating expense",
                "rent roll", "vacancy rate", "gross income"
            ],
            "legal": [
                "lease terms", "tenant rights", "renewal option", "assignment clauses",
                "use restrictions", "compliance requirements"
            ],
            "physical": [
                "square footage", "building condition", "parking", "zoning",
                "improvements", "maintenance", "utilities", "amenities"
            ],
            "comprehensive": [
                "rental income", "NOI", "cap rate", "lease terms", "square footage",
                "building condition", "parking", "zoning", "tenant information"
            ]
        }

        search_terms = analysis_queries.get(analysis_focus, analysis_queries["comprehensive"])
        extracted_data = {}

        for term in search_terms:
            try:
                query_embedding = get_embedding(term)
                result = supabase.rpc(
                    'match_documents',
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.5,
                        "match_count": 3,
                        "listing_id": listing_id,
                    }
                ).execute()

                if result.data:
                    extracted_data[term] = {
                        "found": True,
                        "content": result.data[0]["chunk_text"][:300] + "...",
                        "source": result.data[0].get("source_document", "Unknown"),
                        "confidence": result.data[0].get("similarity")
                    }
                else:
                    extracted_data[term] = {"found": False}
                    
            except Exception as e:
                extracted_data[term] = {"found": False, "error": str(e)}
        
        return json.dumps({
            "success": True,
            "property_id": listing_id,
            "property_title": listing_info.get("title"),
            "analysis_focus": analysis_focus,
            "documents_analyzed": len(docs_result.data),
            "extracted_data": extracted_data,
            "document_list": [doc["filename"] for doc in docs_result.data],
            "message": f"Analyzed {len(docs_result.data)} documents for {analysis_focus} information"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to analyze listing documents: {str(e)}",
            "suggestion": "Ensure documents are uploaded and processed correctly"
        })