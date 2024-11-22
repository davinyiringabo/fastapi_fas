from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from ..models.models import UserType, ApplicationStatus

class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(BaseModel):
    email: EmailStr = Field(..., 
        description="Admin's email address",
        example="admin@example.com"
    )
    password: str = Field(..., 
        description="Strong password",
        min_length=8,
        example="StrongAdminPass123!"
    )
    full_name: str = Field(..., 
        description="Admin's full name",
        example="John Admin"
    )
    user_type: UserType = Field(..., 
        description="Must be 'admin' for this endpoint",
        example=UserType.ADMIN
    )

class User(UserBase):
    id:int
    is_active:bool
    user_type: UserType

    class Config: 
        from_attribute = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[EmailStr] = None
    user_type: Optional[UserType] = None

class FinancialAidBase(BaseModel):
    amount: int
    purpose: str

class FinancialAidCreate(FinancialAidBase):
    pass

class FinancialAid(FinancialAidBase):
    id: int
    student_id: int
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime

    class Config: 
        from_attribute = True

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., 
        description="User's email address",
        example="user@example.com"
    )
    password: str = Field(..., 
        description="User's password",
        example="strongpassword123"
    )

class EmailRequest(BaseModel):
    email: EmailStr = Field(..., 
        description="Email address for password reset",
        example="user@example.com"
    )

class PasswordReset(BaseModel):
    password: str = Field(...,
        min_length=8,
        description="New password",
        example="newstrongpassword123"
    )

class PasswordChange(BaseModel):
    current_password: str = Field(...,
        description="Current password",
        example="oldpassword123"
    )
    new_password: str = Field(...,
        min_length=8,
        description="New password",
        example="newpassword123"
    )

class MessageResponse(BaseModel):
    message: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    user_type: UserType
    is_active: bool
    email_verified: bool

    class Config:
        from_attributes = True