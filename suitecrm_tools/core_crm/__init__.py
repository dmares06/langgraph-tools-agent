"""Core CRM functionality tools."""

from .broker import get_broker_profile
from .contacts import get_contacts
from .deals import get_deals
from .listings import get_listings, get_recent_inquiries, get_campaigns_performance

__all__ = [
    'get_broker_profile',
    'get_contacts', 
    'get_deals',
    'get_listings',
    'get_recent_inquiries',
    'get_campaigns_performance'
]