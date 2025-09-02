from pydantic import BaseModel
from typing import Optional, List, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum


# Generic type for pagination
T = TypeVar('T')


class ResponseStatus(str, Enum):
    """Standard response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"


class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    page: int = 1
    limit: int = 10
    offset: Optional[int] = None

    def __post_init__(self):
        if self.offset is None:
            self.offset = (self.page - 1) * self.limit


class SortParams(BaseModel):
    """Standard sorting parameters"""
    sort_by: Optional[str] = None
    sort_order: Optional[str] = "asc"  # asc or desc

    class Config:
        validate_assignment = True


class FilterParams(BaseModel):
    """Base filter parameters"""
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response model"""
    data: List[T]
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        data: List[T],
        total: int,
        page: int,
        limit: int
    ):
        total_pages = (total + limit - 1) // limit
        return cls(
            data=data,
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1
        )


class ApiResponse(BaseModel, Generic[T]):
    """Generic API response model"""
    status: ResponseStatus = ResponseStatus.SUCCESS
    message: str = "Operation completed successfully"
    data: Optional[T] = None
    errors: Optional[List[str]] = None
    timestamp: datetime = datetime.now()

    @classmethod
    def success(cls, data: Optional[T] = None, message: str = "Operation completed successfully"):
        return cls(
            status=ResponseStatus.SUCCESS,
            message=message,
            data=data
        )

    @classmethod
    def error(cls, message: str = "An error occurred", errors: Optional[List[str]] = None):
        return cls(
            status=ResponseStatus.ERROR,
            message=message,
            errors=errors or []
        )

    @classmethod
    def warning(cls, message: str = "Warning", data: Optional[T] = None):
        return cls(
            status=ResponseStatus.WARNING,
            message=message,
            data=data
        )


class SuccessResponse(BaseModel):
    """Simple success response model"""
    success: bool = True
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    timestamp: datetime = datetime.now()
    version: str = "v1"
    database: str = "connected"
    uptime: Optional[int] = None


class BulkOperationResponse(BaseModel):
    """Response model for bulk operations"""
    total_processed: int
    successful: int
    failed: int
    errors: Optional[List[str]] = None
    created_ids: Optional[List[int]] = None


class FileUploadResponse(BaseModel):
    """Response model for file uploads"""
    filename: str
    file_path: str
    file_size: int
    content_type: str
    upload_timestamp: datetime = datetime.now()


class SearchResponse(BaseModel, Generic[T]):
    """Search response model"""
    query: str
    results: List[T]
    total_results: int
    search_time_ms: Optional[float] = None
    suggestions: Optional[List[str]] = None


class IdResponse(BaseModel):
    """Simple response with ID"""
    id: int
    message: str = "Created successfully"


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str


class ValidationError(BaseModel):
    """Validation error model"""
    field: str
    message: str
    value: Optional[Any] = None


class ValidationErrorResponse(BaseModel):
    """Validation error response model"""
    success: bool = False
    message: str = "Validation failed"
    errors: List[ValidationError]


# Database related models
class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class SoftDeleteMixin(BaseModel):
    """Mixin for models with soft delete"""
    deleted_at: Optional[datetime] = None
    is_deleted: bool = False

    class Config:
        from_attributes = True


class AuditMixin(TimestampMixin):
    """Mixin for models with audit trail"""
    created_by: Optional[int] = None
    updated_by: Optional[int] = None

    class Config:
        from_attributes = True


# Common field types
class PhoneNumber(BaseModel):
    """Phone number model with validation"""
    country_code: Optional[str] = None
    number: str

    def __str__(self):
        if self.country_code:
            return f"+{self.country_code}{self.number}"
        return self.number


class Address(BaseModel):
    """Address model"""
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    full_address: Optional[str] = None

    def __str__(self):
        if self.full_address:
            return self.full_address

        parts = [self.street, self.city, self.state, self.postal_code, self.country]
        return ", ".join([part for part in parts if part])


class Money(BaseModel):
    """Money model with currency"""
    amount: float
    currency: str = "USD"

    def __str__(self):
        return f"{self.amount} {self.currency}"


class ImageInfo(BaseModel):
    """Image information model"""
    url: str
    alt_text: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
