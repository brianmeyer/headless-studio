"""
Gumroad Competition Scout - Scrapes Gumroad's public discover page for competitor analysis.

This is FREE and uses public data (robots.txt allows /discover, only /purchases/ is blocked).
Used to calculate the competition_penalty score (-20 to 0) based on real market data.

Competition Scoring Logic:
- Saturated (8+ products OR avg rating > 4.5 with 4+ products): -20 pts (hard to compete)
- Crowded (4-7 products): -10 pts
- Validated market (1-3 products): -5 pts (ideal - proven demand, room to compete)
- No competitors: -10 pts (unvalidated risk - no proof people will pay)
- Low-rated competitors (<3.5 avg rating): -3 pts (opportunity to do better!)
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import quote

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Cache duration for Gumroad results (avoid excessive scraping)
CACHE_DURATION_HOURS = 24


class GumroadProduct(BaseModel):
    """A product found on Gumroad."""

    title: str
    price_cents: int | None = None
    price_display: str | None = None
    seller_name: str | None = None
    rating: float | None = None
    review_count: int | None = None
    url: str
    thumbnail_url: str | None = None


class CompetitionData(BaseModel):
    """Competition analysis for a keyword."""

    keyword: str
    product_count: int
    products: list[GumroadProduct] = Field(default_factory=list)
    price_range_cents: tuple[int, int] | None = None
    avg_price_cents: int | None = None
    avg_rating: float | None = None
    total_reviews: int = 0
    competition_level: str  # "none", "low", "medium", "high", "saturated", "low_quality"
    competition_penalty: int  # -20 to 0
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class GumroadCompetitionScout:
    """
    Scout service for analyzing competition on Gumroad.

    Scrapes the public Gumroad discover page to find competing products.
    Results are cached to avoid excessive requests.
    """

    GUMROAD_DISCOVER_URL = "https://gumroad.com/discover"
    USER_AGENT = "HeadlessStudio/1.0 (market-research)"

    def __init__(self):
        self._cache: dict[str, CompetitionData] = {}

    async def search_competitors(
        self,
        keyword: str,
        limit: int = 20,
        use_cache: bool = True,
    ) -> CompetitionData:
        """
        Search Gumroad for competing products.

        Args:
            keyword: Search term (e.g., "chatgpt prompts real estate")
            limit: Maximum products to analyze
            use_cache: Whether to use cached results (default True)

        Returns:
            CompetitionData with products and competition scoring
        """
        cache_key = keyword.lower().strip()

        # Check cache
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            cache_age = datetime.utcnow() - cached.scraped_at
            if cache_age < timedelta(hours=CACHE_DURATION_HOURS):
                logger.debug(f"Using cached Gumroad data for '{keyword}'")
                return cached

        try:
            products = await self._fetch_products(keyword, limit)
            competition_data = self._analyze_competition(keyword, products)

            # Cache the result
            self._cache[cache_key] = competition_data
            return competition_data

        except Exception as e:
            logger.warning(f"Gumroad search failed for '{keyword}': {e}")
            # Return default medium competition on error
            return CompetitionData(
                keyword=keyword,
                product_count=0,
                competition_level="unknown",
                competition_penalty=-5,  # Default to medium
            )

    async def _fetch_products(
        self,
        keyword: str,
        limit: int,
    ) -> list[GumroadProduct]:
        """Fetch products from Gumroad discover page."""
        products: list[GumroadProduct] = []

        url = f"{self.GUMROAD_DISCOVER_URL}?query={quote(keyword)}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": self.USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml",
                },
                follow_redirects=True,
            )

            if response.status_code != 200:
                logger.warning(f"Gumroad returned status {response.status_code}")
                return []

            html = response.text
            products = self._parse_products_from_html(html, limit)

        logger.info(f"Found {len(products)} Gumroad products for '{keyword}'")
        return products

    def _parse_products_from_html(
        self,
        html: str,
        limit: int,
    ) -> list[GumroadProduct]:
        """
        Parse product cards from Gumroad HTML.

        Gumroad uses React on Rails with js-react-on-rails-component scripts.
        The Discover component contains search_results with product data.
        """
        products: list[GumroadProduct] = []

        try:
            import json

            # Gumroad uses React on Rails - look for Discover component data
            discover_match = re.search(
                r'data-component-name="Discover"[^>]*>(.*?)</script>',
                html,
                re.DOTALL,
            )

            if discover_match:
                try:
                    discover_data = json.loads(discover_match.group(1))
                    search_results = discover_data.get("search_results", {})

                    # search_results is a dict with 'products' key
                    if isinstance(search_results, dict):
                        product_list = search_results.get("products", [])
                    else:
                        product_list = search_results if isinstance(search_results, list) else []

                    for item in product_list[:limit]:
                        try:
                            product = self._parse_product_item(item)
                            if product:
                                products.append(product)
                        except Exception:
                            continue

                    if products:
                        return products
                except json.JSONDecodeError:
                    logger.debug("Failed to parse Discover component JSON")

            # Fallback: Parse HTML directly using regex
            products = self._extract_from_html_regex(html, limit)

        except Exception as e:
            logger.warning(f"Error parsing Gumroad HTML: {e}")

        return products

    def _parse_product_item(self, item: dict[str, Any]) -> GumroadProduct | None:
        """Parse a single product item from JSON data."""
        if not isinstance(item, dict):
            return None

        title = item.get("name") or item.get("title") or ""
        if not title:
            return None

        # Parse price (Gumroad uses cents)
        price_cents = item.get("price_cents")
        price_display = item.get("formatted_price")

        # Parse rating - Gumroad nests it in 'ratings' object
        rating = None
        review_count = None
        ratings_data = item.get("ratings", {})
        if isinstance(ratings_data, dict):
            if "average" in ratings_data:
                try:
                    rating = float(ratings_data["average"])
                except (ValueError, TypeError):
                    pass
            if "count" in ratings_data:
                review_count = ratings_data["count"]
        else:
            # Fallback for flat structure
            if "rating" in item:
                try:
                    rating = float(item["rating"])
                except (ValueError, TypeError):
                    pass
            elif "average_rating" in item:
                try:
                    rating = float(item["average_rating"])
                except (ValueError, TypeError):
                    pass
            if "ratings_count" in item:
                review_count = item["ratings_count"]

        # Parse seller - Gumroad nests it in 'seller' object
        seller_name = None
        seller_data = item.get("seller", {})
        if isinstance(seller_data, dict):
            seller_name = seller_data.get("name")
        else:
            seller_name = item.get("seller_name") or item.get("creator_name")

        # Build URL
        url = item.get("url", "")
        if not url and "permalink" in item:
            url = f"https://gumroad.com/l/{item['permalink']}"

        return GumroadProduct(
            title=title,
            price_cents=price_cents,
            price_display=price_display,
            seller_name=seller_name,
            rating=rating,
            review_count=review_count,
            url=url,
            thumbnail_url=item.get("thumbnail_url") or item.get("cover_url"),
        )

    def _extract_from_html_regex(
        self,
        html: str,
        limit: int,
    ) -> list[GumroadProduct]:
        """
        Fallback: Extract products using regex patterns.

        This is less reliable but works if the JSON approach fails.
        """
        products: list[GumroadProduct] = []

        # Look for product links and titles
        # Pattern for Gumroad product cards
        product_pattern = re.compile(
            r'href="(https://[^"]*gumroad\.com/l/[^"]+)"[^>]*>.*?'
            r'(?:class="[^"]*product[^"]*"[^>]*>.*?)?'
            r'<[^>]*>([^<]{5,100})</[^>]*>',
            re.DOTALL | re.IGNORECASE,
        )

        matches = product_pattern.findall(html)

        for url, title in matches[:limit]:
            title = title.strip()
            if title and len(title) > 3:
                products.append(
                    GumroadProduct(
                        title=title,
                        url=url,
                    )
                )

        # Deduplicate by URL
        seen_urls = set()
        unique_products = []
        for p in products:
            if p.url not in seen_urls:
                seen_urls.add(p.url)
                unique_products.append(p)

        return unique_products[:limit]

    def _analyze_competition(
        self,
        keyword: str,
        products: list[GumroadProduct],
    ) -> CompetitionData:
        """
        Analyze competition level and calculate penalty.

        Scoring Logic:
        - Saturated: 8+ products OR (4+ products with avg rating > 4.5) → -20
        - High: 4-7 products → -10
        - Validated: 1-3 products → -5 (ideal!)
        - None: 0 products → -10 (unvalidated risk)
        - Low Quality: Any count but avg rating < 3.5 → -3 (opportunity!)
        """
        count = len(products)

        # Calculate price statistics
        prices = [p.price_cents for p in products if p.price_cents is not None]
        price_range = (min(prices), max(prices)) if prices else None
        avg_price = int(sum(prices) / len(prices)) if prices else None

        # Calculate rating statistics (only count products with actual reviews)
        ratings = [p.rating for p in products if p.rating is not None and p.review_count and p.review_count > 0]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        total_reviews = sum(p.review_count or 0 for p in products)

        # Determine competition level and penalty
        if count == 0:
            level = "none"
            penalty = -10  # Unvalidated - risky
        elif avg_rating is not None and avg_rating < 3.5 and count > 0:
            level = "low_quality"
            penalty = -3  # Opportunity to do better!
        elif count >= 8 or (count >= 4 and avg_rating and avg_rating > 4.5):
            level = "saturated"
            penalty = -20  # Very hard to compete
        elif count >= 4:
            level = "high"
            penalty = -10  # Crowded
        else:  # 1-3 products
            level = "validated"
            penalty = -5  # Ideal - proven demand, room to compete

        return CompetitionData(
            keyword=keyword,
            product_count=count,
            products=products,
            price_range_cents=price_range,
            avg_price_cents=avg_price,
            avg_rating=avg_rating,
            total_reviews=total_reviews,
            competition_level=level,
            competition_penalty=penalty,
        )

    def clear_cache(self):
        """Clear the product cache."""
        self._cache.clear()
        logger.info("Gumroad cache cleared")

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        return {
            "cached_keywords": len(self._cache),
            "keywords": list(self._cache.keys()),
        }
