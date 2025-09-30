"""
Page Object for Reviews List Page in Hiker's Voice.
Handles the /reviews page with all reviews list.
"""

from typing import Optional
from playwright.async_api import Page
from pages.base_page import BasePage


class ReviewsPage(BasePage):
    """
    Page Object for Reviews List Page (/reviews).
    
    Handles viewing all reviews and filtering/searching functionality.
    """
    
    # Page elements
    PAGE_TITLE = "h1:has-text('Все отзывы')"
    
    # Review cards
    REVIEW_CARDS = "article.card"
    REVIEW_AUTHOR = "span.font-medium >> .. >> text"
    REVIEW_TEXT = "p"  # Review preview text
    REVIEW_RATING = "svg"  # Star icons
    
    # Filters and search
    SEARCH_INPUT = "input[placeholder*='Поиск']"
    FILTER_BUTTON = "button:has-text('Фильтры')"
    
    # Pagination
    PAGINATION = "nav[aria-label='Pagination']"
    NEXT_PAGE = "a:has-text('Следующая')"
    PREV_PAGE = "a:has-text('Предыдущая')"
    
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize ReviewsPage.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
    
    async def open(self) -> None:
        """
        Open the reviews list page.
        """
        url = f"{self.base_url}/reviews"
        await self.page.goto(url)
        await self.wait_for_load()
        
        # Verify we're on the reviews page
        assert await self.is_reviews_page(), "Failed to open reviews page"
    
    async def is_reviews_page(self) -> bool:
        """
        Check if we're currently on the reviews list page.
        
        Returns:
            True if on reviews page
        """
        current_url = self.page.url
        return "/reviews" in current_url
    
    async def get_reviews_count(self) -> int:
        """
        Get the number of reviews displayed on the current page.
        
        Returns:
            Number of review cards
        """
        return await self.page.locator(self.REVIEW_CARDS).count()
    
    async def check_review_exists(self, author_name: str = None, review_text: str = None) -> bool:
        """
        Check if a specific review exists on the reviews page.
        
        Args:
            author_name: Optional author name to search for
            review_text: Optional review text to search for
            
        Returns:
            True if review found
        """
        reviews = await self.page.locator(self.REVIEW_CARDS).all()
        
        for review in reviews:
            review_content = await review.text_content()
            if not review_content:
                continue
            
            # Check author name if provided
            if author_name is not None:
                # Handle anonymous case
                if author_name == "":
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
            if author_name is None and review_text and review_text in review_content:
                return True
        
        return False
    
    async def find_review_by_author(self, author_name: str):
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
    
    async def search_reviews(self, query: str) -> None:
        """
        Search for reviews using the search input.
        
        Args:
            query: Search query
        """
        await self.fill_and_validate(self.SEARCH_INPUT, query)
        await self.page.press(self.SEARCH_INPUT, "Enter")
        await self.page.wait_for_load_state("networkidle")
    
    async def go_to_next_page(self) -> bool:
        """
        Navigate to the next page of reviews if available.
        
        Returns:
            True if navigated to next page, False if no next page
        """
        if await self.is_element_visible(self.NEXT_PAGE):
            await self.click_and_wait(self.NEXT_PAGE)
            return True
        return False
    
    async def check_review_on_any_page(self, author_name: str = None, review_text: str = None, max_pages: int = 5) -> bool:
        """
        Check if a review exists on any page (with pagination).
        
        Args:
            author_name: Optional author name to search for
            review_text: Optional review text to search for
            max_pages: Maximum number of pages to check
            
        Returns:
            True if review found on any page
        """
        for page_num in range(max_pages):
            if await self.check_review_exists(author_name, review_text):
                return True
            
            # Try to go to next page
            if not await self.go_to_next_page():
                break  # No more pages
        
        return False
