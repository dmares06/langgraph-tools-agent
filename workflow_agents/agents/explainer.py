# workflow_agents/agents/explainer.py
"""
Workflow Explainer Agent - Explains workflow execution and debugging.
"""

import logging
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from workflow_agents.config import config
from workflow_agents.constants import WORKFLOW_EXPLAINER_PROMPT
from workflow_agents.state import WorkflowExplainerState
from workflow_agents.tools import (
    get_workflow_flow,
    get_workflow_runs,
    get_run_details,
    get_run_logs,
    get_recent_errors,
    get_workflow_statistics,
    search_logs
)

logger = logging.getLogger(__name__)


def create_explainer_agent():
    """
    Create the Workflow Explainer Agent.
    
    This agent specializes in:
    - Explaining why workflows ran or didn't run
    - Analyzing execution logs
    - Identifying error patterns
    - Providing debugging insights
    - Making execution transparent
    
    Returns:
        Compiled LangGraph agent
    """
    
    # Initialize LLM
    model = init_chat_model(
        config.model_name,
        temperature=0.4,  # Moderate temperature for explanations
        max_tokens=config.max_tokens
    )
    
    # Explainer-specific tools
    explainer_tools = [
        get_workflow_flow,
        get_workflow_runs,
        get_run_details,
        get_run_logs,
        get_recent_errors,
        get_workflow_statistics,
        search_logs
    ]
    
    # Create agent
    agent = create_react_agent(
        model=model,
        tools=explainer_tools,
        state_schema=WorkflowExplainerState,
        prompt=WORKFLOW_EXPLAINER_PROMPT
    )
    
    logger.info("Workflow Explainer Agent created")
    
    return agent


# Pre-compiled agent instance
explainer_agent = create_explainer_agent()


async def invoke_explainer_agent(state: dict, config: dict) -> dict:
    """
    Invoke the Explainer Agent with state and config.
    
    Args:
        state: Current workflow state
        config: Runtime configuration
        
    Returns:
        Updated state with explanations
    """
    try:
        result = await explainer_agent.ainvoke(state, config)
        return result
    except Exception as e:
        logger.error(f"Error invoking Explainer Agent: {str(e)}")
        return {
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"I encountered an error while explaining the workflow: {str(e)}"
            }]
        }


def format_run_explanation(run_data: dict, logs: list[dict]) -> str:
    """
    Format workflow run into detailed explanation.
    
    Args:
        run_data: Run metadata
        logs: Execution logs
        
    Returns:
        Formatted explanation
    """
    status_emoji = {
        "success": "✅",
        "error": "❌",
        "running": "🔄",
        "timeout": "⏱️",
        "cancelled": "⛔"
    }
    
    status = run_data.get("status", "unknown")
    emoji = status_emoji.get(status, "❓")
    
    explanation = f"📊 **Run #{run_data.get('id', '')[:8]}... Explanation**\n\n"
    explanation += f"{emoji} **Status**: {status.title()}\n"
    explanation += f"🕐 **Started**: {run_data.get('started_at', 'Unknown')}\n"
    
    if run_data.get("duration"):
        explanation += f"⏱️ **Duration**: {run_data['duration']}\n"
    
    explanation += "\n🔄 **Execution Steps**:\n\n"
    
    # Explain each log entry
    for idx, log_entry in enumerate(logs, 1):
        step_status = log_entry.get("status", "unknown")
        step_emoji = status_emoji.get(step_status, "❓")
        
        step_name = log_entry.get("step_name", f"Step {idx}")
        explanation += f"{idx}. {step_emoji} **{step_name}**\n"
        
        if log_entry.get("message"):
            explanation += f"   {log_entry['message']}\n"
        
        if log_entry.get("duration_ms"):
            explanation += f"   ⏱️ {log_entry['duration_ms']}ms\n"
        
        explanation += "\n"
    
    # Add error details if present
    if run_data.get("error_message"):
        explanation += f"\n❌ **Error Details**:\n"
        explanation += f"```\n{run_data['error_message']}\n```\n"
        
        # Suggest fixes
        explanation += "\n💡 **Suggested Fixes**:\n"
        explanation += analyze_error_and_suggest_fix(run_data['error_message'])
    
    return explanation


def analyze_error_and_suggest_fix(error_message: str) -> str:
    """
    Analyze error message and suggest fixes.
    
    Args:
        error_message: Error message from run
        
    Returns:
        Suggested fixes
    """
    suggestions = []
    error_lower = error_message.lower()
    
    # Common error patterns
    if "authentication" in error_lower or "401" in error_lower:
        suggestions.append("- Your OAuth token may have expired. Reconnect your account.")
    
    if "permission" in error_lower or "403" in error_lower:
        suggestions.append("- You don't have permission for this action. Check OAuth scopes.")
    
    if "not found" in error_lower or "404" in error_lower:
        suggestions.append("- The resource (calendar, folder, etc.) may have been deleted. Update your workflow configuration.")
    
    if "rate limit" in error_lower or "429" in error_lower:
        suggestions.append("- You've hit the API rate limit. Add a delay between actions or reduce workflow frequency.")
    
    if "timeout" in error_lower:
        suggestions.append("- The action took too long. Increase timeout or optimize the workflow.")
    
    if "invalid" in error_lower:
        suggestions.append("- Check that all required fields are filled correctly.")
    
    if not suggestions:
        suggestions.append("- Check the workflow configuration and try running again.")
        suggestions.append("- Contact support if the issue persists.")
    
    return "\n".join(suggestions)


def identify_error_patterns(runs: list[dict]) -> dict:
    """
    Identify common error patterns across multiple runs.
    
    Args:
        runs: List of workflow runs
        
    Returns:
        Error pattern analysis
    """
    error_runs = [r for r in runs if r.get("status") == "error"]
    
    if not error_runs:
        return {
            "has_patterns": False,
            "message": "No errors found in recent runs"
        }
    
    # Group by error message
    error_groups = {}
    for run in error_runs:
        error_msg = run.get("error_message", "Unknown error")
        # Use first line as key
        error_key = error_msg.split("\n")[0][:100]
        
        if error_key not in error_groups:
            error_groups[error_key] = []
        error_groups[error_key].append(run)
    
    # Find most common
    most_common = max(error_groups.items(), key=lambda x: len(x[1]))
    
    return {
        "has_patterns": True,
        "most_common_error": most_common[0],
        "occurrence_count": len(most_common[1]),
        "total_errors": len(error_runs),
        "unique_errors": len(error_groups),
        "message": f"The error '{most_common[0]}' occurred {len(most_common[1])} times"
    }