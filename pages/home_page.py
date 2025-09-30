"""
Page Object for Hiker's Voice Home Page.
Handles interactions with the main page including reviews display and navigation.
"""

from typing import Dict, Any, Optional
from playwright.async_api import Page, Locator
from pages.base_page import BasePage


class HomePage(BasePage):
    """
    Page Object for the Home Page of Hiker's Voice.
    
    Provides methods to interact with review cards, filters,
    and navigation elements on the main page.
    """
    
    # Locators
    LEAVE_REVIEW_BUTTON = "button:has-text('Оставить отзыв')"
    LEAVE_REVIEW_BUTTON_ALT = "button:has-text('Оставить первый отзыв')"
    
    # Review cards
    REVIEW_CARDS = "[data-testid='review-card'], .review-card, article.review"
    REVIEW_CARD_TITLE = ".review-title, h3, h2"
    REVIEW_CARD_AUTHOR = ".review-author, .author"
    REVIEW_CARD_RATING = ".rating, [data-testid='rating']"
    REVIEW_CARD_CONTENT = ".review-content, .review-text, p"
    
    # Filters and search
    SEARCH_INPUT = "input[placeholder*='Поиск'], input[type='search']"
    FILTER_BUTTON = "button:has-text('Фильтры'), button:has-text('Фильтр')"
    SORT_DROPDOWN = "select[name='sort'], [data-testid='sort-select']"
    
    # Navigation
    LOGO = "a[href='/'], .logo, [data-testid='logo']"
    ABOUT_LINK = "a[href='/about'], a:has-text('О проекте')"
    COMPANIES_LINK = "a[href='/companies'], a:has-text('Компании')"
    GUIDES_LINK = "a[href='/guides'], a:has-text('Гиды')"
    
    # Success messages
    SUCCESS_MESSAGE = ".success-message, [role='alert']:has-text('успешно')"
    ERROR_MESSAGE = ".error-message, [role='alert']:has-text('ошибка')"
    
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize HomePage.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
        
    async def open(self) -> None:
        """
        Open the home page and wait for it to load.
        """

        
        await self.page.goto(self.base_url)
        await self.wait_for_load()
        
        # Force dark theme if needed
        await self.page.evaluate("""
            () => {
                // Add dark class to html/body if using Tailwind dark mode
                document.documentElement.classList.add('dark');
                document.body.classList.add('dark');
                
                // Set dark theme in localStorage if the site uses it
                localStorage.setItem('theme', 'dark');
                localStorage.setItem('color-theme', 'dark');
                
                // Dispatch event to notify about theme change
                window.dispatchEvent(new Event('storage'));
            }
        """)
        

        
        # Verify we're on the home page
        assert await self.is_home_page(), "Failed to open home page"

    
    async def is_home_page(self) -> bool:
        """
        Check if we're currently on the home page.
        
        Returns:
            True if on home page, False otherwise
        """
        current_url = self.page.url
        return current_url == self.base_url or current_url == f"{self.base_url}/"
    
    async def click_leave_review(self) -> None:
        """
        Click the 'Leave Review' button to open review type modal.
        """
        # Try to find and click the leave review button
        button = self.page.locator("button:has-text('Оставить отзыв'), button:has-text('Оставить первый отзыв')").first
        
        # Check if button exists and is visible
        if not await button.is_visible():
            visible_buttons = await self.page.locator("button:visible").all_text_contents()
            raise Exception(f"Leave Review button not found. Available buttons: {visible_buttons}")
        
        await button.click()
        await self.page.wait_for_timeout(1000)  # Wait for modal animation

    
    async def get_reviews_count(self) -> int:
        """
        Get the count of reviews displayed on the page.
        
        Returns:
            Number of review cards visible
        """
        try:
            # Wait for at least one review card or empty state
            await self.page.wait_for_selector(
                f"{self.REVIEW_CARDS}, .empty-state, .no-reviews",
                timeout=5000
            )
            
            # Count review cards
            review_cards = await self.page.locator(self.REVIEW_CARDS).count()

            return review_cards
            
        except Exception as e:

            return 0
    
    async def get_review_data(self, index: int = 0) -> Dict[str, Any]:
        """
        Get data from a specific review card.
        
        Args:
            index: Index of the review card (0-based)
            
        Returns:
            Dictionary with review data
        """
        try:
            review_cards = self.page.locator(self.REVIEW_CARDS)
            count = await review_cards.count()
            
            if index >= count:
                raise IndexError(f"Review index {index} out of range (total: {count})")
            
            card = review_cards.nth(index)
            
            # Extract review data
            data = {
                "title": await self._safe_get_text(card, self.REVIEW_CARD_TITLE),
                "author": await self._safe_get_text(card, self.REVIEW_CARD_AUTHOR),
                "rating": await self._safe_get_text(card, self.REVIEW_CARD_RATING),
                "content": await self._safe_get_text(card, self.REVIEW_CARD_CONTENT),
            }
            

            return data
            
        except Exception as e:
            self.logger.error(f"Failed to get review data: {e}")
            raise
    
    async def search_reviews(self, query: str) -> None:
        """
        Search for reviews using the search input.
        
        Args:
            query: Search query string
        """

        
        # Find and fill search input
        await self.fill_and_validate(self.SEARCH_INPUT, query)
        
        # Press Enter to submit search
        await self.page.press(self.SEARCH_INPUT, "Enter")
        
        # Wait for results to load
        await self.page.wait_for_load_state("networkidle")

    
    async def apply_sort(self, sort_option: str) -> None:
        """
        Apply sorting to reviews list.
        
        Args:
            sort_option: Sort option value (e.g., 'date_desc', 'rating_desc')
        """

        
        # Select sort option
        await self.page.select_option(self.SORT_DROPDOWN, sort_option)
        
        # Wait for re-render
        await self.page.wait_for_load_state("networkidle")

    
    async def navigate_to_companies(self) -> None:
        """Navigate to companies page."""
        await self.click_and_wait(self.COMPANIES_LINK)
        await self.check_url("/companies")
    
    async def navigate_to_guides(self) -> None:
        """Navigate to guides page."""
        await self.click_and_wait(self.GUIDES_LINK)
        await self.check_url("/guides")
    
    async def navigate_to_about(self) -> None:
        """Navigate to about page."""
        await self.click_and_wait(self.ABOUT_LINK)
        await self.check_url("/about")
    
    async def check_success_message(self, expected_text: Optional[str] = None) -> bool:
        """
        Check if success message is displayed.
        
        Args:
            expected_text: Optional expected text in the message
            
        Returns:
            True if success message is displayed
        """
        try:
            if await self.is_element_visible(self.SUCCESS_MESSAGE, timeout=3000):
                if expected_text:
                    actual_text = await self.get_text(self.SUCCESS_MESSAGE)
                    return expected_text.lower() in actual_text.lower()
                return True
            
            # Check URL parameter for success
            current_url = self.page.url
            if "success=review_created" in current_url:

                return True
                
            return False
            
        except:
            return False
    
    async def check_error_message(self) -> Optional[str]:
        """
        Check if error message is displayed and get its text.
        
        Returns:
            Error message text if displayed, None otherwise
        """
        try:
            if await self.is_element_visible(self.ERROR_MESSAGE, timeout=2000):
                return await self.get_text(self.ERROR_MESSAGE)
            return None
        except:
            return None
    
    async def _safe_get_text(self, parent: Locator, selector: str) -> str:
        """
        Safely get text from element within parent.
        
        Args:
            parent: Parent locator
            selector: Child element selector
            
        Returns:
            Text content or empty string
        """
        try:
            element = parent.locator(selector).first
            if await element.is_visible():
                text = await element.text_content()
                return text.strip() if text else ""
        except:
            pass
        return ""
    
    async def wait_for_reviews_to_load(self, timeout: int = 10000) -> None:
        """
        Wait for reviews to load on the page.
        
        Args:
            timeout: Maximum wait time in milliseconds
        """
        try:
            # Wait for either reviews (article.card) or empty state
            # ReviewCard uses <article class="card ...">
            await self.page.wait_for_selector(
                "article.card, .text-center:has-text('Отзывов не найдено')",
                timeout=timeout
            )

        except Exception as e:
            self.logger.error(f"Failed to load reviews section: {e}")
            raise
    
    async def get_review_cards_count(self) -> int:
        """
        Get count of review cards on the page.
        
        Returns:
            Number of review cards
        """
        # ReviewCard uses <article class="card ...">
        count = await self.page.locator("article.card").count()

        return count
    
    async def find_review_by_author(self, author_name: str):
        """
        Find a review card by author name.
        
        Args:
            author_name: Name of the review author
            
        Returns:
            Locator for the review card or None if not found
        """
        # On card, author is displayed as "Автор: {name}"
        selector = f"article.card:has-text('Автор: {author_name}')"
        
        # Check if such card exists
        count = await self.page.locator(selector).count()
        if count > 0:

            return self.page.locator(selector).first
        

        return None
    
    async def check_review_card_content(self, review_card, expected_text: str, truncated: bool = True) -> bool:
        """
        Check if review card contains expected text.
        
        Args:
            review_card: Review card locator
            expected_text: Text to search for
            truncated: If True, expect text to be truncated to 120 chars
            
        Returns:
            True if text found, False otherwise
        """
        card_text = await review_card.text_content()
        
        if truncated:
            # On card, text is truncated to 120 symbols
            search_text = expected_text[:117] if len(expected_text) > 120 else expected_text
        else:
            search_text = expected_text
        
        if card_text and search_text in card_text:

            return True
        else:

            return False
    
    async def click_read_review(self, review_card):
        """
        Click 'Read' button on review card to open full review.
        
        Args:
            review_card: Review card locator
        """
        # Find 'Read' button inside the card
        read_button = review_card.locator("a:has-text('Читать')")
        
        if await read_button.is_visible():
            await read_button.click()

            # Wait for navigation
            await self.page.wait_for_load_state("networkidle")
        else:

            raise Exception("Read button not found")
    
    async def get_review_card_info(self, review_card) -> dict:
        """
        Get all information from review card.
        
        Args:
            review_card: Review card locator
            
        Returns:
            Dictionary with review card information
        """
        info = {}
        
        # Extract author name
        # В ReviewCard структура: <div><span class="font-medium">Автор:</span> Имя автора</div>
        # Сначала находим span с текстом "Автор:", затем его родительский div
        author_span = review_card.locator("span.font-medium").filter(has_text="Автор:")
        if await author_span.count() > 0:
            # Получаем родительский div
            parent_div = author_span.first.locator("..")  # Родительский элемент
            full_text = await parent_div.text_content()
            if full_text:
                info['author'] = full_text.replace('Автор:', '').strip()
        
        # Extract company name
        # Структура: <div><span>Компания:</span><a или span с названием></div>
        company_divs = review_card.locator("div").filter(has_text="Компания:")
        for i in range(await company_divs.count()):
            div = company_divs.nth(i)
            # Проверяем, что это непосредственно див с компанией, а не вложенный
            direct_span = div.locator("> span").first
            if await direct_span.count() > 0:
                span_text = await direct_span.text_content()
                if span_text and "Компания" in span_text:
                    # Ищем ссылку или span с названием
                    company_link = div.locator("a, span.font-medium").nth(1)  # Второй элемент после span с "Компания:"
                    if await company_link.count() > 0:
                        info['company'] = await company_link.text_content()
                    break
        
        # Extract guide name if present (аналогично компании)
        guide_divs = review_card.locator("div").filter(has_text="Гид:")
        for i in range(await guide_divs.count()):
            div = guide_divs.nth(i)
            direct_span = div.locator("> span").first
            if await direct_span.count() > 0:
                span_text = await direct_span.text_content()
                if span_text and "Гид" in span_text:
                    guide_link = div.locator("a, span.font-medium").nth(1)
                    if await guide_link.count() > 0:
                        info['guide'] = await guide_link.text_content()
                    break
        
        # Extract rating (count of star SVGs)
        stars = await review_card.locator('svg').count()
        info['has_rating'] = stars > 0
        info['rating_stars'] = stars
        
        # Extract review date
        date_element = review_card.locator("time")
        if await date_element.count() > 0:
            info['date'] = await date_element.first.text_content()
        
        # Extract truncated content
        content_p = review_card.locator("p")
        if await content_p.count() > 0:
            info['content_preview'] = await content_p.first.text_content()
        
        return info  # Add return statement

    async def get_full_review_text(self) -> str:
        """
        Get full review text from review page.
        
        Returns:
            Full review text content
        """
        full_review_text = await self.page.locator(".prose").first.text_content()
        assert full_review_text, "Full review text is empty"
        return full_review_text
    
    async def check_rating_on_review_page(self, rating: int) -> bool:
        """
        Check if rating is displayed on review page.
        
        Args:
            rating: Expected rating value
            
        Returns:
            True if rating is displayed
        """
        rating_element = self.page.locator(".text-lg.font-semibold").filter(has_text=f"{rating}/5")
        return await rating_element.count() > 0
    
    async def check_author_on_review_page(self, author_name: str) -> bool:
        """
        Check if author name is displayed on review page.
        
        Args:
            author_name: Expected author name
            
        Returns:
            True if author is displayed
        """
        author_section = self.page.locator("div").filter(has_text="Автор:").filter(has_text=author_name)
        return await author_section.count() > 0
