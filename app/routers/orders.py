from fastapi import APIRouter, HTTPException, Form, Query
from app.db import get_connection
from app.models import (
    OrderCreateModel,
    OrderUpdateModel,
    OrderResponseModel,
    OrderSummaryModel,
    OrderWithCustomerModel,
    OrderStatus,
    OrderStatusUpdateModel,
    OrderItemCreateModel,
    OrderItemUpdateModel,
    OrderItemResponseModel,
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    MessageResponse
)
from typing import List, Optional
import mysql.connector
from decimal import Decimal
from datetime import datetime

router = APIRouter(prefix="/orders", tags=["orders"])

# ------------------- GET ALL ORDERS -------------------
@router.get("/", response_model=ApiResponse[PaginatedResponse[OrderSummaryModel]])
def get_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None),
    customer_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None, description="Search by guest name or email")
):
    """Get all orders with pagination and filtering"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build base queries
        base_query = """
        SELECT o.order_id, o.customer_id, o.guest_name, o.guest_email,
               o.total_amount, o.status, o.created_at,
               COUNT(oi.order_item_id) as items_count
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        """

        count_query = "SELECT COUNT(DISTINCT o.order_id) FROM orders o"

        # Build WHERE conditions
        conditions = []
        params = []

        if status is not None:
            conditions.append("o.status = %s")
            params.append(status.value)

        if customer_id is not None:
            conditions.append("o.customer_id = %s")
            params.append(customer_id)

        if search:
            conditions.append("(o.guest_name LIKE %s OR o.guest_email LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        # Add WHERE clause if we have conditions
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Get total count
        cursor.execute(count_query + where_clause, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query = base_query + where_clause + " GROUP BY o.order_id ORDER BY o.created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        orders = [
            OrderSummaryModel(
                order_id=row[0],
                customer_id=row[1],
                guest_name=row[2],
                guest_email=row[3],
                total_amount=row[4],
                status=OrderStatus(row[5]),
                created_at=row[6],
                items_count=row[7]
            ) for row in rows
        ]

        paginated_response = PaginatedResponse.create(
            data=orders,
            total=total,
            page=page,
            limit=limit
        )

        return ApiResponse.success(
            data=paginated_response,
            message=f"Retrieved {len(orders)} orders"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- GET ORDER BY ID -------------------
@router.get("/{order_id}", response_model=ApiResponse[OrderResponseModel])
def get_order(order_id: int):
    """Get a specific order by ID with all items"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get order
        cursor.execute("SELECT * FROM orders WHERE order_id = %s", (order_id,))
        order_row = cursor.fetchone()
        if not order_row:
            raise HTTPException(status_code=404, detail="Order not found")

        # Get order items with product information
        cursor.execute("""
            SELECT oi.*, p.name as product_name,
                   v.attribute_name as variation_name, v.attribute_value as variation_value
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN variations v ON oi.variation_id = v.variation_id
            WHERE oi.order_id = %s
            ORDER BY oi.order_item_id
        """, (order_id,))
        item_rows = cursor.fetchall()

        items = [
            OrderItemResponseModel(
                order_item_id=row["order_item_id"],
                order_id=row["order_id"],
                product_id=row["product_id"],
                variation_id=row["variation_id"],
                quantity=row["quantity"],
                price=row["price"],
                product_name=row["product_name"],
                variation_name=row["variation_name"],
                variation_value=row["variation_value"]
            ) for row in item_rows
        ]

        # Get customer information if applicable
        customer_name = None
        customer_email = None
        if order_row["customer_id"]:
            cursor.execute(
                "SELECT name, email FROM customers WHERE customer_id = %s",
                (order_row["customer_id"],)
            )
            customer_row = cursor.fetchone()
            if customer_row:
                customer_name = customer_row["name"]
                customer_email = customer_row["email"]

        order = OrderResponseModel(
            order_id=order_row["order_id"],
            customer_id=order_row["customer_id"],
            guest_name=order_row["guest_name"],
            guest_email=order_row["guest_email"],
            guest_phone=order_row["guest_phone"],
            guest_address=order_row["guest_address"],
            total_amount=order_row["total_amount"],
            status=OrderStatus(order_row["status"]),
            created_at=order_row["created_at"],
            items=items,
            customer_name=customer_name,
            customer_email=customer_email
        )

        return ApiResponse.success(
            data=order,
            message="Order retrieved successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- CREATE ORDER -------------------
@router.post("/", response_model=ApiResponse[OrderResponseModel], status_code=201)
def create_order(order: OrderCreateModel):
    """Create a new order"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validate customer if provided
        if order.customer_id is not None:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (order.customer_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Customer not found")

        # Validate that either customer_id or guest information is provided
        if order.customer_id is None and not order.guest_email:
            raise HTTPException(status_code=400, detail="Either customer_id or guest information must be provided")

        # Insert order
        cursor.execute("""
            INSERT INTO orders (customer_id, guest_name, guest_email, guest_phone, guest_address, total_amount, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            order.customer_id,
            order.guest_name,
            order.guest_email,
            order.guest_phone,
            order.guest_address,
            order.total_amount,
            order.status.value
        ))
        order_id = cursor.lastrowid

        # Add order items if provided
        created_items = []
        for item in order.items:
            # Validate product exists
            cursor.execute("SELECT product_id, name, price FROM products WHERE product_id = %s", (item.product_id,))
            product_row = cursor.fetchone()
            if not product_row:
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")

            # Validate variation if provided
            variation_name = None
            variation_value = None
            if item.variation_id is not None:
                cursor.execute(
                    "SELECT attribute_name, attribute_value FROM variations WHERE variation_id = %s AND product_id = %s",
                    (item.variation_id, item.product_id)
                )
                variation_row = cursor.fetchone()
                if not variation_row:
                    raise HTTPException(status_code=400, detail=f"Variation {item.variation_id} not found for product {item.product_id}")
                variation_name = variation_row[0]
                variation_value = variation_row[1]

            # Insert order item
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, variation_id, quantity, price)
                VALUES (%s, %s, %s, %s, %s)
            """, (order_id, item.product_id, item.variation_id, item.quantity, item.price))

            created_items.append(OrderItemResponseModel(
                order_item_id=cursor.lastrowid,
                order_id=order_id,
                product_id=item.product_id,
                variation_id=item.variation_id,
                quantity=item.quantity,
                price=item.price,
                product_name=product_row[1],
                variation_name=variation_name,
                variation_value=variation_value
            ))

        conn.commit()

        # Get customer information if applicable
        customer_name = None
        customer_email = None
        if order.customer_id:
            cursor.execute("SELECT name, email FROM customers WHERE customer_id = %s", (order.customer_id,))
            customer_row = cursor.fetchone()
            if customer_row:
                customer_name = customer_row[0]
                customer_email = customer_row[1]

        created_order = OrderResponseModel(
            order_id=order_id,
            customer_id=order.customer_id,
            guest_name=order.guest_name,
            guest_email=order.guest_email,
            guest_phone=order.guest_phone,
            guest_address=order.guest_address,
            total_amount=order.total_amount,
            status=order.status,
            created_at=datetime.now(),
            items=created_items,
            customer_name=customer_name,
            customer_email=customer_email
        )

        return ApiResponse.success(
            data=created_order,
            message="Order created successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "customer_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid customer")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- UPDATE ORDER -------------------
@router.put("/{order_id}", response_model=ApiResponse[OrderResponseModel])
def update_order(order_id: int, order: OrderUpdateModel):
    """Update an existing order"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate customer if provided
        if order.customer_id is not None:
            cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (order.customer_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Customer not found")

        # Build dynamic update query
        update_fields = []
        params = []

        if order.total_amount is not None:
            update_fields.append("total_amount = %s")
            params.append(order.total_amount)
        if order.customer_id is not None:
            update_fields.append("customer_id = %s")
            params.append(order.customer_id)
        if order.guest_name is not None:
            update_fields.append("guest_name = %s")
            params.append(order.guest_name)
        if order.guest_email is not None:
            update_fields.append("guest_email = %s")
            params.append(order.guest_email)
        if order.guest_phone is not None:
            update_fields.append("guest_phone = %s")
            params.append(order.guest_phone)
        if order.guest_address is not None:
            update_fields.append("guest_address = %s")
            params.append(order.guest_address)
        if order.status is not None:
            update_fields.append("status = %s")
            params.append(order.status.value)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute update
        query = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = %s"
        params.append(order_id)
        cursor.execute(query, params)
        conn.commit()

        # Return updated order
        return get_order(order_id)

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "customer_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid customer")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- UPDATE ORDER STATUS -------------------
@router.patch("/{order_id}/status", response_model=ApiResponse[OrderResponseModel])
def update_order_status(order_id: int, status_update: OrderStatusUpdateModel):
    """Update order status"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")

        # Update status
        cursor.execute(
            "UPDATE orders SET status = %s WHERE order_id = %s",
            (status_update.status.value, order_id)
        )
        conn.commit()

        # Return updated order
        return get_order(order_id)

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- DELETE ORDER -------------------
@router.delete("/{order_id}", response_model=SuccessResponse)
def delete_order(order_id: int):
    """Delete an order"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")

        # Delete order (cascading delete will handle order_items)
        cursor.execute("DELETE FROM orders WHERE order_id = %s", (order_id,))
        conn.commit()

        return SuccessResponse(
            message="Order deleted successfully",
            data={"deleted_order_id": order_id}
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- ADD ITEM TO ORDER -------------------
@router.post("/{order_id}/items", response_model=ApiResponse[OrderItemResponseModel], status_code=201)
def add_order_item(order_id: int, item: OrderItemCreateModel):
    """Add an item to an existing order"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order exists
        cursor.execute("SELECT order_id FROM orders WHERE order_id = %s", (order_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order not found")

        # Validate product exists
        cursor.execute("SELECT product_id, name FROM products WHERE product_id = %s", (item.product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")

        # Validate variation if provided
        variation_name = None
        variation_value = None
        if item.variation_id is not None:
            cursor.execute(
                "SELECT attribute_name, attribute_value FROM variations WHERE variation_id = %s AND product_id = %s",
                (item.variation_id, item.product_id)
            )
            variation_row = cursor.fetchone()
            if not variation_row:
                raise HTTPException(status_code=400, detail=f"Variation {item.variation_id} not found for product {item.product_id}")
            variation_name = variation_row[0]
            variation_value = variation_row[1]

        # Insert order item
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, variation_id, quantity, price)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_id, item.product_id, item.variation_id, item.quantity, item.price))

        item_id = cursor.lastrowid
        conn.commit()

        created_item = OrderItemResponseModel(
            order_item_id=item_id,
            order_id=order_id,
            product_id=item.product_id,
            variation_id=item.variation_id,
            quantity=item.quantity,
            price=item.price,
            product_name=product_row[1],
            variation_name=variation_name,
            variation_value=variation_value
        )

        return ApiResponse.success(
            data=created_item,
            message="Item added to order successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "product_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid product")
        if "variation_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid variation")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- UPDATE ORDER ITEM -------------------
@router.put("/{order_id}/items/{item_id}", response_model=ApiResponse[OrderItemResponseModel])
def update_order_item(order_id: int, item_id: int, item: OrderItemUpdateModel):
    """Update an order item"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order item exists and belongs to the order
        cursor.execute(
            "SELECT * FROM order_items WHERE order_item_id = %s AND order_id = %s",
            (item_id, order_id)
        )
        existing_item = cursor.fetchone()
        if not existing_item:
            raise HTTPException(status_code=404, detail="Order item not found")

        # Build dynamic update query
        update_fields = []
        params = []

        if item.product_id is not None:
            # Validate product exists
            cursor.execute("SELECT product_id FROM products WHERE product_id = %s", (item.product_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
            update_fields.append("product_id = %s")
            params.append(item.product_id)

        if item.variation_id is not None:
            product_id = item.product_id if item.product_id is not None else existing_item[2]
            cursor.execute(
                "SELECT variation_id FROM variations WHERE variation_id = %s AND product_id = %s",
                (item.variation_id, product_id)
            )
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail=f"Variation {item.variation_id} not found for product {product_id}")
            update_fields.append("variation_id = %s")
            params.append(item.variation_id)

        if item.quantity is not None:
            update_fields.append("quantity = %s")
            params.append(item.quantity)

        if item.price is not None:
            update_fields.append("price = %s")
            params.append(item.price)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute update
        query = f"UPDATE order_items SET {', '.join(update_fields)} WHERE order_item_id = %s"
        params.append(item_id)
        cursor.execute(query, params)
        conn.commit()

        # Fetch updated item with product information
        cursor.execute("""
            SELECT oi.*, p.name as product_name,
                   v.attribute_name as variation_name, v.attribute_value as variation_value
            FROM order_items oi
            LEFT JOIN products p ON oi.product_id = p.product_id
            LEFT JOIN variations v ON oi.variation_id = v.variation_id
            WHERE oi.order_item_id = %s
        """, (item_id,))
        updated_row = cursor.fetchone()

        updated_item = OrderItemResponseModel(
            order_item_id=updated_row[0],
            order_id=updated_row[1],
            product_id=updated_row[2],
            variation_id=updated_row[3],
            quantity=updated_row[4],
            price=updated_row[5],
            product_name=updated_row[6],
            variation_name=updated_row[7],
            variation_value=updated_row[8]
        )

        return ApiResponse.success(
            data=updated_item,
            message="Order item updated successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "product_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid product")
        if "variation_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid variation")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- DELETE ORDER ITEM -------------------
@router.delete("/{order_id}/items/{item_id}", response_model=SuccessResponse)
def delete_order_item(order_id: int, item_id: int):
    """Delete an order item"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if order item exists and belongs to the order
        cursor.execute(
            "SELECT order_item_id FROM order_items WHERE order_item_id = %s AND order_id = %s",
            (item_id, order_id)
        )
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Order item not found")

        # Delete order item
        cursor.execute("DELETE FROM order_items WHERE order_item_id = %s", (item_id,))
        conn.commit()

        return SuccessResponse(
            message="Order item deleted successfully",
            data={"deleted_item_id": item_id}
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- GET ORDERS BY CUSTOMER -------------------
@router.get("/customer/{customer_id}", response_model=ApiResponse[PaginatedResponse[OrderSummaryModel]])
def get_orders_by_customer(
    customer_id: int,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[OrderStatus] = Query(None)
):
    """Get all orders for a specific customer"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if customer exists
        cursor.execute("SELECT customer_id FROM customers WHERE customer_id = %s", (customer_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Customer not found")

        # Calculate offset
        offset = (page - 1) * limit

        # Build query with optional status filter
        base_query = """
        SELECT o.order_id, o.customer_id, o.guest_name, o.guest_email,
               o.total_amount, o.status, o.created_at,
               COUNT(oi.order_item_id) as items_count
        FROM orders o
        LEFT JOIN order_items oi ON o.order_id = oi.order_id
        WHERE o.customer_id = %s
        """

        count_query = "SELECT COUNT(*) FROM orders WHERE customer_id = %s"
        params = [customer_id]

        if status is not None:
            base_query += " AND o.status = %s"
            count_query += " AND status = %s"
            params.append(status.value)

        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query = base_query + " GROUP BY o.order_id ORDER BY o.created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        orders = [
            OrderSummaryModel(
                order_id=row[0],
                customer_id=row[1],
                guest_name=row[2],
                guest_email=row[3],
                total_amount=row[4],
                status=OrderStatus(row[5]),
                created_at=row[6],
                items_count=row[7]
            ) for row in rows
        ]

        paginated_response = PaginatedResponse.create(
            data=orders,
            total=total,
            page=page,
            limit=limit
        )

        return ApiResponse.success(
            data=paginated_response,
            message=f"Retrieved {len(orders)} orders for customer {customer_id}"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
