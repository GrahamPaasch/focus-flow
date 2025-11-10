# 🚀 HOW TO USE THIS

## The Simple Way (Web Browser)

1. **Start the server:**
```bash
python webhook_server.py
```

2. **Open the dashboard in your browser:**
```bash
# Just double-click this file:
dashboard.html

# Or open manually: file:///mnt/e/focus-flow/dashboard.html
```

3. **That's it!** You'll see:
   - 📊 Real-time stats (queue depth, alerts processed)
   - 🎯 Routing decisions (Immediate/Batch/Auto/Park)
   - 📨 Send test alerts with the form
   - 📈 Live telemetry data

## Getting Real Data Into It

### Method 1: Use the Dashboard Form (Easiest)

1. Open `dashboard.html` in your browser
2. Use the form at the top:
   - Select alert source (Datadog, PagerDuty, etc.)
   - Pick severity (P1 = Critical, P5 = Info)
   - Type a message like "Database is slow"
   - Click "Send Alert"
3. Watch it appear in the queue below!

### Method 2: Send Alerts from Terminal

Run this while the server is running:
```bash
./send_test_alerts.sh
```

Or manually:
```bash
curl -X POST http://localhost:5000/webhook/datadog \
  -H "Content-Type: application/json" \
  -d '{"id": "123", "title": "Production DB slow", "priority": "P1", "alert_type": "error"}'
```

### Method 3: Connect Your Real Monitoring Systems

Point Datadog/PagerDuty/Prometheus webhooks to:
```
http://your-server-ip:5000/webhook/datadog
http://your-server-ip:5000/webhook/pagerduty
http://your-server-ip:5000/webhook/prometheus
```

**For external access** (webhooks from the internet):
```bash
# Install ngrok from https://ngrok.com
ngrok http 5000

# Use the https URL it gives you (e.g., https://abc123.ngrok.io/webhook/datadog)
```

### Method 4: Enable Real Telemetry (Optional)

To track your actual activity, queue depth, and calendar:

```bash
# Check what's missing:
python setup_real_data.py

# Install dependencies:
pip install requests google-auth-oauthlib google-api-python-client

# Set environment variables:
export PAGERDUTY_API_TOKEN="your-token"
export PAGERDUTY_USER_ID="P123ABC"
export JIRA_SERVER="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your-jira-token"

# Restart the server
python webhook_server.py
```

## What You'll See

The dashboard shows how the AI routes alerts:
- **🚨 IMMEDIATE** (Red) = Page the human NOW
- **📋 BATCH** (Orange) = Queue for review later  
- **🤖 AUTO** (Green) = AI handles it automatically
- **⏸️ PARK** (Gray) = Defer until less busy

## Try It Right Now

1. Make sure server is running: `python webhook_server.py`
2. Open `dashboard.html` in your browser
3. In the form, select "PagerDuty" + "P1 - Critical"
4. Type: "Payment system is down"
5. Click "Send Alert"
6. **Watch it route to IMMEDIATE!**

## Troubleshooting

**"Server Not Running" in dashboard?**
→ Run `python webhook_server.py` in a terminal

**Permission denied errors?**
→ Ignore them - the router still works with defaults

**Nothing happens when I send alerts?**
→ Check the terminal running webhook_server.py for logs

**Want to see what the router decided?**
→ Look at the terminal logs or the queue in the dashboard
