from sqlalchemy.orm import Session
from . import models, schemas
from .auth import get_password_hash
from typing import List, Optional


def get_recordings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Recording).offset(skip).limit(limit).all()


def get_recording(db: Session, recording_id: int):
    return db.query(models.Recording).filter(models.Recording.id == recording_id).first()


def create_recording(db: Session, recording: schemas.RecordingCreate):
    db_recording = models.Recording(**recording.dict())
    db.add(db_recording)
    db.commit()
    db.refresh(db_recording)
    return db_recording


def delete_recording(db: Session, recording_id: int) -> bool:
    """Delete a recording from the database

    Returns:
        bool: True if recording was deleted, False if recording was not found
    """
    recording = get_recording(db, recording_id)
    if recording is None:
        return False

    db.delete(recording)
    db.commit()
    return True


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        name=user.name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_name(db: Session, user_id: int, name: str):
    """Update a user's name

    Args:
        db: Database session
        user_id: ID of the user to update
        name: New name for the user

    Returns:
        Updated user object or None if user was not found
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return None

    db_user.name = name
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_admin_status(db: Session, user_id: int, is_admin: bool):
    """Update a user's admin status"""
    db_user = get_user(db, user_id)
    if db_user is None:
        return None

    db_user.is_admin = is_admin
    db.commit()
    db.refresh(db_user)
    return db_user


# User Permission CRUD operations

def get_user_permissions(db: Session, user_id: int):
    """Get all permissions for a user"""
    return db.query(models.UserPermission).filter(models.UserPermission.user_id == user_id).all()


def get_user_permission(db: Session, permission_id: int):
    """Get a specific permission by ID"""
    return db.query(models.UserPermission).filter(models.UserPermission.id == permission_id).first()


def user_has_permission_for_group(db: Session, user_id: int, group_name: str) -> bool:
    """Check if a user already has permission for a specific group"""
    return db.query(models.UserPermission)\
             .filter(models.UserPermission.user_id == user_id,
                     models.UserPermission.group_name == group_name)\
             .first() is not None


def create_user_permission(db: Session, permission: schemas.UserPermissionCreate, user_id: int):
    """Create a new permission for a user"""
    # Check if permission already exists
    if user_has_permission_for_group(db, user_id, permission.group_name):
        return None

    db_permission = models.UserPermission(
        user_id=user_id,
        group_name=permission.group_name,
        can_edit=permission.can_edit
    )
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_permission


def update_user_permission(db: Session, permission_id: int, permission: schemas.UserPermissionCreate):
    """Update an existing permission"""
    db_permission = get_user_permission(db, permission_id)
    if db_permission is None:
        return None

    db_permission.group_name = permission.group_name
    db_permission.can_edit = permission.can_edit

    db.commit()
    db.refresh(db_permission)
    return db_permission


def delete_user_permission(db: Session, permission_id: int) -> bool:
    """Delete a user permission"""
    permission = get_user_permission(db, permission_id)
    if permission is None:
        return False

    db.delete(permission)
    db.commit()
    return True


def get_accessible_recordings(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """Get recordings that a user has permission to access based on their group permissions"""
    # Get all groups that the user has permission to access
    user_groups = db.query(models.UserPermission.group_name)\
                    .filter(models.UserPermission.user_id == user_id)\
                    .all()

    # Extract group names from result tuples
    group_names = [group[0] for group in user_groups]

    if not group_names:
        # If user has no permissions, return empty list
        return []

    # Query recordings where meeting_name is in the list of allowed groups
    return db.query(models.Recording)\
             .filter(models.Recording.meeting_name.in_(group_names))\
             .offset(skip)\
             .limit(limit)\
             .all()


def check_recording_access(db: Session, user_id: int, recording_id: int) -> bool:
    """Check if a user has permission to access a specific recording"""
    # Get the recording
    recording = get_recording(db, recording_id)
    if recording is None:
        return False

    # If the recording doesn't have a meeting_name, it can't be accessed
    if not recording.meeting_name:
        return False

    # Check if the user has permission for this meeting_name
    permission = db.query(models.UserPermission)\
                   .filter(models.UserPermission.user_id == user_id,
                           models.UserPermission.group_name == recording.meeting_name)\
                   .first()

    return permission is not None


def get_unique_group_names(db: Session) -> List[str]:
    """Get all unique group names from recordings table"""
    groups = db.query(models.Recording.meeting_name)\
        .filter(models.Recording.meeting_name.isnot(None))\
        .distinct()\
        .all()
    # Filter out None values and extract strings
    return [group[0] for group in groups if group[0]]
