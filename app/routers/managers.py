from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..routers.auth import get_current_user
from typing import List

router = APIRouter()

@router.get("/applications", response_model=List[schemas.FinancialAid])
async def get_all_applications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != models.UserType.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can view all applications"
        )
    
    applications = db.query(models.FinancialAid).all()
    return applications

@router.put("/applications/{aid_id}/status")
async def update_application_status(
    aid_id: int,
    status: models.ApplicationStatus,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.user_type != models.UserType.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers can update application status"
        )
    
    application = db.query(models.FinancialAid).filter(models.FinancialAid.id == aid_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Application not found"
        )
    
    application.status = status
    db.commit()
    db.refresh(application)
    return {"message": "Application status updated successfully"}
