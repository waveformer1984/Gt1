"""
Authentication Manager for Z-areo OBD2 System
=============================================

Handles user authentication, session management, and security operations.
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update, delete

import structlog

from .models import User, AdminProfile, SessionToken, UserRole
from .security import SecurityManager

logger = structlog.get_logger(__name__)

class AuthenticationError(Exception):
    """Base authentication error."""
    pass

class AuthManager:
    """
    Manages user authentication and session handling for the Z-areo system.
    
    Features:
    - Secure JWT-based authentication
    - Session management with automatic cleanup
    - Role-based access control
    - Security audit logging
    - Multi-device session support
    """
    
    def __init__(self, 
                 db_session: AsyncSession,
                 jwt_secret: str,
                 jwt_expiration: int = 3600,
                 refresh_expiration: int = 86400):
        self.db_session = db_session
        self.jwt_secret = jwt_secret
        self.jwt_expiration = jwt_expiration
        self.refresh_expiration = refresh_expiration
        self.security_manager = SecurityManager()
        
        # Session cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self) -> bool:
        """Initialize the authentication manager."""
        try:
            logger.info("Initializing authentication manager")
            
            # Start session cleanup task
            await self._start_session_cleanup()
            
            # Create default admin user if none exists
            await self._ensure_default_admin()
            
            logger.info("Authentication manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize authentication manager: {e}")
            return False
    
    async def authenticate_user(self, 
                              username: str, 
                              password: str,
                              device_info: Optional[Dict[str, Any]] = None,
                              ip_address: Optional[str] = None,
                              user_agent: Optional[str] = None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Authenticate a user and create a session.
        
        Returns:
            Tuple of (access_token, refresh_token, user_data)
        """
        try:
            # Find user by username or email
            stmt = select(User).options(selectinload(User.admin_profile)).where(
                (User.username == username) | (User.email == username)
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                logger.warning(f"Authentication failed: user not found", username=username)
                raise AuthenticationError("Invalid credentials")
            
            if not user.is_active:
                logger.warning(f"Authentication failed: user inactive", username=username)
                raise AuthenticationError("Account is disabled")
            
            if not user.check_password(password):
                logger.warning(f"Authentication failed: incorrect password", username=username)
                await self.security_manager.log_security_event(
                    "failed_login", 
                    user_id=user.id,
                    details={"reason": "incorrect_password", "ip_address": ip_address}
                )
                raise AuthenticationError("Invalid credentials")
            
            # Update last login
            user.last_login = datetime.utcnow()
            
            # Create session tokens
            access_token = user.generate_jwt_token(self.jwt_secret, self.jwt_expiration)
            refresh_token = self._generate_refresh_token()
            
            # Create session record
            session = SessionToken(
                user_id=user.id,
                token_hash=self._hash_token(access_token),
                refresh_token_hash=self._hash_token(refresh_token),
                expires_at=datetime.utcnow() + timedelta(seconds=self.jwt_expiration),
                device_info=device_info,
                ip_address=ip_address,
                user_agent=user_agent,
                login_method="password"
            )
            
            self.db_session.add(session)
            await self.db_session.commit()
            
            # Log successful authentication
            await self.security_manager.log_security_event(
                "successful_login",
                user_id=user.id,
                details={
                    "session_id": session.id,
                    "ip_address": ip_address,
                    "device_info": device_info
                }
            )
            
            user_data = user.to_dict(include_sensitive=True)
            
            logger.info(f"User authenticated successfully", username=username, user_id=user.id)
            
            return access_token, refresh_token, user_data
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise AuthenticationError("Authentication failed")
    
    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh an access token using a refresh token.
        
        Returns:
            Tuple of (new_access_token, new_refresh_token)
        """
        try:
            refresh_token_hash = self._hash_token(refresh_token)
            
            # Find session with this refresh token
            stmt = select(SessionToken).options(selectinload(SessionToken.user)).where(
                SessionToken.refresh_token_hash == refresh_token_hash,
                SessionToken.is_active == True
            )
            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session:
                raise AuthenticationError("Invalid refresh token")
            
            if session.is_expired():
                await self._revoke_session(session.id)
                raise AuthenticationError("Refresh token expired")
            
            user = session.user
            if not user.is_active:
                raise AuthenticationError("User account disabled")
            
            # Generate new tokens
            new_access_token = user.generate_jwt_token(self.jwt_secret, self.jwt_expiration)
            new_refresh_token = self._generate_refresh_token()
            
            # Update session
            session.token_hash = self._hash_token(new_access_token)
            session.refresh_token_hash = self._hash_token(new_refresh_token)
            session.expires_at = datetime.utcnow() + timedelta(seconds=self.jwt_expiration)
            session.last_activity = datetime.utcnow()
            
            await self.db_session.commit()
            
            logger.info(f"Token refreshed for user", user_id=user.id)
            
            return new_access_token, new_refresh_token
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise AuthenticationError("Token refresh failed")
    
    async def verify_token(self, token: str) -> Optional[User]:
        """
        Verify a JWT token and return the associated user.
        """
        try:
            # Decode JWT token
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            if not user_id:
                return None
            
            # Verify session exists and is active
            token_hash = self._hash_token(token)
            stmt = select(SessionToken).where(
                SessionToken.token_hash == token_hash,
                SessionToken.is_active == True
            )
            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if not session or session.is_expired():
                return None
            
            # Get user with admin profile
            stmt = select(User).options(selectinload(User.admin_profile)).where(
                User.id == user_id,
                User.is_active == True
            )
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Update last activity
                session.last_activity = datetime.utcnow()
                await self.db_session.commit()
            
            return user
            
        except jwt.ExpiredSignatureError:
            logger.debug("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.debug("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None
    
    async def logout(self, token: str) -> bool:
        """Log out a user by revoking their session."""
        try:
            token_hash = self._hash_token(token)
            
            stmt = select(SessionToken).where(
                SessionToken.token_hash == token_hash
            )
            result = await self.db_session.execute(stmt)
            session = result.scalar_one_or_none()
            
            if session:
                await self._revoke_session(session.id)
                
                # Log logout event
                await self.security_manager.log_security_event(
                    "logout",
                    user_id=session.user_id,
                    details={"session_id": session.id}
                )
                
                logger.info(f"User logged out", user_id=session.user_id)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    async def logout_all_sessions(self, user_id: str) -> int:
        """Log out all sessions for a specific user."""
        try:
            stmt = update(SessionToken).where(
                SessionToken.user_id == user_id,
                SessionToken.is_active == True
            ).values(is_active=False)
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            revoked_count = result.rowcount
            
            # Log security event
            await self.security_manager.log_security_event(
                "logout_all_sessions",
                user_id=user_id,
                details={"revoked_sessions": revoked_count}
            )
            
            logger.info(f"All sessions revoked for user", user_id=user_id, count=revoked_count)
            
            return revoked_count
            
        except Exception as e:
            logger.error(f"Logout all sessions error: {e}")
            return 0
    
    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all active sessions for a user."""
        try:
            stmt = select(SessionToken).where(
                SessionToken.user_id == user_id,
                SessionToken.is_active == True
            ).order_by(SessionToken.last_activity.desc())
            
            result = await self.db_session.execute(stmt)
            sessions = result.scalars().all()
            
            return [session.to_dict() for session in sessions]
            
        except Exception as e:
            logger.error(f"Get user sessions error: {e}")
            return []
    
    async def create_user(self, 
                         username: str,
                         email: str,
                         password: str,
                         first_name: Optional[str] = None,
                         last_name: Optional[str] = None,
                         organization: Optional[str] = None,
                         role: UserRole = UserRole.USER) -> User:
        """Create a new user account."""
        try:
            # Check if user already exists
            stmt = select(User).where(
                (User.username == username) | (User.email == email)
            )
            result = await self.db_session.execute(stmt)
            existing_user = result.scalar_one_or_none()
            
            if existing_user:
                raise ValueError("User with this username or email already exists")
            
            # Create new user
            user = User(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                organization=organization,
                role=role.value
            )
            user.set_password(password)
            
            self.db_session.add(user)
            await self.db_session.flush()  # Get the user ID
            
            # Create admin profile if user is admin
            if role in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
                admin_profile = AdminProfile(
                    user_id=user.id,
                    admin_level=3 if role == UserRole.SUPER_ADMIN else 1
                )
                self.db_session.add(admin_profile)
            
            await self.db_session.commit()
            
            logger.info(f"User created successfully", username=username, user_id=user.id)
            
            return user
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"User creation error: {e}")
            raise
    
    def _generate_refresh_token(self) -> str:
        """Generate a secure refresh token."""
        return secrets.token_urlsafe(32)
    
    def _hash_token(self, token: str) -> str:
        """Hash a token for secure storage."""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def _revoke_session(self, session_id: str) -> None:
        """Revoke a specific session."""
        stmt = update(SessionToken).where(
            SessionToken.id == session_id
        ).values(is_active=False)
        
        await self.db_session.execute(stmt)
        await self.db_session.commit()
    
    async def _start_session_cleanup(self) -> None:
        """Start the session cleanup background task."""
        if self._cleanup_task:
            return
        
        self._cleanup_task = asyncio.create_task(self._session_cleanup_loop())
    
    async def _session_cleanup_loop(self) -> None:
        """Background task to clean up expired sessions."""
        while not self._shutdown:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                # Delete expired sessions
                stmt = delete(SessionToken).where(
                    SessionToken.expires_at < datetime.utcnow()
                )
                
                result = await self.db_session.execute(stmt)
                await self.db_session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Cleaned up expired sessions", count=result.rowcount)
                
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
    
    async def _ensure_default_admin(self) -> None:
        """Ensure a default admin user exists."""
        try:
            # Check if any admin users exist
            stmt = select(User).where(User.role == UserRole.SUPER_ADMIN.value)
            result = await self.db_session.execute(stmt)
            admin_user = result.scalar_one_or_none()
            
            if not admin_user:
                # Create default admin
                default_admin = await self.create_user(
                    username="admin",
                    email="admin@zareo-nonprofit.org",
                    password="zareo_admin_2024!",  # Should be changed immediately
                    first_name="System",
                    last_name="Administrator",
                    organization="Z-areo Non-Profit",
                    role=UserRole.SUPER_ADMIN
                )
                
                # Grant full OBD2 permissions
                admin_profile = AdminProfile(
                    user_id=default_admin.id,
                    admin_level=3,
                    department="System Administration",
                    access_clearance="maximum",
                    obd2_permissions={
                        "read_data": True,
                        "write_data": True,
                        "bidirectional_access": True,
                        "ecu_programming": True,
                        "system_configuration": True,
                        "user_management": True,
                        "audit_access": True
                    },
                    system_access={
                        "dashboard": True,
                        "mobile_bridge": True,
                        "can_sniffer": True,
                        "data_export": True,
                        "compliance_manager": True
                    }
                )
                
                self.db_session.add(admin_profile)
                await self.db_session.commit()
                
                logger.info("Default admin user created", username="admin")
                logger.warning("Default admin password should be changed immediately!")
                
        except Exception as e:
            logger.error(f"Failed to create default admin: {e}")
    
    async def cleanup(self) -> None:
        """Clean up the authentication manager."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Authentication manager cleanup completed")