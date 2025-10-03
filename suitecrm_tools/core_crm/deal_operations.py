"""Deal creation and update operations."""

import json
from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_deal(
    title: str,
    contact_id: str,
    category: str,
    priority: str,
    deadline: str,
    description: str,
    deal_value: float,
    stage: str = "qualified",
    expected_close: Optional[str] = None,
    property_address: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Create a new deal in the pipeline.
    
    Args:
        title: Deal title (required)
        contact_id: Associated contact ID (required)
        category: Deal category (required)
        priority: Deal priority (required)
        deadline: Deal deadline (required)
        description: Deal description (required)
        deal_value: Deal value in dollars (required)
        stage: Deal stage ('qualified', 'proposal', 'negotiation', 'closing', 'closed', 'lost')
        expected_close: Expected closing date (ISO format: YYYY-MM-DD)
        property_address: Property address if applicable
        notes: Additional notes about the deal
    
    Returns:
        JSON string with created deal information
    """
    try:
        supabase = get_supabase_client()
        
        deal_data = {
            "title": title,
            "contact_id": contact_id,
            "category": category,
            "priority": priority,
            "deadline": deadline,
            "description": description,
            "deal_value": deal_value,
            "stage": stage,
            "expected_close": expected_close,
            "property_address": property_address,
            "notes": notes,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("deals").insert(deal_data).execute()
        
        return json.dumps({
            "success": True,
            "deal": result.data[0],
            "message": f"Successfully created deal: {title} (${deal_value:,.0f})"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create deal: {str(e)}",
            "suggestion": "Verify the contact_id exists and all required fields are provided."
        })

@tool
def update_deal(
    deal_id: str,
    title: Optional[str] = None,
    category: Optional[str] = None,
    priority: Optional[str] = None,
    deadline: Optional[str] = None,
    description: Optional[str] = None,
    deal_value: Optional[float] = None,
    stage: Optional[str] = None,
    expected_close: Optional[str] = None,
    notes: Optional[str] = None
) -> str:
    """
    Update an existing deal in the pipeline.
    
    Args:
        deal_id: ID of the deal to update (required)
        title: Updated title
        category: Updated category
        priority: Updated priority
        deadline: Updated deadline
        description: Updated description
        deal_value: Updated deal value
        stage: Updated stage
        expected_close: Updated expected closing date
        notes: Updated notes
    
    Returns:
        JSON string with updated deal information
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if title is not None:
            update_data["title"] = title
        if category is not None:
            update_data["category"] = category
        if priority is not None:
            update_data["priority"] = priority
        if deadline is not None:
            update_data["deadline"] = deadline
        if description is not None:
            update_data["description"] = description
        if deal_value is not None:
            update_data["deal_value"] = deal_value
        if stage is not None:
            update_data["stage"] = stage
        if expected_close is not None:
            update_data["expected_close"] = expected_close
        if notes is not None:
            update_data["notes"] = notes
        
        result = supabase.table("deals").update(update_data).eq("id", deal_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Deal with ID {deal_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "deal": result.data[0],
            "message": "Successfully updated deal"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update deal: {str(e)}"
        })