"""
X/Grok Scout Service - Primary discovery using xAI's Grok API.

Grok has native X/Twitter search capability, making it ideal for discovering
real-time pain points, requests, and product opportunities on X.
"""

import logging
from datetime import datetime
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.config import Settings

logger = logging.getLogger(__name__)


class XSignal(BaseModel):
    """A signal discovered from X/Twitter via Grok."""

    tweet_id: str
    text: str
    author_username: str
    author_followers: int | None = None
    engagement_score: int = Field(default=0, description="likes + retweets + replies")
    created_at: datetime
    url: str
    relevance_score: float = Field(default=0.0, ge=0, le=1)
    pain_point_type: str | None = None  # "request", "frustration", "question"

    # Extracted signals
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class XSearchResponse(BaseModel):
    """Response from X search."""

    success: bool
    query: str
    signal_count: int
    signals: list[XSignal]
    raw_response: dict[str, Any] | None = None


class XGrokScout:
    """
    Scout service for discovering product opportunities on X/Twitter using Grok.

    Uses xAI's Grok API which has native X search capabilities.
    """

    XAI_API_BASE = "https://api.x.ai/v1"

    # Search query templates for finding product opportunities
    SEARCH_TEMPLATES = [
        "{topic} need help",
        "{topic} frustrated",
        "{topic} wish there was",
        "{topic} looking for",
        "{topic} anyone know",
        "{topic} recommendation",
        "{topic} best way to",
        "{topic} struggle with",
        "{topic} how do I",
        "{topic} can't find",
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = settings.xai_api_key

        if not self.api_key:
            logger.warning("XAI_API_KEY not configured - X/Grok scout will be disabled")

    @property
    def is_configured(self) -> bool:
        """Check if the xAI API is configured."""
        return bool(self.api_key)

    def _get_headers(self) -> dict[str, str]:
        """Get headers for xAI API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def search_x(
        self,
        topics: list[str],
        search_queries: list[str] | None = None,
        time_filter: str = "week",
        limit: int = 100,
    ) -> list[XSignal]:
        """
        Search X for pain points, requests, and product opportunities.

        Uses Grok to search X and analyze results for relevance.

        Args:
            topics: List of topics to search (e.g., ["chatgpt prompts", "AI tools"])
            search_queries: Optional custom search queries (overrides templates)
            time_filter: Time range - "day", "week", "month"
            limit: Maximum signals to return

        Returns:
            List of XSignal objects with relevance scores
        """
        if not self.is_configured:
            logger.warning("X/Grok scout not configured, returning empty results")
            return []

        all_signals: list[XSignal] = []

        # Build search queries
        queries = search_queries or []
        if not queries:
            for topic in topics:
                for template in self.SEARCH_TEMPLATES[:5]:  # Use top 5 templates
                    queries.append(template.format(topic=topic))

        try:
            # Use Grok to search and analyze X posts
            for query in queries[:10]:  # Limit to 10 queries per run
                signals = await self._search_and_analyze(query, time_filter)
                all_signals.extend(signals)

                if len(all_signals) >= limit:
                    break

            # Deduplicate by tweet_id
            seen_ids = set()
            unique_signals = []
            for signal in all_signals:
                if signal.tweet_id not in seen_ids:
                    seen_ids.add(signal.tweet_id)
                    unique_signals.append(signal)

            # Sort by relevance and engagement
            unique_signals.sort(
                key=lambda s: (s.relevance_score, s.engagement_score),
                reverse=True,
            )

            return unique_signals[:limit]

        except Exception as e:
            logger.exception(f"X search failed: {e}")
            return []

    async def _search_and_analyze(
        self,
        query: str,
        time_filter: str,
    ) -> list[XSignal]:
        """
        Use Grok to search X and analyze results.

        Grok can search X natively and provide structured analysis.
        """
        prompt = f"""Search X/Twitter for recent posts matching this query: "{query}"

Focus on finding posts where users are:
- Expressing frustration or pain points
- Asking for help or recommendations
- Looking for tools, templates, or resources
- Complaining about existing solutions

For each relevant post found, extract:
1. The tweet text
2. Author username
3. Engagement (likes, retweets, replies estimate)
4. What type of signal it is (request, frustration, question)
5. Key pain points mentioned
6. Any buying signals (willingness to pay, urgency)

Time filter: {time_filter}

Return the results as a JSON array with this structure:
{{
    "tweets": [
        {{
            "tweet_id": "unique_id",
            "text": "tweet content",
            "author_username": "username",
            "author_followers": 1000,
            "likes": 10,
            "retweets": 2,
            "replies": 5,
            "created_at": "2026-01-20T10:00:00Z",
            "pain_point_type": "frustration",
            "pain_points": ["can't find good prompts"],
            "buying_signals": ["would pay for this"],
            "relevance_score": 0.85
        }}
    ]
}}

Only include posts that are genuinely relevant to product opportunities.
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.XAI_API_BASE}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": "grok-beta",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a market research assistant that searches X/Twitter for product opportunities. Always return valid JSON.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"xAI API error: {response.status_code} - {response.text}")
                    return []

                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Parse the JSON response
                signals = self._parse_grok_response(content, query)
                return signals

        except httpx.TimeoutException:
            logger.warning(f"xAI API timeout for query: {query}")
            return []
        except Exception as e:
            logger.exception(f"xAI API call failed: {e}")
            return []

    def _parse_grok_response(self, content: str, query: str) -> list[XSignal]:
        """Parse Grok's response into XSignal objects."""
        import json

        signals = []

        try:
            # Try to extract JSON from the response
            # Grok might wrap it in markdown code blocks
            json_str = content
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0]

            data = json.loads(json_str.strip())
            tweets = data.get("tweets", [])

            for tweet in tweets:
                try:
                    # Calculate engagement score
                    engagement = (
                        tweet.get("likes", 0)
                        + tweet.get("retweets", 0) * 2
                        + tweet.get("replies", 0) * 3
                    )

                    # Build tweet URL
                    username = tweet.get("author_username", "unknown")
                    tweet_id = tweet.get("tweet_id", f"generated_{hash(tweet.get('text', ''))}")
                    url = f"https://x.com/{username}/status/{tweet_id}"

                    # Parse created_at
                    created_at_str = tweet.get("created_at")
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
                        except ValueError:
                            created_at = datetime.utcnow()
                    else:
                        created_at = datetime.utcnow()

                    signal = XSignal(
                        tweet_id=tweet_id,
                        text=tweet.get("text", ""),
                        author_username=username,
                        author_followers=tweet.get("author_followers"),
                        engagement_score=engagement,
                        created_at=created_at,
                        url=url,
                        relevance_score=float(tweet.get("relevance_score", 0.5)),
                        pain_point_type=tweet.get("pain_point_type"),
                        pain_points=tweet.get("pain_points", []),
                        buying_signals=tweet.get("buying_signals", []),
                        keywords=[query],
                    )
                    signals.append(signal)

                except Exception as e:
                    logger.warning(f"Failed to parse tweet: {e}")
                    continue

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Grok JSON response: {e}")
            # Try to extract signals from free-form text
            signals = self._parse_freeform_response(content)

        return signals

    def _parse_freeform_response(self, content: str) -> list[XSignal]:
        """Fallback parser for non-JSON responses."""
        # This is a fallback if Grok doesn't return proper JSON
        # In production, we'd implement more robust parsing
        logger.info("Falling back to freeform response parsing")
        return []

    async def analyze_signals(
        self,
        signals: list[XSignal],
    ) -> dict[str, Any]:
        """
        Use Grok to analyze a batch of signals and identify opportunities.

        Args:
            signals: List of XSignal objects to analyze

        Returns:
            Analysis with opportunity suggestions
        """
        if not signals:
            return {"opportunities": [], "summary": "No signals to analyze"}

        if not self.is_configured:
            return {"opportunities": [], "summary": "X/Grok scout not configured"}

        # Prepare signals for analysis
        signal_texts = [
            f"- @{s.author_username}: {s.text[:200]}..." for s in signals[:20]
        ]
        signal_summary = "\n".join(signal_texts)

        prompt = f"""Analyze these X/Twitter posts for product opportunity patterns:

{signal_summary}

Identify:
1. Common pain points across posts
2. Specific product ideas that could solve these problems
3. Target audience characteristics
4. Suggested product types (prompt pack, guide, template, checklist)
5. Potential keywords for SEO

Return as JSON:
{{
    "opportunities": [
        {{
            "title": "Suggested product title",
            "description": "What this product would solve",
            "target_audience": "Who would buy this",
            "product_type": "prompt_pack",
            "confidence": 0.8,
            "pain_points": ["list of pain points addressed"],
            "keywords": ["seo", "keywords"]
        }}
    ],
    "summary": "Overall analysis of the opportunity space"
}}
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.XAI_API_BASE}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": "grok-beta",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product opportunity analyst. Analyze social signals to identify digital product opportunities.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.5,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"xAI API error: {response.status_code}")
                    return {"opportunities": [], "summary": "Analysis failed"}

                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

                # Parse JSON response
                import json

                try:
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0]
                    elif "```" in content:
                        json_str = content.split("```")[1].split("```")[0]
                    else:
                        json_str = content

                    return json.loads(json_str.strip())
                except json.JSONDecodeError:
                    return {
                        "opportunities": [],
                        "summary": content[:500],
                    }

        except Exception as e:
            logger.exception(f"Signal analysis failed: {e}")
            return {"opportunities": [], "summary": f"Analysis error: {e}"}

    def get_search_queries(self, topics: list[str]) -> list[str]:
        """Generate search queries for given topics."""
        queries = []
        for topic in topics:
            for template in self.SEARCH_TEMPLATES:
                queries.append(template.format(topic=topic))
        return queries
