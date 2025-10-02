"""Business analytics and performance insights."""

import json
from typing import Optional
from datetime import datetime, timedelta
from langchain_core.tools import tool
from ..utils import get_supabase_client

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