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
    
    async def find_and_moderate_company(
        self,
        company_name: str,
        action: str = "approve"
    ) -> Optional[int]:
        """
        Find company by name and moderate it.
        Note: Companies don't have pending status, they are created as approved.
        This method is kept for compatibility with test flow.
        
        Args:
            company_name: Name of the company
            action: "approve" or "reject" (for compatibility)
            
        Returns:
            Company ID if found, None otherwise
        """
        try:
            # Get all companies
            response = await self.client.get("/api/v1/test/companies/all")
            
            if response.status_code != 200:
                logger.error(f"Failed to get companies: {response.status_code}")
                return None
            
            data = response.json()
            companies = data.get("companies", [])
            
            # Find company by name
            for company in companies:
                if company.get("name") == company_name:
                    company_id = company.get("id")
                    logger.info(f"Found company ID {company_id} for name {company_name}")
                    
                    # Call moderate endpoint for compatibility (it will just return success)
                    mod_response = await self.client.post(
                        f"/api/v1/test/moderate/company/{company_id}",
                        params={"action": action}
                    )
                    
                    if mod_response.status_code == 200:
                        logger.info(f"Company {company_id} moderation completed (action: {action})")
                        return company_id
                    else:
                        logger.error(f"Failed to moderate company: {mod_response.status_code}")
                        return None
            
            logger.warning(f"No company found with name: {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding/moderating company: {e}")
            return None
    
    async def delete_company(self, company_id: int) -> bool:
        """
        Delete a company by ID (for cleanup).
        
        Args:
            company_id: ID of the company to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = await self.client.delete(
                f"/api/v1/test/companies/{company_id}"
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Successfully deleted company {company_id}")
                return True
            else:
                logger.error(f"Failed to delete company {company_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting company {company_id}: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
