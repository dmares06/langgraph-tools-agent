# workflow_agents/utils/helpers.py
"""
Utility functions for workflow agents.
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)


def sanitize_node_config(config: dict) -> dict:
    """
    Sanitize node configuration, removing sensitive data.
    
    Args:
        config: Raw node configuration
        
    Returns:
        Sanitized configuration
    """
    sensitive_fields = [
        "api_key", "secret", "token", "password",
        "credential", "auth", "bearer"
    ]
    
    sanitized = config.copy()
    
    for key in list(sanitized.keys()):
        # Check if key contains sensitive terms
        if any(term in key.lower() for term in sensitive_fields):
            sanitized[key] = "***REDACTED***"
        
        # Recursively sanitize nested dicts
        elif isinstance(sanitized[key], dict):
            sanitized[key] = sanitize_node_config(sanitized[key])
    
    return sanitized


def redact_pii(text: str) -> str:
    """
    Redact PII from text.
    
    Args:
        text: Text potentially containing PII
        
    Returns:
        Text with PII redacted
    """
    # Email addresses
    text = re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        '[EMAIL]',
        text
    )
    
    # Phone numbers (US format)
    text = re.sub(
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        '[PHONE]',
        text
    )
    
    # SSN
    text = re.sub(
        r'\b\d{3}-\d{2}-\d{4}\b',
        '[SSN]',
        text
    )
    
    return text


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable form.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted string (e.g., "2m 30s")
    """
    if seconds < 1:
        return f"{int(seconds * 1000)}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


def parse_workflow_intent(message: str) -> dict:
    """
    Parse user message to extract workflow intent.
    
    Args:
        message: User's natural language message
        
    Returns:
        Parsed intent dictionary
    """
    message_lower = message.lower()
    
    intent = {
        "action": None,  # create, edit, validate, explain
        "trigger_type": None,
        "action_type": None,
        "entities": [],
        "conditions": [],
        "confidence": 0.0
    }
    
    # Detect action
    if any(word in message_lower for word in ["create", "build", "make", "set up"]):
        intent["action"] = "create"
        intent["confidence"] += 0.3
    elif any(word in message_lower for word in ["edit", "update", "modify", "change"]):
        intent["action"] = "edit"
        intent["confidence"] += 0.3
    elif any(word in message_lower for word in ["validate", "check", "test"]):
        intent["action"] = "validate"
        intent["confidence"] += 0.3
    elif any(word in message_lower for word in ["why", "explain", "what happened"]):
        intent["action"] = "explain"
        intent["confidence"] += 0.3
    
    # Detect trigger type
    if "email" in message_lower or "gmail" in message_lower:
        intent["trigger_type"] = "gmail"
        intent["confidence"] += 0.2
    elif "calendar" in message_lower or "event" in message_lower:
        intent["trigger_type"] = "google_calendar"
        intent["confidence"] += 0.2
    elif "webhook" in message_lower:
        intent["trigger_type"] = "webhook"
        intent["confidence"] += 0.2
    elif "schedule" in message_lower or "daily" in message_lower or "weekly" in message_lower:
        intent["trigger_type"] = "schedule"
        intent["confidence"] += 0.2
    
    # Extract entities (simple regex patterns)
    # Email addresses
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', message)
    if emails:
        intent["entities"].extend([{"type": "email", "value": e} for e in emails])
        intent["confidence"] += 0.1
    
    # Addresses (simple pattern)
    address_pattern = r'\b\d{1,5}\s+\w+\s+(street|st|avenue|ave|road|rd|drive|dr)\b'
    addresses = re.findall(address_pattern, message, re.IGNORECASE)
    if addresses:
        intent["entities"].extend([{"type": "address", "value": a} for a in addresses])
        intent["confidence"] += 0.1
    
    # Detect conditions
    if "if" in message_lower or "when" in message_lower:
        intent["conditions"].append({"detected": True})
        intent["confidence"] += 0.1
    
    return intent


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid
    """
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))


def generate_oauth_url(
    provider: str,
    user_id: str,
    redirect_base: str,
    scopes: list[str]
) -> str:
    """
    Generate OAuth connection URL.
    
    Args:
        provider: Provider name (gmail, google_calendar, slack)
        user_id: User's UUID
        redirect_base: Base URL for redirects
        scopes: Required OAuth scopes
        
    Returns:
        OAuth URL
    """
    # This is a placeholder - implement actual OAuth flow
    from urllib.parse import urlencode
    
    params = {
        "provider": provider,
        "user_id": user_id,
        "scopes": ",".join(scopes),
        "redirect_uri": f"{redirect_base}/oauth/callback"
    }
    
    return f"{redirect_base}/oauth/connect?{urlencode(params)}"


def format_run_summary(run_data: dict) -> str:
    """
    Format workflow run data into human-readable summary.
    
    Args:
        run_data: Raw run data from database
        
    Returns:
        Formatted markdown summary
    """
    status_emoji = {
        "success": "✅",
        "error": "❌",
        "running": "🔄",
        "timeout": "⏱️",
        "cancelled": "⛔"
    }
    
    status = run_data.get("status", "unknown")
    emoji = status_emoji.get(status, "❓")
    
    started = run_data.get("started_at")
    completed = run_data.get("completed_at")
    duration = None
    
    if started and completed:
        start_dt = datetime.fromisoformat(started.replace('Z', '+00:00'))
        complete_dt = datetime.fromisoformat(completed.replace('Z', '+00:00'))
        duration_seconds = (complete_dt - start_dt).total_seconds()
        duration = format_duration(duration_seconds)
    
    summary = f"""📊 **Run #{run_data['id'][:8]}... Summary**

{emoji} **Status**: {status.title()}
⏱️ **Duration**: {duration or 'In progress...'}
🚀 **Started**: {started}

"""
    
    # Add step details if available
    logs = run_data.get("logs", [])
    if logs:
        summary += "🔄 **Steps**:\n"
        for i, log in enumerate(logs, 1):
            step_emoji = "✅" if log.get("status") == "success" else "❌"
            summary += f"{i}. {step_emoji} {log.get('step_name', 'Unknown step')}\n"
    
    # Add error if present
    error = run_data.get("error_message")
    if error:
        summary += f"\n❌ **Error**: {error}\n"
    
    return summary


class WorkflowLogger:
    """
    Structured logger for workflow operations.
    """
    
    def __init__(self, workflow_id: str, user_id: str):
        self.workflow_id = workflow_id
        self.user_id = user_id
        self.logger = logging.getLogger(__name__)
    
    def info(self, message: str, **kwargs):
        """Log info level message."""
        self.logger.info(
            f"[Workflow {self.workflow_id[:8]}] {message}",
            extra={"workflow_id": self.workflow_id, "user_id": self.user_id, **kwargs}
        )
    
    def error(self, message: str, **kwargs):
        """Log error level message."""
        self.logger.error(
            f"[Workflow {self.workflow_id[:8]}] {message}",
            extra={"workflow_id": self.workflow_id, "user_id": self.user_id, **kwargs}
        )
    
    def warning(self, message: str, **kwargs):
        """Log warning level message."""
        self.logger.warning(
            f"[Workflow {self.workflow_id[:8]}] {message}",
            extra={"workflow_id": self.workflow_id, "user_id": self.user_id, **kwargs}
        )


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to max length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."