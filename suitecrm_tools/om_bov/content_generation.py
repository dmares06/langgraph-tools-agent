"""Content generation for OM/BOV documents."""

import json
from datetime import datetime
from langchain_core.tools import tool
from ..utils import get_supabase_client

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
        else:  # OM content templates
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
            "next_steps": f"Use analyze_listing_documents() and research_market_data() for comprehensive {document_type} content"
        }, default=str)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to generate {document_type} content: {str(e)}"
        })