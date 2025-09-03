"""
Security Manager for audit logging and security events.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json
import structlog

logger = structlog.get_logger(__name__)

class SecurityManager:
    """
    Handles security audit logging and security event management.
    
    Features:
    - Security event logging
    - Audit trail maintenance  
    - Intrusion detection
    - Security metrics
    """
    
    def __init__(self):
        self.security_events: List[Dict[str, Any]] = []
        self.max_events_memory = 10000
        
    async def log_security_event(self, 
                                event_type: str, 
                                user_id: Optional[str] = None,
                                details: Optional[Dict[str, Any]] = None) -> None:
        """Log a security event."""
        try:
            event = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': user_id,
                'details': details or {},
                'severity': self._get_event_severity(event_type)
            }
            
            # Add to memory store (limited)
            self.security_events.append(event)
            if len(self.security_events) > self.max_events_memory:
                self.security_events = self.security_events[-self.max_events_memory:]
            
            # Log to structured logger
            logger.info(
                "Security event logged",
                event_type=event_type,
                user_id=user_id,
                severity=event['severity'],
                **details if details else {}
            )
            
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
    
    def _get_event_severity(self, event_type: str) -> str:
        """Determine the severity level of a security event."""
        high_severity = ['failed_login', 'unauthorized_access', 'privilege_escalation']
        medium_severity = ['logout_all_sessions', 'password_change']
        
        if event_type in high_severity:
            return 'high'
        elif event_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    async def get_security_events(self, 
                                 user_id: Optional[str] = None,
                                 event_type: Optional[str] = None,
                                 limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve security events with optional filtering."""
        events = self.security_events
        
        if user_id:
            events = [e for e in events if e.get('user_id') == user_id]
        
        if event_type:
            events = [e for e in events if e.get('event_type') == event_type]
        
        return events[-limit:] if events else []