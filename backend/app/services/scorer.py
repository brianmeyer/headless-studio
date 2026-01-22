"""
Opportunity Scorer Service - Calculates opportunity scores from signals.

Scoring formula (0-100):
- Demand Score (0-50): Based on mentions, engagement, trend
- Intent Score (0-40): Based on buying signals, pain points, questions
- Competition Penalty (-20 to 0): Based on existing Gumroad products

Total = Demand + Intent + Competition

Competition Scoring (from Gumroad scout):
- Saturated (8+ products OR high-rated crowded): -20 pts
- High (4-7 products): -10 pts
- Validated (1-3 products): -5 pts (ideal - proven demand!)
- None (0 products): -10 pts (unvalidated risk)
- Low Quality (<3.5 avg rating): -3 pts (opportunity to do better)
"""

import logging
import re
from typing import Any, TYPE_CHECKING

from app.models.signals import RedditSignal

if TYPE_CHECKING:
    from app.services.gumroad_scout import CompetitionData

logger = logging.getLogger(__name__)


# Price ranges by product type (in cents)
PRICE_RANGES = {
    "prompt_pack": {"min": 500, "max": 1500, "default": 900},
    "guide": {"min": 900, "max": 2900, "default": 1900},
    "template_pack": {"min": 700, "max": 1900, "default": 1200},
    "checklist": {"min": 500, "max": 1200, "default": 700},
    "roadmap": {"min": 900, "max": 2500, "default": 1500},
}

# Product type keywords for inference
PRODUCT_TYPE_KEYWORDS = {
    "prompt_pack": ["prompt", "chatgpt", "gpt", "ai prompt", "llm", "claude"],
    "guide": ["guide", "tutorial", "how to", "learn", "course", "step by step"],
    "template_pack": ["template", "notion", "spreadsheet", "worksheet", "doc"],
    "checklist": ["checklist", "framework", "process", "system", "sop", "routine"],
    "roadmap": ["roadmap", "plan", "strategy", "path", "journey", "career"],
}


class OpportunityScorer:
    """Scores signals and generates opportunity data."""

    def score_signals(
        self,
        signals: list[RedditSignal],
        primary_keyword: str | None = None,
    ) -> dict[str, Any]:
        """
        Score aggregated signals and generate opportunity data.

        Args:
            signals: List of RedditSignal objects
            primary_keyword: Optional keyword for SEO focus

        Returns:
            Dictionary with opportunity data and scores
        """
        if not signals:
            return {
                "opportunity_score": 0,
                "demand_score": 0,
                "intent_score": 0,
                "confidence": "low",
            }

        # Calculate component scores
        demand_score = self._calculate_demand_score(signals)
        intent_score = self._calculate_intent_score(signals)
        competition_penalty = self._estimate_competition_penalty(signals)

        # Total score (floor at 0, cap at 100)
        total_score = max(0, min(demand_score + intent_score + competition_penalty, 100))

        # Determine confidence based on signal quality
        confidence = self._determine_confidence(signals, total_score)

        # Infer product type
        product_type = self._infer_product_type(signals)

        # Generate title and description
        title = self._generate_title(signals, product_type)
        description = self._generate_description(signals, product_type)
        target_audience = self._identify_audience(signals)

        # Suggest price
        suggested_price = self._suggest_price(product_type, total_score)

        # Extract evidence URLs (top 5 by relevance)
        evidence_urls = [
            s.post_url for s in sorted(signals, key=lambda x: x.relevance_score, reverse=True)[:5]
        ]

        return {
            "title": title,
            "description": description,
            "target_audience": target_audience,
            "product_type": product_type,
            "opportunity_score": round(total_score, 1),
            "demand_score": round(demand_score, 1),
            "intent_score": round(intent_score, 1),
            "competition_penalty": round(competition_penalty, 1),
            "confidence": confidence,
            "primary_keyword": primary_keyword or self._extract_keyword(signals),
            "reddit_mentions": len(signals),
            "evidence_urls": evidence_urls,
            "suggested_price_cents": suggested_price,
            "signal_summary": {
                "total_signals": len(signals),
                "avg_relevance": round(sum(s.relevance_score for s in signals) / len(signals), 2),
                "total_engagement": sum(s.post_score + s.comment_count for s in signals),
                "subreddits": list(set(s.subreddit for s in signals)),
                "top_pain_points": self._aggregate_pain_points(signals),
                "top_buying_signals": self._aggregate_buying_signals(signals),
            },
        }

    def _calculate_demand_score(self, signals: list[RedditSignal]) -> float:
        """
        Calculate demand score (0-50) based on:
        - Number of signals (0-20)
        - Total engagement (0-15)
        - Subreddit diversity (0-10)
        - Recency bonus (0-5)
        """
        score = 0.0

        # Signal count (0-20)
        signal_count = len(signals)
        if signal_count >= 20:
            score += 20
        elif signal_count >= 10:
            score += 15
        elif signal_count >= 5:
            score += 10
        elif signal_count >= 2:
            score += 5

        # Total engagement (0-15)
        total_engagement = sum(s.post_score + (s.comment_count * 2) for s in signals)
        if total_engagement >= 1000:
            score += 15
        elif total_engagement >= 500:
            score += 12
        elif total_engagement >= 200:
            score += 9
        elif total_engagement >= 50:
            score += 5

        # Subreddit diversity (0-10)
        unique_subreddits = len(set(s.subreddit for s in signals))
        if unique_subreddits >= 5:
            score += 10
        elif unique_subreddits >= 3:
            score += 7
        elif unique_subreddits >= 2:
            score += 4

        # Average relevance bonus (0-5)
        avg_relevance = sum(s.relevance_score for s in signals) / len(signals)
        score += avg_relevance * 5

        return min(score, 50)

    def _calculate_intent_score(self, signals: list[RedditSignal]) -> float:
        """
        Calculate intent score (0-40) based on:
        - Buying signals (0-20)
        - Pain points (0-12)
        - Questions (0-8)
        """
        score = 0.0

        # Count buying signals
        total_buying = sum(len(s.buying_signals) for s in signals)
        if total_buying >= 15:
            score += 20
        elif total_buying >= 10:
            score += 16
        elif total_buying >= 5:
            score += 12
        elif total_buying >= 2:
            score += 6

        # Count pain points
        total_pain = sum(len(s.pain_points) for s in signals)
        if total_pain >= 10:
            score += 12
        elif total_pain >= 5:
            score += 9
        elif total_pain >= 2:
            score += 5

        # Count questions
        total_questions = sum(len(s.questions) for s in signals)
        if total_questions >= 10:
            score += 8
        elif total_questions >= 5:
            score += 6
        elif total_questions >= 2:
            score += 3

        return min(score, 40)

    def _estimate_competition_penalty(
        self,
        signals: list[RedditSignal],
        competition_data: "CompetitionData | None" = None,
    ) -> float:
        """
        Calculate competition penalty (-20 to 0).

        Uses Gumroad competition data if provided, otherwise defaults to -5.

        Args:
            signals: Reddit signals (for context)
            competition_data: Pre-fetched Gumroad competition data

        Returns:
            Penalty score from -20 (saturated) to -3 (opportunity)
        """
        if competition_data is not None:
            # Use real Gumroad data
            logger.debug(
                f"Competition: {competition_data.competition_level} "
                f"({competition_data.product_count} products) → {competition_data.competition_penalty}"
            )
            return competition_data.competition_penalty

        # Default: assume medium competition
        return -5

    def _determine_confidence(
        self,
        signals: list[RedditSignal],
        total_score: float,
    ) -> str:
        """Determine confidence level based on signal quality."""
        if len(signals) >= 10 and total_score >= 70:
            return "high"
        elif len(signals) >= 5 and total_score >= 50:
            return "medium"
        else:
            return "low"

    def _infer_product_type(self, signals: list[RedditSignal]) -> str:
        """Infer best product type from signals."""
        type_scores: dict[str, int] = {k: 0 for k in PRODUCT_TYPE_KEYWORDS}

        for signal in signals:
            text = f"{signal.post_title} {' '.join(signal.questions)}".lower()
            for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[product_type] += 1

        best_type = max(type_scores, key=type_scores.get)
        return best_type if type_scores[best_type] > 0 else "guide"

    def _generate_title(self, signals: list[RedditSignal], product_type: str) -> str:
        """Generate a product title from signals."""
        # Extract common themes from post titles
        words: dict[str, int] = {}
        stop_words = {
            "the", "a", "an", "is", "are", "for", "to", "of", "and", "or",
            "in", "on", "at", "by", "with", "how", "what", "why", "when",
            "i", "you", "my", "your", "this", "that", "it", "do", "does",
        }

        for signal in signals:
            for word in re.findall(r'\b[a-zA-Z]+\b', signal.post_title.lower()):
                if word not in stop_words and len(word) > 3:
                    words[word] = words.get(word, 0) + 1

        # Get top words
        top_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:3]
        topic = " ".join(w[0].title() for w in top_words) if top_words else "Digital Product"

        # Format based on product type
        type_formats = {
            "prompt_pack": f"{topic} Prompt Pack",
            "guide": f"The Complete {topic} Guide",
            "template_pack": f"{topic} Template Bundle",
            "checklist": f"{topic} Checklist & Framework",
            "roadmap": f"{topic} Roadmap",
        }

        return type_formats.get(product_type, f"{topic} Resource Pack")

    def _generate_description(self, signals: list[RedditSignal], product_type: str) -> str:
        """Generate a brief description from signals."""
        pain_points = self._aggregate_pain_points(signals)
        if pain_points:
            return f"Helps with: {', '.join(pain_points[:3])}"
        return f"A comprehensive {product_type.replace('_', ' ')} based on real user needs."

    def _identify_audience(self, signals: list[RedditSignal]) -> str:
        """Identify target audience from subreddits."""
        subreddits = [s.subreddit for s in signals]

        # Map subreddits to audience types
        audience_map = {
            "Entrepreneur": "entrepreneurs",
            "smallbusiness": "small business owners",
            "startups": "startup founders",
            "freelance": "freelancers",
            "productivity": "productivity enthusiasts",
            "ChatGPT": "AI users",
            "OpenAI": "AI enthusiasts",
            "learnprogramming": "developers",
            "personalfinance": "personal finance enthusiasts",
            "careerguidance": "career changers",
        }

        audiences = []
        for sub in set(subreddits):
            if sub in audience_map:
                audiences.append(audience_map[sub])

        return ", ".join(audiences[:3]) if audiences else "digital product buyers"

    def _suggest_price(self, product_type: str, score: float) -> int:
        """Suggest price based on product type and score."""
        price_range = PRICE_RANGES.get(product_type, PRICE_RANGES["guide"])

        # Higher score = can charge more
        if score >= 80:
            return price_range["max"]
        elif score >= 60:
            return int((price_range["max"] + price_range["default"]) / 2)
        elif score >= 40:
            return price_range["default"]
        else:
            return price_range["min"]

    def _extract_keyword(self, signals: list[RedditSignal]) -> str:
        """Extract primary keyword from signals."""
        words: dict[str, int] = {}
        stop_words = {
            "the", "a", "an", "is", "are", "for", "to", "of", "and", "or",
            "in", "on", "at", "by", "with", "i", "you", "my", "your",
        }

        for signal in signals:
            for word in re.findall(r'\b[a-zA-Z]+\b', signal.post_title.lower()):
                if word not in stop_words and len(word) > 3:
                    words[word] = words.get(word, 0) + 1

        if words:
            top_word = max(words.items(), key=lambda x: x[1])[0]
            return top_word

        return "digital product"

    def _aggregate_pain_points(self, signals: list[RedditSignal]) -> list[str]:
        """Aggregate and deduplicate pain points."""
        pain_points: dict[str, int] = {}
        for signal in signals:
            for pp in signal.pain_points:
                pain_points[pp] = pain_points.get(pp, 0) + 1

        sorted_pp = sorted(pain_points.items(), key=lambda x: x[1], reverse=True)
        return [pp[0] for pp in sorted_pp[:5]]

    def _aggregate_buying_signals(self, signals: list[RedditSignal]) -> list[str]:
        """Aggregate and deduplicate buying signals."""
        buying: dict[str, int] = {}
        for signal in signals:
            for bs in signal.buying_signals:
                buying[bs] = buying.get(bs, 0) + 1

        sorted_bs = sorted(buying.items(), key=lambda x: x[1], reverse=True)
        return [bs[0] for bs in sorted_bs[:5]]

    def score_unified_signals(
        self,
        x_signals: list | None = None,
        reddit_signals: list[RedditSignal] | None = None,
        trend_score: int = 0,
        primary_keyword: str | None = None,
        competition_data: "CompetitionData | None" = None,
    ) -> dict[str, Any]:
        """
        Score unified signals from X/Grok (primary), Reddit, and Trends.

        Scoring weights:
        - X signals: PRIMARY (0-30 demand, 0-25 intent)
        - Reddit signals: SUPPLEMENTARY (0-10 demand, 0-10 intent)
        - Trends: SUPPLEMENTARY (0-10 demand)
        - Competition penalty: -20 to 0 (from Gumroad data)

        Args:
            x_signals: List of XSignal objects from X/Grok scout
            reddit_signals: List of RedditSignal objects
            trend_score: Google Trends interest score (0-100)
            primary_keyword: Main keyword for the opportunity
            competition_data: Pre-fetched Gumroad competition data

        Returns:
            Dictionary with opportunity data and scores
        """
        x_signals = x_signals or []
        reddit_signals = reddit_signals or []

        if not x_signals and not reddit_signals:
            return {
                "title": primary_keyword or "Unknown Opportunity",
                "description": "No signals found",
                "target_audience": "unknown",
                "product_type": "guide",
                "opportunity_score": 0,
                "demand_score": 0,
                "intent_score": 0,
                "competition_penalty": 0,
                "confidence": "low",
                "primary_keyword": primary_keyword or "unknown",
                "suggested_price_cents": 900,
                "evidence_urls": [],
                "signal_summary": {
                    "total_signals": 0,
                    "avg_relevance": 0,
                    "total_engagement": 0,
                    "subreddits": [],
                    "top_pain_points": [],
                    "top_buying_signals": [],
                },
            }

        # === Calculate Demand Score (0-50) ===
        demand_score = 0.0

        # X signals demand (PRIMARY - up to 30 points)
        if x_signals:
            x_count = len(x_signals)
            if x_count >= 20:
                demand_score += 30
            elif x_count >= 10:
                demand_score += 22
            elif x_count >= 5:
                demand_score += 15
            elif x_count >= 2:
                demand_score += 8

        # Reddit signals demand (SUPPLEMENTARY - up to 10 points)
        if reddit_signals:
            reddit_count = len(reddit_signals)
            total_engagement = sum(s.post_score + (s.comment_count * 2) for s in reddit_signals)
            if reddit_count >= 10 and total_engagement >= 500:
                demand_score += 10
            elif reddit_count >= 5 and total_engagement >= 200:
                demand_score += 7
            elif reddit_count >= 2:
                demand_score += 4

        # Trends demand (SUPPLEMENTARY - up to 10 points)
        if trend_score >= 70:
            demand_score += 10
        elif trend_score >= 50:
            demand_score += 7
        elif trend_score >= 30:
            demand_score += 4

        demand_score = min(demand_score, 50)

        # === Calculate Intent Score (0-40) ===
        intent_score = 0.0

        # X signal intent (PRIMARY - up to 25 points)
        if x_signals:
            # Count pain points and buying signals from X
            x_pain_points = 0
            x_buying = 0
            for sig in x_signals:
                if hasattr(sig, 'pain_points'):
                    x_pain_points += len(sig.pain_points)
                if hasattr(sig, 'buying_signals'):
                    x_buying += len(sig.buying_signals)
                if hasattr(sig, 'signal_type'):
                    if sig.signal_type in ('frustration', 'pain_point'):
                        x_pain_points += 1
                    elif sig.signal_type in ('request', 'question', 'buying_signal'):
                        x_buying += 1

            # X buying signals (up to 15)
            if x_buying >= 10:
                intent_score += 15
            elif x_buying >= 5:
                intent_score += 10
            elif x_buying >= 2:
                intent_score += 5

            # X pain points (up to 10)
            if x_pain_points >= 10:
                intent_score += 10
            elif x_pain_points >= 5:
                intent_score += 7
            elif x_pain_points >= 2:
                intent_score += 4

        # Reddit signal intent (SUPPLEMENTARY - up to 10 points)
        if reddit_signals:
            reddit_buying = sum(len(s.buying_signals) for s in reddit_signals)
            reddit_pain = sum(len(s.pain_points) for s in reddit_signals)

            if reddit_buying >= 5:
                intent_score += 5
            elif reddit_buying >= 2:
                intent_score += 3

            if reddit_pain >= 5:
                intent_score += 5
            elif reddit_pain >= 2:
                intent_score += 3

        intent_score = min(intent_score, 40)

        # === Competition Penalty (-20 to 0) ===
        if competition_data is not None:
            competition_penalty = competition_data.competition_penalty
            logger.info(
                f"Competition for '{primary_keyword}': {competition_data.competition_level} "
                f"({competition_data.product_count} products) → {competition_penalty} pts"
            )
        else:
            competition_penalty = -5  # Default medium competition

        # === Total Score (floor at 0, cap at 100) ===
        total_score = max(0, min(demand_score + intent_score + competition_penalty, 100))

        # === Determine Confidence ===
        total_signals = len(x_signals) + len(reddit_signals)
        if total_signals >= 15 and total_score >= 70:
            confidence = "high"
        elif total_signals >= 7 and total_score >= 50:
            confidence = "medium"
        else:
            confidence = "low"

        # === Infer Product Type ===
        product_type = self._infer_product_type_unified(x_signals, reddit_signals)

        # === Generate Title and Description ===
        title = self._generate_title_unified(x_signals, reddit_signals, product_type, primary_keyword)
        description = self._generate_description_unified(x_signals, reddit_signals)
        target_audience = self._identify_audience_unified(x_signals, reddit_signals)

        # === Suggest Price ===
        suggested_price = self._suggest_price(product_type, total_score)

        # === Extract Evidence URLs ===
        evidence_urls = []
        for sig in x_signals[:5]:
            if hasattr(sig, 'url') and sig.url:
                evidence_urls.append(sig.url)
        for sig in reddit_signals[:3]:
            if hasattr(sig, 'post_url') and sig.post_url:
                evidence_urls.append(sig.post_url)

        # === Aggregate Pain Points and Buying Signals ===
        all_pain_points = []
        all_buying_signals = []
        for sig in x_signals:
            if hasattr(sig, 'pain_points'):
                all_pain_points.extend(sig.pain_points)
        for sig in reddit_signals:
            all_pain_points.extend(sig.pain_points)
            all_buying_signals.extend(sig.buying_signals)

        # Deduplicate
        pain_counts: dict[str, int] = {}
        for pp in all_pain_points:
            pain_counts[pp] = pain_counts.get(pp, 0) + 1
        top_pain_points = sorted(pain_counts.keys(), key=lambda x: pain_counts[x], reverse=True)[:5]

        buying_counts: dict[str, int] = {}
        for bs in all_buying_signals:
            buying_counts[bs] = buying_counts.get(bs, 0) + 1
        top_buying_signals = sorted(buying_counts.keys(), key=lambda x: buying_counts[x], reverse=True)[:5]

        return {
            "title": title,
            "description": description,
            "target_audience": target_audience,
            "product_type": product_type,
            "opportunity_score": round(total_score, 1),
            "demand_score": round(demand_score, 1),
            "intent_score": round(intent_score, 1),
            "competition_penalty": round(competition_penalty, 1),
            "confidence": confidence,
            "primary_keyword": primary_keyword or self._extract_keyword(reddit_signals) if reddit_signals else "digital product",
            "x_mentions": len(x_signals),
            "reddit_mentions": len(reddit_signals),
            "evidence_urls": evidence_urls,
            "suggested_price_cents": suggested_price,
            "signal_summary": {
                "total_signals": total_signals,
                "avg_relevance": round(sum(s.relevance_score for s in reddit_signals) / len(reddit_signals), 2) if reddit_signals else 0,
                "total_engagement": sum(s.post_score + s.comment_count for s in reddit_signals) if reddit_signals else 0,
                "subreddits": list(set(s.subreddit for s in reddit_signals)) if reddit_signals else [],
                "top_pain_points": top_pain_points,
                "top_buying_signals": top_buying_signals,
            },
        }

    def _infer_product_type_unified(self, x_signals: list, reddit_signals: list[RedditSignal]) -> str:
        """Infer product type from unified signals."""
        type_scores: dict[str, int] = {k: 0 for k in PRODUCT_TYPE_KEYWORDS}

        # Score from X signals
        for sig in x_signals:
            text = sig.text.lower() if hasattr(sig, 'text') else ""
            for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[product_type] += 2  # X signals weighted higher

        # Score from Reddit signals
        for signal in reddit_signals:
            text = f"{signal.post_title} {' '.join(signal.questions)}".lower()
            for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[product_type] += 1

        best_type = max(type_scores, key=type_scores.get)
        return best_type if type_scores[best_type] > 0 else "guide"

    def _generate_title_unified(
        self,
        x_signals: list,
        reddit_signals: list[RedditSignal],
        product_type: str,
        primary_keyword: str | None,
    ) -> str:
        """Generate title from unified signals."""
        words: dict[str, int] = {}
        stop_words = {
            "the", "a", "an", "is", "are", "for", "to", "of", "and", "or",
            "in", "on", "at", "by", "with", "how", "what", "why", "when",
            "i", "you", "my", "your", "this", "that", "it", "do", "does",
        }

        # Extract from X signals
        for sig in x_signals:
            text = sig.text if hasattr(sig, 'text') else ""
            for word in re.findall(r'\b[a-zA-Z]+\b', text.lower()):
                if word not in stop_words and len(word) > 3:
                    words[word] = words.get(word, 0) + 2

        # Extract from Reddit signals
        for signal in reddit_signals:
            for word in re.findall(r'\b[a-zA-Z]+\b', signal.post_title.lower()):
                if word not in stop_words and len(word) > 3:
                    words[word] = words.get(word, 0) + 1

        # Use primary keyword if provided, else top words
        if primary_keyword:
            topic = primary_keyword.title()
        else:
            top_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:3]
            topic = " ".join(w[0].title() for w in top_words) if top_words else "Digital Product"

        type_formats = {
            "prompt_pack": f"{topic} Prompt Pack",
            "guide": f"The Complete {topic} Guide",
            "template_pack": f"{topic} Template Bundle",
            "checklist": f"{topic} Checklist & Framework",
            "roadmap": f"{topic} Roadmap",
        }

        return type_formats.get(product_type, f"{topic} Resource Pack")

    def _generate_description_unified(self, x_signals: list, reddit_signals: list[RedditSignal]) -> str:
        """Generate description from unified signals."""
        pain_points = []
        for sig in x_signals:
            if hasattr(sig, 'pain_points'):
                pain_points.extend(sig.pain_points)
        for sig in reddit_signals:
            pain_points.extend(sig.pain_points)

        if pain_points:
            unique_pain = list(set(pain_points))[:3]
            return f"Helps with: {', '.join(unique_pain)}"
        return "A comprehensive resource based on real user needs."

    def _identify_audience_unified(self, x_signals: list, reddit_signals: list[RedditSignal]) -> str:
        """Identify target audience from unified signals."""
        # From Reddit subreddits
        subreddits = [s.subreddit for s in reddit_signals]
        audience_map = {
            "Entrepreneur": "entrepreneurs",
            "smallbusiness": "small business owners",
            "freelance": "freelancers",
            "ChatGPT": "AI users",
            "productivity": "productivity enthusiasts",
            "personalfinance": "personal finance enthusiasts",
        }

        audiences = []
        for sub in set(subreddits):
            if sub in audience_map:
                audiences.append(audience_map[sub])

        # If no Reddit, infer from X
        if not audiences and x_signals:
            return "professionals seeking productivity tools"

        return ", ".join(audiences[:3]) if audiences else "digital product buyers"
