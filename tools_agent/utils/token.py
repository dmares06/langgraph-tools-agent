"""API key and token management utilities."""

import os
from typing import Dict, Optional

def fetch_tokens(config: Dict) -> Dict[str, str]:
    """
    Fetch API tokens from config or environment variables.
    
    Args:
        config: Configuration dictionary that may contain apiKeys
    
    Returns:
        Dictionary of provider: api_key mappings
    """
    api_keys = config.get("configurable", {}).get("apiKeys", {})
    
    tokens = {
        "openai": api_keys.get("openai") or os.getenv("OPENAI_API_KEY"),
        "anthropic": api_keys.get("anthropic") or os.getenv("ANTHROPIC_API_KEY"),
        "google": api_keys.get("google") or os.getenv("GOOGLE_API_KEY"),
        "tavily": os.getenv("TAVILY_API_KEY"),
        "firecrawl": os.getenv("FIRECRAWL_API_KEY"),
        "serp": os.getenv("SERPAPI_API_KEY"),
    }
    
    # Remove None values
    return {k: v for k, v in tokens.items() if v is not None}

def get_model_api_key(model_name: str, tokens: Dict[str, str]) -> Optional[str]:
    """
    Get the appropriate API key for a given model.
    
    Args:
        model_name: Name of the model (e.g., "openai:gpt-4", "anthropic:claude-3")
        tokens: Dictionary of available API tokens
    
    Returns:
        API key string or None if not found
    """
    model_lower = model_name.lower()
    
    if "anthropic" in model_lower or "claude" in model_lower:
        return tokens.get("anthropic")
    elif "openai" in model_lower or "gpt" in model_lower:
        return tokens.get("openai")
    elif "google" in model_lower or "gemini" in model_lower:
        return tokens.get("google")
    
    return None

# =============================================================================
# USAGE EXAMPLES
# =============================================================================

"""
# Example 1: Import and use specific tool categories
from suitecrm_tools import CORE_CRM_TOOLS, OM_BOV_TOOLS
agent_tools = CORE_CRM_TOOLS + OM_BOV_TOOLS

# Example 2: Import by category dynamically
from suitecrm_tools import get_tools_by_category
crm_tools = get_tools_by_category('core_crm')
doc_tools = get_tools_by_category('documents')

# Example 3: Import all tools (backward compatible)
from suitecrm_tools import CRM_TOOLS
agent_tools = CRM_TOOLS

# Example 4: Import specific tools directly
from suitecrm_tools.core_crm import get_contacts, get_deals
from suitecrm_tools.om_bov import generate_om_content

# Example 5: Use agent with configuration
config = {
    "configurable": {
        "model_name": "openai:gpt-4o",
        "agent_mode": "chat_copilot",
        "user_id": "broker_123"
    }
}
"""
