"""Calendar event creation and management."""

import json
from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    event_type: str = "meeting",
    location: Optional[str] = None,
    description: Optional[str] = None,
    attendees: Optional[list] = None,
    related_contact: Optional[str] = None,
    related_property: Optional[str] = None
) -> str:
    """
    Create a new calendar event.
    
    Args:
        title: Event title (required)
        start_time: Start time in ISO format (YYYY-MM-DDTHH:MM:SS) (required)
        end_time: End time in ISO format (required)
        event_type: Event type ('meeting', 'showing', 'closing', 'call', 'other')
        location: Event location
        description: Event description
        attendees: List of attendee email addresses
        related_contact: Associated contact ID
        related_property: Associated property/listing ID
    
    Returns:
        JSON string with created event information
    """
    try:
        supabase = get_supabase_client()
        
        event_data = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "event_type": event_type,
            "location": location,
            "description": description,
            "attendees": attendees or [],
            "related_contact": related_contact,
            "related_property": related_property,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("calendar_events").insert(event_data).execute()
        
        return json.dumps({
            "success": True,
            "event": result.data[0],
            "message": f"Successfully created event: {title}"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create calendar event: {str(e)}",
            "suggestion": "Ensure start_time and end_time are in ISO format (YYYY-MM-DDTHH:MM:SS)."
        })

@tool
def update_calendar_event(
    event_id: str,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    location: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update an existing calendar event.
    
    Args:
        event_id: ID of the event to update (required)
        title: Updated title
        start_time: Updated start time
        end_time: Updated end time
        location: Updated location
        description: Updated description
    
    Returns:
        JSON string with updated event information
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if title is not None:
            update_data["title"] = title
        if start_time is not None:
            update_data["start_time"] = start_time
        if end_time is not None:
            update_data["end_time"] = end_time
        if location is not None:
            update_data["location"] = location
        if description is not None:
            update_data["description"] = description
        
        result = supabase.table("calendar_events").update(update_data).eq("id", event_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Event with ID {event_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "event": result.data[0],
            "message": "Successfully updated event"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update event: {str(e)}"
        })