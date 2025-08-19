# apis for get_users, get_stores, assigned_visit

from fastapi import APIRouter, Depends, status, HTTPException

from database import connect_to_db



user_router = APIRouter()

@user_router.get("/users", summary="Get all users")
async def get_users():
    try:
        cursor = connect_to_db()
        if cursor is None:
            raise HTTPException(status_code=500, detail="Database connection failed")
        
        cursor.execute("SELECT * FROM users;")
        users = cursor.fetchall()
        return {"status": "success", "data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {e}")
    finally:
        if cursor:
            cursor.close()