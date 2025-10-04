# workflow_agents/tools/connector_tools.py
"""
Tools for managing workflow connectors and integrations.
"""

import logging
from typing import Optional
from langchain_core.tools import tool

from workflow_agents.constants import AVAILABLE_CONNECTORS, CONNECTOR_CATEGORIES

logger = logging.getLogger(__name__)


@tool
def list_all_connectors(category: Optional[str] = None) -> dict:
    """
    List all available workflow connectors.
    
    Args:
        category: Optional category filter (email, calendar, storage, etc.)
        
    Returns:
        List of available connectors with their capabilities
    """
    try:
        if category:
            # Filter by category
            if category not in CONNECTOR_CATEGORIES:
                return {
                    "success": False,
                    "error": f"Invalid category: {category}",
                    "available_categories": list(CONNECTOR_CATEGORIES.keys())
                }
            
            connector_ids = CONNECTOR_CATEGORIES[category]["connectors"]
            connectors = {
                conn_id: AVAILABLE_CONNECTORS[conn_id] 
                for conn_id in connector_ids 
                if conn_id in AVAILABLE_CONNECTORS
            }
        else:
            connectors = AVAILABLE_CONNECTORS
        
        return {
            "success": True,
            "connectors": connectors,
            "count": len(connectors),
            "categories": CONNECTOR_CATEGORIES
        }
        
    except Exception as e:
        logger.error(f"Error listing connectors: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_connector_details(connector_id: str) -> dict:
    """
    Get detailed information about a specific connector.
    
    Args:
        connector_id: Connector identifier (e.g., 'gmail', 'slack')
        
    Returns:
        Connector details including triggers, actions, and OAuth requirements
    """
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found",
                "available_connectors": list(AVAILABLE_CONNECTORS.keys())
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        
        return {
            "success": True,
            "connector": connector,
            "connector_id": connector_id
        }
        
    except Exception as e:
        logger.error(f"Error getting connector details: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_connector_triggers(connector_id: str) -> dict:
    """
    Get available triggers for a connector.
    
    Args:
        connector_id: Connector identifier
        
    Returns:
        List of available triggers
    """
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found"
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        triggers = connector.get("triggers", [])
        
        return {
            "success": True,
            "connector_id": connector_id,
            "connector_name": connector["name"],
            "triggers": triggers,
            "count": len(triggers)
        }
        
    except Exception as e:
        logger.error(f"Error getting connector triggers: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_connector_actions(connector_id: str) -> dict:
    """
    Get available actions for a connector.
    
    Args:
        connector_id: Connector identifier
        
    Returns:
        List of available actions
    """
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found"
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        actions = connector.get("actions", [])
        
        return {
            "success": True,
            "connector_id": connector_id,
            "connector_name": connector["name"],
            "actions": actions,
            "count": len(actions)
        }
        
    except Exception as e:
        logger.error(f"Error getting connector actions: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def search_connectors(query: str) -> dict:
    """
    Search for connectors by name or capability.
    
    Args:
        query: Search query (e.g., "email", "calendar", "salesforce")
        
    Returns:
        Matching connectors
    """
    try:
        query_lower = query.lower()
        matching_connectors = {}
        
        for conn_id, conn_data in AVAILABLE_CONNECTORS.items():
            # Search in name, category, triggers, and actions
            searchable_text = " ".join([
                conn_data["name"].lower(),
                conn_data["category"].lower(),
                " ".join(conn_data.get("triggers", [])),
                " ".join(conn_data.get("actions", []))
            ])
            
            if query_lower in searchable_text or query_lower in conn_id:
                matching_connectors[conn_id] = conn_data
        
        return {
            "success": True,
            "query": query,
            "connectors": matching_connectors,
            "count": len(matching_connectors)
        }
        
    except Exception as e:
        logger.error(f"Error searching connectors: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_connectors_by_category(category: str) -> dict:
    """
    Get all connectors in a specific category.
    
    Args:
        category: Category name (email, calendar, storage, etc.)
        
    Returns:
        Connectors in the category
    """
    try:
        if category not in CONNECTOR_CATEGORIES:
            return {
                "success": False,
                "error": f"Invalid category: {category}",
                "available_categories": list(CONNECTOR_CATEGORIES.keys())
            }
        
        category_data = CONNECTOR_CATEGORIES[category]
        connector_ids = category_data["connectors"]
        
        connectors = {
            conn_id: AVAILABLE_CONNECTORS[conn_id]
            for conn_id in connector_ids
            if conn_id in AVAILABLE_CONNECTORS
        }
        
        return {
            "success": True,
            "category": category,
            "category_label": category_data["label"],
            "connectors": connectors,
            "count": len(connectors)
        }
        
    except Exception as e:
        logger.error(f"Error getting connectors by category: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def check_connector_compatibility(
    trigger_connector: str,
    action_connector: str
) -> dict:
    """
    Check if two connectors can work together in a workflow.
    
    Args:
        trigger_connector: Trigger connector ID
        action_connector: Action connector ID
        
    Returns:
        Compatibility information
    """
    try:
        if trigger_connector not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Trigger connector '{trigger_connector}' not found"
            }
        
        if action_connector not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Action connector '{action_connector}' not found"
            }
        
        trigger_data = AVAILABLE_CONNECTORS[trigger_connector]
        action_data = AVAILABLE_CONNECTORS[action_connector]
        
        # Check if trigger has triggers and action has actions
        has_triggers = len(trigger_data.get("triggers", [])) > 0
        has_actions = len(action_data.get("actions", [])) > 0
        
        compatible = has_triggers and has_actions
        
        return {
            "success": True,
            "compatible": compatible,
            "trigger_connector": {
                "id": trigger_connector,
                "name": trigger_data["name"],
                "available_triggers": trigger_data.get("triggers", [])
            },
            "action_connector": {
                "id": action_connector,
                "name": action_data["name"],
                "available_actions": action_data.get("actions", [])
            },
            "note": "All connectors are compatible for workflows" if compatible else "This combination may not work as expected"
        }
        
    except Exception as e:
        logger.error(f"Error checking connector compatibility: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_connector_oauth_requirements(connector_id: str) -> dict:
    """
    Get OAuth requirements for a connector.
    
    Args:
        connector_id: Connector identifier
        
    Returns:
        OAuth scopes and requirements
    """
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found"
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        
        oauth_required = len(connector.get("oauth_scopes", [])) > 0
        api_key_required = connector.get("api_key_required", False)
        
        return {
            "success": True,
            "connector_id": connector_id,
            "connector_name": connector["name"],
            "oauth_required": oauth_required,
            "oauth_scopes": connector.get("oauth_scopes", []),
            "api_key_required": api_key_required,
            "provider": connector.get("provider")
        }
        
    except Exception as e:
        logger.error(f"Error getting OAuth requirements: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }