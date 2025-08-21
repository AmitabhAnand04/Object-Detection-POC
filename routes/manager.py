# apis for get_users, get_stores, assigned_visit

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasicCredentials
import psycopg2.extras
from pydantic import BaseModel

from database import connect_to_db
from service.auth_service import verify_credentials



manager_router = APIRouter()

@manager_router.get("/get_users", summary="Get all users")
async def get_users(_: HTTPBasicCredentials = Depends(verify_credentials)):
    try:
        cursor, connection = connect_to_db()
        if cursor is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor.execute("SELECT user_id, username, email FROM users WHERE user_type = 'employee';")
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

@manager_router.get("/get_stores", summary="Get all stores")
async def get_stores(_: HTTPBasicCredentials = Depends(verify_credentials)):
    try:
        cursor, conn = connect_to_db()
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
    
@manager_router.post("/assign_visit", summary="Assign visits")
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

@manager_router.get("/get_visits", summary="Get all assigned visits")
def get_visits(manager_id: int, _: HTTPBasicCredentials = Depends(verify_credentials)):
    conn = None
    try:
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    sa.assignment_id,
                    sa.user_id,
                    u.username,
                    s.store_name,
                    sa.assigned_visit_date
                FROM public.storeassignments sa
                JOIN public.users u ON sa.user_id = u.user_id
                JOIN public.stores s ON sa.store_id = s.store_id
                WHERE sa.status = 'assigned'
                  AND sa.assigned_by = %s
                """,
                (manager_id,)
            )
            rows = cursor.fetchall()

            return {"visits": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()

@manager_router.get("/get_completed_visits", summary="Get all completed visits")
def get_visit_images(manager_id: int, _: HTTPBasicCredentials = Depends(verify_credentials)):
    conn = None
    try:
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    sai.image_id,
                    sa.assignment_id,
                    s.store_name,
                    u.username AS employee_name,
                    sa.assigned_visit_date,
                    sa.actual_visit_date,
                    sai.status   -- <-- status from storeassignmentimages
                FROM public.storeassignmentimages sai
                JOIN public.storeassignments sa ON sai.assignment_id = sa.assignment_id
                JOIN public.users u ON sa.user_id = u.user_id
                JOIN public.stores s ON sa.store_id = s.store_id
                WHERE sa.assigned_by = %s
                """,
                (manager_id,)
            )
            rows = cursor.fetchall()

            return {"visits": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()
