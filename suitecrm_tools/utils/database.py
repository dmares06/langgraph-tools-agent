"""Database connection utilities for SuiteCRE CRM."""

import os
from supabase import create_client, Client

def get_supabase_client() -> Client:
    """Get authenticated Supabase client using environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY environment variables.")

    return create_client(supabase_url, supabase_key)