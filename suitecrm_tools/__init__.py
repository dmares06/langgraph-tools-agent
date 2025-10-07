"""SuiteCRE CRM Tools - Complete toolkit for commercial real estate professionals."""

try:
    from .main import (
        CRM_TOOLS,
        CORE_CRM_TOOLS,
        DOCUMENT_TOOLS,
        ANALYTICS_TOOLS,
        OM_BOV_TOOLS,
        PRODUCTIVITY_TOOLS,
        TOOL_COLLECTIONS,
        get_tools_by_category
    )
except ImportError as e:
    # If main.py import fails, provide helpful error
    import sys
    print(f"Error importing from suitecrm_tools.main: {e}", file=sys.stderr)
    print("Make sure suitecrm_tools/main.py exists and all dependencies are installed.", file=sys.stderr)
    raise

__version__ = "1.0.0"

__all__ = [
    'CRM_TOOLS',
    'CORE_CRM_TOOLS',
    'DOCUMENT_TOOLS',
    'ANALYTICS_TOOLS',
    'OM_BOV_TOOLS',
    'PRODUCTIVITY_TOOLS',
    'TOOL_COLLECTIONS',
    'get_tools_by_category'
]