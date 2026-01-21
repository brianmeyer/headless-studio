"""
X/Grok Scout Service - Primary discovery using xAI's Grok API with x_search tool.

Uses the xAI Responses API with native X search capabilities for discovering
real-time pain points, requests, and product opportunities on X.

API Documentation: https://docs.x.ai/docs/guides/tools/search-tools
"""

import json
import logging
from datetime import datetime, timedelta
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
    citations: list[str] = Field(default_factory=list)
    raw_response: dict[str, Any] | None = None


class XGrokScout:
    """
    Scout service for discovering product opportunities on X/Twitter using Grok.

    Uses xAI's Responses API with the x_search tool for native X search capabilities.
    Model: grok-3-fast (optimized for agentic search applications)
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

    def _get_date_range(self, time_filter: str) -> tuple[str, str]:
        """Convert time filter to ISO8601 date range for x_search."""
        now = datetime.utcnow()

        if time_filter == "day":
            from_date = now - timedelta(days=1)
        elif time_filter == "week":
            from_date = now - timedelta(days=7)
        elif time_filter == "month":
            from_date = now - timedelta(days=30)
        else:
            from_date = now - timedelta(days=7)  # Default to week

        return (
            from_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
            now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        )

    async def search_x(
        self,
        topics: list[str],
        search_queries: list[str] | None = None,
        time_filter: str = "week",
        limit: int = 100,
    ) -> list[XSignal]:
        """
        Search X for pain points, requests, and product opportunities.

        Uses the xAI Responses API with x_search tool for native X search.

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
            # Search and analyze for each query
            for query in queries[:10]:  # Limit to 10 queries per run
                signals = await self._search_with_x_tool(query, time_filter, topics)
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

    async def _search_with_x_tool(
        self,
        query: str,
        time_filter: str,
        topics: list[str],
    ) -> list[XSignal]:
        """
        Use the xAI Responses API with x_search tool to search X.

        This uses the proper tool-based API for X search.
        """
        from_date, to_date = self._get_date_range(time_filter)

        # Build the prompt for analyzing X posts
        prompt = f"""Search X/Twitter for posts about: "{query}"

Find posts where users are:
- Expressing frustration or pain points
- Asking for help or recommendations
- Looking for tools, templates, or resources
- Complaining about existing solutions

For each relevant post you find, analyze it and provide:
1. The full tweet text
2. Author username and follower count if available
3. Engagement metrics (likes, retweets, replies)
4. Type of signal: "request", "frustration", or "question"
5. Specific pain points mentioned
6. Any buying signals (willingness to pay, urgency)
7. Relevance score from 0.0 to 1.0

Return a structured JSON response with this format:
{{
    "tweets": [
        {{
            "tweet_id": "the_tweet_id",
            "text": "full tweet content",
            "author_username": "username",
            "author_followers": 1000,
            "likes": 10,
            "retweets": 2,
            "replies": 5,
            "created_at": "2026-01-20T10:00:00Z",
            "url": "https://x.com/username/status/tweet_id",
            "pain_point_type": "frustration",
            "pain_points": ["specific pain point"],
            "buying_signals": ["would pay for this"],
            "relevance_score": 0.85
        }}
    ]
}}

Focus on finding genuine product opportunities. Only include posts that show real demand or pain points related to: {', '.join(topics)}
"""

        try:
            async with httpx.AsyncClient(timeout=90.0) as client:
                # Use the Responses API with x_search tool
                response = await client.post(
                    f"{self.XAI_API_BASE}/responses",
                    headers=self._get_headers(),
                    json={
                        "model": "grok-3-fast",
                        "input": [
                            {"role": "user", "content": prompt}
                        ],
                        "tools": [
                            {
                                "type": "x_search",
                                "x_search": {
                                    "from_date": from_date,
                                    "to_date": to_date,
                                }
                            }
                        ],
                        "include": ["inline_citations"],
                        "temperature": 0.3,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"xAI API error: {response.status_code} - {response.text}")
                    # Fall back to chat completions if responses API fails
                    return await self._fallback_chat_search(query, time_filter, topics)

                data = response.json()

                # Extract the output text from the response
                output_text = ""
                if "output" in data:
                    for item in data.get("output", []):
                        if item.get("type") == "message":
                            for content in item.get("content", []):
                                if content.get("type") == "text":
                                    output_text = content.get("text", "")
                                    break

                # Get citations for reference
                citations = data.get("citations", [])

                # Parse the response
                signals = self._parse_grok_response(output_text, query, citations)
                return signals

        except httpx.TimeoutException:
            logger.warning(f"xAI API timeout for query: {query}")
            return []
        except Exception as e:
            logger.exception(f"xAI API call failed: {e}")
            # Try fallback
            return await self._fallback_chat_search(query, time_filter, topics)

    async def _fallback_chat_search(
        self,
        query: str,
        time_filter: str,
        topics: list[str],
    ) -> list[XSignal]:
        """
        Fallback to chat completions API if responses API is unavailable.

        This provides compatibility with older API access.
        """
        prompt = f"""Search X/Twitter for posts about: "{query}"

Find posts where users are expressing frustration, asking for help, or looking for solutions.
Focus on posts related to: {', '.join(topics)}

Return a JSON response with tweets array containing:
- tweet_id, text, author_username, likes, retweets, replies
- pain_point_type (request/frustration/question)
- pain_points array
- buying_signals array
- relevance_score (0.0-1.0)
"""

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.XAI_API_BASE}/chat/completions",
                    headers=self._get_headers(),
                    json={
                        "model": "grok-3-fast",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a market research assistant. Search X/Twitter and return JSON data about relevant posts.",
                            },
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"Fallback API error: {response.status_code}")
                    return []

                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return self._parse_grok_response(content, query, [])

        except Exception as e:
            logger.exception(f"Fallback search failed: {e}")
            return []

    def _parse_grok_response(
        self,
        content: str,
        query: str,
        citations: list[str],
    ) -> list[XSignal]:
        """Parse Grok's response into XSignal objects."""
        signals = []

        try:
            # Try to extract JSON from the response
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

                    # Build tweet URL if not provided
                    username = tweet.get("author_username", "unknown")
                    tweet_id = tweet.get("tweet_id", f"gen_{hash(tweet.get('text', ''))}")
                    url = tweet.get("url", f"https://x.com/{username}/status/{tweet_id}")

                    # Parse created_at
                    created_at_str = tweet.get("created_at")
                    if created_at_str:
                        try:
                            created_at = datetime.fromisoformat(
                                created_at_str.replace("Z", "+00:00")
                            )
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
            # Try to extract X URLs from citations as fallback
            signals = self._extract_from_citations(citations, query)

        return signals

    def _extract_from_citations(
        self,
        citations: list[str],
        query: str,
    ) -> list[XSignal]:
        """Extract basic signal data from citation URLs."""
        signals = []

        for url in citations:
            if "x.com" in url or "twitter.com" in url:
                try:
                    # Extract tweet ID and username from URL
                    parts = url.split("/")
                    if "status" in parts:
                        status_idx = parts.index("status")
                        tweet_id = parts[status_idx + 1].split("?")[0]
                        username = parts[status_idx - 1]

                        signal = XSignal(
                            tweet_id=tweet_id,
                            text=f"[Tweet from @{username}]",
                            author_username=username,
                            engagement_score=0,
                            created_at=datetime.utcnow(),
                            url=url,
                            relevance_score=0.5,
                            keywords=[query],
                        )
                        signals.append(signal)
                except Exception:
                    continue

        return signals

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
                        "model": "grok-3-fast",
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a product opportunity analyst. Analyze social signals to identify digital product opportunities. Return valid JSON.",
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
