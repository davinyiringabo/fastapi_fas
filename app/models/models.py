from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Enum, DateTime
from sqlalchemy.orm import relationship
from ..database import Base
import enum
from datetime import datetime

class UserType(enum.Enum):
    STUDENT = "student"
    ADMIN = "admin"
    MANAGER = "manager"

class ApplicationStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class EconomicStatus(enum.Enum):
    POOR = "poor"
    MEDIUM = "medium"
    RICH = "rich"

class DisabilityStatus(enum.Enum):
    DISABLED = "disabled"
    NOT_DISABLED = "not_disabled"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    full_name = Column(String)
    user_type = Column(Enum(UserType))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    applications = relationship("FinancialAid", back_populates="student")

class Student(User):
    __tablename__ = "students"
    id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    age = Column(Integer)
    school = Column(String)
    location = Column(String)
    economic_status = Column(Enum(EconomicStatus))
    disability_status = Column(Enum(DisabilityStatus))
class FinancialAid(Base):
    __tablename__ = "financial_aids"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    student = relationship("Student", back_populates="applications")
    amount = Column(Integer)
    purpose = Column(String)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    student = relationship("User", back_populates="applications")