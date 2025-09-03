from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class ProductImageBase(BaseModel):
    """Base model for product images"""
    image_url: str
    is_primary: Optional[bool] = False


class ProductImageCreateModel(ProductImageBase):
    """Model for creating a product image"""
    pass


class ProductImageResponseModel(ProductImageBase):
    """Response model for product image"""
    image_id: int
    product_id: int

    class Config:
        from_attributes = True


class VariationBase(BaseModel):
    """Base model for product variations"""
    attribute_name: str  # e.g., "Size", "Color"
    attribute_value: str  # e.g., "Large", "Red"
    additional_price: Optional[Decimal] = Decimal('0.00')
    stock: Optional[int] = 0


class VariationCreateModel(VariationBase):
    """Model for creating a product variation"""
    pass


class VariationUpdateModel(BaseModel):
    """Model for updating a product variation"""
    attribute_name: Optional[str] = None
    attribute_value: Optional[str] = None
    additional_price: Optional[Decimal] = None
    stock: Optional[int] = None


class VariationResponseModel(VariationBase):
    """Response model for product variation"""
    variation_id: int
    product_id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    """Base model for products"""
    category_id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    stock: Optional[int] = 0


class ProductCreateModel(ProductBase):
    """Model for creating a product"""
    # Images and variations will be handled separately in the endpoint
    pass


class ProductUpdateModel(BaseModel):
    """Model for updating a product - all fields optional"""
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    stock: Optional[int] = None


class ProductResponseModel(ProductBase):
    """Response model for product"""
    product_id: int
    created_at: datetime
    images: Optional[List[ProductImageResponseModel]] = []
    variations: Optional[List[VariationResponseModel]] = []

    class Config:
        from_attributes = True


class ProductSummaryModel(ProductBase):
    """Simplified product model without images and variations for listings"""
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ProductWithCategoryModel(ProductResponseModel):
    """Product model that includes category information"""
    category_name: Optional[str] = None
    category_description: Optional[str] = None


# Models for bulk operations
class ProductCreateBulkModel(BaseModel):
    """Model for creating products in bulk"""
    products: List[ProductCreateModel]


class VariationCreateBulkModel(BaseModel):
    """Model for creating variations in bulk"""
    product_id: int
    variations: List[VariationCreateModel]


class ProductSummaryWithImageModel(ProductBase):
    """Simplified product model with first image for listings"""
    product_id: int
    created_at: datetime
    first_image_url: Optional[str] = None  # Add this field

    class Config:
        from_attributes = True
