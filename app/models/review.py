from datetime import datetime
from pydantic import BaseModel
from typing import Optional


class ReviewResponse(BaseModel):
    review_id: int
    product_id: int
    customer_id: int
    rating: int
    comment: str
    created_at: datetime   # ✅ instead of str
    customer_name: str
    customer_email: str
    order_id: Optional[int] = None
    product_name: str
    first_image_url: Optional[str] = None


class ReviewCreate(BaseModel):
    product_id: int
    customer_id: int
    rating: int
    comment: str

