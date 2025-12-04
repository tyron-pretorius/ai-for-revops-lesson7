import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SERVICE_ACCOUNT_FILE = os.path.join(SCRIPT_DIR, 'sales_mcp.json')
EMAIL = "tyron@theworkflowpro.com"

CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Get an authenticated Google Calendar service for the specified user.
    
    Args:
        user_email: The email of the user to impersonate (must be in your domain)
    
    Returns:
        Google Calendar API service object
    """
    credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE,scopes=CALENDAR_SCOPES)
    delegated_credentials = credentials.with_subject(EMAIL)
    service = build('calendar', 'v3', credentials=delegated_credentials)
    return service


def get_free_busy(time_min, time_max, calendar_ids=None):
    """
    Get free/busy information for specified calendars.
    
    Args:
        user_email: The email of the user to impersonate
        time_min: Start time (ISO format string, e.g., '2024-01-15T09:00:00Z')
        time_max: End time (ISO format string)
        calendar_ids: List of calendar IDs to check (defaults to user's primary calendar)
    
    Returns:
        Free/busy response from the API
    """
    service = get_calendar_service()
    
    if calendar_ids is None:
        calendar_ids = [EMAIL]
    
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cal_id} for cal_id in calendar_ids]
    }
    
    response = service.freebusy().query(body=body).execute()
    return response


def create_calendar_event(event_details, calendar_id='primary'):
    """
    Create a calendar event.
    
    Args:
        user_email: The email of the user to impersonate
        event_details: Dictionary containing event details
        calendar_id: Calendar ID (defaults to 'primary')
    
    Returns:
        Created event response
    
    Example event_details:
        {
            'summary': 'Meeting Title',
            'location': '123 Main St',
            'description': 'Meeting description',
            'start': {
                'dateTime': '2024-01-15T09:00:00',
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': '2024-01-15T10:00:00',
                'timeZone': 'America/New_York',
            },
            'attendees': [
                {'email': 'attendee@example.com'},
            ],
        }
    """
    service = get_calendar_service()
    event = service.events().insert(calendarId=calendar_id, body=event_details).execute()
    return event


def update_calendar_event(event_id, event_details, calendar_id='primary'):
    """
    Update an existing calendar event.
    
    Args:
        user_email: The email of the user to impersonate
        event_id: The ID of the event to update
        event_details: Dictionary containing updated event details
        calendar_id: Calendar ID (defaults to 'primary')
    
    Returns:
        Updated event response
    """
    service = get_calendar_service()
    event = service.events().update(calendarId=calendar_id, eventId=event_id, body=event_details).execute()
    return event


def delete_calendar_event(event_id, calendar_id='primary'):
    """
    Delete a calendar event.
    
    Args:
        user_email: The email of the user to impersonate
        event_id: The ID of the event to delete
        calendar_id: Calendar ID (defaults to 'primary')
    
    Returns:
        None (empty response on success)
    """
    service = get_calendar_service()
    service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
    return {"status": "deleted", "event_id": event_id}