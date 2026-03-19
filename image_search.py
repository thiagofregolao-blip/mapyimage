import httpx
import asyncio
import time
from typing import List, Dict, Optional, Any
from config import GOOGLE_API_KEY, GOOGLE_CX_ID, MAX_SEARCH_RESULTS, REQUEST_DELAY, MAX_RETRIES, RETRY_DELAY
import logging

logger = logging.getLogger(__name__)


class ImageSearcher:
    """Handle image searches via Google Custom Search API"""

    def __init__(self, api_key: str = GOOGLE_API_KEY, cx_id: str = GOOGLE_CX_ID):
        self.api_key = api_key
        self.cx_id = cx_id
        self.last_request_time = 0
        self.client = None
        self.daily_count = 0
        self.DAILY_FREE_LIMIT = 100

    async def init_client(self):
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30)

    async def close_client(self):
        if self.client:
            await self.client.aclose()

    async def _rate_limit(self):
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def build_search_query(self, product: Dict[str, Any]) -> str:
        """Build optimal Google Images search query from product data"""
        parts = []

        # Brand + product description = best results
        marca = product.get('marca', '')
        if marca and marca not in ['GENERAL', 'SIN MARCAS', 'CHINA']:
            parts.append(marca)

        # Use standardized name (without brand since we already added it)
        nombre = product.get('nombre_es', '')
        if nombre:
            # Remove brand prefix if present
            if ' - ' in nombre:
                nombre = nombre.split(' - ', 1)[1]
            parts.append(nombre)

        # Fallback to original description
        if not parts:
            desc = product.get('descripcion_original', '')
            if desc:
                parts.append(desc)

        # Last resort: SKU
        if not parts and product.get('sku'):
            parts.append(str(product['sku']))

        query = " ".join(filter(None, parts))

        # Clean: remove long codes, limit length
        import re
        query = re.sub(r'\b\d{13,}\b', '', query)  # Remove EAN
        query = re.sub(r'\b\d{5,}[-/]\d+\b', '', query)  # Remove internal codes
        query = re.sub(r'\s+', ' ', query).strip()

        return query[:120]  # Google API limit

    async def search_images(
        self,
        query: str,
        num_results: int = MAX_SEARCH_RESULTS
    ) -> List[Dict[str, str]]:
        """Search for images using Google Custom Search API"""
        if not self.api_key or self.api_key == "your_google_api_key_here":
            logger.error("Google API key not configured")
            return []

        if not self.cx_id or self.cx_id == "your_custom_search_cx_here":
            logger.error("Google Custom Search CX ID not configured")
            return []

        await self.init_client()
        await self._rate_limit()

        # Google API returns max 10 per request
        num = min(num_results, 10)

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": self.api_key,
                        "cx": self.cx_id,
                        "q": query,
                        "searchType": "image",
                        "num": num,
                        "imgSize": "large",
                        "safe": "active",
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    self.daily_count += 1

                    images = []
                    for item in data.get("items", [])[:num_results]:
                        images.append({
                            "url": item.get("link", ""),
                            "thumbnail": item.get("image", {}).get("thumbnailLink", ""),
                            "title": item.get("title", ""),
                            "source": item.get("displayLink", ""),
                            "width": item.get("image", {}).get("width", 0),
                            "height": item.get("image", {}).get("height", 0),
                        })

                    logger.info(f"Found {len(images)} images for: {query[:50]}... (daily: {self.daily_count})")
                    return images

                elif response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (attempt + 1)
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limited - max retries exceeded. Daily limit may be reached.")
                        return []

                elif response.status_code == 403:
                    logger.error("Google API: Forbidden. Check your API key and billing.")
                    return []

                else:
                    error_msg = response.json().get("error", {}).get("message", "Unknown")
                    logger.error(f"Google API error {response.status_code}: {error_msg}")
                    return []

            except Exception as e:
                logger.error(f"Search error (attempt {attempt + 1}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RETRY_DELAY)
                    continue
                else:
                    return []

        return []

    async def search_product_images(
        self,
        product: Dict[str, Any],
        num_results: int = MAX_SEARCH_RESULTS
    ) -> List[Dict[str, str]]:
        """Search images for a product"""
        query = self.build_search_query(product)
        if not query:
            return []
        logger.info(f"Searching images for: {query[:60]}")
        return await self.search_images(query, num_results)

    async def batch_search_products(
        self,
        products: List[Dict[str, Any]],
        concurrent_requests: int = 2  # Conservative for Google API
    ) -> Dict[int, List[Dict[str, str]]]:
        """Search images for multiple products"""
        await self.init_client()

        results = {}
        semaphore = asyncio.Semaphore(concurrent_requests)

        async def search_with_semaphore(product):
            async with semaphore:
                try:
                    images = await self.search_product_images(product)
                    return product['id'], images
                except Exception as e:
                    logger.error(f"Error searching product {product.get('id')}: {str(e)}")
                    return product['id'], []

        tasks = [search_with_semaphore(p) for p in products]
        search_results = await asyncio.gather(*tasks)

        for product_id, images in search_results:
            results[product_id] = images

        return results

    def get_daily_usage(self) -> Dict[str, int]:
        """Return daily API usage stats"""
        return {
            "used": self.daily_count,
            "free_limit": self.DAILY_FREE_LIMIT,
            "remaining_free": max(0, self.DAILY_FREE_LIMIT - self.daily_count),
        }


# Global instance
_searcher = None

async def get_searcher() -> ImageSearcher:
    global _searcher
    if not _searcher:
        _searcher = ImageSearcher()
    return _searcher

async def cleanup_searcher():
    global _searcher
    if _searcher:
        await _searcher.close_client()
        _searcher = None
