import re
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
        coca_cola_products (list): List of Coca-Cola product names.
    
    Returns:
        dict: Evaluation results with purity, abused, empty, and non-Coca-Cola products.
    """
    # Normalize Coca-Cola brand names
    coca_cola_normalized = [normalize_brand(p) for p in coca_cola_products]
    
    objects = llm_response.get("objects", [])
    
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
        label = obj.get("label")
        norm_label = normalize_brand(label)
        
        if norm_label:
            # Check if normalized label contains or is contained in any Coca-Cola brand
            if any(norm_brand in norm_label or norm_label in norm_brand for norm_brand in coca_cola_normalized):
                coca_cola_count += 1
            else:
                non_coca_cola.append(label)
        else:
            non_coca_cola.append(None)  # null labels count as non-Coca-Cola

    # Determine purity
    purity = "Pure" if coca_cola_count == len(objects) else "Impure"

    # Determine abused
    abused = "Yes" if coca_cola_count == 0 else "No"

    return {
        "chargeability_percentage": llm_response.get("chargeability_percentage"),
        "auditable": llm_response.get("auditable"),
        "purity": purity,
        "abused": abused,
        "empty": "No",
        "non_coca_cola_products": non_coca_cola
    }

# llm_response = {
#     "chargeability_percentage": 75,
#     "auditable": "Yes",
#     "objects": [
#         {"object": "Bottle", "label": "Sprite", "color": "green", "description": "Lemon-lime soda"},
#         {"object": "Bottle", "label": "Minute Maid Orange", "color": "orange", "description": "Orange juice"},
#         {"object": "Bottle", "label": "Pepsi", "color": "blue", "description": "Cola beverage"}
#     ]
# }
llm_response = {
        "chargeability_percentage": 65,
        "auditable": "Yes",
        "objects": [
            {
                "object": "Mango Drink",
                "label": "FRUITI",
                "color": "Yellow",
                "description": "Yellow plastic bottle of mango flavored drink."
            },
            {
                "object": "Juice",
                "label": "Tropicana",
                "color": "Orange",
                "description": "Orange plastic bottle of juice."
            },
            {
                "object": "Water Bottle",
                "label": "Aquafina",
                "color": "Clear",
                "description": "Clear plastic bottle of water."
            },
            {
                "object": "Chocolate Bar",
                "label": "Dairy Milk",
                "color": "Purple",
                "description": "Purple packaged chocolate bar."
            },
            {
                "object": "Chocolate Bar",
                "label": "Milkybar",
                "color": "Yellow",
                "description": "Yellow packaged chocolate bar."
            },
            {
                "object": "Mints",
                "label": "POLO",
                "color": "Green",
                "description": "Small green and blue pack of Polo mints."
            },
            {
                "object": "Chocolate Box",
                "label": "Nestle Classic",
                "color": "Red",
                "description": "Red cardboard box of chocolates."
            },
            {
                "object": "Chocolate Box",
                "label": "KitKat",
                "color": "Red",
                "description": "Red cardboard box of KitKat chocolates."
            },
            {
                "object": "Sweet/Dessert",
                "label": None,
                "color": "Yellow",
                "description": "Clear plastic container with yellow sweet or dessert, multiple stacked."
            },
            {
                "object": "Juice",
                "label": "Slice",
                "color": "Orange",
                "description": "Orange plastic bottle of mango juice."
            },
            {
                "object": "Energy Drink",
                "label": "Sting",
                "color": "Orange",
                "description": "Orange plastic bottle of energy drink."
            },
            {
                "object": "Soft Drink",
                "label": "Pepsi",
                "color": "Blue",
                "description": "Large dark blue plastic bottle of Pepsi."
            },
            {
                "object": "Soft Drink",
                "label": "7 Up",
                "color": "Green",
                "description": "Large green plastic bottle of 7 Up."
            },
            {
                "object": "Soft Drink",
                "label": "Mountain Dew",
                "color": "Green",
                "description": "Large green plastic bottle of Mountain Dew."
            }
        ]
    }

# result = evaluate_cooler_smart(llm_response)
# print(result)