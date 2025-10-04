# workflow_agents/agents/builder.py
"""
Workflow Builder Agent - Creates and edits workflow automations.
"""

import logging
from typing import Optional
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from workflow_agents.config import config
from workflow_agents.constants import WORKFLOW_BUILDER_PROMPT
from workflow_agents.state import WorkflowBuilderState
from workflow_agents.tools import (
    create_workflow_flow,
    get_workflow_flow,
    update_workflow_flow,
    create_workflow_node,
    update_workflow_node,
    delete_workflow_node,
    create_workflow_edge,
    delete_workflow_edge,
    bulk_create_nodes,
    bulk_create_edges,
    list_all_connectors,
    get_connector_details,
    get_connector_triggers,
    get_connector_actions,
    search_connectors,
    check_credential_exists,
    get_oauth_connection_url,
    check_credentials_for_workflow
)

logger = logging.getLogger(__name__)


def create_builder_agent():
    """
    Create the Workflow Builder Agent.
    
    This agent specializes in:
    - Parsing natural language workflow descriptions
    - Creating draft workflows with nodes and edges
    - Selecting appropriate connectors
    - Identifying missing OAuth connections
    - Proposing sensible default configurations
    
    Returns:
        Compiled LangGraph agent
    """
    
    # Initialize LLM
    model = init_chat_model(
        config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens
    )
    
    # Builder-specific tools
    builder_tools = [
        # Flow management
        create_workflow_flow,
        get_workflow_flow,
        update_workflow_flow,
        create_workflow_node,
        update_workflow_node,
        delete_workflow_node,
        create_workflow_edge,
        delete_workflow_edge,
        bulk_create_nodes,
        bulk_create_edges,
        
        # Connector discovery
        list_all_connectors,
        get_connector_details,
        get_connector_triggers,
        get_connector_actions,
        search_connectors,
        
        # Credentials checking
        check_credential_exists,
        get_oauth_connection_url,
        check_credentials_for_workflow
    ]
    
    # Create agent
    agent = create_react_agent(
        model=model,
        tools=builder_tools,
        state_schema=WorkflowBuilderState,
        prompt=WORKFLOW_BUILDER_PROMPT
    )
    
    logger.info("Workflow Builder Agent created")
    
    return agent


# Pre-compiled agent instance
builder_agent = create_builder_agent()


async def invoke_builder_agent(state: dict, config: dict) -> dict:
    """
    Invoke the Builder Agent with state and config.
    
    Args:
        state: Current workflow state
        config: Runtime configuration
        
    Returns:
        Updated state
    """
    try:
        result = await builder_agent.ainvoke(state, config)
        return result
    except Exception as e:
        logger.error(f"Error invoking Builder Agent: {str(e)}")
        return {
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"I encountered an error while building the workflow: {str(e)}"
            }]
        }


def parse_workflow_intent_from_message(message: str) -> dict:
    """
    Enhanced intent parsing specific to workflow building.
    
    Args:
        message: User's message
        
    Returns:
        Parsed intent with workflow-specific fields
    """
    from workflow_agents.utils.helpers import parse_workflow_intent
    
    base_intent = parse_workflow_intent(message)
    
    # Add workflow-specific enhancements
    message_lower = message.lower()
    
    # Detect workflow type
    if any(word in message_lower for word in ["automation", "automate", "when", "trigger"]):
        base_intent["workflow_type"] = "automation"
    elif any(word in message_lower for word in ["pipeline", "stage", "deal"]):
        base_intent["workflow_type"] = "pipeline"
    else:
        base_intent["workflow_type"] = "automation"  # Default
    
    # Detect multi-step workflows
    if " then " in message_lower or " and " in message_lower:
        base_intent["is_multi_step"] = True
    else:
        base_intent["is_multi_step"] = False
    
    # Detect conditions
    if any(word in message_lower for word in ["if", "when", "unless", "only if"]):
        base_intent["has_conditions"] = True
    else:
        base_intent["has_conditions"] = False
    
    return base_intent


def suggest_node_configuration(node_type: str, user_intent: dict) -> dict:
    """
    Suggest sensible default configuration for a node.
    
    Args:
        node_type: Type of node (e.g., 'gmail_trigger')
        user_intent: Parsed user intent
        
    Returns:
        Suggested configuration
    """
    config = {}
    
    # Gmail trigger defaults
    if node_type == "gmail_trigger":
        config = {
            "label_filter": "inbox",
            "search_query": user_intent.get("entities", [{}])[0].get("value", ""),
            "trigger_on": "received"
        }
    
    # Gmail send action defaults
    elif node_type == "gmail_send_email":
        config = {
            "to": "",  # User must fill
            "subject": "{{trigger.email.subject}}",  # Template variable
            "body": "",  # User must fill
            "reply_to": "{{trigger.email.from}}"
        }
    
    # Calendar create event defaults
    elif node_type in ["google_calendar_create_event", "outlook_calendar_create_event"]:
        config = {
            "calendar_id": "",  # User must select
            "title": "{{trigger.email.subject}}",
            "duration": 60,  # 1 hour default
            "description": "{{trigger.email.body}}",
            "start_time": "{{now + 1 day}}"
        }
    
    # Slack message defaults
    elif node_type == "slack_send_message":
        config = {
            "channel": "",  # User must select
            "message": "New notification: {{trigger.summary}}",
            "username": "SuiteCRM Bot"
        }
    
    # Webhook defaults
    elif node_type == "webhook_http_post":
        config = {
            "url": "",  # User must fill
            "method": "POST",
            "headers": {
                "Content-Type": "application/json"
            },
            "body": "{{trigger}}"
        }
    
    # SuiteCRM task defaults
    elif node_type == "suitecrm_create_task":
        config = {
            "title": "Follow up: {{trigger.subject}}",
            "due_date": "{{now + 3 days}}",
            "priority": "normal",
            "assigned_to": "{{current_user}}"
        }
    
    return config


def generate_workflow_summary(nodes: list[dict], edges: list[dict]) -> str:
    """
    Generate human-readable summary of a workflow.
    
    Args:
        nodes: List of workflow nodes
        edges: List of workflow edges
        
    Returns:
        Formatted summary
    """
    if not nodes:
        return "Empty workflow (no nodes)"
    
    # Find trigger nodes
    trigger_nodes = [n for n in nodes if "_trigger" in n.get("node_type", "")]
    action_nodes = [n for n in nodes if "_action" in n.get("node_type", "")]
    
    summary_parts = []
    
    # Describe triggers
    if trigger_nodes:
        triggers_desc = ", ".join([n.get("label", n.get("node_type", "")) for n in trigger_nodes])
        summary_parts.append(f"**Triggers:** {triggers_desc}")
    
    # Describe actions
    if action_nodes:
        actions_desc = ", ".join([n.get("label", n.get("node_type", "")) for n in action_nodes])
        summary_parts.append(f"**Actions:** {actions_desc}")
    
    # Describe flow
    if edges:
        summary_parts.append(f"**Steps:** {len(nodes)} nodes connected by {len(edges)} connections")
    
    return "\n".join(summary_parts)