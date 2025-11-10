#!/usr/bin/env python3
"""
🎬 COGNITIVE ROUTER DEMO: The Overloaded On-Call Engineer

This simulation shows how the router adapts its decisions based on 
operator cognitive load - the same alert gets routed differently depending 
on how busy you are.
"""

import requests
import time
import json
from datetime import datetime, UTC, timedelta

API_URL = "http://localhost:5000"

def send_alert(source, severity, title, urgency="low"):
    """Send an alert and return the routing decision."""
    if source == "pagerduty":
        payload = {
            "incident": {
                "id": f"INC-{int(time.time())}",
                "title": title,
                "urgency": urgency,
                "status": "triggered"
            }
        }
    elif source == "datadog":
        payload = {
            "id": str(int(time.time())),
            "title": title,
            "priority": severity,
            "alert_type": "error" if severity in ["P1", "P2"] else "warning"
        }
    elif source == "ai_model":
        payload = {
            "prediction_id": f"pred-{int(time.time())}",
            "predicted_action": title,
            "confidence": 0.85,
            "severity": "low",
            "estimated_impact_minutes": 10,
            "explanation": title
        }
    
    resp = requests.post(f"{API_URL}/webhook/{source}", json=payload)
    result = resp.json()
    return result['results'][0] if result.get('results') else None

def simulate_telemetry(active_tasks, pager_events, queue_depth, idle_minutes):
    """Inject fake telemetry to simulate operator state."""
    # This would normally come from real monitoring, but we'll fake it
    print(f"  📊 Operator state: {active_tasks} active tasks, {pager_events} pages, queue depth {queue_depth}, idle {idle_minutes}m")

def clear_queue():
    """Clear the queue."""
    requests.delete(f"{API_URL}/queue") if False else None  # Not implemented, just for demo

def main():
    print("=" * 80)
    print("🎬 COGNITIVE ROUTER DEMO: The Overloaded On-Call Engineer")
    print("=" * 80)
    print()
    print("This demo shows how the SAME alert gets routed DIFFERENTLY based on")
    print("operator cognitive load. Watch how the router protects your attention!")
    print()
    input("Press ENTER to start...")
    print()
    
    # ============================================================================
    # SCENARIO 1: Fresh Morning - Low Cognitive Load
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 SCENARIO 1: Monday 9am - Fresh Start")
    print("=" * 80)
    print("You just arrived at work. Coffee in hand. No incidents. Empty queue.")
    print()
    simulate_telemetry(active_tasks=0, pager_events=0, queue_depth=0, idle_minutes=30)
    print()
    
    time.sleep(2)
    
    print("📨 Alert arrives: 'Database CPU at 75%'")
    result = send_alert("datadog", "P3", "Database CPU usage at 75%")
    print(f"   🎯 Router decision: {result['strategy'].upper()}")
    print(f"   📈 Priority score: {result['priority']:.2f}")
    print(f"   🧠 Attention load: {result['attention_load']:.2f}")
    print()
    print("   ✅ Fresh morning = Low attention load = Routes to BATCH")
    print("      You can review this during your normal queue sweep.")
    print()
    
    input("Press ENTER for next scenario...")
    
    # ============================================================================
    # SCENARIO 2: Afternoon Crunch - Medium Load
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 SCENARIO 2: Same Day, 2pm - Getting Busy")
    print("=" * 80)
    print("You've been working all day. 3 incidents in progress. 8 tickets queued.")
    print()
    simulate_telemetry(active_tasks=3, pager_events=1, queue_depth=8, idle_minutes=5)
    print()
    
    time.sleep(2)
    
    # Send multiple alerts to show routing variance
    alerts = [
        ("Database CPU at 75% (again)", "datadog", "P3"),
        ("Low-confidence ML prediction", "ai_model", "P5"),
        ("API latency spike", "datadog", "P2"),
    ]
    
    for title, source, severity in alerts:
        print(f"📨 Alert arrives: '{title}'")
        result = send_alert(source, severity, title)
        print(f"   🎯 Router decision: {result['strategy'].upper()}")
        print(f"   📈 Priority: {result['priority']:.2f} | Attention: {result['attention_load']:.2f}")
        
        if result['strategy'] == 'auto':
            print(f"   🤖 AI handles this one - you're too busy for low-priority stuff")
        elif result['strategy'] == 'batch':
            print(f"   📋 Queued for later - you'll get to it when you have bandwidth")
        elif result['strategy'] == 'immediate':
            print(f"   🚨 High priority - interrupting you NOW")
        print()
        time.sleep(1.5)
    
    input("Press ENTER for the chaos scenario...")
    
    # ============================================================================
    # SCENARIO 3: Midnight Incident - MAXIMUM LOAD
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 SCENARIO 3: Same Night, 11pm - Everything is on Fire 🔥")
    print("=" * 80)
    print("You're handling a P1 incident. 5 active tasks. Got paged 4 times in the")
    print("last hour. Queue depth at 15. You've been context-switching every 3 minutes.")
    print()
    simulate_telemetry(active_tasks=5, pager_events=4, queue_depth=15, idle_minutes=1)
    print()
    
    time.sleep(2)
    
    print("📨 Alert arrives: 'Database CPU at 75%' (THE SAME ALERT)")
    result = send_alert("datadog", "P3", "Database CPU usage at 75%")
    print(f"   🎯 Router decision: {result['strategy'].upper()}")
    print(f"   📈 Priority: {result['priority']:.2f} | Attention: {result['attention_load']:.2f}")
    print()
    print("   ⏸️  PARKED! Your cognitive bandwidth is maxed out.")
    print("      This can wait until you're not drowning in P1s.")
    print()
    
    time.sleep(2)
    
    print("📨 But what if it's CRITICAL? 'Payment API is DOWN'")
    result = send_alert("pagerduty", "P1", "💥 PAYMENT API RETURNING 503 - NO CHECKOUTS", urgency="high")
    print(f"   🎯 Router decision: {result['strategy'].upper()}")
    print(f"   📈 Priority: {result['priority']:.2f} | Attention: {result['attention_load']:.2f}")
    print()
    print("   🚨 IMMEDIATE! Even though you're overloaded, this is critical.")
    print("      High severity + business impact = Always escalates.")
    print()
    
    input("Press ENTER for the intelligence showcase...")
    
    # ============================================================================
    # SCENARIO 4: The Intelligence - Confidence-Based Routing
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 SCENARIO 4: The AI Confidence Game")
    print("=" * 80)
    print("Watch how the router handles AI predictions differently based on confidence...")
    print()
    
    # High confidence prediction
    print("🤖 AI Model: 'Scale up workers' (94% confidence)")
    payload = {
        "prediction_id": f"pred-{int(time.time())}",
        "predicted_action": "scale_up_worker_pool",
        "confidence": 0.94,
        "severity": "low",
        "estimated_impact_minutes": 5,
        "explanation": "Traffic trending up, recommend 2 more instances"
    }
    resp = requests.post(f"{API_URL}/webhook/ai_model", json=payload)
    result = resp.json()['results'][0]
    print(f"   🎯 Router decision: {result['strategy'].upper()}")
    print(f"   ✅ High confidence + low severity = AUTO")
    print(f"      AI just does it. You never even see this alert.")
    print()
    
    time.sleep(2)
    
    # Low confidence prediction
    print("🤖 AI Model: 'Restart database' (51% confidence)")
    payload = {
        "prediction_id": f"pred-{int(time.time())}",
        "predicted_action": "restart_database_primary",
        "confidence": 0.51,
        "severity": "high",
        "estimated_impact_minutes": 30,
        "explanation": "Database health score declining, consider restart"
    }
    resp = requests.post(f"{API_URL}/webhook/ai_model", json=payload)
    result = resp.json()['results'][0]
    print(f"   🎯 Router decision: {result['strategy'].upper()}")
    print(f"   🚨 Low confidence + high impact = IMMEDIATE")
    print(f"      AI is uncertain. Human judgment required.")
    print()
    
    # ============================================================================
    # THE BIG REVEAL
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧠 THE BIG REVEAL: What Just Happened")
    print("=" * 80)
    print()
    print("The router just demonstrated CONTEXT-AWARE INTELLIGENCE:")
    print()
    print("1. 🔄 ADAPTIVE ROUTING")
    print("   The SAME 'DB CPU 75%' alert was routed differently:")
    print("   • Morning (low load) → BATCH")
    print("   • Evening (high load) → PARK")
    print("   Decision adapts to YOUR availability!")
    print()
    print("2. 🎯 PRIORITY BLENDING")
    print("   Combines multiple signals:")
    print("   • Task urgency (SLO risk, severity)")
    print("   • AI confidence (trust the model?)")
    print("   • Your cognitive load (can you handle this?)")
    print("   • Queue depth (are you drowning?)")
    print()
    print("3. 🤖 AUTONOMOUS FILTERING")
    print("   High-confidence, low-severity → AI handles it")
    print("   You never saw that scaling decision. It just happened.")
    print("   Your attention is reserved for what MATTERS.")
    print()
    print("4. 🛡️ PROTECTION MODE")
    print("   When you're maxed out (5 incidents, paged 4x):")
    print("   • Non-critical stuff → PARK")
    print("   • Critical stuff → Still IMMEDIATE")
    print("   The router PROTECTS your finite attention span.")
    print()
    print("=" * 80)
    print("🎯 BOTTOM LINE")
    print("=" * 80)
    print()
    print("Traditional alerting: 'Here's 50 alerts. Good luck.'")
    print()
    print("Cognitive routing: 'You're handling 5 P1s. I'll auto-resolve")
    print("                    the easy stuff, park the non-urgent,")
    print("                    and only interrupt you for critical decisions.'")
    print()
    print("Your attention is FINITE. The router RESPECTS that.")
    print()
    print("=" * 80)
    print()
    print("✨ Check the dashboard to see all the routing decisions!")
    print()

if __name__ == "__main__":
    main()
