import json
import os
import psycopg2
from psycopg2.extras import RealDictCursor
import google.generativeai as genai
from database import connect_to_db
import requests
import re
from PIL import Image, ExifTags
from io import BytesIO
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise EnvironmentError("GOOGLE_API_KEY is not set in the environment.")

genai.configure(api_key=GOOGLE_API_KEY)
SYSTEM_INSTRUCTION_PROMPT = os.getenv("SYSTEM_INSTRUCTION_PROMPT")
if not SYSTEM_INSTRUCTION_PROMPT:
    raise EnvironmentError("SYSTEM_INSTRUCTION_PROMPT is not set in the environment.")
MODEL = genai.GenerativeModel('gemini-2.5-flash', system_instruction=SYSTEM_INSTRUCTION_PROMPT)

coca_cola_products = [
        "Coca-Cola Original",
        "Coca-Cola Zero Sugar",
        "Diet Coke",
        "Sprite",
        "Fanta",
        "Thums Up",
        "Maaza",
        "Minute Maid",
        "Dasani",
        "Toplo Chico",
        "Smartwater",
        "Vitaminwater",
        "Powerade",
        "BODYARMOR",
        "Aquarius",
        "Ayataka",
        "Georgia (coffee)",
        "Gold Peak",
        "Costa Coffee",
        "Del Valle",
        "Fairlife",
        "Simply",
        "Schweppes",
        "AdeS",
        "Honest Kids",
        "Core Power"
    ]
def normalize_brand(name):
    """Normalize brand name by removing non-alphanumeric characters and lowering case."""
    if not name:
        return None
    return re.sub(r'[^a-z0-9]', '', name.lower())

def evaluate_cooler_smart(llm_response):
    """
    Evaluate cooler status with fuzzy matching for Coca-Cola brands.

    Args:
        llm_response (dict): LLM output JSON with 'objects' list.

    Returns:
        dict: Evaluation results with purity, abused, empty, and non-Coca-Cola products.

    Raises:
        ValueError: If llm_response is not a dict or missing required keys.
        RuntimeError: For unexpected processing errors.
    """
    try:
        if not isinstance(llm_response, dict):
            raise ValueError("llm_response must be a dictionary. but it is: " + str(llm_response))

        # Normalize Coca-Cola brand names
        coca_cola_normalized = [normalize_brand(p) for p in coca_cola_products]

        objects = llm_response.get("objects", [])
        if not isinstance(objects, list):
            raise ValueError("'objects' field in llm_response must be a list.")

        # Empty cooler check
        if not objects:
            return {
                "chargeability_percentage": llm_response.get("chargeability_percentage"),
                "auditable": llm_response.get("auditable"),
                "purity": "Impure",
                "abused": "Yes",
                "empty": "Yes",
                "non_coca_cola_products": []
            }

        coca_cola_count = 0
        non_coca_cola = []

        for obj in objects:
            if not isinstance(obj, dict):
                raise ValueError("Each item in 'objects' must be a dictionary.")

            label = obj.get("label")
            norm_label = normalize_brand(label)

            if norm_label:
                if any(norm_brand in norm_label or norm_label in norm_brand for norm_brand in coca_cola_normalized):
                    coca_cola_count += 1
                else:
                    non_coca_cola.append(label)
            else:
                non_coca_cola.append(None)

        purity = "Pure" if coca_cola_count == len(objects) else "Impure"
        abused = "Yes" if coca_cola_count == 0 else "No"

        return {
            "chargeability_percentage": llm_response.get("chargeability_percentage"),
            "auditable": llm_response.get("auditable"),
            "purity": purity,
            "abused": abused,
            "empty": "No",
            "non_coca_cola_products": non_coca_cola
        }

    except (ValueError, KeyError) as e:
        raise ValueError(f"Invalid input in evaluate_cooler_smart: {e}")

    except Exception as e:
        raise RuntimeError(f"Unexpected error in evaluate_cooler_smart: {e}")


# def evaluate_cooler_smart(llm_response):
#     """
#     Evaluate cooler status with fuzzy matching for Coca-Cola brands.
    
#     Args:
#         llm_response (dict): LLM output JSON with 'objects' list.
#         coca_cola_products (list): List of Coca-Cola product names.
    
#     Returns:
#         dict: Evaluation results with purity, abused, empty, and non-Coca-Cola products.
#     """
#     # Normalize Coca-Cola brand names
#     coca_cola_normalized = [normalize_brand(p) for p in coca_cola_products]
    
#     objects = llm_response.get("objects", [])
    
#     # Empty cooler check
#     if not objects:
#         return {
#             "chargeability_percentage": llm_response.get("chargeability_percentage"),
#             "auditable": llm_response.get("auditable"),
#             "purity": "Impure",
#             "abused": "Yes",
#             "empty": "Yes",
#             "non_coca_cola_products": []
#         }

#     coca_cola_count = 0
#     non_coca_cola = []

#     for obj in objects:
#         label = obj.get("label")
#         norm_label = normalize_brand(label)
        
#         if norm_label:
#             # Check if normalized label contains or is contained in any Coca-Cola brand
#             if any(norm_brand in norm_label or norm_label in norm_brand for norm_brand in coca_cola_normalized):
#                 coca_cola_count += 1
#             else:
#                 non_coca_cola.append(label)
#         else:
#             non_coca_cola.append(None)  # null labels count as non-Coca-Cola

#     # Determine purity
#     purity = "Pure" if coca_cola_count == len(objects) else "Impure"

#     # Determine abused
#     abused = "Yes" if coca_cola_count == 0 else "No"

#     return {
#         "chargeability_percentage": llm_response.get("chargeability_percentage"),
#         "auditable": llm_response.get("auditable"),
#         "purity": purity,
#         "abused": abused,
#         "empty": "No",
#         "non_coca_cola_products": non_coca_cola
#     }

def get_images(assignment_id: int):
    """
    Fetch all image IDs and URLs for a given assignment ID.
    """
    connection = None
    try:
        curr, connection = connect_to_db()
        cursor = connection.cursor(cursor_factory=RealDictCursor)
        
        query = """
            SELECT image_id, image_url
            FROM storeassignmentimages
            WHERE assignment_id = %s
        """
        cursor.execute(query, (assignment_id,))
        results = cursor.fetchall()
        
        return results  # list of dicts: [{'image_id': 1, 'image_url': '...'}, ...]
    
    except Exception as e:
        print(f"Error while fetching images: {e}")
        return []
    
    finally:
        if connection:
            connection.close()

def fetch_image_from_url(image_url: str) -> Image.Image:
    """
    Fetch an image from the given URL and return a PIL Image object.

    Args:
        image_url (str): URL of the image to fetch.

    Returns:
        PIL.Image.Image: The image object.
    """
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        return img
    except requests.exceptions.RequestException as e:
        print(f"Error fetching image from {image_url}: {e}")
        return None

def found_sga_photo(file: Image.Image) -> str:
    """
    Check if the image has original camera EXIF metadata.
    Returns "yes" or "no".
    """
    try:
        # Fetch the image from URL
        # response = requests.get(image_url, timeout=10)
        # response.raise_for_status()
        # img = Image.open(BytesIO(response.content))

        # Extract EXIF data
        exif_data = file._getexif()
        if not exif_data:
            print("failed at pos 1 - No EXIF")
            return "No"

        exif = {
            ExifTags.TAGS.get(tag): value
            for tag, value in exif_data.items()
            if tag in ExifTags.TAGS
        }

        # Camera details
        make = exif.get("Make", "").strip()
        model = exif.get("Model", "").strip()
        software = exif.get("Software", "").lower() if exif.get("Software") else ""

        # Reject if software indicates editing
        editing_signatures = ["photoshop", "snapseed", "lightroom", "pixlr", "canva"]
        if any(editor in software for editor in editing_signatures):
            print("failed at pos 2 - Editing software found")
            return "No"

        # Accept only if camera make & model exist
        if make and model:
            print(f"✅ Found EXIF: Make={make}, Model={model}")
            return "Yes"

        print("failed at pos 3 - Missing make/model")
        return "No"

    except Exception as e:
        print(f"failed at pos 4 - Exception: {e}")
        return "No"

def identify_objects_direct_from_file(file: Image.Image):
    """
    Identifies objects and brands from a binary image file using Gemini API.

    Args:
        file (BinaryIO): Uploaded image file.

    Returns:
        dict: Parsed JSON response from Gemini model.
    """
    try:
        print("Started identifying objects and brands in the image.")
        image = file
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
    
def run_analysis(assignment_id: int):
    """
    Run analysis for all images of a given assignment.
    For each image:
      - Fetch the image
      - Check if it's an original (found_sga_photo)
      - Identify objects using Gemini
      - Print results with assignment_id, image_id
    """
    print(f"🔍 Starting analysis for assignment_id={assignment_id}")

    # Step 1: Get all images for this assignment
    images = get_images(assignment_id)
    if not images:
        print(f"No images found for assignment_id={assignment_id}")
        return {}

    results = {}

    # Step 2: Loop over each image
    for img in images:
        image_id = img["image_id"]
        image_url = img["image_url"]
        print(f"\n📸 Processing image_id={image_id}, url={image_url}")

        # Step 3: Fetch image
        pil_img = fetch_image_from_url(image_url)
        if not pil_img:
            print(f"❌ Failed to fetch image_id={image_id}")
            results[image_id] = {
                "found_sga_photo": "error",
                "object_detection": "error"
            }
            continue

        # Step 4: Run found_sga_photo
        found_sga_result = found_sga_photo(pil_img)

        object_result_raw = identify_objects_direct_from_file(pil_img)

        # Step 6: Pass raw object detection result to cooler evaluator
        object_result = evaluate_cooler_smart(object_result_raw)

        # Step 7: Print and collect results
        print(f"✅ assignment_id={assignment_id}, image_id={image_id}")
        print(f"   - found_sga_photo: {found_sga_result}")
        print(f"   - final_cooler_result: {object_result}")

        results[image_id] = {
            "found_sga_photo": found_sga_result,
            "object_detection": object_result
        }

        # --- Extract values for DB update ---
        auditable = object_result.get("auditable")
        purity = object_result.get("purity")
        chargeability = object_result.get("chargeability_percentage")
        abused = object_result.get("abused")
        emptyy = object_result.get("empty")

        # --- Update storeassignmentimages ---
        try:
            curr, connection = connect_to_db()
            cursor = connection.cursor()

            update_img_query = """
                UPDATE storeassignmentimages
                SET status = %s,
                    found_sga_photo = %s,
                    auditable_photo = %s,
                    purity = %s,
                    chargeability = %s,
                    abused = %s,
                    emptyy = %s
                WHERE image_id = %s
            """
            cursor.execute(update_img_query, (
                "analysed", found_sga_result, auditable, purity,
                chargeability, abused, emptyy, image_id
            ))

            connection.commit()
            print(f"   🔄 Updated storeassignmentimages for image_id={image_id}")

        except Exception as e:
            raise RuntimeError(f"❌ Error updating storeassignmentimages for image_id={image_id}: {e}")
        finally:
            if connection:
                connection.close()

    # --- After all images are processed, update storeassignments ---
    try:
        curr, connection = connect_to_db()
        cursor = connection.cursor()
        update_assign_query = """
            UPDATE storeassignments
            SET status = %s
            WHERE assignment_id = %s
        """
        cursor.execute(update_assign_query, ("analysed", assignment_id))
        connection.commit()
        print(f"   🔄 Updated storeassignments status to 'analysed' for assignment_id={assignment_id}")
    except Exception as e:
        raise RuntimeError(f"❌ Error updating storeassignments for assignment_id={assignment_id}: {e}")
    finally:
        if connection:
            connection.close()

    print(f"\n🎯 Analysis completed for assignment_id={assignment_id}")
    return results
