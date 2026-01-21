"""
Opportunity models for discovery and validation tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class OpportunityStatus(str, Enum):
    """Status progression for opportunities."""

    DISCOVERED = "discovered"
    PENDING_GATE1 = "pending_gate1"
    VALIDATING_ORGANIC = "validating_organic"
    VALIDATING_PAID = "validating_paid"
    VALIDATED = "validated"
    VALIDATION_FAILED = "validation_failed"
    MANUFACTURING = "manufacturing"
    PENDING_GATE2 = "pending_gate2"
    PUBLISHED = "published"
    REJECTED = "rejected"


class ValidationMethod(str, Enum):
    """Validation approaches."""

    ORGANIC = "organic"
    PAID = "paid"
    SKIPPED = "skipped"


class ProductType(str, Enum):
    """Types of digital products."""

    PROMPT_PACK = "prompt_pack"
    GUIDE = "guide"
    ROADMAP = "roadmap"
    TEMPLATE_PACK = "template_pack"
    CHECKLIST = "checklist"


class Confidence(str, Enum):
    """Confidence levels for opportunities."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LandingPageCopy(BaseModel):
    """Landing page copy structure."""

    headline: str
    subhead: str
    bullets: list[str]
    cta_text: str


class OrganicSignals(BaseModel):
    """Tracked organic validation signals."""

    dms: int = 0
    buy_comments: int = 0
    questions: int = 0
    upvotes: int = 0
    shares: int = 0
    email_signups: int = 0


class AdResult(BaseModel):
    """Results from a single ad platform."""

    spend_cents: int = 0
    clicks: int = 0
    signups: int = 0
    cvr: float = 0.0


class OpportunityBase(BaseModel):
    """Base opportunity fields."""

    title: str = Field(..., min_length=5, max_length=200)
    description: str | None = None
    target_audience: str | None = None
    product_type: ProductType | None = None

    # Scores
    opportunity_score: float | None = Field(None, ge=0, le=100)
    demand_score: float | None = Field(None, ge=0, le=50)
    intent_score: float | None = Field(None, ge=0, le=40)
    confidence: Confidence = Confidence.HIGH

    # SEO
    primary_keyword: str | None = None
    monthly_volume: int | None = Field(None, ge=0)
    cpc: float | None = Field(None, ge=0)

    # Pricing
    suggested_price_cents: int | None = Field(None, ge=0)


class OpportunityCreate(OpportunityBase):
    """Fields for creating a new opportunity."""

    # Discovery evidence
    reddit_mentions: int = Field(default=0, ge=0)
    twitter_mentions: int = Field(default=0, ge=0)
    evidence_urls: list[str] | None = None
    competitor_info: dict[str, Any] | None = None


class OpportunityUpdate(BaseModel):
    """Fields that can be updated on an opportunity."""

    title: str | None = None
    description: str | None = None
    target_audience: str | None = None
    product_type: ProductType | None = None

    # Scores
    opportunity_score: float | None = None
    demand_score: float | None = None
    intent_score: float | None = None
    confidence: Confidence | None = None

    # SEO
    primary_keyword: str | None = None
    monthly_volume: int | None = None
    cpc: float | None = None

    # Landing page
    landing_page_url: str | None = None
    landing_page_copy: LandingPageCopy | None = None
    samples: list[str] | None = None

    # Validation
    validation_method: ValidationMethod | None = None
    organic_deadline: datetime | None = None
    logged_signals: OrganicSignals | None = None
    validation_points: int | None = None

    # Paid validation
    ad_platforms: list[str] | None = None
    ad_campaigns: dict[str, Any] | None = None
    ad_results: dict[str, AdResult] | None = None
    combined_cvr: float | None = None

    # Status
    status: OpportunityStatus | None = None
    retry_eligible_after: datetime | None = None
    skipped_validation: bool | None = None

    # Pricing
    suggested_price_cents: int | None = None


class Opportunity(OpportunityBase):
    """Full opportunity model from database."""

    id: UUID
    status: OpportunityStatus = OpportunityStatus.DISCOVERED

    # Discovery evidence
    reddit_mentions: int = 0
    twitter_mentions: int = 0
    evidence_urls: list[str] | None = None
    competitor_info: dict[str, Any] | None = None

    # Landing page
    landing_page_url: str | None = None
    landing_page_copy: LandingPageCopy | None = None
    samples: list[str] | None = None

    # Tracking
    visits: int = 0
    signups: int = 0

    # Validation
    validation_method: ValidationMethod | None = None
    post_templates: dict[str, str] | None = None
    organic_deadline: datetime | None = None
    logged_signals: OrganicSignals | None = None
    validation_points: int = 0

    # Paid validation
    ad_platforms: list[str] | None = None
    ad_campaigns: dict[str, Any] | None = None
    ad_results: dict[str, AdResult] | None = None
    combined_cvr: float | None = None

    # Status
    retry_eligible_after: datetime | None = None
    skipped_validation: bool = False

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
