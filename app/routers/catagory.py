from fastapi import APIRouter, HTTPException, Query
from app.db import get_connection
from app.models import (
    CategoryCreateModel,
    CategoryUpdateModel,
    CategoryResponseModel,
    CategoryWithChildrenModel,
    ApiResponse,
    PaginatedResponse,
    SuccessResponse,
    MessageResponse
)
from typing import List, Optional
import mysql.connector

router = APIRouter(prefix="/categories", tags=["categories"])


# ------------------- GET ALL CATEGORIES -------------------
@router.get("/", response_model=ApiResponse[PaginatedResponse[CategoryResponseModel]])
def get_all_categories(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = Query(None),
    parent_id: Optional[int] = Query(None, description="Filter by parent category ID")
):
    """Get all categories with pagination and optional filtering"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build base queries
        base_query = "SELECT category_id, name, description, parent_id FROM categories"
        count_query = "SELECT COUNT(*) FROM categories"

        # Build WHERE conditions
        conditions = []
        params = []

        if search:
            conditions.append("(name LIKE %s OR description LIKE %s)")
            search_param = f"%{search}%"
            params.extend([search_param, search_param])

        if parent_id is not None:
            conditions.append("parent_id = %s")
            params.append(parent_id)

        # Add WHERE clause if we have conditions
        where_clause = ""
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)

        # Get total count
        cursor.execute(count_query + where_clause, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        query = base_query + where_clause + " ORDER BY name ASC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()

        categories = [
            CategoryResponseModel(
                category_id=row[0],
                name=row[1],
                description=row[2],
                parent_id=row[3]
            ) for row in rows
        ]

        paginated_response = PaginatedResponse.create(
            data=categories,
            total=total,
            page=page,
            limit=limit
        )

        return ApiResponse.success(
            data=paginated_response,
            message=f"Retrieved {len(categories)} categories"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET CATEGORY BY ID -------------------
@router.get("/{category_id}", response_model=ApiResponse[CategoryResponseModel])
def get_category_by_id(category_id: int):
    """Get a specific category by ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")

        category = CategoryResponseModel(
            category_id=row[0],
            name=row[1],
            description=row[2],
            parent_id=row[3]
        )

        return ApiResponse.success(
            data=category,
            message="Category retrieved successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET CATEGORY WITH CHILDREN -------------------
@router.get("/{category_id}/with-children", response_model=ApiResponse[CategoryWithChildrenModel])
def get_category_with_children(category_id: int):
    """Get a category with all its child categories"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get parent category
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        parent_row = cursor.fetchone()
        if not parent_row:
            raise HTTPException(status_code=404, detail="Category not found")

        # Get child categories
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE parent_id = %s ORDER BY name",
            (category_id,)
        )
        child_rows = cursor.fetchall()

        children = [
            CategoryResponseModel(
                category_id=row[0],
                name=row[1],
                description=row[2],
                parent_id=row[3]
            ) for row in child_rows
        ]

        category_with_children = CategoryWithChildrenModel(
            category_id=parent_row[0],
            name=parent_row[1],
            description=parent_row[2],
            parent_id=parent_row[3],
            children=children
        )

        return ApiResponse.success(
            data=category_with_children,
            message=f"Category retrieved with {len(children)} children"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- CREATE CATEGORY -------------------
@router.post("/", response_model=ApiResponse[CategoryResponseModel], status_code=201)
def create_category(category: CategoryCreateModel):
    """Create a new category"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if parent category exists (if parent_id is provided)
        if category.parent_id is not None:
            cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (category.parent_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Parent category not found")

        # Check if category name already exists at the same level
        if category.parent_id is not None:
            cursor.execute(
                "SELECT category_id FROM categories WHERE name = %s AND parent_id = %s",
                (category.name, category.parent_id)
            )
        else:
            cursor.execute(
                "SELECT category_id FROM categories WHERE name = %s AND parent_id IS NULL",
                (category.name,)
            )

        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Category name already exists at this level")

        # Insert new category
        cursor.execute(
            "INSERT INTO categories (name, description, parent_id) VALUES (%s, %s, %s)",
            (category.name, category.description, category.parent_id)
        )
        conn.commit()
        category_id = cursor.lastrowid

        # Fetch the created category
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        row = cursor.fetchone()

        created_category = CategoryResponseModel(
            category_id=row[0],
            name=row[1],
            description=row[2],
            parent_id=row[3]
        )

        return ApiResponse.success(
            data=created_category,
            message="Category created successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "parent_id" in str(err):
            raise HTTPException(status_code=400, detail="Invalid parent category")
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- UPDATE CATEGORY -------------------
@router.put("/{category_id}", response_model=ApiResponse[CategoryResponseModel])
def update_category(category_id: int, category: CategoryUpdateModel):
    """Update an existing category"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if category exists
        cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (category_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Category not found")

        # Check if trying to set self as parent
        if category.parent_id == category_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")

        # Build dynamic update query
        update_fields = []
        params = []

        if category.name is not None:
            # Check for duplicate names at the same level
            if category.parent_id is not None:
                cursor.execute(
                    "SELECT category_id FROM categories WHERE name = %s AND parent_id = %s AND category_id != %s",
                    (category.name, category.parent_id, category_id)
                )
            else:
                cursor.execute(
                    "SELECT category_id FROM categories WHERE name = %s AND parent_id IS NULL AND category_id != %s",
                    (category.name, category_id)
                )

            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Category name already exists at this level")

            update_fields.append("name = %s")
            params.append(category.name)

        if category.description is not None:
            update_fields.append("description = %s")
            params.append(category.description)

        if category.parent_id is not None:
            # Check if parent category exists
            cursor.execute("SELECT category_id FROM categories WHERE category_id = %s", (category.parent_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="Parent category not found")

            # Check for circular reference
            if category.parent_id == category_id:
                raise HTTPException(status_code=400, detail="Category cannot be its own parent")

            update_fields.append("parent_id = %s")
            params.append(category.parent_id)

        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Execute update
        query = f"UPDATE categories SET {', '.join(update_fields)} WHERE category_id = %s"
        params.append(category_id)
        cursor.execute(query, params)
        conn.commit()

        # Fetch updated category
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE category_id = %s",
            (category_id,)
        )
        row = cursor.fetchone()

        updated_category = CategoryResponseModel(
            category_id=row[0],
            name=row[1],
            description=row[2],
            parent_id=row[3]
        )

        return ApiResponse.success(
            data=updated_category,
            message="Category updated successfully"
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        raise HTTPException(status_code=400, detail="Data integrity error")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- DELETE CATEGORY -------------------
@router.delete("/{category_id}", response_model=SuccessResponse)
def delete_category(
    category_id: int,
    force: bool = Query(False, description="Force delete even if category has children or products")
):
    """Delete a category"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Check if category exists
        cursor.execute("SELECT category_id, name FROM categories WHERE category_id = %s", (category_id,))
        category_row = cursor.fetchone()
        if not category_row:
            raise HTTPException(status_code=404, detail="Category not found")

        category_name = category_row[1]

        if not force:
            # Check if category has children
            cursor.execute("SELECT COUNT(*) FROM categories WHERE parent_id = %s", (category_id,))
            child_count = cursor.fetchone()[0]
            if child_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete category '{category_name}' with {child_count} child categories. Use force=true to delete anyway."
                )

            # Check if category has products
            cursor.execute("SELECT COUNT(*) FROM products WHERE category_id = %s", (category_id,))
            product_count = cursor.fetchone()[0]
            if product_count > 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot delete category '{category_name}' with {product_count} products. Use force=true to delete anyway."
                )

        # If force=true, handle cascading deletes
        if force:
            # Set child categories' parent_id to NULL
            cursor.execute("UPDATE categories SET parent_id = NULL WHERE parent_id = %s", (category_id,))

            # You might want to handle products differently - move to a default category or delete them
            # For now, we'll just delete the category and let the foreign key constraint handle products

        # Delete the category
        cursor.execute("DELETE FROM categories WHERE category_id = %s", (category_id,))
        conn.commit()

        return SuccessResponse(
            message=f"Category '{category_name}' deleted successfully",
            data={"deleted_category_id": category_id}
        )

    except mysql.connector.IntegrityError as err:
        conn.rollback()
        if "products" in str(err).lower():
            raise HTTPException(status_code=400, detail="Cannot delete category that has products")
        if "categories" in str(err).lower():
            raise HTTPException(status_code=400, detail="Cannot delete category that has child categories")
        raise HTTPException(status_code=400, detail="Cannot delete category due to foreign key constraints")
    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET ROOT CATEGORIES -------------------
@router.get("/root/", response_model=ApiResponse[List[CategoryResponseModel]])
def get_root_categories():
    """Get all root categories (categories without parent)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE parent_id IS NULL ORDER BY name"
        )
        rows = cursor.fetchall()

        categories = [
            CategoryResponseModel(
                category_id=row[0],
                name=row[1],
                description=row[2],
                parent_id=row[3]
            ) for row in rows
        ]

        return ApiResponse.success(
            data=categories,
            message=f"Retrieved {len(categories)} root categories"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- GET CATEGORY HIERARCHY -------------------
@router.get("/hierarchy/", response_model=ApiResponse[List[CategoryWithChildrenModel]])
def get_category_hierarchy():
    """Get complete category hierarchy (all root categories with their children)"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Get all root categories
        cursor.execute(
            "SELECT category_id, name, description, parent_id FROM categories WHERE parent_id IS NULL ORDER BY name"
        )
        root_rows = cursor.fetchall()

        hierarchy = []
        for root_row in root_rows:
            # Get children for each root category
            cursor.execute(
                "SELECT category_id, name, description, parent_id FROM categories WHERE parent_id = %s ORDER BY name",
                (root_row[0],)
            )
            child_rows = cursor.fetchall()

            children = [
                CategoryResponseModel(
                    category_id=row[0],
                    name=row[1],
                    description=row[2],
                    parent_id=row[3]
                ) for row in child_rows
            ]

            category_with_children = CategoryWithChildrenModel(
                category_id=root_row[0],
                name=root_row[1],
                description=root_row[2],
                parent_id=root_row[3],
                children=children
            )
            hierarchy.append(category_with_children)

        return ApiResponse.success(
            data=hierarchy,
            message=f"Retrieved category hierarchy with {len(hierarchy)} root categories"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()


# ------------------- SEARCH CATEGORIES -------------------
@router.get("/search/", response_model=ApiResponse[List[CategoryResponseModel]])
def search_categories(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50)
):
    """Search categories by name or description"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        query = """
        SELECT category_id, name, description, parent_id
        FROM categories
        WHERE name LIKE %s OR description LIKE %s
        ORDER BY name
        LIMIT %s
        """
        search_param = f"%{q}%"
        cursor.execute(query, (search_param, search_param, limit))
        rows = cursor.fetchall()

        categories = [
            CategoryResponseModel(
                category_id=row[0],
                name=row[1],
                description=row[2],
                parent_id=row[3]
            ) for row in rows
        ]

        return ApiResponse.success(
            data=categories,
            message=f"Found {len(categories)} categories matching '{q}'"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()
