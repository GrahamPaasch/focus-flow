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

## What You'll See

The dashboard shows how the AI routes alerts:
- **🚨 IMMEDIATE** (Red) = Page the human NOW
- **📋 BATCH** (Orange) = Queue for review later  
- **🤖 AUTO** (Green) = AI handles it automatically
- **⏸️ PARK** (Gray) = Defer until less busy

## Try It

1. In the dashboard, select "Datadog" + "P1 - Critical"
2. Type something like "Database is down"
3. Click "Send Alert"
4. Watch it appear in the queue below!

## Connect Real Alerts

Point your monitoring systems (Datadog, PagerDuty, Prometheus) to:
```
http://your-server:5000/webhook/datadog
http://your-server:5000/webhook/pagerduty
http://your-server:5000/webhook/prometheus
```

See INTEGRATION_GUIDE.md for details.

## Troubleshooting

**"Server Not Running" in dashboard?**
→ Run `python webhook_server.py` in a terminal

**Permission denied errors?**
→ Ignore them - the router still works with defaults

**Nothing happens when I send alerts?**
→ Check the terminal running webhook_server.py for logs
