# workflow_agents/tools/credentials_tools.py
"""
Tools for managing OAuth credentials and API keys for workflow connectors.
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
from supabase import create_client, Client
from langchain_core.tools import tool
from cryptography.fernet import Fernet
import base64
import os

from workflow_agents.config import config
from workflow_agents.constants import AVAILABLE_CONNECTORS, OAUTH_PROVIDERS
from workflow_agents.utils.helpers import generate_oauth_url

logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    return create_client(config.supabase_url, config.supabase_key)


def get_encryption_key() -> bytes:
    """Get or create encryption key for credentials."""
    key = os.getenv("CREDENTIAL_ENCRYPTION_KEY")
    if not key:
        # In production, this should be stored securely
        logger.warning("No CREDENTIAL_ENCRYPTION_KEY found, generating temporary key")
        key = Fernet.generate_key().decode()
    return key.encode() if isinstance(key, str) else key


def encrypt_token(token: str) -> str:
    """Encrypt an OAuth token or API key."""
    f = Fernet(get_encryption_key())
    return f.encrypt(token.encode()).decode()


def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an OAuth token or API key."""
    f = Fernet(get_encryption_key())
    return f.decrypt(encrypted_token.encode()).decode()


@tool
def list_user_credentials(user_id: str, provider: Optional[str] = None) -> dict:
    """
    List all OAuth credentials for a user.
    
    Args:
        user_id: User UUID
        provider: Optional filter by provider (google, microsoft, slack, etc.)
        
    Returns:
        List of connected accounts (tokens NOT included)
    """
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("workflow_credentials").select(
            "id, provider, label, account_identifier, scopes, created_at, updated_at, last_used_at, token_expires_at"
        ).eq("owner", user_id)
        
        if provider:
            query = query.eq("provider", provider)
        
        result = query.order("created_at", desc=True).execute()
        
        credentials = result.data if result.data else []
        
        # Add expiration status
        now = datetime.utcnow()
        for cred in credentials:
            if cred.get("token_expires_at"):
                expires_at = datetime.fromisoformat(cred["token_expires_at"].replace('Z', '+00:00'))
                cred["is_expired"] = expires_at < now
                cred["expires_in_days"] = (expires_at - now).days
            else:
                cred["is_expired"] = False
                cred["expires_in_days"] = None
        
        return {
            "success": True,
            "credentials": credentials,
            "count": len(credentials)
        }
        
    except Exception as e:
        logger.error(f"Error listing credentials: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def check_credential_exists(user_id: str, provider: str, account_identifier: Optional[str] = None) -> dict:
    """
    Check if user has connected a specific provider.
    
    Args:
        user_id: User UUID
        provider: Provider name (google, microsoft, slack, etc.)
        account_identifier: Optional specific account (email, etc.)
        
    Returns:
        Connection status
    """
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("workflow_credentials").select("id, label, account_identifier, token_expires_at").eq("owner", user_id).eq("provider", provider)
        
        if account_identifier:
            query = query.eq("account_identifier", account_identifier)
        
        result = query.execute()
        
        connected = len(result.data) > 0 if result.data else False
        
        if connected:
            cred = result.data[0]
            now = datetime.utcnow()
            
            if cred.get("token_expires_at"):
                expires_at = datetime.fromisoformat(cred["token_expires_at"].replace('Z', '+00:00'))
                is_expired = expires_at < now
            else:
                is_expired = False
            
            return {
                "success": True,
                "connected": True,
                "provider": provider,
                "account": cred.get("account_identifier"),
                "label": cred.get("label"),
                "is_expired": is_expired
            }
        else:
            return {
                "success": True,
                "connected": False,
                "provider": provider
            }
        
    except Exception as e:
        logger.error(f"Error checking credential: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_oauth_connection_url(
    user_id: str,
    connector_id: str,
    redirect_uri: Optional[str] = None
) -> dict:
    """
    Generate OAuth connection URL for a connector.
    
    Args:
        user_id: User UUID
        connector_id: Connector identifier (gmail, outlook, etc.)
        redirect_uri: Optional custom redirect URI
        
    Returns:
        OAuth URL to redirect user to
    """
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found"
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        provider = connector.get("provider")
        
        # Check if API key is required instead of OAuth
        if connector.get("api_key_required"):
            return {
                "success": True,
                "requires_api_key": True,
                "connector": connector_id,
                "message": f"{connector['name']} requires an API key, not OAuth"
            }
        
        if not provider or provider == "internal":
            return {
                "success": False,
                "error": f"{connector['name']} does not require external authentication"
            }
        
        if provider not in OAUTH_PROVIDERS:
            return {
                "success": False,
                "error": f"OAuth provider '{provider}' not configured"
            }
        
        scopes = connector.get("oauth_scopes", [])
        
        oauth_url = generate_oauth_url(
            provider=provider,
            user_id=user_id,
            redirect_base=redirect_uri or config.oauth_redirect_base,
            scopes=scopes
        )
        
        return {
            "success": True,
            "oauth_url": oauth_url,
            "provider": provider,
            "connector": connector_id,
            "connector_name": connector["name"],
            "scopes": scopes,
            "message": f"Click the link to connect your {connector['name']} account"
        }
        
    except Exception as e:
        logger.error(f"Error generating OAuth URL: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def store_credential(
    user_id: str,
    provider: str,
    token: str,
    account_identifier: str,
    label: Optional[str] = None,
    scopes: Optional[list[str]] = None,
    expires_in_seconds: Optional[int] = None
) -> dict:
    """
    Store OAuth credential for a user.
    
    Args:
        user_id: User UUID
        provider: Provider name
        token: OAuth access token (will be encrypted)
        account_identifier: Email or username
        label: Optional friendly label
        scopes: OAuth scopes granted
        expires_in_seconds: Token expiration time
        
    Returns:
        Stored credential info
    """
    supabase = get_supabase_client()
    
    try:
        # Encrypt token
        encrypted_token = encrypt_token(token)
        
        # Calculate expiration
        token_expires_at = None
        if expires_in_seconds:
            token_expires_at = (datetime.utcnow() + timedelta(seconds=expires_in_seconds)).isoformat()
        
        credential_data = {
            "owner": user_id,
            "provider": provider,
            "label": label or f"{provider} ({account_identifier})",
            "account_identifier": account_identifier,
            "encrypted_token": encrypted_token,
            "token_expires_at": token_expires_at,
            "scopes": scopes or []
        }
        
        # Check if credential already exists (update instead of insert)
        existing = supabase.table("workflow_credentials").select("id").eq("owner", user_id).eq("provider", provider).eq("account_identifier", account_identifier).execute()
        
        if existing.data:
            # Update existing
            result = supabase.table("workflow_credentials").update(credential_data).eq("id", existing.data[0]["id"]).execute()
        else:
            # Insert new
            result = supabase.table("workflow_credentials").insert(credential_data).execute()
        
        if result.data:
            return {
                "success": True,
                "credential_id": result.data[0]["id"],
                "provider": provider,
                "account": account_identifier
            }
        else:
            return {
                "success": False,
                "error": "Failed to store credential"
            }
        
    except Exception as e:
        logger.error(f"Error storing credential: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def delete_credential(credential_id: str, user_id: str) -> dict:
    """
    Delete a stored credential.
    
    Args:
        credential_id: Credential UUID
        user_id: User UUID (for auth)
        
    Returns:
        Success status
    """
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("workflow_credentials").delete().eq("id", credential_id).eq("owner", user_id).execute()
        
        return {
            "success": True,
            "message": "Credential deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Error deleting credential: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def get_credential_for_connector(
    user_id: str,
    connector_id: str,
    account_identifier: Optional[str] = None
) -> dict:
    """
    Get decrypted credential for a connector.
    INTERNAL USE ONLY - tokens are decrypted.
    
    Args:
        user_id: User UUID
        connector_id: Connector identifier
        account_identifier: Optional specific account
        
    Returns:
        Credential with decrypted token
    """
    supabase = get_supabase_client()
    
    try:
        if connector_id not in AVAILABLE_CONNECTORS:
            return {
                "success": False,
                "error": f"Connector '{connector_id}' not found"
            }
        
        connector = AVAILABLE_CONNECTORS[connector_id]
        provider = connector.get("provider")
        
        if provider == "internal":
            return {
                "success": True,
                "provider": "internal",
                "token": None,
                "message": "Internal connector, no auth required"
            }
        
        query = supabase.table("workflow_credentials").select("*").eq("owner", user_id).eq("provider", provider)
        
        if account_identifier:
            query = query.eq("account_identifier", account_identifier)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": False,
                "error": f"No credential found for {connector['name']}",
                "needs_connection": True,
                "connector_id": connector_id
            }
        
        cred = result.data[0]
        
        # Check expiration
        if cred.get("token_expires_at"):
            expires_at = datetime.fromisoformat(cred["token_expires_at"].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow():
                return {
                    "success": False,
                    "error": "Token has expired",
                    "needs_reconnection": True,
                    "connector_id": connector_id
                }
        
        # Decrypt token
        token = decrypt_token(cred["encrypted_token"])
        
        # Update last used
        supabase.table("workflow_credentials").update({"last_used_at": datetime.utcnow().isoformat()}).eq("id", cred["id"]).execute()
        
        return {
            "success": True,
            "credential_id": cred["id"],
            "provider": provider,
            "token": token,
            "account_identifier": cred["account_identifier"],
            "scopes": cred.get("scopes", [])
        }
        
    except Exception as e:
        logger.error(f"Error getting credential: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@tool
def check_credentials_for_workflow(flow_id: str, user_id: str) -> dict:
    """
    Check if all required credentials are available for a workflow.
    
    Args:
        flow_id: Workflow flow UUID
        user_id: User UUID
        
    Returns:
        Missing credentials and connection URLs
    """
    supabase = get_supabase_client()
    
    try:
        # Get all nodes in the flow
        nodes_result = supabase.table("workflow_nodes").select("*").eq("flow_id", flow_id).execute()
        
        if not nodes_result.data:
            return {
                "success": True,
                "all_connected": True,
                "missing_credentials": []
            }
        
        # Extract connector types from nodes
        required_connectors = set()
        for node in nodes_result.data:
            node_type = node.get("node_type", "")
            # Extract connector from node_type (e.g., "gmail_trigger" -> "gmail")
            connector_id = node_type.split("_")[0]
            if connector_id in AVAILABLE_CONNECTORS:
                required_connectors.add(connector_id)
        
        # Check which are connected
        missing_credentials = []
        for connector_id in required_connectors:
            connector = AVAILABLE_CONNECTORS[connector_id]
            provider = connector.get("provider")
            
            if provider == "internal":
                continue  # Skip internal connectors
            
            # Check if credential exists
            check_result = check_credential_exists(user_id, provider)
            
            if not check_result.get("connected") or check_result.get("is_expired"):
                oauth_url_result = get_oauth_connection_url(user_id, connector_id)
                
                missing_credentials.append({
                    "connector_id": connector_id,
                    "connector_name": connector["name"],
                    "provider": provider,
                    "oauth_url": oauth_url_result.get("oauth_url"),
                    "is_expired": check_result.get("is_expired", False)
                })
        
        return {
            "success": True,
            "all_connected": len(missing_credentials) == 0,
            "missing_credentials": missing_credentials,
            "required_connectors": list(required_connectors)
        }
        
    except Exception as e:
        logger.error(f"Error checking workflow credentials: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }