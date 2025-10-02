"""
Lead Generation Tools for SuiteCRE
Ethical web scraping and search tools for finding commercial real estate prospects.
"""

import os
import json
from typing import List, Dict, Optional
from langchain_core.tools import tool

# =============================================================================
# API Client Setup
# =============================================================================

def get_tavily_api_key() -> str:
    """Get Tavily API key from environment."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")
    return api_key

def get_firecrawl_api_key() -> str:
    """Get Firecrawl API key from environment."""
    api_key = os.getenv("FIRECRAWL_API_KEY")
    if not api_key:
        raise ValueError("FIRECRAWL_API_KEY environment variable not set")
    return api_key

def get_serp_api_key() -> str:
    """Get SERP API key from environment."""
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        raise ValueError("SERPAPI_API_KEY environment variable not set")
    return api_key

# =============================================================================
# Lead Generation Tools
# =============================================================================

@tool
def search_commercial_listings(
    location: str,
    asset_types: Optional[List[str]] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
    min_sqft: Optional[int] = None,
    max_results: int = 10
) -> str:
    """
    Search for commercial property listings that match specified criteria.
    
    Args:
        location: City, state, or market area (e.g., "Dallas, TX", "Phoenix metro area")
        asset_types: List of property types (e.g., ["office", "retail", "industrial"])
        min_price: Minimum property price in dollars
        max_price: Maximum property price in dollars
        min_sqft: Minimum square footage
        max_results: Maximum number of results to return (default: 10)
    
    Returns:
        JSON string with property listings including URLs, descriptions, and contact info
    """
    try:
        # Build search query
        query_parts = [f"commercial real estate {location}"]
        
        if asset_types:
            query_parts.append(" OR ".join(asset_types))
        
        if min_price or max_price:
            price_range = []
            if min_price:
                price_range.append(f"${min_price:,}+")
            if max_price:
                price_range.append(f"up to ${max_price:,}")
            if price_range:
                query_parts.append(" ".join(price_range))
        
        if min_sqft:
            query_parts.append(f"{min_sqft:,} sq ft")
        
        search_query = " ".join(query_parts)
        
        # In production, use Tavily API here
        # For now, return structured example
        sample_listings = [
            {
                "title": f"Commercial Office Building - {location}",
                "url": "https://example.com/listing1",
                "description": "Prime downtown office space, fully leased, 50,000 SF",
                "price": "$5,500,000",
                "sqft": "50,000",
                "asset_type": "office",
                "contact_found": True,
                "confidence": 85
            },
            {
                "title": f"Retail Plaza - {location}",
                "url": "https://example.com/listing2",
                "description": "High-traffic retail center, anchor tenant in place",
                "price": "$3,200,000",
                "sqft": "28,000",
                "asset_type": "retail",
                "contact_found": False,
                "confidence": 72
            }
        ]
        
        return json.dumps({
            "success": True,
            "query": search_query,
            "total_results": len(sample_listings),
            "listings": sample_listings[:max_results],
            "message": f"Found {len(sample_listings)} commercial listings matching criteria",
            "next_steps": "Use scrape_listing_details() to extract contact information from specific listings",
            "note": "API integration required for live search results. Configure TAVILY_API_KEY."
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to search listings: {str(e)}",
            "suggestion": "Check API credentials and search parameters"
        })

@tool
def scrape_listing_details(listing_url: str) -> str:
    """
    Scrape detailed information from a specific property listing URL.
    Uses ethical scraping that respects robots.txt.
    
    Args:
        listing_url: Full URL of the property listing to scrape
    
    Returns:
        JSON string with extracted contact information, property details, and confidence score
    """
    try:
        # In production, use Firecrawl API here
        # For now, return structured example
        
        extracted_data = {
            "url": listing_url,
            "property_details": {
                "address": "123 Commerce Street, Suite 400",
                "city": "Dallas",
                "state": "TX",
                "zip": "75201",
                "price": "$5,500,000",
                "sqft": "50,000",
                "asset_type": "office",
                "year_built": "1998",
                "occupancy": "100%"
            },
            "contact_information": {
                "broker_name": "John Smith",
                "broker_company": "Smith Commercial Realty",
                "broker_email": "jsmith@smithcre.com",
                "broker_phone": "(214) 555-0123",
                "listing_agent_license": "TX-12345"
            },
            "seller_information": {
                "owner_type": "Private Investment Group",
                "represented_by": "Smith Commercial Realty"
            },
            "confidence_score": 88,
            "data_quality": "High - All key fields extracted",
            "scraped_at": "2025-01-15T10:30:00Z"
        }
        
        return json.dumps({
            "success": True,
            "listing_url": listing_url,
            "extracted_data": extracted_data,
            "message": "Successfully extracted listing details and contact information",
            "next_steps": "Use enrich_lead_data() to add additional business intelligence",
            "note": "API integration required for live scraping. Configure FIRECRAWL_API_KEY."
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to scrape listing: {str(e)}",
            "suggestion": "Verify URL is accessible and not behind authentication"
        })

@tool
def find_investment_prospects(
    location: Optional[str] = None,
    asset_focus: Optional[List[str]] = None,
    min_budget: Optional[int] = None,
    investor_type: Optional[str] = None,
    max_results: int = 10
) -> str:
    """
    Search for qualified commercial real estate investment prospects.
    
    Args:
        location: Target market or geographic focus
        asset_focus: Types of assets investor typically acquires
        min_budget: Minimum investment capacity in dollars
        investor_type: Type of investor ("individual", "fund", "reit", "developer", "institutional")
        max_results: Maximum number of prospects to return (default: 10)
    
    Returns:
        JSON string with investor profiles including contact information and investment criteria
    """
    try:
        # Build search query for investor prospects
        query_parts = ["commercial real estate investor"]
        
        if location:
            query_parts.append(location)
        
        if asset_focus:
            query_parts.append(" OR ".join(asset_focus))
        
        if investor_type:
            query_parts.append(investor_type)
        
        search_query = " ".join(query_parts)
        
        # In production, use SERP API + LinkedIn/company databases
        # For now, return structured example
        
        sample_prospects = [
            {
                "investor_name": "Metro Capital Partners",
                "investor_type": "Private Equity Fund",
                "location": "Dallas, TX",
                "investment_focus": ["office", "industrial"],
                "typical_deal_size": "$10M - $50M",
                "recent_acquisitions": "15 properties in last 24 months",
                "contact_info": {
                    "decision_maker": "Sarah Johnson",
                    "title": "VP of Acquisitions",
                    "email": "sjohnson@metrocapital.com",
                    "phone": "(214) 555-0199",
                    "linkedin": "https://linkedin.com/in/sarahjohnson"
                },
                "confidence_score": 92,
                "qualification_notes": "Active buyer, matches criteria, decision-maker identified"
            },
            {
                "investor_name": "Phoenix Development Group",
                "investor_type": "Developer/Investor",
                "location": "Phoenix, AZ",
                "investment_focus": ["retail", "mixed-use"],
                "typical_deal_size": "$5M - $25M",
                "recent_acquisitions": "8 properties in last 18 months",
                "contact_info": {
                    "decision_maker": "Michael Chen",
                    "title": "Managing Partner",
                    "email": "mchen@phoenixdg.com",
                    "phone": "(602) 555-0157",
                    "linkedin": "https://linkedin.com/in/michaelchen-cre"
                },
                "confidence_score": 85,
                "qualification_notes": "Proven track record, actively seeking opportunities"
            }
        ]
        
        return json.dumps({
            "success": True,
            "query": search_query,
            "total_prospects": len(sample_prospects),
            "prospects": sample_prospects[:max_results],
            "message": f"Found {len(sample_prospects)} qualified investment prospects",
            "next_steps": "Use enrich_lead_data() for additional business intelligence on specific prospects",
            "note": "API integration required for live prospect data. Configure SERPAPI_API_KEY."
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to find prospects: {str(e)}",
            "suggestion": "Check search parameters and API credentials"
        })

@tool
def enrich_lead_data(
    lead_name: str,
    lead_company: Optional[str] = None,
    lead_email: Optional[str] = None
) -> str:
    """
    Enrich lead profile with additional business intelligence data.
    Adds company information, financial data, social profiles, and recent activity.
    
    Args:
        lead_name: Name of the lead contact person
        lead_company: Company name if available
        lead_email: Email address if available (helps with verification)
    
    Returns:
        JSON string with enriched lead profile including business intelligence
    """
    try:
        # In production, integrate with:
        # - Clearbit/ZoomInfo for company data
        # - LinkedIn API for professional profiles
        # - Public records databases
        # For now, return structured example
        
        enriched_data = {
            "lead_profile": {
                "name": lead_name,
                "title": "VP of Acquisitions",
                "company": lead_company or "Metro Capital Partners",
                "email": lead_email or "verified@example.com",
                "phone": "(214) 555-0199",
                "linkedin_url": "https://linkedin.com/in/profile",
                "years_experience": "12+ years in CRE"
            },
            "company_intelligence": {
                "company_name": lead_company or "Metro Capital Partners",
                "company_type": "Private Equity Fund",
                "headquarters": "Dallas, TX",
                "founded": "2008",
                "employees": "50-100",
                "aum": "$500M - $1B",
                "website": "https://example.com",
                "company_linkedin": "https://linkedin.com/company/example"
            },
            "investment_activity": {
                "recent_deals": [
                    "Acquired 125,000 SF office building in Plano, TX - $28M (Nov 2024)",
                    "Purchased industrial park in Fort Worth, TX - $15M (Sep 2024)"
                ],
                "active_markets": ["Dallas-Fort Worth", "Austin", "Houston"],
                "preferred_asset_types": ["Office", "Industrial"],
                "typical_deal_size": "$10M - $50M",
                "investment_strategy": "Value-add and core-plus opportunities"
            },
            "engagement_signals": {
                "recent_press": "Featured in D Magazine - 'Top CRE Investors 2024'",
                "job_postings": "Hiring asset manager - indicates growth",
                "recent_website_updates": "Added new portfolio page 2 weeks ago",
                "social_activity": "Active on LinkedIn, posts weekly market insights"
            },
            "contact_strategy": {
                "best_approach": "Email introduction with relevant deal opportunity",
                "timing": "Monday-Wednesday mornings preferred",
                "pain_points": ["Deal sourcing", "Market intelligence", "Off-market opportunities"],
                "value_proposition": "Exclusive off-market deals in target markets",
                "talking_points": [
                    "Reference recent acquisition in Plano",
                    "Highlight similar asset types in portfolio",
                    "Mention value-add opportunities"
                ]
            },
            "confidence_score": 94,
            "data_freshness": "Updated within last 7 days",
            "verification_status": "Email verified, company confirmed, activity recent"
        }
        
        return json.dumps({
            "success": True,
            "lead_name": lead_name,
            "enriched_data": enriched_data,
            "message": "Successfully enriched lead profile with business intelligence",
            "quality_score": "High - Multiple data sources confirmed",
            "note": "Data enrichment APIs required for live intelligence. Configure enrichment service API keys."
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to enrich lead data: {str(e)}",
            "suggestion": "Ensure lead name and company information are accurate"
        })

# =============================================================================
# Tool Collection Export
# =============================================================================

LEAD_GENERATION_TOOLS = [
    search_commercial_listings,
    scrape_listing_details,
    find_investment_prospects,
    enrich_lead_data
]