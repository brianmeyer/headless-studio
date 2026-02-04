"""
Post Templates Service - Generates platform-specific post templates for organic validation.
"""

import logging
from typing import Dict, List
from pydantic import BaseModel

from app.config import Settings
from app.services.llm import LLMService

logger = logging.getLogger(__name__)

class PostTemplates(BaseModel):
    reddit: Dict[str, str]
    x: Dict[str, str]
    facebook: Dict[str, str]
    tips: List[str]

class PostTemplateGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.llm = LLMService(settings)

    async def generate_templates(
        self,
        title: str,
        description: str,
        target_audience: str,
        landing_page_url: str,
        product_type: str = "Digital Guide/Prompt Pack"
    ) -> PostTemplates:
        """
        Generate posting templates for Reddit, X (Twitter), and Facebook.
        """
        prompt = f"""
        You are an expert social media marketer for "Headless Studio", an AI product factory.
        Your goal is to generate high-converting organic post templates to validate a product idea.
        
        PRODUCT DETAILS:
        Title: {title}
        Description: {description}
        Target Audience: {target_audience}
        Product Type: {product_type}
        Landing Page URL: {landing_page_url}
        
        TASKS:
        1. Generate a Reddit post (Title and Body). Focus on being helpful, not salesy. 
           Mention that you're "thinking of building this" and ask if it would be helpful.
           Include a clear call to action for the free samples.
        2. Generate an X (Twitter) post/thread starter. High hook, clear benefit.
        3. Generate a Facebook Group post. Focus on community and solving a specific pain point.
        4. Provide 3 specific tips for organic validation for this niche.
        
        FORMAT: Return a JSON object with:
        {{
            "reddit": {{"title": "...", "body": "..."}},
            "x": {{"text": "..."}},
            "facebook": {{"body": "..."}},
            "tips": ["tip1", "tip2", "tip3"]
        }}
        """
        
        # In a real implementation, we would call the LLM
        # For now, we return a structured mock or call a helper
        try:
            # result = await self.llm.generate_json(prompt)
            # return PostTemplates(**result)
            
            # Mock implementation for now to ensure it works without LLM configured
            return PostTemplates(
                reddit={
                    "title": f"Would a collection of {title} help you? Thinking of putting one together",
                    "body": f"Hey everyone - I've been noticing a lot of people struggling with {description}.\n\nI'm thinking of putting together a {product_type} for {target_audience}. It would include my best resources for this.\n\nWould this be useful? If there's interest, I put together 5 free samples here: {landing_page_url}\n\nOr just DM me if you want early access when it's ready."
                },
                x={
                    "text": f"Stop struggling with {description}. 🛑\n\nI'm building a {product_type} specifically for {target_audience}.\n\nWant the first 5 samples for free? Check it out here: {landing_page_url}\n\n#AI #Productivity"
                },
                facebook={
                    "body": f"Hi everyone! I'm working on a new resource for {target_audience} to help with {description}. It's a {product_type} designed to save you hours each week.\n\nI'd love to get some feedback from this community. Does this sound like something you'd use? I've got 5 free samples ready for anyone who wants to take a look: {landing_page_url}"
                },
                tips=[
                    "Don't post the link directly in subreddits that ban self-promotion. Instead, say 'DM me for the link'.",
                    f"Post in groups specifically where {target_audience} hang out.",
                    "Engage with every single comment to boost visibility."
                ]
            )
        except Exception as e:
            logger.error(f"Failed to generate post templates: {e}")
            raise
