"""
Authentication routes for the Z-areo OBD2 dashboard.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

import structlog

from ..auth import AuthManager, ProfileManager, User, UserRole, AuthenticationError
from ..core.config import settings

logger = structlog.get_logger(__name__)

# Security scheme
security = HTTPBearer()

# Pydantic models for request/response
class LoginRequest(BaseModel):
    username: str
    password: str
    
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class CreateUserRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    role: str = "user"

class UpdateProfileRequest(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None

class UpdateOBD2PermissionsRequest(BaseModel):
    permissions: Dict[str, bool]

class UpdateSystemAccessRequest(BaseModel):
    access: Dict[str, bool]

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Dependency to get database session
async def get_db() -> AsyncSession:
    """Get database session dependency."""
    # This would be properly implemented with your database setup
    # For now, returning a placeholder
    pass

# Dependency to get auth manager
async def get_auth_manager(db: AsyncSession = Depends(get_db)) -> AuthManager:
    """Get authentication manager dependency."""
    jwt_secret = getattr(settings, 'JWT_SECRET', 'your-secret-key-here')
    return AuthManager(
        db_session=db,
        jwt_secret=jwt_secret,
        jwt_expiration=3600,  # 1 hour
        refresh_expiration=86400  # 24 hours
    )

# Dependency to get profile manager
async def get_profile_manager(db: AsyncSession = Depends(get_db)) -> ProfileManager:
    """Get profile manager dependency."""
    return ProfileManager(db_session=db)

# Dependency to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager)
) -> User:
    """Get current authenticated user."""
    try:
        user = await auth_manager.verify_token(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Dependency for admin users only
async def get_current_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify admin privileges."""
    if not current_user.has_role(UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    req: Request,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Authenticate user and return access token."""
    try:
        # Extract device info from request
        device_info = {
            "user_agent": req.headers.get("user-agent"),
            "platform": "web_dashboard"
        }
        
        access_token, refresh_token, user_data = await auth_manager.authenticate_user(
            username=request.username,
            password=request.password,
            device_info=device_info,
            ip_address=req.client.host,
            user_agent=req.headers.get("user-agent")
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=3600,
            user=user_data
        )
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Refresh access token using refresh token."""
    try:
        new_access_token, new_refresh_token = await auth_manager.refresh_token(refresh_token)
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 3600
        }
        
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Log out current user session."""
    try:
        success = await auth_manager.logout(credentials.credentials)
        return {"success": success, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return {"success": False, "message": "Logout failed"}

@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information."""
    return current_user.to_dict(include_sensitive=True)

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_user),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Get all active sessions for current user."""
    sessions = await auth_manager.get_user_sessions(current_user.id)
    return {"sessions": sessions}

@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_user),
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Log out all sessions for current user."""
    revoked_count = await auth_manager.logout_all_sessions(current_user.id)
    return {
        "success": True,
        "message": f"Logged out {revoked_count} sessions",
        "revoked_sessions": revoked_count
    }

@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user's profile."""
    try:
        # Update user fields
        if request.first_name is not None:
            current_user.first_name = request.first_name
        if request.last_name is not None:
            current_user.last_name = request.last_name
        if request.organization is not None:
            current_user.organization = request.organization
        if request.preferences is not None:
            current_user.preferences = {
                **(current_user.preferences or {}),
                **request.preferences
            }
        
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        
        return {
            "success": True,
            "message": "Profile updated successfully",
            "user": current_user.to_dict(include_sensitive=True)
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Profile update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

# Admin-only routes
@router.post("/admin/users", dependencies=[Depends(get_current_admin_user)])
async def create_user(
    request: CreateUserRequest,
    auth_manager: AuthManager = Depends(get_auth_manager)
):
    """Create a new user (admin only)."""
    try:
        # Validate role
        try:
            role = UserRole(request.role)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role specified"
            )
        
        user = await auth_manager.create_user(
            username=request.username,
            email=request.email,
            password=request.password,
            first_name=request.first_name,
            last_name=request.last_name,
            organization=request.organization,
            role=role
        )
        
        return {
            "success": True,
            "message": "User created successfully",
            "user": user.to_dict()
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"User creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/admin/profiles")
async def get_admin_profiles(
    current_admin: User = Depends(get_current_admin_user),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """Get all admin profiles (admin only)."""
    profiles = await profile_manager.get_all_admin_profiles()
    return {"admin_profiles": profiles}

@router.put("/admin/obd2-permissions/{user_id}")
async def update_obd2_permissions(
    user_id: str,
    request: UpdateOBD2PermissionsRequest,
    current_admin: User = Depends(get_current_admin_user),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """Update OBD2 permissions for a user (admin only)."""
    try:
        success = await profile_manager.update_obd2_permissions(
            user_id=user_id,
            permissions=request.permissions,
            updated_by=current_admin.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin profile not found"
            )
        
        return {
            "success": True,
            "message": "OBD2 permissions updated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Permission update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update permissions"
        )

@router.put("/admin/system-access/{user_id}")
async def update_system_access(
    user_id: str,
    request: UpdateSystemAccessRequest,
    current_admin: User = Depends(get_current_admin_user),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """Update system access for a user (admin only)."""
    try:
        success = await profile_manager.update_system_access(
            user_id=user_id,
            access=request.access,
            updated_by=current_admin.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin profile not found"
            )
        
        return {
            "success": True,
            "message": "System access updated successfully"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Access update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update access"
        )

@router.post("/admin/grant-bidirectional/{user_id}")
async def grant_bidirectional_access(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """Grant bidirectional OBD2 access to a user (admin only)."""
    try:
        success = await profile_manager.grant_bidirectional_access(
            user_id=user_id,
            granted_by=current_admin.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin profile not found"
            )
        
        return {
            "success": True,
            "message": "Bidirectional access granted successfully"
        }
        
    except Exception as e:
        logger.error(f"Grant bidirectional access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to grant bidirectional access"
        )

@router.post("/admin/revoke-bidirectional/{user_id}")
async def revoke_bidirectional_access(
    user_id: str,
    current_admin: User = Depends(get_current_admin_user),
    profile_manager: ProfileManager = Depends(get_profile_manager)
):
    """Revoke bidirectional OBD2 access from a user (admin only)."""
    try:
        success = await profile_manager.revoke_bidirectional_access(
            user_id=user_id,
            revoked_by=current_admin.id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Admin profile not found"
            )
        
        return {
            "success": True,
            "message": "Bidirectional access revoked successfully"
        }
        
    except Exception as e:
        logger.error(f"Revoke bidirectional access error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke bidirectional access"
        )