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

def identify_objects_direct_from_file(file: BinaryIO):
    """
    Identifies objects and brands from a binary image file using Gemini API.

    Args:
        file (BinaryIO): Uploaded image file.

    Returns:
        dict: Parsed JSON response from Gemini model.
    """
    prompt_text = """
Carefully analyze the image and identify all discernible objects inside Refrigerator. For each object, determine its label (name) and the associated brand if it is clearly visible. Return the output strictly in the following JSON format:

[
  {
    "object": "<name of the object>",
    "label": "<brand name or null>"
  },
  ...
]

Ensure the JSON is well-structured and contains all relevant objects visible in the image. Use null if the brand is not identifiable.
"""

    try:
        print("Started identifying objects and brands in the image.")
        image = Image.open(file)
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content([prompt_text, image])
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
