"""
Signal models for discovery and validation.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class RedditSignal(BaseModel):
    """A signal discovered from Reddit."""

    subreddit: str
    post_id: str
    post_title: str
    post_url: str
    post_score: int = 0
    comment_count: int = 0
    created_utc: datetime

    # Extracted intent signals
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)

    # Relevance scoring
    relevance_score: float = Field(default=0.0, ge=0, le=1)


class TwitterSignal(BaseModel):
    """A signal discovered from X/Twitter."""

    tweet_id: str
    tweet_text: str
    tweet_url: str
    likes: int = 0
    retweets: int = 0
    replies: int = 0
    created_at: datetime

    # Extracted signals
    pain_points: list[str] = Field(default_factory=list)
    buying_signals: list[str] = Field(default_factory=list)

    relevance_score: float = Field(default=0.0, ge=0, le=1)


class TrendSignal(BaseModel):
    """A signal from Google Trends or similar."""

    keyword: str
    trend_score: int = Field(default=0, ge=0, le=100)
    related_queries: list[str] = Field(default_factory=list)
    region: str = "US"


class KeywordSignal(BaseModel):
    """Keyword research data."""

    keyword: str
    monthly_volume: int = 0
    cpc: float = 0.0
    competition: float = Field(default=0.5, ge=0, le=1)
    trend: str = "stable"  # rising, stable, declining
    related_keywords: list[str] = Field(default_factory=list)


class DiscoverySignal(BaseModel):
    """Aggregated discovery signal for opportunity creation."""

    # Core identification
    topic: str
    product_type: str  # prompt_pack, guide, roadmap, template_pack, checklist

    # Signals from various sources
    reddit_signals: list[RedditSignal] = Field(default_factory=list)
    twitter_signals: list[TwitterSignal] = Field(default_factory=list)
    trend_signals: list[TrendSignal] = Field(default_factory=list)
    keyword_signals: list[KeywordSignal] = Field(default_factory=list)

    # Aggregated metrics
    total_mentions: int = 0
    avg_engagement: float = 0.0
    sentiment: str = "neutral"  # positive, neutral, negative

    # Best keyword for targeting
    primary_keyword: str | None = None
    monthly_volume: int | None = None
    cpc: float | None = None

    # Evidence URLs for human review
    evidence_urls: list[str] = Field(default_factory=list)

    # Competitor analysis
    competitors: list[dict[str, Any]] = Field(default_factory=list)


class OrganicSignals(BaseModel):
    """Tracked organic validation signals."""

    # Signal counts
    dms: int = Field(default=0, ge=0)
    buy_comments: int = Field(default=0, ge=0)
    questions: int = Field(default=0, ge=0)
    upvotes: int = Field(default=0, ge=0)
    shares: int = Field(default=0, ge=0)
    email_signups: int = Field(default=0, ge=0)

    @property
    def total_points(self) -> int:
        """Calculate validation points based on scoring system.

        Scoring:
        - Email signups: 3 pts each
        - DMs: 4 pts each
        - Buy comments: 3 pts each
        - Questions: 2 pts each
        - Upvotes: 1 pt per 25
        """
        return (
            self.email_signups * 3
            + self.dms * 4
            + self.buy_comments * 3
            + self.questions * 2
            + self.upvotes // 25
        )

    @property
    def passed_validation(self) -> bool:
        """Check if validation threshold (15 points) is met."""
        return self.total_points >= 15


class SignalLogEntry(BaseModel):
    """Entry for logging a new signal during organic validation."""

    signal_type: str  # dm, buy_comment, question, upvote, share, email_signup
    count: int = Field(default=1, ge=1)
    source: str | None = None  # reddit, twitter, email, etc.
    evidence_url: str | None = None
    notes: str | None = None
    logged_at: datetime = Field(default_factory=datetime.utcnow)
