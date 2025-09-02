"""
Example usage of the Pydantic models in the E-commerce API

This file demonstrates how to use the various models created for the project.
"""

from datetime import datetime
from decimal import Decimal
from app.models import (
    # Customer models
    CustomerCreateModel,
    CustomerResponseModel,
    CustomerLoginModel,

    # Category models
    CategoryCreateModel,
    CategoryResponseModel,

    # Product models
    ProductCreateModel,
    ProductResponseModel,
    VariationCreateModel,
    ProductImageCreateModel,

    # Order models
    OrderCreateModel,
    OrderItemCreateModel,
    OrderStatus,

    # Common models
    PaginatedResponse,
    ApiResponse,
    SuccessResponse
)


def example_customer_usage():
    """Example of using customer models"""
    print("=== Customer Models Example ===")

    # Creating a new customer
    new_customer = CustomerCreateModel(
        name="John Doe",
        email="john@example.com",
        password="securepassword123",
        phone="1234567890",
        address="123 Main St, City, Country"
    )
    print(f"New customer data: {new_customer.model_dump()}")

    # Login model
    login_data = CustomerLoginModel(
        email="john@example.com",
        password="securepassword123"
    )
    print(f"Login data: {login_data.model_dump()}")

    # Response model (what you'd return from API)
    customer_response = CustomerResponseModel(
        customer_id=1,
        name="John Doe",
        email="john@example.com",
        phone="1234567890",
        address="123 Main St, City, Country",
        created_at=datetime.now()
    )
    print(f"Customer response: {customer_response.model_dump()}")


def example_category_usage():
    """Example of using category models"""
    print("\n=== Category Models Example ===")

    # Creating a parent category
    parent_category = CategoryCreateModel(
        name="Electronics",
        description="All electronic items",
        parent_id=None
    )
    print(f"Parent category: {parent_category.model_dump()}")

    # Creating a child category
    child_category = CategoryCreateModel(
        name="Smartphones",
        description="Mobile phones and accessories",
        parent_id=1  # Electronics category ID
    )
    print(f"Child category: {child_category.model_dump()}")


def example_product_usage():
    """Example of using product models"""
    print("\n=== Product Models Example ===")

    # Creating a product
    new_product = ProductCreateModel(
        category_id=1,
        name="iPhone 15 Pro",
        description="Latest iPhone with advanced features",
        price=Decimal("999.99"),
        stock=50
    )
    print(f"New product: {new_product.model_dump()}")

    # Creating product variations
    size_variation = VariationCreateModel(
        attribute_name="Storage",
        attribute_value="128GB",
        additional_price=Decimal("0.00"),
        stock=20
    )

    color_variation = VariationCreateModel(
        attribute_name="Color",
        attribute_value="Space Black",
        additional_price=Decimal("0.00"),
        stock=15
    )

    print(f"Storage variation: {size_variation.model_dump()}")
    print(f"Color variation: {color_variation.model_dump()}")

    # Creating product image
    product_image = ProductImageCreateModel(
        image_url="uploads/products/iphone15pro.jpg",
        is_primary=True
    )
    print(f"Product image: {product_image.model_dump()}")


def example_order_usage():
    """Example of using order models"""
    print("\n=== Order Models Example ===")

    # Creating order items
    order_item1 = OrderItemCreateModel(
        product_id=1,
        variation_id=1,
        quantity=2,
        price=Decimal("999.99")
    )

    order_item2 = OrderItemCreateModel(
        product_id=2,
        variation_id=None,
        quantity=1,
        price=Decimal("49.99")
    )

    print(f"Order item 1: {order_item1.model_dump()}")
    print(f"Order item 2: {order_item2.model_dump()}")

    # Creating an order for registered customer
    customer_order = OrderCreateModel(
        total_amount=Decimal("2049.97"),
        customer_id=1,
        status=OrderStatus.PENDING,
        items=[order_item1, order_item2]
    )
    print(f"Customer order: {customer_order.model_dump()}")

    # Creating an order for guest checkout
    guest_order = OrderCreateModel(
        total_amount=Decimal("999.99"),
        guest_name="Jane Smith",
        guest_email="jane@example.com",
        guest_phone="9876543210",
        guest_address="456 Oak St, Another City",
        status=OrderStatus.PENDING,
        items=[order_item1]
    )
    print(f"Guest order: {guest_order.model_dump()}")


def example_response_models():
    """Example of using response models"""
    print("\n=== Response Models Example ===")

    # Success response
    success_response = SuccessResponse(
        message="Customer created successfully",
        data={"customer_id": 1, "name": "John Doe"}
    )
    print(f"Success response: {success_response.model_dump()}")

    # API response with data
    api_response = ApiResponse.success(
        data={"customers": [{"id": 1, "name": "John"}]},
        message="Customers retrieved successfully"
    )
    print(f"API response: {api_response.model_dump()}")

    # Paginated response
    customers_data = [
        {"customer_id": 1, "name": "John", "email": "john@example.com"},
        {"customer_id": 2, "name": "Jane", "email": "jane@example.com"}
    ]

    paginated_response = PaginatedResponse.create(
        data=customers_data,
        total=50,
        page=1,
        limit=10
    )
    print(f"Paginated response: {paginated_response.model_dump()}")


def example_validation():
    """Example of model validation"""
    print("\n=== Model Validation Example ===")

    try:
        # This will pass validation
        valid_customer = CustomerCreateModel(
            name="John Doe",
            email="john@example.com",
            password="password123",
            phone="1234567890"
        )
        print("✅ Valid customer created successfully")

    except Exception as e:
        print(f"❌ Validation error: {e}")

    try:
        # This will fail validation (invalid email)
        invalid_customer = CustomerCreateModel(
            name="John Doe",
            email="invalid-email",
            password="pass",  # Too short
            phone="1234567890"
        )

    except Exception as e:
        print(f"❌ Expected validation error: {e}")


def example_model_serialization():
    """Example of model serialization and deserialization"""
    print("\n=== Model Serialization Example ===")

    # Create a product
    product = ProductCreateModel(
        category_id=1,
        name="Test Product",
        description="A test product",
        price=Decimal("29.99"),
        stock=100
    )

    # Serialize to dictionary
    product_dict = product.model_dump()
    print(f"Serialized product: {product_dict}")

    # Serialize to JSON string
    product_json = product.model_dump_json()
    print(f"JSON string: {product_json}")

    # Deserialize from dictionary
    recreated_product = ProductCreateModel(**product_dict)
    print(f"Recreated product: {recreated_product.model_dump()}")

    # Parse from JSON string
    parsed_product = ProductCreateModel.model_validate_json(product_json)
    print(f"Parsed from JSON: {parsed_product.model_dump()}")


if __name__ == "__main__":
    """Run all examples"""
    example_customer_usage()
    example_category_usage()
    example_product_usage()
    example_order_usage()
    example_response_models()
    example_validation()
    example_model_serialization()

    print("\n🎉 All examples completed successfully!")
    print("\nThese models provide:")
    print("- Strong type validation")
    print("- Automatic serialization/deserialization")
    print("- Clear API documentation")
    print("- Consistent data structures")
    print("- Better error handling")
