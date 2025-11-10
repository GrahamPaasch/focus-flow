#!/usr/bin/env python3
"""Quick setup script to connect real data sources."""

import os
import sys

def check_env_var(name, description):
    """Check if an environment variable is set."""
    value = os.getenv(name)
    if value:
        print(f"  ✓ {name} is set")
        return True
    else:
        print(f"  ✗ {name} is NOT set - {description}")
        return False

def main():
    print("=" * 60)
    print("🔌 REAL DATA SOURCE SETUP CHECK")
    print("=" * 60)
    
    print("\n📊 TELEMETRY SOURCES (Optional - router works without these)")
    print("-" * 60)
    
    has_pagerduty = False
    has_jira = False
    has_calendar = False
    
    print("\n1️⃣  PagerDuty Integration:")
    pd_token = check_env_var("PAGERDUTY_API_TOKEN", "Get from PagerDuty > Configuration > API Access")
    pd_user = check_env_var("PAGERDUTY_USER_ID", "From your profile URL")
    has_pagerduty = pd_token and pd_user
    
    print("\n2️⃣  JIRA Integration:")
    jira_server = check_env_var("JIRA_SERVER", "e.g., https://yourcompany.atlassian.net")
    jira_email = check_env_var("JIRA_EMAIL", "Your JIRA email")
    jira_token = check_env_var("JIRA_API_TOKEN", "Create at id.atlassian.com/manage/api-tokens")
    has_jira = jira_server and jira_email and jira_token
    
    print("\n3️⃣  Google Calendar Integration:")
    calendar_creds = check_env_var("GOOGLE_CALENDAR_CREDENTIALS", "Path to credentials.json")
    has_calendar = calendar_creds
    
    print("\n" + "=" * 60)
    print("📨 ALERT SOURCES (How to send real alerts)")
    print("=" * 60)
    
    print("\nThe webhook server is running at: http://localhost:5000")
    print("\nConfigure your monitoring systems to POST to these URLs:")
    print("  • Datadog:     http://localhost:5000/webhook/datadog")
    print("  • PagerDuty:   http://localhost:5000/webhook/pagerduty")
    print("  • Prometheus:  http://localhost:5000/webhook/prometheus")
    print("  • AI Model:    http://localhost:5000/webhook/ai_model")
    
    print("\n" + "=" * 60)
    print("🚀 QUICK START OPTIONS")
    print("=" * 60)
    
    print("\n📍 Option 1: Test with curl (works right now)")
    print("-" * 60)
    print("curl -X POST http://localhost:5000/webhook/datadog \\")
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"id": "123", "title": "Production DB slow", "priority": "P1", "alert_type": "error"}\'')
    
    print("\n📍 Option 2: Install dependencies for real telemetry")
    print("-" * 60)
    print("pip install requests google-auth-oauthlib google-api-python-client python-dateutil")
    
    print("\n📍 Option 3: Set environment variables")
    print("-" * 60)
    print("# Add to ~/.bashrc or ~/.zshrc:")
    print('export PAGERDUTY_API_TOKEN="your-token-here"')
    print('export PAGERDUTY_USER_ID="P123ABC"')
    print('export JIRA_SERVER="https://yourcompany.atlassian.net"')
    print('export JIRA_EMAIL="you@company.com"')
    print('export JIRA_API_TOKEN="your-jira-token"')
    print('export GOOGLE_CALENDAR_CREDENTIALS="/path/to/credentials.json"')
    
    print("\n📍 Option 4: ngrok for external webhooks")
    print("-" * 60)
    print("# Install ngrok: https://ngrok.com/download")
    print("ngrok http 5000")
    print("# Use the https URL ngrok gives you in your webhook configs")
    
    print("\n" + "=" * 60)
    print("📝 WHAT HAPPENS NOW")
    print("=" * 60)
    
    if has_pagerduty:
        print("\n✅ PagerDuty: The router will track your active incidents and recent pages")
    
    if has_jira:
        print("✅ JIRA: The router will monitor your assigned ticket count")
    
    if has_calendar:
        print("✅ Calendar: The router will see when you're in meetings")
    
    if not (has_pagerduty or has_jira or has_calendar):
        print("\n⚠️  No telemetry sources configured (this is fine!)")
        print("   The router uses default values for operator load.")
        print("   It will still route alerts intelligently based on:")
        print("   • Task urgency (SLO risk, severity)")
        print("   • AI confidence levels")
        print("   • Queue depth")
    
    print("\n" + "=" * 60)
    print("🎯 RECOMMENDED NEXT STEP")
    print("=" * 60)
    
    print("\n1. Open the dashboard (dashboard.html)")
    print("2. Send a test alert using the form")
    print("3. Watch it get routed!")
    print("\nOr send a real alert with curl (command above)")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
