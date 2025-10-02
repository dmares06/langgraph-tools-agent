"""Deal management tools."""

import json
from typing import Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def get_deals(
    limit: int = 10,
    stage: Optional[str] = None,
    min_value: Optional[float] = None,
    closing_soon_days: Optional[int] = None,
) -> str:
    """
    Get deals from pipeline with optional filtering. 

    Args:
        limit: Maximum number of deals to return (default: 10)
        stage: Filter by deal stage (e.g. 'qualified','proposal', 'negotiation', 'closing')
        min_value: Filter by minimum deal value (e.g. 1000000)
        closing_soon_days: Show deals closing within X days(e.g. closing in 30 days)

    Returns:
        JSON string with deal information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("deals").select("""
            *,
            contacts:contacts(name, email, company)
        """)

        if stage: 
            query = query.eq("stage", stage)
        if min_value:
            query = query.gte("value", min_value)
        if closing_soon_days:
            cutoff_date = datetime.now() + timedelta(days=closing_soon_days)
            query = query.lte("expected_close", cutoff_date.isoformat())

        result = query.limit(limit).order("created_at", desc=True).execute()

        if not result.data:
            filter_msg = []
            if stage: filter_msg.append(f"stage: {stage}")
            if min_value: filter_msg.append(f"value > ${min_value:,.0f}")
            if closing_soon_days: filter_msg.append(f"closing within {closing_soon_days} days")

            return_json = json.dumps({
                "success": True,
                "message": f"No deals found with {' and '.join(filter_msg) if filter_msg else 'your criteria'}.",
                "deals": [],
                "count": 0,
                "suggestion": "Try different filters or check if deals have been added to your pipeline."
            })
        else:
            return_json = json.dumps({
                "success": True,
                "deals": result.data,
                "count": len(result.data),
                "message": f"Found {len(result.data)} deals in your pipeline."
            }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve deals: {str(e)}",
            "suggestion": "Please verify your data pipeline and try again."
        })
    
    return return_json