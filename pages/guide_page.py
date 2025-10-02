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
    
    # Photo gallery elements
    PHOTO_GALLERY_SECTION = ".card:has-text('Фотографии из отзывов')"
    PHOTO_THUMBNAIL = "button.relative.aspect-square"
    LIGHTBOX_DIALOG = "div[role='dialog']"
    LIGHTBOX_COUNTER = ".absolute.top-4.left-4.text-white"
    LIGHTBOX_CLOSE_BUTTON = "button[aria-label='Закрыть']"
    LIGHTBOX_NEXT_BUTTON = "button[aria-label='Следующее фото']"
    LIGHTBOX_PREV_BUTTON = "button[aria-label='Предыдущее фото']"
    
    # New guide form selectors
    GUIDE_NAME_INPUT = "input#name"
    GUIDE_DESCRIPTION_TEXTAREA = "textarea#description"
    GUIDE_COUNTRIES_SELECT = "select"
    GUIDE_EMAIL_INPUT = "input#contact_email"
    GUIDE_PHONE_INPUT = "input#contact_phone"
    GUIDE_INSTAGRAM_INPUT = "input#contact_instagram"
    GUIDE_TELEGRAM_INPUT = "input#contact_telegram"
    CREATE_GUIDE_BUTTON = "button:has-text('Создать профиль')"
    SUCCESS_MESSAGE = ".bg-green-100"
    
    # Duplicate guide warning selectors
    DUPLICATE_WARNING = ".bg-yellow-50"
    DUPLICATE_MESSAGE = "text=Возможно, этот гид уже существует"
    DUPLICATE_CARD = ".bg-gray-50"
    YES_GO_TO_PROFILE_BUTTON = "text=Да, перейти к профилю"
    NO_CREATE_NEW_BUTTON = "text=Нет, создать нового"
    
    # Duplicate card elements
    DUPLICATE_GUIDE_NAME = ".bg-gray-50 h3"
    DUPLICATE_GUIDE_COUNTRIES = ".bg-gray-50 .bg-blue-100"
    DUPLICATE_GUIDE_RATING = ".bg-gray-50 .text-yellow-400"
    DUPLICATE_GUIDE_CONTACTS = ".bg-gray-50 .space-y-1"
    
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
            # Look for rating in stats blocks
            stats_blocks = await self.page.query_selector_all(".flex.items-center.space-x-3")
            for block in stats_blocks:
                text = await block.text_content()
                if 'Рейтинг' in text and '/' in text:
                    # Extract rating from text like "Рейтинг4.5/5.0"
                    import re
                    match = re.search(r'(\d+\.\d+)/5\.0', text)
                    if match:
                        return float(match.group(1))
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
            import re
            # Look for reviews in stats blocks
            stats_blocks = await self.page.query_selector_all(".flex.items-center.space-x-3")
            for block in stats_blocks:
                text = await block.text_content()
                if 'Отзывы' in text:
                    # Extract count from text like "Отзывы15 оценок"
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
    
    async def open_new_guide_form(self) -> None:
        """Open the new guide creation form."""
        url = f"{self.base_url}/guides/new"
        await self.page.goto(url)
        await self.wait_for_load()
    
    async def fill_guide_form(self, guide_data: Dict[str, Any]) -> None:
        """
        Fill the new guide form with provided data.
        
        Args:
            guide_data: Dictionary containing guide information
        """
        # Fill required fields
        if "name" in guide_data:
            await self.fill_and_validate(self.GUIDE_NAME_INPUT, guide_data["name"])
        
        if "description" in guide_data:
            await self.fill_and_validate(self.GUIDE_DESCRIPTION_TEXTAREA, guide_data["description"])
        
        # Fill countries (multi-select)
        if "countries" in guide_data:
            for country_code in guide_data["countries"]:
                await self.page.select_option(self.GUIDE_COUNTRIES_SELECT, country_code)
                await self.page.wait_for_timeout(300)  # Wait for UI update
        
        # Fill optional contact fields
        if "email" in guide_data:
            await self.fill_and_validate(self.GUIDE_EMAIL_INPUT, guide_data["email"])
        
        if "phone" in guide_data:
            await self.fill_and_validate(self.GUIDE_PHONE_INPUT, guide_data["phone"])
        
        if "instagram" in guide_data:
            await self.fill_and_validate(self.GUIDE_INSTAGRAM_INPUT, guide_data["instagram"])
        
        if "telegram" in guide_data:
            await self.fill_and_validate(self.GUIDE_TELEGRAM_INPUT, guide_data["telegram"])
    
    async def submit_guide_form(self) -> None:
        """Submit the guide creation form."""
        await self.click_and_wait(self.CREATE_GUIDE_BUTTON)
    
    async def wait_for_duplicate_warning(self) -> bool:
        """
        Wait for duplicate guide warning message to appear.
        
        Returns:
            True if duplicate warning appeared, False otherwise
        """
        try:
            await self.page.wait_for_selector(self.DUPLICATE_WARNING, timeout=10000)
            await self.page.wait_for_selector(self.DUPLICATE_MESSAGE, timeout=5000)
            return True
        except:
            return False
    
    async def get_duplicate_guide_info(self) -> Dict[str, Any]:
        """
        Get information about the duplicate guide from the warning card.
        
        Returns:
            Dictionary with duplicate guide information
        """
        info = {}
        
        # Get guide name
        name_element = await self.page.query_selector(self.DUPLICATE_GUIDE_NAME)
        if name_element:
            info["name"] = await name_element.text_content()
        
        # Get countries
        country_badges = await self.page.query_selector_all(self.DUPLICATE_GUIDE_COUNTRIES)
        info["countries"] = []
        for badge in country_badges:
            country = await badge.text_content()
            if country:
                info["countries"].append(country.strip())
        
        # Get rating
        rating_element = await self.page.query_selector(self.DUPLICATE_GUIDE_RATING)
        if rating_element:
            rating_text = await self.page.locator(".bg-gray-50").locator("text=/\\d+\\.\\d+/").first.text_content()
            if rating_text:
                info["rating"] = float(rating_text)
        
        # Get reviews count
        reviews_element = self.page.locator(".bg-gray-50").locator("text=/\\d+ отзыв/").first
        if await reviews_element.count() > 0:
            reviews_text = await reviews_element.text_content()
            import re
            match = re.search(r'(\d+)', reviews_text)
            if match:
                info["reviews_count"] = int(match.group(1))
        
        # Get contacts
        contacts_section = await self.page.query_selector(self.DUPLICATE_GUIDE_CONTACTS)
        if contacts_section:
            contacts_text = await contacts_section.text_content()
            info["contacts"] = {}
            
            if "@" in contacts_text:
                lines = contacts_text.split("\n")
                for line in lines:
                    line = line.strip()
                    if line.startswith("@"):
                        # Could be Telegram or Instagram
                        if "telegram" in line.lower() or len(info["contacts"]) == 0:
                            info["contacts"]["telegram"] = line
                        else:
                            info["contacts"]["instagram"] = line
                    elif "+" in line or line.replace(" ", "").replace("-", "").isdigit():
                        info["contacts"]["phone"] = line
                    elif "@" in line and "." in line:
                        info["contacts"]["email"] = line
        
        return info
    
    async def click_yes_go_to_profile(self) -> None:
        """Click 'Yes, go to profile' button on duplicate warning."""
        await self.click_and_wait(self.YES_GO_TO_PROFILE_BUTTON)
    
    async def check_duplicate_card_has_photo(self) -> bool:
        """
        Check if duplicate guide card displays a photo (not placeholder).
        
        Returns:
            True if real photo is displayed
        """
        img_element = await self.page.query_selector(".bg-gray-50 img")
        if img_element:
            src = await img_element.get_attribute("src")
            return src is not None and "placeholder" not in src
        return False
    
    async def get_success_guide_id(self) -> Optional[int]:
        """
        Get the guide ID from the success message after creation.
        
        Returns:
            Guide ID if found, None otherwise
        """
        try:
            # Wait for success message
            await self.page.wait_for_selector(self.SUCCESS_MESSAGE, timeout=5000)
            
            # Get ID from the success message: "ID гида: <strong>123</strong>"
            id_element = await self.page.query_selector("p.text-sm strong")
            if id_element:
                id_text = await id_element.text_content()
                guide_id = int(id_text)
                return guide_id
            
            return None
            
        except Exception:
            return None
    
    async def wait_for_guide_success(self) -> bool:
        """
        Wait for guide creation success message.
        
        Returns:
            True if success message appeared, False otherwise
        """
        try:
            await self.page.wait_for_selector(self.SUCCESS_MESSAGE, timeout=10000)
            return True
        except:
            return False
    
    async def has_photo_gallery(self) -> bool:
        """
        Check if photo gallery section is present on guide page.
        
        Returns:
            True if photo gallery exists
        """
        gallery = self.page.locator(self.PHOTO_GALLERY_SECTION)
        return await gallery.count() > 0
    
    async def get_photo_thumbnails_count(self) -> int:
        """
        Get the number of photo thumbnails displayed in gallery.
        
        Returns:
            Number of thumbnails
        """
        thumbnails = self.page.locator(self.PHOTO_THUMBNAIL)
        return await thumbnails.count()
    
    async def click_photo_thumbnail(self, index: int = 0) -> None:
        """
        Click on a photo thumbnail to open lightbox.
        
        Args:
            index: Index of thumbnail to click (0-based)
        """
        thumbnail = self.page.locator(self.PHOTO_THUMBNAIL).nth(index)
        await thumbnail.click()
        await self.page.wait_for_timeout(500)
    
    async def is_lightbox_open(self) -> bool:
        """
        Check if photo lightbox is currently open.
        
        Returns:
            True if lightbox is visible
        """
        lightbox = self.page.locator(self.LIGHTBOX_DIALOG)
        return await lightbox.is_visible()
    
    async def get_lightbox_counter_text(self) -> str:
        """
        Get the current lightbox counter text (e.g., '1 / 15').
        
        Returns:
            Counter text
        """
        counter = self.page.locator(self.LIGHTBOX_COUNTER).first
        if await counter.is_visible():
            text = await counter.text_content()
            return text.strip() if text else ""
        return ""
    
    async def verify_lightbox_counter(self, current: int, total: int) -> bool:
        """
        Verify lightbox counter shows expected values.
        
        Args:
            current: Expected current photo number
            total: Expected total photos count
            
        Returns:
            True if counter matches expected
        """
        counter_text = await self.get_lightbox_counter_text()
        expected = f"{current} / {total}"
        return counter_text == expected
    
    async def navigate_lightbox_next(self) -> None:
        """
        Navigate to next photo in lightbox.
        """
        next_btn = self.page.locator(self.LIGHTBOX_NEXT_BUTTON)
        await next_btn.click()
        await self.page.wait_for_timeout(300)
    
    async def navigate_lightbox_prev(self) -> None:
        """
        Navigate to previous photo in lightbox.
        """
        prev_btn = self.page.locator(self.LIGHTBOX_PREV_BUTTON)
        await prev_btn.click()
        await self.page.wait_for_timeout(300)
    
    async def close_lightbox(self) -> None:
        """
        Close the photo lightbox.
        """
        close_btn = self.page.locator(self.LIGHTBOX_CLOSE_BUTTON)
        await close_btn.click()
        await self.page.wait_for_timeout(500)
