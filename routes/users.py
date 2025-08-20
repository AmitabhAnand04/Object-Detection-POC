# apis for get_users, get_stores, assigned_visit

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasicCredentials
import psycopg2.extras
from pydantic import BaseModel

from database import connect_to_db
from service.auth_service import verify_credentials



user_router = APIRouter()

@user_router.get("/get_users", summary="Get all users")
async def get_users(_: HTTPBasicCredentials = Depends(verify_credentials)):
    try:
        cursor, connection = connect_to_db()
        if cursor is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor.execute("SELECT username, email FROM users;")
        users = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        users_dict = [dict(zip(column_names, row)) for row in users]
        print(f"Fetched users: {users_dict}")
        # print(f"Fetched users: {users}")
        return {"status": "success", "data": users_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {e}")
    finally:
        if cursor:
            cursor.close()

@user_router.get("/get_stores", summary="Get all stores")
async def get_stores(_: HTTPBasicCredentials = Depends(verify_credentials)):
    try:
        cursor, connection = connect_to_db()
        if cursor is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor.execute("SELECT store_id, store_name FROM stores;")
        stores = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]
        stores_dict = [dict(zip(column_names, row)) for row in stores]
        print(f"Fetched stores: {stores_dict}")
        return {"status": "success", "data": stores_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stores: {e}")
    finally:
        if cursor:
            cursor.close()

# Request body schema
class AssignVisitRequest(BaseModel):
    manager_id: int
    user_id: int
    store_id: int
    visit_date: str  # ISO format (YYYY-MM-DD)
    
@user_router.post("/assign_visit", summary="Assign visits")
def assign_visit(request: AssignVisitRequest, _: HTTPBasicCredentials = Depends(verify_credentials)):
    conn = None
    try:
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                "SELECT assign_visit(%s, %s, %s, %s)",
                (request.manager_id, request.user_id, request.store_id, request.visit_date),
            )
            row = cursor.fetchone()
            conn.commit()

            return {"assignment_id": row["assign_visit"] if row else None}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()