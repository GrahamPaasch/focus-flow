"""Alert source integrations for feeding tasks into the router."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from .task_models import TaskIntent


class DatadogAlertSource:
    """Convert Datadog webhook payloads into TaskIntent objects."""
    
    @staticmethod
    def from_webhook(payload: Dict[str, Any]) -> TaskIntent:
        """
        Parse a Datadog webhook payload.
        
        Example webhook payload:
        {
          "id": "1234567890",
          "title": "High CPU Usage on prod-server-01",
          "priority": "P1",
          "alert_type": "error",
          "alert_transition": "triggered",
          "body": "CPU usage is above 90% for 5 minutes",
          "last_updated": "2025-11-09T12:00:00Z"
        }
        """
        alert_id = payload.get('id', 'unknown')
        title = payload.get('title', 'Unknown alert')
        priority = payload.get('priority', 'P3')
        
        # Map Datadog priority to severity (1-5)
        severity_map = {'P1': 5, 'P2': 4, 'P3': 3, 'P4': 2, 'P5': 1}
        severity = severity_map.get(priority, 3)
        
        # Estimate SLO risk based on alert type
        alert_type = payload.get('alert_type', 'info')
        slo_risk_map = {'error': 45.0, 'warning': 20.0, 'info': 5.0}
        slo_risk = slo_risk_map.get(alert_type, 15.0)
        
        # For now, assume medium confidence (would come from ML model in production)
        model_confidence = 0.70
        
        return TaskIntent(
            task_id=f"datadog-{alert_id}",
            severity=severity,
            slo_risk_minutes=slo_risk,
            model_confidence=model_confidence,
            explanation=title,
            sensitivity_tag="standard",
            source="datadog",
        )


class PagerDutyAlertSource:
    """Convert PagerDuty incident webhooks into TaskIntent objects."""
    
    @staticmethod
    def from_webhook(payload: Dict[str, Any]) -> TaskIntent:
        """
        Parse a PagerDuty incident webhook.
        
        Example webhook payload:
        {
          "event": {
            "id": "INC123",
            "incident_key": "srv01/high_load",
            "urgency": "high",
            "title": "Database connection pool exhausted",
            "status": "triggered",
            "created_at": "2025-11-09T12:00:00Z",
            "service": {"summary": "Production DB"}
          }
        }
        """
        event = payload.get('event', {})
        incident = payload.get('incident', event)
        
        incident_id = incident.get('id', 'unknown')
        title = incident.get('title', incident.get('summary', 'Unknown incident'))
        urgency = incident.get('urgency', 'low')
        
        # Map urgency to severity
        severity = 5 if urgency == 'high' else 3
        
        # High urgency = high SLO risk
        slo_risk = 40.0 if urgency == 'high' else 15.0
        
        # PagerDuty incidents are usually human-verified, so higher confidence
        model_confidence = 0.75
        
        return TaskIntent(
            task_id=f"pagerduty-{incident_id}",
            severity=severity,
            slo_risk_minutes=slo_risk,
            model_confidence=model_confidence,
            explanation=title,
            sensitivity_tag="standard",
            source="pagerduty",
        )


class PrometheusAlertSource:
    """Convert Prometheus AlertManager webhooks into TaskIntent objects."""
    
    @staticmethod
    def from_webhook(payload: Dict[str, Any]) -> List[TaskIntent]:
        """
        Parse a Prometheus AlertManager webhook (can contain multiple alerts).
        
        Example webhook payload:
        {
          "alerts": [
            {
              "status": "firing",
              "labels": {
                "alertname": "HighMemoryUsage",
                "severity": "warning",
                "instance": "node-1"
              },
              "annotations": {
                "summary": "Memory usage above 80%",
                "description": "Instance node-1 has high memory usage"
              }
            }
          ]
        }
        """
        tasks = []
        alerts = payload.get('alerts', [])
        
        for alert in alerts:
            if alert.get('status') != 'firing':
                continue
            
            labels = alert.get('labels', {})
            annotations = alert.get('annotations', {})
            
            alertname = labels.get('alertname', 'unknown')
            prom_severity = labels.get('severity', 'info')
            
            # Map Prometheus severity to 1-5 scale
            severity_map = {'critical': 5, 'error': 4, 'warning': 3, 'info': 2}
            severity = severity_map.get(prom_severity, 2)
            
            # Estimate SLO risk
            slo_risk_map = {'critical': 50.0, 'error': 30.0, 'warning': 15.0, 'info': 5.0}
            slo_risk = slo_risk_map.get(prom_severity, 10.0)
            
            summary = annotations.get('summary', annotations.get('description', alertname))
            
            # Prometheus alerts are rule-based, medium confidence
            model_confidence = 0.65
            
            tasks.append(TaskIntent(
                task_id=f"prometheus-{alertname}-{labels.get('instance', 'unknown')}",
                severity=severity,
                slo_risk_minutes=slo_risk,
                model_confidence=model_confidence,
                explanation=summary,
                sensitivity_tag="standard",
                source="prometheus",
            ))
        
        return tasks


class AIModelPredictionSource:
    """Convert AI model predictions into TaskIntent objects."""
    
    @staticmethod
    def from_prediction(prediction: Dict[str, Any]) -> TaskIntent:
        """
        Parse ML model output with confidence scores.
        
        Example prediction:
        {
          "prediction_id": "pred-123",
          "predicted_action": "scale_database",
          "confidence": 0.89,
          "severity": "high",
          "estimated_impact_minutes": 35,
          "explanation": "Database CPU trending toward saturation",
          "sensitive_data": false
        }
        """
        pred_id = prediction.get('prediction_id', 'unknown')
        confidence = float(prediction.get('confidence', 0.5))
        severity_str = prediction.get('severity', 'medium')
        
        # Map severity string to numeric
        severity_map = {'critical': 5, 'high': 4, 'medium': 3, 'low': 2, 'info': 1}
        severity = severity_map.get(severity_str, 3)
        
        slo_risk = float(prediction.get('estimated_impact_minutes', 15.0))
        explanation = prediction.get('explanation', 'AI prediction')
        
        sensitivity = 'pii' if prediction.get('sensitive_data') else 'standard'
        
        return TaskIntent(
            task_id=f"ai-{pred_id}",
            severity=severity,
            slo_risk_minutes=slo_risk,
            model_confidence=confidence,
            explanation=explanation,
            sensitivity_tag=sensitivity,
            source="ai_model",
        )


class GenericWebhookHandler:
    """Generic webhook handler that routes to specific parsers."""
    
    def __init__(self):
        self.handlers = {
            'datadog': DatadogAlertSource.from_webhook,
            'pagerduty': PagerDutyAlertSource.from_webhook,
            'prometheus': PrometheusAlertSource.from_webhook,
            'ai_model': AIModelPredictionSource.from_prediction,
        }
    
    def handle_webhook(self, source: str, payload: Dict[str, Any]) -> List[TaskIntent]:
        """Route webhook to appropriate parser."""
        handler = self.handlers.get(source)
        if not handler:
            raise ValueError(f"Unknown webhook source: {source}")
        
        result = handler(payload)
        
        # Normalize to list
        if isinstance(result, TaskIntent):
            return [result]
        return result
    
    def handle_json_string(self, source: str, json_payload: str) -> List[TaskIntent]:
        """Parse JSON string and route to handler."""
        payload = json.loads(json_payload)
        return self.handle_webhook(source, payload)
