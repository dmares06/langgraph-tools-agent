"""Broker profile management tools."""

import json
from langchain_core.tools import tool
from ..utils import get_supabase_client

@tool
def get_broker_profile() -> str:
    """ 
    Get the current broker's profile information including name and company details.
    This provides context about who the agent is helping.

    Returns:
        JSON string with broker profile information
    """
    try:
        supabase = get_supabase_client()
        profile_result = supabase.table("broker_settings").select("*").execute()

        if profile_result.data:
            profile = profile_result.data[0]
            return_json = json.dumps({
                "success": True,
                "broker_name": profile.get("agent_name", "Unknown"),
                "company_name": profile.get("company_name", "Unknown company"),
                "email": profile.get("email"),
                "phone": profile.get("phone_number"),
                "message": f"Profile found for {profile.get('agent_name', 'broker')}"
            }, default=str)
        else:
            return_json = json.dumps({
                "success": False,
                "message": "No profile information found. Please set up your broker profile in settings.",
                "suggestion": "Add your name and company information in your SuiteCRE profile settings."
            })
    except Exception as e:
        return_json = json.dumps({
            "success": False, 
            "error": f"Unable to retrieve broker profile: {str(e)}",
            "suggestion": "Please check your SuiteCRE profile settings and try again."
        })
    
    return return_json