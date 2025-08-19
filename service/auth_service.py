import os
from fastapi import Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, os.getenv("Auth_USERNAME", "default_user"))
    correct_password = secrets.compare_digest(credentials.password, os.getenv("Auth_PASSWORD", "default_password"))
    if not (correct_username and correct_password):
        raise HTTPException(status_code=401, detail="Invalid credentials", headers={"WWW-Authenticate": "Basic"})
