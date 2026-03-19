import httpx
import asyncio
import time
from typing import List, Dict, Optional, Any
from config import SERPAPI_KEY, MAX_SEARCH_RESULTS, REQUEST_DELAY, MAX_RETRIES, RETRY_DELAY
import logging

logger = logging.getLogger(__name__)

class ImageSearcher:
    """Handle image searches via SerpAPI Google Images"""

    def __init__(self, api_key: str = SERPAPI_KEY):
        self.api_key = api_key
        self.last_request_time = 0
        self.client = None

    async def init_client(self):
        """Initialize HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30)

    async def close_client(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()

    async def _rate_limit(self):
        """Enforce rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < REQUEST_DELAY:
            await asyncio.sleep(REQUEST_DELAY - elapsed)
        self.last_request_time = time.time()

    def build_search_query(self, product: Dict[str, Any]) -> str:
        """Build optimal Google Images search query from product data"""
        parts = []

        # Use standardized name first
        if product.get('nombre_es'):
            parts.append(product['nombre_es'])

        # Add brand for specificity
        if product.get('marca'):
            parts.append(product['marca'])

        # Add SKU as fallback
        if not parts and product.get('sku'):
            parts.append(product['sku'])

        query = " ".join(filter(None, parts))

        # Clean up query
        query = query.strip()
        if not query:
            query = product.get('sku', '')

        return query[:100]  # Limit query length

    async def search_images(
        self,
        query: str,
        num_results: int = MAX_SEARCH_RESULTS
    ) -> List[Dict[str, str]]:
        """Search for images using SerpAPI"""
        if not self.api_key or self.api_key == "your_serpapi_key_here":
            logger.error("SerpAPI key not configured")
            return []

        await self.init_client()
        await self._rate_limit()

        for attempt in range(MAX_RETRIES):
            try:
                response = await self.client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": query,
                        "tbm": "isch",  # Image search
                        "api_key": self.api_key,
                        "num": min(num_results, 50),
                        "engine": "google"
                    }
                )

                if response.status_code == 200:
                    data = response.json()

                    images = []
                    for img in data.get("images_results", [])[:num_results]:
                        images.append({
                            "url": img.get("original", ""),
                            "thumbnail": img.get("thumbnail", ""),
                            "title": img.get("title", ""),
                            "source": img.get("source", "")
                        })

                    return images

                elif response.status_code == 429:
                    # Rate limited
                    if attempt < MAX_RETRIES - 1:
                        wait_time = RETRY_DELAY * (attempt + 1)
                        logger.warning(f"Rate limited, waiting {wait_time}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.error("Rate limited - max retries exceeded")
                        return []
                else:
                    logger.error(f"SerpAPI error: {response.status_code}")
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

        logger.info(f"Searching images for: {query}")
        return await self.search_images(query, num_results)

    async def batch_search_products(
        self,
        products: List[Dict[str, Any]],
        concurrent_requests: int = 3
    ) -> Dict[int, List[Dict[str, str]]]:
        """Search images for multiple products concurrently"""
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


# Global instance
_searcher = None

async def get_searcher() -> ImageSearcher:
    """Get or create global ImageSearcher instance"""
    global _searcher
    if not _searcher:
        _searcher = ImageSearcher()
    return _searcher


async def cleanup_searcher():
    """Cleanup global searcher"""
    global _searcher
    if _searcher:
        await _searcher.close_client()
        _searcher = None
