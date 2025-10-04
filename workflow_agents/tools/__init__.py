# workflow_agents/tools/__init__.py
"""
Tools for workflow agents.
"""

from workflow_agents.tools.flow_graph_tools import (
    create_workflow_flow,
    get_workflow_flow,
    update_workflow_flow,
    delete_workflow_flow,
    create_workflow_node,
    update_workflow_node,
    delete_workflow_node,
    create_workflow_edge,
    delete_workflow_edge,
    list_user_workflows,
    bulk_create_nodes,
    bulk_create_edges
)

from workflow_agents.tools.connector_tools import (
    list_all_connectors,
    get_connector_details,
    get_connector_triggers,
    get_connector_actions,
    search_connectors,
    get_connectors_by_category,
    check_connector_compatibility,
    get_connector_oauth_requirements
)

from workflow_agents.tools.credentials_tools import (
    list_user_credentials,
    check_credential_exists,
    get_oauth_connection_url,
    store_credential,
    delete_credential,
    get_credential_for_connector,
    check_credentials_for_workflow
)

from workflow_agents.tools.validation_tools import (
    validate_workflow,
    dry_run_workflow,
    get_validation_issues,
    resolve_validation_issue
)

from workflow_agents.tools.logs_tools import (
    get_workflow_runs,
    get_run_details,
    get_run_logs,
    get_recent_errors,
    get_workflow_statistics,
    search_logs
)

from workflow_agents.tools.supabase_tools import (
    search_contacts,
    search_deals,
    search_listings,
    get_contact_by_email,
    fuzzy_match_contact,
    create_contact
)

__all__ = [
    # Flow graph tools
    "create_workflow_flow",
    "get_workflow_flow",
    "update_workflow_flow",
    "delete_workflow_flow",
    "create_workflow_node",
    "update_workflow_node",
    "delete_workflow_node",
    "create_workflow_edge",
    "delete_workflow_edge",
    "list_user_workflows",
    "bulk_create_nodes",
    "bulk_create_edges",
    
    # Connector tools
    "list_all_connectors",
    "get_connector_details",
    "get_connector_triggers",
    "get_connector_actions",
    "search_connectors",
    "get_connectors_by_category",
    "check_connector_compatibility",
    "get_connector_oauth_requirements",
    
    # Credentials tools
    "list_user_credentials",
    "check_credential_exists",
    "get_oauth_connection_url",
    "store_credential",
    "delete_credential",
    "get_credential_for_connector",
    "check_credentials_for_workflow",
    
    # Validation tools
    "validate_workflow",
    "dry_run_workflow",
    "get_validation_issues",
    "resolve_validation_issue",
    
    # Logs tools
    "get_workflow_runs",
    "get_run_details",
    "get_run_logs",
    "get_recent_errors",
    "get_workflow_statistics",
    "search_logs",
    
    # Supabase tools
    "search_contacts",
    "search_deals",
    "search_listings",
    "get_contact_by_email",
    "fuzzy_match_contact",
    "create_contact"
]