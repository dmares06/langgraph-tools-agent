"""Main SuiteCRE CRM tools registry."""

# Import all tool modules
from .core_crm import (
    get_broker_profile,
    get_contacts,
    get_deals,
    get_listings,
    get_recent_inquiries,
    get_campaigns_performance,
    # Write operations
    create_contact,
    update_contact,
    create_deal,
    update_deal,
    create_listing,
    update_listing,
)

from .documents import (
    get_broker_documents,
    search_broker_documents,
    get_listing_documents, 
    search_listing_documents
)

from .analytics import (
    get_business_analytics,
    get_daily_summary
)

from .om_bov import (
    analyze_listing_documents,
    research_market_data,
    generate_om_content,
    review_om_quality
)

from .productivity import (
    get_calendar_events,
    get_tasks,
    create_task,
    update_task,
    create_note,
    update_note,
    create_calendar_event,
    update_calendar_event,
)

PRODUCTIVITY_TOOLS = [
    get_calendar_events,
    get_tasks,
    create_task,
    update_task,
    create_note,
    update_note,
    create_calendar_event,
    update_calendar_event,
]

# Update tool collections
CORE_CRM_TOOLS = [
    get_broker_profile,
    get_contacts,
    get_deals,
    get_listings,
    get_recent_inquiries,
    get_campaigns_performance,
    create_contact,
    update_contact,
    create_deal,
    update_deal,
    create_listing,
    update_listing,
]

DOCUMENT_TOOLS = [
    get_broker_documents,
    search_broker_documents,
    get_listing_documents,
    search_listing_documents
]

ANALYTICS_TOOLS = [
    get_business_analytics,
    get_daily_summary
]

OM_BOV_TOOLS = [
    analyze_listing_documents,
    research_market_data,
    generate_om_content,
    review_om_quality
]

# Complete tools list (maintain backward compatibility)
CRM_TOOLS = [
    *CORE_CRM_TOOLS,
    *DOCUMENT_TOOLS, 
    *ANALYTICS_TOOLS,
    *OM_BOV_TOOLS,
    *PRODUCTIVITY_TOOLS
]

# Tool collections by category for selective imports
TOOL_COLLECTIONS = {
    'core_crm': CORE_CRM_TOOLS,
    'documents': DOCUMENT_TOOLS,
    'analytics': ANALYTICS_TOOLS,
    'om_bov': OM_BOV_TOOLS,
    'productivity': PRODUCTIVITY_TOOLS,
    'all': CRM_TOOLS
}

def get_tools_by_category(category: str = 'all'):
    """
    Get tools by category.
    
    Args:
        category: Tool category ('core_crm', 'documents', 'analytics', 'om_bov', 'productivity', 'all')
    
    Returns:
        List of tools for the specified category
    """
    return TOOL_COLLECTIONS.get(category, CRM_TOOLS)