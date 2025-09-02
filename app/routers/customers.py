from fastapi import APIRouter, HTTPException, status, Query
from app.db import get_connection
from app.models import (
    CustomerCreateModel,
    CustomerUpdateModel,
    CustomerResponseModel,
    CustomerWithPasswordModel,
    CustomerLoginModel,
    CustomerLoginResponseModel,
    CustomerSummaryModel,
    ApiResponse,
    PaginatedResponse,
    SuccessResponse
)
from typing import List, Optional
import mysql.connector

router = APIRouter(prefix="/customers", tags=["customers"])


# ------------------- GET ALL WITH PAGINATION -------------------
@router.get("/", response_model=ApiResponse[PaginatedResponse[CustomerSummaryModel]])
def get_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """Get all customers with pagination and optional search"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build query with optional search
        base_query = "SELECT customer_id, name, email, created_at FROM customers"
        count_query = "SELECT COUNT(*) FROM customers"

        params = []
        if search:
            search_condition = " WHERE name LIKE %s OR email LIKE %s"
            base_query += search_condition
            count_query += search_condition
            search_param = f"%{search}%"
            params = [search_param, search_param]

        # Get total count
        cursor.execute(count_query, params)
        total_row = cursor.fetchone()
        total = total_row[0] if total_row else 0

        # Get paginated results
        query = base_query + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        customers = [
            CustomerSummaryModel(
                customer_id=row[0],
                name=row[1],
                email=row[2],
                created_at=row[3]
            ) for row in rows
        ]

        paginated_response = PaginatedResponse.create(
            data=customers,
            total=total,
            page=page,
            limit=limit
        )

        return ApiResponse.success(
            data=paginated_response,
            message=f"Retrieved {len(customers)} customers"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET BY ID -------------------
@router.get("/{customer_id}", response_model=ApiResponse[CustomerResponseModel])
def get_customer(customer_id: int):
    """Get a specific customer by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT customer_id, name, email, phone, address, created_at FROM customers WHERE customer_id = %s",
            (customer_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer = CustomerResponseModel(
            customer_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            created_at=row[5]
        )

        return ApiResponse.success(
            data=customer,
            message="Customer retrieved successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- CREATE -------------------
@router.post("/", response_model=ApiResponse[CustomerResponseModel], status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreateModel):
    """Create a new customer"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if email already exists
        cursor.execute("SELECT customer_id FROM customers WHERE email = %s", (customer.email,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Insert new customer
        cursor.execute(
            "INSERT INTO customers (name, email, password, phone, address) VALUES (%s, %s, %s, %s, %s)",
            (customer.name, customer.email, customer.password, customer.phone, customer.address)
        )
        conn.commit()
        customer_id = cursor.lastrowid

        # Fetch the created customer
        cursor.execute(
            "SELECT customer_id, name, email, phone, address, created_at FROM customers WHERE customer_id = %s",
            (customer_id,)
        )
        row = cursor.fetchone()

        created_customer = CustomerResponseModel(
            customer_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            created_at=row[5]
        )

        return ApiResponse.success(
            data=created_customer,
            message="Customer created successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "email" in str(err):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- UPDATE -------------------
@router.put("/{customer_id}", response_model=ApiResponse[CustomerResponseModel])
def update_customer(customer_id: int, customer: CustomerUpdateModel):
    """Update an existing customer"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if customer exists
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")

        # Build dynamic update query
        update_fields = []
        params = []

        if customer.name is not None:
            update_fields.append("name = %s")
            params.append(customer.name)
        if customer.email is not None:
            # Check if email is already taken by another customer
            cursor.execute(
                "SELECT customer_id FROM customers WHERE email = %s AND customer_id != %s",
                (customer.email, customer_id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            update_fields.append("email = %s")
            params.append(customer.email)
        if customer.password is not None:
            update_fields.append("password = %s")
            params.append(customer.password)
        if customer.phone is not None:
            update_fields.append("phone = %s")
            params.append(customer.phone)
        if customer.address is not None:
            update_fields.append("address = %s")
            params.append(customer.address)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute update
        query = f"UPDATE customers SET {', '.join(update_fields)} WHERE customer_id = %s"
        params.append(customer_id)
        cursor.execute(query, params)
        conn.commit()

        # Fetch updated customer
        cursor.execute(
            "SELECT customer_id, name, email, phone, address, created_at FROM customers WHERE customer_id = %s",
            (customer_id,)
        )
        row = cursor.fetchone()

        updated_customer = CustomerResponseModel(
            customer_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[3],
            address=row[4],
            created_at=row[5]
        )

        return ApiResponse.success(
            data=updated_customer,
            message="Customer updated successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "email" in str(err):
            raise HTTPException(status_code=400, detail="Email already registered")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- DELETE -------------------
@router.delete("/{customer_id}", response_model=SuccessResponse)
def delete_customer(customer_id: int):
    """Delete a customer"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if customer has orders
        cursor.execute("SELECT COUNT(*) FROM orders WHERE customer_id = %s", (customer_id,))
        count_row = cursor.fetchone()
        order_count = count_row[0] if count_row else 0

        if order_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete customer with {order_count} existing orders"
            )

        cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")

        conn.commit()
        return SuccessResponse(
            message="Customer deleted successfully",
            data={"deleted_customer_id": customer_id}
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- LOGIN -------------------
@router.post("/login", response_model=ApiResponse[CustomerLoginResponseModel])
def login_customer(credentials: CustomerLoginModel):
    """Customer login endpoint"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT customer_id, name, email, password, phone, address, created_at FROM customers WHERE email = %s",
            (credentials.email,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # ⚠️ Password check (plaintext for now - should be hashed in production)
        if row[3] != credentials.password:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        login_response = CustomerLoginResponseModel(
            customer_id=row[0],
            name=row[1],
            email=row[2],
            phone=row[4],
            address=row[5],
            created_at=row[6]
            # Note: access_token would be added here when JWT is implemented
        )

        return ApiResponse.success(
            data=login_response,
            message="Login successful"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET CUSTOMER WITH PASSWORD (Admin only) -------------------
@router.get("/{customer_id}/with-password", response_model=ApiResponse[CustomerWithPasswordModel])
def get_customer_with_password(customer_id: int):
    """Get customer with password (for admin purposes)"""
    # TODO: Add admin authentication check
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT customer_id, name, email, password, phone, address, created_at FROM customers WHERE customer_id = %s",
            (customer_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Customer not found")

        customer = CustomerWithPasswordModel(
            customer_id=row[0],
            name=row[1],
            email=row[2],
            password=row[3],
            phone=row[4],
            address=row[5],
            created_at=row[6]
        )

        return ApiResponse.success(
            data=customer,
            message="Customer with password retrieved successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- SEARCH CUSTOMERS -------------------
@router.get("/search/", response_model=ApiResponse[List[CustomerSummaryModel]])
def search_customers(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search customers by name or email"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        SELECT customer_id, name, email, created_at
        FROM customers
        WHERE name LIKE %s OR email LIKE %s
        ORDER BY name
        LIMIT %s
        """
        search_param = f"%{q}%"
        cursor.execute(query, (search_param, search_param, limit))
        rows = cursor.fetchall()

        customers = [
            CustomerSummaryModel(
                customer_id=row[0],
                name=row[1],
                email=row[2],
                created_at=row[3]
            ) for row in rows
        ]

        return ApiResponse.success(
            data=customers,
            message=f"Found {len(customers)} customers matching '{q}'"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
