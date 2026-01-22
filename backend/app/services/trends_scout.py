"""
Google Trends Scout Service - OPTIONAL supplementary discovery via Google Trends.

Uses pytrends library to discover trending topics and related queries.

IMPORTANT: pytrends is now ARCHIVED (April 2025) and frequently rate-limited.
This service is designed to fail gracefully - it should NEVER block discovery.
Expect 429 errors and empty results - this is NORMAL.

Alternatives for reliable trends data:
- SerpApi ($75/mo) - Official-like API
- DataForSEO (~$0.002/request) - Already in config
- pytrends-async - Fork with better retry support

TARGET CUSTOMER CONTEXT:
This scout provides trend data to supplement X and Reddit signals. The trends
should be interpreted in context of our target customer:
- NON-TECHNICAL professionals who would PAY for ready-made digital products
- Examples: real estate agents, small business owners, teachers, freelancers,
  coaches, content creators, HR managers, consultants, therapists
- Price point: $15-30 for prompt packs, guides, templates, checklists

Rising queries like "chatgpt for real estate" or "ai prompts for teachers"
are high-value signals. Rising queries about coding or developer tools are not.
"""

import logging
import signal
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from functools import wraps
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Aggressive timeout - fail fast rather than stall discovery
PYTRENDS_TIMEOUT_SECONDS = 10


class TrendData(BaseModel):
    """Data for a trending topic."""

    keyword: str
    interest_score: int = Field(default=0, ge=0, le=100)
    interest_over_time: list[dict[str, Any]] = Field(default_factory=list)
    related_queries: list[str] = Field(default_factory=list)
    related_topics: list[str] = Field(default_factory=list)
    rising_queries: list[str] = Field(default_factory=list)
    region: str = "US"
    timeframe: str = "today 3-m"


def _run_with_timeout(func, timeout_seconds: int, default_value):
    """
    Run a function with a timeout. Returns default_value if it times out or fails.

    This is critical for pytrends which can hang indefinitely.
    """
    def wrapper(*args, **kwargs):
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(func, *args, **kwargs)
            try:
                return future.result(timeout=timeout_seconds)
            except FuturesTimeoutError:
                logger.warning(f"pytrends call timed out after {timeout_seconds}s")
                return default_value
            except Exception as e:
                logger.warning(f"pytrends call failed: {e}")
                return default_value
    return wrapper


class TrendsScout:
    """
    Scout service for discovering trends via Google Trends.

    Uses pytrends library (unofficial Google Trends API).

    WARNING: pytrends is unreliable and can stall. All calls have aggressive
    timeouts and will return empty/default data rather than block.

    This service is OPTIONAL - discovery works fine without it.
    """

    # Cache duration - trends don't change quickly
    CACHE_HOURS = 6

    def __init__(self, enabled: bool = True):
        self._pytrends = None
        self._enabled = enabled
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._cache: dict[str, tuple[TrendData, float]] = {}  # keyword -> (data, timestamp)
        self._rate_limit_until: float = 0  # Timestamp when rate limit expires

    def _get_pytrends(self):
        """Lazy load pytrends to avoid import errors if not installed."""
        if not self._enabled:
            return None
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq

                # Use longer timeout for reliability
                # Note: pytrends retry options have compatibility issues, keep it simple
                self._pytrends = TrendReq(
                    hl="en-US",
                    tz=360,
                    timeout=(10, 30),  # (connect timeout, read timeout) - be patient
                )
            except ImportError:
                logger.warning("pytrends not installed. Install with: pip install pytrends")
                return None
            except Exception as e:
                logger.warning(f"Failed to initialize pytrends: {e}")
                return None
        return self._pytrends

    @property
    def is_available(self) -> bool:
        """Check if pytrends is available and enabled."""
        return self._enabled and self._get_pytrends() is not None

    def disable(self):
        """Disable trends scout (useful if it's causing issues)."""
        self._enabled = False
        logger.info("TrendsScout disabled")

    def enable(self):
        """Re-enable trends scout."""
        self._enabled = True
        logger.info("TrendsScout enabled")

    def _fetch_interest_over_time_sync(
        self,
        keywords: list[str],
        timeframe: str,
        geo: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Synchronous fetch - called within timeout wrapper."""
        pytrends = self._get_pytrends()
        if not pytrends:
            return {}

        keywords = keywords[:5]
        pytrends.build_payload(keywords, timeframe=timeframe, geo=geo)
        df = pytrends.interest_over_time()

        if df.empty:
            return {kw: [] for kw in keywords}

        result = {}
        for kw in keywords:
            if kw in df.columns:
                result[kw] = [
                    {"date": str(idx.date()), "value": int(row[kw])}
                    for idx, row in df.iterrows()
                    if kw in row
                ]
            else:
                result[kw] = []
        return result

    def get_interest_over_time(
        self,
        keywords: list[str],
        timeframe: str = "today 3-m",
        geo: str = "US",
    ) -> dict[str, list[dict[str, Any]]]:
        """
        Get interest over time for keywords.

        Args:
            keywords: Up to 5 keywords to compare
            timeframe: Time range (e.g., "today 3-m", "today 12-m", "2024-01-01 2024-12-31")
            geo: Geographic region (e.g., "US", "GB", "")

        Returns:
            Dictionary mapping keywords to their interest data over time.
            Returns empty dict if timeout or error occurs.
        """
        if not self.is_available:
            return {kw: [] for kw in keywords[:5]}

        try:
            future = self._executor.submit(
                self._fetch_interest_over_time_sync, keywords, timeframe, geo
            )
            return future.result(timeout=PYTRENDS_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning(f"get_interest_over_time timed out after {PYTRENDS_TIMEOUT_SECONDS}s")
            return {kw: [] for kw in keywords[:5]}
        except Exception as e:
            logger.warning(f"Failed to get interest over time: {e}")
            return {kw: [] for kw in keywords[:5]}

    def _fetch_related_queries_sync(self, keyword: str, geo: str) -> dict[str, list[str]]:
        """Synchronous fetch - called within timeout wrapper."""
        pytrends = self._get_pytrends()
        if not pytrends:
            return {"top": [], "rising": []}

        pytrends.build_payload([keyword], geo=geo)
        related = pytrends.related_queries()

        result = {"top": [], "rising": []}
        if keyword in related:
            kw_data = related[keyword]
            if kw_data.get("top") is not None and not kw_data["top"].empty:
                result["top"] = kw_data["top"]["query"].tolist()[:10]
            if kw_data.get("rising") is not None and not kw_data["rising"].empty:
                result["rising"] = kw_data["rising"]["query"].tolist()[:10]
        return result

    def get_related_queries(
        self,
        keyword: str,
        geo: str = "US",
    ) -> dict[str, list[str]]:
        """
        Get related queries for a keyword.

        Returns both "top" (most searched) and "rising" (fastest growing) queries.

        Args:
            keyword: The keyword to analyze
            geo: Geographic region

        Returns:
            Dictionary with "top" and "rising" query lists.
            Returns empty lists if timeout or error occurs.
        """
        if not self.is_available:
            return {"top": [], "rising": []}

        try:
            future = self._executor.submit(self._fetch_related_queries_sync, keyword, geo)
            return future.result(timeout=PYTRENDS_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning(f"get_related_queries timed out after {PYTRENDS_TIMEOUT_SECONDS}s")
            return {"top": [], "rising": []}
        except Exception as e:
            logger.warning(f"Failed to get related queries: {e}")
            return {"top": [], "rising": []}

    def _fetch_related_topics_sync(self, keyword: str, geo: str) -> dict[str, list[str]]:
        """Synchronous fetch - called within timeout wrapper."""
        pytrends = self._get_pytrends()
        if not pytrends:
            return {"top": [], "rising": []}

        pytrends.build_payload([keyword], geo=geo)
        related = pytrends.related_topics()

        result = {"top": [], "rising": []}
        if keyword in related:
            kw_data = related[keyword]
            if kw_data.get("top") is not None and not kw_data["top"].empty:
                result["top"] = kw_data["top"]["topic_title"].tolist()[:10]
            if kw_data.get("rising") is not None and not kw_data["rising"].empty:
                result["rising"] = kw_data["rising"]["topic_title"].tolist()[:10]
        return result

    def get_related_topics(
        self,
        keyword: str,
        geo: str = "US",
    ) -> dict[str, list[str]]:
        """
        Get related topics for a keyword.

        Args:
            keyword: The keyword to analyze
            geo: Geographic region

        Returns:
            Dictionary with "top" and "rising" topic lists.
            Returns empty lists if timeout or error occurs.
        """
        if not self.is_available:
            return {"top": [], "rising": []}

        try:
            future = self._executor.submit(self._fetch_related_topics_sync, keyword, geo)
            return future.result(timeout=PYTRENDS_TIMEOUT_SECONDS)
        except FuturesTimeoutError:
            logger.warning(f"get_related_topics timed out after {PYTRENDS_TIMEOUT_SECONDS}s")
            return {"top": [], "rising": []}
        except Exception as e:
            logger.warning(f"Failed to get related topics: {e}")
            return {"top": [], "rising": []}

    def analyze_keyword(
        self,
        keyword: str,
        geo: str = "US",
        timeframe: str = "today 3-m",
        full_analysis: bool = False,
    ) -> TrendData:
        """
        Trend analysis for a keyword with caching and rate limit handling.

        By default, only fetches interest_over_time (1 API call) to minimize
        stalling risk. Set full_analysis=True for related queries/topics.

        Args:
            keyword: The keyword to analyze
            geo: Geographic region
            timeframe: Time range for analysis
            full_analysis: If True, also fetch related queries/topics (slower, 3 calls)

        Returns:
            TrendData with trend information. Returns default/cached data if unavailable.
        """
        import time

        cache_key = f"{keyword.lower()}:{geo}:{timeframe}"

        # Check cache first
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            cache_age_hours = (time.time() - cached_time) / 3600
            if cache_age_hours < self.CACHE_HOURS:
                logger.debug(f"Using cached trends for '{keyword}' (age: {cache_age_hours:.1f}h)")
                return cached_data

        # Check if we're rate limited
        if time.time() < self._rate_limit_until:
            wait_time = self._rate_limit_until - time.time()
            logger.info(f"Trends rate limited, returning cached/default for '{keyword}' (wait: {wait_time:.0f}s)")
            # Return cached if available, otherwise default
            if cache_key in self._cache:
                return self._cache[cache_key][0]
            return TrendData(keyword=keyword, region=geo, timeframe=timeframe)

        if not self.is_available:
            logger.info(f"TrendsScout unavailable, returning default for '{keyword}'")
            return TrendData(keyword=keyword, region=geo, timeframe=timeframe)

        # Get interest over time (single API call - fast)
        interest_data = self.get_interest_over_time([keyword], timeframe, geo)
        interest_list = interest_data.get(keyword, [])

        # Check if we got rate limited (empty result might mean 429)
        if not interest_list:
            # Set rate limit backoff for 60 seconds
            self._rate_limit_until = time.time() + 60
            logger.info(f"Trends returned empty, rate limiting for 60s")

        # Calculate average interest score
        if interest_list:
            avg_interest = sum(d["value"] for d in interest_list) / len(interest_list)
        else:
            avg_interest = 0

        # Only do full analysis if explicitly requested (adds 2 more API calls)
        related_queries: dict[str, list[str]] = {"top": [], "rising": []}
        related_topics: dict[str, list[str]] = {"top": [], "rising": []}

        if full_analysis and interest_list:  # Only do full analysis if basic worked
            related_queries = self.get_related_queries(keyword, geo)
            related_topics = self.get_related_topics(keyword, geo)

        result = TrendData(
            keyword=keyword,
            interest_score=int(avg_interest),
            interest_over_time=interest_list,
            related_queries=related_queries.get("top", []),
            rising_queries=related_queries.get("rising", []),
            related_topics=related_topics.get("top", []),
            region=geo,
            timeframe=timeframe,
        )

        # Cache the result
        self._cache[cache_key] = (result, time.time())

        return result

    def compare_keywords(
        self,
        keywords: list[str],
        geo: str = "US",
        timeframe: str = "today 3-m",
    ) -> list[dict[str, Any]]:
        """
        Compare multiple keywords by their trend scores.

        Args:
            keywords: List of keywords to compare (up to 5)
            geo: Geographic region
            timeframe: Time range

        Returns:
            List of keyword data sorted by interest score.
        """
        keywords = keywords[:5]  # Google Trends limit
        interest_data = self.get_interest_over_time(keywords, timeframe, geo)

        results = []
        for kw in keywords:
            data = interest_data.get(kw, [])
            if data:
                avg_score = sum(d["value"] for d in data) / len(data)
                latest_score = data[-1]["value"] if data else 0
                trend = "rising" if latest_score > avg_score else "stable"
            else:
                avg_score = 0
                latest_score = 0
                trend = "unknown"

            results.append({
                "keyword": kw,
                "avg_score": round(avg_score, 1),
                "latest_score": latest_score,
                "trend": trend,
            })

        # Sort by average score descending
        return sorted(results, key=lambda x: x["avg_score"], reverse=True)

    def discover_opportunities(
        self,
        seed_keywords: list[str],
        geo: str = "US",
    ) -> list[dict[str, Any]]:
        """
        Discover product opportunities from seed keywords.

        Finds rising queries and topics that could be product opportunities.

        Args:
            seed_keywords: Starting keywords to explore
            geo: Geographic region

        Returns:
            List of opportunity suggestions with trend data.
        """
        opportunities = []

        for keyword in seed_keywords[:3]:  # Limit to avoid rate limiting
            try:
                # Get rising queries (fastest growing)
                related = self.get_related_queries(keyword, geo)
                rising = related.get("rising", [])

                for query in rising[:5]:
                    opportunities.append({
                        "query": query,
                        "source_keyword": keyword,
                        "type": "rising_query",
                        "region": geo,
                    })

                # Get rising topics
                topics = self.get_related_topics(keyword, geo)
                rising_topics = topics.get("rising", [])

                for topic in rising_topics[:3]:
                    opportunities.append({
                        "topic": topic,
                        "source_keyword": keyword,
                        "type": "rising_topic",
                        "region": geo,
                    })

            except Exception as e:
                logger.warning(f"Failed to discover opportunities for {keyword}: {e}")
                continue

        return opportunities
