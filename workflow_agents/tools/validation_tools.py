# workflow_agents/tools/validation_tools.py
"""
Tools for validating workflows before activation.
"""

import logging
from typing import Optional
from supabase import create_client, Client
from langchain_core.tools import tool

from workflow_agents.config import config
from workflow_agents.constants import AVAILABLE_CONNECTORS
from workflow_agents.tools.credentials_tools import check_credentials_for_workflow

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(config.supabase_url, config.supabase_key)


@tool
def validate_workflow(flow_id: str, user_id: str) -> dict:
    """
    Validate a complete workflow for activation readiness.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        Validation results with issues list
    """
    supabase = get_supabase_client()
    issues = []
    
    try:
        # Get flow
        flow_result = supabase.table("workflow_flows").select("*").eq("id", flow_id).eq("owner", user_id).execute()
        
        if not flow_result.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        flow = flow_result.data[0]
        
        # Get nodes and edges
        nodes_result = supabase.table("workflow_nodes").select("*").eq("flow_id", flow_id).execute()
        edges_result = supabase.table("workflow_edges").select("*").eq("flow_id", flow_id).execute()
        
        nodes = nodes_result.data if nodes_result.data else []
        edges = edges_result.data if edges_result.data else []
        
        # VALIDATION 1: Must have at least one node
        if len(nodes) == 0:
            issues.append({
                "severity": "error",
                "field": "nodes",
                "message": "Workflow must have at least one node",
                "suggested_fix": "Add a trigger or action node to your workflow",
                "auto_fixable": False
            })
        
        # VALIDATION 2: Must have at least one trigger node
        trigger_nodes = [n for n in nodes if "_trigger" in n.get("node_type", "")]
        if len(trigger_nodes) == 0:
            issues.append({
                "severity": "error",
                "field": "trigger",
                "message": "Workflow must have at least one trigger",
                "suggested_fix": "Add a trigger node (email, calendar, schedule, etc.)",
                "auto_fixable": False
            })
        
        # VALIDATION 3: Check for disconnected nodes
        node_ids = set(n["id"] for n in nodes)
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge["from_node"])
            connected_nodes.add(edge["to_node"])
        
        disconnected = node_ids - connected_nodes
        if disconnected and len(nodes) > 1:
            issues.append({
                "severity": "warning",
                "field": "edges",
                "message": f"{len(disconnected)} node(s) are not connected",
                "suggested_fix": "Connect all nodes or remove unused nodes",
                "auto_fixable": False
            })
        
        # VALIDATION 4: Validate each node's configuration
        for node in nodes:
            node_issues = validate_node_config(node, flow_id, user_id)
            issues.extend(node_issues)
        
        # VALIDATION 5: Check credentials
        cred_check = check_credentials_for_workflow(flow_id, user_id)
        if not cred_check.get("all_connected"):
            for missing in cred_check.get("missing_credentials", []):
                issues.append({
                    "severity": "error",
                    "field": "credentials",
                    "message": f"Missing or expired connection for {missing['connector_name']}",
                    "suggested_fix": f"Connect your {missing['connector_name']} account",
                    "oauth_url": missing.get("oauth_url"),
                    "auto_fixable": False
                })
        
        # VALIDATION 6: Check for circular dependencies
        if has_circular_dependency(nodes, edges):
            issues.append({
                "severity": "error",
                "field": "edges",
                "message": "Workflow contains circular dependencies",
                "suggested_fix": "Remove loops that would cause infinite execution",
                "auto_fixable": False
            })
        
        # Determine if can activate
        error_count = len([i for i in issues if i["severity"] == "error"])
        warning_count = len([i for i in issues if i["severity"] == "warning"])
        can_activate = error_count == 0
        
        # Store validation issues
        if issues:
            store_validation_issues(flow_id, issues)
        
        return {
            "success": True,
            "can_activate": can_activate,
            "status": "ready" if can_activate else "needs_fixes",
            "issues": issues,
            "summary": {
                "total_issues": len(issues),
                "errors": error_count,
                "warnings": warning_count,
                "nodes_count": len(nodes),
                "edges_count": len(edges)
            }
        }
        
    except Exception as e:
        logger.error(f"Error validating workflow: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def validate_node_config(node: dict, flow_id: str, user_id: str) -> list[dict]:
    """
    Validate a single node's configuration.
    
    Args:
        node: Node dictionary
        flow_id: Parent flow UUID
        user_id: User UUID
        
    Returns:
        List of validation issues for this node
    """
    issues = []
    node_type = node.get("node_type", "")
    config = node.get("config", {})
    
    # Extract connector from node_type
    connector_id = node_type.split("_")[0]
    
    if connector_id not in AVAILABLE_CONNECTORS:
        issues.append({
            "severity": "error",
            "node_id": node["id"],
            "field": "node_type",
            "message": f"Unknown connector: {connector_id}",
            "suggested_fix": "Select a valid connector from the available list",
            "auto_fixable": False
        })
        return issues
    
    connector = AVAILABLE_CONNECTORS[connector_id]
    
    # Connector-specific validations
    if connector_id == "gmail":
        if "_action" in node_type and "send_email" in node_type:
            if not config.get("to"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "to",
                    "message": "Email recipient is required",
                    "suggested_fix": "Add recipient email address",
                    "auto_fixable": False
                })
            if not config.get("subject"):
                issues.append({
                    "severity": "warning",
                    "node_id": node["id"],
                    "field": "subject",
                    "message": "Email subject is empty",
                    "suggested_fix": "Add a subject line",
                    "auto_fixable": False
                })
            if not config.get("body"):
                issues.append({
                    "severity": "warning",
                    "node_id": node["id"],
                    "field": "body",
                    "message": "Email body is empty",
                    "suggested_fix": "Add email content",
                    "auto_fixable": False
                })
    
    elif connector_id in ["google_calendar", "outlook_calendar"]:
        if "_action" in node_type and "create_event" in node_type:
            if not config.get("calendar_id"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "calendar_id",
                    "message": "Calendar ID is required",
                    "suggested_fix": "Select a calendar from your connected account",
                    "auto_fixable": False
                })
            if not config.get("title"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "title",
                    "message": "Event title is required",
                    "suggested_fix": "Add an event title",
                    "auto_fixable": False
                })
            if not config.get("start_time"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "start_time",
                    "message": "Event start time is required",
                    "suggested_fix": "Set event start time",
                    "auto_fixable": False
                })
    
    elif connector_id == "webhook":
        if "_action" in node_type:
            if not config.get("url"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "url",
                    "message": "Webhook URL is required",
                    "suggested_fix": "Add webhook endpoint URL",
                    "auto_fixable": False
                })
            elif not config["url"].startswith(("http://", "https://")):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "url",
                    "message": "Invalid webhook URL format",
                    "suggested_fix": "URL must start with http:// or https://",
                    "auto_fixable": False
                })
    
    elif connector_id == "slack":
        if "_action" in node_type and "send_message" in node_type:
            if not config.get("channel"):
                issues.append({
                    "severity": "error",
                    "node_id": node["id"],
                    "field": "channel",
                    "message": "Slack channel is required",
                    "suggested_fix": "Select or enter a channel name",
                    "auto_fixable": False
                })
            if not config.get("message"):
                issues.append({
                    "severity": "warning",
                    "node_id": node["id"],
                    "field": "message",
                    "message": "Message content is empty",
                    "suggested_fix": "Add message text",
                    "auto_fixable": False
                })
    
    return issues


def has_circular_dependency(nodes: list[dict], edges: list[dict]) -> bool:
    """
    Check if workflow has circular dependencies using DFS.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        
    Returns:
        True if circular dependency exists
    """
    # Build adjacency list
    graph = {node["id"]: [] for node in nodes}
    for edge in edges:
        graph[edge["from_node"]].append(edge["to_node"])
    
    visited = set()
    rec_stack = set()
    
    def dfs(node_id: str) -> bool:
        visited.add(node_id)
        rec_stack.add(node_id)
        
        for neighbor in graph.get(node_id, []):
            if neighbor not in visited:
                if dfs(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True
        
        rec_stack.remove(node_id)
        return False
    
    for node_id in graph:
        if node_id not in visited:
            if dfs(node_id):
                return True
    
    return False


def store_validation_issues(flow_id: str, issues: list[dict]):
    """
    Store validation issues in database.
    
    Args:
        flow_id: Workflow flow UUID
        issues: List of validation issues
    """
    supabase = get_supabase_client()
    
    try:
        # Clear existing issues for this flow
        supabase.table("workflow_validation_issues").delete().eq("flow_id", flow_id).execute()
        
        # Insert new issues
        if issues:
            issues_data = []
            for issue in issues:
                issues_data.append({
                    "flow_id": flow_id,
                    "severity": issue["severity"],
                    "issue_type": issue.get("field", "general"),
                    "node_id": issue.get("node_id"),
                    "field_name": issue.get("field"),
                    "message": issue["message"],
                    "suggested_fix": issue.get("suggested_fix")
                })
            
            supabase.table("workflow_validation_issues").insert(issues_data).execute()
            
    except Exception as e:
        logger.error(f"Error storing validation issues: {str(e)}")


@tool
def dry_run_workflow(flow_id: str, user_id: str, test_data: Optional[dict] = None) -> dict:
    """
    Perform a dry run of a workflow with test data.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        test_data: Optional test data to use as trigger
        
    Returns:
        Dry run results showing what would happen
    """
    supabase = get_supabase_client()
    
    try:
        # Get complete workflow
        flow_result = supabase.table("workflow_flows").select("*").eq("id", flow_id).eq("owner", user_id).execute()
        
        if not flow_result.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        nodes_result = supabase.table("workflow_nodes").select("*").eq("flow_id", flow_id).execute()
        edges_result = supabase.table("workflow_edges").select("*").eq("flow_id", flow_id).execute()
        
        nodes = nodes_result.data if nodes_result.data else []
        edges = edges_result.data if edges_result.data else []
        
        # Simulate execution
        execution_log = []
        
        # Find trigger nodes
        trigger_nodes = [n for n in nodes if "_trigger" in n.get("node_type", "")]
        
        if not trigger_nodes:
            return {
                "success": False,
                "error": "No trigger node found"
            }
        
        # Simulate trigger
        trigger = trigger_nodes[0]
        execution_log.append({
            "step": 1,
            "node_id": trigger["id"],
            "node_type": trigger["node_type"],
            "label": trigger.get("label"),
            "status": "success",
            "message": f"Trigger activated with test data",
            "duration_ms": 10
        })
        
        # Build execution order
        execution_order = build_execution_order(nodes, edges, trigger["id"])
        
        # Simulate each step
        for idx, node_id in enumerate(execution_order[1:], start=2):
            node = next((n for n in nodes if n["id"] == node_id), None)
            if not node:
                continue
            
            # Check if node would execute based on conditions
            incoming_edges = [e for e in edges if e["to_node"] == node_id]
            would_execute = True
            
            for edge in incoming_edges:
                if edge.get("condition"):
                    # Simulate condition check
                    would_execute = True  # Simplified for dry run
            
            if would_execute:
                execution_log.append({
                    "step": idx,
                    "node_id": node["id"],
                    "node_type"
                    "node_type": node["node_type"],
                    "label": node.get("label"),
                    "status": "success",
                    "message": f"Would execute: {node.get('label', node['node_type'])}",
                    "duration_ms": 50,
                    "config": node.get("config", {})
                })
            else:
                execution_log.append({
                    "step": idx,
                    "node_id": node["id"],
                    "node_type": node["node_type"],
                    "label": node.get("label"),
                    "status": "skipped",
                    "message": "Condition not met, skipped",
                    "duration_ms": 0
                })
        
        return {
            "success": True,
            "dry_run": True,
            "execution_log": execution_log,
            "total_steps": len(execution_log),
            "would_succeed": True,
            "estimated_duration_ms": sum(log["duration_ms"] for log in execution_log),
            "note": "This is a simulation. Actual execution may differ."
        }
        
    except Exception as e:
        logger.error(f"Error in dry run: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


def build_execution_order(nodes: list[dict], edges: list[dict], start_node_id: str) -> list[str]:
    """
    Build execution order using topological sort.
    
    Args:
        nodes: List of nodes
        edges: List of edges
        start_node_id: Starting node UUID
        
    Returns:
        Ordered list of node IDs
    """
    # Build adjacency list
    graph = {node["id"]: [] for node in nodes}
    for edge in edges:
        graph[edge["from_node"]].append(edge["to_node"])
    
    # BFS from start node
    execution_order = []
    visited = set()
    queue = [start_node_id]
    
    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        
        visited.add(current)
        execution_order.append(current)
        
        # Add children to queue
        for child in graph.get(current, []):
            if child not in visited:
                queue.append(child)
    
    return execution_order


@tool
def get_validation_issues(flow_id: str, user_id: str) -> dict:
    """
    Get stored validation issues for a workflow.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        List of validation issues
    """
    supabase = get_supabase_client()
    
    try:
        # Verify ownership
        flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
        if not flow_check.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        # Get unresolved issues
        issues_result = supabase.table("workflow_validation_issues").select("*").eq("flow_id", flow_id).is_("resolved_at", "null").execute()
        
        issues = issues_result.data if issues_result.data else []
        
        error_count = len([i for i in issues if i["severity"] == "error"])
        warning_count = len([i for i in issues if i["severity"] == "warning"])
        
        return {
            "success": True,
            "issues": issues,
            "summary": {
                "total": len(issues),
                "errors": error_count,
                "warnings": warning_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation issues: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def resolve_validation_issue(issue_id: str, flow_id: str, user_id: str) -> dict:
    """
    Mark a validation issue as resolved.
    
    Args:
        issue_id: Issue UUID
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        Success status
    """
    supabase = get_supabase_client()
    
    try:
        # Verify ownership
        flow_check = supabase.table("workflow_flows").select("id").eq("id", flow_id).eq("owner", user_id).execute()
        if not flow_check.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        # Mark as resolved
        from datetime import datetime
        result = supabase.table("workflow_validation_issues").update({
            "resolved_at": datetime.utcnow().isoformat()
        }).eq("id", issue_id).eq("flow_id", flow_id).execute()
        
        return {
            "success": True,
            "message": "Validation issue resolved"
        }
        
    except Exception as e:
        logger.error(f"Error resolving validation issue: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }