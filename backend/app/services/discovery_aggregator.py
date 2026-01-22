"""
Discovery Aggregator - Orchestrates all discovery sources and produces unified opportunities.

This is the main discovery service that:
1. Searches X/Twitter via Grok (PRIMARY)
2. Searches Reddit (when API available)
3. Gets Google Trends data (supplementary)
4. Scores and ranks opportunities
5. Checks for duplicates
6. Returns top opportunities for Gate 1 review

TARGET CUSTOMER PROFILE:
All discovery is optimized to find opportunities for NON-TECHNICAL professionals
who would PAY $15-30 for ready-made digital products rather than create their own.

Examples of ideal target audiences:
- Real estate agents wanting ChatGPT help with listings
- Small business owners needing social media templates
- Teachers looking for lesson planning resources
- Freelancers wanting client proposal templates
- Content creators needing workflow systems
- Coaches wanting client onboarding checklists
- HR managers, sales reps, consultants, therapists, fitness trainers

NOT our target: developers, programmers, AI researchers, tech enthusiasts
(they would build their own solutions rather than pay for them).
"""

import logging
from datetime import datetime, timedelta
from typing import Any

from pydantic import BaseModel, Field

from app.config import Settings
from app.models.signals import RedditSignal
from app.services.x_scout import XGrokScout, XSignal
from app.services.reddit_scout import RedditScout
from app.services.trends_scout import TrendsScout
from app.services.gumroad_scout import GumroadCompetitionScout, CompetitionData
from app.services.scorer import OpportunityScorer
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class DiscoveryConfig(BaseModel):
    """Configuration for a discovery run."""

    topics: list[str] = Field(
        default_factory=lambda: ["chatgpt prompts", "ai tools", "productivity"],
        description="Topics to search for opportunities"
    )
    time_filter: str = Field(
        default="week",
        description="Time range: day, week, month"
    )
    min_score: int = Field(
        default=50,
        description="Minimum opportunity score to surface (0-100)"
    )
    max_opportunities: int = Field(
        default=10,
        description="Maximum opportunities to return"
    )
    check_duplicates: bool = Field(
        default=True,
        description="Check for duplicate/similar opportunities"
    )
    duplicate_lookback_days: int = Field(
        default=90,
        description="Days to look back for duplicates"
    )
    use_trends: bool = Field(
        default=True,
        description="Whether to fetch Google Trends data (can be slow/unreliable)"
    )


class DiscoveredOpportunity(BaseModel):
    """A discovered and scored opportunity."""

    title: str
    description: str
    target_audience: str
    product_type: str

    # Scores
    opportunity_score: float
    demand_score: float
    intent_score: float
    competition_penalty: float
    confidence: str

    # SEO
    primary_keyword: str
    suggested_price_cents: int

    # Signal sources
    x_mentions: int = 0
    reddit_mentions: int = 0
    trend_score: int = 0

    # Evidence
    evidence_urls: list[str] = Field(default_factory=list)
    top_pain_points: list[str] = Field(default_factory=list)
    top_buying_signals: list[str] = Field(default_factory=list)

    # Raw signals for storage
    x_signals: list[dict[str, Any]] = Field(default_factory=list)
    reddit_signals: list[dict[str, Any]] = Field(default_factory=list)


class DiscoveryResult(BaseModel):
    """Result of a discovery run."""

    success: bool
    run_at: datetime = Field(default_factory=datetime.utcnow)
    topics_searched: list[str]
    opportunities: list[DiscoveredOpportunity]
    total_x_signals: int = 0
    total_reddit_signals: int = 0
    duplicates_filtered: int = 0
    below_threshold_filtered: int = 0
    errors: list[str] = Field(default_factory=list)


class DiscoveryAggregator:
    """
    Main discovery service that orchestrates all signal sources.

    Flow:
    1. Search X/Twitter via Grok (primary)
    2. Search Reddit (if API available)
    3. Optionally enrich with Google Trends
    4. Score all signals together
    5. Filter duplicates
    6. Return top opportunities
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.x_scout = XGrokScout(settings)
        self.reddit_scout = RedditScout()  # Uses get_settings() internally
        self.trends_scout = TrendsScout()
        self.gumroad_scout = GumroadCompetitionScout()
        self.scorer = OpportunityScorer()

    async def run_discovery(
        self,
        config: DiscoveryConfig | None = None,
    ) -> DiscoveryResult:
        """
        Run a full discovery pass.

        This is the main entry point for the weekly discovery workflow.

        Args:
            config: Discovery configuration (uses defaults if not provided)

        Returns:
            DiscoveryResult with scored and filtered opportunities
        """
        config = config or DiscoveryConfig()
        errors: list[str] = []
        all_x_signals: list[XSignal] = []
        all_reddit_signals: list[RedditSignal] = []

        # === 1. Search X/Twitter via Grok (PRIMARY) ===
        if self.x_scout.is_configured:
            try:
                logger.info(f"Searching X for topics: {config.topics}")
                x_signals = await self.x_scout.search_x(
                    topics=config.topics,
                    time_filter=config.time_filter,
                    limit=300,  # Gather plenty for filtering
                )
                all_x_signals = x_signals
                logger.info(f"Found {len(x_signals)} X signals")
            except Exception as e:
                logger.exception("X/Grok search failed")
                errors.append(f"X search error: {str(e)}")
        else:
            logger.warning("X/Grok scout not configured - skipping")
            errors.append("X/Grok not configured (XAI_API_KEY missing)")

        # === 2. Search Reddit (SUPPLEMENTARY - when available) ===
        if self.reddit_scout.is_configured:
            try:
                logger.info(f"Searching Reddit for topics: {config.topics}")
                for topic in config.topics[:3]:  # Limit API calls
                    signals = await self.reddit_scout.search_subreddits(
                        query=topic,
                        time_filter=config.time_filter,
                        limit=25,
                    )
                    all_reddit_signals.extend(signals)
                logger.info(f"Found {len(all_reddit_signals)} Reddit signals")
            except Exception as e:
                logger.warning(f"Reddit search failed (API may not be approved): {e}")
                errors.append(f"Reddit search skipped: {str(e)}")
        else:
            logger.info("Reddit scout not configured - skipping (API not approved)")

        # === 3. Cluster signals by topic/theme ===
        # For now, we treat all signals as one opportunity per topic
        # Future: use LLM clustering to identify distinct opportunities
        opportunities: list[DiscoveredOpportunity] = []

        for topic in config.topics:
            # Filter signals relevant to this topic
            # For X signals: use all signals since they came from topic-specific searches
            # In the future, use LLM to cluster by distinct product opportunities
            topic_keywords = [kw.lower() for kw in topic.split() if len(kw) > 2]
            topic_x_signals = [
                s for s in all_x_signals
                if any(kw in s.text.lower() for kw in topic_keywords)
            ]

            # If no keyword matches, use all signals (they came from this topic's search)
            if not topic_x_signals:
                topic_x_signals = all_x_signals

            topic_reddit_signals = [
                s for s in all_reddit_signals
                if topic.lower() in s.post_title.lower() or any(
                    kw in s.post_title.lower() for kw in topic_keywords
                )
            ]

            if not topic_x_signals and not topic_reddit_signals:
                continue

            # === 4. Get trend data for the topic (OPTIONAL - fails gracefully) ===
            trend_score = 0
            if config.use_trends and self.trends_scout.is_available:
                try:
                    # Only fetch interest score (1 API call), skip related queries
                    trend_data = self.trends_scout.analyze_keyword(topic, full_analysis=False)
                    trend_score = trend_data.interest_score
                    if trend_score > 0:
                        logger.info(f"Trends score for '{topic}': {trend_score}")
                except Exception as e:
                    # Trends failing should NEVER block discovery
                    logger.warning(f"Trends lookup failed for {topic} (non-blocking): {e}")

            # === 4.5. Get Gumroad competition data ===
            competition_data: CompetitionData | None = None
            try:
                competition_data = await self.gumroad_scout.search_competitors(topic)
                logger.info(
                    f"Gumroad competition for '{topic}': {competition_data.competition_level} "
                    f"({competition_data.product_count} products)"
                )
            except Exception as e:
                logger.warning(f"Gumroad lookup failed for {topic} (non-blocking): {e}")

            # === 5. Score the signals ===
            score_result = self.scorer.score_unified_signals(
                x_signals=topic_x_signals,
                reddit_signals=topic_reddit_signals,
                trend_score=trend_score,
                primary_keyword=topic,
                competition_data=competition_data,
            )

            # Create opportunity object
            opportunity = DiscoveredOpportunity(
                title=score_result["title"],
                description=score_result["description"],
                target_audience=score_result["target_audience"],
                product_type=score_result["product_type"],
                opportunity_score=score_result["opportunity_score"],
                demand_score=score_result["demand_score"],
                intent_score=score_result["intent_score"],
                competition_penalty=score_result["competition_penalty"],
                confidence=score_result["confidence"],
                primary_keyword=score_result["primary_keyword"],
                suggested_price_cents=score_result["suggested_price_cents"],
                x_mentions=len(topic_x_signals),
                reddit_mentions=len(topic_reddit_signals),
                trend_score=trend_score,
                evidence_urls=score_result["evidence_urls"],
                top_pain_points=score_result["signal_summary"]["top_pain_points"],
                top_buying_signals=score_result["signal_summary"]["top_buying_signals"],
                x_signals=[s.model_dump() for s in topic_x_signals[:20]],  # Store top 20
                reddit_signals=[s.model_dump() for s in topic_reddit_signals[:10]],
            )

            opportunities.append(opportunity)

        # === 6. Filter by minimum score ===
        below_threshold = len([o for o in opportunities if o.opportunity_score < config.min_score])
        opportunities = [o for o in opportunities if o.opportunity_score >= config.min_score]

        # === 7. Check for duplicates ===
        duplicates_filtered = 0
        if config.check_duplicates:
            filtered_opportunities = []
            for opp in opportunities:
                is_dup = await self._is_duplicate(
                    opp.primary_keyword,
                    opp.title,
                    config.duplicate_lookback_days,
                )
                if is_dup:
                    duplicates_filtered += 1
                    logger.info(f"Filtered duplicate: {opp.title}")
                else:
                    filtered_opportunities.append(opp)
            opportunities = filtered_opportunities

        # === 8. Sort by score and limit ===
        opportunities.sort(key=lambda o: o.opportunity_score, reverse=True)
        opportunities = opportunities[:config.max_opportunities]

        return DiscoveryResult(
            success=len(opportunities) > 0 or len(errors) == 0,
            topics_searched=config.topics,
            opportunities=opportunities,
            total_x_signals=len(all_x_signals),
            total_reddit_signals=len(all_reddit_signals),
            duplicates_filtered=duplicates_filtered,
            below_threshold_filtered=below_threshold,
            errors=errors,
        )

    async def _is_duplicate(
        self,
        keyword: str,
        title: str,
        lookback_days: int,
    ) -> bool:
        """
        Check if an opportunity is a duplicate of a recent one.

        Checks:
        1. Exact keyword match in last N days
        2. Similar title in last N days
        3. Match to published product (forever)
        """
        try:
            client = get_supabase_client()
            cutoff = datetime.utcnow() - timedelta(days=lookback_days)
            cutoff_str = cutoff.isoformat()

            # Check recent opportunities with same keyword
            result = (
                client.table("opportunities")
                .select("id, primary_keyword, title")
                .eq("primary_keyword", keyword.lower())
                .gte("created_at", cutoff_str)
                .execute()
            )

            if result.data:
                return True

            # Check published products (forever)
            product_result = (
                client.table("products")
                .select("id, title")
                .ilike("title", f"%{keyword}%")
                .execute()
            )

            if product_result.data:
                return True

            return False

        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False  # Don't block on errors

    async def quick_search(
        self,
        topic: str,
        time_filter: str = "week",
    ) -> dict[str, Any]:
        """
        Quick search for a single topic (for testing/exploration).

        Args:
            topic: Topic to search
            time_filter: Time range

        Returns:
            Dictionary with signals and scoring
        """
        x_signals: list[XSignal] = []
        reddit_signals: list[RedditSignal] = []

        # Search X
        if self.x_scout.is_configured:
            x_signals = await self.x_scout.search_x(
                topics=[topic],
                time_filter=time_filter,
                limit=50,
            )

        # Search Reddit
        if self.reddit_scout.is_configured:
            reddit_signals = await self.reddit_scout.search_subreddits(
                query=topic,
                time_filter=time_filter,
                limit=25,
            )

        # Get trend (optional, fails gracefully)
        trend_score = 0
        if self.trends_scout.is_available:
            try:
                trend_data = self.trends_scout.analyze_keyword(topic, full_analysis=False)
                trend_score = trend_data.interest_score
            except Exception as e:
                logger.debug(f"Trends unavailable for quick_search: {e}")

        # Score
        score_result = self.scorer.score_unified_signals(
            x_signals=x_signals,
            reddit_signals=reddit_signals,
            trend_score=trend_score,
            primary_keyword=topic,
        )

        return {
            "topic": topic,
            "x_signals": len(x_signals),
            "reddit_signals": len(reddit_signals),
            "trend_score": trend_score,
            "scoring": score_result,
            "sample_x_signals": [s.model_dump() for s in x_signals[:5]],
            "sample_reddit_signals": [s.model_dump() for s in reddit_signals[:5]],
        }
