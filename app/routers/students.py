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
