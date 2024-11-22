from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database import get_db
from ..models import models
from ..schemas import schemas
import os
from dotenv import load_dotenv
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordRequestForm
from fastapi import Security

load_dotenv()
router = APIRouter()

# Constants and configurations
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize the security scheme
security = HTTPBearer()

# Utility functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Email functions
def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)

def send_verification_email(email: str, token: str, background_tasks: BackgroundTasks):
    """Send verification email"""
    verification_url = f"{API_BASE_URL}/auth/verify-email/{token}"
    subject = "Verify your email address"
    body = f"""
    <h2>Welcome to Student Financial Aid System!</h2>
    <p>Please click the link below to verify your email address:</p>
    <p><a href="{verification_url}">Verify Email</a></p>
    <p>This link will expire in 24 hours.</p>
    """
    background_tasks.add_task(send_email, email, subject, body)

def send_password_reset_email(email: str, token: str, background_tasks: BackgroundTasks):
    """Send password reset email"""
    reset_url = f"{API_BASE_URL}/auth/reset-password/{token}"
    subject = "Reset your password"
    body = f"""
    <h2>Password Reset Request</h2>
    <p>Click the link below to reset your password:</p>
    <p><a href="{reset_url}">Reset Password</a></p>
    <p>This link will expire in 1 hour.</p>
    """
    background_tasks.add_task(send_email, email, subject, body)

# Define get_current_user before using it in routes
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        token = credentials.credentials  # Get the token from credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Now define all the route handlers
@router.post("/login", response_model=schemas.Token)
async def login(
    credentials: schemas.LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/register", response_model=schemas.UserResponse)
async def register(
    user: schemas.UserCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Register a new user"""
    # Check if email exists
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = pwd_context.hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    
    db_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        user_type=user.user_type,
        is_active=False,  # Will be activated after email verification
        verification_token=verification_token,
        verification_token_expires=datetime.utcnow() + timedelta(days=1)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Send verification email
    send_verification_email(user.email, verification_token, background_tasks)
    
    return db_user

@router.get("/verify-email/{token}", response_model=schemas.MessageResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email address"""
    user = db.query(models.User).filter(
        models.User.verification_token == token,
        models.User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.is_active = True
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    
    db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/forgot-password", response_model=schemas.MessageResponse)
async def forgot_password(
    email_request: schemas.EmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset"""
    user = db.query(models.User).filter(models.User.email == email_request.email).first()
    if user:
        reset_token = secrets.token_urlsafe(32)
        user.reset_token = reset_token
        user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.commit()
        
        send_password_reset_email(user.email, reset_token, background_tasks)
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/reset-password/{token}", response_model=schemas.MessageResponse)
async def reset_password(
    token: str,
    new_password: schemas.PasswordReset,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    user = db.query(models.User).filter(
        models.User.reset_token == token,
        models.User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user.password = pwd_context.hash(new_password.password)
    user.reset_token = None
    user.reset_token_expires = None
    
    db.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/change-password", response_model=schemas.MessageResponse)
async def change_password(
    passwords: schemas.PasswordChange,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    if not pwd_context.verify(passwords.current_password, current_user.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    current_user.password = pwd_context.hash(passwords.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}
