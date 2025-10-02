"""Contact management tools."""

import json
from typing import List, Optional
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool 
def get_contacts(
    limit: int = 10,
    tags: Optional[List[str]] = None, 
    asset_type: Optional[List[str]] = None,
    email_subscribed: Optional[bool] = None
) -> str:
    """
    Get contacts from CRM with optional filtering.
    
    Args:
        limit: Maximum number of contacts to return (default: 10)
        tags: Filter by contact tags (e.g. ['High-Value', 'investor', 'seller'])
        asset_type: Filter by asset types (e.g. ['office', 'retail', 'industrial', 'multifamily', 'mixed-use', 'warehouse', 'land', 'other'])
        email_subscribed: Filter by email subscription status

    Returns:
        JSON string with contact information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("contacts").select("*")

        if tags:
            query = query.contains("tags", tags)
        if asset_type:
            query = query.contains("asset_type", asset_type)
        if email_subscribed is not None:
            query = query.eq("email_subscriber", email_subscribed)

        result = query.limit(limit).order("created_at", desc=True).execute()

        if not result.data:
            return_json = json.dumps({
                "success": True,
                "message": "No contacts found matching the criteria. Try adjusting your filters or check if contacts have been added to your CRM.",
                "contacts": [],
                "count": 0,
                "suggestion": "Remove filters or add new contacts to see results."
            })
        else:
            return_json = json.dumps({
                "success": True,
                "contacts": result.data,
                "count": len(result.data),
                "message": f"Found {len(result.data)} contacts matching your criteria."
            }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve contacts: {str(e)}",
            "suggestion": "Please check your database and try again."
        })
    
    return return_json