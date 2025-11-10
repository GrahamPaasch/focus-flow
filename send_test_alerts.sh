#!/bin/bash
# Send realistic test alerts to simulate real monitoring data

echo "🚀 Sending realistic test alerts to the dashboard..."
echo ""

# Alert 1: Critical production issue
echo "1️⃣  Sending CRITICAL alert (should go IMMEDIATE)..."
curl -s -X POST http://localhost:5000/webhook/pagerduty \
  -H "Content-Type: application/json" \
  -d '{
    "incident": {
      "id": "INC-'$(date +%s)'",
      "title": "Payment API returning 503 errors - customers cannot checkout",
      "urgency": "high",
      "status": "triggered"
    }
  }' | jq -r '.results[0] | "   → Routed to: \(.strategy | ascii_upcase) (priority: \(.priority))"'

sleep 1

# Alert 2: High confidence AI recommendation
echo ""
echo "2️⃣  Sending AI prediction (should go AUTO)..."
curl -s -X POST http://localhost:5000/webhook/ai_model \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "pred-'$(date +%s)'",
    "predicted_action": "scale_up_web_servers",
    "confidence": 0.94,
    "severity": "low",
    "estimated_impact_minutes": 5,
    "explanation": "Traffic trending up 15%, recommend adding 2 instances"
  }' | jq -r '.results[0] | "   → Routed to: \(.strategy | ascii_upcase) (priority: \(.priority))"'

sleep 1

# Alert 3: Medium priority warning
echo ""
echo "3️⃣  Sending WARNING alert (should go BATCH)..."
curl -s -X POST http://localhost:5000/webhook/datadog \
  -H "Content-Type: application/json" \
  -d '{
    "id": "'$(date +%s)'",
    "title": "Database connection pool at 75% capacity",
    "priority": "P3",
    "alert_type": "warning"
  }' | jq -r '.results[0] | "   → Routed to: \(.strategy | ascii_upcase) (priority: \(.priority))"'

sleep 1

# Alert 4: Multiple Prometheus alerts
echo ""
echo "4️⃣  Sending Prometheus alerts (2 alerts)..."
curl -s -X POST http://localhost:5000/webhook/prometheus \
  -H "Content-Type: application/json" \
  -d '{
    "alerts": [
      {
        "status": "firing",
        "labels": {
          "alertname": "HighMemoryUsage",
          "severity": "warning",
          "instance": "web-01"
        },
        "annotations": {
          "summary": "Memory usage 82% on web-01"
        }
      },
      {
        "status": "firing",
        "labels": {
          "alertname": "DiskSpaceLow",
          "severity": "critical",
          "instance": "storage-01"
        },
        "annotations": {
          "summary": "Disk space below 8% on storage-01"
        }
      }
    ]
  }' | jq -r '.results[] | "   → \(.strategy | ascii_upcase): Task \(.task_id)"'

echo ""
echo "✅ Done! Check the dashboard to see how alerts were routed."
echo ""
echo "Current queue status:"
curl -s http://localhost:5000/queue | jq '{
  total: .total,
  immediate: (.by_strategy.immediate | length),
  batch: (.by_strategy.batch | length),
  auto_handled: "Auto alerts dont appear in queue"
}'
