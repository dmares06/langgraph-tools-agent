"""Contact creation and update operations."""

import json
from typing import Optional, Dict, Any
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_contact(
    name: str,
    email: str,
    company: Optional[str] = None,
    phone: Optional[str] = None,
    target_size: Optional[str] = None,
    source: Optional[str] = None,
    tags: Optional[list] = None,
    asset_type: Optional[list] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    notes: Optional[str] = None
) -> str:
    """
    Create a new contact in the CRM.
    
    Args:
        name: Contact's full name (required)
        title: Contact's title 
        email: Contact's email address (required)
        company: Company name
        source: Source of the contact [cold outreach, referral, website, networking event,social media, advertisement]
        target_size: Target size of property interest [ex: 1,000 sqft, 10,000 sqft, 100,000 sqft, 1,000,000 sqft]
        phone: Phone number
        tags: List of tags (e.g., ['High-Value', 'investor'])
        asset_type: List of asset interests (e.g., ['office', 'retail'])
        budget_min: Minimum budget [ex: 1,000,000, 2,000,000, 3,000,000, 4,000,000, 5,000,000]
        budget_max: Maximum budget
        notes: Additional notes about the contact
    
    Returns:
        JSON string with created contact information
    """
    try:
        supabase = get_supabase_client()
        
        contact_data = {
            "name": name,
            "email": email,
            "company": company,
            "source": source,
            "target_size": target_size,
            "phone_number": phone,
            "tags": tags or [],
            "asset_type": asset_type or [],
            "budget_min": budget_min,
            "budget_max": budget_max,
            "notes": notes,
            "created_at": datetime.now().isoformat(),
            "email_subscriber": True
        }
        
        result = supabase.table("contacts").insert(contact_data).execute()
        
        return json.dumps({
            "success": True,
            "contact": result.data[0],
            "message": f"Successfully created contact: {name}"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create contact: {str(e)}",
            "suggestion": "Check that all required fields are provided and valid."
        })

@tool
def update_contact(
    contact_id: str,
    name: Optional[str] = None,
    email: Optional[str] = None,
    company: Optional[str] = None,
    source: Optional[str] = None,
    target_size: Optional[str] = None,
    phone: Optional[str] = None,
    tags: Optional[list] = None,
    asset_type: Optional[list] = None,
    budget_min: Optional[float] = None,
    budget_max: Optional[float] = None,
    notes: Optional[str] = None
) -> str:
    """
    Update an existing contact in the CRM.
    
    Args:
        contact_id: ID of the contact to update (required)
        name: Updated name
        email: Updated email
        company: Updated company
        source: Updated source
        target_size: Updated target size
        phone: Updated phone number
        tags: Updated tags list
        asset_type: Updated asset interests
        budget_min: Updated minimum budget
        budget_max: Updated maximum budget
        notes: Updated notes
    
    Returns:
        JSON string with updated contact information
    """
    try:
        supabase = get_supabase_client()
        
        # Build update data dict with only provided fields
        update_data: Dict[str, Any] = {"updated_at": datetime.now().isoformat()}
        
        if name is not None:
            update_data["name"] = name
        if email is not None:
            update_data["email"] = email
        if company is not None:
            update_data["company"] = company
        if source is not None:
            update_data["source"] = source
        if target_size is not None:
            update_data["target_size"] = target_size
        if phone is not None:
            update_data["phone_number"] = phone
        if tags is not None:
            update_data["tags"] = tags
        if asset_type is not None:
            update_data["asset_type"] = asset_type
        if budget_min is not None:
            update_data["budget_min"] = budget_min
        if budget_max is not None:
            update_data["budget_max"] = budget_max
        if notes is not None:
            update_data["notes"] = notes
        
        result = supabase.table("contacts").update(update_data).eq("id", contact_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Contact with ID {contact_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "contact": result.data[0],
            "message": f"Successfully updated contact"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update contact: {str(e)}"
        })