import os
from pathlib import Path

# Environment variables with defaults
SERPAPI_KEY = os.getenv("SERPAPI_KEY", "your_serpapi_key_here")
DATABASE_PATH = "/sessions/lucid-laughing-allen/mapy_data/products.db"
IMAGES_DIR = "/sessions/lucid-laughing-allen/mapy_data/images"
MAX_SEARCH_RESULTS = 10
ITEMS_PER_PAGE = 24
BATCH_SIZE = 5  # Images to search concurrently per batch

# Create directories if they don't exist
Path(IMAGES_DIR).mkdir(parents=True, exist_ok=True)
Path(DATABASE_PATH).parent.mkdir(parents=True, exist_ok=True)

# Image search settings
SEARCH_TIMEOUT = 30  # seconds
REQUEST_DELAY = 1.5  # seconds between SerpAPI requests (rate limiting)
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Database settings
SQLITE_CHECK_SAME_THREAD = False

# Pagination
DEFAULT_PAGE = 1

# Status categories
STATUS_CHOICES = ["pending", "partial", "complete", "no_image"]

# UI Language
LANGUAGE = "es"  # Spanish

# Categories and Brands (will be populated from XLSX)
VALID_CATEGORIES = []
VALID_BRANDS = []
