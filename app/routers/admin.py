from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..routers.auth import get_current_user, get_password_hash
from typing import List

# Create two separate routers
public_router = APIRouter()
protected_router = APIRouter()

@public_router.post("/initial-admin", 
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create initial admin user (only works if no admin exists)"
)
async def create_initial_admin(
    admin: schemas.UserCreate,
    db: Session = Depends(get_db)
):
    # Check if any admin exists
    existing_admin = db.query(models.User).filter(
        models.User.user_type == models.UserType.ADMIN
    ).first()
    
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin user already exists. Use admin credentials to create additional admins."
        )
    
    if admin.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User type must be admin"
        )
    
    # Check if email exists
    if db.query(models.User).filter(models.User.email == admin.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create admin user
    db_admin = models.User(
        email=admin.email,
        password=get_password_hash(admin.password),
        full_name=admin.full_name,
        user_type=models.UserType.ADMIN,
        is_active=True,
        email_verified=True  # Initial admin is pre-verified
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    
    return db_admin

# Protected routes
@protected_router.post("/admins", 
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new admin user (requires admin privileges)"
)
async def create_admin(
    admin: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify current user is admin
    if current_user.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create other admins"
        )
    
    # Verify new user is admin type
    if admin.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User type must be admin"
        )
    
    # Check if email exists
    if db.query(models.User).filter(models.User.email == admin.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create admin user
    db_admin = models.User(
        email=admin.email,
        password=get_password_hash(admin.password),
        full_name=admin.full_name,
        user_type=models.UserType.ADMIN,
        is_active=True,
        email_verified=True
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    
    return db_admin

@protected_router.get("/managers", response_model=List[schemas.User])
async def get_all_managers(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view managers"
        )
    
    managers = db.query(models.User)\
        .filter(models.User.user_type == models.UserType.MANAGER)\
        .all()
    return managers

@protected_router.put("/managers/{manager_id}/deactivate")
async def deactivate_manager(
    manager_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can deactivate managers"
        )
    
    manager = db.query(models.User)\
        .filter(models.User.id == manager_id, models.User.user_type == models.UserType.MANAGER)\
        .first()
    
    if not manager:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Manager not found"
        )
    
    manager.is_active = False
    db.commit()
    return {"message": "Manager deactivated successfully"}

@protected_router.get("/students", response_model=List[schemas.User])
async def get_all_students(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != models.UserType.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view all students"
        )
    
    students = db.query(models.User)\
        .filter(models.User.user_type == models.UserType.STUDENT)\
        .all()
    return students
