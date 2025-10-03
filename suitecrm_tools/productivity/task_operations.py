"""Task creation and management operations."""

import json
from typing import Optional
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def create_task(
    title: str,
    due_date: str,
    priority: str = "medium",
    description: Optional[str] = None,
    related_contact: Optional[str] = None,
    related_property: Optional[str] = None,
    task_type: Optional[str] = None
) -> str:
    """
    Create a new task in the CRM.
    
    Args:
        title: Task title (required)
        due_date: Due date in ISO format YYYY-MM-DD (required)
        priority: Priority level ('low', 'medium', 'high', 'critical')
        description: Task description
        related_contact: Associated contact ID
        related_property: Associated property/listing ID
        task_type: Task category ('follow_up', 'marketing', 'coordination', 'admin')
    
    Returns:
        JSON string with created task information
    """
    try:
        supabase = get_supabase_client()
        
        task_data = {
            "title": title,
            "description": description,
            "due_date": due_date,
            "priority": priority,
            "status": "pending",
            "task_type": task_type,
            "related_contact": related_contact,
            "related_property": related_property,
            "created_date": datetime.now().isoformat()
        }
        
        result = supabase.table("tasks").insert(task_data).execute()
        
        return json.dumps({
            "success": True,
            "task": result.data[0],
            "message": f"Successfully created task: {title} (due: {due_date})"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create task: {str(e)}",
            "suggestion": "Ensure due_date is in YYYY-MM-DD format and priority is valid."
        })

@tool
def update_task(
    task_id: str,
    title: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_date: Optional[str] = None,
    description: Optional[str] = None
) -> str:
    """
    Update an existing task.
    
    Args:
        task_id: ID of the task to update (required)
        title: Updated title
        status: Updated status ('pending', 'in_progress', 'completed', 'overdue')
        priority: Updated priority
        due_date: Updated due date
        description: Updated description
    
    Returns:
        JSON string with updated task information
    """
    try:
        supabase = get_supabase_client()
        
        update_data = {}
        
        if title is not None:
            update_data["title"] = title
        if status is not None:
            update_data["status"] = status
        if priority is not None:
            update_data["priority"] = priority
        if due_date is not None:
            update_data["due_date"] = due_date
        if description is not None:
            update_data["description"] = description
        
        result = supabase.table("tasks").update(update_data).eq("id", task_id).execute()
        
        if not result.data:
            return json.dumps({
                "success": False,
                "error": f"Task with ID {task_id} not found"
            })
        
        return json.dumps({
            "success": True,
            "task": result.data[0],
            "message": "Successfully updated task"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update task: {str(e)}"
        })