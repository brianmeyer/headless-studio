"""
Sample Generator Service

Generates free sample content for opportunities to deliver to signups.
Uses Groq (Qwen3 or Llama) for fast, high-quality sample generation.
"""

import json
import logging
from typing import Any

from groq import Groq
from pydantic import BaseModel

from ..config import Settings

logger = logging.getLogger(__name__)


class Sample(BaseModel):
    """A single sample item."""

    title: str
    content: str


class SampleGenerator:
    """
    Generates sample content for smoke test signups.

    Creates 5 high-quality, actually useful samples that:
    - Demonstrate the value of the full product
    - Are immediately usable
    - Leave people wanting more
    """

    def __init__(self, config: Settings):
        """Initialize the generator with Groq client."""
        self.config = config
        self.client = Groq(api_key=config.groq_api_key)
        # Use a fast, capable model
        self.model = "llama-3.1-70b-versatile"

    async def generate_samples(
        self,
        title: str,
        description: str | None = None,
        target_audience: str | None = None,
        product_type: str | None = None,
        num_samples: int = 5,
    ) -> list[Sample]:
        """
        Generate sample content for an opportunity.

        Args:
            title: The opportunity/product title
            description: Optional description
            target_audience: Who the product is for
            product_type: Type of digital product
            num_samples: Number of samples to generate (default 5)

        Returns:
            List of Sample objects with title and content
        """
        prompt = self._build_prompt(
            title, description, target_audience, product_type, num_samples
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert content creator. Generate high-quality, immediately useful samples that demonstrate real value.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.8,
                max_tokens=3000,
            )

            return self._parse_response(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Failed to generate samples: {e}")
            # Return fallback samples
            return self._generate_fallback(title, product_type, num_samples)

    def _build_prompt(
        self,
        title: str,
        description: str | None,
        target_audience: str | None,
        product_type: str | None,
        num_samples: int,
    ) -> str:
        """Build the prompt for sample generation."""
        context_parts = [f"Product: {title}"]

        if description:
            context_parts.append(f"Description: {description}")
        if target_audience:
            context_parts.append(f"Target Audience: {target_audience}")
        if product_type:
            context_parts.append(f"Product Type: {product_type}")

        context = "\n".join(context_parts)

        # Customize prompt based on product type
        type_instructions = self._get_type_instructions(product_type)

        return f"""Generate {num_samples} FREE SAMPLE items for this digital product:

{context}

{type_instructions}

Requirements for each sample:
1. Must be IMMEDIATELY USEFUL - the person should be able to use it right away
2. Must be COMPLETE - not a teaser or truncated version
3. Must DEMONSTRATE VALUE - show the quality of the full product
4. Must be SPECIFIC - not generic filler content

Return ONLY valid JSON in this exact format:
{{
    "samples": [
        {{
            "title": "Sample 1 Title",
            "content": "The actual sample content here..."
        }},
        {{
            "title": "Sample 2 Title",
            "content": "The actual sample content here..."
        }}
    ]
}}

Generate exactly {num_samples} samples. Each sample should be 50-200 words of actual usable content."""

    def _get_type_instructions(self, product_type: str | None) -> str:
        """Get type-specific instructions for sample generation."""
        instructions = {
            "prompt_pack": """For a prompt pack, generate actual ready-to-use prompts.
Each sample should be a complete prompt that the user can copy and paste into an AI tool.
Include any necessary context, role-setting, and output format instructions.""",
            "template": """For a template pack, generate actual template content.
Each sample should be a complete, usable template (email template, document template, etc).
Include placeholders marked with [brackets] where users customize.""",
            "ebook": """For an ebook/guide, generate actual excerpts or mini-chapters.
Each sample should teach one specific concept or technique completely.
Include actionable steps or insights the reader can implement immediately.""",
            "course": """For a course, generate actual lesson content.
Each sample should be a complete mini-lesson covering one concept.
Include clear explanations and at least one practical exercise or example.""",
            "checklist": """For a checklist product, generate actual checklist sections.
Each sample should be a complete, usable checklist for one specific task or process.
Include 5-10 actionable items per checklist.""",
            "swipe_file": """For a swipe file, generate actual examples to swipe.
Each sample should be a complete, ready-to-adapt example (headline, email, ad copy, etc).
Include brief notes on why the example works.""",
        }

        return instructions.get(
            product_type or "prompt_pack",
            instructions["prompt_pack"],
        )

    def _parse_response(self, text: str) -> list[Sample]:
        """Parse the LLM response into sample objects."""
        try:
            # Handle markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            data = json.loads(text.strip())
            samples = data.get("samples", [])

            return [
                Sample(
                    title=s.get("title", f"Sample {i+1}"),
                    content=s.get("content", ""),
                )
                for i, s in enumerate(samples)
                if s.get("content")
            ]

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            raise ValueError(f"Invalid LLM response format: {e}")

    def _generate_fallback(
        self,
        title: str,
        product_type: str | None,
        num_samples: int,
    ) -> list[Sample]:
        """Generate fallback samples when LLM fails."""
        # Generic fallback samples based on product type
        fallback_templates = {
            "prompt_pack": [
                Sample(
                    title="Quick Start Prompt",
                    content=f"You are an expert assistant helping with {title}. I need you to [describe your specific need]. Please provide a detailed, actionable response that includes step-by-step instructions and best practices.",
                ),
                Sample(
                    title="Problem-Solving Prompt",
                    content=f"I'm facing a challenge with {title}. The specific issue is [describe problem]. Please analyze this situation and provide 3 different approaches I could take, along with pros and cons of each.",
                ),
                Sample(
                    title="Learning Prompt",
                    content=f"Explain {title} to me as if I'm a complete beginner. Break down the key concepts, provide real-world examples, and give me 3 practical exercises I can do to practice.",
                ),
            ],
            "template": [
                Sample(
                    title="Basic Template",
                    content=f"# {title}\n\n## Overview\n[Your overview here]\n\n## Key Points\n- Point 1: [Details]\n- Point 2: [Details]\n- Point 3: [Details]\n\n## Action Items\n[ ] Task 1\n[ ] Task 2\n[ ] Task 3",
                ),
            ],
        }

        templates = fallback_templates.get(
            product_type or "prompt_pack",
            fallback_templates["prompt_pack"],
        )

        # Return up to num_samples
        return templates[:num_samples]

    def to_list(self, samples: list[Sample]) -> list[dict[str, Any]]:
        """Convert samples to list of dicts for storage."""
        return [{"title": s.title, "content": s.content} for s in samples]
