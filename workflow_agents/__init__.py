# workflow_agents/__init__.py
"""
Workflow Agents - LangGraph-based automation workflow system.
"""

from workflow_agents.config import config
from workflow_agents.constants import (
    WORKFLOW_TYPE_AUTOMATION,
    WORKFLOW_TYPE_PIPELINE,
    AVAILABLE_CONNECTORS,
    CONNECTOR_CATEGORIES
)

__version__ = "1.0.0"

__all__ = [
    
    # Config
    "config",
    
    # Constants
    "WORKFLOW_TYPE_AUTOMATION",
    "WORKFLOW_TYPE_PIPELINE",
    "AVAILABLE_CONNECTORS",
    "CONNECTOR_CATEGORIES",
]