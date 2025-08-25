import os
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from typing import List
from azure.storage.blob import BlobServiceClient
import uuid
from fastapi.security import HTTPBasicCredentials
import psycopg2.extras
from pydantic import BaseModel
from datetime import datetime
from database import connect_to_db
from service.auth_service import verify_credentials


BLOB_CONTAINER_NAME = os.getenv("BLOB_CONTAINER_NAME")
BLOB_CONNECTION_STRING = os.getenv("BLOB_CONNECTION_STRING")
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
                    sa.actual_visit_date,
                    m.username AS assigned_by,
                    sa.status,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'image_id', sai.image_id,
                                'image_url', sai.image_url,
                                'status', sai.status
                            )
                        ) FILTER (WHERE sai.image_id IS NOT NULL), '[]'
                    ) AS images
                FROM public.storeassignments sa
                JOIN public.stores s 
                    ON sa.store_id = s.store_id
                JOIN public.users m 
                    ON sa.assigned_by = m.user_id
                LEFT JOIN public.storeassignmentimages sai
                    ON sa.assignment_id = sai.assignment_id
                WHERE sa.user_id = %s
                GROUP BY sa.assignment_id, s.store_name, sa.assigned_visit_date, m.username, sa.status;
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

@user_router.post("/visit-upload", summary="Upload visit images")
def upload_visit_images(
    assignment_id: int = Form(...),
    files: List[UploadFile] = File(...),
    _: HTTPBasicCredentials = Depends(verify_credentials)
):
    conn = None
    try:
        # init blob client
        blob_service_client = BlobServiceClient.from_connection_string(BLOB_CONNECTION_STRING)
        container_client = blob_service_client.get_container_client(BLOB_CONTAINER_NAME)

        uploaded_urls = []

        # upload each file
        for file in files:
            blob_name = f"{assignment_id}/{uuid.uuid4()}_{file.filename}"
            blob_client = container_client.get_blob_client(blob_name)

            # upload file
            blob_client.upload_blob(file.file, overwrite=True)

            # get blob url
            url = blob_client.url
            uploaded_urls.append(url)

        # DB connection
        cur, conn = connect_to_db()
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            
            # update storeassignments table
            cursor.execute(
                """
                UPDATE public.storeassignments
                SET status = 'visited',
                    actual_visit_date = %s
                WHERE assignment_id = %s
                """,
                (datetime.utcnow(), assignment_id)
            )

            # insert each image into storeassignmentimages
            for url in uploaded_urls:
                cursor.execute(
                    """
                    INSERT INTO public.storeassignmentimages 
                        (assignment_id, image_url, status) 
                    VALUES (%s, %s, 'uploaded')
                    """,
                    (assignment_id, url)
                )

            conn.commit()

        return {
            "assignment_id": assignment_id,
            "uploaded_images": uploaded_urls,
            "message": f"{len(uploaded_urls)} images uploaded and saved successfully."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if conn:
            conn.close()