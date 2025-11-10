#!/usr/bin/env python3
"""Real-world integration example with live data sources."""

import time
from datetime import timedelta

from cognitive_router import (
    TelemetryCollector,
    AttentionModel,
    RouterService,
    RoutingPolicy,
    QueueDepthContextProvider,
)
from cognitive_router.telemetry_sources import CombinedTelemetrySource
from cognitive_router.alert_sources import GenericWebhookHandler


def main():
    print("=== Live Cognitive Router Integration ===\n")
    
    # Step 1: Set up telemetry with real data sources
    print("Setting up telemetry collection...")
    telemetry_collector = TelemetryCollector(window=timedelta(minutes=30))
    telemetry_source = CombinedTelemetrySource()
    
    # Collect initial telemetry sample
    print("Collecting system telemetry...")
    try:
        sample = telemetry_source.collect_sample()
        telemetry_collector.record_sample(sample)
        print(f"  ✓ Idle time: {sample.idle_minutes:.1f} minutes")
        print(f"  ✓ Active incidents: {sample.active_tasks}")
        print(f"  ✓ Queue depth: {sample.queue_depth}")
        print(f"  ✓ Calendar blocks: {sample.calendar_block_minutes:.0f} minutes")
        print(f"  ✓ Recent pages: {sample.pager_events}")
    except Exception as e:
        print(f"  ⚠ Telemetry collection failed (using defaults): {e}")
        # Use a default sample if real telemetry fails
        from cognitive_router.telemetry import TelemetrySample
        from datetime import datetime, UTC
        sample = TelemetrySample(
            timestamp=datetime.now(UTC),
            keystrokes_per_min=100,
            mouse_moves_per_min=150,
            window_focus_changes=2,
            pager_events=0,
            active_tasks=0,
            idle_minutes=5.0,
        )
        telemetry_collector.record_sample(sample)
    
    # Step 2: Set up the router
    print("\nSetting up cognitive router...")
    attention_model = AttentionModel()
    policy = RoutingPolicy(
        slo_weight=0.4,
        uncertainty_weight=0.25,
        immediate_threshold=0.75,
        batch_threshold=0.45,
    )
    router = RouterService(telemetry_collector, attention_model, policy)
    
    # Step 3: Add context providers
    work_queue = []
    queue_provider = QueueDepthContextProvider(queue_length_fn=lambda: len(work_queue))
    router.register_context_provider(queue_provider)
    
    # Step 4: Set up webhook handler for incoming alerts
    webhook_handler = GenericWebhookHandler()
    
    print("✓ Router ready\n")
    
    # Step 5: Simulate receiving alerts from various sources
    print("=== Simulating Incoming Alerts ===\n")
    
    # Example 1: Datadog alert
    datadog_payload = {
        "id": "12345",
        "title": "High database connection pool usage on prod-db-01",
        "priority": "P2",
        "alert_type": "warning",
        "alert_transition": "triggered",
    }
    
    print("📨 Datadog webhook received")
    tasks = webhook_handler.handle_webhook('datadog', datadog_payload)
    for task in tasks:
        work_item = router.handle_task(task)
        print(f"  → {work_item.route_strategy.upper()}: {task.explanation}")
        print(f"     Priority: {work_item.priority:.2f}, Confidence: {task.model_confidence:.0%}")
        if work_item.route_strategy != "auto":
            work_queue.append(work_item)
    
    print()
    
    # Example 2: PagerDuty incident
    pagerduty_payload = {
        "incident": {
            "id": "INC-789",
            "title": "Payment API responding with 503 errors",
            "urgency": "high",
            "status": "triggered",
        }
    }
    
    print("📨 PagerDuty webhook received")
    tasks = webhook_handler.handle_webhook('pagerduty', pagerduty_payload)
    for task in tasks:
        work_item = router.handle_task(task)
        print(f"  → {work_item.route_strategy.upper()}: {task.explanation}")
        print(f"     Priority: {work_item.priority:.2f}, Confidence: {task.model_confidence:.0%}")
        if work_item.route_strategy != "auto":
            work_queue.append(work_item)
    
    print()
    
    # Example 3: AI model prediction
    ai_prediction = {
        "prediction_id": "pred-456",
        "predicted_action": "scale_up_workers",
        "confidence": 0.92,
        "severity": "low",
        "estimated_impact_minutes": 8,
        "explanation": "Queue depth trending up, recommend scaling worker pool",
        "sensitive_data": False,
    }
    
    print("📨 AI model prediction received")
    tasks = webhook_handler.handle_webhook('ai_model', ai_prediction)
    for task in tasks:
        work_item = router.handle_task(task)
        print(f"  → {work_item.route_strategy.upper()}: {task.explanation}")
        print(f"     Priority: {work_item.priority:.2f}, Confidence: {task.model_confidence:.0%}")
        if work_item.route_strategy != "auto":
            work_queue.append(work_item)
    
    print()
    
    # Example 4: Prometheus alerts (multiple)
    prometheus_payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "HighMemoryUsage",
                    "severity": "warning",
                    "instance": "web-server-03"
                },
                "annotations": {
                    "summary": "Memory usage above 85% on web-server-03"
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
                    "summary": "Disk space below 5% on storage-01"
                }
            }
        ]
    }
    
    print("📨 Prometheus AlertManager webhook received (2 alerts)")
    tasks = webhook_handler.handle_webhook('prometheus', prometheus_payload)
    for task in tasks:
        work_item = router.handle_task(task)
        print(f"  → {work_item.route_strategy.upper()}: {task.explanation}")
        print(f"     Priority: {work_item.priority:.2f}, Confidence: {task.model_confidence:.0%}")
        if work_item.route_strategy != "auto":
            work_queue.append(work_item)
    
    # Summary
    print(f"\n=== Summary ===")
    print(f"Total alerts processed: {len(tasks) + 3}")
    print(f"Current queue depth: {len(work_queue)}")
    print(f"\nQueue breakdown:")
    
    immediate = [w for w in work_queue if w.route_strategy == "immediate"]
    batch = [w for w in work_queue if w.route_strategy == "batch"]
    park = [w for w in work_queue if w.route_strategy == "park"]
    
    print(f"  IMMEDIATE (needs attention now): {len(immediate)}")
    print(f"  BATCH (review when available): {len(batch)}")
    print(f"  PARK (defer for later): {len(park)}")
    
    print("\n💡 Next steps:")
    print("  1. Set environment variables for real integrations:")
    print("     - PAGERDUTY_API_TOKEN, PAGERDUTY_USER_ID")
    print("     - JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN")
    print("     - GOOGLE_CALENDAR_CREDENTIALS (path to credentials.json)")
    print("  2. Install optional dependencies: pip install requests google-auth-oauthlib")
    print("  3. Set up webhook endpoints to receive real alerts")
    print("  4. Configure routing sinks to actually page/queue/auto-resolve")


if __name__ == "__main__":
    main()
