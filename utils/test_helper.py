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
        action: str = "approve",
        company_id: Optional[int] = None,
        guide_id: Optional[int] = None
    ) -> Optional[int]:
        """
        Find review by author name, then moderate it.
        
        IMPORTANT: Reviews are created with status 'pending_rate_limited' and WITHOUT entity linking.
        Entity linking (company_id/guide_id assignment) happens ONLY during moderation approval.
        Therefore, we search ONLY by author_name, not by company_id/guide_id.
        
        Args:
            author_name: Name of the review author (should be unique with timestamp)
            action: "approve" or "reject"
            company_id: Optional - used ONLY for verification AFTER moderation
            guide_id: Optional - used ONLY for verification AFTER moderation
            
        Returns:
            Review ID if found and moderated, None otherwise
        """
        try:
            # Get all reviews
            response = await self.client.get("/api/v1/test/reviews/all")
            
            if response.status_code != 200:
                logger.error(f"Failed to get reviews: {response.status_code}")
                return None
            
            data = response.json()
            reviews = data.get("reviews", [])
            
            # Find reviews by author name and pending status ONLY
            # Do NOT filter by company_id/guide_id - they are NULL before moderation!
            matching_reviews = []
            for review in reviews:
                # Check author name matches
                if review.get("author_name") != author_name:
                    continue
                
                # Check status is pending (any variant)
                status = review.get("status")
                if status not in ["pending", "pending_rate_limited", "pending_moderation"]:
                    continue
                
                matching_reviews.append(review)
            
            if not matching_reviews:
                logger.warning(f"No pending review found for author: {author_name}")
                logger.warning(f"Searched statuses: pending, pending_rate_limited, pending_moderation")
                return None
            
            # If multiple matches, take the one with HIGHEST ID (most recent)
            if len(matching_reviews) > 1:
                logger.warning(f"Found {len(matching_reviews)} matching reviews for '{author_name}', taking the most recent one")
                matching_reviews.sort(key=lambda r: r.get("id", 0), reverse=True)
            
            review = matching_reviews[0]
            review_id = review.get("id")
            
            # Log what we found BEFORE moderation
            logger.info(f"Found review ID {review_id} for author '{author_name}'")
            logger.debug(f"  Status before moderation: {review.get('status')}")
            logger.debug(f"  company_id before moderation: {review.get('company_id')}")
            logger.debug(f"  guide_id before moderation: {review.get('guide_id')}")
            
            # Moderate the review
            mod_response = await self.client.post(
                f"/api/v1/test/moderate/{review_id}",
                params={"action": action}
            )
            
            if mod_response.status_code == 200:
                logger.info(f"Review {review_id} {action}d successfully")
                
                # Optional: Verify entity linking happened correctly AFTER moderation
                if action == "approve" and (company_id or guide_id):
                    # Re-fetch review to check entity linking
                    verify_response = await self.client.get("/api/v1/test/reviews/all")
                    if verify_response.status_code == 200:
                        verify_data = verify_response.json()
                        verify_reviews = verify_data.get("reviews", [])
                        moderated_review = next((r for r in verify_reviews if r.get("id") == review_id), None)
                        
                        if moderated_review:
                            linked_company = moderated_review.get("company_id")
                            linked_guide = moderated_review.get("guide_id")
                            
                            if company_id and linked_company != company_id:
                                logger.warning(f"Entity linking mismatch! Expected company_id={company_id}, got {linked_company}")
                            if guide_id and linked_guide != guide_id:
                                logger.warning(f"Entity linking mismatch! Expected guide_id={guide_id}, got {linked_guide}")
                            
                            logger.debug(f"  company_id after moderation: {linked_company}")
                            logger.debug(f"  guide_id after moderation: {linked_guide}")
                
                return review_id
            else:
                logger.error(f"Failed to moderate review: {mod_response.status_code}")
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
    
    async def get_master_key(self, entity_type: str, entity_id: int) -> Optional[str]:
        """
        Get or generate master key for an entity via test endpoint.
        
        This endpoint returns existing master key or automatically generates a new one
        if it doesn't exist (similar to Telegram bot's /generate_company_key command).
        
        Args:
            entity_type: "company" or "guide"
            entity_id: ID of the entity
            
        Returns:
            Master key UUID string if successful, None otherwise
        """
        try:
            response = await self.client.get(
                f"/api/v1/test/master-key/{entity_type}/{entity_id}"
            )
            
            if response.status_code == 200:
                data = response.json()
                master_key = data.get("master_key")
                was_generated = data.get("generated", False)
                
                if was_generated:
                    logger.info(f"Generated new master key for {entity_type} #{entity_id}")
                else:
                    logger.info(f"Retrieved existing master key for {entity_type} #{entity_id}")
                
                return master_key
            elif response.status_code == 404:
                logger.error(f"{entity_type.capitalize()} {entity_id} not found")
                return None
            else:
                logger.error(f"Failed to get master key: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting master key for {entity_type} {entity_id}: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
