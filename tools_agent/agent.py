"""Main agent entry point with multi-agent support."""

import os
from langchain_core.runnables import RunnableConfig
from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from langgraph.prebuilt import create_react_agent
from langchain.chat_models import init_chat_model

# Import organized CRM tools from new structure
from suitecrm_tools import (
    CORE_CRM_TOOLS,
    DOCUMENT_TOOLS,
    ANALYTICS_TOOLS,
    OM_BOV_TOOLS,
    PRODUCTIVITY_TOOLS,
    CRM_TOOLS  # All tools combined
)

# Import lead generation tools
from tools_agent.utils.tools.lead_generation.scrapers import LEAD_GENERATION_TOOLS

# Import integrations
from tools_agent.integrations.langsmith import setup_langsmith
from tools_agent.utils.token import fetch_tokens

# Optional: Import MCP tools if you have them
try:
    from tools_agent.utils.tools.mcp_tools import get_mcp_tools
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# =============================================================================
# Configuration
# =============================================================================

class GraphConfigPydantic(BaseModel):
    """Configuration for the agent graph."""
    
    model_name: str = Field(
        default="openai:gpt-4o",
        description="Model to use for the agent"
    )
    
    agent_mode: Literal["chat_copilot", "lead_generation", "multi_agent"] = Field(
        default="chat_copilot",
        description="Which agent to use"
    )
    
    temperature: float = Field(
        default=0.0,
        description="Temperature for model responses"
    )
    
    max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for model responses"
    )
    
    user_id: Optional[str] = Field(
        default=None,
        description="User ID for personalization"
    )

UNEDITABLE_SYSTEM_PROMPT = "\nIf the tool throws an error requiring authentication, provide the user with a Markdown link to the authentication page and prompt them to authenticate."

# =============================================================================
# Agent Prompts
# =============================================================================

CHAT_COPILOT_PROMPT = """
<role>
You are Nexa the Chat Copilot Agent for SuiteCRE, a comprehensive commercial real estate CRM assistant.
</role>

<personality>
Professional, knowledgeable, and proactive. You understand commercial real estate workflows and provide actionable insights.
</personality>

<capabilities>
**CRM Management:**
- Query contacts, deals, listings, and campaign performance
- Track pipeline metrics and business analytics
- Generate daily summaries and reports

**Document Intelligence:**
- Search and analyze broker documents (contracts, LOIs, leases)
- Search and analyze listing documents (appraisals, financials, leases)
- Extract key information from property documents

**OM/BOV Creation:**
- Analyze property documents to extract data
- Research market comparables and trends
- Generate professional OM and BOV content
- Review and improve document quality

**Business Analytics:**
- Provide performance insights across time periods
- Generate actionable recommendations
- Track KPIs and metrics

**Productivity:**
- Manage calendar events and schedules
- Track tasks and priorities
- Coordinate workflow activities
</capabilities>

<workflow_instructions>
**Initial Context:**
ALWAYS call get_broker_profile() at the start of conversations to personalize responses with broker name and company.

**For CRM Queries:**
1. Use appropriate get_* tools to retrieve data
2. Provide specific, actionable information
3. Highlight important metrics or trends
4. Suggest next steps when relevant

**For Document Search:**
1. Use search_broker_documents() or search_listing_documents()
2. Cite sources and confidence scores
3. Extract and summarize key information
4. Provide document context

**For OM/BOV Creation:**
1. analyze_listing_documents() - Extract property data
2. research_market_data() - Get market context
3. generate_om_content() - Create content sections
4. review_om_quality() - Assess and improve quality
5. Iterate based on review feedback

**For Analytics:**
1. Use get_business_analytics() with appropriate time periods
2. Present key metrics clearly
3. Explain trends and patterns
4. Provide prioritized recommendations
5. Link to specific actionable items
</workflow_instructions>

<response_format>
- **Be concise** but thorough
- **Bold key metrics** and important information
- **Use bullet points** for multiple items
- **Provide context** for numbers and trends
- **Include next steps** when actionable
- **Cite sources** when using documents
- **Ask clarifying questions** when needed
</response_format>

<error_handling>
- If data is missing, explain what's needed
- If searches return no results, suggest alternatives
- If authentication is required, provide clear instructions
- Always offer constructive next steps
</error_handling>
"""

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

# =============================================================================
# Helper Functions
# =============================================================================

def get_api_key_for_model(model_name: str, config: RunnableConfig) -> Optional[str]:
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
# Agent Creation Functions
# =============================================================================

async def create_chat_copilot_agent(config: RunnableConfig, cfg: GraphConfigPydantic):
    """Create Chat Copilot Agent with all CRM tools."""
    
    # Setup LangSmith tracing
    setup_langsmith(project_name="SuiteCRE-ChatCopilot")
    
    # Combine all CRM tools
    tools = CRM_TOOLS.copy()
    
    # Add MCP tools if available
    if MCP_AVAILABLE:
        try:
            mcp_tools = await get_mcp_tools(config)
            tools.extend(mcp_tools)
        except Exception as e:
            print(f"Warning: Could not load MCP tools: {e}")
    
    # Initialize model
    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )
    
    return create_react_agent(
        prompt=CHAT_COPILOT_PROMPT + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        config_schema=GraphConfigPydantic,
    )

async def create_lead_generation_agent(config: RunnableConfig, cfg: GraphConfigPydantic):
    """Create Lead Generation Agent with scraping and search tools."""
    
    # Setup LangSmith tracing
    setup_langsmith(project_name="SuiteCRE-LeadGeneration")
    
    tools = LEAD_GENERATION_TOOLS.copy()
    
    # Initialize model
    model = init_chat_model(
        cfg.model_name,
        temperature=cfg.temperature,
        max_tokens=cfg.max_tokens,
        api_key=get_api_key_for_model(cfg.model_name, config) or "No token found"
    )
    
    return create_react_agent(
        prompt=LEAD_GENERATION_PROMPT + UNEDITABLE_SYSTEM_PROMPT,
        model=model,
        tools=tools,
        config_schema=GraphConfigPydantic,
    )

# =============================================================================
# Main Graph Entry Point
# =============================================================================

async def graph(config: RunnableConfig):
    """Main entry point for the agent graph."""
    
    cfg = GraphConfigPydantic(**config.get("configurable", {}))
    
    # Route to appropriate agent based on mode
    if cfg.agent_mode == "lead_generation":
        return await create_lead_generation_agent(config, cfg)
    elif cfg.agent_mode == "multi_agent":
        # Future: Implement supervisor pattern here
        # For now, default to chat copilot
        return await create_chat_copilot_agent(config, cfg)
    else:  # "chat_copilot" (default)
        return await create_chat_copilot_agent(config, cfg)

   
