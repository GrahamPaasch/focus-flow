#!/usr/bin/env python3
"""Example: Using the cognitive router in your own code."""

from datetime import UTC, datetime, timedelta
from cognitive_router import (
    TelemetryCollector,
    TelemetrySample,
    AttentionModel,
    RouterService,
    RoutingPolicy,
    TaskIntent,
    QueueDepthContextProvider,
)


def main():
    print("=== Cognitive Bandwidth Router Demo ===\n")
    
    # Step 1: Set up telemetry collector (uses 30 min window by default)
    from datetime import timedelta
    telemetry = TelemetryCollector(window=timedelta(minutes=30))
    
    # Simulate some recent operator activity
    now = datetime.now(UTC)
    for minutes_ago in [25, 20, 15, 10, 5]:
        telemetry.record_sample(
            TelemetrySample(
                timestamp=now - timedelta(minutes=minutes_ago),
                keystrokes_per_min=150.0,
                mouse_moves_per_min=200.0,
                window_focus_changes=3,
                pager_events=2,  # They got paged twice recently
                active_tasks=3,  # Currently juggling 3 incidents
                idle_minutes=2.0,
                queue_depth=8,
                calendar_block_minutes=30.0,  # In a meeting
            )
        )
    
    # Step 2: Set up attention model and router
    attention_model = AttentionModel()
    policy = RoutingPolicy(
        slo_weight=0.4,
        uncertainty_weight=0.25,
        immediate_threshold=0.75,
        batch_threshold=0.45,
    )
    router = RouterService(telemetry, attention_model, policy)
    
    # Step 3: Add context providers (queue depth, calendar, etc.)
    current_queue = []
    queue_provider = QueueDepthContextProvider(queue_length_fn=lambda: len(current_queue))
    router.register_context_provider(queue_provider)
    
    # Step 4: Create some AI agent tasks that need routing
    tasks = [
        TaskIntent(
            task_id="alert-1",
            severity=5,  # Critical
            slo_risk_minutes=45.0,
            model_confidence=0.55,  # AI is uncertain
            explanation="Production database latency spike detected",
            sensitivity_tag="standard",
        ),
        TaskIntent(
            task_id="alert-2",
            severity=2,  # Low severity
            slo_risk_minutes=10.0,
            model_confidence=0.92,  # AI is very confident
            explanation="Dev environment cache cleanup recommended",
            sensitivity_tag="standard",
        ),
        TaskIntent(
            task_id="alert-3",
            severity=3,  # Medium
            slo_risk_minutes=25.0,
            model_confidence=0.70,
            explanation="API rate limit approaching threshold",
            sensitivity_tag="security",
        ),
    ]
    
    # Step 5: Route each task
    print("Current operator state:")
    print(f"  - Active incidents: 3")
    print(f"  - Recent pages: 2")
    print(f"  - In meeting: 30 min")
    print(f"  - Queue depth: {len(current_queue)}")
    print(f"\nRouting decisions:\n")
    
    for task in tasks:
        work_item = router.handle_task(task)
        
        print(f"Task: {task.task_id} (severity={task.severity}, "
              f"confidence={task.model_confidence:.0%}, "
              f"slo_risk={task.slo_risk_minutes:.0f}m)")
        print(f"  → {work_item.route_strategy.upper()}")
        print(f"  → Priority: {work_item.priority:.2f}")
        print(f"  → Attention load: {work_item.attention_load:.2f}")
        print(f"  → {task.explanation}")
        
        # Add to queue if not auto-resolved
        if work_item.route_strategy != "auto":
            current_queue.append(work_item)
        
        print()
    
    print(f"Final queue depth: {len(current_queue)} items")
    print("\nInterpretation:")
    print("  IMMEDIATE = Wake the human up NOW")
    print("  BATCH = Queue for next review window")
    print("  AUTO = AI handles it autonomously")
    print("  PARK = Defer until operator has more bandwidth")


if __name__ == "__main__":
    main()
