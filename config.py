import os
from pathlib import Path

# ============================================================
# Google Custom Search API
# Get your keys at:
#   API Key: https://console.cloud.google.com/apis/credentials
#   CX ID:   https://programmablesearchengine.google.com/
# ============================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "your_google_api_key_here")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID", "your_custom_search_cx_here")

# Database & Storage
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/products.db")
IMAGES_DIR = os.getenv("IMAGES_DIR", "data/images")
MAX_SEARCH_RESULTS = 10
ITEMS_PER_PAGE = 24
BATCH_SIZE = 5

# Create directories
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# API rate limiting (Google allows ~100 free/day)
SEARCH_TIMEOUT = 30
REQUEST_DELAY = 1.0
MAX_RETRIES = 3
RETRY_DELAY = 2

# Database
SQLITE_CHECK_SAME_THREAD = False

# Pagination
DEFAULT_PAGE = 1

# Status
STATUS_CHOICES = ["pending", "partial", "complete", "no_image"]

# UI Language
LANGUAGE = "es"

# Dynamic (populated from XLSX)
VALID_CATEGORIES = []
VALID_BRANDS = []
