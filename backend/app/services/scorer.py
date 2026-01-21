"""
Opportunity Scorer Service - Calculates opportunity scores from signals.

Scoring formula (0-100):
- Demand Score (0-50): Based on mentions, engagement, trend
- Intent Score (0-40): Based on buying signals, pain points, questions
- Competition Penalty (-20 to 0): Based on existing products

Total = Demand + Intent + Competition
"""

import logging
import re
from typing import Any

from app.models.signals import RedditSignal

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

        # Total score (capped at 100)
        total_score = min(demand_score + intent_score + competition_penalty, 100)

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

    def _estimate_competition_penalty(self, signals: list[RedditSignal]) -> float:
        """
        Estimate competition penalty (-20 to 0).

        For now, uses heuristics. In production, would check:
        - Gumroad search results
        - Existing products in database
        - Google search results
        """
        # Default: assume medium competition
        # Negative penalty reduces score
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
