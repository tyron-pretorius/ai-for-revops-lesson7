"""
Simple MCP Server that exposes functions from:
- gmail_functions.py
- gcal_functions.py
- salesforce_functions.py
"""

from fastmcp import FastMCP
import sys, os, secrets
from starlette.responses import JSONResponse, PlainTextResponse
from fastmcp.server.auth.auth import AuthProvider, AccessToken
from dotenv import load_dotenv

load_dotenv()

# Add current directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all our function modules
import gmail_functions
import gcal_functions
import salesforce_functions

# ============================================================================
# Simple Bearer (API key) auth provider
# ============================================================================
class StaticApiKeyAuth(AuthProvider):
    """
    Very small auth provider that accepts exactly one API key via
    Authorization: Bearer <API_KEY>.
    """

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.required_scopes = []  # No scopes

    @staticmethod
    def _normalize(token: str | None) -> str:
        if not token:
            return ""
        parts = token.strip().split()
        # "Bearer <key>" / "Token <key>" / "ApiKey <key>"
        if len(parts) == 2 and parts[0].lower() in ("bearer", "token", "apikey"):
            return parts[1]
        # raw token
        return token.strip()

    
    async def verify_token(self, token: str) -> AccessToken | None:
        presented = self._normalize(token)
        if presented and self.api_key and secrets.compare_digest(presented, self.api_key):
            return AccessToken(
                token=presented,                # the presented bearer token
                client_id="revops-mcp-client",  # any stable id/name for the caller
                scopes=[]                      # you’re not using scopes; keep empty
            )
        return None

# Create the MCP server (we’ll attach auth + routes below)
# NOTE: we pass auth=... to enable Bearer verification on HTTP calls.
mcp = FastMCP(
    "RevOps Functions Server",
    auth=StaticApiKeyAuth(api_key=os.getenv("MCP_API_KEY", "")),
)

# ============================================================================
# Health route
# ============================================================================

@mcp.custom_route("/info", methods=["GET"])
async def mcp_info(_request):
    return PlainTextResponse("RevOps MCP Server - MCP endpoint is at / (POST/SSE).")

@mcp.custom_route("/health", methods=["GET"])
async def health(_request):
    # Lightweight app health (not tool health)
    return JSONResponse({"status": "ok"})

# ============================================================================
# Gmail Functions
# ============================================================================

@mcp.tool()
def send_email(to: str, subject: str, message_text: str, cc: str = "", reply_to: str = "", is_html: bool = False) -> dict:
    """
    Send an email using Gmail API.
    
    Args:
        to: REQUIRED. Recipient email address
        subject: REQUIRED. Email subject line
        message_text: REQUIRED. Email body content (plain text or HTML)
        cc: Optional. CC recipient email address
        reply_to: Optional. Reply-to email address
        is_html: Optional. Set to true if message_text contains HTML (default: false)
    
    Example call:
        send_email(
            to="recipient@example.com",
            subject="Meeting Follow-up",
            message_text="Hi, thanks for the call today..."
        )
    """
    service = gmail_functions.get_gmail_service()
    result = gmail_functions.send_email(service, to, cc, subject, message_text, reply_to, is_html)
    return result

# ============================================================================
# Google Calendar Functions
# ============================================================================

@mcp.tool()
def get_calendar_free_busy(time_min: str, time_max: str, calendar_ids: list = None) -> dict:
    """
    Get free/busy information for calendars within a time range.
    
    Args:
        time_min: REQUIRED. Start time in ISO format (e.g., '2024-01-15T09:00:00Z')
        time_max: REQUIRED. End time in ISO format (e.g., '2024-01-15T17:00:00Z')
        calendar_ids: Optional. List of calendar IDs to check (defaults to primary calendar)
    
    Example call:
        get_calendar_free_busy(
            time_min="2024-01-15T09:00:00Z",
            time_max="2024-01-15T17:00:00Z"
        )
    """
    result = gcal_functions.get_free_busy(time_min, time_max, calendar_ids)
    return result

@mcp.tool()
def create_calendar_event(event_details: dict, calendar_id: str = 'primary') -> dict:
    """
    Create a calendar event.
    
    IMPORTANT: Use "dateTime" (camelCase), NOT "date_time". Use "timeZone" (camelCase), NOT "time_zone".
    
    Args:
        event_details: REQUIRED. Dictionary containing event details:
            REQUIRED fields:
                - summary (str): Event title/name
                - start (dict): Must contain "dateTime" (ISO format) and "timeZone"
                - end (dict): Must contain "dateTime" (ISO format) and "timeZone"
            OPTIONAL fields:
                - location (str): Event location
                - description (str): Event description
                - attendees (list): List of dicts with 'email' key
        calendar_id: Optional. Calendar ID (defaults to 'primary')
    
    Example call:
        create_calendar_event(
            event_details={
                "summary": "Team Meeting",
                "description": "Weekly sync",
                "start": {"dateTime": "2024-12-15T09:00:00", "timeZone": "America/Chicago"},
                "end": {"dateTime": "2024-12-15T10:00:00", "timeZone": "America/Chicago"},
                "attendees": [{"email": "colleague@example.com"}]
            },
            calendar_id="primary"
        )
    """
    result = gcal_functions.create_calendar_event(event_details, calendar_id)
    return result

@mcp.tool()
def update_calendar_event(event_id: str, event_details: dict, calendar_id: str = 'primary') -> dict:
    """
    Update an existing calendar event (partial update - only include fields to change).
    
    IMPORTANT: Use "dateTime" (camelCase), NOT "date_time". Use "timeZone" (camelCase), NOT "time_zone".
    
    Args:
        event_id: REQUIRED. The ID of the event to update
        event_details: REQUIRED. Dictionary containing ONLY the fields you want to change:
            - summary (str): New event title
            - location (str): New location
            - description (str): New description
            - start (dict): New start with "dateTime" and "timeZone"
            - end (dict): New end with "dateTime" and "timeZone"
            - attendees (list): Updated list of attendees
        calendar_id: Optional. Calendar ID (defaults to 'primary')
    
    Example call (reschedule an event):
        update_calendar_event(
            event_id="abc123xyz",
            event_details={
                "start": {"dateTime": "2024-12-16T14:00:00", "timeZone": "America/Chicago"},
                "end": {"dateTime": "2024-12-16T15:00:00", "timeZone": "America/Chicago"}
            }
        )
    """
    result = gcal_functions.update_calendar_event(event_id, event_details, calendar_id)
    return result

@mcp.tool()
def delete_calendar_event(event_id: str, calendar_id: str = 'primary') -> dict:
    """
    Delete a calendar event.
    
    Args:
        event_id: REQUIRED. The ID of the event to delete
        calendar_id: Optional. Calendar ID (defaults to 'primary')
    
    Example call:
        delete_calendar_event(event_id="abc123xyz")
    """
    result = gcal_functions.delete_calendar_event(event_id, calendar_id)
    return result

# ============================================================================
# Salesforce Functions
# ============================================================================

@mcp.tool()
def find_salesforce_contact_or_lead(email: str = None, phone: str = None) -> dict:
    """
    Find if an email or phone number belongs to a Contact or Lead in Salesforce.
    
    Args:
        email: Email address to search for
        phone: Phone number to search for
    
    Important: You MUST provide at least one of 'email' or 'phone'. You can provide both.
    
    Example calls:
        find_salesforce_contact_or_lead(email="john@example.com")
        find_salesforce_contact_or_lead(phone="+1-555-123-4567")
        find_salesforce_contact_or_lead(email="john@example.com", phone="+1-555-123-4567")
    """
    result = salesforce_functions.find_contact_or_lead(email, phone)
    return result if result else {"error": "Not found"}

@mcp.tool()
def create_salesforce_lead(fields: dict) -> dict:
    """
    Create a new Lead in Salesforce.
    
    Args:
        fields: REQUIRED. Dictionary of Lead fields. You MUST provide this argument.
            RECOMMENDED fields (provide at least one identifier):
                - Email (str): Email address
                - Phone (str): Phone number
                - FirstName (str): Lead's first name
                - LastName (str): Lead's last name (defaults to 'Unknown' if not provided)
                - Company (str): Company name (defaults to 'Unknown' if not provided)
            OPTIONAL fields:
                - Title (str): Job title
                - Website (str): Company website
                - Country (str): Country
                - Lead_Source_Detail__c (str): Valid values: "SMS Chat", "Web Chat", or "Sales Line"
    
    Important: 
        - Only include fields for which you have actual values
        - Do NOT include fields with empty, null, or unknown values
    
    Example call:
        create_salesforce_lead(
            fields={
                "FirstName": "John",
                "LastName": "Smith",
                "Email": "john.smith@example.com",
                "Company": "Acme Corp",
                "Phone": "+1-555-123-4567"
            }
        )
    """
    result = salesforce_functions.create_lead(fields)
    return result

@mcp.tool()
def log_salesforce_task(person_id: str, subject: str, body: str, direction: str = "Inbound") -> dict:
    """
    Create a Task in Salesforce to log communication activity.
    
    Args:
        person_id: REQUIRED. Salesforce Contact or Lead ID (the WhoId to associate this task with)
        subject: REQUIRED. Task subject line
        body: REQUIRED. Task description/body content
        direction: Optional. 'Inbound' or 'Outbound' (default: 'Inbound')
    
    Example call:
        log_salesforce_task(
            person_id="00Q5e000001ABC123",
            subject="Follow-up call scheduled",
            body="Discussed pricing options. Customer wants to schedule a demo.",
            direction="Outbound"
        )
    """
    result = salesforce_functions.log_sfdc_task(person_id, subject, body, direction)
    return result

# ============================================================================
# Run the server
# ============================================================================

if __name__ == "__main__":

    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/")
