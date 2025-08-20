from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasicCredentials
import psycopg2.extras
from pydantic import BaseModel

from database import connect_to_db
from service.auth_service import verify_credentials



user_router = APIRouter()

@user_router.get("/get_visits", summary="Get visits for the user")
def get_user_visits(user_id: int, _: HTTPBasicCredentials = Depends(verify_credentials)):
    conn = None
    try:
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    sa.assignment_id,
                    s.store_name,
                    sa.assigned_visit_date,
                    m.username AS assigned_by,
                    sa.status
                FROM public.storeassignments sa
                JOIN public.stores s ON sa.store_id = s.store_id
                JOIN public.users m ON sa.assigned_by = m.user_id   -- manager name
                WHERE sa.user_id = %s
                """,
                (user_id,)
            )
            rows = cursor.fetchall()

            return {"user_visits": rows}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()
