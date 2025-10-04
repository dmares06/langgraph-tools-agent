# workflow_agents/tools/supabase_tools.py
"""
Tools for querying SuiteCRM data from Supabase for data mapping.
"""

import logging
from typing import Optional
from supabase import create_client, Client
from langchain_core.tools import tool

from workflow_agents.config import config

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(config.supabase_url, config.supabase_key)


@tool
def search_contacts(
    user_id: str,
    query: str,
    limit: int = 10
) -> dict:
    """
    Search for contacts in SuiteCRM by name or email.
    
    Args:
        user_id: User UUID
        query: Search query (name or email)
        limit: Maximum results
        
    Returns:
        Matching contacts
    """
    supabase = get_supabase_client()
    
    try:
        # Search by name or email (assuming contacts table exists)
        # This is a placeholder - adjust based on your actual schema
        result = supabase.table("contacts").select("*").or_(
            f"name.ilike.%{query}%,email.ilike.%{query}%"
        ).eq("owner", user_id).limit(limit).execute()
        
        contacts = result.data if result.data else []
        
        return {
            "success": True,
            "contacts": contacts,
            "count": len(contacts),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error searching contacts: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def search_deals(
    user_id: str,
    query: str,
    limit: int = 10
) -> dict:
    """
    Search for deals in SuiteCRM.
    
    Args:
        user_id: User UUID
        query: Search query
        limit: Maximum results
        
    Returns:
        Matching deals
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("deals").select("*").ilike("name", f"%{query}%").eq("owner", user_id).limit(limit).execute()
        
        deals = result.data if result.data else []
        
        return {
            "success": True,
            "deals": deals,
            "count": len(deals),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error searching deals: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def search_listings(
    user_id: str,
    query: str,
    limit: int = 10
) -> dict:
    """
    Search for property listings in SuiteCRM.
    
    Args:
        user_id: User UUID
        query: Search query (address)
        limit: Maximum results
        
    Returns:
        Matching listings
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("listings").select("*").ilike("address", f"%{query}%").eq("owner", user_id).limit(limit).execute()
        
        listings = result.data if result.data else []
        
        return {
            "success": True,
            "listings": listings,
            "count": len(listings),
            "query": query
        }
        
    except Exception as e:
        logger.error(f"Error searching listings: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_contact_by_email(user_id: str, email: str) -> dict:
    """
    Get contact by exact email match.
    
    Args:
        user_id: User UUID
        email: Email address
        
    Returns:
        Contact if found
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("contacts").select("*").eq("email", email.lower()).eq("owner", user_id).execute()
        
        if result.data:
            return {
                "success": True,
                "found": True,
                "contact": result.data[0],
                "confidence": 1.0,
                "match_type": "exact"
            }
        else:
            return {
                "success": True,
                "found": False,
                "email": email
            }
        
    except Exception as e:
        logger.error(f"Error getting contact by email: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def fuzzy_match_contact(
    user_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    phone: Optional[str] = None
) -> dict:
    """
    Fuzzy match contact by multiple fields.
    
    Args:
        user_id: User UUID
        name: Contact name
        email: Email address
        phone: Phone number
        
    Returns:
        Best matching contacts with confidence scores
    """
    supabase = get_supabase_client()
    
    try:
        matches = []
        
        # Try email first (highest confidence)
        if email:
            email_result = supabase.table("contacts").select("*").eq("email", email.lower()).eq("owner", user_id).execute()
            if email_result.data:
                for contact in email_result.data:
                    matches.append({
                        "contact": contact,
                        "confidence": 0.95,
                        "match_type": "email_exact"
                    })
        
        # Try name (medium confidence)
        if name and not matches:
            name_result = supabase.table("contacts").select("*").ilike("name", f"%{name}%").eq("owner", user_id).limit(5).execute()
            if name_result.data:
                for contact in name_result.data:
                    matches.append({
                        "contact": contact,
                        "confidence": 0.7,
                        "match_type": "name_fuzzy"
                    })
        
        # Try phone (medium confidence)
        if phone and not matches:
            phone_clean = phone.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
            phone_result = supabase.table("contacts").select("*").ilike("phone", f"%{phone_clean}%").eq("owner", user_id).limit(5).execute()
            if phone_result.data:
                for contact in phone_result.data:
                    matches.append({
                        "contact": contact,
                        "confidence": 0.75,
                        "match_type": "phone_fuzzy"
                    })
        
        # Sort by confidence
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "success": True,
            "matches": matches[:5],  # Top 5 matches
            "count": len(matches)
        }
        
    except Exception as e:
        logger.error(f"Error fuzzy matching contact: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def create_contact(
    user_id: str,
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    company: Optional[str] = None
) -> dict:
    """
    Create a new contact in SuiteCRM.
    
    Args:
        user_id: User UUID
        name: Contact name
        email: Email address
        phone: Phone number
        company: Company name
        
    Returns:
        Created contact
    """
    supabase = get_supabase_client()
    
    try:
        contact_data = {
            "owner": user_id,
            "name": name,
            "email": email,
            "phone": phone,
            "company": company
        }
        
        result = supabase.table("contacts").insert(contact_data).execute()
        
        if result.data:
            return {
                "success": True,
                "contact": result.data[0],
                "message": f"Created contact: {name}"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create contact"
            }
        
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }