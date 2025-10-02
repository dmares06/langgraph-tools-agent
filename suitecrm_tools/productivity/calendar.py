"""Calendar management tools."""

import json
from typing import Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool

@tool
def get_calendar_events(
    days_ahead: int = 7,
    event_type: Optional[str] = None,
    include_past: bool = False
) -> str:
    """
    Get calendar events and schedule for the broker.
    
    Args:
        days_ahead: Number of days to look ahead (default 7)
        event_type: Filter by event type (meeting, showing, closing, etc.)
        include_past: Whether to include past events from today
    
    Returns:
        JSON string with calendar events and schedule information
    """
    try:
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        start_date = today if not include_past else today - timedelta(days=1)
        
        # Simulated calendar events for framework
        sample_events = [
            {
                "id": "cal_event_1",
                "title": "Property Showing - 123 Main St",
                "start_time": (today + timedelta(days=1, hours=2)).isoformat(),
                "end_time": (today + timedelta(days=1, hours=3)).isoformat(),
                "event_type": "showing",
                "location": "123 Main St, City, State",
                "attendees": ["john.investor@email.com"],
                "description": "Office building tour with potential investor",
                "priority": "high"
            },
            {
                "id": "cal_event_2", 
                "title": "Closing - ABC Corp Deal",
                "start_time": (today + timedelta(days=3, hours=4)).isoformat(),
                "end_time": (today + timedelta(days=3, hours=6)).isoformat(),
                "event_type": "closing",
                "location": "Title Company Office",
                "attendees": ["abc.corp@email.com", "attorney@law.com"],
                "description": "$2.5M office building closing",
                "priority": "critical"
            },
            {
                "id": "cal_event_3",
                "title": "Client Meeting - Metro Investment",
                "start_time": (today + timedelta(days=5, hours=1)).isoformat(),
                "end_time": (today + timedelta(days=5, hours=2)).isoformat(),
                "event_type": "meeting",
                "location": "Coffee Shop Downtown",
                "attendees": ["metro.invest@email.com"],
                "description": "Discuss new investment opportunities",
                "priority": "medium"
            }
        ]
        
        # Filter by event type if specified
        if event_type:
            filtered_events = [e for e in sample_events if e["event_type"] == event_type]
        else:
            filtered_events = sample_events
        
        # Sort by start time
        filtered_events.sort(key=lambda x: x["start_time"])
        
        return json.dumps({
            "success": True,
            "date_range": f"{start_date.date()} to {end_date.date()}",
            "days_ahead": days_ahead,
            "event_type_filter": event_type,
            "total_events": len(filtered_events),
            "events": filtered_events,
            "upcoming_critical": [e for e in filtered_events if e["priority"] == "critical"],
            "this_week_summary": f"{len(filtered_events)} events scheduled",
            "integration_needed": "Google Calendar API or similar calendar service integration required for live data"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get calendar events: {str(e)}",
            "suggestion": "Calendar integration (Google Calendar API) required for live schedule data"
        })