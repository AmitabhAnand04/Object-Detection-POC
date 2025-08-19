# apis for login & logout

from fastapi import APIRouter, Depends, status, HTTPException



auth_router = APIRouter()

# @auth_router.post("/login")
# async def login(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
#     pass