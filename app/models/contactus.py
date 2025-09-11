from pydantic import BaseModel, EmailStr
from datetime import datetime
class ContactCreate(BaseModel):
    customer_id: int | None = None
    name: str
    email: EmailStr
    phone: str
    message: str

class ContactResponse(BaseModel):
    contact_id: int | None = None
    name: str
    email: EmailStr
    phone: str
    message: str
    customer_id: int | None = None
    created_at: datetime | None = None   # <-- allow datetime

class ContactResponse(BaseModel):
    contact_id: int
    name: str
    email: EmailStr
    phone: str
    message: str
    customer_id: int | None = None
    created_at: datetime