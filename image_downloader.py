"""
Mapy Image Downloader
Downloads 2-3 product images from Google Custom Search API
Organizes in folders by category
"""
import httpx
import asyncio
import os
import re
import json
import time
import hashlib
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_CX_ID = os.getenv("GOOGLE_CX_ID", "")
IMAGES_PER_PRODUCT = 3
OUTPUT_DIR = "images"
PROGRESS_FILE = "progress.json"
REQUEST_DELAY = 1.2  # seconds between API calls
DOWNLOAD_TIMEOUT = 15
MAX_RETRIES = 2


class ImageDownloader:
    def __init__(self, api_key: str = "", cx_id: str = ""):
        self.api_key = api_key or GOOGLE_API_KEY
        self.cx_id = cx_id or GOOGLE_CX_ID
        self.daily_count = 0
        self.total_downloaded = 0
        self.total_failed = 0
        self.progress = {}
        self.client = None

    async def init(self):
        self.client = httpx.AsyncClient(timeout=DOWNLOAD_TIMEOUT, follow_redirects=True)
        self._load_progress()

    async def close(self):
        if self.client:
            await self.client.aclose()
        self._save_progress()

    def _load_progress(self):
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                self.progress = json.load(f)
            logger.info(f"Progress loaded: {len(self.progress)} products already processed")

    def _save_progress(self):
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(self.progress, f)

    def _build_query(self, row: Dict) -> str:
        """Build search query optimized for product images"""
        parts = []
        marca = str(row.get('MARCA', '')).strip()
        desc = str(row.get('DESCRIPCION', '')).strip()

        if marca and marca not in ['GENERAL', 'SIN MARCAS', 'CHINA']:
            parts.append(marca)

        # Clean description: remove codes
        clean = re.sub(r'\b\d{13,}\b', '', desc)
        clean = re.sub(r'\b\d{5,}[-/]\d+\b', '', clean)
        clean = re.sub(r'\s+', ' ', clean).strip()
        parts.append(clean)

        query = ' '.join(parts)[:120]
        return query

    async def search_images(self, query: str, num: int = 5) -> List[Dict]:
        """Search Google Custom Search API for images"""
        if not self.api_key or not self.cx_id:
            logger.error("Google API Key or CX ID not configured!")
            return []

        await asyncio.sleep(REQUEST_DELAY)
        self.daily_count += 1

        try:
            resp = await self.client.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": self.api_key,
                    "cx": self.cx_id,
                    "q": query,
                    "searchType": "image",
                    "num": min(num, 10),
                    "imgSize": "large",
                    "safe": "active",
                }
            )

            if resp.status_code == 200:
                data = resp.json()
                images = []
                for item in data.get("items", []):
                    images.append({
                        "url": item.get("link", ""),
                        "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
                        "title": item.get("title", ""),
                        "width": item.get("image", {}).get("width", 0),
                        "height": item.get("image", {}).get("height", 0),
                        "mime": item.get("mime", ""),
                    })
                return images

            elif resp.status_code == 429:
                logger.warning("Rate limited! Daily quota may be exhausted.")
                return []
            elif resp.status_code == 403:
                logger.error("API Forbidden. Check API key and billing.")
                return []
            else:
                logger.error(f"API error {resp.status_code}: {resp.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    async def download_image(self, url: str, save_path: str) -> bool:
        """Download image from URL and save to disk"""
        for attempt in range(MAX_RETRIES):
            try:
                resp = await self.client.get(url)
                if resp.status_code == 200:
                    content_type = resp.headers.get('content-type', '')
                    if 'image' in content_type or url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                        with open(save_path, 'wb') as f:
                            f.write(resp.content)
                        if os.path.getsize(save_path) > 1000:  # >1KB = valid image
                            return True
                        else:
                            os.remove(save_path)
                return False
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(1)
                continue
        return False

    def _get_extension(self, url: str, mime: str = "") -> str:
        if 'png' in mime or url.endswith('.png'):
            return '.png'
        if 'webp' in mime or url.endswith('.webp'):
            return '.webp'
        return '.jpg'

    async def process_product(self, row: Dict, category_dir: str) -> Dict:
        """Search and download images for one product"""
        sku = str(row.get('SKU', ''))

        # Skip if already processed
        if sku in self.progress and self.progress[sku].get('status') == 'complete':
            return self.progress[sku]

        query = self._build_query(row)
        logger.info(f"[{self.daily_count}] SKU {sku}: {query[:60]}...")

        # Search
        images = await self.search_images(query, num=IMAGES_PER_PRODUCT + 2)

        if not images:
            result = {"sku": sku, "status": "no_results", "images": [], "query": query}
            self.progress[sku] = result
            self.total_failed += 1
            return result

        # Download top images
        downloaded = []
        product_dir = os.path.join(category_dir, sku)
        os.makedirs(product_dir, exist_ok=True)

        for i, img in enumerate(images[:IMAGES_PER_PRODUCT + 2]):
            if len(downloaded) >= IMAGES_PER_PRODUCT:
                break

            ext = self._get_extension(img['url'], img.get('mime', ''))
            filename = f"{sku}_img{len(downloaded)+1}{ext}"
            filepath = os.path.join(product_dir, filename)

            success = await self.download_image(img['url'], filepath)
            if success:
                downloaded.append({
                    "file": filepath,
                    "url": img['url'],
                    "thumbnail": img['thumbnail'],
                })

        status = "complete" if len(downloaded) >= 2 else ("partial" if downloaded else "failed")
        result = {
            "sku": sku,
            "status": status,
            "images": downloaded,
            "query": query,
            "results_found": len(images),
        }
        self.progress[sku] = result

        if downloaded:
            self.total_downloaded += len(downloaded)
            logger.info(f"  ✅ Downloaded {len(downloaded)} images")
        else:
            self.total_failed += 1
            logger.warning(f"  ❌ No images downloaded")

        # Save progress every 50 products
        if len(self.progress) % 50 == 0:
            self._save_progress()

        return result

    async def process_category(self, df: pd.DataFrame, category: str, limit: int = 0):
        """Process all products in a category"""
        cat_clean = re.sub(r'[/\\. ]', '_', category)
        cat_dir = os.path.join(OUTPUT_DIR, cat_clean)
        os.makedirs(cat_dir, exist_ok=True)

        products = df[df['CATEGORIA'] == category]
        total = len(products) if limit == 0 else min(limit, len(products))

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {category} ({total} products)")
        logger.info(f"Output: {cat_dir}")
        logger.info(f"{'='*60}")

        stats = {"complete": 0, "partial": 0, "failed": 0, "no_results": 0, "skipped": 0}

        for i, (_, row) in enumerate(products.head(total).iterrows()):
            sku = str(row.get('SKU', ''))
            if sku in self.progress and self.progress[sku].get('status') == 'complete':
                stats['skipped'] += 1
                continue

            result = await self.process_product(row.to_dict(), cat_dir)
            stats[result['status']] = stats.get(result['status'], 0) + 1

            # Print progress every 10
            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i+1}/{total} | API calls: {self.daily_count}")

            # Check daily limit
            if self.daily_count >= 95:  # Leave buffer before 100 free limit
                logger.warning("Approaching daily API limit! Saving progress...")
                self._save_progress()
                return stats

        self._save_progress()

        logger.info(f"\n--- {category} DONE ---")
        logger.info(f"  Complete (2-3 imgs): {stats['complete']}")
        logger.info(f"  Partial (1 img):     {stats['partial']}")
        logger.info(f"  Failed:              {stats['failed']}")
        logger.info(f"  No results:          {stats['no_results']}")
        logger.info(f"  Skipped (done):      {stats['skipped']}")

        return stats

    async def process_all(self, xlsx_path: str, limit_per_category: int = 0):
        """Process all categories from XLSX"""
        df = pd.read_excel(xlsx_path)
        logger.info(f"Loaded {len(df)} products from {xlsx_path}")

        all_stats = {}
        for cat in df['CATEGORIA'].value_counts().index:
            stats = await self.process_category(df, cat, limit_per_category)
            all_stats[cat] = stats

            if self.daily_count >= 95:
                logger.warning("Daily limit reached. Run again tomorrow to continue.")
                break

        # Final report
        logger.info(f"\n{'='*60}")
        logger.info(f"FINAL REPORT")
        logger.info(f"{'='*60}")
        logger.info(f"API calls used: {self.daily_count}")
        logger.info(f"Images downloaded: {self.total_downloaded}")
        logger.info(f"Products processed: {len(self.progress)}")

        return all_stats


# ============================================================
# MAIN - CLI
# ============================================================
async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Mapy Image Downloader")
    parser.add_argument("xlsx", help="Path to XLSX catalog file")
    parser.add_argument("--category", "-c", help="Process only this category")
    parser.add_argument("--limit", "-l", type=int, default=0, help="Limit products per category (0=all)")
    parser.add_argument("--api-key", help="Google API Key")
    parser.add_argument("--cx-id", help="Google CX ID")
    parser.add_argument("--output", "-o", default="images", help="Output directory")
    args = parser.parse_args()

    global OUTPUT_DIR
    OUTPUT_DIR = args.output

    downloader = ImageDownloader(
        api_key=args.api_key or GOOGLE_API_KEY,
        cx_id=args.cx_id or GOOGLE_CX_ID,
    )
    await downloader.init()

    try:
        if args.category:
            df = pd.read_excel(args.xlsx)
            await downloader.process_category(df, args.category, args.limit)
        else:
            await downloader.process_all(args.xlsx, args.limit)
    finally:
        await downloader.close()


if __name__ == "__main__":
    asyncio.run(main())
