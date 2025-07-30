import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from PIL import Image
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
