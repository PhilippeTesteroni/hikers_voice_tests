"""
Frontend API Client for creating test data using the same endpoints as the frontend.

This client uses public API endpoints (/api/v1) to create companies and guides
for test isolation, ensuring each test has its own unique entities.
"""

import logging
from typing import Optional, List
import httpx
from datetime import datetime

logger = logging.getLogger(__name__)


class FrontendApiClient:
    """
    Client for interacting with frontend-facing API endpoints.
    
    Uses the same endpoints that the frontend uses to create companies and guides.
    This ensures test data is created exactly as real users would create it.
    """
    
    def __init__(self, backend_url: str):
        """
        Initialize Frontend API Client.
        
        Args:
            backend_url: Backend API URL (e.g., http://localhost:8000)
        """
        self.backend_url = backend_url
        self.client = httpx.AsyncClient(base_url=backend_url, timeout=30.0)
    
    async def create_company(
        self,
        name: str,
        country_code: str = "GE",
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_website: Optional[str] = None,
    ) -> dict:
        """
        Create a company using the public API endpoint.
        
        This uses POST /api/v1/companies - the same endpoint the frontend uses.
        
        Args:
            name: Company name (will be made unique with timestamp if needed)
            country_code: ISO country code (default: GE)
            description: Company description
            contact_email: Contact email
            contact_phone: Contact phone
            contact_website: Website URL
            
        Returns:
            dict with company data: {"id": int, "name": str, ...}
            
        Raises:
            HTTPException: If creation fails
        """
        # Make name unique with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{name} TEST-{timestamp}"
        
        # Prepare request data
        company_data = {
            "name": unique_name,
            "country_code": country_code,
        }
        
        if description:
            company_data["description"] = description
        if contact_email:
            company_data["contact_email"] = contact_email
        if contact_phone:
            company_data["contact_phone"] = contact_phone
        if contact_website:
            company_data["contact_website"] = contact_website
        
        try:
            logger.info(f"Creating company via API: {unique_name}")
            
            response = await self.client.post(
                "/companies",  # БЕЗ /api/v1 prefix!
                json=company_data
            )
            
            if response.status_code in [200, 201]:  # Backend может вернуть 200 или 201
                result = response.json()
                company_id = result.get("id")
                logger.info(f"Company created successfully: ID={company_id}, Name={unique_name}")
                
                # Fetch full company data
                company = await self.get_company(company_id)
                return company
                
            elif response.status_code == 409:
                logger.warning(f"Company {unique_name} already exists (409)")
                raise ValueError(f"Company already exists: {unique_name}")
            else:
                logger.error(f"Failed to create company: {response.status_code} - {response.text}")
                raise ValueError(f"Failed to create company: HTTP {response.status_code}")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating company: {e}")
            raise ValueError(f"HTTP error: {e}")
    
    async def create_guide(
        self,
        name: str,
        countries: List[str],
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_phone: Optional[str] = None,
        contact_instagram: Optional[str] = None,
        contact_telegram: Optional[str] = None,
        force_create: bool = False,
    ) -> dict:
        """
        Create a guide using the public API endpoint.
        
        This uses POST /api/v1/guides - the same endpoint the frontend uses.
        
        Args:
            name: Guide name (will be made unique with timestamp)
            countries: List of ISO country codes (e.g., ["GE", "AM"])
            description: Guide description
            contact_email: Contact email
            contact_phone: Contact phone
            contact_instagram: Instagram handle
            contact_telegram: Telegram username
            force_create: Skip duplicate check if True
            
        Returns:
            dict with guide data: {"id": int, "name": str, ...}
            
        Raises:
            HTTPException: If creation fails
        """
        # Make name unique with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_name = f"{name} TEST-{timestamp}"
        
        # Prepare request data
        guide_data = {
            "name": unique_name,
            "countries": countries,
        }
        
        if description:
            guide_data["description"] = description
        if contact_email:
            guide_data["contact_email"] = contact_email
        if contact_phone:
            guide_data["contact_phone"] = contact_phone
        if contact_instagram:
            guide_data["contact_instagram"] = contact_instagram
        if contact_telegram:
            guide_data["contact_telegram"] = contact_telegram
        
        try:
            logger.info(f"Creating guide via API: {unique_name} in {countries}")
            
            # Add force_create parameter if needed
            params = {"force_create": "true"} if force_create else {}
            
            response = await self.client.post(
                "/guides",  # БЕЗ /api/v1 prefix!
                json=guide_data,
                params=params
            )
            
            if response.status_code in [200, 201]:  # Backend может вернуть 200 или 201
                result = response.json()
                guide_id = result.get("id")
                logger.info(f"Guide created successfully: ID={guide_id}, Name={unique_name}")
                
                # Fetch full guide data
                guide = await self.get_guide(guide_id)
                return guide
                
            elif response.status_code == 409:
                logger.warning(f"Guide {unique_name} already exists in {countries} (409)")
                
                # Return existing guide data from 409 response
                result = response.json()
                if "existing_guide" in result:
                    logger.info(f"Returning existing guide data from 409 response")
                    return result["existing_guide"]
                else:
                    raise ValueError(f"Guide already exists: {unique_name} in {countries}")
            else:
                logger.error(f"Failed to create guide: {response.status_code} - {response.text}")
                raise ValueError(f"Failed to create guide: HTTP {response.status_code}")
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error creating guide: {e}")
            raise ValueError(f"HTTP error: {e}")
    
    async def get_company(self, company_id: int) -> Optional[dict]:
        """
        Get company by ID.
        
        Args:
            company_id: Company ID
            
        Returns:
            Company data dict or None if not found
        """
        try:
            response = await self.client.get(f"/companies/{company_id}")  # БЕЗ /api/v1 prefix!
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Company {company_id} not found")
                return None
            else:
                logger.error(f"Failed to get company {company_id}: {response.status_code}")
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting company: {e}")
            return None
    
    async def get_guide(self, guide_id: int) -> Optional[dict]:
        """
        Get guide by ID.
        
        Args:
            guide_id: Guide ID
            
        Returns:
            Guide data dict or None if not found
        """
        try:
            response = await self.client.get(f"/guides/{guide_id}")  # БЕЗ /api/v1 prefix!
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"Guide {guide_id} not found")
                return None
            else:
                logger.error(f"Failed to get guide {guide_id}: {response.status_code}")
                return None
                
        except httpx.HTTPError as e:
            logger.error(f"HTTP error getting guide: {e}")
            return None
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
