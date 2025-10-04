# workflow_agents/constants.py
"""
Constants for workflow agents system.
Defines all system-wide values, prompts, and configurations.
"""

# =====================================================
# WORKFLOW TYPES
# =====================================================
WORKFLOW_TYPE_AUTOMATION = "automation"  # Visual workflow builder
WORKFLOW_TYPE_PIPELINE = "pipeline"      # CRM pipeline workflows

# =====================================================
# WORKFLOW STATUSES
# =====================================================
STATUS_DRAFT = "draft"
STATUS_ACTIVE = "active"
STATUS_PAUSED = "paused"
STATUS_ARCHIVED = "archived"

# =====================================================
# RATE LIMITING CONFIGURATIONS
# =====================================================
RATE_LIMITS = {
    "workflow_create": {
        "limit": 20,
        "window_hours": 1,
        "message": "You've created {count} workflows in the last hour. Please wait {minutes} minutes."
    },
    "workflow_validate": {
        "limit": 50,
        "window_hours": 1,
        "message": "You've run {count} validations in the last hour. Please wait {minutes} minutes."
    },
    "workflow_explain": {
        "limit": 100,
        "window_hours": 1,
        "message": "You've requested {count} explanations in the last hour. Please wait {minutes} minutes."
    },
    "db_writes": {
        "limit": 10,
        "window_minutes": 1,
        "message": "Too many database operations. Please slow down."
    }
}

# =====================================================
# AGENT SYSTEM PROMPTS
# =====================================================

WORKFLOW_BUILDER_PROMPT = """You are a workflow automation builder specialist for SuiteCRE.

Your ONLY job is to create visual workflow automations on the canvas.

TERMINOLOGY:
- "workflow" or "automation" = visual flow diagram on canvas
- "trigger" = what starts the workflow (email received, calendar event, webhook, etc.)
- "action" = what the workflow does (create task, send email, update CRM, etc.)
- "node" = individual step in the workflow
- "connector" = integration (Gmail, Google Calendar, Slack, Webhooks, etc.)
- "flow" = the complete automation being built

YOU DO NOT:
- Manage CRM pipelines (that's Nexa's job)
- Handle general assistant tasks
- Work outside the workflow canvas

RULES:
1. ALWAYS create workflows as DRAFTS first
2. NEVER activate workflows without explicit user confirmation
3. Ask clarifying questions when requirements are ambiguous
4. Propose sensible defaults (e.g., "inbox" label for Gmail triggers)
5. If a required connector is not connected, provide an OAuth connection link
6. Use natural language to explain technical workflow concepts
7. When mapping data (like email to CRM contact), offer to call the Data Mapper Agent

OUTPUT FORMAT:
After creating a draft, respond with:
- Brief summary of what the workflow does
- Visual representation if helpful (trigger → action flow)
- List any missing configurations the user needs to fill
- Link to review the workflow on the canvas
- Clear next steps ("Review and click 'Activate' when ready")

EXAMPLES OF GOOD WORKFLOWS:
- "When email mentions '123 Main St', create showing event" → Gmail trigger + Calendar action
- "When deal moves to Closing, send congratulations email" → CRM trigger + Gmail action  
- "Every Monday at 9am, send weekly report" → Schedule trigger + Email action

Remember: You build automations, not manage pipelines."""

WORKFLOW_VALIDATOR_PROMPT = """You are a workflow validation specialist for SuiteCRE.

Your ONLY job is to check if workflows are ready to activate.

YOU CHECK FOR:
1. **Missing or expired credentials**
   - OAuth tokens valid?
   - API keys present?
   - Scopes sufficient?

2. **Empty required fields**
   - Email templates have subject and body?
   - Calendar IDs selected?
   - Webhook URLs valid?

3. **Invalid configurations**
   - Calendar/folder/list IDs exist and accessible?
   - Email addresses formatted correctly?
   - Conditional logic valid?

4. **Security and scope issues**
   - OAuth permissions adequate for actions?
   - Rate limits considered?

OUTPUT FORMAT:
Return structured validation results:
{
  "status": "ready" | "needs_fixes",
  "can_activate": true | false,
  "issues": [
    {
      "severity": "error" | "warning" | "info",
      "node_id": "uuid",
      "field": "calendar_id",
      "message": "Calendar ID is required",
      "suggested_fix": "Select a calendar from your connected Google account",
      "auto_fixable": false
    }
  ],
  "summary": "Found 2 errors and 1 warning"
}

RULES:
1. NEVER modify workflows yourself - only suggest fixes
2. Errors block activation, warnings don't
3. Always provide actionable suggested fixes
4. Test API connectivity when possible (dry run)
5. Be helpful and clear - users may not be technical

PRIORITY ORDER:
1. Critical errors (missing credentials, broken configs)
2. Warnings (suboptimal settings, rate limit risks)
3. Info (suggestions for improvement)

Remember: You validate, not fix. Empower users to make workflows production-ready."""

WORKFLOW_EXPLAINER_PROMPT = """You are a workflow explainer specialist for SuiteCRE.

Your ONLY job is to make workflow execution transparent and debuggable.

YOU EXPLAIN:
- Why workflows did or didn't run
- What each step did and why
- Why steps were skipped
- What errors occurred and how to fix them
- Performance insights (slow steps, rate limits hit)

OUTPUT FORMAT:
For run summaries, use this structure:
📊 **Run #{run_id} Summary**
- **Status**: Success/Error/Timeout
- **Duration**: X seconds
- **Trigger**: What started it

🔄 **Step-by-Step:**
1. ✅ **Gmail Trigger** - Detected email from john@example.com mentioning "123 Main St"
2. ⏭️ **Condition** - Skipped: Property value ($85k) below threshold ($100k)
3. ❌ **Calendar Action** - Failed: Missing calendar_id configuration

💡 **Recommendations:**
- Update threshold to $80k if you want to include this property
- Configure calendar ID in node settings

RULES:
1. Use emojis for visual clarity (✅ ❌ ⏭️ ⚠️)
2. Keep explanations concise (2-4 bullets per step)
3. Always reference specific step/node IDs for precision
4. Provide actionable fixes for errors
5. Use plain language - avoid technical jargon
6. Highlight patterns ("This node often fails because...")

HANDLING QUESTIONS:
- "Why didn't my workflow run?" → Check trigger conditions, creds, activation status
- "Why was step X skipped?" → Explain conditional logic evaluation
- "Why did it fail?" → Identify root cause, suggest fix
- "How can I improve this?" → Performance tips, better configurations

PRIVACY:
- Redact PII by default (emails, phone numbers, addresses)
- Only show relevant error context
- Summarize large data payloads

Remember: You make the invisible visible. Help users understand their automations."""

WORKFLOW_DATA_MAPPER_PROMPT = """You are a data mapping specialist for SuiteCRE.

Your ONLY job is to intelligently map external data to SuiteCRE CRM entities.

YOU MAP:
- Email data → Contacts, Deals, Listings
- Calendar events → Showings, Tasks
- External forms → Lead capture
- Spreadsheet rows → Bulk imports

MAPPING STRATEGIES:
1. **Exact Match** - Email exactly matches contact email
2. **Fuzzy Match** - "john doe" matches "John Doe" in CRM
3. **Semantic Match** - "123 Main Street" matches "123 Main St"
4. **Context Clues** - Property mentioned in email + contact together

OUTPUT FORMAT:
{
  "matches": [
    {
      "field": "email_from",
      "value": "john.doe@example.com",
      "crm_entity": "contact",
      "crm_id": "uuid",
      "crm_name": "John Doe",
      "confidence": 0.95,
      "match_type": "exact"
    }
  ],
  "unmapped": ["property_address"],
  "suggestions": [
    {
      "field": "property_address",
      "create_new": true,
      "entity_type": "listing",
      "reason": "No existing listing matches '456 Oak Ave'"
    }
  ]
}

RULES:
1. Ask for confirmation on low-confidence matches (< 0.8)
2. Suggest creating new entities when no match found
3. Learn from user corrections (store mappings)
4. Handle multiple possible matches gracefully
5. Consider context (e.g., recent email thread)

CONFIDENCE LEVELS:
- 1.0 = Perfect match (exact email/ID)
- 0.9-0.99 = Very high (normalized match)
- 0.7-0.89 = High (fuzzy match)
- 0.5-0.69 = Medium (semantic match)
- < 0.5 = Low (requires confirmation)

EXAMPLES:
- Email from "j.smith@gmail.com" → Match to Contact "John Smith" (0.95)
- Subject "Showing at 123 Main" → Match to Listing "123 Main St" (0.88)
- New email "jane@example.com" → Suggest creating new Contact (1.0 new)

Remember: Accuracy over speed. Better to ask than to guess wrong."""

SUPERVISOR_PROMPT = """You are the workflow automation supervisor for SuiteCRE.

Your job is to route user requests to the right specialist agent.

AVAILABLE AGENTS:
1. **Builder Agent** - Creates and edits workflows
2. **Validator Agent** - Checks workflows for errors
3. **Explainer Agent** - Explains workflow runs and debugging
4. **Data Mapper Agent** - Maps external data to CRM entities

ROUTING LOGIC:

→ **Builder Agent** when user wants to:
- "Create a workflow that..."
- "Build an automation for..."
- "Set up a trigger when..."
- "Add a step to..."
- "Edit my workflow to..."

→ **Validator Agent** when user wants to:
- "Check if my workflow is ready"
- "Validate this automation"
- "Why can't I activate..."
- "Find errors in..."
- "Test my workflow"

→ **Explainer Agent** when user wants to:
- "Why didn't my workflow run?"
- "What happened in run #..."
- "Explain why step X failed"
- "Show me the logs for..."
- "Why was this skipped?"

→ **Data Mapper Agent** when user wants to:
- "Map these email fields to..."
- "Which contact does this email belong to?"
- "Find the listing for '123 Main St'"
- "Match this data to CRM"

RULES:
1. Route to ONE agent at a time (no parallel calls)
2. If ambiguous, ask clarifying question
3. Pass full context to delegated agent
4. Synthesize multi-agent responses clearly
5. Track conversation state across agents

WORKFLOW:
User → Supervisor → Specialist Agent → Response → Supervisor → User

Remember: You orchestrate, agents execute. Be the intelligent traffic controller."""

# workflow_agents/constants.py (UPDATED CONNECTORS SECTION)
"""
Updated connector definitions with comprehensive integrations.
"""

# =====================================================
# CONNECTOR DEFINITIONS
# All available workflow connectors
# =====================================================
AVAILABLE_CONNECTORS = {
    # ===== EMAIL PROVIDERS =====
    "gmail": {
        "name": "Gmail",
        "category": "email",
        "provider": "google",
        "triggers": [
            "email_received",
            "email_sent",
            "label_added",
            "starred",
            "attachment_received"
        ],
        "actions": [
            "send_email",
            "send_with_attachment",
            "add_label",
            "remove_label",
            "create_draft",
            "mark_read",
            "mark_unread",
            "star",
            "archive",
            "trash"
        ],
        "oauth_scopes": [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/gmail.compose"
        ],
        "icon": "gmail",
        "color": "#EA4335"
    },
    "outlook": {
        "name": "Outlook Email",
        "category": "email",
        "provider": "microsoft",
        "triggers": [
            "email_received",
            "email_sent",
            "folder_changed",
            "flag_added"
        ],
        "actions": [
            "send_email",
            "send_with_attachment",
            "move_to_folder",
            "add_flag",
            "mark_read",
            "mark_unread",
            "delete",
            "create_draft"
        ],
        "oauth_scopes": [
            "Mail.ReadWrite",
            "Mail.Send"
        ],
        "icon": "outlook",
        "color": "#0078D4"
    },
    
    # ===== CALENDAR PROVIDERS =====
    "google_calendar": {
        "name": "Google Calendar",
        "category": "calendar",
        "provider": "google",
        "triggers": [
            "event_created",
            "event_updated",
            "event_deleted",
            "event_starting",
            "event_response_received"
        ],
        "actions": [
            "create_event",
            "update_event",
            "delete_event",
            "add_attendee",
            "send_reminder",
            "block_time"
        ],
        "oauth_scopes": [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events"
        ],
        "icon": "google-calendar",
        "color": "#4285F4"
    },
    "outlook_calendar": {
        "name": "Outlook Calendar",
        "category": "calendar",
        "provider": "microsoft",
        "triggers": [
            "event_created",
            "event_updated",
            "event_deleted",
            "event_starting",
            "meeting_accepted"
        ],
        "actions": [
            "create_event",
            "update_event",
            "delete_event",
            "add_attendee",
            "send_meeting_invite",
            "block_time"
        ],
        "oauth_scopes": [
            "Calendars.ReadWrite"
        ],
        "icon": "outlook-calendar",
        "color": "#0078D4"
    },
    "calendly": {
        "name": "Calendly",
        "category": "calendar",
        "provider": "calendly",
        "triggers": [
            "event_scheduled",
            "event_cancelled",
            "event_rescheduled",
            "invitee_created"
        ],
        "actions": [
            "create_event_type",
            "cancel_event",
            "get_scheduled_events"
        ],
        "oauth_scopes": [],
        "api_key_required": True,
        "icon": "calendly",
        "color": "#006BFF"
    },
    
    # ===== CLOUD STORAGE =====
    "google_drive": {
        "name": "Google Drive",
        "category": "storage",
        "provider": "google",
        "triggers": [
            "file_created",
            "file_updated",
            "file_deleted",
            "file_shared",
            "folder_created"
        ],
        "actions": [
            "upload_file",
            "create_folder",
            "share_file",
            "move_file",
            "copy_file",
            "delete_file",
            "download_file",
            "update_permissions"
        ],
        "oauth_scopes": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/drive.file"
        ],
        "icon": "google-drive",
        "color": "#4285F4"
    },
    "onedrive": {
        "name": "OneDrive",
        "category": "storage",
        "provider": "microsoft",
        "triggers": [
            "file_created",
            "file_updated",
            "file_deleted",
            "folder_created"
        ],
        "actions": [
            "upload_file",
            "create_folder",
            "share_file",
            "move_file",
            "copy_file",
            "delete_file",
            "download_file"
        ],
        "oauth_scopes": [
            "Files.ReadWrite",
            "Files.ReadWrite.All"
        ],
        "icon": "onedrive",
        "color": "#0078D4"
    },
    
    # ===== DOCUMENT EDITORS =====
    "google_sheets": {
        "name": "Google Sheets",
        "category": "spreadsheet",
        "provider": "google",
        "triggers": [
            "row_added",
            "row_updated",
            "cell_changed",
            "sheet_created"
        ],
        "actions": [
            "add_row",
            "update_row",
            "delete_row",
            "create_sheet",
            "update_cell",
            "clear_sheet",
            "find_row",
            "bulk_update"
        ],
        "oauth_scopes": [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive.file"
        ],
        "icon": "google-sheets",
        "color": "#0F9D58"
    },
    "excel": {
        "name": "Microsoft Excel",
        "category": "spreadsheet",
        "provider": "microsoft",
        "triggers": [
            "row_added",
            "row_updated",
            "worksheet_changed"
        ],
        "actions": [
            "add_row",
            "update_row",
            "delete_row",
            "create_worksheet",
            "update_cell",
            "create_table",
            "add_chart"
        ],
        "oauth_scopes": [
            "Files.ReadWrite"
        ],
        "icon": "excel",
        "color": "#217346"
    },
    "google_docs": {
        "name": "Google Docs",
        "category": "document",
        "provider": "google",
        "triggers": [
            "document_created",
            "document_updated",
            "comment_added"
        ],
        "actions": [
            "create_document",
            "update_content",
            "append_text",
            "insert_table",
            "share_document",
            "export_as_pdf"
        ],
        "oauth_scopes": [
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/drive.file"
        ],
        "icon": "google-docs",
        "color": "#4285F4"
    },
    "word": {
        "name": "Microsoft Word",
        "category": "document",
        "provider": "microsoft",
        "triggers": [
            "document_created",
            "document_updated"
        ],
        "actions": [
            "create_document",
            "update_content",
            "insert_text",
            "insert_table",
            "export_as_pdf"
        ],
        "oauth_scopes": [
            "Files.ReadWrite"
        ],
        "icon": "word",
        "color": "#2B579A"
    },
    
    # ===== COMMUNICATION =====
    "slack": {
        "name": "Slack",
        "category": "communication",
        "provider": "slack",
        "triggers": [
            "message_received",
            "reaction_added",
            "channel_created",
            "user_joined",
            "mention_received"
        ],
        "actions": [
            "send_message",
            "send_dm",
            "create_channel",
            "add_reaction",
            "pin_message",
            "set_status",
            "upload_file",
            "invite_to_channel"
        ],
        "oauth_scopes": [
            "chat:write",
            "channels:read",
            "channels:write",
            "users:read",
            "files:write"
        ],
        "icon": "slack",
        "color": "#4A154B"
    },
    "teams": {
        "name": "Microsoft Teams",
        "category": "communication",
        "provider": "microsoft",
        "triggers": [
            "message_received",
            "channel_created",
            "meeting_started",
            "mention_received"
        ],
        "actions": [
            "send_message",
            "create_channel",
            "create_meeting",
            "add_member",
            "send_notification",
            "upload_file"
        ],
        "oauth_scopes": [
            "Chat.ReadWrite",
            "Team.ReadBasic.All",
            "ChannelMessage.Send"
        ],
        "icon": "teams",
        "color": "#6264A7"
    },
    "zoom": {
        "name": "Zoom",
        "category": "video",
        "provider": "zoom",
        "triggers": [
            "meeting_started",
            "meeting_ended",
            "participant_joined",
            "recording_completed"
        ],
        "actions": [
            "create_meeting",
            "update_meeting",
            "delete_meeting",
            "add_registrant",
            "send_invitation",
            "start_recording"
        ],
        "oauth_scopes": [
            "meeting:write",
            "meeting:read"
        ],
        "icon": "zoom",
        "color": "#2D8CFF"
    },
    
    # ===== CRM =====
    "salesforce": {
        "name": "Salesforce",
        "category": "crm",
        "provider": "salesforce",
        "triggers": [
            "record_created",
            "record_updated",
            "opportunity_stage_changed",
            "lead_converted",
            "task_completed"
        ],
        "actions": [
            "create_record",
            "update_record",
            "delete_record",
            "search_records",
            "create_task",
            "log_activity",
            "update_opportunity",
            "convert_lead"
        ],
        "oauth_scopes": [
            "api",
            "refresh_token"
        ],
        "icon": "salesforce",
        "color": "#00A1E0"
    },
    "hubspot": {
        "name": "HubSpot",
        "category": "crm",
        "provider": "hubspot",
        "triggers": [
            "contact_created",
            "contact_updated",
            "deal_stage_changed",
            "form_submitted",
            "email_opened"
        ],
        "actions": [
            "create_contact",
            "update_contact",
            "create_deal",
            "update_deal",
            "create_task",
            "send_email",
            "add_to_list",
            "log_activity"
        ],
        "oauth_scopes": [
            "crm.objects.contacts.write",
            "crm.objects.deals.write",
            "crm.objects.companies.write"
        ],
        "icon": "hubspot",
        "color": "#FF7A59"
    },
    "suitecrm": {
        "name": "SuiteCRM",
        "category": "crm",
        "provider": "internal",
        "triggers": [
            "deal_updated",
            "contact_created",
            "listing_created",
            "task_completed",
            "showing_scheduled",
            "pipeline_stage_changed"
        ],
        "actions": [
            "create_contact",
            "update_contact",
            "create_deal",
            "update_deal",
            "create_listing",
            "create_task",
            "add_note",
            "schedule_showing",
            "move_pipeline_stage"
        ],
        "oauth_scopes": [],
        "icon": "crm",
        "color": "#0EA5E9"
    },
    
    # ===== PRODUCTIVITY =====
    "tasks": {
        "name": "Tasks",
        "category": "productivity",
        "provider": "internal",
        "triggers": [
            "task_created",
            "task_completed",
            "task_overdue",
            "task_assigned"
        ],
        "actions": [
            "create_task",
            "update_task",
            "complete_task",
            "assign_task",
            "set_due_date",
            "add_subtask"
        ],
        "oauth_scopes": [],
        "icon": "tasks",
        "color": "#8B5CF6"
    },
    "notes": {
        "name": "Notes",
        "category": "productivity",
        "provider": "internal",
        "triggers": [
            "note_created",
            "note_updated",
            "note_tagged"
        ],
        "actions": [
            "create_note",
            "update_note",
            "delete_note",
            "add_tag",
            "attach_to_record"
        ],
        "oauth_scopes": [],
        "icon": "notes",
        "color": "#F59E0B"
    },
    
    # ===== SIGNATURES & CONTRACTS =====
    "docusign": {
        "name": "DocuSign",
        "category": "esignature",
        "provider": "docusign",
        "triggers": [
            "envelope_sent",
            "envelope_signed",
            "envelope_completed",
            "recipient_viewed",
            "envelope_voided"
        ],
        "actions": [
            "send_envelope",
            "create_template",
            "add_recipient",
            "void_envelope",
            "download_document",
            "resend_envelope"
        ],
        "oauth_scopes": [
            "signature",
            "impersonation"
        ],
        "icon": "docusign",
        "color": "#FFBE00"
    },
    
    # ===== SOCIAL & PROFESSIONAL =====
    "linkedin": {
        "name": "LinkedIn",
        "category": "social",
        "provider": "linkedin",
        "triggers": [
            "connection_added",
            "message_received",
            "post_engagement"
        ],
        "actions": [
            "share_post",
            "send_message",
            "create_company_post",
            "add_connection"
        ],
        "oauth_scopes": [
            "r_liteprofile",
            "r_emailaddress",
            "w_member_social"
        ],
        "icon": "linkedin",
        "color": "#0A66C2"
    },
    
    # ===== AUTOMATION PLATFORMS =====
    "zapier": {
        "name": "Zapier",
        "category": "automation",
        "provider": "zapier",
        "triggers": [
            "zap_triggered",
            "webhook_received"
        ],
        "actions": [
            "trigger_zap",
            "send_webhook"
        ],
        "oauth_scopes": [],
        "api_key_required": True,
        "icon": "zapier",
        "color": "#FF4A00"
    },
    "make": {
        "name": "Make (Integromat)",
        "category": "automation",
        "provider": "make",
        "triggers": [
            "scenario_triggered",
            "webhook_received"
        ],
        "actions": [
            "trigger_scenario",
            "send_webhook",
            "execute_module"
        ],
        "oauth_scopes": [],
        "api_key_required": True,
        "icon": "make",
        "color": "#6D00CC"
    },
    
    # ===== WEBHOOKS & CUSTOM =====
    "webhook": {
        "name": "Webhook",
        "category": "integration",
        "provider": "generic",
        "triggers": [
            "webhook_received"
        ],
        "actions": [
            "http_get",
            "http_post",
            "http_put",
            "http_delete",
            "http_patch"
        ],
        "oauth_scopes": [],
        "icon": "webhook",
        "color": "#64748B"
    }
}

# =====================================================
# CONNECTOR CATEGORIES
# For UI organization
# =====================================================
CONNECTOR_CATEGORIES = {
    "email": {
        "label": "Email",
        "icon": "mail",
        "connectors": ["gmail", "outlook"]
    },
    "calendar": {
        "label": "Calendar",
        "icon": "calendar",
        "connectors": ["google_calendar", "outlook_calendar", "calendly"]
    },
    "storage": {
        "label": "Cloud Storage",
        "icon": "cloud",
        "connectors": ["google_drive", "onedrive"]
    },
    "spreadsheet": {
        "label": "Spreadsheets",
        "icon": "table",
        "connectors": ["google_sheets", "excel"]
    },
    "document": {
        "label": "Documents",
        "icon": "file-text",
        "connectors": ["google_docs", "word"]
    },
    "communication": {
        "label": "Team Communication",
        "icon": "message-circle",
        "connectors": ["slack", "teams"]
    },
    "video": {
        "label": "Video Conferencing",
        "icon": "video",
        "connectors": ["zoom"]
    },
    "crm": {
        "label": "CRM",
        "icon": "users",
        "connectors": ["salesforce", "hubspot", "suitecrm"]
    },
    "productivity": {
        "label": "Productivity",
        "icon": "check-square",
        "connectors": ["tasks", "notes"]
    },
    "esignature": {
        "label": "E-Signature",
        "icon": "pen-tool",
        "connectors": ["docusign"]
    },
    "social": {
        "label": "Social & Professional",
        "icon": "share-2",
        "connectors": ["linkedin"]
    },
    "automation": {
        "label": "Automation Platforms",
        "icon": "zap",
        "connectors": ["zapier", "make"]
    },
    "integration": {
        "label": "Custom Integrations",
        "icon": "code",
        "connectors": ["webhook"]
    }
}

# =====================================================
# PROVIDER OAUTH CONFIGS
# Base URLs and configurations for OAuth
# =====================================================
OAUTH_PROVIDERS = {
    "google": {
        "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "user_info_url": "https://www.googleapis.com/oauth2/v2/userinfo"
    },
    "microsoft": {
        "auth_url": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "token_url": "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        "user_info_url": "https://graph.microsoft.com/v1.0/me"
    },
    "slack": {
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "token_url": "https://slack.com/api/oauth.v2.access",
        "user_info_url": "https://slack.com/api/users.identity"
    },
    "salesforce": {
        "auth_url": "https://login.salesforce.com/services/oauth2/authorize",
        "token_url": "https://login.salesforce.com/services/oauth2/token",
        "user_info_url": "https://login.salesforce.com/services/oauth2/userinfo"
    },
    "hubspot": {
        "auth_url": "https://app.hubspot.com/oauth/authorize",
        "token_url": "https://api.hubapi.com/oauth/v1/token",
        "user_info_url": "https://api.hubapi.com/oauth/v1/access-tokens"
    },
    "linkedin": {
        "auth_url": "https://www.linkedin.com/oauth/v2/authorization",
        "token_url": "https://www.linkedin.com/oauth/v2/accessToken",
        "user_info_url": "https://api.linkedin.com/v2/me"
    },
    "zoom": {
        "auth_url": "https://zoom.us/oauth/authorize",
        "token_url": "https://zoom.us/oauth/token",
        "user_info_url": "https://api.zoom.us/v2/users/me"
    },
    "docusign": {
        "auth_url": "https://account.docusign.com/oauth/auth",
        "token_url": "https://account.docusign.com/oauth/token",
        "user_info_url": "https://account.docusign.com/oauth/userinfo"
    },
    "calendly": {
        "auth_url": "https://auth.calendly.com/oauth/authorize",
        "token_url": "https://auth.calendly.com/oauth/token",
        "user_info_url": "https://api.calendly.com/users/me"
    }
}

# =====================================================
# ERROR MESSAGES
# =====================================================
ERROR_MESSAGES = {
    "rate_limit_exceeded": "Rate limit exceeded. Please try again in {minutes} minutes.",
    "invalid_workflow_type": "Invalid workflow type. Must be 'automation' or 'pipeline'.",
    "missing_credentials": "Missing credentials for {provider}. Please connect your account.",
    "validation_failed": "Workflow validation failed. {count} issues found.",
    "activation_blocked": "Cannot activate workflow with errors. Please fix issues first.",
    "not_found": "Workflow not found or you don't have access.",
    "unauthorized": "You don't have permission to access this workflow."
}

# =====================================================
# SUCCESS MESSAGES
# =====================================================
SUCCESS_MESSAGES = {
    "workflow_created": "✅ Workflow '{name}' created successfully!",
    "workflow_activated": "🚀 Workflow '{name}' is now active!",
    "workflow_paused": "⏸️ Workflow '{name}' paused.",
    "validation_passed": "✅ All validation checks passed!",
    "dry_run_success": "✅ Dry run completed successfully!"
}