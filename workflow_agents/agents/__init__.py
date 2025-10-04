# workflow_agents/agents/__init__.py
"""
Workflow agents for automation building.
"""

from workflow_agents.agents.builder import (
    create_builder_agent,
    builder_agent,
    invoke_builder_agent,
    parse_workflow_intent_from_message,
    suggest_node_configuration,
    generate_workflow_summary
)

from workflow_agents.agents.validator import (
    create_validator_agent,
    validator_agent,
    invoke_validator_agent,
    format_validation_results,
    prioritize_issues,
    group_issues_by_type
)

from workflow_agents.agents.explainer import (
    create_explainer_agent,
    explainer_agent,
    invoke_explainer_agent,
    format_run_explanation,
    analyze_error_and_suggest_fix,
    identify_error_patterns
)

from workflow_agents.agents.data_mapper import (
    create_data_mapper_agent,
    data_mapper_agent,
    invoke_data_mapper_agent,
    calculate_match_confidence,
    format_mapping_results,
    suggest_entity_creation,
    normalize_contact_data
)

__all__ = [
    # Builder
    "create_builder_agent",
    "builder_agent",
    "invoke_builder_agent",
    "parse_workflow_intent_from_message",
    "suggest_node_configuration",
    "generate_workflow_summary",
    
    # Validator
    "create_validator_agent",
    "validator_agent",
    "invoke_validator_agent",
    "format_validation_results",
    "prioritize_issues",
    "group_issues_by_type",
    
    # Explainer
    "create_explainer_agent",
    "explainer_agent",
    "invoke_explainer_agent",
    "format_run_explanation",
    "analyze_error_and_suggest_fix",
    "identify_error_patterns",
    
    # Data Mapper
    "create_data_mapper_agent",
    "data_mapper_agent",
    "invoke_data_mapper_agent",
    "calculate_match_confidence",
    "format_mapping_results",
    "suggest_entity_creation",
    "normalize_contact_data"
]