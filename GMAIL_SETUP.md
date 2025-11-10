# Gmail Job Hunt Router - Setup Guide

## What This Does

Routes your job hunt emails intelligently so you're not having a panic attack every time Gmail buzzes:

- **🚨 Interview requests** → Stay in inbox, marked IMPORTANT (you NEVER miss these)
- **📋 Job applications/networking** → Labeled for batch processing (review once a day)
- **⏸️ Rejection emails** → Moved to separate folder (read when YOU decide, not at 2pm on a bad day)
- **🗑️ Recruiter spam** → Auto-archived ("exciting opportunity in insurance sales" goes straight to trash)

## Why This Matters

When every email could be "the one," your brain is in constant panic mode. You compulsively check everything, get destroyed by rejections, waste energy on spam, and can't focus on actual interviews.

This system **protects your limited mental energy** for what actually matters.

## Setup (5 minutes)

### 1. Install Python dependencies

```bash
pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
```

### 2. Enable Gmail API

1. Go to: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Click "Enable"
3. Go to: https://console.cloud.google.com/apis/credentials
4. Click "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: **Desktop app**
6. Download the credentials
7. Save as `credentials.json` in this folder

### 3. Run it

```bash
python gmail_job_router.py
```

First time: Opens browser to authorize access to your Gmail.  
After that: Runs automatically.

### 4. What happens

The script:
- Scans your unread emails from the last 24 hours
- Detects job-related emails
- Routes them based on content:
  - "interview" or "phone screen" → IMMEDIATE
  - "moved forward with other candidates" → PARKED (rejection)
  - "exciting opportunity" with no details → SPAM
  - Application confirmations → BATCH

### 5. Check your Gmail

You'll see new labels:
- **JobHunt/IMMEDIATE** (red) - Check NOW
- **JobHunt/Batch** (orange) - Review once a day
- **JobHunt/Rejections** (gray) - Out of inbox, read when ready
- **JobHunt/Spam** (dark gray) - Archived

## Run it automatically

### Linux/Mac (cron job - runs every hour)

```bash
crontab -e
```

Add this line:
```
0 * * * * cd /path/to/focus-flow && python gmail_job_router.py >> gmail_router.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 1 hour
4. Action: Start program `python.exe`
5. Arguments: `C:\path\to\focus-flow\gmail_job_router.py`

## Examples

**Before routing:**
```
Inbox (47 unread)
├─ "Exciting opportunity!" (recruiter spam)
├─ "Thanks for applying" (auto-confirmation)
├─ "Interview request - Can you talk tomorrow?" (CRITICAL)
├─ "We've moved forward with other candidates" (rejection)
├─ "Perfect fit for you!" (more spam)
└─ ...42 more
```

**After routing:**
```
Inbox (1 unread) 🚨
└─ "Interview request - Can you talk tomorrow?" [IMPORTANT]

JobHunt/Batch (2)
├─ "Thanks for applying"
└─ "Coffee chat opportunity"

JobHunt/Rejections (1)
└─ "We've moved forward with other candidates"

JobHunt/Spam (archived, 43)
└─ All the "exciting opportunity" garbage
```

## The Mental Health Impact

**Without this:**
- Phone buzzes → Panic ("Is it an interview?")
- Open Gmail → Recruiter spam
- Phone buzzes → Panic again
- Open Gmail → Rejection email at 2pm (day ruined)
- Phone buzzes → Can't even tell what's important anymore
- Mental energy depleted, can't focus on actual interview when it comes

**With this:**
- Phone buzzes with "IMPORTANT" → Actually an interview
- Rejection emails quietly filed away → Read on YOUR schedule
- Spam auto-archived → Never see it
- Mental energy preserved → Can focus on real opportunities

## Privacy

This runs entirely on YOUR computer. No data is sent anywhere except to Google's Gmail API to read/label your emails. The code is open source - read it yourself in `gmail_job_router.py`.

## Need Help?

The script will tell you exactly what it's doing. Check the output. If something's wrong, it'll say what's missing.
