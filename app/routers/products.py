from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query, Depends
from app.db import get_connection
from app.models import (
    ProductCreateModel,
    ProductUpdateModel,
    ProductResponseModel,
    ProductSummaryModel,
    ProductWithCategoryModel,
    VariationCreateModel,
    VariationUpdateModel,
    VariationResponseModel,
    ProductImageCreateModel,
    ProductImageResponseModel,
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    FileUploadResponse
)
from typing import List, Optional
import mysql.connector
import os
import shutil
from decimal import Decimal
from datetime import datetime

router = APIRouter(prefix="/products", tags=["products"])
UPLOAD_DIR = "uploads/products"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ------------------- GET ALL PRODUCTS -------------------
@router.get("/", response_model=ApiResponse[PaginatedResponse[ProductSummaryModel]])
def get_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    in_stock_only: bool = Query(False)
):
    """Get all products with pagination and filtering"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build base queries
        base_query = "SELECT product_id, category_id, name, description, price, stock, created_at FROM products"
        count_query = "SELECT COUNT(*) FROM products"

        # Build WHERE conditions
        conditions = []
        params = []

        if search:
            conditions.append("(name LIKE %s OR description LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        if category_id is not None:
            conditions.append("category_id = %s")
            params.append(category_id)

        if min_price is not None:
            conditions.append("price >= %s")
            params.append(min_price)

        if max_price is not None:
            conditions.append("price <= %s")
            params.append(max_price)

        if in_stock_only:
            conditions.append("stock > 0")

        # Add WHERE clause if we have conditions
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Get total count
        cursor.execute(count_query + where_clause, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query = base_query + where_clause + " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        products = [
            ProductSummaryModel(
                product_id=row[0],
                category_id=row[1],
                name=row[2],
                description=row[3],
                price=row[4],
                stock=row[5],
                created_at=row[6]
            ) for row in rows
        ]

        paginated_response = PaginatedResponse.create(
            data=products,
            total=total,
            page=page,
            limit=limit
        )

        return ApiResponse.success(
            data=paginated_response,
            message=f"Retrieved {len(products)} products"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- GET PRODUCT BY ID -------------------
@router.get("/{product_id}", response_model=ApiResponse[ProductResponseModel])
def get_product(product_id: int):
    """Get a specific product by ID with images and variations"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get product
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            raise HTTPException(status_code=404, detail="Product not found")

        # Get product images
        cursor.execute("SELECT * FROM product_images WHERE product_id = %s ORDER BY is_primary DESC", (product_id,))
        image_rows = cursor.fetchall()

        images = [
            ProductImageResponseModel(
                image_id=row["image_id"],
                product_id=row["product_id"],
                image_url=row["image_url"],
                is_primary=row["is_primary"]
            ) for row in image_rows
        ]

        # Get product variations
        cursor.execute("SELECT * FROM variations WHERE product_id = %s ORDER BY attribute_name, attribute_value", (product_id,))
        variation_rows = cursor.fetchall()

        variations = [
            VariationResponseModel(
                variation_id=row["variation_id"],
                product_id=row["product_id"],
                attribute_name=row["attribute_name"],
                attribute_value=row["attribute_value"],
                additional_price=row["additional_price"],
                stock=row["stock"]
            ) for row in variation_rows
        ]

        product = ProductResponseModel(
            product_id=product_row["product_id"],
            category_id=product_row["category_id"],
            name=product_row["name"],
            description=product_row["description"],
            price=product_row["price"],
            stock=product_row["stock"],
            created_at=product_row["created_at"],
            images=images,
            variations=variations
        )

        return ApiResponse.success(
            data=product,
            message="Product retrieved successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- CREATE PRODUCT -------------------
@router.post("/", response_model=ApiResponse[ProductResponseModel], status_code=201)
def create_product(
    category_id: int = Form(...),
    name: str = Form(...),
    description: str = Form(None),
    price: float = Form(...),
    stock: int = Form(...),
    images: List[UploadFile] = File([]),
    variation_names: List[str] = Form([]),
    variation_values: List[str] = Form([]),
    variation_prices: List[float] = Form([]),
    variation_stocks: List[int] = Form([]),
):
    """Create a new product with optional images and variations"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Validate category exists
        cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Category not found")

        # Validate variation arrays have same length
        variation_arrays = [variation_names, variation_values, variation_prices, variation_stocks]
        if variation_names:  # If variations are provided
            if not all(len(arr) == len(variation_names) for arr in variation_arrays):
                raise HTTPException(status_code=400, detail="All variation arrays must have the same length")

        # Insert product
        cursor.execute(
            "INSERT INTO products (category_id, name, description, price, stock) VALUES (%s, %s, %s, %s, %s)",
            (category_id, name, description, Decimal(str(price)), stock),
        )
        product_id = cursor.lastrowid

        # Save product images
        saved_images = []
        for i, img in enumerate(images):
            if img.filename:
                # Generate unique filename
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{product_id}_{timestamp}_{i}_{img.filename}"
                file_path = os.path.join(UPLOAD_DIR, filename)

                # Save file
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(img.file, buffer)

                # Insert image record
                cursor.execute(
                    "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)",
                    (product_id, file_path, i == 0),  # First image is primary
                )

                saved_images.append(ProductImageResponseModel(
                    image_id=cursor.lastrowid,
                    product_id=product_id,
                    image_url=file_path,
                    is_primary=i == 0
                ))

        # Save product variations
        saved_variations = []
        for i in range(len(variation_names)):
            cursor.execute(
                "INSERT INTO variations (product_id, attribute_name, attribute_value, additional_price, stock) VALUES (%s, %s, %s, %s, %s)",
                (product_id, variation_names[i], variation_values[i], Decimal(str(variation_prices[i])), variation_stocks[i]),
            )

            saved_variations.append(VariationResponseModel(
                variation_id=cursor.lastrowid,
                product_id=product_id,
                attribute_name=variation_names[i],
                attribute_value=variation_values[i],
                additional_price=Decimal(str(variation_prices[i])),
                stock=variation_stocks[i]
            ))

        conn.commit()

        # Create response
        created_product = ProductResponseModel(
            product_id=product_id,
            category_id=category_id,
            name=name,
            description=description,
            price=Decimal(str(price)),
            stock=stock,
            created_at=datetime.now(),
            images=saved_images,
            variations=saved_variations
        )

        return ApiResponse.success(
            data=created_product,
            message="Product created successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "category_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid category")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- UPDATE PRODUCT -------------------
@router.put("/{product_id}", response_model=ApiResponse[ProductResponseModel])
def update_product(
    product_id: int,
    category_id: Optional[int] = Form(None),
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    stock: Optional[int] = Form(None),
    images: List[UploadFile] = File([]),
    replace_images: bool = Form(False),
    variation_names: List[str] = Form([]),
    variation_values: List[str] = Form([]),
    variation_prices: List[float] = Form([]),
    variation_stocks: List[int] = Form([]),
    replace_variations: bool = Form(False),
):
    """Update an existing product"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Check if product exists
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        existing_product = cursor.fetchone()
        if not existing_product:
            raise HTTPException(status_code=404, detail="Product not found")

        # Validate category if provided
        if category_id is not None:
            cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (category_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Category not found")

        # Build dynamic update query for product
        update_fields = []
        params = []

        if category_id is not None:
            update_fields.append("category_id = %s")
            params.append(category_id)
        if name is not None:
            update_fields.append("name = %s")
            params.append(name)
        if description is not None:
            update_fields.append("description = %s")
            params.append(description)
        if price is not None:
            update_fields.append("price = %s")
            params.append(Decimal(str(price)))
        if stock is not None:
            update_fields.append("stock = %s")
            params.append(stock)

        # Update product if there are fields to update
        if update_fields:
            query = f"UPDATE products SET {', '.join(update_fields)} WHERE product_id = %s"
            params.append(product_id)
            cursor.execute(query, params)

        # Handle images
        if replace_images and images:
            # Delete old images
            cursor.execute("DELETE FROM product_images WHERE product_id = %s", (product_id,))

            # Add new images
            for i, img in enumerate(images):
                if img.filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{product_id}_{timestamp}_{i}_{img.filename}"
                    file_path = os.path.join(UPLOAD_DIR, filename)

                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)

                    cursor.execute(
                        "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)",
                        (product_id, file_path, i == 0),
                    )
        elif images:  # Add new images without replacing
            for img in images:
                if img.filename:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{product_id}_{timestamp}_{img.filename}"
                    file_path = os.path.join(UPLOAD_DIR, filename)

                    with open(file_path, "wb") as buffer:
                        shutil.copyfileobj(img.file, buffer)

                    cursor.execute(
                        "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)",
                        (product_id, file_path, False),
                    )

        # Handle variations
        if replace_variations:
            cursor.execute("DELETE FROM variations WHERE product_id = %s", (product_id,))

        if variation_names:
            # Validate variation arrays
            variation_arrays = [variation_names, variation_values, variation_prices, variation_stocks]
            if not all(len(arr) == len(variation_names) for arr in variation_arrays):
                raise HTTPException(status_code=400, detail="All variation arrays must have the same length")

            if replace_variations:
                # Add new variations
                for i in range(len(variation_names)):
                    cursor.execute(
                        "INSERT INTO variations (product_id, attribute_name, attribute_value, additional_price, stock) VALUES (%s, %s, %s, %s, %s)",
                        (product_id, variation_names[i], variation_values[i], Decimal(str(variation_prices[i])), variation_stocks[i]),
                    )

        conn.commit()

        # Fetch updated product with images and variations
        cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
        updated_product_row = cursor.fetchone()

        # Get images
        cursor.execute("SELECT * FROM product_images WHERE product_id = %s ORDER BY is_primary DESC", (product_id,))
        image_rows = cursor.fetchall()
        images = [
            ProductImageResponseModel(
                image_id=row["image_id"],
                product_id=row["product_id"],
                image_url=row["image_url"],
                is_primary=row["is_primary"]
            ) for row in image_rows
        ]

        # Get variations
        cursor.execute("SELECT * FROM variations WHERE product_id = %s", (product_id,))
        variation_rows = cursor.fetchall()
        variations = [
            VariationResponseModel(
                variation_id=row["variation_id"],
                product_id=row["product_id"],
                attribute_name=row["attribute_name"],
                attribute_value=row["attribute_value"],
                additional_price=row["additional_price"],
                stock=row["stock"]
            ) for row in variation_rows
        ]

        updated_product = ProductResponseModel(
            product_id=updated_product_row["product_id"],
            category_id=updated_product_row["category_id"],
            name=updated_product_row["name"],
            description=updated_product_row["description"],
            price=updated_product_row["price"],
            stock=updated_product_row["stock"],
            created_at=updated_product_row["created_at"],
            images=images,
            variations=variations
        )

        return ApiResponse.success(
            data=updated_product,
            message="Product updated successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "category_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid category")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- DELETE PRODUCT -------------------
@router.delete("/{product_id}", response_model=SuccessResponse)
def delete_product(product_id: int):
    """Delete a product"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if product exists
        cursor.execute("SELECT name FROM products WHERE product_id = %s", (product_id,))
        product_row = cursor.fetchone()
        if not product_row:
            raise HTTPException(status_code=404, detail="Product not found")

        product_name = product_row[0]

        # Check if product is in any orders
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE product_id = %s", (product_id,))
        order_count = cursor.fetchone()[0]
        if order_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete product '{product_name}' as it exists in {order_count} orders"
            )

        # Delete product (cascading deletes will handle images and variations)
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()

        return SuccessResponse(
            message=f"Product '{product_name}' deleted successfully",
            data={"deleted_product_id": product_id}
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "order_items" in str(err).lower():
            raise HTTPException(status_code=400, detail="Cannot delete product that exists in orders")
        raise HTTPException(status_code=400, detail="Cannot delete product due to foreign key constraints")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- ADD PRODUCT IMAGE -------------------
@router.post("/{product_id}/images", response_model=ApiResponse[ProductImageResponseModel], status_code=201)
def add_product_image(
    product_id: int,
    image: UploadFile = File(...),
    is_primary: bool = Form(False)
):
    """Add an image to a product"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if product exists
        cursor.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")

        if not image.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # If setting as primary, unset other primary images
        if is_primary:
            cursor.execute("UPDATE product_images SET is_primary = FALSE WHERE product_id = %s", (product_id,))

        # Save image file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{product_id}_{timestamp}_{image.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Insert image record
        cursor.execute(
            "INSERT INTO product_images (product_id, image_url, is_primary) VALUES (%s, %s, %s)",
            (product_id, file_path, is_primary),
        )
        image_id = cursor.lastrowid
        conn.commit()

        created_image = ProductImageResponseModel(
            image_id=image_id,
            product_id=product_id,
            image_url=file_path,
            is_primary=is_primary
        )

        return ApiResponse.success(
            data=created_image,
            message="Product image added successfully"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- DELETE PRODUCT IMAGE -------------------
@router.delete("/{product_id}/images/{image_id}", response_model=SuccessResponse)
def delete_product_image(product_id: int, image_id: int):
    """Delete a product image"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if image exists and belongs to the product
        cursor.execute(
            "SELECT image_url FROM product_images WHERE image_id = %s AND product_id = %s",
            (image_id, product_id)
        )
        image_row = cursor.fetchone()
        if not image_row:
            raise HTTPException(status_code=404, detail="Product image not found")

        # Delete from database
        cursor.execute("DELETE FROM product_images WHERE image_id = %s", (image_id,))
        conn.commit()

        # Try to delete physical file (don't fail if file doesn't exist)
        try:
            if os.path.exists(image_row[0]):
                os.remove(image_row[0])
        except OSError:
            pass  # File deletion failed, but database record is removed

        return SuccessResponse(
            message="Product image deleted successfully",
            data={"deleted_image_id": image_id}
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- ADD PRODUCT VARIATION -------------------
@router.post("/{product_id}/variations", response_model=ApiResponse[VariationResponseModel], status_code=201)
def add_product_variation(product_id: int, variation: VariationCreateModel):
    """Add a variation to a product"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if product exists
        cursor.execute("SELECT product_id FROM products WHERE product_id = %s", (product_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Product not found")

        # Check if variation already exists
        cursor.execute(
            "SELECT variation_id FROM variations WHERE product_id = %s AND attribute_name = %s AND attribute_value = %s",
            (product_id, variation.attribute_name, variation.attribute_value)
        )
        if cursor.fetchone():
            raise HTTPException(
                status_code=400,
                detail=f"Variation {variation.attribute_name}: {variation.attribute_value} already exists"
            )

        # Insert variation
        cursor.execute(
            "INSERT INTO variations (product_id, attribute_name, attribute_value, additional_price, stock) VALUES (%s, %s, %s, %s, %s)",
            (product_id, variation.attribute_name, variation.attribute_value, variation.additional_price, variation.stock),
        )
        variation_id = cursor.lastrowid
        conn.commit()

        created_variation = VariationResponseModel(
            variation_id=variation_id,
            product_id=product_id,
            attribute_name=variation.attribute_name,
            attribute_value=variation.attribute_value,
            additional_price=variation.additional_price,
            stock=variation.stock
        )

        return ApiResponse.success(
            data=created_variation,
            message="Product variation added successfully"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- UPDATE PRODUCT VARIATION -------------------
@router.put("/{product_id}/variations/{variation_id}", response_model=ApiResponse[VariationResponseModel])
def update_product_variation(product_id: int, variation_id: int, variation: VariationUpdateModel):
    """Update a product variation"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if variation exists and belongs to the product
        cursor.execute(
            "SELECT * FROM variations WHERE variation_id = %s AND product_id = %s",
            (variation_id, product_id)
        )
        existing_variation = cursor.fetchone()
        if not existing_variation:
            raise HTTPException(status_code=404, detail="Product variation not found")

        # Build dynamic update query
        update_fields = []
        params = []

        if variation.attribute_name is not None:
            update_fields.append("attribute_name = %s")
            params.append(variation.attribute_name)
        if variation.attribute_value is not None:
            update_fields.append("attribute_value = %s")
            params.append(variation.attribute_value)
        if variation.additional_price is not None:
            update_fields.append("additional_price = %s")
            params.append(variation.additional_price)
        if variation.stock is not None:
            update_fields.append("stock = %s")
            params.append(variation.stock)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute update
        query = f"UPDATE variations SET {', '.join(update_fields)} WHERE variation_id = %s"
        params.append(variation_id)
        cursor.execute(query, params)
        conn.commit()

        # Fetch updated variation
        cursor.execute("SELECT * FROM variations WHERE variation_id = %s", (variation_id,))
        updated_row = cursor.fetchone()

        updated_variation = VariationResponseModel(
            variation_id=updated_row[0],
            product_id=updated_row[1],
            attribute_name=updated_row[2],
            attribute_value=updated_row[3],
            additional_price=updated_row[4],
            stock=updated_row[5]
        )

        return ApiResponse.success(
            data=updated_variation,
            message="Product variation updated successfully"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- DELETE PRODUCT VARIATION -------------------
@router.delete("/{product_id}/variations/{variation_id}", response_model=SuccessResponse)
def delete_product_variation(product_id: int, variation_id: int):
    """Delete a product variation"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if variation exists and belongs to the product
        cursor.execute(
            "SELECT attribute_name, attribute_value FROM variations WHERE variation_id = %s AND product_id = %s",
            (variation_id, product_id)
        )
        variation_row = cursor.fetchone()
        if not variation_row:
            raise HTTPException(status_code=404, detail="Product variation not found")

        # Check if variation is used in orders
        cursor.execute("SELECT COUNT(*) FROM order_items WHERE variation_id = %s", (variation_id,))
        order_count = cursor.fetchone()[0]
        if order_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete variation '{variation_row[0]}: {variation_row[1]}' as it exists in {order_count} orders"
            )

        # Delete variation
        cursor.execute("DELETE FROM variations WHERE variation_id = %s", (variation_id,))
        conn.commit()

        return SuccessResponse(
            message=f"Product variation '{variation_row[0]}: {variation_row[1]}' deleted successfully",
            data={"deleted_variation_id": variation_id}
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()

# ------------------- SEARCH PRODUCTS -------------------
@router.get("/search/", response_model=ApiResponse[List[ProductSummaryModel]])
def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search products by name or description"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        SELECT product_id, category_id, name, description, price, stock, created_at
        FROM products
        WHERE name LIKE %s OR description LIKE %s
        ORDER BY name
        LIMIT %s
        """
        search_param = f"%{q}%"
        cursor.execute(query, (search_param, search_param, limit))
        rows = cursor.fetchall()

        products = [
            ProductSummaryModel(
                product_id=row[0],
                category_id=row[1],
                name=row[2],
                description=row[3],
                price=row[4],
                stock=row[5],
                created_at=row[6]
            ) for row in rows
        ]

        return ApiResponse.success(
            data=products,
            message=f"Found {len(products)} products matching '{q}'"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
