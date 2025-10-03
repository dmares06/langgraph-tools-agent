"""Note creation and management."""

import json
from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_note(
    content: str,
    related_to_type: str,
    related_to_id: str,
    title: Optional[str] = None
) -> str:
    """
    Create a note attached to a contact, deal, or listing.
    
    Args:
        content: Note content (required)
        related_to_type: Type of related entity ('contact', 'deal', 'listing')
        related_to_id: ID of the related entity (required)
        title: Optional note title
    
    Returns:
        JSON string with created note information
    """
    try:
        supabase = get_supabase_client()
        
        note_data = {
            "title": title,
            "content": content,
            "related_to_type": related_to_type,
            "related_to_id": related_to_id,
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("notes").insert(note_data).execute()
        
        return json.dumps({
            "success": True,
            "note": result.data[0],
            "message": f"Successfully created note for {related_to_type}"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create note: {str(e)}",
            "suggestion": "Verify the related_to_id exists and related_to_type is valid."
        })

@tool
def update_note(
    note_id: str,
    content: Optional[str] = None,
    title: Optional[str] = None
) -> str:
    """
    Update an existing note.
    
    Args:
        note_id: ID of the note to update (required)
        content: Updated content
        title: Updated title
    
    Returns:
        JSON string with updated note information
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {"updated_at": datetime.now().isoformat()}
        
        if content is not None:
            update_data["content"] = content
        if title is not None:
            update_data["title"] = title
        
        result = supabase.table("notes").update(update_data).eq("id", note_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Note with ID {note_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "note": result.data[0],
            "message": "Successfully updated note"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update note: {str(e)}"
        })