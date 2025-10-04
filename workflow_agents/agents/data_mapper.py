# workflow_agents/agents/data_mapper.py
"""
Workflow Data Mapper Agent - Maps external data to CRM entities.
"""

import logging
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

from workflow_agents.config import config
from workflow_agents.constants import WORKFLOW_DATA_MAPPER_PROMPT
from workflow_agents.state import WorkflowDataMapperState
from workflow_agents.tools import (
    search_contacts,
    search_deals,
    search_listings,
    get_contact_by_email,
    fuzzy_match_contact,
    create_contact
)

logger = logging.getLogger(__name__)


def create_data_mapper_agent():
    """
    Create the Workflow Data Mapper Agent.
    
    This agent specializes in:
    - Mapping email data to CRM contacts
    - Matching addresses to property listings
    - Fuzzy matching for similar names
    - Creating new entities when no match found
    - Learning from user corrections
    
    Returns:
        Compiled LangGraph agent
    """
    
    # Initialize LLM
    model = init_chat_model(
        config.model_name,
        temperature=0.3,  # Lower temperature for accurate matching
        max_tokens=config.max_tokens
    )
    
    # Data Mapper-specific tools
    mapper_tools = [
        search_contacts,
        search_deals,
        search_listings,
        get_contact_by_email,
        fuzzy_match_contact,
        create_contact
    ]
    
    # Create agent
    agent = create_react_agent(
        model=model,
        tools=mapper_tools,
        state_schema=WorkflowDataMapperState,
        prompt=WORKFLOW_DATA_MAPPER_PROMPT
    )
    
    logger.info("Workflow Data Mapper Agent created")
    
    return agent


# Pre-compiled agent instance
data_mapper_agent = create_data_mapper_agent()


async def invoke_data_mapper_agent(state: dict, config: dict) -> dict:
    """
    Invoke the Data Mapper Agent with state and config.
    
    Args:
        state: Current workflow state
        config: Runtime configuration
        
    Returns:
        Updated state with mapping results
    """
    try:
        result = await data_mapper_agent.ainvoke(state, config)
        return result
    except Exception as e:
        logger.error(f"Error invoking Data Mapper Agent: {str(e)}")
        return {
            "messages": state.get("messages", []) + [{
                "role": "assistant",
                "content": f"I encountered an error while mapping data: {str(e)}"
            }]
        }


def calculate_match_confidence(
    source_data: dict,
    crm_entity: dict,
    match_type: str
) -> float:
    """
    Calculate confidence score for a data match.
    
    Args:
        source_data: Source data to map
        crm_entity: CRM entity being matched to
        match_type: Type of match (email_exact, name_fuzzy, etc.)
        
    Returns:
        Confidence score (0.0 to 1.0)
    """
    base_confidence = {
        "email_exact": 0.95,
        "phone_exact": 0.90,
        "name_exact": 0.85,
        "email_fuzzy": 0.75,
        "name_fuzzy": 0.70,
        "phone_fuzzy": 0.70,
        "semantic": 0.60
    }
    
    confidence = base_confidence.get(match_type, 0.50)
    
    # Boost confidence if multiple fields match
    matches = 0
    if source_data.get("email") and crm_entity.get("email"):
        if source_data["email"].lower() == crm_entity["email"].lower():
            matches += 1
    
    if source_data.get("phone") and crm_entity.get("phone"):
        # Normalize phone numbers for comparison
        source_phone = source_data["phone"].replace("-", "").replace(" ", "")
        crm_phone = crm_entity["phone"].replace("-", "").replace(" ", "")
        if source_phone == crm_phone:
            matches += 1
    
    if source_data.get("name") and crm_entity.get("name"):
        if source_data["name"].lower() in crm_entity["name"].lower() or \
           crm_entity["name"].lower() in source_data["name"].lower():
            matches += 1
    
    # Boost by 5% for each additional matching field
    confidence += (matches * 0.05)
    
    return min(confidence, 1.0)  # Cap at 1.0


def format_mapping_results(matches: list[dict], unmapped: list[str]) -> str:
    """
    Format data mapping results into human-readable message.
    
    Args:
        matches: List of successful matches
        unmapped: List of unmapped fields
        
    Returns:
        Formatted message
    """
    message = "🗺️ **Data Mapping Results**\n\n"
    
    if matches:
        message += "**✅ Matched Fields:**\n"
        for match in matches:
            confidence = match.get("confidence", 0.0)
            confidence_pct = int(confidence * 100)
            
            # Confidence indicator
            if confidence >= 0.9:
                indicator = "🟢"
            elif confidence >= 0.7:
                indicator = "🟡"
            else:
                indicator = "🟠"
            
            message += f"{indicator} **{match['field']}** → {match['crm_entity']} "
            message += f"*{match['crm_name']}* ({confidence_pct}% confidence)\n"
            message += f"   Match type: {match.get('match_type', 'unknown')}\n\n"
    
    if unmapped:
        message += "\n**❓ Unmapped Fields:**\n"
        for field in unmapped:
            message += f"- {field}\n"
        message += "\n💡 Would you like me to create new CRM entries for these?\n"
    
    return message


def suggest_entity_creation(unmapped_field: str, value: str) -> dict:
    """
    Suggest creating a new CRM entity for unmapped data.
    
    Args:
        unmapped_field: Field that couldn't be mapped
        value: Value of the unmapped field
        
    Returns:
        Suggestion for creating new entity
    """
    suggestions = {
        "email": {
            "entity_type": "contact",
            "reason": f"No existing contact found with email: {value}",
            "action": "create_contact",
            "fields": {
                "email": value,
                "name": value.split("@")[0].replace(".", " ").title()
            }
        },
        "phone": {
            "entity_type": "contact",
            "reason": f"No existing contact found with phone: {value}",
            "action": "create_contact",
            "fields": {
                "phone": value
            }
        },
        "address": {
            "entity_type": "listing",
            "reason": f"No existing listing found for address: {value}",
            "action": "create_listing",
            "fields": {
                "address": value
            }
        },
        "company": {
            "entity_type": "company",
            "reason": f"No existing company found: {value}",
            "action": "create_company",
            "fields": {
                "name": value
            }
        }
    }
    
    return suggestions.get(unmapped_field, {
        "entity_type": "unknown",
        "reason": f"Could not map field: {unmapped_field}",
        "action": "manual_review",
        "fields": {}
    })


def normalize_contact_data(raw_data: dict) -> dict:
    """
    Normalize contact data for consistent matching.
    
    Args:
        raw_data: Raw contact data
        
    Returns:
        Normalized data
    """
    normalized = {}
    
    # Normalize email
    if raw_data.get("email"):
        normalized["email"] = raw_data["email"].strip().lower()
    
    # Normalize phone
    if raw_data.get("phone"):
        phone = raw_data["phone"]
        # Remove common formatting
        phone = phone.replace("-", "").replace("(", "").replace(")", "")
        phone = phone.replace(" ", "").replace(".", "")
        normalized["phone"] = phone
    
    # Normalize name
    if raw_data.get("name"):
        name = raw_data["name"].strip()
        # Title case
        name = " ".join(word.capitalize() for word in name.split())
        normalized["name"] = name
    
    # Pass through other fields
    for key, value in raw_data.items():
        if key not in ["email", "phone", "name"]:
            normalized[key] = value
    
    return normalized