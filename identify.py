import io
import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from PIL import Image, ExifTags
from typing import BinaryIO
import json

load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY is not set in the environment.")

genai.configure(api_key=GOOGLE_API_KEY)
SYSTEM_INSTRUCTION_PROMPT = os.getenv("SYSTEM_INSTRUCTION_PROMPT")
if not SYSTEM_INSTRUCTION_PROMPT:
    raise EnvironmentError("SYSTEM_INSTRUCTION_PROMPT is not set in the environment.")
MODEL = genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_INSTRUCTION_PROMPT)

def identify_objects_direct_from_file(file: BinaryIO):
    """
    Identifies objects and brands from a binary image file using Gemini API.

    Args:
        file (BinaryIO): Uploaded image file.

    Returns:
        dict: Parsed JSON response from Gemini model.
    """
    try:
        print("Started identifying objects and brands in the image.")
        image = Image.open(file)
        response = MODEL.generate_content([image])
        print("Got Response!!")  # Debug output
        # Clean and convert the string response to JSON
        response_text = response.text.strip("```json").strip("```").strip()
        print(response_text)  # Debug output
        parsed = json.loads(response_text)
        return parsed

    except json.JSONDecodeError:
        raise ValueError("Failed to parse model output as JSON.")
    except Exception as e:
        raise RuntimeError(f"Gemini model failed: {e}")

# def is_original_camera_image(image_bytes: bytes) -> bool:
#     try:
#         img = Image.open(io.BytesIO(image_bytes))
#         exif_data = img._getexif()
#         if not exif_data:
#             print("failed at pos 1")
#             return False  # No EXIF, likely downloaded or edited

#         exif = {
#             ExifTags.TAGS.get(tag): value
#             for tag, value in exif_data.items()
#             if tag in ExifTags.TAGS
#         }

#         # Check for camera info
#         make = exif.get("Make", "").strip()
#         model = exif.get("Model", "").strip()
#         software = exif.get("Software", "").lower()

#         # Reject if software indicates editing
#         editing_signatures = ["photoshop", "snapseed", "lightroom", "pixlr", "canva"]
#         if any(editor in software for editor in editing_signatures):
#             print("failed at pos 2")
#             return False

#         # Accept only if camera make & model exist
#         if make and model:
#             print("Make "+make+" Model "+model)
#             return True
#         print("failed at pos 3")
#         return False
#     except Exception:
#         print("failed at pos 4")
#         return False
def is_original_camera_image(file: BinaryIO) -> bool:
    try:
        img = Image.open(file)
        exif_data = img._getexif()
        if not exif_data:
            print("failed at pos 1")
            return False  # No EXIF, likely downloaded or edited

        exif = {
            ExifTags.TAGS.get(tag): value
            for tag, value in exif_data.items()
            if tag in ExifTags.TAGS
        }

        # Check for camera info
        make = exif.get("Make", "").strip()
        model = exif.get("Model", "").strip()
        software = exif.get("Software", "").lower()

        # Reject if software indicates editing
        editing_signatures = ["photoshop", "snapseed", "lightroom", "pixlr", "canva"]
        if any(editor in software for editor in editing_signatures):
            print("failed at pos 2")
            return False

        # Accept only if camera make & model exist
        if make and model:
            print("Make "+make+" Model "+model)
            return True
        print("failed at pos 3")
        return False
    except Exception:
        print("failed at pos 4")
        return False