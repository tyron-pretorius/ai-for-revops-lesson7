"""
Test script for the RevOps MCP Server
Run with: python test_mcp.py

Requires the MCP server to be running on port 8000:
    python mcp_server.py
"""

import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configuration
BASE_URL = "http://localhost:8000"
API_KEY = os.getenv("MCP_API_KEY", "")

# Headers for MCP requests
HEADERS = {
    "Content-Type": "application/json",
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
    else:
        print(result)


def call_mcp_tool(tool_name, arguments=None):
    """
    Call an MCP tool using the JSON-RPC protocol.
    """
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments or {}
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/",
            headers=HEADERS,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if "error" in result:
                return {"success": False, "error": result["error"]}
            return {"success": True, "result": result.get("result", result)}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def test_health_endpoints():
    """Test the health and info endpoints."""
    print_header("Testing Health Endpoints")
    
    # Test /health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print_result("/health endpoint", response.json(), response.status_code == 200)
    except Exception as e:
        print_result("/health endpoint", str(e), False)
    
    # Test /info
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=10)
        print_result("/info endpoint", response.text, response.status_code == 200)
    except Exception as e:
        print_result("/info endpoint", str(e), False)


def test_list_tools():
    """List all available tools."""
    print_header("Listing Available Tools")
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(f"{BASE_URL}/", headers=HEADERS, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            tools = result.get("result", {}).get("tools", [])
            print(f"\n✅ Found {len(tools)} tools:\n")
            for tool in tools:
                print(f"  • {tool.get('name')}: {tool.get('description', 'No description')[:60]}...")
        else:
            print_result("List tools", f"HTTP {response.status_code}: {response.text}", False)
    except Exception as e:
        print_result("List tools", str(e), False)


def test_gmail_send_email():
    """Test the send_email function."""
    print_header("Testing Gmail: send_email")
    
    # WARNING: This will actually send an email!
    test_email = input("\nEnter email address to send test email to (or press Enter to skip): ").strip()
    
    if not test_email:
        print("⏭️  Skipped send_email test")
        return None
    
    result = call_mcp_tool("send_email", {
        "to": test_email,
        "subject": "MCP Test Email",
        "message_text": f"This is a test email sent from the MCP server at {datetime.now().isoformat()}",
        "cc": "",
        "reply_to": "",
        "is_html": False
    })
    
    print_result("send_email", result, result.get("success", False))
    return result


def test_calendar_free_busy():
    """Test the get_calendar_free_busy function."""
    print_header("Testing Calendar: get_calendar_free_busy")
    
    # Get free/busy for the next 7 days
    time_min = datetime.utcnow().isoformat() + "Z"
    time_max = (datetime.utcnow() + timedelta(days=7)).isoformat() + "Z"
    
    result = call_mcp_tool("get_calendar_free_busy", {
        "time_min": time_min,
        "time_max": time_max,
        "calendar_ids": None
    })
    
    print_result("get_calendar_free_busy", result, result.get("success", False))
    return result


def test_calendar_create_event():
    """Test the create_calendar_event function."""
    print_header("Testing Calendar: create_calendar_event")
    
    confirm = input("\nCreate a test calendar event? (y/n): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipped create_calendar_event test")
        return None
    
    # Create an event for tomorrow
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
    
    result = call_mcp_tool("create_calendar_event", {
        "event_details": event_details,
        "calendar_id": "primary"
    })
    
    print_result("create_calendar_event", result, result.get("success", False))
    return result


def test_calendar_update_event(event_id):
    """Test the update_calendar_event function."""
    print_header("Testing Calendar: update_calendar_event")
    
    if not event_id:
        event_id = input("\nEnter event ID to update (or press Enter to skip): ").strip()
    
    if not event_id:
        print("⏭️  Skipped update_calendar_event test")
        return None
    
    event_details = {
        "summary": "MCP Test Event (Updated)",
        "description": f"Updated at {datetime.now().isoformat()}"
    }
    
    result = call_mcp_tool("update_calendar_event", {
        "event_id": event_id,
        "event_details": event_details,
        "calendar_id": "primary"
    })
    
    print_result("update_calendar_event", result, result.get("success", False))
    return result


def test_calendar_delete_event(event_id):
    """Test the delete_calendar_event function."""
    print_header("Testing Calendar: delete_calendar_event")
    
    if not event_id:
        event_id = input("\nEnter event ID to delete (or press Enter to skip): ").strip()
    
    if not event_id:
        print("⏭️  Skipped delete_calendar_event test")
        return None
    
    confirm = input(f"Delete event {event_id}? (y/n): ").strip().lower()
    if confirm != 'y':
        print("⏭️  Skipped delete_calendar_event test")
        return None
    
    result = call_mcp_tool("delete_calendar_event", {
        "event_id": event_id,
        "calendar_id": "primary"
    })
    
    print_result("delete_calendar_event", result, result.get("success", False))
    return result


def test_salesforce_find_contact_or_lead():
    """Test the find_salesforce_contact_or_lead function."""
    print_header("Testing Salesforce: find_salesforce_contact_or_lead")
    
    email = input("\nEnter email to search (or press Enter to skip): ").strip()
    phone = input("Enter phone to search (or press Enter to skip): ").strip()
    
    if not email and not phone:
        print("⏭️  Skipped find_salesforce_contact_or_lead test")
        return None
    
    result = call_mcp_tool("find_salesforce_contact_or_lead", {
        "email": email if email else None,
        "phone": phone if phone else None
    })
    
    print_result("find_salesforce_contact_or_lead", result, result.get("success", False))
    return result


def test_salesforce_create_lead():
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
    
    result = call_mcp_tool("create_salesforce_lead", {
        "fields": fields
    })
    
    print_result("create_salesforce_lead", result, result.get("success", False))
    return result


def test_salesforce_log_task(person_id=None):
    """Test the log_salesforce_task function."""
    print_header("Testing Salesforce: log_salesforce_task")
    
    if not person_id:
        person_id = input("\nEnter Contact/Lead ID to log task against (or press Enter to skip): ").strip()
    
    if not person_id:
        print("⏭️  Skipped log_salesforce_task test")
        return None
    
    result = call_mcp_tool("log_salesforce_task", {
        "person_id": person_id,
        "subject": "MCP Test Task",
        "body": f"This is a test task created by MCP at {datetime.now().isoformat()}",
        "direction": "Inbound"
    })
    
    print_result("log_salesforce_task", result, result.get("success", False))
    return result


def run_all_tests():
    """Run all tests interactively."""
    print("\n" + "=" * 60)
    print("  RevOps MCP Server Test Suite")
    print("=" * 60)
    print(f"\nServer URL: {BASE_URL}")
    print(f"API Key: {'Set' if API_KEY else 'Not set (may cause auth errors)'}")
    
    # Test health endpoints (non-destructive)
    test_health_endpoints()
    
    # List available tools
    test_list_tools()
    
    # Test each category
    print("\n" + "=" * 60)
    print("  Interactive Tests (some will create/modify data)")
    print("=" * 60)
    
    # Gmail
    test_gmail_send_email()
    
    # Calendar
    test_calendar_free_busy()
    create_result = test_calendar_create_event()
    
    # If we created an event, offer to update and delete it
    event_id = None
    if create_result and create_result.get("success"):
        try:
            # Extract event ID from result
            result_data = create_result.get("result", {})
            if isinstance(result_data, dict):
                content = result_data.get("content", [])
                if content and isinstance(content[0], dict):
                    text = content[0].get("text", "{}")
                    event_data = json.loads(text)
                    event_id = event_data.get("id")
        except:
            pass
    
    test_calendar_update_event(event_id)
    test_calendar_delete_event(event_id)
    
    # Salesforce
    find_result = test_salesforce_find_contact_or_lead()
    lead_result = test_salesforce_create_lead()
    
    # If we created a lead, offer to log a task against it
    lead_id = None
    if lead_result and lead_result.get("success"):
        try:
            result_data = lead_result.get("result", {})
            if isinstance(result_data, dict):
                content = result_data.get("content", [])
                if content and isinstance(content[0], dict):
                    text = content[0].get("text", "{}")
                    lead_data = json.loads(text)
                    lead_id = lead_data.get("id")
        except:
            pass
    
    test_salesforce_log_task(lead_id)
    
    print("\n" + "=" * 60)
    print("  Test Suite Complete!")
    print("=" * 60 + "\n")


def run_quick_test():
    """Run only non-destructive tests."""
    print("\n" + "=" * 60)
    print("  Quick Test (Non-Destructive)")
    print("=" * 60)
    print(f"\nServer URL: {BASE_URL}")
    
    test_health_endpoints()
    test_list_tools()
    test_calendar_free_busy()
    
    print("\n✅ Quick test complete!\n")


if __name__ == "__main__":
    print("\nSelect test mode:")
    print("  1. Quick test (non-destructive, no prompts)")
    print("  2. Full interactive test (may create/modify data)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        run_quick_test()
    else:
        run_all_tests()

