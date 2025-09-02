from pydantic import BaseModel
from typing import Optional


class CategoryBase(BaseModel):
    """Base category model with common fields"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreateModel(CategoryBase):
    """Model for creating a new category"""
    pass


class CategoryUpdateModel(BaseModel):
    """Model for updating a category - all fields optional"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryResponseModel(CategoryBase):
    """Response model for category with ID"""
    category_id: int

    class Config:
        from_attributes = True


class CategoryWithChildrenModel(CategoryResponseModel):
    """Category model that includes child categories"""
    children: Optional[list['CategoryResponseModel']] = []


# Update forward references
CategoryWithChildrenModel.model_rebuild()
