# workflow_agents/tools/logs_tools.py
"""
Tools for fetching and analyzing workflow execution logs.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from langchain_core.tools import tool

from workflow_agents.config import config
from workflow_agents.utils.helpers import format_run_summary, format_duration

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(config.supabase_url, config.supabase_key)


@tool
def get_workflow_runs(
    flow_id: str,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 20
) -> dict:
    """
    Get execution runs for a workflow.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        status: Optional filter by status (success, error, running, etc.)
        limit: Maximum number of results
        
    Returns:
        List of workflow runs
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
        
        query = supabase.table("workflow_runs").select("*").eq("flow_id", flow_id).limit(limit)
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("started_at", desc=True).execute()
        
        runs = result.data if result.data else []
        
        # Add computed fields
        for run in runs:
            if run.get("started_at") and run.get("completed_at"):
                started = datetime.fromisoformat(run["started_at"].replace('Z', '+00:00'))
                completed = datetime.fromisoformat(run["completed_at"].replace('Z', '+00:00'))
                duration_seconds = (completed - started).total_seconds()
                run["duration"] = format_duration(duration_seconds)
                run["duration_seconds"] = duration_seconds
        
        return {
            "success": True,
            "runs": runs,
            "count": len(runs)
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow runs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_run_details(run_id: str, flow_id: str, user_id: str) -> dict:
    """
    Get detailed information about a specific run.
    
    Args:
        run_id: Run UUID
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        Detailed run information with logs
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
        
        # Get run
        run_result = supabase.table("workflow_runs").select("*").eq("id", run_id).eq("flow_id", flow_id).execute()
        
        if not run_result.data:
            return {
                "success": False,
                "error": "Run not found"
            }
        
        run = run_result.data[0]
        
        # Format summary
        summary = format_run_summary(run)
        
        return {
            "success": True,
            "run": run,
            "summary": summary,
            "logs": run.get("logs", []),
            "step_results": run.get("step_results", {})
        }
        
    except Exception as e:
        logger.error(f"Error getting run details: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_run_logs(run_id: str, flow_id: str, user_id: str) -> dict:
    """
    Get execution logs for a specific run.
    
    Args:
        run_id: Run UUID
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        Execution logs
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
        
        # Get run logs
        run_result = supabase.table("workflow_runs").select("logs, step_results").eq("id", run_id).eq("flow_id", flow_id).execute()
        
        if not run_result.data:
            return {
                "success": False,
                "error": "Run not found"
            }
        
        run = run_result.data[0]
        logs = run.get("logs", [])
        step_results = run.get("step_results", {})
        
        return {
            "success": True,
            "run_id": run_id,
            "logs": logs,
            "step_results": step_results,
            "log_count": len(logs)
        }
        
    except Exception as e:
        logger.error(f"Error getting run logs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_recent_errors(flow_id: str, user_id: str, hours: int = 24, limit: int = 10) -> dict:
    """
    Get recent error runs for a workflow.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        hours: Look back this many hours
        limit: Maximum number of results
        
    Returns:
        Recent error runs
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
        
        # Calculate cutoff time
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Get error runs
        result = supabase.table("workflow_runs").select("*").eq("flow_id", flow_id).eq("status", "error").gte("started_at", cutoff.isoformat()).limit(limit).order("started_at", desc=True).execute()
        
        errors = result.data if result.data else []
        
        # Extract error patterns
        error_types = {}
        for error_run in errors:
            error_msg = error_run.get("error_message", "Unknown error")
            # Extract first line as error type
            error_type = error_msg.split("\n")[0][:100]
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        return {
            "success": True,
            "errors": errors,
            "count": len(errors),
            "error_patterns": error_types,
            "time_window_hours": hours
        }
        
    except Exception as e:
        logger.error(f"Error getting recent errors: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_workflow_statistics(flow_id: str, user_id: str, days: int = 7) -> dict:
    """
    Get execution statistics for a workflow.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        days: Statistics for last N days
        
    Returns:
        Workflow execution statistics
    """
    supabase = get_supabase_client()
    
    try:
        # Verify ownership
        flow_check = supabase.table("workflow_flows").select("id, name").eq("id", flow_id).eq("owner", user_id).execute()
        if not flow_check.data:
            return {
                "success": False,
                "error": "Workflow not found or access denied"
            }
        
        flow = flow_check.data[0]
        
        # Calculate cutoff time
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get runs in time window
        result = supabase.table("workflow_runs").select("*").eq("flow_id", flow_id).gte("started_at", cutoff.isoformat()).execute()
        
        runs = result.data if result.data else []
        
        # Calculate statistics
        total_runs = len(runs)
        success_count = len([r for r in runs if r.get("status") == "success"])
        error_count = len([r for r in runs if r.get("status") == "error"])
        timeout_count = len([r for r in runs if r.get("status") == "timeout"])
        running_count = len([r for r in runs if r.get("status") == "running"])
        
        # Calculate average duration for completed runs
        completed_runs = [r for r in runs if r.get("started_at") and r.get("completed_at")]
        if completed_runs:
            durations = []
            for run in completed_runs:
                started = datetime.fromisoformat(run["started_at"].replace('Z', '+00:00'))
                completed = datetime.fromisoformat(run["completed_at"].replace('Z', '+00:00'))
                durations.append((completed - started).total_seconds())
            
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = 0
            max_duration = 0
            min_duration = 0
        
        # Success rate
        success_rate = (success_count / total_runs * 100) if total_runs > 0 else 0
        
        # Runs per day
        runs_per_day = total_runs / days if days > 0 else 0
        
        return {
            "success": True,
            "workflow_id": flow_id,
            "workflow_name": flow.get("name"),
            "time_window_days": days,
            "statistics": {
                "total_runs": total_runs,
                "success_count": success_count,
                "error_count": error_count,
                "timeout_count": timeout_count,
                "running_count": running_count,
                "success_rate_percent": round(success_rate, 2),
                "avg_duration_seconds": round(avg_duration, 2),
                "avg_duration": format_duration(avg_duration),
                "max_duration": format_duration(max_duration),
                "min_duration": format_duration(min_duration),
                "runs_per_day": round(runs_per_day, 2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def search_logs(
    flow_id: str,
    user_id: str,
    query: str,
    limit: int = 50
) -> dict:
    """
    Search through workflow execution logs.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        query: Search query
        limit: Maximum results
        
    Returns:
        Matching log entries
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
        
        # Get recent runs
        runs_result = supabase.table("workflow_runs").select("*").eq("flow_id", flow_id).limit(limit).order("started_at", desc=True).execute()
        
        runs = runs_result.data if runs_result.data else []
        
        # Search through logs
        matching_entries = []
        query_lower = query.lower()
        
        for run in runs:
            logs = run.get("logs", [])
            for log_entry in logs:
                # Search in log message and step details
                searchable_text = str(log_entry).lower()
                if query_lower in searchable_text:
                    matching_entries.append({
                        "run_id": run["id"],
                        "run_status": run.get("status"),
                        "started_at": run.get("started_at"),
                        "log_entry": log_entry
                    })
        
        return {
            "success": True,
            "query": query,
            "matches": matching_entries,
            "count": len(matching_entries)
        }
        
    except Exception as e:
        logger.error(f"Error searching logs: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }