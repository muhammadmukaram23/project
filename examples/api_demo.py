#!/usr/bin/env python3
"""
API Demo Script for E-commerce FastAPI Application

This script demonstrates how to use the updated FastAPI endpoints
with the new Pydantic models for validation and response handling.

Run this after starting the FastAPI server with:
uvicorn app.main:app --reload

Then run this demo with:
python examples/api_demo.py
"""

import requests
import json
from datetime import datetime
from decimal import Decimal

# Base URL for the API
BASE_URL = "http://localhost:8000"

def print_response(title: str, response: requests.Response):
    """Helper function to print API responses nicely"""
    print(f"\n{'='*50}")
    print(f"{title}")
    print(f"{'='*50}")
    print(f"Status Code: {response.status_code}")
    if response.status_code < 400:
        try:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2, default=str)}")
        except:
            print(f"Response: {response.text}")
    else:
        print(f"Error: {response.text}")

def demo_customers():
    """Demo customer endpoints with new models"""
    print("\n🧑 CUSTOMER API DEMO")

    # 1. Create a customer
    customer_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "password": "securepassword123",
        "phone": "1234567890",
        "address": "123 Main St, City, Country"
    }

    response = requests.post(f"{BASE_URL}/customers/", json=customer_data)
    print_response("1. Create Customer", response)

    if response.status_code == 201:
        customer = response.json()["data"]
        customer_id = customer["customer_id"]

        # 2. Get customer by ID
        response = requests.get(f"{BASE_URL}/customers/{customer_id}")
        print_response("2. Get Customer by ID", response)

        # 3. Update customer
        update_data = {
            "phone": "9876543210",
            "address": "456 Updated Ave, New City"
        }
        response = requests.put(f"{BASE_URL}/customers/{customer_id}", json=update_data)
        print_response("3. Update Customer", response)

        # 4. Customer login
        login_data = {
            "email": "john.doe@example.com",
            "password": "securepassword123"
        }
        response = requests.post(f"{BASE_URL}/customers/login", json=login_data)
        print_response("4. Customer Login", response)

    # 5. Get all customers with pagination
    response = requests.get(f"{BASE_URL}/customers/?page=1&limit=5")
    print_response("5. Get All Customers (Paginated)", response)

    # 6. Search customers
    response = requests.get(f"{BASE_URL}/customers/search/?q=John&limit=10")
    print_response("6. Search Customers", response)

def demo_categories():
    """Demo category endpoints with new models"""
    print("\n📁 CATEGORY API DEMO")

    # 1. Create root category
    category_data = {
        "name": "Electronics",
        "description": "All electronic devices and gadgets",
        "parent_id": None
    }

    response = requests.post(f"{BASE_URL}/categories/", json=category_data)
    print_response("1. Create Root Category", response)

    if response.status_code == 201:
        root_category = response.json()["data"]
        root_category_id = root_category["category_id"]

        # 2. Create child category
        child_category_data = {
            "name": "Smartphones",
            "description": "Mobile phones and accessories",
            "parent_id": root_category_id
        }

        response = requests.post(f"{BASE_URL}/categories/", json=child_category_data)
        print_response("2. Create Child Category", response)

        if response.status_code == 201:
            child_category_id = response.json()["data"]["category_id"]

            # 3. Get category with children
            response = requests.get(f"{BASE_URL}/categories/{root_category_id}/with-children")
            print_response("3. Get Category with Children", response)

    # 4. Get all categories
    response = requests.get(f"{BASE_URL}/categories/?page=1&limit=10")
    print_response("4. Get All Categories", response)

    # 5. Get category hierarchy
    response = requests.get(f"{BASE_URL}/categories/hierarchy/")
    print_response("5. Get Category Hierarchy", response)

    # 6. Search categories
    response = requests.get(f"{BASE_URL}/categories/search/?q=Electronics")
    print_response("6. Search Categories", response)

def demo_products():
    """Demo product endpoints with new models"""
    print("\n📱 PRODUCT API DEMO")

    # First, get a category ID for the product
    response = requests.get(f"{BASE_URL}/categories/?page=1&limit=1")
    if response.status_code == 200 and response.json()["data"]["data"]:
        category_id = response.json()["data"]["data"][0]["category_id"]

        # 1. Create a product (using form data for file uploads)
        product_data = {
            "category_id": category_id,
            "name": "iPhone 15 Pro",
            "description": "Latest iPhone with advanced features",
            "price": 999.99,
            "stock": 50,
            "variation_names": ["Storage", "Color"],
            "variation_values": ["128GB", "Space Black"],
            "variation_prices": [0.00, 0.00],
            "variation_stocks": [25, 25]
        }

        response = requests.post(f"{BASE_URL}/products/", data=product_data)
        print_response("1. Create Product", response)

        if response.status_code == 201:
            product = response.json()["data"]
            product_id = product["product_id"]

            # 2. Get product by ID
            response = requests.get(f"{BASE_URL}/products/{product_id}")
            print_response("2. Get Product by ID", response)

            # 3. Add product variation
            variation_data = {
                "attribute_name": "Storage",
                "attribute_value": "256GB",
                "additional_price": 100.00,
                "stock": 15
            }

            response = requests.post(f"{BASE_URL}/products/{product_id}/variations", json=variation_data)
            print_response("3. Add Product Variation", response)

    # 4. Get all products with filters
    response = requests.get(f"{BASE_URL}/products/?page=1&limit=5&in_stock_only=true")
    print_response("4. Get All Products (In Stock)", response)

    # 5. Search products
    response = requests.get(f"{BASE_URL}/products/search/?q=iPhone&limit=10")
    print_response("5. Search Products", response)

def demo_orders():
    """Demo order endpoints with new models"""
    print("\n📦 ORDER API DEMO")

    # Get a customer ID and product ID for the order
    customers_response = requests.get(f"{BASE_URL}/customers/?page=1&limit=1")
    products_response = requests.get(f"{BASE_URL}/products/?page=1&limit=1")

    if (customers_response.status_code == 200 and
        products_response.status_code == 200 and
        customers_response.json()["data"]["data"] and
        products_response.json()["data"]["data"]):

        customer_id = customers_response.json()["data"]["data"][0]["customer_id"]
        product_id = products_response.json()["data"]["data"][0]["product_id"]

        # 1. Create order for registered customer
        order_data = {
            "customer_id": customer_id,
            "total_amount": 999.99,
            "status": "pending",
            "items": [
                {
                    "product_id": product_id,
                    "variation_id": None,
                    "quantity": 1,
                    "price": 999.99
                }
            ]
        }

        response = requests.post(f"{BASE_URL}/orders/", json=order_data)
        print_response("1. Create Order for Customer", response)

        if response.status_code == 201:
            order_id = response.json()["data"]["order_id"]

            # 2. Get order by ID
            response = requests.get(f"{BASE_URL}/orders/{order_id}")
            print_response("2. Get Order by ID", response)

            # 3. Update order status
            status_data = {"status": "processing"}
            response = requests.patch(f"{BASE_URL}/orders/{order_id}/status", json=status_data)
            print_response("3. Update Order Status", response)

            # 4. Add item to order
            item_data = {
                "product_id": product_id,
                "variation_id": None,
                "quantity": 1,
                "price": 49.99
            }
            response = requests.post(f"{BASE_URL}/orders/{order_id}/items", json=item_data)
            print_response("4. Add Item to Order", response)

    # 5. Create guest order
    guest_order_data = {
        "customer_id": None,
        "guest_name": "Jane Smith",
        "guest_email": "jane.smith@example.com",
        "guest_phone": "9876543210",
        "guest_address": "789 Guest St, Guest City",
        "total_amount": 299.99,
        "status": "pending",
        "items": []
    }

    response = requests.post(f"{BASE_URL}/orders/", json=guest_order_data)
    print_response("5. Create Guest Order", response)

    # 6. Get all orders with pagination
    response = requests.get(f"{BASE_URL}/orders/?page=1&limit=5")
    print_response("6. Get All Orders", response)

def demo_error_handling():
    """Demo error handling with model validation"""
    print("\n❌ ERROR HANDLING DEMO")

    # 1. Invalid customer data (missing required fields)
    invalid_customer = {
        "name": "",  # Empty name
        "email": "invalid-email",  # Invalid email
        "password": "123"  # Too short password
    }

    response = requests.post(f"{BASE_URL}/customers/", json=invalid_customer)
    print_response("1. Invalid Customer Data", response)

    # 2. Non-existent resource
    response = requests.get(f"{BASE_URL}/customers/99999")
    print_response("2. Non-existent Customer", response)

    # 3. Invalid category parent
    invalid_category = {
        "name": "Test Category",
        "parent_id": 99999  # Non-existent parent
    }

    response = requests.post(f"{BASE_URL}/categories/", json=invalid_category)
    print_response("3. Invalid Category Parent", response)

def demo_response_formats():
    """Demo the consistent API response format"""
    print("\n📄 RESPONSE FORMAT DEMO")

    print("""
    All API responses follow a consistent format with the new models:

    Success Response:
    {
        "status": "success",
        "message": "Operation completed successfully",
        "data": { ... actual data ... },
        "timestamp": "2024-01-01T12:00:00"
    }

    Paginated Response:
    {
        "status": "success",
        "message": "Retrieved X items",
        "data": {
            "data": [ ... items ... ],
            "total": 100,
            "page": 1,
            "limit": 10,
            "total_pages": 10,
            "has_next": true,
            "has_prev": false
        },
        "timestamp": "2024-01-01T12:00:00"
    }

    Error Response:
    {
        "success": false,
        "message": "Error description",
        "error_code": "VALIDATION_ERROR",
        "details": { ... error details ... }
    }
    """)

def main():
    """Run the complete API demo"""
    print("🚀 E-COMMERCE API DEMO WITH PYDANTIC MODELS")
    print("=" * 60)

    try:
        # Test if server is running
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code != 200:
            print("❌ FastAPI server is not running!")
            print("Please start the server with: uvicorn app.main:app --reload")
            return

        print("✅ FastAPI server is running!")

        # Run demos
        demo_response_formats()
        demo_customers()
        demo_categories()
        demo_products()
        demo_orders()
        demo_error_handling()

        print(f"\n🎉 Demo completed successfully!")
        print(f"📖 Visit {BASE_URL}/docs for interactive API documentation")
        print(f"📊 Visit {BASE_URL}/redoc for alternative documentation")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API server!")
        print("Make sure the FastAPI server is running on http://localhost:8000")
        print("Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()
