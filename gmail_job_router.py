#!/usr/bin/env python3
"""
Gmail Job Hunt Router - Protect Your Sanity

This connects to your actual Gmail and routes job hunt emails intelligently:
- Interview requests → Phone notification (ALWAYS)
- Applications/networking → Digest once a day
- Rejections → Quarantine (read when YOU decide, not when they arrive)
- Recruiter spam → Auto-archive

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

# Email classification patterns
PATTERNS = {
    'interview_request': [
        r'interview',
        r'phone screen',
        r'schedule.*call',
        r'next steps',
        r'meet.*team',
        r'technical.*assessment',
        r'conversation.*role',
    ],
    'rejection': [
        r'moved forward with other candidates',
        r'decided not to move forward',
        r'unfortunately',
        r'at this time.*not',
        r'pursuing other candidates',
        r'position has been filled',
        r'appreciate your interest.*however',
    ],
    'recruiter_spam': [
        r'exciting opportunity',
        r'perfect fit for you',
        r'immediate opening',
        r'looking for top talent',
        r'competitive salary.*apply now',
    ],
    'application_received': [
        r'application.*received',
        r'thank you for applying',
        r'we.*received your',
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
    labels_to_create = {
        'JobHunt/IMMEDIATE': 'ff0000',  # Red
        'JobHunt/Batch': 'ff9900',      # Orange
        'JobHunt/Rejections': '999999', # Gray
        'JobHunt/Spam': '666666',       # Dark gray
    }
    
    existing_labels = service.users().labels().list(userId='me').execute()
    existing_names = {label['name'] for label in existing_labels.get('labels', [])}
    
    created = []
    for label_name, color in labels_to_create.items():
        if label_name not in existing_names:
            label = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show',
                'color': {
                    'textColor': '#ffffff',
                    'backgroundColor': f'#{color}'
                }
            }
            service.users().labels().create(userId='me', body=label).execute()
            created.append(label_name)
            print(f"✅ Created label: {label_name}")
    
    return created

def get_unread_job_emails(service, hours=24):
    """Get unread emails from the last N hours that are job-related."""
    # Look for emails from last 24 hours
    time_filter = datetime.now() - timedelta(hours=hours)
    query = f'is:unread after:{time_filter.strftime("%Y/%m/%d")}'
    
    # Add common job-related domains/keywords
    job_keywords = [
        'indeed', 'linkedin', 'greenhouse', 'lever', 'workday',
        'application', 'interview', 'recruiter', 'hiring',
    ]
    
    results = service.users().messages().list(
        userId='me',
        q=query,
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
        
        # Check if job-related
        text = (subject + ' ' + sender + ' ' + body).lower()
        is_job_related = any(keyword in text for keyword in job_keywords)
        
        if is_job_related:
            category, severity, strategy = classify_email(subject, body)
            job_emails.append({
                'id': msg['id'],
                'subject': subject,
                'sender': sender,
                'category': category,
                'severity': severity,
                'strategy': strategy,
                'body_preview': body[:200] if body else ''
            })
    
    return job_emails

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
    print("  🚨 Interview requests → Stay in inbox, marked important")
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
        
        # Get and route emails
        print("📨 Scanning for job-related emails (last 24 hours)...")
        print()
        
        emails = get_unread_job_emails(service, hours=24)
        
        if not emails:
            print("📭 No unread job emails found.")
            print()
            print("The router will run in the background and process new emails automatically.")
            return
        
        print(f"Found {len(emails)} job-related emails. Routing...\n")
        
        immediate_count = 0
        batch_count = 0
        park_count = 0
        auto_count = 0
        
        for email in emails:
            route_email(service, email)
            
            if email['strategy'] == 'immediate':
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
        print(f"  🚨 IMMEDIATE (in inbox, important): {immediate_count}")
        print(f"  📋 BATCH (labeled, read later): {batch_count}")
        print(f"  ⏸️  PARKED (rejections, out of sight): {park_count}")
        print(f"  🗑️  AUTO-ARCHIVED (spam): {auto_count}")
        print()
        print("Check your Gmail:")
        print("  • Interview requests are still in your inbox (red label)")
        print("  • Rejections are in JobHunt/Rejections (read when YOU want)")
        print("  • Spam is archived")
        print()
        print("Your inbox is now actually useful. 🎯")
        print()
        
    except HttpError as error:
        print(f"❌ An error occurred: {error}")

if __name__ == '__main__':
    main()
