"""Daily summary and reporting tools."""

import json
from datetime import datetime, timedelta
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def get_daily_summary() -> str:
    """
    Get daily summary of key CRM metrics and activities.

    Returns:
        JSON string with daily summary data.
    """
    try:
        supabase = get_supabase_client()
        today = datetime.now().date()

        new_contacts = supabase.table("contacts").select("*").gte("created_at", today.isoformat()).execute()

        week_end = today + timedelta(days=7)
        closing_deals = supabase.table("deals").select("*").gte("expected_close", today.isoformat()).lte("expected_close", week_end.isoformat()).execute()
        
        pending_inquiries = supabase.table("listing_inquiries").select("*").eq("status", "pending").execute()
        
        active_listings = supabase.table("listings").select("*").eq("status", "ACTIVE").execute()

        summary = {
            "date": today.isoformat(),
            "new_contacts_today": len(new_contacts.data),
            "deals_closing_this_week": len(closing_deals.data),
            "pending_inquiries": len(pending_inquiries.data),
            "active_listings": len(active_listings.data),
            "recent_contacts": new_contacts.data,
        }

        return_json = json.dumps({
            "success": True,
            "summary": summary,
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Failed to get daily summary: {str(e)}"
        })
    
    return return_json