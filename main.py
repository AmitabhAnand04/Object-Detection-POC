import io
import os
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from identify import identify_objects_direct_from_file, is_original_camera_image
from typing import List
import uvicorn
from dotenv import load_dotenv, find_dotenv

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

@app.post("/analyze-image", summary="Analyze Image for Objects and Brands")
async def analyze_image(
    file: UploadFile = File(...),
    _: HTTPBasicCredentials = Depends(verify_credentials)
    ):
    if file.content_type.split("/")[0] != "image":
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")
    if not is_original_camera_image(file.file):
        raise HTTPException(
            status_code=400,
            detail="Image Rejected! Image must be original from phone camera and unedited."
        )
    
    # 🔁 Rewind the file pointer before reading again
    file.file.seek(0)

    try:
        print("Got the image to indetify objects and brands.")
        result = identify_objects_direct_from_file(file.file)
        return {"status": "success", "data": result}
    except ValueError as ve:
        raise HTTPException(status_code=500, detail=f"Model response error: {ve}")
    except RuntimeError as re:
        raise HTTPException(status_code=500, detail=f"Internal error: {re}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# @app.post("/analyze-image", summary="Analyze Image for Objects and Brands")
# async def analyze_image(
#     file: UploadFile = File(...),
#     _: HTTPBasicCredentials = Depends(verify_credentials)
# ):
#     if file.content_type.split("/")[0] != "image":
#         raise HTTPException(status_code=400, detail="Invalid file type. Please upload an image.")

#     image_bytes = await file.read()

#     if not is_original_camera_image(image_bytes):
#         raise HTTPException(
#             status_code=400,
#             detail="Image Rejected! Image must be original from phone camera and unedited."
#         )

#     file_like = io.BytesIO(image_bytes)

#     try:
#         print("Got the image to identify objects and brands.")
#         result = identify_objects_direct_from_file(file_like)
#         return {"status": "success", "data": result}

#     except ValueError as ve:
#         raise HTTPException(status_code=500, detail=f"Model response error: {ve}")
#     except RuntimeError as re:
#         raise HTTPException(status_code=500, detail=f"Internal error: {re}")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

# Optional: run locally
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8080, reload=True)
