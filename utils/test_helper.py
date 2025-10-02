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
                    
                    # Companies are auto-approved, so just return the ID
                    logger.info(f"Company {company_id} is already approved (companies don't need moderation)")
                    return company_id
            
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
    
    async def get_guide_by_id(self, guide_id: int) -> Optional[dict]:
        """
        Get guide information by ID.
        
        Args:
            guide_id: ID of the guide
            
        Returns:
            Guide data dictionary if found, None otherwise
        """
        try:
            response = await self.client.get(f"/api/v1/guides/{guide_id}")
            
            if response.status_code == 200:
                guide_data = response.json()
                logger.info(f"Retrieved guide {guide_id}: {guide_data.get('name')}")
                return guide_data
            else:
                logger.error(f"Failed to get guide {guide_id}: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting guide {guide_id}: {e}")
            return None
    
    async def get_guides_list(self, limit: int = 50) -> Optional[list]:
        """
        Get list of all guides.
        
        Args:
            limit: Maximum number of guides to fetch
            
        Returns:
            List of guide dictionaries if successful, None otherwise
        """
        try:
            response = await self.client.get("/api/v1/guides", params={"limit": limit, "offset": 0})
            
            if response.status_code == 200:
                data = response.json()
                # API может возвращать как новый формат {items: [], total: N}, так и legacy {guides: [], total: N}
                guides = data.get("items") or data.get("guides", [])
                logger.info(f"Retrieved {len(guides)} guides from API")
                return guides
            else:
                logger.error(f"Failed to get guides list: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting guides list: {e}")
            return None
    
    async def delete_guide(self, guide_id: int) -> bool:
        """
        Delete a guide by ID (for cleanup).
        
        Args:
            guide_id: ID of the guide to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            response = await self.client.delete(
                f"/api/v1/test/guides/{guide_id}"
            )
            
            if response.status_code in [200, 204]:
                logger.info(f"Successfully deleted guide {guide_id}")
                return True
            else:
                logger.error(f"Failed to delete guide {guide_id}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting guide {guide_id}: {e}")
            return False
    
    async def delete_review(self, review_id: int) -> bool:
        """
        Delete a review by ID using admin panel endpoint (for cleanup).
        
        Args:
            review_id: ID of the review to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        import base64
        
        # Admin credentials - EXACTLY as in backend
        ADMIN_USERNAME = "Philippe_testeroni"
        ADMIN_PASSWORD = "KeklikG0nnaKek!"
        
        # Create Basic Auth header
        credentials = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode('ascii')
        auth_headers = {"Authorization": f"Basic {encoded_credentials}"}
        
        try:
            response = await self.client.post(
                f"/admin/review/{review_id}/delete",
                headers=auth_headers,
                follow_redirects=False
            )
            
            # 303 See Other is the expected response (redirect after deletion)
            if response.status_code == 303:
                logger.info(f"Successfully deleted review {review_id}")
                return True
            elif response.status_code == 401:
                logger.error(f"Failed to authenticate with admin panel for review {review_id}")
                logger.error(f"Tried credentials: {ADMIN_USERNAME}")
                return False
            else:
                logger.error(f"Failed to delete review {review_id}: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting review {review_id}: {e}")
            return False
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
