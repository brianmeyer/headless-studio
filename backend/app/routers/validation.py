"""
Validation Router - API endpoints for opportunity validation tracking.

Handles logging organic signals, calculating validation points, 
and managing validation status.
"""

import logging
from enum import Enum
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)
router = APIRouter()

class SignalType(str, Enum):
    EMAIL_SIGNUP = "email_signup"
    DM = "dm"
    BUY_COMMENT = "buy_comment"
    SHARE = "share"
    QUESTION = "question"
    HELPFUL_COMMENT = "helpful_comment"
    SAVE = "save"
    FOLLOW = "follow"
    UPVOTE = "upvote"
    WEAK_COMMENT = "weak_comment"

SIGNAL_POINTS = {
    SignalType.EMAIL_SIGNUP: 3,
    SignalType.DM: 4,
    SignalType.BUY_COMMENT: 3,
    SignalType.SHARE: 3,
    SignalType.QUESTION: 2,
    SignalType.HELPFUL_COMMENT: 2,
    SignalType.SAVE: 2,
    SignalType.FOLLOW: 2,
    SignalType.UPVOTE: 0.04,  # 1 pt per 25
    SignalType.WEAK_COMMENT: 1,
}

class SignalLogRequest(BaseModel):
    opportunity_id: UUID
    signal_type: SignalType
    platform: str
    quote: str | None = None
    count: int = 1

def calculate_points(logged_signals: dict) -> int:
    """Calculate validation points based on the rubric."""
    total_points = 0.0
    for signal_type_str, count in logged_signals.items():
        try:
            signal_type = SignalType(signal_type_str)
            points_per = SIGNAL_POINTS.get(signal_type, 0)
            total_points += points_per * count
        except ValueError:
            continue
    return int(total_points)

@router.post("/log-signal")
async def log_organic_signal(request: SignalLogRequest):
    """
    Log an organic validation signal and update total points.
    """
    try:
        client = get_supabase_client()
        
        # Fetch current opportunity
        result = client.table("opportunities").select("id, logged_signals, validation_points, signups").eq("id", str(request.opportunity_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")
        
        opp = result.data
        logged_signals = opp.get("logged_signals") or {}
        
        # Update counts
        current_count = logged_signals.get(request.signal_type.value, 0)
        logged_signals[request.signal_type.value] = current_count + request.count
        
        # Recalculate points
        # Note: signups are tracked separately in the database but also count for points
        # We ensure signups from the signups table are included if not already in logged_signals
        if "email_signup" not in logged_signals or logged_signals["email_signup"] < opp.get("signups", 0):
            logged_signals["email_signup"] = opp.get("signups", 0)
            
        points = calculate_points(logged_signals)
        
        # Update opportunity
        update_data = {
            "logged_signals": logged_signals,
            "validation_points": points
        }
        
        # If points >= 15, we might want to auto-transition or just flag it
        # For now, just update points
        
        client.table("opportunities").update(update_data).eq("id", str(request.opportunity_id)).execute()
        
        # Log to system_logs
        client.table("system_logs").insert({
            "log_type": "validation",
            "message": f"Logged {request.count} {request.signal_type.value} signals for opportunity",
            "details": {
                "platform": request.platform,
                "quote": request.quote,
                "new_total_points": points
            },
            "opportunity_id": str(request.opportunity_id)
        }).execute()
        
        return {
            "success": True,
            "new_points": points,
            "logged_signals": logged_signals
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to log signal")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{opportunity_id}/status")
async def get_validation_status(opportunity_id: UUID):
    """Get detailed validation status for an opportunity."""
    try:
        client = get_supabase_client()
        result = client.table("opportunities").select("*").eq("id", str(opportunity_id)).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Opportunity not found")
            
        opp = result.data
        points = opp.get("validation_points") or 0
        passed = points >= 15
        
        return {
            "opportunity_id": str(opportunity_id),
            "title": opp.get("title"),
            "status": opp.get("status"),
            "validation_points": points,
            "pass_threshold": 15,
            "passed": passed,
            "logged_signals": opp.get("logged_signals") or {},
            "signups": opp.get("signups") or 0
        }
    except Exception as e:
        logger.exception("Failed to get validation status")
        raise HTTPException(status_code=500, detail=str(e))
