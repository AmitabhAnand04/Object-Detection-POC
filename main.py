import io
import os
from fastapi import FastAPI, File, Response, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from typing import List
import uvicorn
from dotenv import load_dotenv, find_dotenv
from routes.auth import auth_router
from routes.manager import manager_router
from routes.user import user_router

load_dotenv(find_dotenv())

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv("Auth_USERNAME", "default_user"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("Auth_PASSWORD", "default_password"))
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})


app = FastAPI(
    title="Image Object & Brand Identifier API",
    description="Accepts an image and returns objects and their brands using Gemini model.",
    version="1.0.0"
)



allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
# Allow cross-origin requests if needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return Response(status_code=204)  # No Content
app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(manager_router, prefix="/manager", tags=["manager"])
app.include_router(user_router, prefix="/user", tags=["user"])

# Optional: run locally
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
