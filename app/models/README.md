# E-commerce API Models Documentation

This package contains all the Pydantic models used throughout the E-commerce FastAPI application. These models provide type validation, serialization, and automatic API documentation.

## Overview

The models are organized into several modules:

- **`customers.py`** - Customer-related models
- **`categories.py`** - Product category models
- **`products.py`** - Product, variation, and image models
- **`orders.py`** - Order and order item models
- **`auth.py`** - Authentication and authorization models
- **`common.py`** - Shared utilities and response models

## Model Categories

### Customer Models (`customers.py`)

#### Core Models
- **`CustomerCreateModel`** - For creating new customers
- **`CustomerUpdateModel`** - For updating existing customers (all fields optional)
- **`CustomerResponseModel`** - Standard customer response (excludes password)
- **`CustomerWithPasswordModel`** - Includes password for specific use cases
- **`CustomerLoginModel`** - For customer login requests
- **`CustomerLoginResponseModel`** - For successful login responses

#### Authentication Models
- **`PasswordChangeModel`** - For password change requests
- **`PasswordResetModel`** - For password reset requests
- **`PasswordResetConfirmModel`** - For confirming password resets

```python
# Example usage
customer = CustomerCreateModel(
    name="John Doe",
    email="john@example.com",
    password="securepassword",
    phone="1234567890",
    address="123 Main St"
)
```

### Category Models (`categories.py`)

#### Core Models
- **`CategoryCreateModel`** - For creating categories
- **`CategoryUpdateModel`** - For updating categories
- **`CategoryResponseModel`** - Standard category response
- **`CategoryWithChildrenModel`** - Includes child categories

Categories support hierarchical structure through the `parent_id` field.

```python
# Example: Creating a parent category
electronics = CategoryCreateModel(
    name="Electronics",
    description="Electronic devices and gadgets"
)

# Example: Creating a child category
smartphones = CategoryCreateModel(
    name="Smartphones",
    description="Mobile phones",
    parent_id=1  # Electronics category ID
)
```

### Product Models (`products.py`)

#### Product Models
- **`ProductCreateModel`** - For creating products
- **`ProductUpdateModel`** - For updating products
- **`ProductResponseModel`** - Full product response with images and variations
- **`ProductSummaryModel`** - Simplified product info for listings
- **`ProductWithCategoryModel`** - Includes category information

#### Image Models
- **`ProductImageCreateModel`** - For adding product images
- **`ProductImageResponseModel`** - Product image response

#### Variation Models
- **`VariationCreateModel`** - For creating product variations (size, color, etc.)
- **`VariationUpdateModel`** - For updating variations
- **`VariationResponseModel`** - Variation response

```python
# Example: Creating a product with variations
product = ProductCreateModel(
    category_id=1,
    name="T-Shirt",
    description="Cotton t-shirt",
    price=Decimal("19.99"),
    stock=100
)

# Size variation
size_variation = VariationCreateModel(
    attribute_name="Size",
    attribute_value="Large",
    additional_price=Decimal("0.00"),
    stock=25
)

# Color variation
color_variation = VariationCreateModel(
    attribute_name="Color",
    attribute_value="Blue",
    additional_price=Decimal("2.00"),
    stock=15
)
```

### Order Models (`orders.py`)

#### Order Models
- **`OrderCreateModel`** - For creating orders (supports both customer and guest)
- **`OrderUpdateModel`** - For updating orders
- **`OrderResponseModel`** - Full order response with items
- **`OrderSummaryModel`** - Simplified order info for listings
- **`OrderWithCustomerModel`** - Includes full customer information

#### Order Item Models
- **`OrderItemCreateModel`** - For adding items to orders
- **`OrderItemUpdateModel`** - For updating order items
- **`OrderItemResponseModel`** - Order item response

#### Status and Utilities
- **`OrderStatus`** - Enum for order statuses (pending, processing, shipped, etc.)
- **`OrderCalculationModel`** - For calculating order totals
- **`OrderStatusUpdateModel`** - For updating order status

```python
# Example: Creating an order for a registered customer
order_items = [
    OrderItemCreateModel(
        product_id=1,
        variation_id=2,
        quantity=2,
        price=Decimal("19.99")
    )
]

customer_order = OrderCreateModel(
    total_amount=Decimal("39.98"),
    customer_id=1,
    status=OrderStatus.PENDING,
    items=order_items
)

# Example: Creating a guest order
guest_order = OrderCreateModel(
    total_amount=Decimal("19.99"),
    guest_name="Jane Doe",
    guest_email="jane@example.com",
    guest_phone="9876543210",
    guest_address="456 Oak St",
    status=OrderStatus.PENDING
)
```

### Authentication Models (`auth.py`)

- **`Token`** - JWT token response
- **`TokenData`** - JWT payload data
- **`LoginRequest`** - Login credentials
- **`LoginResponse`** - Successful login response
- **`RegisterRequest`** - User registration data

```python
# Example: Login request
login = LoginRequest(
    email="user@example.com",
    password="password123"
)

# Example: Token response
token = Token(
    access_token="jwt_token_here",
    token_type="bearer",
    expires_in=3600
)
```

### Common Models (`common.py`)

#### Response Models
- **`ApiResponse[T]`** - Generic API response wrapper
- **`PaginatedResponse[T]`** - For paginated results
- **`SuccessResponse`** - Simple success response
- **`ErrorResponse`** - Error response
- **`HealthCheckResponse`** - Health check endpoint response

#### Utility Models
- **`PaginationParams`** - Standard pagination parameters
- **`SortParams`** - Sorting parameters
- **`FilterParams`** - Filtering parameters
- **`FileUploadResponse`** - File upload response
- **`BulkOperationResponse`** - Bulk operation results

#### Mixins
- **`TimestampMixin`** - Adds created_at and updated_at fields
- **`SoftDeleteMixin`** - Adds soft delete functionality
- **`AuditMixin`** - Adds audit trail fields

```python
# Example: Paginated response
paginated_products = PaginatedResponse.create(
    data=[product1, product2, product3],
    total=100,
    page=1,
    limit=10
)

# Example: Success response
success = ApiResponse.success(
    data={"customer_id": 1},
    message="Customer created successfully"
)

# Example: Error response
error = ApiResponse.error(
    message="Validation failed",
    errors=["Email is required", "Password too short"]
)
```

## Key Features

### Type Safety
All models provide strict type validation using Pydantic:

```python
# This will raise a validation error
try:
    invalid_customer = CustomerCreateModel(
        name="",  # Empty name
        email="invalid-email",  # Invalid email format
        password="123"  # Too short
    )
except ValidationError as e:
    print(e.errors())
```

### Automatic Serialization
Models can be easily converted to/from dictionaries and JSON:

```python
# To dictionary
customer_dict = customer.model_dump()

# To JSON string
customer_json = customer.model_dump_json()

# From dictionary
customer = CustomerCreateModel(**data)

# From JSON string
customer = CustomerCreateModel.model_validate_json(json_string)
```

### OpenAPI Documentation
FastAPI automatically generates OpenAPI/Swagger documentation from these models.

### Inheritance and Composition
Models use inheritance to reduce code duplication:

```python
class CustomerBase(BaseModel):
    name: str
    email: EmailStr

class CustomerCreateModel(CustomerBase):
    password: str

class CustomerResponseModel(CustomerBase):
    customer_id: int
    created_at: datetime
```

## Configuration

### Model Configuration
Many models include configuration classes:

```python
class Config:
    from_attributes = True  # Enable ORM mode for database objects
    validate_assignment = True  # Validate on assignment
    use_enum_values = True  # Use enum values in serialization
```

### Field Validation
Fields include validation constraints:

```python
name: str = Field(..., min_length=1, max_length=100)
email: EmailStr  # Automatic email validation
password: str = Field(..., min_length=6)
```

## Usage Examples

See `examples/model_usage.py` for comprehensive usage examples of all models.

## Import Usage

```python
# Import specific models
from app.models import CustomerCreateModel, ProductResponseModel

# Import multiple models
from app.models import (
    CustomerCreateModel,
    CustomerResponseModel,
    OrderCreateModel,
    OrderStatus
)

# Import common response models
from app.models import ApiResponse, PaginatedResponse
```

## Best Practices

1. **Use appropriate models**: Use `CreateModel` for input, `ResponseModel` for output
2. **Validate strictly**: Let Pydantic handle validation automatically
3. **Use type hints**: Always specify proper types for better IDE support
4. **Handle decimals properly**: Use `Decimal` for monetary values
5. **Use enums**: Define enums for fixed choices (like order status)
6. **Paginate large datasets**: Use `PaginatedResponse` for lists
7. **Consistent responses**: Use `ApiResponse` for consistent API responses

## Model Dependencies

Make sure to install required dependencies:

```bash
pip install pydantic[email] python-jose[cryptography] email-validator
```

## Future Enhancements

Potential improvements to consider:

1. **Async validation**: For database-dependent validation
2. **Custom validators**: For complex business rules
3. **Model versioning**: For API versioning support
4. **Schema evolution**: For backward compatibility
5. **Caching**: For frequently used model validation