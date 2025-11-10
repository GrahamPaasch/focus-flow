"""Flask webhook server for receiving alerts and routing them."""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import timedelta
import threading
import time

from cognitive_router import (
    TelemetryCollector,
    AttentionModel,
    RouterService,
    RoutingPolicy,
    QueueDepthContextProvider,
    WorkItem,
)
from cognitive_router.telemetry_sources import CombinedTelemetrySource
from cognitive_router.alert_sources import GenericWebhookHandler


app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Global router state
telemetry_collector = TelemetryCollector(window=timedelta(minutes=30))
telemetry_source = CombinedTelemetrySource()
attention_model = AttentionModel()
policy = RoutingPolicy()
router = RouterService(telemetry_collector, attention_model, policy)
webhook_handler = GenericWebhookHandler()
work_queue = []

# Add queue depth provider
queue_provider = QueueDepthContextProvider(queue_length_fn=lambda: len(work_queue))
router.register_context_provider(queue_provider)


def telemetry_collection_loop():
    """Background thread that collects telemetry every minute."""
    while True:
        try:
            sample = telemetry_source.collect_sample()
            telemetry_collector.record_sample(sample)
            print(f"📊 Telemetry: idle={sample.idle_minutes:.1f}m, "
                  f"incidents={sample.active_tasks}, queue={sample.queue_depth}")
        except Exception as e:
            print(f"⚠ Telemetry collection error: {e}")
        
        time.sleep(60)  # Collect every minute


def route_immediate(work_item: WorkItem):
    """Handler for immediate routing - actually page the human."""
    print(f"🚨 IMMEDIATE: {work_item.task.explanation}")
    # TODO: Send to PagerDuty/Slack/etc
    # Example: requests.post('https://api.pagerduty.com/incidents', ...)


def route_batch(work_item: WorkItem):
    """Handler for batch routing - add to review queue."""
    print(f"📋 BATCH: {work_item.task.explanation}")
    # TODO: Add to ticket system
    # Example: jira.create_issue(...)


def route_auto(work_item: WorkItem):
    """Handler for auto routing - let AI handle it."""
    print(f"🤖 AUTO: {work_item.task.explanation}")
    # TODO: Execute automated remediation
    # Example: kubernetes.scale_deployment(...)


def route_park(work_item: WorkItem):
    """Handler for park routing - defer for now."""
    print(f"⏸️ PARK: {work_item.task.explanation}")
    # TODO: Store in deferred queue


# Register routing sinks
router.register_sink("immediate", route_immediate)
router.register_sink("batch", route_batch)
router.register_sink("auto", route_auto)
router.register_sink("park", route_park)


@app.route('/webhook/<source>', methods=['POST'])
def receive_webhook(source):
    """
    Receive webhook from monitoring/alerting systems.
    
    Examples:
      POST /webhook/datadog
      POST /webhook/pagerduty
      POST /webhook/prometheus
      POST /webhook/ai_model
    """
    try:
        payload = request.json
        
        # Parse webhook into TaskIntent objects
        tasks = webhook_handler.handle_webhook(source, payload)
        
        results = []
        for task in tasks:
            # Route through the cognitive router
            work_item = router.handle_task(task)
            
            # Add to queue if not auto-resolved
            if work_item.route_strategy != "auto":
                work_queue.append(work_item)
            
            results.append({
                'task_id': task.task_id,
                'strategy': work_item.route_strategy,
                'priority': work_item.priority,
                'attention_load': work_item.attention_load,
            })
        
        return jsonify({
            'status': 'success',
            'tasks_processed': len(tasks),
            'results': results,
            'queue_depth': len(work_queue),
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/queue', methods=['GET'])
def get_queue():
    """Get current work queue status."""
    queue_by_strategy = {}
    for item in work_queue:
        strategy = item.route_strategy
        if strategy not in queue_by_strategy:
            queue_by_strategy[strategy] = []
        queue_by_strategy[strategy].append({
            'task_id': item.task_id,
            'priority': item.priority,
            'explanation': item.task.explanation,
        })
    
    return jsonify({
        'total': len(work_queue),
        'by_strategy': queue_by_strategy,
    })


@app.route('/telemetry', methods=['GET'])
def get_telemetry():
    """Get current telemetry summary."""
    summary = telemetry_collector.summarize()
    return jsonify(summary)


@app.route('/policy', methods=['GET', 'POST'])
def manage_policy():
    """Get or update routing policy."""
    global policy, router
    
    if request.method == 'GET':
        return jsonify({
            'slo_weight': policy.slo_weight,
            'uncertainty_weight': policy.uncertainty_weight,
            'severity_weight': policy.severity_weight,
            'attention_weight': policy.attention_weight,
            'immediate_threshold': policy.immediate_threshold,
            'batch_threshold': policy.batch_threshold,
            'min_confidence_for_auto': policy.min_confidence_for_auto,
        })
    
    # Update policy
    data = request.json
    new_policy = RoutingPolicy(
        slo_weight=data.get('slo_weight', policy.slo_weight),
        uncertainty_weight=data.get('uncertainty_weight', policy.uncertainty_weight),
        severity_weight=data.get('severity_weight', policy.severity_weight),
        attention_weight=data.get('attention_weight', policy.attention_weight),
        immediate_threshold=data.get('immediate_threshold', policy.immediate_threshold),
        batch_threshold=data.get('batch_threshold', policy.batch_threshold),
        min_confidence_for_auto=data.get('min_confidence_for_auto', policy.min_confidence_for_auto),
    )
    
    policy = new_policy
    router.policy = new_policy
    
    return jsonify({'status': 'updated'})


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'queue_depth': len(work_queue),
        'telemetry_samples': len(telemetry_collector._samples),
    })


def main():
    """Start the webhook server."""
    print("🚀 Starting Cognitive Router Webhook Server")
    print("=" * 50)
    print("\nEndpoints:")
    print("  POST /webhook/<source>  - Receive alerts (datadog, pagerduty, prometheus, ai_model)")
    print("  GET  /queue            - View current work queue")
    print("  GET  /telemetry        - View telemetry summary")
    print("  GET  /policy           - View routing policy")
    print("  POST /policy           - Update routing policy")
    print("  GET  /health           - Health check")
    print("\nStarting background telemetry collection...")
    
    # Start telemetry collection in background
    telemetry_thread = threading.Thread(target=telemetry_collection_loop, daemon=True)
    telemetry_thread.start()
    
    print("✓ Ready to receive webhooks\n")
    
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)


if __name__ == '__main__':
    main()
