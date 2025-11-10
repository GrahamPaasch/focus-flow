# Real-World Integration Guide

This guide shows you how to connect the cognitive router to real data sources and alerting systems.

## Quick Test (No Setup Required)

```bash
python live_integration_example.py
```

This simulates receiving webhooks from Datadog, PagerDuty, Prometheus, and AI models. Works immediately without any configuration.

## Option 1: Webhook Server (Recommended for Production)

### Setup

1. **Install Flask**:
```bash
pip install flask
```

2. **Start the server**:
```bash
python webhook_server.py
```

The server runs on `http://localhost:5000` with these endpoints:

- `POST /webhook/<source>` - Receive alerts from monitoring systems
- `GET /queue` - View current work queue
- `GET /telemetry` - View operator load metrics
- `GET /policy` - View routing policy
- `POST /policy` - Update routing policy dynamically

### Configure Your Monitoring Systems

#### Datadog
In Datadog, go to **Integrations → Webhooks** and add:
```
URL: http://your-server:5000/webhook/datadog
Payload: (use default)
```

#### PagerDuty
In PagerDuty, go to **Configuration → Extensions** and create a webhook:
```
URL: http://your-server:5000/webhook/pagerduty
```

#### Prometheus AlertManager
Edit `alertmanager.yml`:
```yaml
receivers:
  - name: 'cognitive-router'
    webhook_configs:
      - url: 'http://your-server:5000/webhook/prometheus'
```

#### Test with curl
```bash
# Send a test Datadog alert
curl -X POST http://localhost:5000/webhook/datadog \
  -H "Content-Type: application/json" \
  -d '{
    "id": "123",
    "title": "High CPU on prod-server",
    "priority": "P1",
    "alert_type": "error"
  }'

# Check the queue
curl http://localhost:5000/queue

# View telemetry
curl http://localhost:5000/telemetry
```

## Option 2: Real Telemetry Sources

### System Activity Monitoring (Linux)

The router can monitor actual system activity. Install optional tools:

```bash
# For idle time detection
sudo apt install xprintidle

# For window management
sudo apt install wmctrl
```

### PagerDuty Integration

1. Get your API token from PagerDuty **Configuration → API Access**
2. Get your user ID from your profile URL
3. Set environment variables:

```bash
export PAGERDUTY_API_TOKEN="your-token-here"
export PAGERDUTY_USER_ID="P123ABC"
```

### JIRA Integration

1. Create an API token at https://id.atlassian.com/manage/api-tokens
2. Set environment variables:

```bash
export JIRA_SERVER="https://yourcompany.atlassian.net"
export JIRA_EMAIL="you@company.com"
export JIRA_API_TOKEN="your-token-here"
```

### Google Calendar Integration

1. Enable Google Calendar API at https://console.cloud.google.com
2. Download OAuth credentials
3. Set path:

```bash
export GOOGLE_CALENDAR_CREDENTIALS="/path/to/credentials.json"
```

4. Install dependencies:
```bash
pip install google-auth-oauthlib google-api-python-client requests python-dateutil
```

## Option 3: Python API Integration

Embed the router directly in your application:

```python
from cognitive_router import (
    TelemetryCollector,
    AttentionModel,
    RouterService,
    RoutingPolicy,
)
from cognitive_router.alert_sources import DatadogAlertSource
from datetime import timedelta

# Set up router
telemetry = TelemetryCollector(window=timedelta(minutes=30))
router = RouterService(telemetry, AttentionModel(), RoutingPolicy())

# Register handlers
def handle_immediate(work_item):
    # Send to PagerDuty, Slack, etc.
    print(f"URGENT: {work_item.task.explanation}")

router.register_sink("immediate", handle_immediate)

# Process incoming alert
datadog_webhook = {"id": "123", "title": "DB down", "priority": "P1"}
task = DatadogAlertSource.from_webhook(datadog_webhook)
work_item = router.handle_task(task)
# Router automatically calls registered sinks based on strategy
```

## Customizing Alert Parsers

Edit `src/cognitive_router/alert_sources.py` to customize how alerts map to task properties:

```python
class YourCustomAlertSource:
    @staticmethod
    def from_webhook(payload):
        return TaskIntent(
            task_id=payload['alert_id'],
            severity=payload['severity'],  # 1-5
            slo_risk_minutes=payload['impact'],
            model_confidence=payload.get('confidence', 0.7),
            explanation=payload['message'],
            sensitivity_tag='standard',
            source='your_system',
        )
```

Then register it:
```python
webhook_handler.handlers['your_system'] = YourCustomAlertSource.from_webhook
```

## Tuning the Routing Policy

Update policy weights based on your team's preferences:

```bash
curl -X POST http://localhost:5000/policy \
  -H "Content-Type: application/json" \
  -d '{
    "slo_weight": 0.5,
    "uncertainty_weight": 0.2,
    "immediate_threshold": 0.8,
    "batch_threshold": 0.5
  }'
```

Or in code:
```python
policy = RoutingPolicy(
    slo_weight=0.5,              # Prioritize SLO risk more
    uncertainty_weight=0.2,       # Care less about AI confidence
    immediate_threshold=0.8,      # Higher bar for immediate alerts
    batch_threshold=0.5,          # More things go to batch
)
```

## Production Deployment

### Using Docker

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY . /app
RUN pip install -e . && pip install flask requests

CMD ["python", "webhook_server.py"]
```

Build and run:
```bash
docker build -t cognitive-router .
docker run -p 5000:5000 -e PAGERDUTY_API_TOKEN=$PAGERDUTY_API_TOKEN cognitive-router
```

### Using systemd

Create `/etc/systemd/system/cognitive-router.service`:
```ini
[Unit]
Description=Cognitive Bandwidth Router
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/cognitive-router
Environment="PAGERDUTY_API_TOKEN=your-token"
ExecStart=/usr/bin/python3 /opt/cognitive-router/webhook_server.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable cognitive-router
sudo systemctl start cognitive-router
```

## Monitoring the Router

Check router health:
```bash
curl http://localhost:5000/health
```

View current telemetry:
```bash
curl http://localhost:5000/telemetry | jq
```

Monitor queue depth:
```bash
watch -n 5 'curl -s http://localhost:5000/queue | jq ".total"'
```

## Troubleshooting

**Telemetry collection fails:**
- Install optional tools: `xprintidle`, `wmctrl`
- Router will use defaults if tools aren't available

**PagerDuty integration not working:**
- Verify API token: `curl -H "Authorization: Token token=$PAGERDUTY_API_TOKEN" https://api.pagerduty.com/users/me`
- Check user ID is correct

**Webhooks not routing correctly:**
- Check payload format matches expected schema in `alert_sources.py`
- Add debug logging: `app.run(debug=True)`

**Queue keeps growing:**
- Lower thresholds to route more to AUTO
- Increase `min_confidence_for_auto` to trust AI more
- Ensure you're actually processing the queue!
