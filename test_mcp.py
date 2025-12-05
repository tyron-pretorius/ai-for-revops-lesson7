"""
Test script for the RevOps MCP Server
Run with: python test_mcp.py

Requires the MCP server to be running on port 8000:
    python mcp_server.py
"""

import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000/"
API_KEY = os.getenv("MCP_API_KEY", "")

# Headers for authentication
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}


def print_header(title):
    """Print a formatted section header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(name, result, success=True):
    """Print a formatted result."""
    status = "✅" if success else "❌"
    print(f"\n{status} {name}")
    print("-" * 40)
    if isinstance(result, dict):
        print(json.dumps(result, indent=2, default=str))
    elif hasattr(result, '__dict__'):
        print(json.dumps(result.__dict__, indent=2, default=str))
    else:
        print(result)


async def run_mcp_tests():
    """Run all MCP tests using the official client."""
    print("\n" + "=" * 60)
    print("  RevOps MCP Server Test Suite")
    print("=" * 60)
    print(f"\nServer URL: {BASE_URL}")
    print(f"API Key: {'Set' if API_KEY else 'Not set (may cause auth errors)'}")
    
    try:
        print("\n🔄 Connecting to MCP server...")
        async with streamablehttp_client(BASE_URL, headers=HEADERS) as (read_stream, write_stream, _):
            print("🔄 HTTP connection established, creating session...")
            async with ClientSession(read_stream, write_stream) as session:
                print("🔄 Session created, initializing...")
                # Initialize the session
                await session.initialize()
                print("\n✅ Connected to MCP server successfully!")
                
                # List available tools
                print_header("Available Tools")
                tools_result = await session.list_tools()
                print(f"\nFound {len(tools_result.tools)} tools:\n")
                for tool in tools_result.tools:
                    print(f"  • {tool.name}: {tool.description[:60]}...")
                
                # Run interactive tests
                await run_interactive_tests(session)
                
    except Exception as e:
        import traceback
        print(f"\n❌ Failed to connect to MCP server: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\nMake sure the server is running: python mcp_server.py")
        return


async def run_interactive_tests(session: ClientSession):
    """Run interactive tests for each tool."""
    
    print("\n" + "=" * 60)
    print("  Interactive Tests")
    print("=" * 60)
    
    # Test Gmail
    await test_send_email(session)
    
    # Test Calendar
    await test_calendar_free_busy(session)
    created_event_id = await test_create_calendar_event(session)
    if created_event_id:
        await test_update_calendar_event(session, created_event_id)
        await test_delete_calendar_event(session, created_event_id)
    
    # Test Salesforce
    await test_find_contact_or_lead(session)
    created_lead_id = await test_create_lead(session)
    if created_lead_id:
        await test_log_task(session, created_lead_id)
    
    print("\n" + "=" * 60)
    print("  Test Suite Complete!")
    print("=" * 60 + "\n")


async def call_tool(session: ClientSession, tool_name: str, arguments: dict):
    """Call an MCP tool and return the result."""
    try:
        result = await session.call_tool(tool_name, arguments)
        # Parse the result content
        if result.content and len(result.content) > 0:
            text_content = result.content[0].text
            try:
                return {"success": True, "data": json.loads(text_content)}
            except json.JSONDecodeError:
                return {"success": True, "data": text_content}
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def test_send_email(session: ClientSession):
    """Test the send_email function."""
    print_header("Testing Gmail: send_email")
    
    test_email = input("\nEnter email address to send test email to (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⏭️  Skipped send_email test")
        return
    
    result = await call_tool(session, "send_email", {
        "to": test_email,
        "subject": "MCP Test Email",
        "message_text": f"This is a test email sent from the MCP server at {datetime.now().isoformat()}",
        "cc": "",
        "reply_to": "",
        "is_html": False
    })
    
    print_result("send_email", result, result.get("success", False))


async def test_calendar_free_busy(session: ClientSession):
    """Test the get_calendar_free_busy function."""
    print_header("Testing Calendar: get_calendar_free_busy")
    
    time_min = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    time_max = (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
    
    result = await call_tool(session, "get_calendar_free_busy", {
        "time_min": time_min,
        "time_max": time_max
    })
    
    print_result("get_calendar_free_busy", result, result.get("success", False))


async def test_create_calendar_event(session: ClientSession) -> str | None:
    """Test the create_calendar_event function."""
    print_header("Testing Calendar: create_calendar_event")
    
    confirm = input("\nCreate a test calendar event? (y/n): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipped create_calendar_event test")
        return None
    
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=10, minute=0, second=0, microsecond=0)
    end_time = tomorrow.replace(hour=11, minute=0, second=0, microsecond=0)
    
    event_details = {
        "summary": "MCP Test Event",
        "description": "This is a test event created by the MCP test script",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "Africa/Johannesburg"
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "Africa/Johannesburg"
        }
    }
    
    result = await call_tool(session, "create_calendar_event", {
        "event_details": event_details,
        "calendar_id": "primary"
    })
    
    print_result("create_calendar_event", result, result.get("success", False))
    
    # Extract event ID for subsequent tests
    if result.get("success") and isinstance(result.get("data"), dict):
        return result["data"].get("id")
    return None


async def test_update_calendar_event(session: ClientSession, event_id: str):
    """Test the update_calendar_event function."""
    print_header("Testing Calendar: update_calendar_event")
    
    if not event_id:
        event_id = input("\nEnter event ID to update (or press Enter to skip): ").strip()
    
    if not event_id:
        print("⏭️  Skipped update_calendar_event test")
        return
    
    event_details = {
        "summary": "MCP Test Event (Updated)",
        "description": f"Updated at {datetime.now().isoformat()}"
    }
    
    result = await call_tool(session, "update_calendar_event", {
        "event_id": event_id,
        "event_details": event_details,
        "calendar_id": "primary"
    })
    
    print_result("update_calendar_event", result, result.get("success", False))


async def test_delete_calendar_event(session: ClientSession, event_id: str):
    """Test the delete_calendar_event function."""
    print_header("Testing Calendar: delete_calendar_event")
    
    if not event_id:
        event_id = input("\nEnter event ID to delete (or press Enter to skip): ").strip()
    
    if not event_id:
        print("⏭️  Skipped delete_calendar_event test")
        return
    
    confirm = input(f"Delete event {event_id}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipped delete_calendar_event test")
        return
    
    result = await call_tool(session, "delete_calendar_event", {
        "event_id": event_id,
        "calendar_id": "primary"
    })
    
    print_result("delete_calendar_event", result, result.get("success", False))


async def test_find_contact_or_lead(session: ClientSession):
    """Test the find_salesforce_contact_or_lead function."""
    print_header("Testing Salesforce: find_salesforce_contact_or_lead")
    
    email = input("\nEnter email to search (or press Enter to skip): ").strip()
    phone = input("Enter phone to search (or press Enter to skip): ").strip()
    
    if not email and not phone:
        print("⏭️  Skipped find_salesforce_contact_or_lead test")
        return
    
    args = {}
    if email:
        args["email"] = email
    if phone:
        args["phone"] = phone
    
    result = await call_tool(session, "find_salesforce_contact_or_lead", args)
    
    print_result("find_salesforce_contact_or_lead", result, result.get("success", False))


async def test_create_lead(session: ClientSession) -> str | None:
    """Test the create_salesforce_lead function."""
    print_header("Testing Salesforce: create_salesforce_lead")
    
    confirm = input("\nCreate a test Lead in Salesforce? (y/n): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipped create_salesforce_lead test")
        return None
    
    fields = {
        "FirstName": "MCP",
        "LastName": "Test Lead",
        "Company": "MCP Test Company",
        "Email": f"mcp.test.{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com",
        "Phone": "+1234567890"
    }
    
    result = await call_tool(session, "create_salesforce_lead", {
        "fields": fields
    })
    
    print_result("create_salesforce_lead", result, result.get("success", False))
    
    # Extract lead ID for subsequent tests
    if result.get("success") and isinstance(result.get("data"), dict):
        return result["data"].get("id")
    return None


async def test_log_task(session: ClientSession, person_id: str = None):
    """Test the log_salesforce_task function."""
    print_header("Testing Salesforce: log_salesforce_task")
    
    if not person_id:
        person_id = input("\nEnter Contact/Lead ID to log task against (or press Enter to skip): ").strip()
    
    if not person_id:
        print("⏭️  Skipped log_salesforce_task test")
        return
    
    result = await call_tool(session, "log_salesforce_task", {
        "person_id": person_id,
        "subject": "MCP Test Task",
        "body": f"This is a test task created by MCP at {datetime.now().isoformat()}",
        "direction": "Inbound"
    })
    
    print_result("log_salesforce_task", result, result.get("success", False))


async def run_quick_test():
    """Run only non-destructive tests."""
    print("\n" + "=" * 60)
    print("  Quick Test (Non-Destructive)")
    print("=" * 60)
    print(f"\nServer URL: {BASE_URL}")
    
    try:
        print("\n🔄 Connecting to MCP server...")
        async with streamablehttp_client(BASE_URL, headers=HEADERS) as (read_stream, write_stream, _):
            print("🔄 HTTP connection established, creating session...")
            async with ClientSession(read_stream, write_stream) as session:
                print("🔄 Session created, initializing...")
                await session.initialize()
                print("\n✅ Connected to MCP server successfully!")
                
                # List tools
                print_header("Available Tools")
                tools_result = await session.list_tools()
                print(f"\nFound {len(tools_result.tools)} tools:\n")
                for tool in tools_result.tools:
                    print(f"  • {tool.name}")
                
                # Test calendar free/busy (read-only)
                print_header("Testing Calendar: get_calendar_free_busy")
                time_min = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                time_max = (datetime.now(timezone.utc) + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
                
                result = await call_tool(session, "get_calendar_free_busy", {
                    "time_min": time_min,
                    "time_max": time_max
                })
                print_result("get_calendar_free_busy", result, result.get("success", False))
                
    except Exception as e:
        import traceback
        print(f"\n❌ Failed to connect: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\nMake sure the server is running: python mcp_server.py")
    
    print("\n✅ Quick test complete!\n")


if __name__ == "__main__":
    print("\nSelect test mode:")
    print("  1. Quick test (non-destructive, no prompts)")
    print("  2. Full interactive test (may create/modify data)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        asyncio.run(run_quick_test())
    else:
        asyncio.run(run_mcp_tests())
