print("Testing SuiteCRE imports...\n")

# Test 1: Main CRM tools
try:
    from suitecrm_tools import CRM_TOOLS, CORE_CRM_TOOLS, DOCUMENT_TOOLS
    print(f"✓ CRM_TOOLS: {len(CRM_TOOLS)} tools total")
    print(f"  - Core CRM: {len(CORE_CRM_TOOLS)} tools")
    print(f"  - Documents: {len(DOCUMENT_TOOLS)} tools")
except ImportError as e:
    print(f"✗ CRM tools import failed: {e}")

# Test 2: Lead generation
try:
    from tools_agent.utils.tools.lead_generation.scrapers import LEAD_GENERATION_TOOLS
    print(f"✓ Lead generation: {len(LEAD_GENERATION_TOOLS)} tools")
except ImportError as e:
    print(f"✗ Lead gen import failed: {e}")

# Test 3: Integrations
try:
    from tools_agent.integrations.langsmith import setup_langsmith, create_run_metadata
    print("✓ LangSmith integration imported")
except ImportError as e:
    print(f"✗ LangSmith import failed: {e}")

# Test 4: Token utilities
try:
    from tools_agent.utils.token import fetch_tokens, get_model_api_key
    print("✓ Token utilities imported")
except ImportError as e:
    print(f"✗ Token utils import failed: {e}")

# Test 5: Agent graph
try:
    from tools_agent.agent import graph, GraphConfigPydantic
    print("✓ Agent graph imported")
except ImportError as e:
    print(f"✗ Agent import failed: {e}")

print("\n" + "="*50)
print("All imports successful! ✅")
print("="*50)