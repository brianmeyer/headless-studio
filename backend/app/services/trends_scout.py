"""
Google Trends Scout Service - Supplementary discovery via Google Trends.

Uses pytrends library to discover trending topics and related queries
that can inform product opportunity decisions.

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
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


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


class TrendsScout:
    """
    Scout service for discovering trends via Google Trends.

    Uses pytrends library (unofficial Google Trends API).
    Note: Rate limited, so use sparingly.
    """

    def __init__(self):
        self._pytrends = None

    def _get_pytrends(self):
        """Lazy load pytrends to avoid import errors if not installed."""
        if self._pytrends is None:
            try:
                from pytrends.request import TrendReq

                self._pytrends = TrendReq(hl="en-US", tz=360)
            except ImportError:
                logger.warning("pytrends not installed. Install with: pip install pytrends")
                return None
        return self._pytrends

    @property
    def is_available(self) -> bool:
        """Check if pytrends is available."""
        return self._get_pytrends() is not None

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
        """
        pytrends = self._get_pytrends()
        if not pytrends:
            return {}

        try:
            # Limit to 5 keywords (Google Trends limit)
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

        except Exception as e:
            logger.warning(f"Failed to get interest over time: {e}")
            return {kw: [] for kw in keywords}

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
        """
        pytrends = self._get_pytrends()
        if not pytrends:
            return {"top": [], "rising": []}

        try:
            pytrends.build_payload([keyword], geo=geo)
            related = pytrends.related_queries()

            result = {"top": [], "rising": []}

            if keyword in related:
                kw_data = related[keyword]

                # Top queries
                if kw_data.get("top") is not None and not kw_data["top"].empty:
                    result["top"] = kw_data["top"]["query"].tolist()[:10]

                # Rising queries (fastest growing)
                if kw_data.get("rising") is not None and not kw_data["rising"].empty:
                    result["rising"] = kw_data["rising"]["query"].tolist()[:10]

            return result

        except Exception as e:
            logger.warning(f"Failed to get related queries: {e}")
            return {"top": [], "rising": []}

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
        """
        pytrends = self._get_pytrends()
        if not pytrends:
            return {"top": [], "rising": []}

        try:
            pytrends.build_payload([keyword], geo=geo)
            related = pytrends.related_topics()

            result = {"top": [], "rising": []}

            if keyword in related:
                kw_data = related[keyword]

                # Top topics
                if kw_data.get("top") is not None and not kw_data["top"].empty:
                    result["top"] = kw_data["top"]["topic_title"].tolist()[:10]

                # Rising topics
                if kw_data.get("rising") is not None and not kw_data["rising"].empty:
                    result["rising"] = kw_data["rising"]["topic_title"].tolist()[:10]

            return result

        except Exception as e:
            logger.warning(f"Failed to get related topics: {e}")
            return {"top": [], "rising": []}

    def analyze_keyword(
        self,
        keyword: str,
        geo: str = "US",
        timeframe: str = "today 3-m",
    ) -> TrendData:
        """
        Comprehensive trend analysis for a keyword.

        Args:
            keyword: The keyword to analyze
            geo: Geographic region
            timeframe: Time range for analysis

        Returns:
            TrendData with all available trend information.
        """
        # Get interest over time
        interest_data = self.get_interest_over_time([keyword], timeframe, geo)
        interest_list = interest_data.get(keyword, [])

        # Calculate average interest score
        if interest_list:
            avg_interest = sum(d["value"] for d in interest_list) / len(interest_list)
        else:
            avg_interest = 0

        # Get related queries
        related_queries = self.get_related_queries(keyword, geo)

        # Get related topics
        related_topics = self.get_related_topics(keyword, geo)

        return TrendData(
            keyword=keyword,
            interest_score=int(avg_interest),
            interest_over_time=interest_list,
            related_queries=related_queries.get("top", []),
            rising_queries=related_queries.get("rising", []),
            related_topics=related_topics.get("top", []),
            region=geo,
            timeframe=timeframe,
        )

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
