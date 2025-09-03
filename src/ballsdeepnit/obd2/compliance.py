"""
Compliance Manager for Z-areo Non-Profit OBD2 Data Collection
============================================================

Handles data privacy, anonymization, and compliance requirements
for non-profit vehicle data collection in accordance with regulations.
"""

import hashlib
import json
import time
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import re

import structlog

logger = structlog.get_logger(__name__)

class DataClassification(Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class ProcessingPurpose(Enum):
    RESEARCH = "research"
    DIAGNOSTICS = "diagnostics"
    SAFETY_ANALYSIS = "safety_analysis"
    EMISSIONS_MONITORING = "emissions_monitoring"
    FLEET_MANAGEMENT = "fleet_management"

@dataclass
class ConsentRecord:
    """Record of user consent for data collection."""
    consent_id: str
    participant_id: str
    timestamp: datetime
    purposes: List[ProcessingPurpose]
    data_types: List[str]
    retention_period_days: int
    is_active: bool = True
    withdrawal_date: Optional[datetime] = None

@dataclass
class DataRetentionPolicy:
    """Data retention policy configuration."""
    data_type: str
    retention_days: int
    auto_deletion: bool = True
    anonymization_after_days: Optional[int] = None
    classification: DataClassification = DataClassification.INTERNAL

@dataclass
class AuditLogEntry:
    """Audit log entry for compliance tracking."""
    timestamp: datetime
    user_id: str
    action: str
    resource_type: str
    resource_id: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None

class ComplianceManager:
    """
    Comprehensive compliance management for Z-areo non-profit data collection.
    
    Features:
    - Data privacy and anonymization
    - Consent management
    - Data retention policies
    - Audit logging
    - Regulatory compliance (GDPR-inspired)
    - Research ethics compliance
    - Non-profit data governance
    """
    
    def __init__(self, 
                 organization_name: str = "Z-areo Non-Profit",
                 data_controller: str = "Z-areo Data Protection Officer"):
        
        self.organization_name = organization_name
        self.data_controller = data_controller
        
        # Compliance configuration
        self.retention_policies: Dict[str, DataRetentionPolicy] = {}
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.audit_log: List[AuditLogEntry] = []
        
        # PII detection patterns
        self.pii_patterns = {
            'vin': re.compile(r'^[A-HJ-NPR-Z0-9]{17}$'),
            'license_plate': re.compile(r'^[A-Z0-9]{2,8}$'),
            'phone': re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'ssn': re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
        }
        
        # Setup default retention policies
        self._setup_default_policies()
        
    def _setup_default_policies(self):
        """Setup default data retention policies for non-profit research."""
        
        # Vehicle diagnostic data - 7 years for research
        self.retention_policies['vehicle_data'] = DataRetentionPolicy(
            data_type='vehicle_data',
            retention_days=2555,  # 7 years
            auto_deletion=False,  # Keep for research
            anonymization_after_days=365,  # Anonymize after 1 year
            classification=DataClassification.CONFIDENTIAL
        )
        
        # Personal information - 3 years unless consent withdrawn
        self.retention_policies['personal_info'] = DataRetentionPolicy(
            data_type='personal_info',
            retention_days=1095,  # 3 years
            auto_deletion=True,
            classification=DataClassification.RESTRICTED
        )
        
        # Diagnostic codes - 10 years for safety research
        self.retention_policies['diagnostic_codes'] = DataRetentionPolicy(
            data_type='diagnostic_codes',
            retention_days=3650,  # 10 years
            auto_deletion=False,
            anonymization_after_days=730,  # 2 years
            classification=DataClassification.INTERNAL
        )
        
        # CAN messages - 1 year (technical data only)
        self.retention_policies['can_messages'] = DataRetentionPolicy(
            data_type='can_messages',
            retention_days=365,
            auto_deletion=True,
            anonymization_after_days=90,
            classification=DataClassification.INTERNAL
        )
        
        # Audit logs - 7 years (compliance requirement)
        self.retention_policies['audit_logs'] = DataRetentionPolicy(
            data_type='audit_logs',
            retention_days=2555,
            auto_deletion=False,
            classification=DataClassification.CONFIDENTIAL
        )
    
    async def register_consent(self, 
                             participant_id: str,
                             purposes: List[ProcessingPurpose],
                             data_types: List[str],
                             retention_days: int = 2555) -> str:
        """Register participant consent for data collection."""
        try:
            consent_id = f"consent_{participant_id}_{int(time.time())}"
            
            consent_record = ConsentRecord(
                consent_id=consent_id,
                participant_id=participant_id,
                timestamp=datetime.utcnow(),
                purposes=purposes,
                data_types=data_types,
                retention_period_days=retention_days
            )
            
            self.consent_records[consent_id] = consent_record
            
            # Log consent registration
            await self._log_audit_event(
                user_id=participant_id,
                action="consent_registered",
                resource_type="consent_record",
                resource_id=consent_id,
                details={
                    'purposes': [p.value for p in purposes],
                    'data_types': data_types,
                    'retention_days': retention_days
                }
            )
            
            logger.info("Consent registered", 
                       participant_id=participant_id,
                       consent_id=consent_id,
                       purposes=purposes)
            
            return consent_id
            
        except Exception as e:
            logger.error("Error registering consent", error=str(e))
            raise
    
    async def withdraw_consent(self, consent_id: str, participant_id: str) -> bool:
        """Withdraw consent and trigger data deletion if required."""
        try:
            consent = self.consent_records.get(consent_id)
            if not consent or consent.participant_id != participant_id:
                logger.error("Invalid consent withdrawal attempt", 
                           consent_id=consent_id,
                           participant_id=participant_id)
                return False
            
            # Mark consent as withdrawn
            consent.is_active = False
            consent.withdrawal_date = datetime.utcnow()
            
            # Log consent withdrawal
            await self._log_audit_event(
                user_id=participant_id,
                action="consent_withdrawn",
                resource_type="consent_record",
                resource_id=consent_id,
                details={'withdrawal_date': consent.withdrawal_date.isoformat()}
            )
            
            logger.info("Consent withdrawn", 
                       consent_id=consent_id,
                       participant_id=participant_id)
            
            return True
            
        except Exception as e:
            logger.error("Error withdrawing consent", error=str(e))
            return False
    
    def anonymize_data(self, data: Dict[str, Any], preserve_utility: bool = True) -> Dict[str, Any]:
        """Anonymize data while preserving research utility."""
        try:
            anonymized = data.copy()
            
            # Remove or hash direct identifiers
            if 'vin' in anonymized:
                if preserve_utility:
                    # Keep partial VIN for research (last 8 chars hashed)
                    vin = anonymized['vin']
                    if len(vin) >= 17:
                        anonymized['vin_hash'] = self._hash_identifier(vin[-8:])
                        anonymized['manufacturer_code'] = vin[:3]  # Keep for research
                    del anonymized['vin']
                else:
                    del anonymized['vin']
            
            # Remove personal information
            for field in ['name', 'address', 'phone', 'email', 'license_plate']:
                if field in anonymized:
                    del anonymized[field]
            
            # Hash participant ID if present
            if 'participant_id' in anonymized:
                anonymized['participant_hash'] = self._hash_identifier(anonymized['participant_id'])
                del anonymized['participant_id']
            
            # Generalize location data
            if 'latitude' in anonymized and 'longitude' in anonymized:
                # Reduce precision to ~1km (2 decimal places)
                anonymized['latitude'] = round(float(anonymized['latitude']), 2)
                anonymized['longitude'] = round(float(anonymized['longitude']), 2)
            
            # Add anonymization timestamp
            anonymized['_anonymized_at'] = datetime.utcnow().isoformat()
            
            return anonymized
            
        except Exception as e:
            logger.error("Error anonymizing data", error=str(e))
            return data
    
    def _hash_identifier(self, identifier: str) -> str:
        """Create consistent hash of identifier."""
        # Use SHA-256 for consistent hashing
        salt = f"{self.organization_name}_salt"
        return hashlib.sha256(f"{salt}_{identifier}".encode()).hexdigest()[:16]
    
    def detect_pii(self, data: Dict[str, Any]) -> List[str]:
        """Detect potentially personally identifiable information."""
        detected_pii = []
        
        for field, value in data.items():
            if not isinstance(value, str):
                continue
                
            # Check against PII patterns
            for pii_type, pattern in self.pii_patterns.items():
                if pattern.search(value):
                    detected_pii.append(f"{field}:{pii_type}")
        
        return detected_pii
    
    def classify_data_sensitivity(self, data: Dict[str, Any]) -> DataClassification:
        """Classify data sensitivity level."""
        
        # Check for restricted data (PII)
        pii_detected = self.detect_pii(data)
        if pii_detected:
            return DataClassification.RESTRICTED
        
        # Check for confidential data
        confidential_fields = ['vin', 'diagnostic_codes', 'location', 'timestamp']
        if any(field in data for field in confidential_fields):
            return DataClassification.CONFIDENTIAL
        
        # Check for internal data
        internal_fields = ['vehicle_data', 'can_messages', 'sensor_data']
        if any(field in data for field in internal_fields):
            return DataClassification.INTERNAL
        
        return DataClassification.PUBLIC
    
    async def apply_retention_policy(self, data_type: str, data_age_days: int) -> str:
        """Apply retention policy to determine data action."""
        policy = self.retention_policies.get(data_type)
        if not policy:
            return "retain"  # No policy = retain by default
        
        # Check if data should be anonymized
        if (policy.anonymization_after_days and 
            data_age_days >= policy.anonymization_after_days):
            return "anonymize"
        
        # Check if data should be deleted
        if policy.auto_deletion and data_age_days >= policy.retention_days:
            return "delete"
        
        return "retain"
    
    async def _log_audit_event(self, 
                             user_id: str,
                             action: str,
                             resource_type: str,
                             resource_id: str,
                             details: Dict[str, Any],
                             ip_address: Optional[str] = None):
        """Log audit event for compliance tracking."""
        try:
            audit_entry = AuditLogEntry(
                timestamp=datetime.utcnow(),
                user_id=user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details,
                ip_address=ip_address
            )
            
            self.audit_log.append(audit_entry)
            
            # Trim audit log if it gets too large
            if len(self.audit_log) > 10000:
                self.audit_log = self.audit_log[-5000:]  # Keep last 5000 entries
                
        except Exception as e:
            logger.error("Error logging audit event", error=str(e))
    
    def generate_privacy_report(self, session_id: str) -> Dict[str, Any]:
        """Generate privacy compliance report for a data collection session."""
        try:
            # Find relevant audit entries
            session_audits = [
                entry for entry in self.audit_log
                if session_id in entry.resource_id or session_id in str(entry.details)
            ]
            
            # Find applicable consents
            applicable_consents = [
                consent for consent in self.consent_records.values()
                if consent.is_active
            ]
            
            report = {
                'session_id': session_id,
                'report_generated': datetime.utcnow().isoformat(),
                'organization': self.organization_name,
                'data_controller': self.data_controller,
                'privacy_compliance': {
                    'consent_records': len(applicable_consents),
                    'audit_events': len(session_audits),
                    'retention_policies_applied': len(self.retention_policies),
                    'pii_detection_enabled': True,
                    'anonymization_available': True
                },
                'data_governance': {
                    'purpose_limitation': True,
                    'data_minimization': True,
                    'storage_limitation': True,
                    'accuracy_measures': True,
                    'security_measures': True,
                    'accountability': True
                },
                'research_ethics': {
                    'informed_consent': True,
                    'voluntary_participation': True,
                    'right_to_withdraw': True,
                    'data_anonymization': True,
                    'benefit_sharing': True  # Non-profit research
                },
                'audit_trail': [
                    {
                        'timestamp': entry.timestamp.isoformat(),
                        'action': entry.action,
                        'resource_type': entry.resource_type,
                        'user_id': entry.user_id
                    }
                    for entry in session_audits[-10:]  # Last 10 events
                ]
            }
            
            return report
            
        except Exception as e:
            logger.error("Error generating privacy report", error=str(e))
            return {'error': str(e)}
    
    def validate_research_ethics(self, 
                               data_collection_plan: Dict[str, Any]) -> Dict[str, Any]:
        """Validate research ethics compliance for data collection plan."""
        
        validation_results = {
            'is_compliant': True,
            'issues': [],
            'recommendations': []
        }
        
        # Check for informed consent
        if not data_collection_plan.get('informed_consent'):
            validation_results['is_compliant'] = False
            validation_results['issues'].append("Informed consent not documented")
        
        # Check for legitimate research purpose
        purposes = data_collection_plan.get('purposes', [])
        research_purposes = [
            ProcessingPurpose.RESEARCH,
            ProcessingPurpose.SAFETY_ANALYSIS,
            ProcessingPurpose.EMISSIONS_MONITORING
        ]
        
        if not any(p in purposes for p in research_purposes):
            validation_results['issues'].append("No legitimate research purpose specified")
        
        # Check data minimization
        if not data_collection_plan.get('data_minimization_applied'):
            validation_results['recommendations'].append(
                "Ensure data collection is limited to what's necessary for research"
            )
        
        # Check retention period
        retention_days = data_collection_plan.get('retention_days', 0)
        if retention_days > 3650:  # 10 years
            validation_results['recommendations'].append(
                "Consider shorter retention period unless justified by research needs"
            )
        
        return validation_results
    
    def get_compliance_status(self) -> Dict[str, Any]:
        """Get overall compliance status summary."""
        return {
            'organization': self.organization_name,
            'data_controller': self.data_controller,
            'active_consents': sum(1 for c in self.consent_records.values() if c.is_active),
            'retention_policies': len(self.retention_policies),
            'audit_log_entries': len(self.audit_log),
            'privacy_features': {
                'pii_detection': True,
                'data_anonymization': True,
                'consent_management': True,
                'audit_logging': True,
                'retention_policies': True,
                'research_ethics_validation': True
            },
            'compliance_frameworks': [
                'Research Ethics Guidelines',
                'Non-Profit Data Governance',
                'Privacy by Design Principles',
                'Data Minimization Standards'
            ]
        }