"""
Test helper for managing test data and API operations.
"""

import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class TestHelper:
    """Single entry point for all test operations with backend."""
    
    def __init__(self, backend_url: str):
        """
        Initialize TestHelper with backend URL.
        
        Args:
            backend_url: Backend API URL
        """
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(base_url=backend_url, timeout=10.0)
    
    async def find_and_moderate_review(
        self, 
        author_name: str,
        action: str = "approve"
    ) -> Optional[int]:
        """
        Find review by author name and moderate it.
        Single point for review moderation logic.
        
        Args:
            author_name: Name of the review author
            action: "approve" or "reject"
            
        Returns:
            Review ID if found and moderated, None otherwise
        """
        try:
            # Get all pending reviews (including rate-limited)
            response = await self.client.get("/api/v1/test/reviews/all")
            
            if response.status_code != 200:
                logger.error(f"Failed to get reviews: {response.status_code}")
                return None
            
            data = response.json()
            reviews = data.get("reviews", [])
            
            # Find review by author name
            for review in reviews:
                if review.get("author_name") == author_name and \
                   review.get("status") in ["pending", "pending_rate_limited"]:
                    review_id = review.get("id")
                    logger.info(f"Found review ID {review_id} for author {author_name}")
                    
                    # Moderate the review
                    mod_response = await self.client.post(
                        f"/api/v1/test/moderate/{review_id}",
                        params={"action": action}
                    )
                    
                    if mod_response.status_code == 200:
                        logger.info(f"Review {review_id} {action}d successfully")
                        return review_id
                    else:
                        logger.error(f"Failed to moderate review: {mod_response.status_code}")
                        return None
            
            logger.warning(f"No pending review found for author: {author_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding/moderating review: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
