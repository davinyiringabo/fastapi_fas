from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import models
from ..schemas import schemas
from ..routers.auth import get_current_user, get_password_hash

router = APIRouter()

@router.post("/apply", response_model=schemas.FinancialAid)
async def apply_for_aid(
    aid: schemas.FinancialAidCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print("user", current_user)
    if current_user.user_type != models.UserType.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can apply for financial aid"
        )
    
    db_aid = models.FinancialAid(
        **aid.dict(),
        student_id=current_user.id
    )
    db.add(db_aid)
    db.commit()
    db.refresh(db_aid)
    return db_aid

@router.get("/applications", response_model=List[schemas.FinancialAid])
async def get_student_applications(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    print(current_user.full_name, current_user.email, current_user.id)
    if current_user.user_type != models.UserType.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can view their applications"
        )
    print(db.query(models.FinancialAid).all())
    # Fetch applications with student details
    applications = db.query(models.FinancialAid).join(models.Student).filter(models.FinancialAid.student_id == current_user.id).all()
    
    return current_user.applications

@router.get("/applications/{student_id}", response_model=List[schemas.FinancialAid])
async def get_applications_by_student_id(
    student_id: int,
    db: Session = Depends(get_db)
):
    # Fetch applications for the specified student ID
    applications = db.query(models.FinancialAid).filter(models.FinancialAid.student_id == student_id).all()
    
    return applications
