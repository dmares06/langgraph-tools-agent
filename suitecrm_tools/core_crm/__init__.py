"""Core CRM functionality tools."""

from .broker import get_broker_profile
from .contacts import get_contacts
from .deals import get_deals
from .listings import get_listings, get_recent_inquiries, get_campaigns_performance
# Add write operations
from .contact_operations import create_contact, update_contact
from .deal_operations import create_deal, update_deal
from .listing_operations import create_listing, update_listing

__all__ = [
    'get_broker_profile',
    'get_contacts',
    'get_deals',
    'get_listings',
    'get_recent_inquiries',
    'get_campaigns_performance',
    # Write operations
    'create_contact',
    'update_contact',
    'create_deal',
    'update_deal',
    'create_listing',
    'update_listing',
]