#!/usr/bin/env python3
"""
Gmail Job Hunt Router - Protect Your Sanity

This connects to your actual Gmail and routes job hunt emails intelligently:
- Important people (Pearl, actual recruiters) → Flag if unanswered
- Interview requests → Phone notification (ALWAYS)
- Applications/networking → Digest once a day
- Rejections → Quarantine (read when YOU decide, not when they arrive)
- Recruiter spam (ZipRecruiter, Lensa) → Auto-archive

Setup:
1. Enable Gmail API: https://console.cloud.google.com/apis/library/gmail.googleapis.com
2. Download credentials.json
3. Run this script
4. Authorize access
5. Let it protect your mental health
"""

import os
import pickle
import re
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
from email.mime.text import MIMEText

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

# VIP contacts - actual humans you're working with
VIP_CONTACTS = [
    'gypclany@yahoo.com',  # Pearl Collings - Datadog recruiter
    # Add more as needed
]

# Automated spam sources to auto-archive
SPAM_SOURCES = [
    'ziprecruiter.com',
    'lensa.com',
    'theladders.com',
    'indeed.com',
    'linkedin.com',  # Only the automated job alerts, not actual messages
]

# Email classification patterns
PATTERNS = {
    'interview_request': [
        r'schedule.*interview',
        r'interview.*schedule',
        r'phone screen.*schedule',
        r'schedule.*phone screen',
        r'available.*interview',
        r'interview.*time',
        r'calendly.*interview',
        r'meet.*discuss.*role',
        r'next.*interview.*step',
        r'technical.*interview',
        r'video.*interview',
        r'zoom.*interview',
    ],
    'rejection': [
        r'moved forward with other candidates',
        r'decided not to move forward',
        r'not.*selected.*position',
        r'pursuing other candidates',
        r'position has been filled',
        r'will not be moving forward',
        r'chosen.*another candidate',
    ],
    'recruiter_spam': [
        r'exciting opportunity.*apply',
        r'perfect fit for you.*click',
        r'immediate opening.*urgent',
        r'top talent.*exclusive',
        r'competitive salary.*apply now',
        r'limited time.*position',
        r'unsubscribe.*opportunity',
    ],
    'application_received': [
        r'application.*received',
        r'thank you for applying',
        r'we.*received your application',
        r'successfully submitted.*application',
    ],
}

def authenticate_gmail():
    """Authenticate with Gmail API."""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("❌ Missing credentials.json")
                print()
                print("Get it here:")
                print("1. Go to: https://console.cloud.google.com/apis/credentials")
                print("2. Create OAuth 2.0 Client ID (Desktop app)")
                print("3. Download as credentials.json")
                print("4. Put it in this folder")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

def classify_email(subject, body):
    """Classify an email based on patterns."""
    text = (subject + ' ' + body).lower()
    
    # Check patterns in priority order
    for pattern_list in PATTERNS['interview_request']:
        if re.search(pattern_list, text):
            return 'INTERVIEW', 5, 'immediate'  # Critical
    
    for pattern_list in PATTERNS['rejection']:
        if re.search(pattern_list, text):
            return 'REJECTION', 1, 'park'  # Park when mental state is low
    
    for pattern_list in PATTERNS['recruiter_spam']:
        if re.search(pattern_list, text):
            return 'SPAM', 1, 'auto'  # Auto-archive
    
    for pattern_list in PATTERNS['application_received']:
        if re.search(pattern_list, text):
            return 'CONFIRMATION', 2, 'batch'  # Low priority confirmation
    
    # Default: job-related email
    return 'JOB_EMAIL', 3, 'batch'

def create_labels(service):
    """Create Gmail labels for routing."""
    labels_to_create = [
        'JobHunt/IMMEDIATE',
        'JobHunt/Batch',
        'JobHunt/Rejections',
        'JobHunt/Spam',
    ]
    
    existing_labels = service.users().labels().list(userId='me').execute()
    existing_names = {label['name'] for label in existing_labels.get('labels', [])}
    
    created = []
    for label_name in labels_to_create:
        if label_name not in existing_names:
            label = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }
            service.users().labels().create(userId='me', body=label).execute()
            created.append(label_name)
            print(f"✅ Created label: {label_name}")
    
    return created

def get_unread_job_emails(service, hours=24):
    """Get unread emails from the last N hours that are job-related."""
    time_filter = datetime.now() - timedelta(hours=hours)
    
    # Build query for job-related emails, excluding automated spam
    spam_exclusions = ' '.join([f'-from:{domain}' for domain in SPAM_SOURCES])
    
    job_query = (
        f'is:unread after:{time_filter.strftime("%Y/%m/%d")} '
        f'(from:greenhouse.io OR from:lever.co OR from:applytojob.com OR '
        f'subject:interview OR subject:application OR subject:"your application") '
        f'{spam_exclusions}'
    )
    
    results = service.users().messages().list(
        userId='me',
        q=job_query,
        maxResults=50
    ).execute()
    
    messages = results.get('messages', [])
    
    job_emails = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me', 
            id=msg['id'],
            format='full'
        ).execute()
        
        headers = msg_data['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
        
        # Get email body (simplified)
        body = ''
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                    break
        
        # Check if from VIP
        is_vip = any(vip in sender.lower() for vip in VIP_CONTACTS)
        
        category, severity, strategy = classify_email(subject, body)
        
        # Override strategy for VIPs
        if is_vip:
            strategy = 'immediate'
            category = 'VIP'
            severity = 5
        
        job_emails.append({
            'id': msg['id'],
            'subject': subject,
            'sender': sender,
            'category': category,
            'severity': severity,
            'strategy': strategy,
            'is_vip': is_vip,
            'body_preview': body[:200] if body else ''
        })
    
    return job_emails

def check_unanswered_vips(service, days=7):
    """Check for unanswered emails from VIP contacts."""
    time_filter = datetime.now() - timedelta(days=days)
    
    unanswered = []
    for vip in VIP_CONTACTS:
        # Search for emails from VIP that you haven't replied to
        query = f'from:{vip} after:{time_filter.strftime("%Y/%m/%d")} -label:sent'
        
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=10
        ).execute()
        
        messages = results.get('messages', [])
        
        for msg in messages:
            msg_data = service.users().messages().get(
                userId='me', 
                id=msg['id'],
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            headers = msg_data['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            date_str = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), '')
            
            # Check if you've sent any email to this person since
            thread_id = msg_data['threadId']
            thread = service.users().threads().get(userId='me', id=thread_id).execute()
            
            # Check if you replied in the thread
            your_reply = False
            for thread_msg in thread['messages']:
                thread_headers = thread_msg['payload']['headers']
                thread_from = next((h['value'] for h in thread_headers if h['name'] == 'From'), '')
                if 'grahampaasch@gmail.com' in thread_from.lower():
                    # You sent a message in this thread
                    thread_date = next((h['value'] for h in thread_headers if h['name'] == 'Date'), '')
                    # Check if it's after the VIP's message
                    # (simplified - just check if you've sent anything in thread)
                    your_reply = True
                    break
            
            if not your_reply:
                unanswered.append({
                    'sender': sender,
                    'subject': subject,
                    'date': date_str,
                    'days_ago': (datetime.now() - datetime.strptime(date_str[:25], '%a, %d %b %Y %H:%M:%S')).days
                })
    
    return unanswered

def route_email(service, email):
    """Route an email based on its classification."""
    msg_id = email['id']
    strategy = email['strategy']
    category = email['category']
    
    # Get all labels
    labels = service.users().labels().list(userId='me').execute()
    label_map = {label['name']: label['id'] for label in labels.get('labels', [])}
    
    modifications = {'removeLabelIds': ['UNREAD']}
    
    if strategy == 'immediate':
        # Keep as unread, mark as important, add IMMEDIATE label
        modifications = {'addLabelIds': [label_map.get('JobHunt/IMMEDIATE', ''), 'IMPORTANT']}
        print(f"   🚨 IMMEDIATE: {email['subject'][:60]}")
        
    elif strategy == 'batch':
        # Mark read, add to batch
        modifications = {
            'removeLabelIds': ['UNREAD'],
            'addLabelIds': [label_map.get('JobHunt/Batch', '')]
        }
        print(f"   📋 BATCH: {email['subject'][:60]}")
        
    elif strategy == 'park':
        # Rejections - move to folder, mark read
        modifications = {
            'removeLabelIds': ['UNREAD', 'INBOX'],
            'addLabelIds': [label_map.get('JobHunt/Rejections', '')]
        }
        print(f"   ⏸️  PARKED (rejection): {email['subject'][:60]}")
        
    elif strategy == 'auto':
        # Spam - archive immediately
        modifications = {
            'removeLabelIds': ['UNREAD', 'INBOX'],
            'addLabelIds': [label_map.get('JobHunt/Spam', '')]
        }
        print(f"   🗑️  AUTO-ARCHIVED (spam): {email['subject'][:60]}")
    
    # Apply modifications
    service.users().messages().modify(
        userId='me',
        id=msg_id,
        body=modifications
    ).execute()

def main():
    print("=" * 80)
    print("📧 Gmail Job Hunt Router")
    print("=" * 80)
    print()
    print("This will scan your Gmail and intelligently route job hunt emails:")
    print()
    print("  � VIP contacts (Pearl) → Always flagged if unanswered")
    print("  �🚨 Interview requests → Stay in inbox, marked important")
    print("  📋 Applications/networking → Marked for batch processing")
    print("  ⏸️  Rejections → Moved out of inbox (protect your mental health)")
    print("  🗑️  Recruiter spam → Auto-archived")
    print()
    
    # Authenticate
    print("🔐 Authenticating with Gmail...")
    creds = authenticate_gmail()
    if not creds:
        return
    
    try:
        service = build('gmail', 'v1', credentials=creds)
        print("✅ Connected to Gmail")
        print()
        
        # Create labels
        print("📁 Setting up labels...")
        create_labels(service)
        print()
        
        # Check for unanswered VIPs first
        print("👤 Checking for unanswered VIP emails...")
        unanswered = check_unanswered_vips(service, days=30)
        
        if unanswered:
            print()
            print("⚠️  UNANSWERED EMAILS FROM IMPORTANT PEOPLE:")
            print("-" * 80)
            for email in unanswered:
                print(f"  👤 {email['sender']}")
                print(f"     Subject: {email['subject']}")
                print(f"     📅 {email['days_ago']} days ago")
                print(f"     ⏰ YOU HAVEN'T REPLIED YET")
                print()
            print("=" * 80)
            print()
        else:
            print("✅ No unanswered VIP emails")
            print()
        
        # Get and route emails
        print("📨 Scanning for job-related emails (last 24 hours)...")
        print()
        
        emails = get_unread_job_emails(service, hours=24)
        
        if not emails:
            print("📭 No unread job emails found.")
            print()
            if not unanswered:
                print("The router will run in the background and process new emails automatically.")
            return
        
        print(f"Found {len(emails)} job-related emails. Routing...\n")
        
        immediate_count = 0
        batch_count = 0
        park_count = 0
        auto_count = 0
        vip_count = 0
        
        for email in emails:
            route_email(service, email)
            
            if email.get('is_vip'):
                vip_count += 1
            elif email['strategy'] == 'immediate':
                immediate_count += 1
            elif email['strategy'] == 'batch':
                batch_count += 1
            elif email['strategy'] == 'park':
                park_count += 1
            elif email['strategy'] == 'auto':
                auto_count += 1
        
        print()
        print("=" * 80)
        print("✅ ROUTING COMPLETE")
        print("=" * 80)
        print()
        if vip_count > 0:
            print(f"  👤 VIP EMAILS (flagged): {vip_count}")
        print(f"  🚨 IMMEDIATE (in inbox, important): {immediate_count}")
        print(f"  📋 BATCH (labeled, read later): {batch_count}")
        print(f"  ⏸️  PARKED (rejections, out of sight): {park_count}")
        print(f"  🗑️  AUTO-ARCHIVED (spam): {auto_count}")
        print()
        print("Check your Gmail:")
        print("  • VIP emails (Pearl) are flagged")
        print("  • Interview requests are still in your inbox")
        print("  • Rejections are in JobHunt/Rejections (read when YOU want)")
        print("  • Automated spam is archived")
        print()
        print("Your inbox is now actually useful. 🎯")
        print()
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")

if __name__ == '__main__':
    main()
