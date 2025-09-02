from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    """Token data model for JWT payload"""
    customer_id: Optional[int] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None


class LoginRequest(BaseModel):
    """Login request model"""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response model"""
    customer_id: int
    name: str
    email: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None

    class Config:
        from_attributes = True


class RegisterRequest(BaseModel):
    """Registration request model"""
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
    address: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """Refresh token request model"""
    refresh_token: str


class ApiKeyRequest(BaseModel):
    """API key request model"""
    api_key: str


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str
    confirm_password: str


class PasswordChangeRequest(BaseModel):
    """Password change request model"""
    current_password: str
    new_password: str
    confirm_password: str


class AuthResponse(BaseModel):
    """Generic authentication response"""
    success: bool
    message: str
    data: Optional[dict] = None
