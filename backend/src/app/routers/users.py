from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..dependencies import get_db, get_current_user_dependency
from .. import crud, schemas
from ..models import User

router = APIRouter(
    prefix="/users",
    tags=["users"]
)


@router.get("/me", response_model=schemas.UserWithPermissions)
async def read_users_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get the current authenticated user with their permissions"""
    db_user = crud.get_user(db, user_id=current_user.id)
    return db_user


@router.patch("/me/name", response_model=schemas.User)
async def update_user_name(
    name_update: schemas.UpdateUserName,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update the current user's name"""
    return crud.update_user_name(db, current_user.id, name_update.name)


@router.get("", response_model=List[schemas.UserWithPermissions])
async def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all users (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only admins can access this endpoint")
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=schemas.UserWithPermissions)
async def read_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get a specific user by ID with their permissions (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only admins can access this endpoint")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.patch("/{user_id}/admin", response_model=schemas.User)
async def update_user_admin_status(
    user_id: int,
    admin_update: schemas.UpdateUserAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Update a user's admin status (admin only)"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only admins can access this endpoint")
    if user_id == current_user.id:
        raise HTTPException(
            status_code=400, detail="Cannot modify your own admin status")
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return crud.update_user_admin_status(db, user_id, admin_update.is_admin)
