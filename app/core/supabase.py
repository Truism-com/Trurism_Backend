"""
Supabase Client Setup

Provides a singleton Supabase client initialized from environment variables.
Requires `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` in `.env`.
"""

import os
from dotenv import load_dotenv
from postgrest import PostgrestClient

# Load .env for local development
load_dotenv()

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
# Support common env var names for the service key
_SUPABASE_SERVICE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_SERVICE_KEY")
    or os.getenv("SUPABASE_sERVICE_KEY")  # user-provided variant
    or ""
)

_supabase_client: PostgrestClient | None = None


def get_supabase() -> PostgrestClient:
    """
    Returns a singleton Supabase client. Raises ValueError if env vars missing.
    """
    global _supabase_client
    if _supabase_client is None:
        if not _SUPABASE_URL or not _SUPABASE_SERVICE_KEY:
            raise ValueError(
                "Supabase env vars missing: set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
        # Use REST (PostgREST) client to avoid httpx proxy compatibility issues
        rest_url = _SUPABASE_URL.rstrip('/') + "/rest/v1"
        _supabase_client = PostgrestClient(
            rest_url,
            headers={
                "apikey": _SUPABASE_SERVICE_KEY,
                "Authorization": f"Bearer {_SUPABASE_SERVICE_KEY}",
                "Content-Type": "application/json"
            }
        )
    return _supabase_client
