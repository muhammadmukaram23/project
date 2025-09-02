"""
Pydantic models for the E-commerce API

This module provides all the Pydantic models used throughout the application
for request/response validation and serialization.
"""

# Customer models
from .customers import (
    CustomerBase,
    CustomerCreateModel,
    CustomerUpdateModel,
    CustomerResponseModel,
    CustomerWithPasswordModel,
    CustomerLoginModel,
    CustomerLoginResponseModel,
    CustomerSummaryModel,
    PasswordChangeModel,
    PasswordResetModel,
    PasswordResetConfirmModel
)

# Category models
from .categories import (
    CategoryBase,
    CategoryCreateModel,
    CategoryUpdateModel,
    CategoryResponseModel,
    CategoryWithChildrenModel
)

# Product models
from .products import (
    ProductImageBase,
    ProductImageCreateModel,
    ProductImageResponseModel,
    VariationBase,
    VariationCreateModel,
    VariationUpdateModel,
    VariationResponseModel,
    ProductBase,
    ProductCreateModel,
    ProductUpdateModel,
    ProductResponseModel,
    ProductSummaryModel,
    ProductWithCategoryModel,
    ProductCreateBulkModel,
    VariationCreateBulkModel
)

# Order models
from .orders import (
    OrderStatus,
    OrderItemBase,
    OrderItemCreateModel,
    OrderItemUpdateModel,
    OrderItemResponseModel,
    OrderBase,
    OrderCreateModel,
    OrderUpdateModel,
    OrderResponseModel,
    OrderSummaryModel,
    OrderWithCustomerModel,
    OrderStatusUpdateModel,
    OrderCalculationModel,
    OrderCalculationResponseModel,
    OrderCreateBulkModel,
    OrderItemCreateBulkModel
)

# Authentication models
from .auth import (
    Token,
    TokenData,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RefreshTokenRequest,
    ApiKeyRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    PasswordChangeRequest,
    AuthResponse
)

# Common models
from .common import (
    ResponseStatus,
    PaginationParams,
    SortParams,
    FilterParams,
    PaginatedResponse,
    ApiResponse,
    SuccessResponse,
    ErrorResponse,
    HealthCheckResponse,
    BulkOperationResponse,
    FileUploadResponse,
    SearchResponse,
    IdResponse,
    MessageResponse,
    ValidationError,
    ValidationErrorResponse,
    TimestampMixin,
    SoftDeleteMixin,
    AuditMixin,
    PhoneNumber,
    Address,
    Money,
    ImageInfo
)

__all__ = [
    # Customer models
    "CustomerBase",
    "CustomerCreateModel",
    "CustomerUpdateModel",
    "CustomerResponseModel",
    "CustomerWithPasswordModel",
    "CustomerLoginModel",
    "CustomerLoginResponseModel",
    "CustomerSummaryModel",
    "PasswordChangeModel",
    "PasswordResetModel",
    "PasswordResetConfirmModel",

    # Category models
    "CategoryBase",
    "CategoryCreateModel",
    "CategoryUpdateModel",
    "CategoryResponseModel",
    "CategoryWithChildrenModel",

    # Product models
    "ProductImageBase",
    "ProductImageCreateModel",
    "ProductImageResponseModel",
    "VariationBase",
    "VariationCreateModel",
    "VariationUpdateModel",
    "VariationResponseModel",
    "ProductBase",
    "ProductCreateModel",
    "ProductUpdateModel",
    "ProductResponseModel",
    "ProductSummaryModel",
    "ProductWithCategoryModel",
    "ProductCreateBulkModel",
    "VariationCreateBulkModel",

    # Order models
    "OrderStatus",
    "OrderItemBase",
    "OrderItemCreateModel",
    "OrderItemUpdateModel",
    "OrderItemResponseModel",
    "OrderBase",
    "OrderCreateModel",
    "OrderUpdateModel",
    "OrderResponseModel",
    "OrderSummaryModel",
    "OrderWithCustomerModel",
    "OrderStatusUpdateModel",
    "OrderCalculationModel",
    "OrderCalculationResponseModel",
    "OrderCreateBulkModel",
    "OrderItemCreateBulkModel",

    # Authentication models
    "Token",
    "TokenData",
    "LoginRequest",
    "LoginResponse",
    "RegisterRequest",
    "RefreshTokenRequest",
    "ApiKeyRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "PasswordChangeRequest",
    "AuthResponse",

    # Common models
    "ResponseStatus",
    "PaginationParams",
    "SortParams",
    "FilterParams",
    "PaginatedResponse",
    "ApiResponse",
    "SuccessResponse",
    "ErrorResponse",
    "HealthCheckResponse",
    "BulkOperationResponse",
    "FileUploadResponse",
    "SearchResponse",
    "IdResponse",
    "MessageResponse",
    "ValidationError",
    "ValidationErrorResponse",
    "TimestampMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "PhoneNumber",
    "Address",
    "Money",
    "ImageInfo"
]
