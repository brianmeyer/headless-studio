"""
Reddit Scout Service - Discovers product opportunities from Reddit.

Searches subreddits for pain points, buying signals, and product demand.
Uses PRAW (Python Reddit API Wrapper) for Reddit API access.
"""

import logging
import re
from datetime import datetime, timezone
from typing import Any

import praw
from praw.models import Submission

from app.config import get_settings
from app.models.signals import RedditSignal

logger = logging.getLogger(__name__)


# Subreddits to scan for digital product opportunities
DEFAULT_SUBREDDITS = [
    # Productivity & Business
    "Entrepreneur",
    "smallbusiness",
    "startups",
    "SideProject",
    "productivity",
    "freelance",
    # AI & Tech
    "ChatGPT",
    "artificial",
    "OpenAI",
    "LocalLLaMA",
    "MachineLearning",
    "learnprogramming",
    # Content Creation
    "content_marketing",
    "socialmedia",
    "copywriting",
    "blogging",
    # Learning & Self-Improvement
    "getdisciplined",
    "selfimprovement",
    "DecidingToBeBetter",
    "LifeProTips",
    # Finance & Career
    "personalfinance",
    "careerguidance",
    "jobs",
    "remotework",
    # Specific Niches (high intent)
    "NotionTemplates",
    "ObsidianMD",
    "Notion",
]

# Keywords that signal buying intent
BUYING_SIGNALS = [
    "looking for",
    "need help with",
    "anyone know",
    "recommendation",
    "suggest",
    "best way to",
    "how do i",
    "where can i find",
    "does anyone have",
    "willing to pay",
    "budget",
    "worth buying",
    "is there a",
    "template for",
    "guide for",
    "resource for",
    "tool for",
    "prompt for",
    "checklist for",
]

# Keywords indicating pain points
PAIN_POINT_SIGNALS = [
    "struggling with",
    "frustrated",
    "can't figure out",
    "wasting time",
    "taking forever",
    "so hard to",
    "impossible to",
    "hate having to",
    "wish there was",
    "if only",
    "pain point",
    "biggest challenge",
    "stuck on",
    "overwhelmed by",
]

# Product type mapping based on keywords
PRODUCT_TYPE_KEYWORDS = {
    "prompt_pack": ["prompt", "chatgpt", "gpt", "ai prompt", "llm"],
    "guide": ["guide", "tutorial", "how to", "learn", "course", "roadmap"],
    "template_pack": ["template", "notion", "spreadsheet", "worksheet"],
    "checklist": ["checklist", "framework", "process", "system", "sop"],
    "roadmap": ["roadmap", "plan", "strategy", "path", "journey"],
}


class RedditScout:
    """Scout service for discovering opportunities from Reddit."""

    def __init__(self):
        """Initialize Reddit client with credentials."""
        settings = get_settings()
        self.reddit = praw.Reddit(
            client_id=settings.reddit_client_id,
            client_secret=settings.reddit_client_secret,
            user_agent=settings.reddit_user_agent,
        )
        self.max_results = settings.max_opportunities_per_run

    def search_subreddits(
        self,
        subreddits: list[str] | None = None,
        query: str | None = None,
        time_filter: str = "week",
        limit_per_subreddit: int = 25,
    ) -> list[RedditSignal]:
        """
        Search multiple subreddits for relevant posts.

        Args:
            subreddits: List of subreddit names to search (defaults to curated list)
            query: Optional search query to filter posts
            time_filter: Time filter for posts (hour, day, week, month, year, all)
            limit_per_subreddit: Max posts to fetch per subreddit

        Returns:
            List of RedditSignal objects with extracted signals
        """
        subreddits = subreddits or DEFAULT_SUBREDDITS
        signals: list[RedditSignal] = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                if query:
                    # Search with specific query
                    posts = subreddit.search(
                        query,
                        time_filter=time_filter,
                        limit=limit_per_subreddit,
                    )
                else:
                    # Get hot posts
                    posts = subreddit.hot(limit=limit_per_subreddit)

                for post in posts:
                    signal = self._extract_signal(post, subreddit_name)
                    if signal and signal.relevance_score > 0.3:
                        signals.append(signal)

            except Exception as e:
                logger.warning(f"Error scanning r/{subreddit_name}: {e}")
                continue

        # Sort by relevance and limit results
        signals.sort(key=lambda s: s.relevance_score, reverse=True)
        return signals[: self.max_results * 3]  # Return 3x to allow for dedup

    def search_by_keywords(
        self,
        keywords: list[str],
        subreddits: list[str] | None = None,
        time_filter: str = "week",
    ) -> list[RedditSignal]:
        """
        Search for specific keywords across subreddits.

        Args:
            keywords: List of keywords to search for
            subreddits: Optional list of subreddits (defaults to all of Reddit)
            time_filter: Time filter for posts

        Returns:
            List of RedditSignal objects
        """
        signals: list[RedditSignal] = []

        for keyword in keywords:
            try:
                if subreddits:
                    # Search specific subreddits
                    for sub_name in subreddits:
                        subreddit = self.reddit.subreddit(sub_name)
                        posts = subreddit.search(
                            keyword,
                            time_filter=time_filter,
                            limit=10,
                        )
                        for post in posts:
                            signal = self._extract_signal(post, sub_name)
                            if signal:
                                signals.append(signal)
                else:
                    # Search all of Reddit
                    posts = self.reddit.subreddit("all").search(
                        keyword,
                        time_filter=time_filter,
                        limit=25,
                    )
                    for post in posts:
                        signal = self._extract_signal(post, post.subreddit.display_name)
                        if signal:
                            signals.append(signal)

            except Exception as e:
                logger.warning(f"Error searching for '{keyword}': {e}")
                continue

        # Deduplicate by post_id
        seen_ids = set()
        unique_signals = []
        for signal in signals:
            if signal.post_id not in seen_ids:
                seen_ids.add(signal.post_id)
                unique_signals.append(signal)

        unique_signals.sort(key=lambda s: s.relevance_score, reverse=True)
        return unique_signals[: self.max_results * 2]

    def get_trending_topics(
        self,
        subreddits: list[str] | None = None,
        time_filter: str = "day",
    ) -> list[dict[str, Any]]:
        """
        Get trending topics from subreddits.

        Returns aggregated topics with mention counts and example posts.
        """
        subreddits = subreddits or DEFAULT_SUBREDDITS[:10]  # Limit for speed
        topic_counts: dict[str, dict[str, Any]] = {}

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                posts = subreddit.top(time_filter=time_filter, limit=50)

                for post in posts:
                    # Extract potential topics from title
                    topics = self._extract_topics(post.title)
                    for topic in topics:
                        topic_lower = topic.lower()
                        if topic_lower not in topic_counts:
                            topic_counts[topic_lower] = {
                                "topic": topic,
                                "count": 0,
                                "total_score": 0,
                                "subreddits": set(),
                                "example_posts": [],
                            }
                        topic_counts[topic_lower]["count"] += 1
                        topic_counts[topic_lower]["total_score"] += post.score
                        topic_counts[topic_lower]["subreddits"].add(subreddit_name)
                        if len(topic_counts[topic_lower]["example_posts"]) < 3:
                            topic_counts[topic_lower]["example_posts"].append({
                                "title": post.title,
                                "url": f"https://reddit.com{post.permalink}",
                                "score": post.score,
                            })

            except Exception as e:
                logger.warning(f"Error getting trends from r/{subreddit_name}: {e}")
                continue

        # Convert to list and sort by engagement
        topics = []
        for data in topic_counts.values():
            if data["count"] >= 2:  # At least 2 mentions
                topics.append({
                    "topic": data["topic"],
                    "mention_count": data["count"],
                    "total_engagement": data["total_score"],
                    "subreddit_count": len(data["subreddits"]),
                    "subreddits": list(data["subreddits"]),
                    "example_posts": data["example_posts"],
                })

        topics.sort(key=lambda t: t["total_engagement"], reverse=True)
        return topics[:20]

    def _extract_signal(
        self,
        post: Submission,
        subreddit_name: str,
    ) -> RedditSignal | None:
        """Extract signal data from a Reddit post."""
        try:
            text = f"{post.title} {post.selftext if hasattr(post, 'selftext') else ''}"
            text_lower = text.lower()

            # Check for buying signals
            buying_signals = [
                signal for signal in BUYING_SIGNALS
                if signal in text_lower
            ]

            # Check for pain points
            pain_points = [
                signal for signal in PAIN_POINT_SIGNALS
                if signal in text_lower
            ]

            # Extract questions (sentences ending with ?)
            questions = re.findall(r'[^.!?]*\?', text)
            questions = [q.strip() for q in questions if len(q) > 10][:5]

            # Calculate relevance score
            relevance = self._calculate_relevance(
                post,
                buying_signals,
                pain_points,
                questions,
            )

            return RedditSignal(
                subreddit=subreddit_name,
                post_id=post.id,
                post_title=post.title[:200],
                post_url=f"https://reddit.com{post.permalink}",
                post_score=post.score,
                comment_count=post.num_comments,
                created_utc=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
                pain_points=pain_points[:5],
                buying_signals=buying_signals[:5],
                questions=questions,
                relevance_score=relevance,
            )
        except Exception as e:
            logger.debug(f"Error extracting signal from post: {e}")
            return None

    def _calculate_relevance(
        self,
        post: Submission,
        buying_signals: list[str],
        pain_points: list[str],
        questions: list[str],
    ) -> float:
        """
        Calculate relevance score (0-1) for a post.

        Factors:
        - Buying signal presence (0.4 weight)
        - Pain point presence (0.3 weight)
        - Engagement (score + comments) (0.2 weight)
        - Question presence (0.1 weight)
        """
        score = 0.0

        # Buying signals (up to 0.4)
        if buying_signals:
            score += min(len(buying_signals) * 0.1, 0.4)

        # Pain points (up to 0.3)
        if pain_points:
            score += min(len(pain_points) * 0.1, 0.3)

        # Engagement score (up to 0.2)
        engagement = post.score + (post.num_comments * 2)
        if engagement > 100:
            score += 0.2
        elif engagement > 50:
            score += 0.15
        elif engagement > 20:
            score += 0.1
        elif engagement > 5:
            score += 0.05

        # Questions (up to 0.1)
        if questions:
            score += min(len(questions) * 0.03, 0.1)

        return min(score, 1.0)

    def _extract_topics(self, title: str) -> list[str]:
        """Extract potential product topics from a post title."""
        # Remove common words and extract key phrases
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "i", "you", "he", "she", "it", "we", "they", "what", "which",
            "who", "when", "where", "why", "how", "all", "each", "every",
            "both", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too",
            "very", "just", "can", "my", "your", "this", "that", "these",
            "those", "am", "for", "and", "but", "or", "if", "then",
            "with", "from", "to", "of", "in", "on", "at", "by", "about",
        }

        # Extract 2-3 word phrases
        words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
        words = [w for w in words if w not in stop_words and len(w) > 2]

        topics = []
        # Single important words
        for word in words:
            if len(word) > 4:
                topics.append(word)

        # Two-word phrases
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            topics.append(phrase)

        return topics[:5]

    def infer_product_type(self, signals: list[RedditSignal]) -> str:
        """
        Infer the best product type based on aggregated signals.

        Returns: prompt_pack, guide, template_pack, checklist, or roadmap
        """
        type_scores: dict[str, int] = {
            "prompt_pack": 0,
            "guide": 0,
            "template_pack": 0,
            "checklist": 0,
            "roadmap": 0,
        }

        for signal in signals:
            text = f"{signal.post_title} {' '.join(signal.questions)}".lower()

            for product_type, keywords in PRODUCT_TYPE_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in text:
                        type_scores[product_type] += 1

        # Default to guide if no clear winner
        best_type = max(type_scores, key=type_scores.get)
        if type_scores[best_type] == 0:
            return "guide"

        return best_type
