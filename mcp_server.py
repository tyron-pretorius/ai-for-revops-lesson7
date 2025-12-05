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
    """Send an email using Gmail API via service account."""
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
        time_min: Start time in ISO format (e.g., '2024-01-15T09:00:00Z')
        time_max: End time in ISO format (e.g., '2024-01-15T17:00:00Z')
        calendar_ids: Optional list of calendar IDs to check (defaults to primary calendar)
    """
    result = gcal_functions.get_free_busy(time_min, time_max, calendar_ids)
    return result

@mcp.tool()
def create_calendar_event(event_details: dict, calendar_id: str = 'primary') -> dict:
    """
    Create a calendar event.
    
    Args:
        event_details: Dictionary containing event details with keys like:
            - summary: Event title
            - location: Event location
            - description: Event description
            - start: Dict with 'dateTime' and 'timeZone'
            - end: Dict with 'dateTime' and 'timeZone'
            - attendees: List of dicts with 'email' key
        calendar_id: Calendar ID (defaults to 'primary')
    """
    result = gcal_functions.create_calendar_event(event_details, calendar_id)
    return result

@mcp.tool()
def update_calendar_event(event_id: str, event_details: dict, calendar_id: str = 'primary') -> dict:
    """
    Update an existing calendar event.
    
    Args:
        event_id: The ID of the event to update
        event_details: Dictionary containing updated event details
        calendar_id: Calendar ID (defaults to 'primary')
    """
    result = gcal_functions.update_calendar_event(event_id, event_details, calendar_id)
    return result

@mcp.tool()
def delete_calendar_event(event_id: str, calendar_id: str = 'primary') -> dict:
    """
    Delete a calendar event.
    
    Args:
        event_id: The ID of the event to delete
        calendar_id: Calendar ID (defaults to 'primary')
    """
    result = gcal_functions.delete_calendar_event(event_id, calendar_id)
    return result

# ============================================================================
# Salesforce Functions
# ============================================================================

@mcp.tool()
def find_salesforce_contact_or_lead(email: str = None, phone: str = None) -> dict:
    """Find if an email or phone number belongs to a Contact or Lead in Salesforce."""
    result = salesforce_functions.find_contact_or_lead(email, phone)
    return result if result else {"error": "Not found"}

@mcp.tool()
def create_salesforce_lead(fields: dict) -> dict:
    """
    Create a new Lead in Salesforce.
    
    Args:
        fields: Dictionary of Lead fields. Valid fields are:
            - FirstName: Lead's first name (string)
            - LastName: Lead's last name (string, defaults to 'Unknown' if not provided)
            - Company: Company name (string, defaults to 'Unknown' if not provided)
            - Email: Email address (string)
            - Phone: Phone number (string)
            - Title: Job title (string)
            - Website: Company website (string)
            - Country: Country (string)
            - Lead_Source_Detail__c: Lead source detail. Valid values: "SMS Chat", "Web Chat", or "Sales Line"
            
    Important: 
        - Only include fields for which you have actual values. Do NOT include fields with empty, null, or unknown values.
    """
    result = salesforce_functions.create_lead(fields)
    return result

@mcp.tool()
def log_salesforce_task(person_id: str, subject: str, body: str, direction: str = "Inbound") -> dict:
    """
    Create a Task in Salesforce to log email activity.
    
    Args:
        person_id: Contact or Lead ID (WhoId)
        subject: Email subject
        body: Email body content
        direction: 'Inbound' or 'Outbound' (default: 'Inbound')
    """
    result = salesforce_functions.log_sfdc_task(person_id, subject, body, direction)
    return result

# ============================================================================
# Run the server
# ============================================================================

if __name__ == "__main__":

    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/")
