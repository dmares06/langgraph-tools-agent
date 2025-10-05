# workflow_agents/state.py
"""
State schemas for workflow agents.
Defines the shared state structure used across all agents.
"""

from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage


class WorkflowAgentState(TypedDict):
    """
    Shared state for all workflow agents.
    
    This state is passed between agents in the supervisor system.
    """
    # Message history (core state)
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Workflow context
    workflow_type: Literal["automation", "pipeline"]  # Which type of workflow
    flow_id: str | None  # UUID of current workflow being edited
    
    # Agent routing
    current_agent: str | None  # Which agent is currently active
    agent_history: list[str]  # Track which agents have been called
    
    # User context
    user_id: str  # From auth
    org_id: str | None
    
    # Workflow draft state
    draft_nodes: list[dict] | None  # Nodes being built
    draft_edges: list[dict] | None  # Edges being built
    
    # Validation state
    validation_issues: list[dict] | None  # Issues found by Validator
    can_activate: bool | None  # Whether workflow can be activated
    
    # Explanation state
    run_id: str | None  # For explaining specific runs
    
    # Data mapping state
    mapping_context: dict | None  # Context for Data Mapper
    
    # Rate limiting
    action_count: dict[str, int]  # Track actions for rate limiting


class WorkflowBuilderState(TypedDict):
    """State specific to Builder Agent."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # ADD THIS LINE - Required by create_react_agent
    flow_id: str | None
    user_intent: dict | None  # Parsed intent from NL
    selected_connectors: list[str] | None  # Which connectors to use
    missing_connections: list[str] | None  # OAuth needed
    proposed_nodes: list[dict] | None
    proposed_edges: list[dict] | None


class WorkflowValidatorState(TypedDict):
    """State specific to Validator Agent."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # ADD THIS LINE
    flow_id: str
    validation_results: dict | None
    issues_found: list[dict] | None
    dry_run_results: dict | None


class WorkflowExplainerState(TypedDict):
    """State specific to Explainer Agent."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # ADD THIS LINE
    flow_id: str | None
    run_id: str | None
    run_logs: list[dict] | None
    step_details: dict | None


class WorkflowDataMapperState(TypedDict):
    """State specific to Data Mapper Agent."""
    messages: Annotated[list[AnyMessage], add_messages]
    remaining_steps: int  # ADD THIS LINE
    source_data: dict
    target_entities: list[str]
    matches: list[dict] | None
    confidence_threshold: float