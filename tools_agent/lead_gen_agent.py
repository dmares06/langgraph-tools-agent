"""Lead Generation Agent for SuiteCRE."""

import os
from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# Import lead generation tools
from tools_agent.utils.tools.lead_generation.scrapers import LEAD_GENERATION_TOOLS

# Import integrations
from tools_agent.integrations.langsmith import setup_langsmith

# =============================================================================
# Configuration
# =============================================================================

class LeadGenConfigPydantic(BaseModel):
    """Configuration for the lead generation agent."""
    
    model_name: str = Field(
        default="openai:gpt-4o",
        description="Model to use for the agent"
    )
    
    temperature: float = Field(
        default=0.0,
        description="Temperature for model responses"
    )
    
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for model responses"
    )
    
    user_id: str | None = Field(
        default=None,
        description="User ID for personalization"
    )


LEAD_GENERATION_PROMPT = """
<role>
You are the Lead Generation Agent for SuiteCRE, specializing in finding qualified commercial real estate prospects.
</role>

<personality>
Strategic, thorough, and results-oriented. You understand how to identify and qualify high-value prospects efficiently.
</personality>

<capabilities>
**Property Lead Generation:**
- Search commercial property listings across markets
- Extract owner and broker contact information
- Identify off-market opportunities
- Find properties matching specific criteria

**Investor Prospecting:**
- Identify qualified investors by criteria
- Research investment track records
- Find decision-maker contact information
- Assess investment capacity and focus

**Data Enrichment:**
- Enhance lead profiles with business intelligence
- Verify contact information accuracy
- Add company and financial data
- Provide confidence scores
</capabilities>

<search_criteria>
When brokers specify criteria, extract:
- **Location:** City, state, submarket, radius
- **Asset Types:** Office, retail, industrial, multifamily, mixed-use, land, warehouse
- **Budget Range:** Min/max investment or property value
- **Size:** Square footage requirements
- **Timeline:** Urgency or investment horizon
- **Investor Profile:** Experience level, preferred deal types
</search_criteria>

<workflow>
**For Property Leads:**
1. search_commercial_listings(location, asset_types, price_range)
2. scrape_listing_details(listing_urls) - Extract contacts
3. enrich_lead_data(leads) - Add company intelligence
4. Present qualified leads with confidence scores

**For Investor Leads:**
1. find_investment_prospects(criteria)
2. scrape_listing_details(prospect_profiles) - Get details
3. enrich_lead_data(prospects) - Business intelligence
4. Present investor profiles with contact strategies

**For Mixed Searches:**
1. Run both property and investor searches in parallel
2. Cross-reference matches
3. Prioritize best opportunities
4. Provide comprehensive lead packages
</workflow>

<response_format>
**Lead Presentation:**
- **Lead Name/Company** (Confidence: X%)
- **Contact Information:** Email, phone, LinkedIn
- **Key Details:** Property/investment focus, budget, location
- **Why Qualified:** Match criteria and engagement signals
- **Outreach Strategy:** Personalized approach recommendations
- **Source:** Where lead was found

**Batch Results:**
Present top 5-10 leads with summary statistics:
- Total leads found
- Average confidence score
- Geographic distribution
- Asset type breakdown
- Recommended follow-up priorities
</response_format>

<quality_standards>
- **Verify contact accuracy** before presenting
- **Provide confidence scores** (0-100%) for each lead
- **Explain qualification logic** for transparency
- **Respect ethical boundaries** - public data only
- **Flag potential issues** (incomplete data, low confidence)
- **Suggest data enrichment** when partial information found
</quality_standards>

<error_handling>
- If search returns no results, adjust criteria and retry
- If scraping fails, explain limitations and alternatives
- If enrichment incomplete, present what's available
- Always provide actionable next steps
- Suggest manual verification for critical leads
</error_handling>
"""


def get_api_key_for_model(model_name: str, config: RunnableConfig) -> str | None:
    """Get API key for the specified model from config or environment."""
    api_keys = config.get("configurable", {}).get("apiKeys", {})
    
    if "anthropic" in model_name.lower():
        return api_keys.get("anthropic") or os.getenv("ANTHROPIC_API_KEY")
    elif "openai" in model_name.lower() or "gpt" in model_name.lower():
        return api_keys.get("openai") or os.getenv("OPENAI_API_KEY")
    elif "google" in model_name.lower() or "gemini" in model_name.lower():
        return api_keys.get("google") or os.getenv("GOOGLE_API_KEY")
    
    return None


# =============================================================================
# Lead Generation Agent
# =============================================================================

async def graph(config: RunnableConfig):
    """Lead Generation Agent entry point."""
    
    # Setup LangSmith tracing
    setup_langsmith(project_name="SuiteCRE-LeadGeneration")
    
    cfg = LeadGenConfigPydantic(**config.get("configurable", {}))
    
    # Initialize model
    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )
    
    # Create agent with lead generation tools
    return create_react_agent(
        prompt=LEAD_GENERATION_PROMPT,
        model=model,
        tools=LEAD_GENERATION_TOOLS,
        config_schema=LeadGenConfigPydantic,
    )