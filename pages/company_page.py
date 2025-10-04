"""
Page Object for company-related pages (companies list, individual company, new company form).
Handles company listing, creation, and viewing operations.
"""

from typing import Optional, Dict, Any
from playwright.async_api import Page
from pages.base_page import BasePage
import logging

logger = logging.getLogger(__name__)


class CompanyPage(BasePage):
    """Page Object for company-related pages."""
    
    # Selectors for company list page
    COMPANIES_LIST = ".space-y-6"  # Основной контейнер списка компаний
    ADD_COMPANY_BUTTON = "text=Добавить компанию"
    COMPANY_CARD = "article.card"  # Карточка компании
    
    # Selectors for new company form
    COMPANY_NAME_INPUT = "input#name"
    COUNTRY_SELECT = "select#country_code"
    DESCRIPTION_TEXTAREA = "textarea#description"
    EMAIL_INPUT = "input#contact_email"
    PHONE_INPUT = "input#contact_phone"
    WEBSITE_INPUT = "input#contact_website"
    INSTAGRAM_INPUT = "input#contact_instagram"
    TELEGRAM_INPUT = "input#contact_telegram"
    CREATE_COMPANY_BUTTON = "button:has-text('Создать компанию')"
    SUCCESS_MESSAGE = ".bg-green-100"
    ERROR_MESSAGE = ".bg-red-50"
    VIEW_COMPANY_BUTTON = "text=Посмотреть страницу компании"
    
    # Duplicate company warning selectors
    DUPLICATE_WARNING = ".bg-yellow-100"
    DUPLICATE_MESSAGE = "text=Компания уже существует"
    VIEW_EXISTING_COMPANY_BUTTON = "text=Перейти к существующей компании"
    TRY_AGAIN_BUTTON = "text=Попробовать снова"
    
    # Selectors for company details page
    COMPANY_TITLE = "h1"
    COMPANY_COUNTRY = ".flex:has(svg) span.text-lg"
    COMPANY_DESCRIPTION = "p.text-gray-600.text-lg"
    COMPANY_RATING = ".mb-4 svg"
    REVIEWS_COUNT = "text=/\\d+ отзыв/"
    NO_REVIEWS_TEXT = "text=Нет отзывов"
    
    # Contact information selectors
    CONTACT_PHONE = "a[href^='tel:']"
    CONTACT_EMAIL = "a[href^='mailto:']"
    CONTACT_WEBSITE = "a:has-text('Сайт компании')"
    CONTACT_INSTAGRAM = "a[href*='instagram.com']"
    CONTACT_TELEGRAM = "a[href*='t.me']"
    
    # Photo gallery elements
    PHOTO_GALLERY_SECTION = ".card:has-text('Фотографии из отзывов')"
    PHOTO_THUMBNAIL = "button.relative.aspect-square"
    LIGHTBOX_DIALOG = "div[role='dialog']"
    LIGHTBOX_COUNTER = ".absolute.top-4.left-4.text-white"
    LIGHTBOX_CLOSE_BUTTON = "button[aria-label='Закрыть']"
    LIGHTBOX_NEXT_BUTTON = "button[aria-label='Следующее фото']"
    LIGHTBOX_PREV_BUTTON = "button[aria-label='Предыдущее фото']"
    
    def __init__(self, page: Page):
        """Initialize CompanyPage with a Playwright page instance."""
        super().__init__(page)
        self.page = page
    
    async def open_companies_page(self) -> None:
        """Open the companies listing page."""
        await self.page.goto("/companies")
        await self.wait_for_load()
    
    async def open_company_page(self, company_id: int) -> None:
        """
        Open a specific company's page.
        
        Args:
            company_id: ID of the company to open
        """
        await self.page.goto(f"/companies/{company_id}")
        await self.wait_for_load()
    
    async def click_add_company_button(self) -> None:
        """Click the 'Add Company' button."""
        await self.click_and_wait(self.ADD_COMPANY_BUTTON)
    
    async def fill_company_form(self, company_data: Dict[str, Any]) -> None:
        """
        Fill the new company form with provided data.
        
        Args:
            company_data: Dictionary containing company information
        """
        # Fill required fields
        if "name" in company_data:
            await self.fill_and_validate(self.COMPANY_NAME_INPUT, company_data["name"])
            
        if "country_code" in company_data:
            await self.page.select_option(self.COUNTRY_SELECT, company_data["country_code"])
            
        if "description" in company_data:
            await self.fill_and_validate(self.DESCRIPTION_TEXTAREA, company_data["description"])
        
        # Fill optional contact fields
        if "email" in company_data:
            await self.fill_and_validate(self.EMAIL_INPUT, company_data["email"])
            
        if "phone" in company_data:
            await self.fill_and_validate(self.PHONE_INPUT, company_data["phone"])
            
        if "website" in company_data:
            await self.fill_and_validate(self.WEBSITE_INPUT, company_data["website"])
            
        if "instagram" in company_data:
            await self.fill_and_validate(self.INSTAGRAM_INPUT, company_data["instagram"])
            
        if "telegram" in company_data:
            await self.fill_and_validate(self.TELEGRAM_INPUT, company_data["telegram"])
    
    async def submit_company_form(self) -> None:
        """Submit the company creation form."""
        await self.click_and_wait(self.CREATE_COMPANY_BUTTON)
    
    async def get_success_company_id(self) -> Optional[int]:
        """
        Get the company ID from the success message after creation.
        
        Returns:
            Company ID if found, None otherwise
        """
        try:
            # Wait for success message
            await self.page.wait_for_selector(self.SUCCESS_MESSAGE, timeout=5000)
            
            # Get ID from the success message
            id_element = await self.page.query_selector("p.text-sm strong")
            if id_element:
                id_text = await id_element.text_content()
                company_id = int(id_text)
                return company_id
            
            return None
            
        except Exception:
            return None
    
    async def get_current_url(self) -> str:
        """Get the current page URL."""
        return self.page.url
    
    async def get_company_name(self) -> str:
        """Get the company name from the details page."""
        name_element = await self.page.query_selector(self.COMPANY_TITLE)
        if name_element:
            return await name_element.text_content()
        return ""
    
    async def get_company_country(self) -> str:
        """Get the company country from the details page."""
        country_element = await self.page.query_selector(self.COMPANY_COUNTRY)
        if country_element:
            return await country_element.text_content()
        return ""
    
    async def get_company_description(self) -> str:
        """Get the company description from the details page."""
        desc_element = await self.page.query_selector(self.COMPANY_DESCRIPTION)
        if desc_element:
            return await desc_element.text_content()
        return ""
    
    async def get_company_rating(self) -> Optional[float]:
        """Get the company rating value from the details page."""
        try:
            # Look for rating in stats section: <div>Рейтинг</div> followed by <div>X.X/5.0</div>
            # Structure: div.flex > div > div.text-sm with "X.X/5.0"
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
            logger.debug(f"Error getting company rating: {e}")
        return None
    
    async def get_company_reviews_count(self) -> int:
        """Get the number of reviews from the details page."""
        try:
            # Look for "X отзыв(ов)" text in stats section
            import re
            
            # Try to find in stats section with "Отзывы" label
            stats_blocks = await self.page.query_selector_all(".flex.items-center.space-x-3")
            for block in stats_blocks:
                text = await block.text_content()
                if 'Отзывы' in text or 'Отзыв' in text:
                    # Extract number from patterns like "5 отзывов" or "1 отзыв"
                    match = re.search(r'(\d+)\s+отзыв', text)
                    if match:
                        return int(match.group(1))
            
            # Fallback: look for standalone "X отзыв" pattern in page
            page_content = await self.page.content()
            match = re.search(r'(\d+)\s+отзыв', page_content)
            if match:
                return int(match.group(1))
        except Exception as e:
            logger.debug(f"Error getting reviews count: {e}")
        return 0
    
    async def get_company_rating_text(self) -> str:
        """Get the rating text (e.g., '0 отзывов' or '4.5/5.0')."""
        # First check if there's a "Нет отзывов" text
        no_reviews = await self.page.query_selector(self.NO_REVIEWS_TEXT)
        if no_reviews:
            return "Нет отзывов"
        
        # Otherwise, look for reviews count
        reviews_element = await self.page.query_selector(self.REVIEWS_COUNT)
        if reviews_element:
            return await reviews_element.text_content()
        
        return ""
    
    async def get_contact_email(self) -> Optional[str]:
        """Get the contact email if displayed."""
        email_element = await self.page.query_selector(self.CONTACT_EMAIL)
        if email_element:
            return await email_element.text_content()
        return None
    
    async def get_contact_phone(self) -> Optional[str]:
        """Get the contact phone if displayed."""
        phone_element = await self.page.query_selector(self.CONTACT_PHONE)
        if phone_element:
            return await phone_element.text_content()
        return None
    
    async def get_contact_website(self) -> Optional[str]:
        """Get the contact website URL if displayed."""
        website_element = await self.page.query_selector(self.CONTACT_WEBSITE)
        if website_element:
            return await website_element.get_attribute("href")
        return None
    
    async def get_contact_instagram(self) -> Optional[str]:
        """Get the Instagram username if displayed."""
        instagram_element = await self.page.query_selector(self.CONTACT_INSTAGRAM)
        if instagram_element:
            text = await instagram_element.text_content()
            # Remove @ sign if present
            return text.replace("@", "") if text else None
        return None
    
    async def get_contact_telegram(self) -> Optional[str]:
        """Get the Telegram username if displayed."""
        telegram_element = await self.page.query_selector(self.CONTACT_TELEGRAM)
        if telegram_element:
            text = await telegram_element.text_content()
            # Remove @ sign if present
            return text.replace("@", "") if text else None
        return None
    
    async def check_company_in_catalog(self, company_name: str) -> bool:
        """
        Check if a company appears in the companies catalog.
        
        Args:
            company_name: Name of the company to search for
            
        Returns:
            True if company found, False otherwise
        """
        await self.open_companies_page()
        
        # Search for company by name in cards
        company_cards = await self.page.query_selector_all(self.COMPANY_CARD)
        
        for card in company_cards:
            name_elem = await card.query_selector("h3")
            if name_elem:
                name = await name_elem.text_content()
                if company_name in name:
                    return True
        
        return False
    
    async def wait_for_company_success(self) -> bool:
        """
        Wait for company creation success message.
        
        Returns:
            True if success message appeared, False otherwise
        """
        try:
            await self.page.wait_for_selector(self.SUCCESS_MESSAGE, timeout=10000)
            return True
        except:
            return False
    
    async def click_view_company_button(self) -> None:
        """
        Click the 'View company page' button after successful creation.
        Waits for navigation to company page.
        """
        await self.click_and_wait(self.VIEW_COMPANY_BUTTON)
    
    async def get_first_company_name(self) -> str:
        """
        Get the name of the first company from the companies list page.
        
        Returns:
            Name of the first company, or empty string if no companies found
        """
        await self.wait_for_load()
        company_card = await self.page.query_selector(self.COMPANY_CARD)
        
        if company_card:
            name_elem = await company_card.query_selector("h3")
            if name_elem:
                return await name_elem.text_content()
        
        return ""
    
    async def wait_for_duplicate_warning(self) -> bool:
        """
        Wait for duplicate company warning message to appear.
        
        Returns:
            True if duplicate warning appeared, False otherwise
        """
        try:
            await self.page.wait_for_selector(self.DUPLICATE_WARNING, timeout=10000)
            await self.page.wait_for_selector(self.DUPLICATE_MESSAGE, timeout=5000)
            return True
        except:
            return False
    
    async def click_view_existing_company(self) -> None:
        """
        Click the 'View existing company' button on duplicate warning page.
        """
        await self.click_and_wait(self.VIEW_EXISTING_COMPANY_BUTTON)
    
    async def has_photo_gallery(self) -> bool:
        """
        Check if photo gallery section is present on company page.
        
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
    
    # Edit functionality selectors
    EDIT_BUTTON = "button:has-text('Изменение данных компании')"
    EDIT_BUTTON_SHORT = "button:has-text('Редактировать')"
    
    # Edit modal - Stage 1 (master key)
    EDIT_MODAL = "div[role='dialog']"
    MODAL_TITLE_KEY = "text=Подтверждение прав редактирования"
    INFO_MESSAGE = ".bg-blue-50"
    INFO_MESSAGE_DARK = ".dark\\:bg-blue-900"
    MASTER_KEY_INPUT = "input[type='text'].font-mono"
    MASTER_KEY_ERROR = ".text-sm.text-red-600"
    MASTER_KEY_HINT = "text=Мастер-ключ должен быть в формате UUID"
    EDIT_PROCEED_BUTTON = "button[type='submit']:has-text('Редактировать')"
    CANCEL_BUTTON = "button:has-text('Отмена')"
    
    # Edit modal - Stage 2 (edit form)
    MODAL_TITLE_EDIT = "text=Изменение данных компании"
    EDIT_NAME_INPUT = "input[type='text']"
    EDIT_DESCRIPTION_TEXTAREA = "textarea"
    EDIT_EMAIL_INPUT = "input[type='email']"
    EDIT_PHONE_INPUT = "input[type='tel']"
    EDIT_WEBSITE_INPUT = "input[type='url']"
    EDIT_INSTAGRAM_INPUT = "input[placeholder*='@yourcompany']"
    SAVE_BUTTON = "button:has-text('Сохранить изменения')"
    SUBMIT_ERROR = ".bg-red-50"
    SAVING_SPINNER = "text=Сохранение..."
    
    # Success/Error toasts
    SUCCESS_TOAST = ".bg-green-50"
    SUCCESS_TOAST_DARK = ".dark\\:bg-green-900"
    ERROR_TOAST = ".bg-red-50"
    ERROR_TOAST_DARK = ".dark\\:bg-red-900"
    TOAST_TITLE = ".bg-green-50 .text-sm.font-medium, .bg-red-50 .text-sm.font-medium"  # Title inside toast
    TOAST_TEXT = ".bg-green-50 .mt-1.text-sm, .bg-red-50 .mt-1.text-sm"  # Body text inside toast
    TOAST_CLOSE_BUTTON = "button[aria-label='Закрыть уведомление']"
    
    async def click_edit_button(self) -> None:
        """
        Click the edit button on company page.
        Tries both desktop and mobile versions.
        """
        try:
            # Try desktop version first
            await self.page.click(self.EDIT_BUTTON, timeout=2000)
        except:
            # Fallback to mobile version
            await self.page.click(self.EDIT_BUTTON_SHORT)
        
        # Wait for modal content to appear (more reliable for Headless UI modals)
        # Headless UI Dialog doesn't become 'visible' immediately due to CSS transitions
        await self.page.wait_for_selector(
            "text=Подтверждение прав редактирования",
            state="visible",
            timeout=5000
        )
        await self.page.wait_for_timeout(300)
    
    async def is_edit_modal_open(self) -> bool:
        """
        Check if edit modal is currently open.
        
        Returns:
            True if modal is visible
        """
        # Check by modal title text instead of dialog wrapper (more reliable with Headless UI)
        title = self.page.locator("text=Подтверждение прав редактирования")
        try:
            return await title.is_visible()
        except:
            return False
    
    async def get_info_message_text(self) -> str:
        """
        Get the text from the informational message in master key step.
        
        Returns:
            Info message text
        """
        # Try light mode selector first
        info_elem = await self.page.query_selector(self.INFO_MESSAGE)
        if info_elem:
            text = await info_elem.text_content()
            return text.strip() if text else ""
        return ""
    
    async def fill_master_key(self, master_key: str) -> None:
        """
        Fill the master key input field.
        
        Args:
            master_key: UUID master key string
        """
        await self.fill_and_validate(self.MASTER_KEY_INPUT, master_key)
    
    async def get_master_key_error(self) -> Optional[str]:
        """
        Get the master key validation error message if present.
        
        Returns:
            Error text or None
        """
        error_elem = await self.page.query_selector(self.MASTER_KEY_ERROR)
        if error_elem:
            text = await error_elem.text_content()
            return text.strip() if text else None
        return None
    
    async def is_edit_proceed_button_enabled(self) -> bool:
        """
        Check if the 'Редактировать' button is enabled.
        
        Returns:
            True if button is enabled
        """
        button = self.page.locator(self.EDIT_PROCEED_BUTTON)
        is_disabled = await button.is_disabled()
        return not is_disabled
    
    async def click_edit_proceed_button(self) -> None:
        """
        Click the 'Редактировать' button to proceed to edit form.
        """
        await self.page.click(self.EDIT_PROCEED_BUTTON)
        # Wait for form to load
        await self.page.wait_for_selector(self.MODAL_TITLE_EDIT, state="visible", timeout=5000)
        await self.page.wait_for_timeout(300)
    
    async def fill_edit_form(self, data: Dict[str, Any]) -> None:
        """
        Fill the company edit form with provided data.
        Only fills fields that are present in data dict.
        
        Args:
            data: Dictionary with fields to update (name, description, email, etc.)
        """
        if "name" in data:
            # Clear and fill name input
            name_input = self.page.locator(self.EDIT_NAME_INPUT).first
            await name_input.clear()
            await name_input.fill(data["name"])
        
        if "description" in data:
            desc_textarea = self.page.locator(self.EDIT_DESCRIPTION_TEXTAREA)
            await desc_textarea.clear()
            await desc_textarea.fill(data["description"])
        
        if "email" in data:
            email_input = self.page.locator(self.EDIT_EMAIL_INPUT)
            await email_input.clear()
            await email_input.fill(data["email"])
        
        if "phone" in data:
            phone_input = self.page.locator(self.EDIT_PHONE_INPUT)
            await phone_input.clear()
            await phone_input.fill(data["phone"])
        
        if "website" in data:
            website_input = self.page.locator(self.EDIT_WEBSITE_INPUT)
            await website_input.clear()
            await website_input.fill(data["website"])
        
        if "instagram" in data:
            instagram_input = self.page.locator(self.EDIT_INSTAGRAM_INPUT).first
            await instagram_input.clear()
            await instagram_input.fill(data["instagram"])
        
        if "telegram" in data:
            telegram_input = self.page.locator(self.EDIT_INSTAGRAM_INPUT).nth(1)
            await telegram_input.clear()
            await telegram_input.fill(data["telegram"])
    
    async def submit_edit_form(self) -> None:
        """
        Submit the edit form by clicking 'Сохранить изменения' button.
        Waits for navigation or error response.
        """
        # Click submit button
        await self.page.click(self.SAVE_BUTTON)
        
        # Wait for navigation to complete (redirect with success/error param)
        # or for error toast to appear if validation fails
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10000)
        except:
            # If networkidle timeout, wait a bit more
            await self.page.wait_for_timeout(2000)
    
    async def wait_for_success_toast(self, timeout: int = 10000) -> bool:
        """
        Wait for success toast to appear.
        
        Args:
            timeout: Timeout in milliseconds
        
        Returns:
            True if toast appeared
        """
        try:
            await self.page.wait_for_selector(self.SUCCESS_TOAST, state="visible", timeout=timeout)
            return True
        except:
            return False
    
    async def wait_for_error_toast(self, timeout: int = 10000) -> bool:
        """
        Wait for error toast to appear.
        
        Args:
            timeout: Timeout in milliseconds
        
        Returns:
            True if toast appeared
        """
        try:
            await self.page.wait_for_selector(self.ERROR_TOAST, state="visible", timeout=timeout)
            return True
        except:
            return False
    
    async def get_toast_title(self) -> str:
        """
        Get the title text from the toast notification.
        
        Returns:
            Toast title text
        """
        title_elem = await self.page.query_selector(self.TOAST_TITLE)
        if title_elem:
            text = await title_elem.text_content()
            return text.strip() if text else ""
        return ""
    
    async def get_toast_text(self) -> str:
        """
        Get the body text from the toast notification.
        
        Returns:
            Toast body text
        """
        text_elem = await self.page.query_selector(self.TOAST_TEXT)
        if text_elem:
            text = await text_elem.text_content()
            return text.strip() if text else ""
        return ""
    
    async def close_toast(self) -> None:
        """
        Close the toast notification by clicking the X button.
        """
        try:
            await self.page.click(self.TOAST_CLOSE_BUTTON, timeout=2000)
            await self.page.wait_for_timeout(300)
        except:
            # Toast might have auto-closed
            pass
    
    async def check_url_has_success_param(self, expected_value: str) -> bool:
        """
        Check if URL contains success parameter with expected value.
        
        Args:
            expected_value: Expected value (e.g., 'company_updated')
        
        Returns:
            True if URL has correct success parameter
        """
        current_url = await self.get_current_url()
        return f"success={expected_value}" in current_url
    
    async def check_url_has_error_param(self, expected_value: str) -> bool:
        """
        Check if URL contains error parameter with expected value.
        
        Args:
            expected_value: Expected value (e.g., 'invalid_master_key')
        
        Returns:
            True if URL has correct error parameter
        """
        current_url = await self.get_current_url()
        return f"error={expected_value}" in current_url
