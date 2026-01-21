"""
Landing Pages Router - Serves HTML landing pages and handles signups.

Landing pages are served from FastAPI on Railway using Jinja2 templates.
Note: Supabase Edge Functions cannot serve HTML (returns text/plain).
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize Jinja2 templates
templates = Jinja2Templates(directory="app/templates")


# Default landing page copy if none generated
DEFAULT_COPY = {
    "headline": "Get Your Free Preview",
    "subhead": "Sign up to receive free samples and be notified when the full product launches.",
    "bullets": [
        "Instant access to free samples",
        "Early-bird discount when we launch",
        "No spam, unsubscribe anytime",
    ],
    "cta_text": "Get Free Samples",
    "badge": "Free Preview",
}


@router.get("/lp/{opportunity_id}", response_class=HTMLResponse)
async def landing_page(request: Request, opportunity_id: UUID) -> Response:
    """
    Serve the landing page for an opportunity.

    Renders HTML with the opportunity's landing page copy and tracks visits.
    """
    try:
        client = get_supabase_client()

        # Fetch opportunity
        result = (
            client.table("opportunities")
            .select("id, title, landing_page_copy, samples, visits")
            .eq("id", str(opportunity_id))
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Landing page not found")

        opp = result.data

        # Increment visit counter
        new_visits = (opp.get("visits") or 0) + 1
        client.table("opportunities").update({"visits": new_visits}).eq(
            "id", str(opportunity_id)
        ).execute()

        # Get landing page copy (use default if not generated)
        copy = opp.get("landing_page_copy") or DEFAULT_COPY

        return templates.TemplateResponse(
            "landing_page.html",
            {
                "request": request,
                "opportunity_id": str(opportunity_id),
                "copy": copy,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Landing page error: {e}")
        raise HTTPException(status_code=500, detail="Error loading landing page")


@router.post("/api/signup/{opportunity_id}", response_class=HTMLResponse)
async def handle_signup(
    request: Request,
    opportunity_id: UUID,
    email: str = Form(...),
) -> Response:
    """
    Handle email signup from landing page.

    Validates email, stores signup, and shows thank you page with samples.
    """
    try:
        client = get_supabase_client()

        # Basic email validation
        if not email or "@" not in email or "." not in email:
            raise HTTPException(status_code=400, detail="Invalid email address")

        email = email.lower().strip()

        # Fetch opportunity
        result = (
            client.table("opportunities")
            .select("id, title, samples, signups")
            .eq("id", str(opportunity_id))
            .single()
            .execute()
        )

        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        opp = result.data

        # Check for duplicate signup
        existing = (
            client.table("smoke_test_signups")
            .select("id")
            .eq("opportunity_id", str(opportunity_id))
            .eq("email", email)
            .execute()
        )

        is_new_signup = not existing.data

        if is_new_signup:
            # Get request metadata
            user_agent = request.headers.get("user-agent", "")
            referrer = request.headers.get("referer", "")

            # Insert signup
            client.table("smoke_test_signups").insert(
                {
                    "opportunity_id": str(opportunity_id),
                    "email": email,
                    "source": "landing_page",
                    "user_agent": user_agent[:500] if user_agent else None,
                    "referrer": referrer[:500] if referrer else None,
                    "samples_delivered": True,
                }
            ).execute()

            # Increment signup counter
            new_signups = (opp.get("signups") or 0) + 1
            client.table("opportunities").update({"signups": new_signups}).eq(
                "id", str(opportunity_id)
            ).execute()

            # Log the signup
            client.table("system_logs").insert(
                {
                    "log_type": "workflow",
                    "workflow_name": "signup",
                    "message": f"New signup for: {opp['title']}",
                    "details": {"email_domain": email.split("@")[1], "is_new": True},
                    "severity": "info",
                    "opportunity_id": str(opportunity_id),
                }
            ).execute()

        # Get samples for thank you page
        samples = opp.get("samples") or []

        # Format samples for display
        formatted_samples = []
        for i, sample in enumerate(samples):
            if isinstance(sample, dict):
                formatted_samples.append(sample)
            else:
                formatted_samples.append({"title": f"Sample {i + 1}", "content": str(sample)})

        return templates.TemplateResponse(
            "thank_you.html",
            {
                "request": request,
                "samples": formatted_samples,
                "full_count": 50,  # Estimated full product count
                "is_new": is_new_signup,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Signup error: {e}")
        raise HTTPException(status_code=500, detail="Error processing signup")


@router.get("/api/track/{opportunity_id}")
async def track_visit(opportunity_id: UUID) -> Response:
    """
    Tracking pixel endpoint for visit counting.

    Returns a 1x1 transparent GIF.
    """
    # The actual visit tracking happens in the landing_page route
    # This is just for cases where JS is disabled

    # 1x1 transparent GIF
    gif_bytes = (
        b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
        b"\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00"
        b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;"
    )

    return Response(content=gif_bytes, media_type="image/gif")


@router.get("/api/signups/{opportunity_id}")
async def get_signups(opportunity_id: UUID) -> dict[str, Any]:
    """
    Get signup count and details for an opportunity.

    Used by the validation dashboard.
    """
    try:
        client = get_supabase_client()

        # Get opportunity stats
        opp_result = (
            client.table("opportunities")
            .select("id, title, visits, signups, validation_points")
            .eq("id", str(opportunity_id))
            .single()
            .execute()
        )

        if not opp_result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        # Get signup list (without full emails for privacy)
        signups_result = (
            client.table("smoke_test_signups")
            .select("id, created_at, source, samples_delivered")
            .eq("opportunity_id", str(opportunity_id))
            .order("created_at", desc=True)
            .execute()
        )

        opp = opp_result.data
        visits = opp.get("visits") or 0
        signups = opp.get("signups") or 0

        # Calculate conversion rate
        cvr = (signups / visits * 100) if visits > 0 else 0

        return {
            "success": True,
            "opportunity_id": str(opportunity_id),
            "title": opp.get("title"),
            "visits": visits,
            "signups": signups,
            "conversion_rate": round(cvr, 2),
            "validation_points": opp.get("validation_points") or 0,
            "signup_list": signups_result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Get signups error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching signups")


@router.post("/api/signups/{opportunity_id}/resend-samples")
async def resend_samples(
    opportunity_id: UUID,
    email: str = Form(...),
) -> dict[str, Any]:
    """
    Resend samples to an existing signup.

    Useful if user lost the original thank you page.
    """
    try:
        client = get_supabase_client()

        email = email.lower().strip()

        # Check if signup exists
        signup_result = (
            client.table("smoke_test_signups")
            .select("id")
            .eq("opportunity_id", str(opportunity_id))
            .eq("email", email)
            .single()
            .execute()
        )

        if not signup_result.data:
            raise HTTPException(status_code=404, detail="Signup not found")

        # Get opportunity samples
        opp_result = (
            client.table("opportunities")
            .select("samples")
            .eq("id", str(opportunity_id))
            .single()
            .execute()
        )

        if not opp_result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")

        samples = opp_result.data.get("samples") or []

        return {
            "success": True,
            "message": "Samples retrieved",
            "samples": samples,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Resend samples error: {e}")
        raise HTTPException(status_code=500, detail="Error resending samples")
