"""
Profile Manager for admin profile management and permissions.
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select, update
import structlog

from .models import User, AdminProfile, UserRole
from .security import SecurityManager

logger = structlog.get_logger(__name__)

class ProfileManager:
    """
    Manages admin profiles and their permissions for the Z-areo system.
    
    Features:
    - Admin profile creation and management
    - OBD2 permission management
    - System access control
    - Profile auditing
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.security_manager = SecurityManager()
    
    async def create_admin_profile(self, 
                                  user_id: str, 
                                  admin_level: int = 1,
                                  department: Optional[str] = None,
                                  obd2_permissions: Optional[Dict[str, bool]] = None,
                                  system_access: Optional[Dict[str, bool]] = None) -> AdminProfile:
        """Create an admin profile for a user."""
        try:
            # Check if user exists and is eligible for admin profile
            stmt = select(User).where(User.id == user_id)
            result = await self.db_session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValueError("User not found")
            
            if not user.has_role(UserRole.ADMIN):
                raise ValueError("User must have admin role or higher")
            
            # Check if admin profile already exists
            stmt = select(AdminProfile).where(AdminProfile.user_id == user_id)
            result = await self.db_session.execute(stmt)
            existing_profile = result.scalar_one_or_none()
            
            if existing_profile:
                raise ValueError("Admin profile already exists for this user")
            
            # Set default permissions
            default_obd2_permissions = {
                "read_data": True,
                "write_data": False,
                "bidirectional_access": False,
                "ecu_programming": False,
                "system_configuration": False,
                "user_management": False,
                "audit_access": False
            }
            
            default_system_access = {
                "dashboard": True,
                "mobile_bridge": False,
                "can_sniffer": False,
                "data_export": False,
                "compliance_manager": False
            }
            
            # Create admin profile
            admin_profile = AdminProfile(
                user_id=user_id,
                admin_level=admin_level,
                department=department,
                obd2_permissions=obd2_permissions or default_obd2_permissions,
                system_access=system_access or default_system_access
            )
            
            self.db_session.add(admin_profile)
            await self.db_session.commit()
            
            # Log the creation
            await self.security_manager.log_security_event(
                "admin_profile_created",
                user_id=user_id,
                details={
                    "admin_level": admin_level,
                    "department": department,
                    "created_by": "system"  # This could be populated with the actual creator
                }
            )
            
            logger.info(f"Admin profile created", user_id=user_id, admin_level=admin_level)
            
            return admin_profile
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to create admin profile: {e}")
            raise
    
    async def get_admin_profile(self, user_id: str) -> Optional[AdminProfile]:
        """Get admin profile for a user."""
        try:
            stmt = select(AdminProfile).options(
                selectinload(AdminProfile.user)
            ).where(AdminProfile.user_id == user_id)
            
            result = await self.db_session.execute(stmt)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get admin profile: {e}")
            return None
    
    async def update_obd2_permissions(self, 
                                     user_id: str, 
                                     permissions: Dict[str, bool],
                                     updated_by: Optional[str] = None) -> bool:
        """Update OBD2 permissions for an admin user."""
        try:
            admin_profile = await self.get_admin_profile(user_id)
            if not admin_profile:
                raise ValueError("Admin profile not found")
            
            # Update permissions
            current_permissions = admin_profile.obd2_permissions or {}
            current_permissions.update(permissions)
            
            stmt = update(AdminProfile).where(
                AdminProfile.user_id == user_id
            ).values(
                obd2_permissions=current_permissions
            )
            
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Log the permission change
            await self.security_manager.log_security_event(
                "obd2_permissions_updated",
                user_id=user_id,
                details={
                    "updated_permissions": permissions,
                    "updated_by": updated_by,
                    "full_permissions": current_permissions
                }
            )
            
            logger.info(f"OBD2 permissions updated", user_id=user_id, permissions=permissions)
            
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update OBD2 permissions: {e}")
            return False
    
    async def update_system_access(self, 
                                  user_id: str, 
                                  access: Dict[str, bool],
                                  updated_by: Optional[str] = None) -> bool:
        """Update system access for an admin user."""
        try:
            admin_profile = await self.get_admin_profile(user_id)
            if not admin_profile:
                raise ValueError("Admin profile not found")
            
            # Update access
            current_access = admin_profile.system_access or {}
            current_access.update(access)
            
            stmt = update(AdminProfile).where(
                AdminProfile.user_id == user_id
            ).values(
                system_access=current_access
            )
            
            await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            # Log the access change
            await self.security_manager.log_security_event(
                "system_access_updated",
                user_id=user_id,
                details={
                    "updated_access": access,
                    "updated_by": updated_by,
                    "full_access": current_access
                }
            )
            
            logger.info(f"System access updated", user_id=user_id, access=access)
            
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to update system access: {e}")
            return False
    
    async def grant_bidirectional_access(self, user_id: str, granted_by: Optional[str] = None) -> bool:
        """Grant bidirectional OBD2 access to an admin user."""
        permissions = {
            "bidirectional_access": True,
            "write_data": True  # Bidirectional typically requires write access
        }
        
        success = await self.update_obd2_permissions(user_id, permissions, granted_by)
        
        if success:
            await self.security_manager.log_security_event(
                "bidirectional_access_granted",
                user_id=user_id,
                details={"granted_by": granted_by}
            )
        
        return success
    
    async def revoke_bidirectional_access(self, user_id: str, revoked_by: Optional[str] = None) -> bool:
        """Revoke bidirectional OBD2 access from an admin user."""
        permissions = {
            "bidirectional_access": False,
            "ecu_programming": False  # Also revoke ECU programming as it requires bidirectional
        }
        
        success = await self.update_obd2_permissions(user_id, permissions, revoked_by)
        
        if success:
            await self.security_manager.log_security_event(
                "bidirectional_access_revoked",
                user_id=user_id,
                details={"revoked_by": revoked_by}
            )
        
        return success
    
    async def set_admin_level(self, user_id: str, admin_level: int, updated_by: Optional[str] = None) -> bool:
        """Update admin level for a user."""
        try:
            if admin_level not in [1, 2, 3]:
                raise ValueError("Admin level must be 1, 2, or 3")
            
            stmt = update(AdminProfile).where(
                AdminProfile.user_id == user_id
            ).values(
                admin_level=admin_level
            )
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            if result.rowcount == 0:
                return False
            
            # Log the level change
            await self.security_manager.log_security_event(
                "admin_level_changed",
                user_id=user_id,
                details={
                    "new_admin_level": admin_level,
                    "updated_by": updated_by
                }
            )
            
            logger.info(f"Admin level updated", user_id=user_id, admin_level=admin_level)
            
            return True
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to set admin level: {e}")
            return False
    
    async def get_all_admin_profiles(self) -> List[Dict[str, Any]]:
        """Get all admin profiles with user information."""
        try:
            stmt = select(AdminProfile).options(
                selectinload(AdminProfile.user)
            ).order_by(AdminProfile.admin_level.desc())
            
            result = await self.db_session.execute(stmt)
            profiles = result.scalars().all()
            
            admin_data = []
            for profile in profiles:
                profile_dict = profile.to_dict()
                if profile.user:
                    profile_dict['user'] = profile.user.to_dict()
                admin_data.append(profile_dict)
            
            return admin_data
            
        except Exception as e:
            logger.error(f"Failed to get admin profiles: {e}")
            return []
    
    async def delete_admin_profile(self, user_id: str, deleted_by: Optional[str] = None) -> bool:
        """Delete an admin profile."""
        try:
            # Get the profile first for logging
            admin_profile = await self.get_admin_profile(user_id)
            if not admin_profile:
                return False
            
            # Delete the profile
            stmt = select(AdminProfile).where(AdminProfile.user_id == user_id)
            result = await self.db_session.execute(stmt)
            profile = result.scalar_one_or_none()
            
            if profile:
                await self.db_session.delete(profile)
                await self.db_session.commit()
                
                # Log the deletion
                await self.security_manager.log_security_event(
                    "admin_profile_deleted",
                    user_id=user_id,
                    details={
                        "deleted_by": deleted_by,
                        "admin_level": admin_profile.admin_level
                    }
                )
                
                logger.info(f"Admin profile deleted", user_id=user_id)
                return True
            
            return False
            
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Failed to delete admin profile: {e}")
            return False
    
    async def check_permission(self, user_id: str, permission_type: str, permission: str) -> bool:
        """Check if a user has a specific permission."""
        try:
            admin_profile = await self.get_admin_profile(user_id)
            if not admin_profile:
                return False
            
            if permission_type == "obd2":
                return admin_profile.has_obd2_permission(permission)
            elif permission_type == "system":
                return admin_profile.has_system_access(permission)
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to check permission: {e}")
            return False