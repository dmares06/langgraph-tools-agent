"""Listing management tools."""

import json
from typing import List, Optional
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def get_listings(
    limit: int = 10,
    status: Optional[List[str]] = None,
    listing_type: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """
    Get listings from CRM with optional filtering.

    Args:
    limit: Maximum number of listings to return (default: 10)
    status: Filter by listing status (e.g. ['active', 'inactive','LOI',  'under contract', 'sold'])
    listing_type: Filter by listing type (e.g. ['sale', 'lease', 'auction', 'foreclosure'])
    min_price: Filter by minimum asking price (e.g. 1000000)
    max_price: Filter by maximum asking price (e.g. 10000000)

    Returns:
        JSON string with listing information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("listings").select("""
        *,
        contact:contacts(name, email, company)
        """)

        if status:
            query = query.contains("status", status)
        if listing_type:
            query = query.contains("listing_type", listing_type)
        if min_price:
            query = query.gte("asking_price", min_price)
        if max_price:
            query = query.lte("asking_price", max_price)

        result = query.limit(limit).order("created_at", desc=True).execute()

        return_json = json.dumps({
            "success": True,
            "listings": result.data,
            "count": len(result.data),
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve listings: {str(e)}",
            "suggestion": "Please verify your data pipeline and try again."
        })
    
    return return_json

@tool
def get_recent_inquiries(limit: int = 10, status: Optional[str] = None) -> str:
    """
    Get recent listing inquiries

    Args:
        limit: Maximum number of inquiries to return (default: 10)
        status: Filter by inquiry status (e.g. 'pending', 'responded', 'resolved', etc.)

    Returns:
        JSON string with inquiry information including listing details and contact information if provided
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("listing_inquiries").select("""
            *,
            listing:listings(address, asking_price, title, listing_type, status)
        """)

        if status:
            query = query.eq("status", status)

        result = query.limit(limit).order("created_at", desc=True).execute()
        
        return_json = json.dumps({
            "success": True,
            "inquiries": result.data,
            "count": len(result.data),
        }, default=str)
    
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve inquiries: {str(e)}",
        })
    
    return return_json

@tool
def get_campaigns_performance(limit: int = 5, status: Optional[str] = None) -> str:
    """
    Get campaign performance metrics.

    Args:
        limit: Maximum number of campaigns to return (default: 5)
        status: Filter by campaign status (optional)

    Returns:
        JSON string with campaign performance data
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("email_campaigns").select("*")
        
        if status:
            query = query.eq("status", status)
            
        result = query.limit(limit).order("created_at", desc=True).execute()
        
        return_json = json.dumps({
            "success": True,
            "campaigns": result.data,
            "count": len(result.data),
        }, default=str)
    
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve campaigns performance: {str(e)}",
        })
    
    return return_json
