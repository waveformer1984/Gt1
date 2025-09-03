"""
Database models for authentication and user management.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import uuid

from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import bcrypt
import jwt

Base = declarative_base()

class UserRole(Enum):
    GUEST = "guest"
    USER = "user"
    TECHNICIAN = "technician"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    """User account model with authentication capabilities."""
    
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile information
    first_name = Column(String(50))
    last_name = Column(String(50))
    organization = Column(String(100))
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(20), default=UserRole.USER.value)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Settings and preferences
    preferences = Column(JSON, default=lambda: {})
    permissions = Column(JSON, default=lambda: [])
    
    # Relationships
    admin_profile = relationship("AdminProfile", uselist=False, back_populates="user")
    sessions = relationship("SessionToken", back_populates="user", cascade="all, delete-orphan")
    
    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password: str) -> bool:
        """Verify a password against the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role or higher."""
        role_hierarchy = [
            UserRole.GUEST,
            UserRole.USER, 
            UserRole.TECHNICIAN,
            UserRole.ADMIN,
            UserRole.SUPER_ADMIN
        ]
        user_role_index = role_hierarchy.index(UserRole(self.role))
        required_role_index = role_hierarchy.index(role)
        return user_role_index >= required_role_index
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission."""
        return permission in self.permissions
    
    def generate_jwt_token(self, secret_key: str, expires_in: int = 3600) -> str:
        """Generate a JWT token for the user."""
        payload = {
            'user_id': self.id,
            'username': self.username,
            'role': self.role,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, secret_key, algorithm='HS256')
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Convert user to dictionary representation."""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email if include_sensitive else None,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'organization': self.organization,
            'role': self.role,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'preferences': self.preferences,
            'permissions': self.permissions if include_sensitive else []
        }
        
        if include_sensitive and self.admin_profile:
            data['admin_profile'] = self.admin_profile.to_dict()
            
        return data

class AdminProfile(Base):
    """Extended profile for admin users with additional capabilities."""
    
    __tablename__ = "admin_profiles"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False, unique=True)
    
    # Admin-specific information
    admin_level = Column(Integer, default=1)  # 1=basic admin, 2=senior admin, 3=super admin
    department = Column(String(100))
    access_clearance = Column(String(50), default="standard")
    
    # OBD2 specific permissions
    obd2_permissions = Column(JSON, default=lambda: {
        "read_data": True,
        "write_data": False,
        "bidirectional_access": False,
        "ecu_programming": False,
        "system_configuration": False,
        "user_management": False,
        "audit_access": False
    })
    
    # System access
    system_access = Column(JSON, default=lambda: {
        "dashboard": True,
        "mobile_bridge": False,
        "can_sniffer": False,
        "data_export": False,
        "compliance_manager": False
    })
    
    # Emergency contacts and backup access
    emergency_contact = Column(String(255))
    backup_admin_id = Column(String, ForeignKey('users.id'))
    
    # Audit and tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_admin_action = Column(DateTime)
    
    # Security settings
    require_2fa = Column(Boolean, default=True)
    session_timeout_minutes = Column(Integer, default=60)
    max_concurrent_sessions = Column(Integer, default=3)
    
    # Relationships
    user = relationship("User", back_populates="admin_profile")
    backup_admin = relationship("User", foreign_keys=[backup_admin_id])
    
    def has_obd2_permission(self, permission: str) -> bool:
        """Check if admin has specific OBD2 permission."""
        return self.obd2_permissions.get(permission, False)
    
    def has_system_access(self, system: str) -> bool:
        """Check if admin has access to specific system component."""
        return self.system_access.get(system, False)
    
    def grant_obd2_permission(self, permission: str) -> None:
        """Grant an OBD2 permission to the admin."""
        if self.obd2_permissions is None:
            self.obd2_permissions = {}
        self.obd2_permissions[permission] = True
        self.updated_at = datetime.utcnow()
    
    def revoke_obd2_permission(self, permission: str) -> None:
        """Revoke an OBD2 permission from the admin."""
        if self.obd2_permissions is None:
            self.obd2_permissions = {}
        self.obd2_permissions[permission] = False
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert admin profile to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'admin_level': self.admin_level,
            'department': self.department,
            'access_clearance': self.access_clearance,
            'obd2_permissions': self.obd2_permissions,
            'system_access': self.system_access,
            'emergency_contact': self.emergency_contact,
            'backup_admin_id': self.backup_admin_id,
            'require_2fa': self.require_2fa,
            'session_timeout_minutes': self.session_timeout_minutes,
            'max_concurrent_sessions': self.max_concurrent_sessions,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_admin_action': self.last_admin_action.isoformat() if self.last_admin_action else None
        }

class SessionToken(Base):
    """User session management and tracking."""
    
    __tablename__ = "session_tokens"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey('users.id'), nullable=False)
    token_hash = Column(String(255), nullable=False, unique=True)
    refresh_token_hash = Column(String(255), unique=True)
    
    # Session metadata
    device_info = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Session lifecycle
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Security tracking
    login_method = Column(String(50))  # password, biometric, 2fa, etc.
    security_flags = Column(JSON, default=lambda: {})
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    
    def is_expired(self) -> bool:
        """Check if the session token is expired."""
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self) -> bool:
        """Check if the session is valid and active."""
        return self.is_active and not self.is_expired()
    
    def extend_session(self, additional_minutes: int = 60) -> None:
        """Extend the session expiration time."""
        self.expires_at = datetime.utcnow() + timedelta(minutes=additional_minutes)
        self.last_activity = datetime.utcnow()
    
    def revoke(self) -> None:
        """Revoke the session token."""
        self.is_active = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary representation."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'is_active': self.is_active,
            'login_method': self.login_method,
            'security_flags': self.security_flags
        }