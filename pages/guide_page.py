"""
Page Object for Guide Pages in Hiker's Voice.
Handles guide profile pages and guide-related interactions.
"""

from typing import Dict, Any, Optional
from playwright.async_api import Page
from pages.base_page import BasePage


class GuidePage(BasePage):
    """
    Page Object for Guide Profile Pages.
    
    Handles viewing guide profiles, reviews, and related information.
    """
    
    # Guide profile elements
    GUIDE_NAME = "h1"
    GUIDE_RATING = ".text-lg.font-semibold"  # Contains "X/5" rating
    GUIDE_REVIEWS_COUNT = "text=отзыв"  # Text containing review count
    GUIDE_INFO = ".space-y-2"  # Container with guide information
    
    # Review elements on guide page
    REVIEW_SECTION = "article.card"  # Review cards on guide page
    REVIEW_AUTHOR = "span.font-medium >> .. >> text"  # Author name in review
    REVIEW_TEXT = ".prose"  # Review text content
    REVIEW_RATING = "svg"  # Star icons for rating
    
    # Navigation
    BACK_BUTTON = "a:has-text('← Назад')"
    LEAVE_REVIEW_BUTTON = "a:has-text('Оставить отзыв')"
    
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize GuidePage.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
    
    async def open_guide_page(self, guide_id: int) -> None:
        """
        Open a specific guide's profile page.
        
        Args:
            guide_id: ID of the guide
        """
        url = f"{self.base_url}/guides/{guide_id}"
        await self.page.goto(url)
        await self.wait_for_load()
        
        # Verify we're on the guide page
        assert await self.is_guide_page(guide_id), f"Failed to open guide page for ID {guide_id}"
    
    async def is_guide_page(self, guide_id: int) -> bool:
        """
        Check if we're currently on a specific guide's page.
        
        Args:
            guide_id: Expected guide ID
            
        Returns:
            True if on the correct guide page
        """
        current_url = self.page.url
        return f"/guides/{guide_id}" in current_url
    
    async def get_guide_name(self) -> str:
        """
        Get the guide's name from the profile page.
        
        Returns:
            Guide name
        """
        name_element = self.page.locator(self.GUIDE_NAME).first
        if await name_element.is_visible():
            name = await name_element.text_content()
            return name.strip() if name else ""
        return ""
    
    async def get_guide_rating(self) -> Optional[float]:
        """
        Get the guide's average rating.
        
        Returns:
            Average rating or None if no rating
        """
        try:
            # Look for rating text like "4.5/5"
            rating_elements = await self.page.locator(self.GUIDE_RATING).all()
            for element in rating_elements:
                text = await element.text_content()
                if text and "/5" in text:
                    rating_str = text.split("/")[0].strip()
                    return float(rating_str)
            
            # Alternative: look for any text with pattern X.X/5 or X/5
            import re
            page_text = await self.page.locator("body").text_content()
            if page_text:
                # Search for rating pattern
                rating_match = re.search(r'(\d+\.?\d*)\s*/\s*5', page_text)
                if rating_match:
                    return float(rating_match.group(1))
        except Exception as e:
            self.logger.error(f"Failed to get guide rating: {e}")
        return None
    
    async def get_reviews_count(self) -> int:
        """
        Get the number of reviews for the guide.
        
        Returns:
            Number of reviews
        """
        try:
            # Look for text like "15 отзывов"
            elements = await self.page.locator("text=/\\d+ отзыв/").all()
            for element in elements:
                text = await element.text_content()
                if text:
                    # Extract number from text
                    import re
                    match = re.search(r'(\d+)', text)
                    if match:
                        return int(match.group(1))
        except Exception as e:
            self.logger.error(f"Failed to get reviews count: {e}")
        return 0
    
    async def check_review_exists(self, author_name: str = None, review_text: str = None) -> bool:
        """
        Check if a specific review exists on the guide page.
        
        Args:
            author_name: Optional author name to search for
            review_text: Optional review text to search for
            
        Returns:
            True if review found
        """
        reviews = await self.page.locator(self.REVIEW_SECTION).all()
        
        for review in reviews:
            review_content = await review.text_content()
            if not review_content:
                continue
            
            # Check author name if provided
            if author_name:
                # Handle anonymous case
                if author_name == "" or author_name is None:
                    if "Автор: Аноним" in review_content:
                        if review_text and review_text in review_content:
                            return True
                        elif not review_text:
                            return True
                else:
                    if f"Автор: {author_name}" in review_content:
                        if review_text and review_text in review_content:
                            return True
                        elif not review_text:
                            return True
            
            # Check review text if provided and author not specified
            if not author_name and review_text and review_text in review_content:
                return True
        
        return False
    
    async def get_review_by_author(self, author_name: str):
        """
        Find a review by author name.
        
        Args:
            author_name: Name of the review author (empty string for anonymous)
            
        Returns:
            Review locator or None if not found
        """
        if author_name == "" or author_name is None:
            # Looking for anonymous review
            selector = f"article.card:has-text('Автор: Аноним')"
        else:
            selector = f"article.card:has-text('Автор: {author_name}')"
        
        count = await self.page.locator(selector).count()
        if count > 0:
            return self.page.locator(selector).first
        return None
    
    async def check_review_rating(self, review_element, expected_rating: int) -> bool:
        """
        Check if a review has the expected rating.
        
        Args:
            review_element: Review card locator
            expected_rating: Expected star rating (1-5)
            
        Returns:
            True if rating matches
        """
        if not review_element:
            return False
        
        # The Rating component always renders 5 stars but changes their style
        # Filled stars have classes: text-yellow-400 fill-current
        # Empty stars have classes: text-gray-300 or text-gray-600
        
        # Count filled stars (yellow ones)
        filled_stars = await review_element.locator("svg.text-yellow-400.fill-current").count()
        
        # If no filled stars found with both classes, try just yellow color
        if filled_stars == 0:
            filled_stars = await review_element.locator("svg.text-yellow-400").count()
        
        self.logger.info(f"Found {filled_stars} filled stars, expected {expected_rating}")
        
        return filled_stars == expected_rating
    
    async def check_review_text(self, review_element, expected_text: str) -> bool:
        """
        Check if a review contains the expected text.
        
        Args:
            review_element: Review card locator
            expected_text: Expected text in the review
            
        Returns:
            True if text found
        """
        if not review_element:
            return False
        
        content = await review_element.text_content()
        return expected_text in content if content else False
    
    async def click_leave_review(self) -> None:
        """
        Click the 'Leave Review' button on the guide page.
        """
        if await self.is_element_visible(self.LEAVE_REVIEW_BUTTON):
            await self.click_and_wait(self.LEAVE_REVIEW_BUTTON)
        else:
            raise Exception("Leave Review button not found on guide page")
    
    async def get_guide_info(self) -> Dict[str, Any]:
        """
        Get all guide information from the profile page.
        
        Returns:
            Dictionary with guide information
        """
        info = {
            "name": await self.get_guide_name(),
            "rating": await self.get_guide_rating(),
            "reviews_count": await self.get_reviews_count()
        }
        
        # Try to get additional info from the info section
        info_section = self.page.locator(self.GUIDE_INFO).first
        if await info_section.is_visible():
            info_text = await info_section.text_content()
            if info_text:
                # Parse info text for languages, experience, etc.
                lines = info_text.split("\n")
                for line in lines:
                    if "Языки:" in line:
                        info["languages"] = line.replace("Языки:", "").strip()
                    elif "Опыт:" in line:
                        info["experience"] = line.replace("Опыт:", "").strip()
                    elif "Специализация:" in line:
                        info["specialization"] = line.replace("Специализация:", "").strip()
        
        return info
