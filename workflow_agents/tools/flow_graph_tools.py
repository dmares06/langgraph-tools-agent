# workflow_agents/tools/flow_graph_tools.py
"""
Tools for creating, reading, updating, and deleting workflow flows, nodes, and edges.
"""

import logging
from typing import Any, Optional
from datetime import datetime
from supabase import create_client, Client
from langchain_core.tools import tool

from workflow_agents.config import config
from workflow_agents.utils.helpers import WorkflowLogger, sanitize_node_config

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(config.supabase_url, config.supabase_key)


@tool
def create_workflow_flow(
    name: str,
    description: str,
    workflow_type: str,
    user_id: str,
    org_id: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Create a new workflow flow (automation or pipeline).
    
    Args:
        name: Workflow name
        description: Workflow description
        workflow_type: Type of workflow ('automation' or 'pipeline')
        user_id: User UUID who owns this workflow
        org_id: Optional organization UUID
        metadata: Optional metadata dictionary
        
    Returns:
        Created flow data with ID
    """
    supabase = get_supabase_client()
    
    flow_data = {
        "name": name,
        "description": description,
        "type": workflow_type,
        "owner": user_id,
        "org_id": org_id,
        "status": "draft",
        "metadata": metadata or {}
    }
    
    try:
        result = supabase.table("workflow_flows").insert(flow_data).execute()
        
        if result.data:
            flow = result.data[0]
            wf_logger = WorkflowLogger(flow["id"], user_id)
            wf_logger.info(f"Created workflow flow: {name}")
            
            return {
                "success": True,
                "flow_id": flow["id"],
                "flow": flow
            }
        else:
            return {
                "success": False,
                "error": "Failed to create workflow flow"
            }
            
    except Exception as e:
        logger.error(f"Error creating workflow flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_workflow_flow(flow_id: str, user_id: str) -> dict:
    """
    Get a workflow flow by ID with all its nodes and edges.
    
    Args:
        flow_id: Flow UUID
        user_id: User UUID (for auth check)
        
    Returns:
        Complete flow data including nodes and edges
    """
    supabase = get_supabase_client()
    
    try:
        # Get flow (RLS will check ownership)
        flow_result = supabase.table("workflow_flows").select("*").eq("id", flow_id).eq("owner", user_id).execute()
        
        if not flow_result.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        flow = flow_result.data[0]
        
        # Get nodes
        nodes_result = supabase.table("workflow_nodes").select("*").eq("flow_id", flow_id).execute()
        nodes = nodes_result.data if nodes_result.data else []
        
        # Get edges
        edges_result = supabase.table("workflow_edges").select("*").eq("flow_id", flow_id).execute()
        edges = edges_result.data if edges_result.data else []
        
        return {
            "success": True,
            "flow": flow,
            "nodes": nodes,
            "edges": edges
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def update_workflow_flow(
    flow_id: str,
    user_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Update a workflow flow.
    
    Args:
        flow_id: Flow UUID
        user_id: User UUID (for auth check)
        name: Optional new name
        description: Optional new description
        status: Optional new status
        metadata: Optional metadata updates
        
    Returns:
        Updated flow data
    """
    supabase = get_supabase_client()
    
    update_data = {}
    if name:
        update_data["name"] = name
    if description:
        update_data["description"] = description
    if status:
        update_data["status"] = status
        if status == "active":
            update_data["activated_at"] = datetime.utcnow().isoformat()
    if metadata:
        update_data["metadata"] = metadata
    
    try:
        result = supabase.table("workflow_flows").update(update_data).eq("id", flow_id).eq("owner", user_id).execute()
        
        if result.data:
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Updated workflow flow: {update_data}")
            
            return {
                "success": True,
                "flow": result.data[0]
            }
        else:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
            
    except Exception as e:
        logger.error(f"Error updating workflow flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def delete_workflow_flow(flow_id: str, user_id: str) -> dict:
    """
    Delete a workflow flow (archives it).
    
    Args:
        flow_id: Flow UUID
        user_id: User UUID (for auth check)
        
    Returns:
        Success status
    """
    supabase = get_supabase_client()
    
    try:
        # Archive instead of delete
        result = supabase.table("workflow_flows").update({"status": "archived"}).eq("id", flow_id).eq("owner", user_id).execute()
        
        if result.data:
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info("Archived workflow flow")
            
            return {
                "success": True,
                "message": "Workflow archived successfully"
            }
        else:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
            
    except Exception as e:
        logger.error(f"Error deleting workflow flow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def create_workflow_node(
    flow_id: str,
    node_type: str,
    config: dict,
    user_id: str,
    label: Optional[str] = None,
    position: Optional[dict] = None
) -> dict:
    """
    Create a workflow node.
    
    Args:
        flow_id: Parent flow UUID
        node_type: Type of node (e.g., 'gmail_trigger', 'calendar_action')
        config: Node configuration dictionary
        user_id: User UUID (for logging)
        label: Optional node label
        position: Optional position on canvas {"x": 100, "y": 200}
        
    Returns:
        Created node data
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership first
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    node_data = {
        "flow_id": flow_id,
        "node_type": node_type,
        "label": label or node_type.replace("_", " ").title(),
        "config": config,
        "position": position or {"x": 0, "y": 0}
    }
    
    try:
        result = supabase.table("workflow_nodes").insert(node_data).execute()
        
        if result.data:
            node = result.data[0]
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Created node: {node_type} - {node['id']}")
            
            return {
                "success": True,
                "node_id": node["id"],
                "node": node
            }
        else:
            return {
                "success": False,
                "error": "Failed to create node"
            }
            
    except Exception as e:
        logger.error(f"Error creating workflow node: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def update_workflow_node(
    node_id: str,
    flow_id: str,
    user_id: str,
    label: Optional[str] = None,
    config: Optional[dict] = None,
    position: Optional[dict] = None
) -> dict:
    """
    Update a workflow node.
    
    Args:
        node_id: Node UUID
        flow_id: Parent flow UUID
        user_id: User UUID (for auth check)
        label: Optional new label
        config: Optional new configuration
        position: Optional new position
        
    Returns:
        Updated node data
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    update_data = {}
    if label:
        update_data["label"] = label
    if config:
        update_data["config"] = config
    if position:
        update_data["position"] = position
    
    try:
        result = supabase.table("workflow_nodes").update(update_data).eq("id", node_id).eq("flow_id", flow_id).execute()
        
        if result.data:
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Updated node: {node_id}")
            
            return {
                "success": True,
                "node": result.data[0]
            }
        else:
            return {
                "success": False,
                "error": "Node not found"
            }
            
    except Exception as e:
        logger.error(f"Error updating workflow node: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def delete_workflow_node(
    node_id: str,
    flow_id: str,
    user_id: str
) -> dict:
    """
    Delete a workflow node.
    
    Args:
        node_id: Node UUID
        flow_id: Parent flow UUID
        user_id: User UUID (for auth check)
        
    Returns:
        Success status
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    try:
        result = supabase.table("workflow_nodes").delete().eq("id", node_id).eq("flow_id", flow_id).execute()
        
        wf_logger = WorkflowLogger(flow_id, user_id)
        wf_logger.info(f"Deleted node: {node_id}")
        
        return {
            "success": True,
            "message": "Node deleted successfully"
        }
            
    except Exception as e:
        logger.error(f"Error deleting workflow node: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def create_workflow_edge(
    flow_id: str,
    from_node: str,
    to_node: str,
    user_id: str,
    condition: Optional[dict] = None,
    label: Optional[str] = None
) -> dict:
    """
    Create a workflow edge (connection between nodes).
    
    Args:
        flow_id: Parent flow UUID
        from_node: Source node UUID
        to_node: Target node UUID
        user_id: User UUID (for auth check)
        condition: Optional condition for edge traversal
        label: Optional edge label
        
    Returns:
        Created edge data
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    edge_data = {
        "flow_id": flow_id,
        "from_node": from_node,
        "to_node": to_node,
        "condition": condition,
        "label": label
    }
    
    try:
        result = supabase.table("workflow_edges").insert(edge_data).execute()
        
        if result.data:
            edge = result.data[0]
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Created edge: {from_node} -> {to_node}")
            
            return {
                "success": True,
                "edge_id": edge["id"],
                "edge": edge
            }
        else:
            return {
                "success": False,
                "error": "Failed to create edge"
            }
            
    except Exception as e:
        logger.error(f"Error creating workflow edge: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def delete_workflow_edge(
    edge_id: str,
    flow_id: str,
    user_id: str
) -> dict:
    """
    Delete a workflow edge.
    
    Args:
        edge_id: Edge UUID
        flow_id: Parent flow UUID
        user_id: User UUID (for auth check)
        
    Returns:
        Success status
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    try:
        result = supabase.table("workflow_edges").delete().eq("id", edge_id).eq("flow_id", flow_id).execute()
        
        wf_logger = WorkflowLogger(flow_id, user_id)
        wf_logger.info(f"Deleted edge: {edge_id}")
        
        return {
            "success": True,
            "message": "Edge deleted successfully"
        }
            
    except Exception as e:
        logger.error(f"Error deleting workflow edge: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def list_user_workflows(
    user_id: str,
    workflow_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
) -> dict:
    """
    List all workflows for a user.
    
    Args:
        user_id: User UUID
        workflow_type: Optional filter by type ('automation' or 'pipeline')
        status: Optional filter by status
        limit: Maximum number of results
        
    Returns:
        List of workflows
    """
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("workflow_flows").select("*").eq("owner", user_id).limit(limit)
        
        if workflow_type:
            query = query.eq("type", workflow_type)
        if status:
            query = query.eq("status", status)
        
        result = query.order("updated_at", desc=True).execute()
        
        return {
            "success": True,
            "workflows": result.data if result.data else [],
            "count": len(result.data) if result.data else 0
        }
            
    except Exception as e:
        logger.error(f"Error listing workflows: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def bulk_create_nodes(
    flow_id: str,
    user_id: str,
    nodes: list[dict]
) -> dict:
    """
    Create multiple nodes at once.
    
    Args:
        flow_id: Parent flow UUID
        user_id: User UUID (for auth check)
        nodes: List of node dictionaries with node_type, config, label, position
        
    Returns:
        Created nodes data
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    # Prepare nodes data
    nodes_data = []
    for node in nodes:
        nodes_data.append({
            "flow_id": flow_id,
            "node_type": node.get("node_type"),
            "label": node.get("label", node.get("node_type", "").replace("_", " ").title()),
            "config": node.get("config", {}),
            "position": node.get("position", {"x": 0, "y": 0})
        })
    
    try:
        result = supabase.table("workflow_nodes").insert(nodes_data).execute()
        
        if result.data:
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Bulk created {len(result.data)} nodes")
            
            return {
                "success": True,
                "nodes": result.data,
                "count": len(result.data)
            }
        else:
            return {
                "success": False,
                "error": "Failed to create nodes"
            }
            
    except Exception as e:
        logger.error(f"Error bulk creating nodes: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def bulk_create_edges(
    flow_id: str,
    user_id: str,
    edges: list[dict]
) -> dict:
    """
    Create multiple edges at once.
    
    Args:
        flow_id: Parent flow UUID
        user_id: User UUID (for auth check)
        edges: List of edge dictionaries with from_node, to_node, condition, label
        
    Returns:
        Created edges data
    """
    supabase = get_supabase_client()
    
    # Verify flow ownership
    flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
    if not flow_check.data:
        return {
            "success": False,
            "error": "Flow not found or access denied"
        }
    
    # Prepare edges data
    edges_data = []
    for edge in edges:
        edges_data.append({
            "flow_id": flow_id,
            "from_node": edge.get("from_node"),
            "to_node": edge.get("to_node"),
            "condition": edge.get("condition"),
            "label": edge.get("label")
        })
    
    try:
        result = supabase.table("workflow_edges").insert(edges_data).execute()
        
        if result.data:
            wf_logger = WorkflowLogger(flow_id, user_id)
            wf_logger.info(f"Bulk created {len(result.data)} edges")
            
            return {
                "success": True,
                "edges": result.data,
                "count": len(result.data)
            }
        else:
            return {
                "success": False,
                "error": "Failed to create edges"
            }
            
    except Exception as e:
        logger.error(f"Error bulk creating edges: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }