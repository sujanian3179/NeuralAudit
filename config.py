"""
Configuration file for NeuralAudit system
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ===================== SELENIUM CONFIG =====================
SELENIUM_HEADLESS = os.getenv("SELENIUM_HEADLESS", "True").lower() == "true"
SELENIUM_WAIT_TIMEOUT = int(os.getenv("SELENIUM_WAIT_TIMEOUT", "10"))
SELENIUM_IMPLICIT_WAIT = int(os.getenv("SELENIUM_IMPLICIT_WAIT", "5"))
SCREENSHOT_ON_ERROR = os.getenv("SCREENSHOT_ON_ERROR", "True").lower() == "true"

# ===================== IMAGE PREPROCESSING CONFIG =====================
IMAGE_SIZE = int(os.getenv("IMAGE_SIZE", "224"))
CROP_RATIO = float(os.getenv("CROP_RATIO", "0.6"))  # Center crop 60% of image
HSV_HUE_THRESHOLD = int(os.getenv("HSV_HUE_THRESHOLD", "15"))

# ===================== MODEL CONFIG =====================
MODEL_NAME = os.getenv("MODEL_NAME", "resnet18")
NUM_CLASSES = int(os.getenv("NUM_CLASSES", "10"))
MODEL_CHECKPOINT = os.getenv("MODEL_CHECKPOINT", "./models/resnet18_colors.pth")
DEVICE = os.getenv("DEVICE", "cpu")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.70"))

# ===================== COLOR FAMILIES =====================
COLOR_FAMILIES = {
    0: "Red",
    1: "Blue",
    2: "Green",
    3: "Yellow",
    4: "Orange",
    5: "Purple",
    6: "Pink",
    7: "Brown",
    8: "Black",
    9: "White"
}

# ===================== COLOR MAPPING (Metadata -> Family) =====================
COLOR_LABEL_TO_FAMILY = {
    # Reds
    "red": "Red",
    "crimson": "Red",
    "scarlet": "Red",
    "burgundy": "Red",
    "maroon": "Red",
    "brick": "Red",
    "rust": "Red",
    
    # Blues
    "blue": "Blue",
    "navy": "Blue",
    "cyan": "Blue",
    "cobalt": "Blue",
    "midnight": "Blue",
    "royal": "Blue",
    "steel": "Blue",
    "periwinkle": "Blue",
    "teal": "Blue",
    "aqua": "Blue",
    
    # Greens
    "green": "Green",
    "lime": "Green",
    "forest": "Green",
    "olive": "Green",
    "sage": "Green",
    "mint": "Green",
    "emerald": "Green",
    "moss": "Green",
    
    # Yellows
    "yellow": "Yellow",
    "gold": "Yellow",
    "lemon": "Yellow",
    "sunny": "Yellow",
    "buttercup": "Yellow",
    
    # Oranges
    "orange": "Orange",
    "coral": "Orange",
    "peach": "Orange",
    "salmon": "Orange",
    "apricot": "Orange",
    "tangerine": "Orange",
    
    # Purples
    "purple": "Purple",
    "violet": "Purple",
    "lavender": "Purple",
    "plum": "Purple",
    "indigo": "Purple",
    "mauve": "Purple",
    
    # Pinks
    "pink": "Pink",
    "rose": "Pink",
    "magenta": "Pink",
    "fuchsia": "Pink",
    "blush": "Pink",
    "hot pink": "Pink",
    
    # Browns
    "brown": "Brown",
    "tan": "Brown",
    "beige": "Brown",
    "taupe": "Brown",
    "khaki": "Brown",
    "camel": "Brown",
    "chocolate": "Brown",
    
    # Blacks
    "black": "Black",
    "charcoal": "Black",
    "ebony": "Black",
    
    # Whites
    "white": "White",
    "cream": "White",
    "ivory": "White",
    "off-white": "White",
    "natural": "White",
    "beige": "White",
}

# ===================== SUPABASE CONFIG =====================
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ===================== API CONFIG =====================
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
API_DEBUG = os.getenv("API_DEBUG", "False").lower() == "true"

# ===================== LOGGING CONFIG =====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "./logs/neuralaudit.log")

# ===================== PROCESSING CONFIG =====================
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
PROCESSING_BATCH_SIZE = int(os.getenv("PROCESSING_BATCH_SIZE", "5"))
