# Google Calendar API Setup Instructions

This guide assumes you have already completed the Gmail Service Account setup. Here we'll add the necessary permissions to work with Google Calendar API for:
- Looking up free/busy times
- Creating calendar events
- Modifying/deleting calendar events

## Prerequisites

- Completed Gmail Service Account setup
- Existing service account with JSON key file
- Access to Google Workspace Admin Console

## Step-by-Step Instructions

### Step 1: Enable Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your existing project (the one with the Gmail service account)
3. Go to **APIs & Services** > **Library**
4. Search for "Google Calendar API"
5. Click on "Google Calendar API" from the results
6. Click **"Enable"**

### Step 2: Add Calendar Scopes to Domain-Wide Delegation

1. Go to [Google Workspace Admin Console](https://admin.google.com/)
2. Navigate to **Security** > **API Controls** > **Domain-wide Delegation**
3. Find your existing service account entry (the one you created for Gmail)
4. Click **"Edit"** (pencil icon)
5. In the **OAuth Scopes** field, add the Calendar scopes alongside your existing Gmail scope:

   ```
   https://www.googleapis.com/auth/gmail.send,https://www.googleapis.com/auth/calendar.events,https://www.googleapis.com/auth/calendar.freebusy
   ```

   **Note:** Scopes should be comma-separated with no spaces.

6. Click **"Authorize"**

### Understanding the Calendar Scopes

| Scope | Purpose |
|-------|---------|
| `https://www.googleapis.com/auth/calendar.freebusy` | Query free/busy information (minimal access) |
| `https://www.googleapis.com/auth/calendar.events` | Create, modify, and delete events on all calendars |
| `https://www.googleapis.com/auth/calendar.readonly` | Read-only access to calendars and events |
| `https://www.googleapis.com/auth/calendar` | Full access to all calendar operations |

**Recommended minimum scopes for your use case:**
- `calendar.freebusy` - For checking availability
- `calendar.events` - For creating, updating, and deleting events

### Step 3: Test the Setup

Test if the Calendar API is working correctly:

```python
from calendar_functions import get_calendar_service, get_free_busy
from datetime import datetime, timedelta

# Test service connection
service = get_calendar_service()
print("Calendar service configured successfully!")

# Test free/busy lookup
time_min = datetime.utcnow().isoformat() + 'Z'
time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

free_busy = get_free_busy(time_min, time_max)
print(f"Free/busy data: {free_busy}")
```

## Important Notes

⚠️ **Scope Changes Take Time:**
- After updating scopes in the Admin Console, changes can take up to 24 hours to propagate
- Typically it's faster (5-15 minutes), but be patient if you encounter permission errors immediately after setup

⚠️ **Calendar IDs:**
- `'primary'` refers to the user's primary calendar
- The user's email address also works as their primary calendar ID
- Shared calendars have unique IDs (found in Calendar Settings > Integrate calendar)

⚠️ **Time Zones:**
- Always specify time zones in event creation to avoid confusion
- Use IANA time zone format (e.g., `America/New_York`, `Europe/London`)

## Troubleshooting

**Error: "Insufficient Permission" or "Access denied"**
- Verify the Calendar API is enabled in Google Cloud Console
- Check that the new scopes are added correctly in Domain-Wide Delegation
- Ensure there are no typos in the scopes (must match exactly)
- Wait a few minutes for scope changes to propagate

**Error: "Calendar API has not been used in project"**
- Go to Google Cloud Console and enable the Calendar API
- Make sure you're in the correct project

**Error: "Invalid time format"**
- Ensure times are in ISO 8601 format
- Include the 'Z' suffix for UTC times or specify a timeZone

**Error: "Not Found" when modifying/deleting events**
- Verify the event_id is correct
- Ensure you're using the correct calendar_id
- Check that the user has access to the calendar

## Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar/api)
- [Calendar API Reference](https://developers.google.com/calendar/api/v3/reference)
- [Free/Busy Query Reference](https://developers.google.com/calendar/api/v3/reference/freebusy/query)
- [Events Resource Reference](https://developers.google.com/calendar/api/v3/reference/events)

