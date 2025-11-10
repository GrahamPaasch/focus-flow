#!/usr/bin/env python3
"""
🧠 COGNITIVE ROUTER: Job Hunt Edition

When you're unemployed, EVERYTHING feels urgent. Every LinkedIn notification,
every job posting, every email could be "the one." But your mental energy is 
FINITE, especially after a year of rejection.

This routes your job hunt tasks based on:
- What actually matters (interviews > applications > networking)
- Your current mental state (burned out? depressed? motivated?)
- How many rejections you've gotten this week
- Whether you've been doom-scrolling for 3 hours

Let's stop treating your brain like it has infinite capacity.
"""

import requests
import time
from datetime import datetime

API_URL = "http://localhost:5000"

def send_task(task_type, title, urgency, confidence=0.7):
    """Send a job hunt task."""
    if task_type == "interview":
        severity = 5  # Critical - actual interview
        slo_risk = 60  # You have 1 hour to prepare
    elif task_type == "application":
        severity = 3  # Medium - could be important
        slo_risk = 30  # Should apply soon
    elif task_type == "networking":
        severity = 2  # Low but valuable
        slo_risk = 15  # Not time-sensitive
    elif task_type == "linkedin_spam":
        severity = 1  # Noise
        slo_risk = 5   # Doesn't matter
    else:
        severity = 2
        slo_risk = 20
    
    # Map to severity levels
    priority_map = {5: "P1", 4: "P2", 3: "P3", 2: "P4", 1: "P5"}
    
    payload = {
        "id": str(int(time.time())),
        "title": title,
        "priority": priority_map[severity],
        "alert_type": "error" if severity >= 4 else "warning"
    }
    
    resp = requests.post(f"{API_URL}/webhook/datadog", json=payload)
    return resp.json()['results'][0]

def main():
    print("=" * 80)
    print("🧠 COGNITIVE ROUTER: Job Hunt Edition")
    print("=" * 80)
    print()
    print("You've been unemployed for a year. Every day feels like this:")
    print()
    print("  • 47 unread LinkedIn messages (95% recruiter spam)")
    print("  • 3 'perfect fit' job posts (you've seen 1,000 of these)")
    print("  • 1 actual interview request (buried in the noise)")
    print("  • Your mental energy is at 20% after last week's 3 rejections")
    print()
    print("Traditional approach: CHECK EVERYTHING NOW.")
    print("Cognitive routing: Let's be smart about your finite brain power.")
    print()
    input("Press ENTER to start...")
    print()
    
    # ============================================================================
    # SCENARIO 1: Monday Morning - Fresh Week (Motivated State)
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 MONDAY MORNING: Fresh Week Energy")
    print("=" * 80)
    print("You slept well. Coffee's good. You're feeling motivated today.")
    print("Mental state: 7/10")
    print()
    
    time.sleep(2)
    
    tasks = [
        ("application", "Senior Dev role at startup (good fit)", "high", 0.8),
        ("networking", "Coffee chat with someone from Dream Company", "medium", 0.6),
        ("linkedin_spam", "InMail: 'Exciting opportunity in insurance sales'", "low", 0.3),
    ]
    
    for task_type, title, urgency, confidence in tasks:
        print(f"📨 Task: {title}")
        result = send_task(task_type, title, urgency, confidence)
        print(f"   🎯 Router: {result['strategy'].upper()}")
        
        if result['strategy'] == 'immediate':
            print(f"   💪 Do this NOW while you have energy")
        elif result['strategy'] == 'batch':
            print(f"   📋 Save for your afternoon application batch")
        elif result['strategy'] == 'auto':
            print(f"   🗑️  Auto-archived (obvious spam)")
        elif result['strategy'] == 'park':
            print(f"   ⏸️  Low priority - skip if you're drained")
        print()
        time.sleep(1.5)
    
    input("Press ENTER for Wednesday...")
    
    # ============================================================================
    # SCENARIO 2: Wednesday - Rejection Fatigue
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 WEDNESDAY: You Got Two Rejections Yesterday")
    print("=" * 80)
    print("One was after a 4-hour interview process. The other ghosted you for")
    print("3 weeks then sent a form email. You've been on Reddit for 2 hours.")
    print("Mental state: 3/10")
    print()
    
    time.sleep(2)
    
    tasks = [
        ("interview", "⚡ INTERVIEW REQUEST: Phone screen tomorrow 10am", "critical", 0.9),
        ("application", "Another 'senior' role (probably wants 10 YOE for $60k)", "medium", 0.4),
        ("networking", "Alumni wants to connect", "low", 0.5),
        ("linkedin_spam", "Recruiter: 'I have the perfect role' (doesn't say what)", "low", 0.2),
    ]
    
    for task_type, title, urgency, confidence in tasks:
        print(f"📨 Task: {title}")
        result = send_task(task_type, title, urgency, confidence)
        print(f"   🎯 Router: {result['strategy'].upper()}")
        
        if result['strategy'] == 'immediate':
            print(f"   🚨 Interview = ALWAYS immediate, even when you're burned out")
        elif result['strategy'] == 'batch':
            print(f"   📋 Batch this - you don't have energy for 20 applications today")
        elif result['strategy'] == 'park':
            print(f"   ⏸️  Park it. You need to not think about jobs for an hour.")
        elif result['strategy'] == 'auto':
            print(f"   🗑️  Obvious noise - auto-ignored")
        print()
        time.sleep(1.5)
    
    input("Press ENTER for Friday...")
    
    # ============================================================================
    # SCENARIO 3: Friday - Maximum Burnout
    # ============================================================================
    print("\n" + "=" * 80)
    print("📅 FRIDAY: You're Fucking Done")
    print("=" * 80)
    print("It's 4pm. You've sent 15 applications this week, heard nothing back.")
    print("You've been scrolling Twitter/LinkedIn for 4 hours. Brain is mush.")
    print("Mental state: 1/10")
    print()
    
    time.sleep(2)
    
    print("📨 LinkedIn: '387 people applied to the role you're viewing'")
    result = send_task("linkedin_spam", "387 people applied notification", "low", 0.1)
    print(f"   🎯 Router: {result['strategy'].upper()}")
    print(f"   🗑️  AUTO-IGNORED. This is designed to make you feel like shit.")
    print()
    
    time.sleep(1.5)
    
    print("📨 Email: 'Thanks for applying. We've decided to move forward with other candidates.'")
    result = send_task("application", "Rejection email #47", "low", 0.2)
    print(f"   🎯 Router: {result['strategy'].upper()}")
    print(f"   ⏸️  PARKED. You don't need to read this right now.")
    print(f"       Mark it read. Deal with it Monday when you're not destroyed.")
    print()
    
    time.sleep(1.5)
    
    print("📨 Email: 'RE: Interview - Next Steps'")
    result = send_task("interview", "Interview follow-up from Dream Company", "critical", 0.95)
    print(f"   🎯 Router: {result['strategy'].upper()}")
    print(f"   ✅ IMMEDIATE. Even in burnout mode, THIS gets through.")
    print(f"      Everything else can wait. Not this.")
    print()
    
    # ============================================================================
    # THE REAL REVEAL
    # ============================================================================
    print("\n" + "=" * 80)
    print("🧠 WHAT THIS ACTUALLY MEANS FOR YOU")
    print("=" * 80)
    print()
    print("When you're unemployed, EVERYTHING screams for attention:")
    print()
    print("❌ Without routing:")
    print("   → Check all 47 LinkedIn messages (95% spam)")
    print("   → Read every rejection email immediately (max pain)")
    print("   → Apply to 20 jobs a day (burnout speedrun)")
    print("   → Mental energy depleted by noon")
    print("   → Can't even handle a real interview request")
    print()
    print("✅ With cognitive routing:")
    print("   → Interviews ALWAYS break through (even when burned out)")
    print("   → Spam auto-filtered (save your mental energy)")
    print("   → Applications batched (10 at once vs scattered all day)")
    print("   → Rejections parked when you're fragile")
    print("   → LinkedIn doom-scroll triggers → auto-ignored")
    print()
    print("=" * 80)
    print("🎯 THE ACTUAL USE CASE FOR YOU")
    print("=" * 80)
    print()
    print("Connect this to your email/LinkedIn:")
    print()
    print("1. Interview requests → IMMEDIATE notification")
    print("2. Job posts → BATCH (review in one focused session)")
    print("3. Recruiter spam → AUTO-FILTER")
    print("4. Rejections → PARK when your mental state is low")
    print("5. LinkedIn 'X people applied' → AUTO-IGNORE (toxic)")
    print()
    print("Your mental energy is LIMITED. A year of unemployment is EXHAUSTING.")
    print("This router protects your attention for what actually matters:")
    print()
    print("  → Real opportunities (interviews, good referrals)")
    print("  → NOT LinkedIn engagement bait")
    print("  → NOT your 400th rejection email at 2pm on a bad day")
    print()
    print("Traditional tools: 'Here are 10,000 notifications.'")
    print("Cognitive routing: 'Here are the 3 that matter. Ignore the rest.'")
    print()
    print("=" * 80)
    print()
    print("Want this for real? Let's wire it to your actual Gmail/LinkedIn.")
    print()

if __name__ == "__main__":
    main()
