from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class OrderItemBase(BaseModel):
    """Base model for order items"""
    product_id: int
    variation_id: Optional[int] = None
    quantity: int
    price: Decimal


class OrderItemCreateModel(OrderItemBase):
    """Model for creating an order item"""
    pass


class OrderItemUpdateModel(BaseModel):
    """Model for updating an order item"""
    product_id: Optional[int] = None
    variation_id: Optional[int] = None
    quantity: Optional[int] = None
    price: Optional[Decimal] = None


class OrderItemResponseModel(OrderItemBase):
    """Response model for order item"""
    order_item_id: int
    order_id: int
    # Additional product information for convenience
    product_name: Optional[str] = None
    variation_name: Optional[str] = None
    variation_value: Optional[str] = None

    class Config:
        from_attributes = True


class OrderBase(BaseModel):
    """Base model for orders"""
    total_amount: Decimal
    status: Optional[OrderStatus] = OrderStatus.PENDING


class OrderCreateModel(OrderBase):
    """Model for creating an order"""
    # For registered customers
    customer_id: Optional[int] = None

    # For guest checkout
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_address: Optional[str] = None

    # Order items can be added separately or together
    items: Optional[List[OrderItemCreateModel]] = []


class OrderUpdateModel(BaseModel):
    """Model for updating an order"""
    total_amount: Optional[Decimal] = None
    customer_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_address: Optional[str] = None
    status: Optional[OrderStatus] = None


class OrderResponseModel(OrderBase):
    """Response model for order"""
    order_id: int
    customer_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    guest_phone: Optional[str] = None
    guest_address: Optional[str] = None
    created_at: datetime
    items: Optional[List[OrderItemResponseModel]] = []

    # Additional customer information for convenience
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None

    class Config:
        from_attributes = True


class OrderSummaryModel(BaseModel):
    """Simplified order model for listings"""
    order_id: int
    customer_id: Optional[int] = None
    guest_name: Optional[str] = None
    guest_email: Optional[str] = None
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    items_count: Optional[int] = 0

    class Config:
        from_attributes = True


class OrderWithCustomerModel(OrderResponseModel):
    """Order model that includes full customer information"""
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    class Config:
        from_attributes = True


# Models for order processing
class OrderStatusUpdateModel(BaseModel):
    """Model for updating order status"""
    status: OrderStatus


class OrderCalculationModel(BaseModel):
    """Model for calculating order totals"""
    items: List[OrderItemCreateModel]
    discount_amount: Optional[Decimal] = Decimal('0.00')
    tax_amount: Optional[Decimal] = Decimal('0.00')
    shipping_amount: Optional[Decimal] = Decimal('0.00')


class OrderCalculationResponseModel(BaseModel):
    """Response model for order calculations"""
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    shipping_amount: Decimal
    total_amount: Decimal
    items: List[dict]  # Item details with calculated prices


# Models for bulk operations
class OrderCreateBulkModel(BaseModel):
    """Model for creating multiple orders"""
    orders: List[OrderCreateModel]


class OrderItemCreateBulkModel(BaseModel):
    """Model for adding multiple items to an order"""
    order_id: int
    items: List[OrderItemCreateModel]
