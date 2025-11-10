"""Real-world telemetry data source implementations."""

from __future__ import annotations

import os
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Optional

from .telemetry import TelemetrySample


class LinuxActivityMonitor:
    """Monitors user activity on Linux systems using /proc and xinput."""
    
    def __init__(self):
        self.last_check = time.time()
        self.last_idle_time = 0
        
    def get_idle_seconds(self) -> float:
        """Get system idle time in seconds using xprintidle or similar."""
        try:
            # Try xprintidle first (needs: apt install xprintidle)
            result = subprocess.run(
                ['xprintidle'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return float(result.stdout.strip()) / 1000.0  # ms to seconds
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: check X11 screen saver
        try:
            result = subprocess.run(
                ['xssstate', '-i'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return float(result.stdout.strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return 0.0
    
    def get_keyboard_events(self) -> int:
        """Estimate keyboard activity from /proc/interrupts."""
        try:
            with open('/proc/interrupts', 'r') as f:
                for line in f:
                    if 'keyboard' in line.lower() or 'i8042' in line.lower():
                        parts = line.split()
                        # Sum interrupt counts across all CPUs
                        counts = [int(p) for p in parts[1:] if p.isdigit()]
                        return sum(counts)
        except (FileNotFoundError, PermissionError):
            pass
        return 0
    
    def get_window_count(self) -> int:
        """Count open windows using wmctrl."""
        try:
            result = subprocess.run(
                ['wmctrl', '-l'],
                capture_output=True,
                text=True,
                timeout=1
            )
            if result.returncode == 0:
                return len([l for l in result.stdout.strip().split('\n') if l])
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        return 0
    
    def collect_sample(self) -> TelemetrySample:
        """Collect a telemetry sample from system state."""
        now = datetime.now(UTC)
        idle_seconds = self.get_idle_seconds()
        
        # Estimate activity rates (rough approximation)
        keyboard_events = self.get_keyboard_events()
        window_count = self.get_window_count()
        
        # Very rough heuristics - these would need calibration
        keystrokes_per_min = max(0, 200 - (idle_seconds * 5))
        mouse_moves_per_min = max(0, 300 - (idle_seconds * 7))
        
        return TelemetrySample(
            timestamp=now,
            keystrokes_per_min=keystrokes_per_min,
            mouse_moves_per_min=mouse_moves_per_min,
            window_focus_changes=min(window_count, 10),
            pager_events=0,  # Set externally from monitoring systems
            active_tasks=0,  # Set externally from ticket/alert systems
            idle_minutes=idle_seconds / 60.0,
            queue_depth=0,
            calendar_block_minutes=0.0,
        )


class PagerDutyMonitor:
    """Monitor PagerDuty incidents for pager events."""
    
    def __init__(self, api_token: Optional[str] = None, user_id: Optional[str] = None):
        self.api_token = api_token or os.getenv('PAGERDUTY_API_TOKEN')
        self.user_id = user_id or os.getenv('PAGERDUTY_USER_ID')
        self.base_url = 'https://api.pagerduty.com'
    
    def get_recent_pager_count(self, hours: int = 1) -> int:
        """Count pager events in the last N hours."""
        if not self.api_token:
            return 0
        
        try:
            import requests
            from datetime import timedelta
            
            since = datetime.now(UTC) - timedelta(hours=hours)
            headers = {
                'Authorization': f'Token token={self.api_token}',
                'Accept': 'application/vnd.pagerduty+json;version=2'
            }
            params = {
                'user_ids[]': self.user_id,
                'since': since.isoformat(),
                'statuses[]': ['triggered', 'acknowledged']
            }
            
            response = requests.get(
                f'{self.base_url}/incidents',
                headers=headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return len(response.json().get('incidents', []))
        except (ImportError, Exception):
            pass
        
        return 0
    
    def get_active_incident_count(self) -> int:
        """Count currently active incidents."""
        if not self.api_token:
            return 0
        
        try:
            import requests
            
            headers = {
                'Authorization': f'Token token={self.api_token}',
                'Accept': 'application/vnd.pagerduty+json;version=2'
            }
            params = {
                'user_ids[]': self.user_id,
                'statuses[]': ['triggered', 'acknowledged']
            }
            
            response = requests.get(
                f'{self.base_url}/incidents',
                headers=headers,
                params=params,
                timeout=5
            )
            
            if response.status_code == 200:
                return len(response.json().get('incidents', []))
        except (ImportError, Exception):
            pass
        
        return 0


class GoogleCalendarMonitor:
    """Monitor Google Calendar for busy time blocks."""
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
        self.calendar_id = 'primary'
    
    def get_busy_minutes_next_hour(self) -> float:
        """Get minutes of calendar blocks in the next hour."""
        if not self.credentials_path or not Path(self.credentials_path).exists():
            return 0.0
        
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build
            from datetime import timedelta
            
            creds = Credentials.from_authorized_user_file(self.credentials_path)
            service = build('calendar', 'v3', credentials=creds)
            
            now = datetime.now(UTC)
            time_min = now.isoformat()
            time_max = (now + timedelta(hours=1)).isoformat()
            
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            total_minutes = 0.0
            
            for event in events:
                start = event.get('start', {}).get('dateTime')
                end = event.get('end', {}).get('dateTime')
                
                if start and end:
                    from dateutil.parser import parse
                    start_dt = parse(start)
                    end_dt = parse(end)
                    duration = (end_dt - start_dt).total_seconds() / 60.0
                    total_minutes += duration
            
            return total_minutes
            
        except (ImportError, Exception):
            pass
        
        return 0.0


class JiraQueueMonitor:
    """Monitor JIRA for assigned ticket count."""
    
    def __init__(self, server: Optional[str] = None, email: Optional[str] = None, 
                 api_token: Optional[str] = None):
        self.server = server or os.getenv('JIRA_SERVER')
        self.email = email or os.getenv('JIRA_EMAIL')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
    
    def get_assigned_ticket_count(self) -> int:
        """Count tickets currently assigned to the user."""
        if not all([self.server, self.email, self.api_token]):
            return 0
        
        try:
            import requests
            from requests.auth import HTTPBasicAuth
            
            auth = HTTPBasicAuth(self.email, self.api_token)
            headers = {'Accept': 'application/json'}
            
            # JQL query for open tickets assigned to current user
            jql = 'assignee = currentUser() AND status not in (Done, Closed, Resolved)'
            
            response = requests.get(
                f'{self.server}/rest/api/3/search',
                params={'jql': jql, 'maxResults': 100},
                headers=headers,
                auth=auth,
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json().get('total', 0)
                
        except (ImportError, Exception):
            pass
        
        return 0


class CombinedTelemetrySource:
    """Combines multiple data sources into unified telemetry samples."""
    
    def __init__(self):
        self.activity_monitor = LinuxActivityMonitor()
        self.pagerduty = PagerDutyMonitor()
        self.calendar = GoogleCalendarMonitor()
        self.jira = JiraQueueMonitor()
    
    def collect_sample(self) -> TelemetrySample:
        """Collect a complete telemetry sample from all sources."""
        # Start with system activity
        sample = self.activity_monitor.collect_sample()
        
        # Enrich with external sources
        sample.pager_events = self.pagerduty.get_recent_pager_count(hours=1)
        sample.active_tasks = self.pagerduty.get_active_incident_count()
        sample.queue_depth = self.jira.get_assigned_ticket_count()
        sample.calendar_block_minutes = self.calendar.get_busy_minutes_next_hour()
        
        return sample
