# workflow_agents/agents/validator.py
"""
Workflow Validator Agent - Validates workflows before activation.
"""

import logging
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from workflow_agents.config import config
from workflow_agents.constants import WORKFLOW_VALIDATOR_PROMPT
from workflow_agents.state import WorkflowValidatorState
from workflow_agents.tools import (
    get_workflow_flow,
    validate_workflow,
    dry_run_workflow,
    get_validation_issues,
    resolve_validation_issue,
    check_credentials_for_workflow,
    list_user_credentials
)

logger = logging.getLogger(__name__)


def create_validator_agent():
    """
    Create the Workflow Validator Agent.
    
    This agent specializes in:
    - Checking workflow configuration completeness
    - Validating credentials and OAuth connections
    - Testing API connectivity
    - Identifying configuration errors
    - Suggesting fixes for issues
    
    Returns:
        Compiled LangGraph agent
    """
    
    # Initialize LLM
    model = init_chat_model(
        config.model_name,
        temperature=0.2,  # Lower temperature for validation (more deterministic)
        max_tokens=config.max_tokens
    )
    
    # Validator-specific tools
    validator_tools = [
        get_workflow_flow,
        validate_workflow,
        dry_run_workflow,
        get_validation_issues,
        resolve_validation_issue,
        check_credentials_for_workflow,
        list_user_credentials
    ]
    
    # Create agent
    agent = create_react_agent(
        model=model,
        tools=validator_tools,
        state_schema=WorkflowValidatorState,
        prompt=WORKFLOW_VALIDATOR_PROMPT
    )
    
    logger.info("Workflow Validator Agent created")
    
    return agent


# Pre-compiled agent instance
validator_agent = create_validator_agent()


async def invoke_validator_agent(state: dict, config: dict) -> dict:
    """
    Invoke the Validator Agent with state and config.
    
    Args:
        state: Current workflow state
        config: Runtime configuration
        
    Returns:
        Updated state with validation results
    """
    try:
        result = await validator_agent.ainvoke(state, config)
        return result
    except Exception as e:
        logger.error(f"Error invoking Validator Agent: {str(e)}")
        return {
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"I encountered an error while validating the workflow: {str(e)}"
            }]
        }


def format_validation_results(validation_data: dict) -> str:
    """
    Format validation results into human-readable message.
    
    Args:
        validation_data: Validation results from validate_workflow tool
        
    Returns:
        Formatted message
    """
    if not validation_data.get("success"):
        return f"❌ Validation failed: {validation_data.get('error')}"
    
    can_activate = validation_data.get("can_activate", False)
    issues = validation_data.get("issues", [])
    summary = validation_data.get("summary", {})
    
    if can_activate:
        message = "✅ **Workflow is ready to activate!**\n\n"
        message += "All validation checks passed. You can safely activate this workflow.\n"
        
        # Show warnings if any
        warnings = [i for i in issues if i["severity"] == "warning"]
        if warnings:
            message += f"\n⚠️ **{len(warnings)} Warning(s):**\n"
            for warning in warnings:
                message += f"- {warning['message']}\n"
    else:
        message = "❌ **Workflow needs fixes before activation**\n\n"
        
        # Show errors
        errors = [i for i in issues if i["severity"] == "error"]
        if errors:
            message += f"**{len(errors)} Error(s) found:**\n"
            for idx, error in enumerate(errors, 1):
                message += f"{idx}. {error['message']}\n"
                if error.get("suggested_fix"):
                    message += f"   💡 *Fix:* {error['suggested_fix']}\n"
                if error.get("oauth_url"):
                    message += f"   🔗 [Connect Account]({error['oauth_url']})\n"
                message += "\n"
        
        # Show warnings
        warnings = [i for i in issues if i["severity"] == "warning"]
        if warnings:
            message += f"\n⚠️ **{len(warnings)} Warning(s):**\n"
            for warning in warnings:
                message += f"- {warning['message']}\n"
    
    # Add summary
    message += f"\n📊 **Summary:**\n"
    message += f"- Total nodes: {summary.get('nodes_count', 0)}\n"
    message += f"- Total connections: {summary.get('edges_count', 0)}\n"
    message += f"- Issues: {summary.get('errors', 0)} errors, {summary.get('warnings', 0)} warnings\n"
    
    return message


def prioritize_issues(issues: list[dict]) -> list[dict]:
    """
    Sort validation issues by priority.
    
    Args:
        issues: List of validation issues
        
    Returns:
        Sorted issues (highest priority first)
    """
    priority_order = {
        "error": 0,
        "warning": 1,
        "info": 2
    }
    
    return sorted(issues, key=lambda x: priority_order.get(x.get("severity", "info"), 3))


def group_issues_by_type(issues: list[dict]) -> dict[str, list[dict]]:
    """
    Group validation issues by type for better presentation.
    
    Args:
        issues: List of validation issues
        
    Returns:
        Dictionary mapping issue types to lists of issues
    """
    grouped = {}
    
    for issue in issues:
        issue_type = issue.get("field", "general")
        if issue_type not in grouped:
            grouped[issue_type] = []
        grouped[issue_type].append(issue)
    
    return grouped