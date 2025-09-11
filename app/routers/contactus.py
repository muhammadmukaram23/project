from fastapi import APIRouter, HTTPException, Query, status,Depends
from app.db import get_connection
from app.models.contactus import (

ContactCreate,
ContactResponse


)
from app.models.common import (ApiResponse)
from app.auth.auth import verify_token

from typing import List, Optional
import mysql.connector

router = APIRouter(prefix="/contact_us", tags=["contact_us"],dependencies=[Depends(verify_token)])


@router.post("/", response_model=ApiResponse[ContactResponse], status_code=status.HTTP_201_CREATED)
def create_contact(contact: ContactCreate):
    """Create a new contact message"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Insert new contact
        cursor.execute(
            """
            INSERT INTO Contact (customer_id, name, email, phone, message)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (contact.customer_id, contact.name, contact.email, contact.phone, contact.message)
        )
        conn.commit()
        contact_id = cursor.lastrowid

        # Fetch the created contact
        cursor.execute(
            """
            SELECT contact_id, customer_id, name, email, phone, message, created_at
            FROM Contact WHERE contact_id = %s
            """,
            (contact_id,)
        )
        row = cursor.fetchone()

        created_contact = ContactResponse(
            contact_id=row[0],
            customer_id=row[1],
            name=row[2],
            email=row[3],
            phone=row[4],
            message=row[5],
            created_at=row[6]
        )

        return ApiResponse.success(
            data=created_contact,
            message="Message sent successfully to support"
        )

    except mysql.connector.Error as err:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        cursor.close()
        conn.close()



@router.get("/", response_model=ApiResponse[list[ContactResponse]])
def get_all_contacts():
    """Fetch all customer contact messages"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT contact_id, customer_id, name, email, phone, message, created_at
            FROM Contact ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()

        contacts = [
            ContactResponse(
                contact_id=row[0],
                customer_id=row[1],
                name=row[2],
                email=row[3],
                phone=row[4],
                message=row[5],
                created_at=row[6],
            )
            for row in rows
        ]

        return ApiResponse.success(
            data=contacts,
            message="Customer messages fetched successfully"
        )

    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Database error: {err}")

    finally:
        cursor.close()
        conn.close()
      
