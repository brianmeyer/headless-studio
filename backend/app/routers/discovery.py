"""
Discovery Router - API endpoints for opportunity discovery.

Handles X/Grok scouting (primary), Reddit scouting, trend analysis,
and opportunity surfacing.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import get_settings
from app.models.opportunity import OpportunityCreate
from app.models.signals import RedditSignal
from app.services.reddit_scout import RedditScout, DEFAULT_SUBREDDITS
from app.services.x_scout import XGrokScout, XSignal
from app.services.scorer import OpportunityScorer
from app.services.landing_page import LandingPageGenerator
from app.services.sample_generator import SampleGenerator
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()


# =============================================================================
# X/Grok Discovery Endpoints (Primary)
# =============================================================================


class XSearchRequest(BaseModel):
    """Request body for X search."""
    topics: list[str]
    search_queries: list[str] | None = None
    time_filter: str = "week"
    limit: int = 50


@router.post("/x")
async def search_x(request: XSearchRequest) -> dict[str, Any]:
    """
    Search X/Twitter for product opportunities using Grok.

    This is the PRIMARY discovery method. Grok has native X search capability.

    Args:
        topics: Topics to search for (e.g., ["chatgpt prompts", "AI tools"])
        search_queries: Optional custom queries (overrides auto-generated)
        time_filter: Time range - "day", "week", "month"
        limit: Maximum signals to return

    Returns:
        List of X signals with pain points, buying signals, and relevance scores.
    """
    settings = get_settings()

    if not settings.xai_api_key:
        raise HTTPException(
            status_code=503,
            detail="X/Grok discovery not configured. Set XAI_API_KEY in environment.",
        )

    try:
        scout = XGrokScout(settings)

        signals = await scout.search_x(
            topics=request.topics,
            search_queries=request.search_queries,
            time_filter=request.time_filter,
            limit=request.limit,
        )

        return {
            "success": True,
            "source": "x_grok",
            "count": len(signals),
            "signals": [s.model_dump() for s in signals],
        }

    except Exception as e:
        logger.exception("X/Grok search failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/x/analyze")
async def analyze_x_signals(signals: list[XSignal]) -> dict[str, Any]:
    """
    Analyze X signals to identify product opportunities.

    Uses Grok to cluster signals and suggest product ideas.
    """
    settings = get_settings()

    if not settings.xai_api_key:
        raise HTTPException(
            status_code=503,
            detail="X/Grok not configured. Set XAI_API_KEY in environment.",
        )

    try:
        scout = XGrokScout(settings)
        analysis = await scout.analyze_signals(signals)

        return {
            "success": True,
            "signal_count": len(signals),
            "analysis": analysis,
        }

    except Exception as e:
        logger.exception("X signal analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/x/status")
async def x_scout_status() -> dict[str, Any]:
    """Check if X/Grok scout is configured and operational."""
    settings = get_settings()
    scout = XGrokScout(settings)

    return {
        "configured": scout.is_configured,
        "api_key_set": bool(settings.xai_api_key),
        "message": "X/Grok scout ready" if scout.is_configured else "XAI_API_KEY not set",
    }


# =============================================================================
# Reddit Discovery Endpoints (Supplementary)
# =============================================================================


@router.get("/reddit/search")
async def search_reddit(
    query: str = Query(None, description="Search query"),
    subreddits: str = Query(None, description="Comma-separated subreddit names"),
    time_filter: str = Query("week", description="Time filter: hour, day, week, month, year, all"),
    limit: int = Query(25, ge=1, le=100, description="Results per subreddit"),
) -> dict[str, Any]:
    """
    Search Reddit for product opportunities.

    Returns posts with buying signals, pain points, and relevance scores.
    """
    try:
        scout = RedditScout()

        subreddit_list = None
        if subreddits:
            subreddit_list = [s.strip() for s in subreddits.split(",")]

        signals = scout.search_subreddits(
            subreddits=subreddit_list,
            query=query,
            time_filter=time_filter,
            limit_per_subreddit=limit,
        )

        return {
            "success": True,
            "count": len(signals),
            "signals": [s.model_dump() for s in signals],
        }

    except Exception as e:
        logger.exception("Reddit search failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reddit/keywords")
async def search_by_keywords(
    keywords: str = Query(..., description="Comma-separated keywords to search"),
    subreddits: str = Query(None, description="Comma-separated subreddit names"),
    time_filter: str = Query("week", description="Time filter"),
) -> dict[str, Any]:
    """
    Search Reddit for specific keywords.

    Useful for validating specific product ideas.
    """
    try:
        scout = RedditScout()

        keyword_list = [k.strip() for k in keywords.split(",")]
        subreddit_list = None
        if subreddits:
            subreddit_list = [s.strip() for s in subreddits.split(",")]

        signals = scout.search_by_keywords(
            keywords=keyword_list,
            subreddits=subreddit_list,
            time_filter=time_filter,
        )

        # Infer product type
        product_type = scout.infer_product_type(signals)

        return {
            "success": True,
            "keywords": keyword_list,
            "count": len(signals),
            "inferred_product_type": product_type,
            "signals": [s.model_dump() for s in signals],
        }

    except Exception as e:
        logger.exception("Keyword search failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/reddit/trending")
async def get_trending_topics(
    subreddits: str = Query(None, description="Comma-separated subreddit names"),
    time_filter: str = Query("day", description="Time filter: hour, day, week"),
) -> dict[str, Any]:
    """
    Get trending topics from monitored subreddits.

    Returns aggregated topics with mention counts and engagement.
    """
    try:
        scout = RedditScout()

        subreddit_list = None
        if subreddits:
            subreddit_list = [s.strip() for s in subreddits.split(",")]

        topics = scout.get_trending_topics(
            subreddits=subreddit_list,
            time_filter=time_filter,
        )

        return {
            "success": True,
            "count": len(topics),
            "topics": topics,
        }

    except Exception as e:
        logger.exception("Trending topics failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subreddits")
async def list_default_subreddits() -> dict[str, Any]:
    """Get the default list of monitored subreddits."""
    return {
        "subreddits": DEFAULT_SUBREDDITS,
        "count": len(DEFAULT_SUBREDDITS),
    }


@router.post("/score")
async def score_signals(
    signals: list[RedditSignal],
    primary_keyword: str = Query(None, description="Primary keyword for SEO scoring"),
) -> dict[str, Any]:
    """
    Score a list of signals and generate opportunity data.

    Returns scored opportunity with demand, intent, and overall scores.
    """
    try:
        scorer = OpportunityScorer()
        scored = scorer.score_signals(signals, primary_keyword)

        return {
            "success": True,
            "opportunity": scored,
        }

    except Exception as e:
        logger.exception("Scoring failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities")
async def create_opportunity(opportunity: OpportunityCreate) -> dict[str, Any]:
    """
    Create a new opportunity in the database.

    This surfaces the opportunity for Gate 1 review.
    """
    try:
        client = get_supabase_client()

        # Insert into database
        data = opportunity.model_dump()

        # Convert evidence_urls list to JSONB
        if data.get("evidence_urls"):
            data["evidence_urls"] = data["evidence_urls"]

        result = client.table("opportunities").insert(data).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create opportunity")

        created = result.data[0]

        # Log the creation
        client.table("system_logs").insert({
            "log_type": "workflow",
            "workflow_name": "discovery",
            "message": f"New opportunity created: {opportunity.title}",
            "details": {"opportunity_id": created["id"]},
            "severity": "info",
            "opportunity_id": created["id"],
        }).execute()

        return {
            "success": True,
            "opportunity": created,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Create opportunity failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities")
async def list_opportunities(
    status: str = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    """
    List opportunities from the database.

    Supports filtering by status and pagination.
    """
    try:
        client = get_supabase_client()

        query = client.table("opportunities").select("*")

        if status:
            query = query.eq("status", status)

        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)

        result = query.execute()

        return {
            "success": True,
            "count": len(result.data),
            "opportunities": result.data,
        }

    except Exception as e:
        logger.exception("List opportunities failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: UUID) -> dict[str, Any]:
    """Get a single opportunity by ID."""
    try:
        client = get_supabase_client()

        result = client.table("opportunities").select("*").eq("id", str(opportunity_id)).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        return {
            "success": True,
            "opportunity": result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get opportunity failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
async def run_discovery(
    subreddits: str = Query(None, description="Comma-separated subreddit names"),
    keywords: str = Query(None, description="Comma-separated keywords"),
    auto_create: bool = Query(False, description="Automatically create opportunities"),
) -> dict[str, Any]:
    """
    Run a full discovery workflow.

    1. Scans subreddits for signals
    2. Scores and ranks opportunities
    3. Optionally creates opportunities in database

    This is the main entry point for the Monday discovery workflow.
    """
    try:
        scout = RedditScout()
        scorer = OpportunityScorer()

        subreddit_list = None
        if subreddits:
            subreddit_list = [s.strip() for s in subreddits.split(",")]

        # Step 1: Gather signals
        if keywords:
            keyword_list = [k.strip() for k in keywords.split(",")]
            signals = scout.search_by_keywords(
                keywords=keyword_list,
                subreddits=subreddit_list,
            )
        else:
            signals = scout.search_subreddits(subreddits=subreddit_list)

        if not signals:
            return {
                "success": True,
                "message": "No relevant signals found",
                "opportunities": [],
            }

        # Step 2: Group signals by topic and score
        # For now, treat all signals as one opportunity
        # In production, would cluster by topic
        scored = scorer.score_signals(signals)

        opportunities = []
        if auto_create and scored.get("opportunity_score", 0) >= 50:
            # Create opportunity in database
            client = get_supabase_client()

            opp_data = {
                "title": scored["title"],
                "description": scored.get("description"),
                "target_audience": scored.get("target_audience"),
                "product_type": scored.get("product_type"),
                "opportunity_score": scored.get("opportunity_score"),
                "demand_score": scored.get("demand_score"),
                "intent_score": scored.get("intent_score"),
                "confidence": scored.get("confidence", "medium"),
                "primary_keyword": scored.get("primary_keyword"),
                "reddit_mentions": len(signals),
                "evidence_urls": scored.get("evidence_urls", []),
                "suggested_price_cents": scored.get("suggested_price_cents"),
                "status": "discovered",
            }

            result = client.table("opportunities").insert(opp_data).execute()
            if result.data:
                opportunities.append(result.data[0])

                # Log creation
                client.table("system_logs").insert({
                    "log_type": "workflow",
                    "workflow_name": "discovery",
                    "message": f"Discovery run created opportunity: {opp_data['title']}",
                    "details": {"signal_count": len(signals)},
                    "severity": "info",
                    "opportunity_id": result.data[0]["id"],
                }).execute()

        return {
            "success": True,
            "signal_count": len(signals),
            "scored_opportunity": scored,
            "created_opportunities": opportunities,
            "auto_create": auto_create,
        }

    except Exception as e:
        logger.exception("Discovery run failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/generate-copy")
async def generate_landing_page_copy(opportunity_id: UUID) -> dict[str, Any]:
    """
    Generate landing page copy for an opportunity.

    Uses LLM to create headline, subhead, bullets, and CTA text.
    Updates the opportunity with the generated copy.
    """
    try:
        client = get_supabase_client()
        settings = get_settings()

        # Fetch opportunity
        result = client.table("opportunities").select("*").eq("id", str(opportunity_id)).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        opp = result.data

        # Generate copy
        generator = LandingPageGenerator(settings)
        copy = await generator.generate_copy(
            title=opp["title"],
            description=opp.get("description"),
            target_audience=opp.get("target_audience"),
            product_type=opp.get("product_type"),
        )

        # Update opportunity with copy
        copy_dict = generator.to_dict(copy)
        client.table("opportunities").update({
            "landing_page_copy": copy_dict
        }).eq("id", str(opportunity_id)).execute()

        # Log the action
        client.table("system_logs").insert({
            "log_type": "workflow",
            "workflow_name": "landing_page",
            "message": f"Generated landing page copy for: {opp['title']}",
            "details": {"copy": copy_dict},
            "severity": "info",
            "opportunity_id": str(opportunity_id),
        }).execute()

        return {
            "success": True,
            "opportunity_id": str(opportunity_id),
            "landing_page_copy": copy_dict,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Generate copy failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/generate-samples")
async def generate_samples(
    opportunity_id: UUID,
    num_samples: int = Query(5, ge=1, le=10, description="Number of samples to generate"),
) -> dict[str, Any]:
    """
    Generate sample content for an opportunity.

    Creates free samples to deliver to smoke test signups.
    Updates the opportunity with the generated samples.
    """
    try:
        client = get_supabase_client()
        settings = get_settings()

        # Fetch opportunity
        result = client.table("opportunities").select("*").eq("id", str(opportunity_id)).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        opp = result.data

        # Generate samples
        generator = SampleGenerator(settings)
        samples = await generator.generate_samples(
            title=opp["title"],
            description=opp.get("description"),
            target_audience=opp.get("target_audience"),
            product_type=opp.get("product_type"),
            num_samples=num_samples,
        )

        # Update opportunity with samples
        samples_list = generator.to_list(samples)
        client.table("opportunities").update({
            "samples": samples_list
        }).eq("id", str(opportunity_id)).execute()

        # Log the action
        client.table("system_logs").insert({
            "log_type": "workflow",
            "workflow_name": "sample_generation",
            "message": f"Generated {len(samples)} samples for: {opp['title']}",
            "details": {"sample_count": len(samples)},
            "severity": "info",
            "opportunity_id": str(opportunity_id),
        }).execute()

        return {
            "success": True,
            "opportunity_id": str(opportunity_id),
            "sample_count": len(samples),
            "samples": samples_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Generate samples failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/opportunities/{opportunity_id}/prepare-landing-page")
async def prepare_landing_page(
    opportunity_id: UUID,
    num_samples: int = Query(5, ge=1, le=10),
) -> dict[str, Any]:
    """
    Fully prepare an opportunity for landing page testing.

    Generates both landing page copy and samples in one call.
    Returns the landing page URL when complete.
    """
    try:
        client = get_supabase_client()
        settings = get_settings()

        # Fetch opportunity
        result = client.table("opportunities").select("*").eq("id", str(opportunity_id)).single().execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        opp = result.data

        # Generate landing page copy
        copy_generator = LandingPageGenerator(settings)
        copy = await copy_generator.generate_copy(
            title=opp["title"],
            description=opp.get("description"),
            target_audience=opp.get("target_audience"),
            product_type=opp.get("product_type"),
        )
        copy_dict = copy_generator.to_dict(copy)

        # Generate samples
        sample_generator = SampleGenerator(settings)
        samples = await sample_generator.generate_samples(
            title=opp["title"],
            description=opp.get("description"),
            target_audience=opp.get("target_audience"),
            product_type=opp.get("product_type"),
            num_samples=num_samples,
        )
        samples_list = sample_generator.to_list(samples)

        # Construct landing page URL
        landing_page_url = f"{settings.supabase_url}/functions/v1/landing-page/{opportunity_id}"

        # Update opportunity with all data
        client.table("opportunities").update({
            "landing_page_copy": copy_dict,
            "samples": samples_list,
            "landing_page_url": landing_page_url,
            "status": "pending_gate1",
        }).eq("id", str(opportunity_id)).execute()

        # Log the action
        client.table("system_logs").insert({
            "log_type": "workflow",
            "workflow_name": "landing_page_prep",
            "message": f"Landing page prepared for: {opp['title']}",
            "details": {
                "landing_page_url": landing_page_url,
                "sample_count": len(samples),
            },
            "severity": "info",
            "opportunity_id": str(opportunity_id),
        }).execute()

        return {
            "success": True,
            "opportunity_id": str(opportunity_id),
            "landing_page_url": landing_page_url,
            "landing_page_copy": copy_dict,
            "sample_count": len(samples),
            "samples": samples_list,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Prepare landing page failed")
        raise HTTPException(status_code=500, detail=str(e))
