"""
Landing Page Copy Generator Service

Generates compelling landing page copy for opportunities using LLM.
Uses Google Gemini for benefit-focused, conversion-optimized copy.
"""

import json
import logging
from typing import Any

import google.generativeai as genai
from pydantic import BaseModel

from ..config import Settings

logger = logging.getLogger(__name__)


class LandingPageCopy(BaseModel):
    """Generated landing page copy structure."""

    headline: str
    subhead: str
    bullets: list[str]
    cta_text: str


class LandingPageGenerator:
    """
    Generates landing page copy for opportunities.

    Uses Google Gemini to create:
    - Compelling headline
    - Benefit-focused subheadline
    - 3-5 bullet points highlighting value
    - Call-to-action text
    """

    def __init__(self, config: Settings):
        """Initialize the generator with API credentials."""
        self.config = config
        genai.configure(api_key=config.google_ai_api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    async def generate_copy(
        self,
        title: str,
        description: str | None = None,
        target_audience: str | None = None,
        product_type: str | None = None,
    ) -> LandingPageCopy:
        """
        Generate landing page copy for an opportunity.

        Args:
            title: The opportunity/product title
            description: Optional description of the product
            target_audience: Who the product is for
            product_type: Type of digital product

        Returns:
            LandingPageCopy with headline, subhead, bullets, and CTA
        """
        prompt = self._build_prompt(title, description, target_audience, product_type)

        try:
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000,
                ),
            )

            return self._parse_response(response.text)

        except Exception as e:
            logger.error(f"Failed to generate landing page copy: {e}")
            # Return fallback copy
            return self._generate_fallback(title, description, product_type)

    def _build_prompt(
        self,
        title: str,
        description: str | None,
        target_audience: str | None,
        product_type: str | None,
    ) -> str:
        """Build the prompt for copy generation."""
        context_parts = [f"Product: {title}"]

        if description:
            context_parts.append(f"Description: {description}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")
        if product_type:
            context_parts.append(f"Product Type: {product_type}")

        context = "\n".join(context_parts)

        return f"""You are an expert copywriter specializing in digital product landing pages.

Generate compelling landing page copy for this digital product:

{context}

Requirements:
1. Headline: Attention-grabbing, benefit-focused (max 10 words)
2. Subhead: Expands on the benefit, creates curiosity (max 20 words)
3. Bullets: 3-4 specific benefits, start with action verbs (max 12 words each)
4. CTA Text: Action-oriented button text (max 4 words)

Focus on:
- What the customer gets (not what the product is)
- Solving a specific pain point
- Creating urgency or desire
- Being specific, not generic

Return ONLY valid JSON in this exact format:
{{
    "headline": "Your headline here",
    "subhead": "Your subheadline here",
    "bullets": ["Benefit 1", "Benefit 2", "Benefit 3"],
    "cta_text": "Get Started Now"
}}"""

    def _parse_response(self, text: str) -> LandingPageCopy:
        """Parse the LLM response into structured copy."""
        # Try to extract JSON from the response
        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())

            return LandingPageCopy(
                headline=data.get("headline", ""),
                subhead=data.get("subhead", ""),
                bullets=data.get("bullets", []),
                cta_text=data.get("cta_text", "Get Free Samples"),
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")

    def _generate_fallback(
        self,
        title: str,
        description: str | None,
        product_type: str | None,
    ) -> LandingPageCopy:
        """Generate fallback copy when LLM fails."""
        # Map product types to appropriate copy templates
        type_templates = {
            "prompt_pack": {
                "headline": f"Get {title}",
                "subhead": "Ready-to-use prompts that save you hours of work",
                "bullets": [
                    "Copy-paste prompts for immediate use",
                    "Tested and optimized for best results",
                    "Regular updates with new prompts",
                ],
                "cta_text": "Get Free Samples",
            },
            "template": {
                "headline": f"Get {title}",
                "subhead": "Professional templates ready to customize",
                "bullets": [
                    "Save hours with pre-built designs",
                    "Easy to customize for your brand",
                    "Instant download, start immediately",
                ],
                "cta_text": "Download Now",
            },
            "ebook": {
                "headline": f"Get {title}",
                "subhead": "Expert insights in an easy-to-read format",
                "bullets": [
                    "Actionable strategies you can implement today",
                    "Based on real-world experience",
                    "Includes bonus resources and checklists",
                ],
                "cta_text": "Get Your Copy",
            },
            "course": {
                "headline": f"Learn {title}",
                "subhead": "Step-by-step training to master the skill",
                "bullets": [
                    "Clear, practical lessons",
                    "Learn at your own pace",
                    "Includes exercises and examples",
                ],
                "cta_text": "Start Learning",
            },
        }

        # Get template or use default
        template = type_templates.get(
            product_type or "prompt_pack",
            type_templates["prompt_pack"],
        )

        return LandingPageCopy(
            headline=template["headline"],
            subhead=description or template["subhead"],
            bullets=template["bullets"],
            cta_text=template["cta_text"],
        )

    def to_dict(self, copy: LandingPageCopy) -> dict[str, Any]:
        """Convert copy to dictionary for storage."""
        return {
            "headline": copy.headline,
            "subhead": copy.subhead,
            "bullets": copy.bullets,
            "cta_text": copy.cta_text,
        }
