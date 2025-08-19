# apis for login & logout

from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.security import HTTPBasicCredentials
import psycopg2.extras
from pydantic import BaseModel
from database import connect_to_db
from service.auth_service import verify_credentials


auth_router = APIRouter()

# @auth_router.post("/login")
# async def login(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
#     pass

# -------------------------------
# Request Schema
# -------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str

# -------------------------------
# Login Endpoint
# -------------------------------
@auth_router.post("/login")
def login(request: LoginRequest, _: HTTPBasicCredentials = Depends(verify_credentials)):
    conn = None
    try:
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM login_user(%s, %s);", (request.username, request.password))
            row = cursor.fetchone()

            # The function always returns exactly one row.
            if not row:
                # Defensive: should not happen, but handle just in case.
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Login function returned no row"
                )

            if row["success"]:
                return {
                    "success": True,
                    "user_id": row["user_id"],
                    "user_type": row["user_type"],
                    "full_name": row["full_name"],
                }
            else:
                # Wrong username/password
                return {
                    "success": False,
                    "user_id": None,
                    "user_type": None,
                    "full_name": None
                }

    except Exception as e:
        # log properly in production
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {e}"
        )
    finally:
        if conn:
            conn.close()