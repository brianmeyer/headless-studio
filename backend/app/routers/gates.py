"""
Gates Router - API endpoints for Gate 1 and Gate 2 reviews.

Manages opportunity approvals, validation assignments, and publishing.
"""

import logging
from typing import Literal
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.utils.supabase_client import get_supabase_client
from app.services.post_templates import PostTemplateGenerator
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

class ApprovalRequest(BaseModel):
    opportunity_id: UUID
    validation_method: Literal["organic", "paid", "skip"]
    notes: str | None = None

class RejectionRequest(BaseModel):
    opportunity_id: UUID
    reason: str | None = None

@router.get("/gate1/pending")
async def get_pending_gate1():
    """
    Get all opportunities pending Gate 1 review.
    """
    try:
        client = get_supabase_client()
        result = client.table("opportunities").select("*").eq("status", "discovered").execute()
        
        # Also include 'pending_gate1' if they were partially prepared
        result2 = client.table("opportunities").select("*").eq("status", "pending_gate1").execute()
        
        return {
            "success": True,
            "count": len(result.data) + len(result2.data),
            "opportunities": result.data + result2.data
        }
    except Exception as e:
        logger.exception("Failed to fetch pending opportunities")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gate1/approve")
async def approve_gate1(request: ApprovalRequest):
    """
    Approve an opportunity and move it to the selected validation phase.
    """
    try:
        client = get_supabase_client()
        settings = get_settings()
        
        # Fetch current opportunity
        opp_result = client.table("opportunities").select("*").eq("id", str(request.opportunity_id)).single().execute()
        if not opp_result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")
            
        opp = opp_result.data
        
        # Update status and data based on method
        new_status = "validating_organic" if request.validation_method == "organic" else \
                     "validating_paid" if request.validation_method == "paid" else \
                     "manufacturing"
        
        update_data = {
            "status": new_status,
            "validation_method": request.validation_method,
            "gate1_approved_at": datetime.utcnow().isoformat(),
            "gate1_notes": request.notes
        }
        
        # If organic, generate post templates if not already present
        if request.validation_method == "organic":
            template_gen = PostTemplateGenerator(settings)
            lp_url = opp.get("landing_page_url") or f"{settings.api_url}/lp/{opp['id']}"
            
            templates = await template_gen.generate_templates(
                title=opp["title"],
                description=opp.get("description", ""),
                target_audience=opp.get("target_audience", ""),
                landing_page_url=lp_url,
                product_type=opp.get("product_type", "Digital Product")
            )
            update_data["post_templates"] = templates.model_dump()
            
            # Set validation deadline (7 days from now)
            deadline = datetime.utcnow() + timedelta(days=7)
            update_data["validation_deadline"] = deadline.isoformat()
            
        client.table("opportunities").update(update_data).eq("id", str(request.opportunity_id)).execute()
        
        # Log the approval
        client.table("system_logs").insert({
            "log_type": "workflow",
            "workflow_name": "gate1",
            "message": f"Gate 1 Approved: {opp['title']} (Method: {request.validation_method})",
            "opportunity_id": str(request.opportunity_id),
            "severity": "info"
        }).execute()
        
        return {
            "success": True,
            "new_status": new_status,
            "opportunity_id": str(request.opportunity_id)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Gate 1 approval failed")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/gate1/reject")
async def reject_gate1(request: RejectionRequest):
    """
    Reject an opportunity and archive it.
    """
    try:
        client = get_supabase_client()
        
        # Set retry eligible after 90 days
        retry_date = datetime.utcnow() + timedelta(days=90)
        
        update_data = {
            "status": "rejected",
            "gate1_rejected_at": datetime.utcnow().isoformat(),
            "gate1_rejection_reason": request.reason,
            "retry_eligible_after": retry_date.isoformat()
        }
        
        client.table("opportunities").update(update_data).eq("id", str(request.opportunity_id)).execute()
        
        return {
            "success": True,
            "status": "rejected",
            "retry_eligible_after": retry_date.isoformat()
        }
    except Exception as e:
        logger.exception("Gate 1 rejection failed")
        raise HTTPException(status_code=500, detail=str(e))
