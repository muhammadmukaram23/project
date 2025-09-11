from fastapi import APIRouter, HTTPException, Query, status,Depends
from app.db import get_connection
from app.models.review import (

ReviewCreate,
ReviewResponse


)
from app.auth.auth import verify_token
from app.models.common import (ApiResponse)

from typing import List, Optional
import mysql.connector

router = APIRouter(prefix="/review", tags=["reviews"],dependencies=[Depends(verify_token)])

@router.post("/", response_model=ApiResponse[ReviewResponse], status_code=status.HTTP_201_CREATED)
def create_review(review: ReviewCreate):
    """Create a new review"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # ✅ Ensure customer purchased the product
        cursor.execute("""
            SELECT oi.order_id
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.order_id
            WHERE oi.product_id = %s AND o.customer_id = %s
            LIMIT 1
        """, (review.product_id, review.customer_id))
        order_row = cursor.fetchone()

        if not order_row:
            raise HTTPException(status_code=400, detail="Customer has not purchased this product")

        order_id = order_row[0]

        # ✅ Ensure customer has not already reviewed this product
        cursor.execute("""
            SELECT review_id FROM REVIEWS
            WHERE product_id = %s AND customer_id = %s
        """, (review.product_id, review.customer_id))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="Customer already reviewed this product")

        # ✅ Insert review
        cursor.execute("""
            INSERT INTO REVIEWS (product_id, customer_id, rating, comment)
            VALUES (%s, %s, %s, %s)
        """, (review.product_id, review.customer_id, review.rating, review.comment))
        conn.commit()
        review_id = cursor.lastrowid

        # ✅ Fetch created review with safe joins
        cursor.execute("""
            SELECT r.review_id, r.product_id, r.customer_id, r.rating, r.comment, r.created_at,
                   c.name, c.email, %s AS order_id, p.name,
                   (
                       SELECT pi.image_url 
                       FROM product_images pi 
                       WHERE pi.product_id = p.product_id
                       ORDER BY pi.is_primary DESC, pi.image_id ASC
                       LIMIT 1
                   ) AS first_image_url
            FROM REVIEWS r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN products p ON r.product_id = p.product_id
            WHERE r.review_id = %s
        """, (order_id, review_id))
        row = cursor.fetchone()

        created_review = ReviewResponse(
            review_id=row[0],
            product_id=row[1],
            customer_id=row[2],
            rating=row[3],
            comment=row[4],
            created_at=row[5],
            customer_name=row[6],
            customer_email=row[7],
            order_id=row[8],       # now always safe
            product_name=row[9],
            first_image_url=row[10]
        )

        return ApiResponse.success(
            data=created_review,
            message="Review created successfully"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")
    finally:
        cursor.close()
        conn.close()



@router.get("/{review_id}", response_model=ApiResponse[ReviewResponse])
def get_review(review_id: int):
    """Get a single review with customer + product info"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)  # ✅ dictionary + buffered

    try:
        cursor.execute("""
            SELECT r.review_id, r.product_id, r.customer_id, r.rating, r.comment, r.created_at,
                   c.name AS customer_name, c.email AS customer_email,
                   oi.order_id, p.name AS product_name,
                   (SELECT pi.image_url 
                    FROM product_images pi 
                    WHERE pi.product_id = p.product_id
                    ORDER BY pi.is_primary DESC, pi.image_id ASC LIMIT 1) AS first_image_url
            FROM REVIEWS r
            JOIN customers c ON r.customer_id = c.customer_id
            LEFT JOIN order_items oi ON r.product_id = oi.product_id
            JOIN products p ON r.product_id = p.product_id
            WHERE r.review_id = %s
        """, (review_id,))
        row = cursor.fetchone()

        if not row:
            raise HTTPException(status_code=404, detail="Review not found")

        review = ReviewResponse(
            review_id=row["review_id"],
            product_id=row["product_id"],
            customer_id=row["customer_id"],
            rating=row["rating"],
            comment=row["comment"],
            created_at=row["created_at"].isoformat() if row["created_at"] else None,  # ✅ convert datetime
            customer_name=row["customer_name"],
            customer_email=row["customer_email"],
            order_id=row["order_id"],
            product_name=row["product_name"],
            first_image_url=row["first_image_url"]
        )

        return ApiResponse.success(data=review, message="Review fetched successfully")

    finally:
        cursor.close()
        conn.close()


@router.get("/", response_model=ApiResponse[List[ReviewResponse]])
def get_all_reviews():
    """Get all reviews with customer + product info"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT r.review_id, r.product_id, r.customer_id, r.rating, r.comment, r.created_at,
                   c.name, c.email,
                   (
                       SELECT oi.order_id
                       FROM order_items oi
                       JOIN orders o ON oi.order_id = o.order_id
                       WHERE oi.product_id = r.product_id
                         AND o.customer_id = r.customer_id
                       LIMIT 1
                   ) AS order_id,
                   p.name,
                   (
                       SELECT pi.image_url 
                       FROM product_images pi 
                       WHERE pi.product_id = p.product_id
                       ORDER BY pi.is_primary DESC, pi.image_id ASC
                       LIMIT 1
                   ) AS first_image_url
            FROM REVIEWS r
            JOIN customers c ON r.customer_id = c.customer_id
            JOIN products p ON r.product_id = p.product_id
            ORDER BY r.created_at DESC
        """)
        rows = cursor.fetchall()

        reviews = [
            ReviewResponse(
                review_id=row[0],
                product_id=row[1],
                customer_id=row[2],
                rating=row[3],
                comment=row[4],
                created_at=row[5],
                customer_name=row[6],
                customer_email=row[7],
                order_id=row[8],      # safely matched with review.customer_id
                product_name=row[9],
                first_image_url=row[10]
            )
            for row in rows
        ]

        return ApiResponse.success(data=reviews, message="All reviews fetched successfully")

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        cursor.close()
        conn.close()



@router.delete("/{review_id}", response_model=ApiResponse[dict], status_code=status.HTTP_200_OK)
def delete_review(review_id: int):
    """Delete a review by its ID"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if review exists
        cursor.execute("SELECT review_id FROM REVIEWS WHERE review_id = %s", (review_id,))
        review = cursor.fetchone()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")

        # Delete review
        cursor.execute("DELETE FROM REVIEWS WHERE review_id = %s", (review_id,))
        conn.commit()

        return ApiResponse.success(
            data={"review_id": review_id},
            message="Review deleted successfully"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        cursor.close()
        conn.close()
