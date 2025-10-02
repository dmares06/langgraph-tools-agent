"""Task management tools."""

import json
from typing import Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool

@tool
def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_within_days: Optional[int] = None,
    limit: int = 20
) -> str:
    """
    Get tasks and to-dos for the broker.
    
    Args:
        status: Filter by status ('pending', 'in_progress', 'completed', 'overdue')
        priority: Filter by priority ('low', 'medium', 'high', 'critical')
        due_within_days: Show tasks due within X days
        limit: Maximum number of tasks to return (default 20)
    
    Returns:
        JSON string with task information
    """
    try:
        today = datetime.now()
        
        # Simulated task data for framework
        sample_tasks = [
            {
                "id": "task_1",
                "title": "Follow up with ABC Corp on lease renewal",
                "description": "Lease expires in 60 days, need to discuss renewal terms",
                "status": "pending",
                "priority": "high",
                "due_date": (today + timedelta(days=3)).isoformat(),
                "create_date": (today - timedelta(days=5)).isoformat(),
                "assigned_to": "broker",
                "related_contact": "ABC Corp",
                "related_property": "123 Office Building",
                "task_type": "follow_up",
                "estimated_time": "30 minutes"
            },
            {
                "id": "task_2",
                "title": "Prepare OM for downtown retail property",
                "description": "Create offering memorandum for 456 Retail Plaza listing",
                "status": "in_progress", 
                "priority": "medium",
                "due_date": (today + timedelta(days=7)).isoformat(),
                "created_date": (today - timedelta(days=2)).isoformat(),
                "assigned_to": "broker",
                "related_contact": None,
                "related_property": "456 Retail Plaza",
                "task_type": "marketing",
                "estimated_time": "2 hours"
            },
            {
                "id": "task_3",
                "title": "Schedule property inspection for warehouse deal",
                "description": "Coordinate inspection with buyer's team for industrial property",
                "status": "pending",
                "priority": "critical",
                "due_date": (today + timedelta(days=1)).isoformat(),
                "created_date": today.isoformat(),
                "assigned_to": "broker",
                "related_contact": "Industrial Investors LLC",
                "related_property": "789 Warehouse Complex",
                "task_type": "coordination",
                "estimated_time": "45 minutes"
            },
            {
                "id": "task_4",
                "title": "Update CRM with new investor contacts",
                "description": "Add contacts from networking event to CRM system",
                "status": "pending",
                "priority": "low",
                "due_date": (today + timedelta(days=14)).isoformat(),
                "created_date": (today - timedelta(days=1)).isoformat(),
                "assigned_to": "broker",
                "related_contact": None,
                "related_property": None,
                "task_type": "admin",
                "estimated_time": "1 hour"
            }
        ]
        
        # Apply filters
        filtered_tasks = sample_tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
            
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
            
        if due_within_days:
            cutoff_date = today + timedelta(days=due_within_days)
            filtered_tasks = [t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) <= cutoff_date]
        
        # Sort by due date and priority
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        filtered_tasks.sort(key=lambda x: (datetime.fromisoformat(x["due_date"]), -priority_order.get(x["priority"], 0)))
        
        # Limit results
        filtered_tasks = filtered_tasks[:limit]
        
        # Calculate task statistics
        overdue_tasks = [t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) < today and t["status"] != "completed"]
        high_priority_tasks = [t for t in filtered_tasks if t["priority"] in ["high", "critical"]]
        
        return json.dumps({
            "success": True,
            "total_tasks": len(filtered_tasks),
            "filters_applied": {
                "status": status,
                "priority": priority,
                "due_within_days": due_within_days
            },
            "tasks": filtered_tasks,
            "task_summary": {
                "overdue_count": len(overdue_tasks),
                "high_priority_count": len(high_priority_tasks),
                "due_today": len([t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]).date() == today.date()]),
                "due_this_week": len([t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) <= today + timedelta(days=7)])
            },
            "integration_needed": "Task management system integration required for live task data"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get tasks: {str(e)}",
            "suggestion": "Task management system integration required"
        })