""" 
Complete SuiteCRE CRM Tools for Chat Copilot Agent
"""

import base64
import os
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
from supabase import create_client, Client
from datetime import datetime, timedelta
import json
from openai import OpenAI

def get_supabase_client(url: str, key: str) -> Client:
    """Get authenticated Supabase client using environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY environment variables.")

    return create_client(supabase_url, supabase_key)

def get_openai_client(api_key: str) -> OpenAI:
    """Get OpenAI client for embeddings."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Missing OPENAI_API_KEY environment variable.")

    return OpenAI(api_key=api_key)

def get_embedding(text: str, model: str = "text-embedding-3-small") -> List[float]:
    """Get embedding for text."""
    try:
        client = get_openai_client()
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        raise Exception(f"Failed to get embedding: {str(e)}")
        print(f"Error getting embedding: {str(e)}")
        return None
@tool
def get_broker_profile() -> str:
    """ 
    Get the current broker's profile information including name and company details.
    This provides context about who the agent is helping.

    Returns:
        JSON string with probker profile information
    """
    try:
        supabase = get_supabase_client()

        profile = profile_result.data[0]

        if profile_result.data:
           return_json = json.dumps({
                "success": True,
            "broker_name": profile.get("agent_name", "Unkown"),
            "company_name": profile.get("company_name", "Unkown company"),
            "email": profile.get("email"),
            "phone": profile.get("phone_number"),
            "message": f"Profile found for {profile.get('agent_name', 'broker')}. I'm Nexa, your ai assistant ready to assist you with your CRM needs."
        }, default=str)
    else:
        return_json = json.dumps({
            "success": False,
            "message": "No profile information found. Please set up your broker profile in settings.",
            "suggestion": "Add your name and company information in your SuiteCRE profile settings."
        })
    except Exception as e:
        return_json = json.dumps({
        "success": False, 
        "error": f"Unable to retrieve broker profile: {str(e)}",
        "suggestion": "Please check your SuiteCRE profile settings and try again."
    })

@tool 
def get_contacts(
    limit: int = 10,
    tags: Optional[List[str]] = None, 
    asset_type: Optional[List[str]] = None,
    email_subscribed: Optional[bool] = None
) -> str:
    """
    Get contacts from CRM with optional filtering.
    
    Args:
        limit: Maximum number of contacts to return (default: 10)
        tags: Filter by contact tags (e.g. ['High-Value', 'investor', 'seller'])
        asset_type: Filter by asset types (e.g. ['office', 'retail', 'industrial', 'multifamily', 'mixed-use', 'warehouse', 'land', 'other'])
        email_subscribed: Filter by email subscription status

    Returns:
        JSON string with contact information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("contacts").select("*")

        if tags:
            query = query.contains("tags", tags)
        if asset_type:
            query = query.contains("asset_type", asset_type)
        if email_subscribed:
            query = query.eq("email_subscriber", email_subscribed)

        result = query.limit(limit).order("created_at", desc=True).execute()

        if not result.data:
            return_json = json.dumps({
                "success": True,
                "message": "No contacts found matching the criteria. Try adjusting your filters or check if contacts have been added to your CRM.",
                "contacts": [],
                "count": 0,
                "suggestion": "Remove filters or add new contacts to see results."
            })

        return_json = json.dumps({
            "success": True,
            "contacts": result.data,
            "count": len(result.data),
            "message": f"Found {len(result.data)} contacts matching your criteria."
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve contacts: {str(e)}",
            "suggestion": "Please check your database and try again."
        })

@tool
def get_deals(
    limit: int = 10,
    stage: Optional[List[str]] = None,
    min_value: Optional[float] = None,
    closing_soon_days: Optional[int] = None,
) -> str:
    """
    Get deals from pipeline with optional filtering. 

    Args:
        limit: Maximum number of deals to return (default: 10)
        stage: Filter by deal stage (e.g. ['qualified','proposal', 'negotiation', 'closing'])
        min_value: Filter by minimum deal value (e.g. 1000000)
        closing_soon_days: Show deals closing within X days(e.g. closing in 30 days)

    Returns:
        JSON string with deal information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("deals").select("""
            *,
            contacts:contacts(name, email, company)
        """)

        if stage: 
            query = query.eq("stage", stage)
        if min_value:
            query = query.gte("value", min_value)
        if closing_soon_days:
            cutoff_date = datetime.now() + timedelta(days=closing_soon_days)
            query = query.lte("expected_close", datetime.now() + timedelta(days=closing_soon_days))

        result = query.limit(limit).order("created_at", desc=True).execute()

        if not result.data:
            filter_msg = []
            if stage: filter_msg.append(f"stage: {stage}")
            if min_value: filter_msg.append(f"value > ${min_value:,.Of}")
            if closing_soon_days: filter_msg.append(f"closing within {closing_soon_days} days")

            return_json = json.dumps({
                "success": True,
                "message": f"No deals found with {' and '.join(filter_msg) if filter_msg else 'your criteria'.}",
                "deals": [],
                "count": 0,
                "suggestion": "Try different filters or check if deals have been added to your pipeline."
            })

        return_json = json.dumps({
            "success": True,
            "deals": result.data,
            "count": len(result.data),
            "message": f"Found {len(result.data)} deals in your pipeline."
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve deals: {str(e)}",
            "suggestion": "Please verify your data pipeline and try again."
        })

@tool
def get_listings(
    limit: int = 10,
    status: Optional[List[str]] = None,
    listing_type: Optional[List[str]] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
) -> str:
    """
    Get listings from CRM with optional filtering.

    Args:
    limit: Maximum number of listings to return (default: 10)
    status: Filter by listing status (e.g. ['active', 'inactive','LOI',  'under contract', 'sold'])
    listing_type: Filter by listing type (e.g. ['sale', 'lease', 'auction', 'foreclosure'])
    min_price: Filter by minimum asking price (e.g. 1000000)
    max_price: Filter by maximum asking price (e.g. 10000000)

    Returns:
        JSON string with listing information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("listings").select("""
        *,
        contact:contacts(name, email, company)
        """)

        if status:
            query = query.contains("status", status)
        if listing_type:
            query = query.contains("listing_type", listing_type)
        if min_price:
            query: query.gte("asking_price", min_price)
        if max_price:
            query = query.lte("asking_price", max_price)

        result = query.limit(limit).order("created_at", desc=True).execute()

        return_json = json.dumps({
            "success": True,
            "listings": result.data,
            "count": len(result.data),
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve listings: {str(e)}",
            "suggestion": "Please verify your data pipeline and try again."
        })
    
@tool
def get_recent_inquiries(limit: int = 10, status: Optional[str] = None) -> str:
    """
    Get recent listing inquiries

    Args:
        limit: Maximum number of inquiries to return (default: 10)
        status: Filter by inquiry status (e.g. 'pending', 'responded', 'resolved', etc.)

    Returns:
        JSON string with inquiry information including listing details and contact information if provided
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("listing_inquiries").select("""
            *,
            listing:listings(address, asking_price, title, listing_type, status)
        """)

        if status:
            query = query.eq("status", status)

        result = query.limit(limit).order("created_at", desc=True).execute()
        
        return_json = json.dumps({
            "success": True,
            "inquiries": result.data,
            "count": len(result.data),
        }, default=str)
    
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve inquiries: {str(e)}",
        })
    
@tool
def get_campaigns_performance(limit: int = 5, status: Optional[str] = None) -> str:
    """
    Get campaign performance metrics.

    Args:
        limit: Maximum number of campaigns to return (default: 5)

    Returns:
        JSON string with campaign performance data
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("email_campaigns").select("*").limit(limit).order("created_at", desc=True).execute()
        
        return_json = json.dumps({
        "success": True,
        "campaigns": result.data,
        "count": len(result.data),
    }, default=str)
   
    
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to retrieve campaigns performance: {str(e)}",
        })

@tool
def get_business_analytics(
    time_period: str = "monthly",
    include_recommendations: bool = True,
    focus_area: Optional[str] = None
) -> str:
    """
    Get comprehensive business analytics and performance insights for the broker.
    
    Args:
        time_period: Analysis period ("weekly", "monthly", "quarterly", "yearly")
        include_recommendations: Whether to include improvement recommendations
        focus_area: Specific area to analyze ("revenue", "efficiency", "pipeline", "marketing")
    
    Returns:
        JSON string with business analytics and performance recommendations
    """
    try:
        supabase = get_supabase_client()
        from datetime import datetime, timedelta
        
        # Calculate date ranges based on time period
        today = datetime.now()
        if time_period == "weekly":
            start_date = today - timedelta(weeks=1)
            previous_start = today - timedelta(weeks=2)
        elif time_period == "monthly":
            start_date = today - timedelta(days=30)
            previous_start = today - timedelta(days=60)
        elif time_period == "quarterly":
            start_date = today - timedelta(days=90)
            previous_start = today - timedelta(days=180)
        else:  # yearly
            start_date = today - timedelta(days=365)
            previous_start = today - timedelta(days=730)
        
        # Revenue Analytics
        deals_current = supabase.table("deals").select("*").gte("created_at", start_date.isoformat()).execute()
        deals_previous = supabase.table("deals").select("*").gte("created_at", previous_start.isoformat()).lt("created_at", start_date.isoformat()).execute()
        
        current_revenue = sum(deal.get("deal_value", 0) or 0 for deal in deals_current.data if deal.get("stage") == "closed")
        previous_revenue = sum(deal.get("deal_value", 0) or 0 for deal in deals_previous.data if deal.get("stage") == "closed")
        
        # Pipeline Analytics
        pipeline_deals = [deal for deal in deals_current.data if deal.get("stage") not in ["closed", "lost"]]
        pipeline_value = sum(deal.get("deal_value", 0) or 0 for deal in pipeline_deals)
        
        # Contact Analytics
        contacts_current = supabase.table("contacts").select("*").gte("created_at", start_date.isoformat()).execute()
        contacts_previous = supabase.table("contacts").select("*").gte("created_at", previous_start.isoformat()).lt("created_at", start_date.isoformat()).execute()
        
        # Listing Analytics
        listings_current = supabase.table("listings").select("*").gte("created_at", start_date.isoformat()).execute()
        active_listings = supabase.table("listings").select("*").eq("status", "ACTIVE").execute()
        
        # Campaign Analytics
        campaigns_current = supabase.table("email_campaigns").select("*").gte("created_at", start_date.isoformat()).execute()
        
        # Calculate key metrics
        revenue_growth = ((current_revenue - previous_revenue) / max(previous_revenue, 1)) * 100 if previous_revenue else 0
        contact_growth = ((len(contacts_current.data) - len(contacts_previous.data)) / max(len(contacts_previous.data), 1)) * 100
        
        avg_deal_size = current_revenue / max(len([d for d in deals_current.data if d.get("stage") == "closed"]), 1)
        conversion_rate = (len([d for d in deals_current.data if d.get("stage") == "closed"]) / max(len(contacts_current.data), 1)) * 100
        
        # Performance Analysis
        analytics_data = {
            "period_analysis": {
                "time_period": time_period,
                "start_date": start_date.isoformat(),
                "end_date": today.isoformat()
            },
            "revenue_metrics": {
                "current_revenue": current_revenue,
                "previous_revenue": previous_revenue,
                "revenue_growth_percent": round(revenue_growth, 2),
                "average_deal_size": round(avg_deal_size, 2),
                "deals_closed": len([d for d in deals_current.data if d.get("stage") == "closed"])
            },
            "pipeline_metrics": {
                "pipeline_value": pipeline_value,
                "deals_in_pipeline": len(pipeline_deals),
                "conversion_rate_percent": round(conversion_rate, 2),
                "average_deal_cycle": "Analysis needed - requires deal stage tracking"
            },
            "activity_metrics": {
                "new_contacts": len(contacts_current.data),
                "contact_growth_percent": round(contact_growth, 2),
                "new_listings": len(listings_current.data),
                "active_listings": len(active_listings.data),
                "campaigns_sent": len(campaigns_current.data)
            },
            "efficiency_metrics": {
                "contacts_per_deal": round(len(contacts_current.data) / max(len(deals_current.data), 1), 2),
                "listings_per_deal": round(len(listings_current.data) / max(len(deals_current.data), 1), 2),
                "campaign_effectiveness": "Requires campaign response tracking"
            }
        }
        
        # Generate recommendations if requested
        recommendations = []
        if include_recommendations:
            if revenue_growth < 0:
                recommendations.append({
                    "category": "Revenue Growth",
                    "priority": "High",
                    "issue": f"Revenue declined {abs(revenue_growth):.1f}% from previous {time_period}",
                    "recommendation": "Focus on deal velocity and larger opportunities. Review lost deals for patterns.",
                    "action_items": ["Analyze lost deal reasons", "Target higher-value prospects", "Improve closing techniques"]
                })
            
            if conversion_rate < 5:
                recommendations.append({
                    "category": "Lead Conversion",
                    "priority": "Medium",
                    "issue": f"Low conversion rate at {conversion_rate:.1f}%",
                    "recommendation": "Improve lead qualification and follow-up processes",
                    "action_items": ["Implement lead scoring", "Automate follow-up sequences", "Focus on higher-quality leads"]
                })
            
            if len(pipeline_deals) < 5:
                recommendations.append({
                    "category": "Pipeline Health",
                    "priority": "High",
                    "issue": f"Only {len(pipeline_deals)} deals in pipeline",
                    "recommendation": "Increase prospecting activities and lead generation",
                    "action_items": ["Use lead generation agent more frequently", "Expand networking activities", "Increase marketing campaigns"]
                })
            
            if len(active_listings.data) > len(deals_current.data) * 2:
                recommendations.append({
                    "category": "Listing Efficiency",
                    "priority": "Medium", 
                    "issue": "High listing-to-deal ratio suggests marketing inefficiency",
                    "recommendation": "Improve listing marketing and pricing strategy",
                    "action_items": ["Review pricing strategies", "Enhance listing presentations", "Increase listing promotion"]
                })
        
        # Focus area specific analysis
        focus_insights = None
        if focus_area:
            if focus_area == "revenue":
                focus_insights = {
                    "top_revenue_sources": "Analysis of highest-value deals and client types",
                    "revenue_trends": "Monthly revenue patterns and seasonality",
                    "commission_analysis": "Average commission per deal type"
                }
            elif focus_area == "efficiency":
                focus_insights = {
                    "time_per_deal": "Average time investment per deal stage", 
                    "productivity_metrics": "Deals per week/month ratios",
                    "automation_opportunities": "Repetitive tasks that can be automated"
                }
        
        return json.dumps({
            "success": True,
            "analytics_data": analytics_data,
            "recommendations": recommendations,
            "focus_area_insights": focus_insights,
            "performance_summary": {
                "overall_trend": "Positive" if revenue_growth > 0 else "Negative" if revenue_growth < -5 else "Stable",
                "key_strength": "Revenue growth" if revenue_growth > 10 else "Pipeline management" if len(pipeline_deals) > 10 else "Lead generation",
                "primary_opportunity": recommendations[0]["category"] if recommendations else "Continue current performance"
            },
            "next_steps": [
                "Review detailed recommendations",
                "Implement highest priority action items", 
                "Set goals for next period",
                "Track progress weekly"
            ]
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to generate business analytics: {str(e)}",
            "suggestion": "Ensure sufficient data exists in CRM for meaningful analysis"
        })

@tool
def get_broker_documents(
    document_type: Optional[str] = None,
    limit: int = 20
) -> str:
    """
    Get list of general broker documents (contracts, LOIs, lease agreements, etc.).
    
    Args:
        document_type: Filter by type (contract, loi, lease, legal, business_plan, etc.)
        limit: Maximum number of documents to return (default 20)
    
    Returns:
        JSON string with broker document information
    """
    try:
        supabase = get_supabase_client()
        query = supabase.table("broker_documents").select("*")
        
        if document_type:
            query = query.eq("document_type", document_type)
            
        result = query.limit(limit).order("uploaded_at", desc=True).execute()
        
        return json.dumps({
            "success": True,
            "documents": result.data,
            "count": len(result.data)
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get broker documents: {str(e)}"
        })

@tool
def search_broker_documents(
    query: str,
    document_type: Optional[str] = None,
    match_threshold: float = 0.7,
    limit: int = 5
) -> str:
    """
    Search through broker's general documents using semantic search.
    
    Args:
        query: Search query text (e.g. "termination clause", "payment terms", "renewal options")
        document_type: Filter by document type (contract, loi, lease, etc.)
        match_threshold: Similarity threshold (0.0-1.0, default 0.7)
        limit: Maximum number of results (default 5)
    
    Returns:
        JSON string with matching document chunks and sources
    """
    try:
        supabase = get_supabase_client()
        
        # Check if broker has documents
        doc_check = supabase.table("broker_documents").select("id, filename, document_type")
        if document_type:
            doc_check = doc_check.eq("document_type", document_type)
        doc_check = doc_check.execute()
        
        if not doc_check.data:
            return json.dumps({
                "success": True,
                "message": f"No {'broker' if not document_type else document_type} documents found. Upload documents first to enable search.",
                "results": [],
                "count": 0,
                "suggestion": "Upload broker documents (contracts, LOIs, leases) to search through them"
            })
        
        query_embedding = get_embedding(query)
        
        # Use a new broker document search function (you'll need to create this)
        result = supabase.rpc(
            'match_broker_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': match_threshold,
                'document_type_filter': document_type,
                'match_count': limit
            }
        ).execute()
        
        if not result.data:
            return json.dumps({
                "success": True,
                "message": f"No relevant content found for '{query}' in broker documents.",
                "results": [],
                "count": 0,
                "available_documents": [{"filename": doc["filename"], "type": doc["document_type"]} for doc in doc_check.data],
                "suggestion": f"Try different search terms or browse the {len(doc_check.data)} available documents directly"
            })
        
        formatted_results = []
        for row in result.data:
            doc_result = supabase.table("broker_documents").select("filename, document_type").eq("id", row.get("document_id", "")).execute()
            doc_info = doc_result.data[0] if doc_result.data else {}
            
            formatted_results.append({
                "chunk_text": row["chunk_text"],
                "similarity": round(row["similarity"], 3),
                "source_document": doc_info.get("filename", "Unknown document"),
                "document_type": doc_info.get("document_type", "Unknown type"),
                "metadata": row.get("metadata", {})
            })
        
        return json.dumps({
            "success": True,
            "results": formatted_results,
            "count": len(formatted_results),
            "query": query,
            "message": f"Found {len(formatted_results)} relevant sections for '{query}'"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Unable to search broker documents: {str(e)}",
            "suggestion": "Check that documents have been processed for search"
        })

@tool 
def search_listing_documents(
    listing_id: str,
    query: str,
    match_threshold: float = 0.7,
    limit: int = 5,
) -> str:
    """
    Search through listing documents using semantic search.

    Args: 
        listing_id: ID of the listing to search documents for
        query: Search query text (e.g. 'renewal terms', 'square footage', 'amenities', 'cap rat', etc.)
        match_threshold: Similarity threshold (0.0-1.0, default 0.7)
        limit: Maximum number of documents to return (default 5)

    Returns:
        JSON string with matching document chunks and sources results
    """
    try:
        supabase = get_supabase_client()
        doc_check = supabase.table("listing_documents").select("id, filename").eq("listing_id", listing_id).execute()
        
        if not doc_check.data:
            return_json = json.dumps({
                "success": True,
                "message": f"No documents found for listing {listing_id}",
                "results": [],
                "count": 0,
                "suggestion": "Upload listing documents (leases, appraisals, financial reports) to search through them."
            })
            
        query_embedding = get_embedding(query)

        result = supabase.rpc(
            'match_documents',
            {
                "query_embedding": query_embedding,
                "match_threshold": match_threshold,
                "match_count": limit,
                "listing_id": listing_id,
            }
        ).execute()

        if not result.data:
            return_json = json.dumps({
                "success": True,
                "message": f"No relevant content for '{query}' in listing documents. Try different search terms or check if documents contain this information.",
                "results": [],
                "count": 0,
                "available_documents": [doc["filename"] for doc in doc_check.data],
                "suggestion": f"Try searching for related terms or browse the {len(doc_check.data)} available documents in your listing."
            })
        
        formatted_results = []
        for row in result.data:
            doc_result = supabase.table("listing_documents").select("filename, document_type").eq("id", row.get("document_id", "")).execute()
            doc_info = doc_result.data[0] if doc_result.data else {}

            formatted_results.append({
                "chunk_text": row["chunk_text"],
                "similarity": round(row["similarity"], 3),
                "chunk_type": row.get("chunk_type"),
                "source_document": doc_info.get("filename", "Unknown document"),
                "metadate": row.get("metadata", {}),
            })

            return_json = json.dumps({
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "query": query,
                "listing_id": listing_id,
                "message": f"Found {len(formatted_results)} relevant sections for '{query}' in listing documents.",
            }, default=str)

    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Unable to search listing documents: {str(e)}",
            "query": query,
            "listing_id": listing_id,
            "suggestion": "Check that the listing ID is correct and documents have processed for search."
        })

@tool
def get_listing_documents(listing_id: str) -> str:
    """
    Get list of documents uploaded for a specific listing.

    Args:
        listing_id: ID of the listing to get documents for

    Returns:
        JSON string with document information
    """
    try:
        supabase = get_supabase_client()
        result = supabase.table("listing_documents").select("*").eq("listing_id", listing_id).execute()
        
        return_json = json.dumps({
            "success": True,
            "documents": result.data,
            "count": len(result.data),
        }, default=str)
    except Exception as e:
        return json.dumps({
            "succes": False,
            "error": f"Failed to get listing documents: {str(e)}"
        })

@tool
def get_daily_summary() -> str:
    """
    Get daily summary of key CRM metrics and activities.

    Returns:
        JSON string with daily summary data.
    """
    try:
        supabase = get_supabase_client()
        today = datetime.now().date()

        new_contacts = supabase.table("contacts").select("*").gte("created_at", today.isoformat()).execute()

        week_end = today + timedelta(days=7)
        closing_deals = supabase.table("deals").select("*").gte("expected_close", week_end.isoformat()).lte("expected_close", today.isoformat()).execute()
        
        pending_inquiries = supabase.table("listing_inquiries").select("*").eq("status", "pending").execute()
        
        active_listings = supabase.table("listings").select("*").eq("status", "ACTIVE").execute()

        summary = {
            "date": today.isoformat(),
            "new_contacts_today": len(new_contacts.data),
            "deals_closing_this_week": len(closing_deals.data),
            "pending_inquiries": len(pending_inquiries.data),
            "active_listings": len(active_listings.data),
            "recent_contacts": new_contacts.data,
        }

        return_json = json.dumps({
            "success": True,
            "summary": summary,
        }, default=str)
    except Exception as e:
        return_json = json.dumps({
            "success": False,
            "error": f"Failed to get daily summary: {str(e)}"
        })
        
#OM/BOV Creation Tools

@tool
def analyze_listing_documents(listing_id: str) -> str:
    """
    Analyze uploaded listing documents to extract key information for OM/BOV creation.

    Args:
        listing_id: ID of the listing to analyze
        analysis_focus: Type of analysis ("financial", "legal", "physical", "comprehensive")

    Returns:
        JSON string with extracted listing insights and data points
    """
    try:
        supabase = get_supabase_client()

        listing_result = supabase.table("listings").select("*").eq("id", listing_id).execute()
        if not listing_result.data:
            return_json = json.dumps({
                "success": False,
                "error": "Check the lisitng ID and try again": {listing_id}"
            })

        listing_info = listing_result.data[0]

        docs_result = supabase.table("listing_documents").select("*").eq("listing_id", listing_id).execute()

        if not docs_result.data:
            return_json = json.dumps({
                "success": True,
                "meesage": "No documents found to analyze. UPload documents first.",
                "listing_title": listing_info.get("title"),
                "suggestion": "Uplodad lease agreements, LOIs, financials, surveys, or appraisals to enable analysis."
            })

        analysis_queries ={
            "financial": [
                "rental income", "NOI", "cap rate", "operating expense",
                "rent roll", "vacancy rate","gross income"
            ],
            "legal":[
                "lease terms", "tenant rights", "renewal option", "assignment clauses",
                "use restrictions", "compliance requirements"
            ],
            "physical":[
                "square footage", "building condition", "parking", "zoning",
                "improvements", "maitenance", "utilities", "amenities"
            ],
            "comprehensive": [
                "rental income", "NOI", "cap rate", "lease terms", "square footage",
                "building condition", "parking", "zoning", "tenant information"
            ]
        }

        search_terms = analysis_queries.get(analysis_focus, analysis_queries["comprehensive"])
        extracted_data = []

        for term in search_terms:
            try:
                query_embedding = get_embedding(term)
                result = supabase.rpc(
                    'match_documents',
                    {
                        "query_embedding": query_embedding,
                        "match_threshold": 0.5,
                        "match_count": 3,
                        "listing_id": listing_id,
                    }
                ).execute()

                if result.data:
                    extracted_data[term] = {
                        "found": True,
                        "content": result.data[0]["chunk_text"][:300] +"... ",
                        "source": result.data[0].get("source_document", "Unknown"),
                        "confidence": result.data[0].get["similarity"]
                    }
                      else:
                    extracted_data[term] = {"found": False}
                    
            except Exception as e:
                extracted_data[term] = {"found": False, "error": str(e)}
        
        return json.dumps({
            "success": True,
            "property_id": listing_id,
            "property_title": listing_info.get("title"),
            "analysis_focus": analysis_focus,
            "documents_analyzed": len(docs_result.data),
            "extracted_data": extracted_data,
            "document_list": [doc["filename"] for doc in docs_result.data],
            "message": f"Analyzed {len(docs_result.data)} documents for {analysis_focus} information"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to analyze listing documents: {str(e)}",
            "suggestion": "Ensure documents are uploaded and processed correctly"
        })

@tool 
def research_market_data(address: str, listing_type: str, square_footage: int = None) -> str:
    """ 
    Research market trends and comparable data for OM/BOV market analysis section. 

    Args:
        address: Property address for location-based research
        listing_type: Type of listing (e.g. 'office', 'retail', 'industrial', 'multifamily', 'mixed-use', 'warehouse', 'land', 'other')
        square_footage: Property square footage for comparable analysis

    Returns:
        JSON string with market research data and trends
    """
    try:
        market_data = {
            "location_analysis": {
                "submarket": "To be determinded via market data API",
                "demographics": "Populationa and economic data needed",
                "accessibility": "Transportation and access analysis",
                "competition": "Competitive properties in area"
            },
            "comparable_sales": {
                "recent_sales": "Recent comparable transactions",
                "price_per_sf": "Market rate per square foot",
                "cap_rate": "Current market cap rates",
                "absorption_rates": "Market absorption trends"
            },
            "market_trends": {
                "vacancy_rates": "Current market and submarket vacancy rates",
                "rental_rates": "Market rental rates",
                "future_outlook": "Market projections",
                "development_pipeline": "upcoming developments"
            }
        }

        return json.dumps({
            "success": True,
            "address": address,
            "listing_type": listing_type,
            "square_footage": square_footage,
            "market_data": market_data,
            "note": "Market data integration with external APIs (LoopNet, Costar, etc.) needed for live data.",
            "suggestion": "Connect market data APIs for real-time comparable and trend analysis."
        }, default=str)
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to research market data: {str(e)}",
            "suggestion": "Market data API integration required for comprehensive analysis."
        })

@tool
def generate_om_content(listing_id: str, content_section: str) -> str:
            
    """
    Generate professional content for Offering Memorandum sections.

    Args:
        listing_id: UUID of the listing
        content_section: Section to generate ("executive summary", "property_overview",
        "financial_analysis", "market_analysis", "investment_highlights")
        style: Writing style ("professional", "compelling", "data_focused")

    Returns:
        JSON stirng with generated content for the specified OM section.
    """
    try:
        supabase = get_supabase_client()

        listing_result = supabase.table("listings").select("*").eq("id", listing_id).execute()
        if not listing_result.data:
            return_json = json.dumps({
                "success": False,
                "error": "Listing not found for content generation": {listing_id}"
            })

        listing_info = listing_result.data[0]

        broker_result = supabase.table("broker_settings").select("*").execute()
        broker_info = broker_result.data[0] if broker_result.data else {}

        content_templates = {
            "executive_summary": f"""
EXECUTIVE SUMMARY

{listing_info.get("title", "Listing")} presents an exceptional {listing_info.get("listing_type", "commercial")} 
investment opportunity located at {listing_info.get("address", "prime location")}.

This {listing_info.get('square_footage', 'XX,XXX')} square foot property offers investors:
- Stable cash flow from established tenant base
- Strategic location with excellent accessibility
- Value-add potential through operational improvements
-  Current asking price: ${listing_info.get("asking_price", "XX,XXX"):,}

[Additonal details would from document analysis]
            """,

            "listing_overview": f"""
LISTING OVERVIEW

Address: {listing_info.get("address", "TBD")}
Listing Type: {listing_info.get("listing_type", "Commercial").title()}
Total Square Footage: {listing_info.get('square_footage', 'XX,XXX'):,} SF
Asking Price: ${listing_info.get('asking_price', 'XX,XXX,XXX'):,}
Price per SF: ${(listing_info.get('asking_price', 0) / max(listing_info.get('square_footage', 1), 1)):.2f}

BUILDING DETAILS
[Details to be populated from document analysis]
• Construction year and building specifications
• Parking ratios and accessibility features  
• Recent improvements and building condition
• Zoning and permitted uses
            """,
            
            "investment_highlights": f"""
INVESTMENT HIGHLIGHTS

✓ PRIME LOCATION: Strategic positioning in established commercial corridor
✓ STABLE INCOME: Long-term lease agreements with creditworthy tenants
✓ VALUE CREATION: Opportunity for rental growth and operational efficiency
✓ MARKET DYNAMICS: Strong fundamentals in {listing_info.get('property_type', 'commercial')} sector

[Specific highlights would be generated from property analysis and market research]
            """
        }
        
        generated_content = content_templates.get(content_section, "Content section not found")
        
        return json.dumps({
            "success": True,
            "listing_id": listing_id,
            "content_section": content_section,
            "style": style,
            "generated_content": generated_content,
            "word_count": len(generated_content.split()),
            "note": "Content generated from available property data. Enhance with document analysis results.",
            "next_steps": "Use analyze_property_documents() to extract specific details for more comprehensive content"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to generate OM content: {str(e)}"
        })

@tool 
def review_om_quality(content: str, review_type: str = "comprehensive") -> str:
    """
    Review and provide quality feedback on OM/BOV content for improvements.
    
    Args:
        content: The OM content to review
        review_type: Type of review ("grammar", "completeness", "persuasiveness", "comprehensive")
    
    Returns:
        JSON string with quality assessment and improvement suggestions
    """
    try:
        content_length = len(content)
        word_count = len(content.split())
        
        quality_score = 0
        feedback = []
        
        if word_count < 100:
            feedback.append("Content appears too brief for professional OM. Consider expanding key sections.")
        elif word_count > 200:
            quality_score += 20
            feedback.append("Good content length for executive summary section.")
        
        financial_indicators = ["$", "NOI", "cap rate", "rental", "income", "expense"]
        financial_mentions = sum(1 for indicator in financial_indicators if indicator.lower() in content.lower())
        if financial_mentions >= 3:
            quality_score += 25
            feedback.append("Strong financial data inclusion.")
        else:
            feedback.append("Consider adding more financial metrics and data points.")
        
        professional_terms = ["investment", "opportunity", "strategic", "positioned", "market", "potential"]
        professional_score = sum(1 for term in professional_terms if term.lower() in content.lower())
        if professional_score >= 4:
            quality_score += 20
            feedback.append("Professional investment language used effectively.")
        
        suggestions = []
        if "square foot" not in content.lower():
            suggestions.append("Add specific square footage details")
        if not any(char.isdigit() for char in content):
            suggestions.append("Include specific numerical data (prices, sizes, dates)")
        if "location" not in content.lower():
            suggestions.append("Emphasize location benefits and accessibility")
        
        quality_score += min(30, len(content.split()) // 10)
        
        return json.dumps({
            "success": True,
            "review_type": review_type,
            "quality_score": min(quality_score, 100),
            "word_count": word_count,
            "character_count": content_length,
            "strengths": feedback,
            "improvement_suggestions": suggestions,
            "overall_assessment": "Professional" if quality_score >= 70 else "Needs Enhancement" if quality_score >= 50 else "Requires Significant Improvement",
            "next_steps": "Implement suggested improvements and ensure all key property details are included"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to review content quality: {str(e)}"
        })

@tool
def get_calendar_events(
    days_ahead: int = 7,
    event_type: Optional[str] = None,
    include_past: bool = False
) -> str:
    """
    Get calendar events and schedule for the broker.
    
    Args:
        days_ahead: Number of days to look ahead (default 7)
        event_type: Filter by event type (meeting, showing, closing, etc.)
        include_past: Whether to include past events from today
    
    Returns:
        JSON string with calendar events and schedule information
    """
    try:
        # This would integrate with Google Calendar API or broker's calendar system
        # For now, providing structure for calendar integration
        
        from datetime import datetime, timedelta
        
        today = datetime.now()
        end_date = today + timedelta(days=days_ahead)
        start_date = today if not include_past else today - timedelta(days=1)
        
        # Simulated calendar events for framework
        sample_events = [
            {
                "id": "cal_event_1",
                "title": "Property Showing - 123 Main St",
                "start_time": (today + timedelta(days=1, hours=2)).isoformat(),
                "end_time": (today + timedelta(days=1, hours=3)).isoformat(),
                "event_type": "showing",
                "location": "123 Main St, City, State",
                "attendees": ["john.investor@email.com"],
                "description": "Office building tour with potential investor",
                "priority": "high"
            },
            {
                "id": "cal_event_2", 
                "title": "Closing - ABC Corp Deal",
                "start_time": (today + timedelta(days=3, hours=4)).isoformat(),
                "end_time": (today + timedelta(days=3, hours=6)).isoformat(),
                "event_type": "closing",
                "location": "Title Company Office",
                "attendees": ["abc.corp@email.com", "attorney@law.com"],
                "description": "$2.5M office building closing",
                "priority": "critical"
            },
            {
                "id": "cal_event_3",
                "title": "Client Meeting - Metro Investment",
                "start_time": (today + timedelta(days=5, hours=1)).isoformat(),
                "end_time": (today + timedelta(days=5, hours=2)).isoformat(),
                "event_type": "meeting",
                "location": "Coffee Shop Downtown",
                "attendees": ["metro.invest@email.com"],
                "description": "Discuss new investment opportunities",
                "priority": "medium"
            }
        ]
        
        # Filter by event type if specified
        if event_type:
            filtered_events = [e for e in sample_events if e["event_type"] == event_type]
        else:
            filtered_events = sample_events
        
        # Sort by start time
        filtered_events.sort(key=lambda x: x["start_time"])
        
        return json.dumps({
            "success": True,
            "date_range": f"{start_date.date()} to {end_date.date()}",
            "days_ahead": days_ahead,
            "event_type_filter": event_type,
            "total_events": len(filtered_events),
            "events": filtered_events,
            "upcoming_critical": [e for e in filtered_events if e["priority"] == "critical"],
            "this_week_summary": f"{len(filtered_events)} events scheduled",
            "integration_needed": "Google Calendar API or similar calendar service integration required for live data"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get calendar events: {str(e)}",
            "suggestion": "Calendar integration (Google Calendar API) required for live schedule data"
        })

@tool
def get_tasks(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due_within_days: Optional[int] = None,
    limit: int = 20
) -> str:
    """
    Get tasks and to-dos for the broker.
    
    Args:
        status: Filter by status ('pending', 'in_progress', 'completed', 'overdue')
        priority: Filter by priority ('low', 'medium', 'high', 'critical')
        due_within_days: Show tasks due within X days
        limit: Maximum number of tasks to return (default 20)
    
    Returns:
        JSON string with task information
    """
    try:
        # This would integrate with your task management system or CRM tasks
        # For now, providing structure based on likely task table schema
        
        from datetime import datetime, timedelta
        
        today = datetime.now()
        
        # Simulated task data for framework
        sample_tasks = [
            {
                "id": "task_1",
                "title": "Follow up with ABC Corp on lease renewal",
                "description": "Lease expires in 60 days, need to discuss renewal terms",
                "status": "pending",
                "priority": "high",
                "due_date": (today + timedelta(days=3)).isoformat(),
                "created_date": (today - timedelta(days=5)).isoformat(),
                "assigned_to": "broker",
                "related_contact": "ABC Corp",
                "related_property": "123 Office Building",
                "task_type": "follow_up",
                "estimated_time": "30 minutes"
            },
            {
                "id": "task_2",
                "title": "Prepare OM for downtown retail property",
                "description": "Create offering memorandum for 456 Retail Plaza listing",
                "status": "in_progress", 
                "priority": "medium",
                "due_date": (today + timedelta(days=7)).isoformat(),
                "created_date": (today - timedelta(days=2)).isoformat(),
                "assigned_to": "broker",
                "related_contact": None,
                "related_property": "456 Retail Plaza",
                "task_type": "marketing",
                "estimated_time": "2 hours"
            },
            {
                "id": "task_3",
                "title": "Schedule property inspection for warehouse deal",
                "description": "Coordinate inspection with buyer's team for industrial property",
                "status": "pending",
                "priority": "critical",
                "due_date": (today + timedelta(days=1)).isoformat(),
                "created_date": today.isoformat(),
                "assigned_to": "broker",
                "related_contact": "Industrial Investors LLC",
                "related_property": "789 Warehouse Complex",
                "task_type": "coordination",
                "estimated_time": "45 minutes"
            },
            {
                "id": "task_4",
                "title": "Update CRM with new investor contacts",
                "description": "Add contacts from networking event to CRM system",
                "status": "pending",
                "priority": "low",
                "due_date": (today + timedelta(days=14)).isoformat(),
                "created_date": (today - timedelta(days=1)).isoformat(),
                "assigned_to": "broker",
                "related_contact": None,
                "related_property": None,
                "task_type": "admin",
                "estimated_time": "1 hour"
            }
        ]
        
        # Apply filters
        filtered_tasks = sample_tasks
        
        if status:
            filtered_tasks = [t for t in filtered_tasks if t["status"] == status]
            
        if priority:
            filtered_tasks = [t for t in filtered_tasks if t["priority"] == priority]
            
        if due_within_days:
            cutoff_date = today + timedelta(days=due_within_days)
            filtered_tasks = [t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) <= cutoff_date]
        
        # Sort by due date and priority
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        filtered_tasks.sort(key=lambda x: (datetime.fromisoformat(x["due_date"]), -priority_order.get(x["priority"], 0)))
        
        # Limit results
        filtered_tasks = filtered_tasks[:limit]
        
        # Calculate task statistics
        overdue_tasks = [t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) < today and t["status"] != "completed"]
        high_priority_tasks = [t for t in filtered_tasks if t["priority"] in ["high", "critical"]]
        
        return json.dumps({
            "success": True,
            "total_tasks": len(filtered_tasks),
            "filters_applied": {
                "status": status,
                "priority": priority,
                "due_within_days": due_within_days
            },
            "tasks": filtered_tasks,
            "task_summary": {
                "overdue_count": len(overdue_tasks),
                "high_priority_count": len(high_priority_tasks),
                "due_today": len([t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]).date() == today.date()]),
                "due_this_week": len([t for t in filtered_tasks if datetime.fromisoformat(t["due_date"]) <= today + timedelta(days=7)])
            },
            "integration_needed": "Task management system integration required for live task data"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get tasks: {str(e)}",
            "suggestion": "Task management system integration required"
        })

# Enhanced OM/BOV generation tool to handle both document types
@tool
def generate_om_content(
    listing_id: str, 
    content_section: str, 
    document_type: str = "OM",
    style: str = "professional"
) -> str:
    """
    Generate professional content for Offering Memorandum (OM) or Broker Opinion of Value (BOV) sections.
    
    Args:
        listing_id: UUID of the listing
        content_section: Section to generate ("executive_summary", "property_overview", 
                        "financial_analysis", "market_analysis", "investment_highlights", "valuation_summary")
        document_type: Type of document ("OM", "BOV")
        style: Writing style ("professional", "compelling", "data_focused")
    
    Returns:
        JSON string with generated content for the specified section
    """
    try:
        supabase = get_supabase_client()
        
        listing_result = supabase.table("listings").select("*").eq("id", listing_id).execute()
        if not listing_result.data:
            return json.dumps({
                "success": False,
                "error": "Property not found for content generation"
            })
        
        listing_info = listing_result.data[0]
        broker_result = supabase.table("broker_settings").select("*").execute()
        broker_info = broker_result.data[0] if broker_result.data else {}
        
        # BOV-specific content templates
        if document_type.upper() == "BOV":
            content_templates = {
                "executive_summary": f"""
BROKER OPINION OF VALUE - EXECUTIVE SUMMARY

Property: {listing_info.get('title', 'Subject Property')}
Address: {listing_info.get('address', 'TBD')}
Prepared by: {broker_info.get('agent_name', 'Licensed Broker')}
Date: {datetime.now().strftime('%B %d, %Y')}

VALUATION CONCLUSION: ${listing_info.get('asking_price', 'TBD'):,}

This Broker Opinion of Value provides a comprehensive analysis of {listing_info.get('title', 'the subject property')} 
based on market research, financial performance, and comparable sales analysis.

KEY VALUATION FACTORS:
• Income approach analysis based on current NOI and market cap rates
• Sales comparison approach using recent comparable transactions
• Physical condition and location premium/discount analysis
• Market timing and liquidity considerations

[Detailed analysis would be populated from property document analysis and market research]
                """,
                
                "valuation_summary": f"""
VALUATION SUMMARY

Property Type: {listing_info.get('property_type', 'Commercial').title()}
Square Footage: {listing_info.get('square_footage', 'XX,XXX'):,} SF
Current Asking Price: ${listing_info.get('asking_price', 'XX,XXX,XXX'):,}

VALUATION APPROACHES:

Income Approach:
• Estimated NOI: [To be determined from financial analysis]
• Market Cap Rate: [To be determined from market research]  
• Indicated Value: [Calculated value]

Sales Comparison Approach:
• Recent comparable sales analysis
• Adjusted price per square foot: [To be determined]
• Indicated Value: [Calculated value]

Cost Approach:
• Land value: [To be assessed]
• Replacement cost new: [To be calculated]
• Less depreciation: [To be estimated]
• Indicated Value: [Calculated value]

FINAL VALUE CONCLUSION: ${listing_info.get('asking_price', 'TBD'):,}
Confidence Level: [To be determined based on data quality]

[Detailed methodology and supporting data would be included]
                """,
                
                "market_analysis": f"""
MARKET ANALYSIS FOR VALUATION

Submarket: [Location analysis required]
Property Type: {listing_info.get('property_type', 'Commercial')}
Analysis Date: {datetime.now().strftime('%B %Y')}

COMPARABLE SALES ANALYSIS:
[Recent transactions within 1 mile and similar property characteristics]

RENTAL MARKET ANALYSIS:
[Current market rents for similar properties]

CAP RATE ANALYSIS:
[Market cap rates by property type and location]

MARKET CONDITIONS IMPACT:
• Supply and demand factors
• Economic conditions affecting value
• Future market outlook
• Liquidity and marketing time considerations

[Market research data would be populated from research_market_data tool]
                """
            }
        else:  # OM content templates (existing)
            content_templates = {
                "executive_summary": f"""
EXECUTIVE SUMMARY

{listing_info.get('title', 'Property')} presents an exceptional {listing_info.get('property_type', 'commercial')} 
investment opportunity located at {listing_info.get('address', 'prime location')}. 

This {listing_info.get('square_footage', 'XX,XXX')} square foot property offers investors:
• Stable cash flow from established tenant base
• Strategic location with excellent accessibility  
• Value-add potential through operational improvements
• Current asking price: ${listing_info.get('asking_price', 'XX,XXX,XXX'):,}

[Additional details would be populated from document analysis]
                """,
                
                "property_overview": f"""
PROPERTY OVERVIEW

Address: {listing_info.get('address', 'TBD')}
Property Type: {listing_info.get('property_type', 'Commercial').title()}
Total Square Footage: {listing_info.get('square_footage', 'XX,XXX'):,} SF
Asking Price: ${listing_info.get('asking_price', 'XX,XXX,XXX'):,}
Price per SF: ${(listing_info.get('asking_price', 0) / max(listing_info.get('square_footage', 1), 1)):.2f}

BUILDING DETAILS
[Details to be populated from document analysis]
• Construction year and building specifications
• Parking ratios and accessibility features  
• Recent improvements and building condition
• Zoning and permitted uses
                """,
                
                "investment_highlights": f"""
INVESTMENT HIGHLIGHTS

✓ PRIME LOCATION: Strategic positioning in established commercial corridor
✓ STABLE INCOME: Long-term lease agreements with creditworthy tenants
✓ VALUE CREATION: Opportunity for rental growth and operational efficiency
✓ MARKET DYNAMICS: Strong fundamentals in {listing_info.get('property_type', 'commercial')} sector

[Specific highlights would be generated from property analysis and market research]
                """
            }
        
        generated_content = content_templates.get(content_section, f"Content section '{content_section}' not available for {document_type}")
        
        return json.dumps({
            "success": True,
            "listing_id": listing_id,
            "document_type": document_type,
            "content_section": content_section,
            "style": style,
            "generated_content": generated_content,
            "word_count": len(generated_content.split()),
            "note": f"{document_type} content generated from available property data. Enhance with document analysis and market research.",
            "next_steps": f"Use analyze_property_documents() and research_market_data() for comprehensive {document_type} content"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to generate {document_type} content: {str(e)}"
        })

# Enhanced review tool to handle both OM and BOV quality assessment
@tool 
def review_om_quality(
    content: str, 
    document_type: str = "OM",
    review_type: str = "comprehensive"
) -> str:
    """
    Review and provide quality feedback on OM/BOV content for improvements.
    
    Args:
        content: The OM or BOV content to review
        document_type: Type of document ("OM", "BOV")
        review_type: Type of review ("grammar", "completeness", "persuasiveness", "comprehensive")
    
    Returns:
        JSON string with quality assessment and improvement suggestions
    """
    try:
        content_length = len(content)
        word_count = len(content.split())
        
        quality_score = 0
        feedback = []
        suggestions = []
        
        # Document type specific criteria
        if document_type.upper() == "BOV":
            # BOV-specific quality checks
            valuation_terms = ["cap rate", "NOI", "market value", "comparable", "valuation", "approach"]
            valuation_score = sum(1 for term in valuation_terms if term.lower() in content.lower())
            
            if valuation_score >= 4:
                quality_score += 30
                feedback.append("Strong valuation methodology and terminology used.")
            else:
                suggestions.append("Include more valuation-specific terms and methodology")
                
            # Check for required BOV sections
            required_sections = ["income approach", "sales comparison", "market analysis"]
            section_mentions = sum(1 for section in required_sections if section.lower() in content.lower())
            
            if section_mentions >= 2:
                quality_score += 25
                feedback.append("Multiple valuation approaches referenced.")
            else:
                suggestions.append("Include references to income approach, sales comparison, and market analysis")
                
        else:  # OM-specific checks
            # Investment language check
            investment_terms = ["investment", "opportunity", "cash flow", "returns", "strategic"]
            investment_score = sum(1 for term in investment_terms if term.lower() in content.lower())
            
            if investment_score >= 4:
                quality_score += 25
                feedback.append("Strong investment language and positioning.")
            else:
                suggestions.append("Enhance investment appeal with stronger positioning language")
        
        # Common quality checks for both document types
        if word_count < 100:
            feedback.append(f"Content appears too brief for professional {document_type}. Consider expanding key sections.")
        elif word_count > 200:
            quality_score += 20
            feedback.append(f"Good content length for {document_type} section.")
        
        # Financial data inclusion
        financial_indicators = ["$", "NOI", "cap rate", "rental", "income", "expense", "price"]
        financial_mentions = sum(1 for indicator in financial_indicators if indicator.lower() in content.lower())
        if financial_mentions >= 3:
            quality_score += 25
            feedback.append("Strong financial data inclusion.")
        else:
            suggestions.append("Add more specific financial metrics and data points")
        
        # Professional presentation
        if not any(char.isdigit() for char in content):
            suggestions.append("Include specific numerical data (prices, sizes, dates)")
        if "location" not in content.lower():
            suggestions.append("Emphasize location benefits and accessibility")
            
        quality_score += min(20, len(content.split()) // 10)
        
        # Document-specific improvement suggestions
        if document_type.upper() == "BOV":
            suggestions.extend([
                "Include confidence level in valuation conclusion",
                "Add market conditions disclaimer",
                "Reference data sources and methodology"
            ])
        else:
            suggestions.extend([
                "Highlight unique value propositions",
                "Include call-to-action for interested investors",
                "Add broker contact information"
            ])
        
        return json.dumps({
            "success": True,
            "document_type": document_type,
            "review_type": review_type,
            "quality_score": min(quality_score, 100),
            "word_count": word_count,
            "character_count": content_length,
            "strengths": feedback,
            "improvement_suggestions": suggestions[:8],  # Limit suggestions
            "overall_assessment": (
                "Professional" if quality_score >= 70 
                else "Needs Enhancement" if quality_score >= 50 
                else "Requires Significant Improvement"
            ),
            "document_specific_notes": f"{document_type} requirements {'met' if quality_score >= 60 else 'need attention'}",
            "next_steps": f"Implement suggested improvements for {document_type} standards"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to review {document_type} content quality: {str(e)}"
        })

# Updated CRM Tools List with new additions
CRM_TOOLS = [
    get_broker_profile,
    get_broker_documents,
    search_broker_documents,
    get_business_analytics,
    get_contacts,
    get_deals,
    get_listings,
    get_recent_inquiries,
    get_campaigns_performance,
    search_listing_documents,
    get_listing_documents,
    get_daily_summary,
    generate_om_content,
    review_om_quality,
    # New productivity tools
    get_calendar_events,
    get_tasks,
    # Enhanced OM/BOV creation tools
    analyze_listing_documents,
    research_market_data,
    generate_om_content,  # Now handles both OM and BOV
    review_om_quality     # Now handles both OM and BOV quality review
]
        