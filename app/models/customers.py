from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class CustomerBase(BaseModel):
    """Base customer model with common fields"""
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class CustomerCreateModel(CustomerBase):
    """Model for creating a new customer"""
    password: str = Field(..., min_length=6, max_length=255)


class CustomerUpdateModel(BaseModel):
    """Model for updating a customer - all fields optional"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6, max_length=255)
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None


class CustomerResponseModel(CustomerBase):
    """Response model for customer (without password for security)"""
    customer_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class CustomerWithPasswordModel(CustomerResponseModel):
    """Response model that includes password (for specific use cases)"""
    password: str


class CustomerLoginModel(BaseModel):
    """Model for customer login"""
    email: EmailStr
    password: str


class CustomerLoginResponseModel(BaseModel):
    """Response model for successful login"""
    customer_id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    access_token: Optional[str] = None  # For when you implement proper JWT tokens

    class Config:
        from_attributes = True


class CustomerSummaryModel(BaseModel):
    """Simplified customer model for listings"""
    customer_id: int
    name: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class PasswordChangeModel(BaseModel):
    """Model for changing customer password"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=255)


class PasswordResetModel(BaseModel):
    """Model for password reset request"""
    email: EmailStr


class PasswordResetConfirmModel(BaseModel):
    """Model for confirming password reset"""
    email: EmailStr
    reset_token: str
    new_password: str = Field(..., min_length=6, max_length=255)
