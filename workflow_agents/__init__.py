# workflow_agents/__init__.py
"""
Workflow Agents - LangGraph-based automation workflow system.
"""

from workflow_agents.supervisor import (
    create_supervisor_graph,
    workflow_supervisor,
    invoke_workflow_supervisor
)

from workflow_agents.config import config
from workflow_agents.constants import (
    WORKFLOW_TYPE_AUTOMATION,
    WORKFLOW_TYPE_PIPELINE,
    AVAILABLE_CONNECTORS,
    CONNECTOR_CATEGORIES
)

from workflow_agents.agents import (
    builder_agent,
    validator_agent,
    explainer_agent,
    data_mapper_agent
)

__version__ = "1.0.0"

__all__ = [
    # Supervisor
    "create_supervisor_graph",
    "workflow_supervisor",
    "invoke_workflow_supervisor",
    
    # Config
    "config",
    
    # Constants
    "WORKFLOW_TYPE_AUTOMATION",
    "WORKFLOW_TYPE_PIPELINE",
    "AVAILABLE_CONNECTORS",
    "CONNECTOR_CATEGORIES",
    
    # Individual agents
    "builder_agent",
    "validator_agent",
    "explainer_agent",
    "data_mapper_agent"
]