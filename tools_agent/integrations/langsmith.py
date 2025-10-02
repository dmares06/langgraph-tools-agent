"""LangSmith integration for observability and tracing."""

import os
from typing import Optional, Dict, Any

def setup_langsmith(project_name: str = "SuiteCRE-Agent") -> None:
    """
    Setup LangSmith tracing for agent observability.
    
    Args:
        project_name: Name of the LangSmith project for organizing traces
    """
    # Set LangSmith environment variables if API key is available
    langsmith_api_key = os.getenv("LANGCHAIN_API_KEY")
    
    if langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = project_name
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
        print(f"✓ LangSmith tracing enabled for project: {project_name}")
    else:
        print("⚠ LangSmith API key not found. Tracing disabled.")

def create_run_metadata(
    user_id: Optional[str] = None,
    agent_mode: Optional[str] = None,
    additional_metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create metadata for LangSmith run tracking.
    
    Args:
        user_id: User identifier for tracking
        agent_mode: Which agent is being used
        additional_metadata: Any additional metadata to include
    
    Returns:
        Dictionary of metadata for the run
    """
    metadata = {
        "agent_mode": agent_mode or "chat_copilot",
        "application": "SuiteCRE",
    }
    
    if user_id:
        metadata["user_id"] = user_id
    
    if additional_metadata:
        metadata.update(additional_metadata)
    
    return metadata