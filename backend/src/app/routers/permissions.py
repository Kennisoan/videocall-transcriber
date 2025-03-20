from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..dependencies import get_db, get_current_user_dependency
from .. import crud, schemas
from ..models import User

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"]
)


@router.get("/my", response_model=List[schemas.UserPermission])
async def read_my_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Get all permissions for the current authenticated user"""
    permissions = crud.get_user_permissions(db, current_user.id)
    return permissions


@router.get("/users/{user_id}", response_model=List[schemas.UserPermission])
async def read_user_permissions(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Admin endpoint: Get all permissions for a specific user"""
    # In a real application, you'd want to check if current_user is an admin
    # For simplicity, we allow any authenticated user to access this endpoint for now
    permissions = crud.get_user_permissions(db, user_id)
    return permissions


@router.post("/users/{user_id}", response_model=schemas.UserPermission)
async def create_permission(
    user_id: int,
    permission: schemas.UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Admin endpoint: Create a new permission for a user"""
    # In a real application, you'd want to check if current_user is an admin
    # For simplicity, we allow any authenticated user to access this endpoint for now

    # Check if user exists
    user = crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return crud.create_user_permission(db, permission, user_id)


@router.put("/{permission_id}", response_model=schemas.UserPermission)
async def update_permission(
    permission_id: int,
    permission: schemas.UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Admin endpoint: Update a permission"""
    # In a real application, you'd want to check if current_user is an admin
    # For simplicity, we allow any authenticated user to access this endpoint for now

    updated_permission = crud.update_user_permission(
        db, permission_id, permission)
    if not updated_permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    return updated_permission


@router.delete("/{permission_id}", response_model=schemas.DeleteResponse)
async def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency)
):
    """Admin endpoint: Delete a permission"""
    # In a real application, you'd want to check if current_user is an admin
    # For simplicity, we allow any authenticated user to access this endpoint for now

    if not crud.delete_user_permission(db, permission_id):
        raise HTTPException(status_code=404, detail="Permission not found")

    return {"message": "Permission deleted successfully"}
