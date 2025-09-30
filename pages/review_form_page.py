"""
Page Object for Review Form Pages in Hiker's Voice.
Handles tour, company, and guide review forms.
"""

from typing import Dict, Any, Optional, List
from playwright.async_api import Page
from pages.base_page import BasePage


class ReviewFormPage(BasePage):
    """
    Page Object for Review Form Pages.
    
    Handles all types of review forms: tour, company, and guide reviews,
    including form filling, validation, and submission.
    """
    
    # Review type selection modal
    REVIEW_TYPE_MODAL = "[role='dialog']"
    REVIEW_TYPE_MODAL_TITLE = "#modal-title"
    REVIEW_TYPE_MODAL_PANEL = ".fixed.inset-0 [role='dialog'] .transform"  # Dialog.Panel внутри модалки
    COMPANY_REVIEW_BUTTON = "button:has-text('Отзыв о компании')"
    GUIDE_REVIEW_BUTTON = "button:has-text('Отзыв о гиде')"
    MODAL_CLOSE_BUTTON = "button[aria-label='Закрыть модальное окно']"
    
    # Common form fields
    AUTHOR_NAME_INPUT = "input[name='author_name'], input[placeholder*='Ваше имя']"
    AUTHOR_CONTACT_INPUT = "input[name='author_contact'], input[placeholder*='Контакт']"
    CONTENT_TEXTAREA = "textarea[name='text'], textarea[placeholder*='Расскажите']"
    RATING_STARS = "[role='radiogroup']"
    RATING_STAR = "button[aria-label*='Оценка']"
    
    # Tour review specific fields
    TOUR_NAME_INPUT = "input[name='tour_name'], input[placeholder*='Название тура']"
    TOUR_DATE_INPUT = "input[name='tour_date'], input[type='date']"
    TOUR_DURATION_INPUT = "input[name='duration'], input[placeholder*='Длительность']"
    TOUR_DIFFICULTY_SELECT = "select[name='difficulty'], [data-testid='difficulty-select']"
    TOUR_TYPE_SELECT = "select[name='tour_type'], [data-testid='tour-type-select']"
    
    # Company review specific fields 
    COUNTRY_SELECT = "select[name='country_code']"
    COMPANY_NAME_INPUT = "input[placeholder*='Начните вводить название компании']"
    COMPANY_AUTOCOMPLETE = ".dropdown"
    COMPANY_AUTOCOMPLETE_ITEM = ".dropdown-item"
    TRIP_DATE_FROM = "input[name='trip_date_from']"
    TRIP_DATE_TO = "input[name='trip_date_to']"
    
    # Guide review specific fields
    GUIDE_SELECT = "select[name='guide_id'], [data-testid='guide-select']"
    GUIDE_NAME_INPUT = "input[placeholder*='Начните вводить имя гида']"
    GUIDE_AUTOCOMPLETE = ".dropdown"
    GUIDE_AUTOCOMPLETE_ITEM = ".dropdown-item"
    GUIDE_LANGUAGES_INPUT = "input[name='languages'], input[placeholder*='Языки']"
    GUIDE_SPECIALIZATION_INPUT = "input[name='specialization'], input[placeholder*='Специализация']"
    GUIDE_EXPERIENCE_RATING = "[data-testid='experience-rating']"
    GUIDE_COMMUNICATION_RATING = "[data-testid='communication-rating']"
    
    # Photos upload
    PHOTO_UPLOAD_INPUT = "input[type='file'][accept*='image']"
    PHOTO_PREVIEW = ".photo-preview, [data-testid='photo-preview']"
    REMOVE_PHOTO_BUTTON = "button[aria-label='Remove photo'], .remove-photo"
    
    # Rules and agreement
    RULES_CHECKBOX = "input[name='rules_accepted']"
    RULES_LABEL = "label[for='rules_accepted']"
    
    # CAPTCHA (auto-passed in dev mode)
    CAPTCHA_CONTAINER = ".captcha, [data-testid='captcha']"
    CAPTCHA_INPUT = "input[name='captcha'], input[placeholder*='captcha']"
    
    # Form actions
    SUBMIT_BUTTON = "button[type='submit']:has-text('Отправить отзыв')"
    CANCEL_BUTTON = "button:has-text('Отмена')"
    
    # Validation messages
    ERROR_MESSAGE = ".field-error, .error-message, [role='alert']"
    FIELD_ERROR = ".field-error, .invalid-feedback"
    SUCCESS_MESSAGE = ".success-message, [data-testid='success-message']"
    
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize ReviewFormPage.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL of the application
        """
        super().__init__(page, base_url)
        
    async def wait_for_modal(self) -> None:
        """
        Wait for review type selection modal to appear and be visible.
        """
        # Wait for modal animation
        await self.page.wait_for_timeout(800)
        
        # Wait for modal title to be visible
        await self.page.wait_for_selector("text=Выберите тип отзыва", state="visible", timeout=5000)
        
        # Verify company button is also visible
        company_button_visible = await self.page.locator(self.COMPANY_REVIEW_BUTTON).is_visible()
        assert company_button_visible, "Company review button not visible in modal"
        
        # Additional pause for stability
        await self.page.wait_for_timeout(200)

    
    async def select_review_type_in_modal(self, review_type: str) -> None:
        """
        Select the type of review in the modal window.
        
        Args:
            review_type: Type of review ('company' or 'guide')
        """
        # Wait for modal to be ready
        await self.wait_for_modal()
        
        if review_type.lower() == 'company':
            await self.page.click(self.COMPANY_REVIEW_BUTTON)
        elif review_type.lower() == 'guide':
            await self.page.click(self.GUIDE_REVIEW_BUTTON)
        else:
            raise ValueError(f"Invalid review type: {review_type}")
        
        # Wait for navigation to complete
        await self.page.wait_for_load_state("networkidle")

    
    async def fill_common_fields(self, data: Dict[str, Any]) -> None:
        """
        Fill common review fields present in all review types.
        
        Args:
            data: Dictionary with field values
        """

        
        # Fill author information
        if 'author_name' in data:
            await self.fill_and_validate(self.AUTHOR_NAME_INPUT, data['author_name'])
        
        if 'author_contact' in data:
            await self.fill_and_validate(self.AUTHOR_CONTACT_INPUT, data['author_contact'])
        
        # Fill review content (text field)
        if 'text' in data:
            await self.fill_and_validate(self.CONTENT_TEXTAREA, data['text'])
        elif 'content' in data:  # Fallback for old field name
            await self.fill_and_validate(self.CONTENT_TEXTAREA, data['content'])
        
        # Set rating
        if 'rating' in data:
            await self.set_rating(data['rating'])
        
        # Check rules if needed
        if 'rules_accepted' in data and data['rules_accepted']:
            await self.accept_rules()
    
    async def fill_tour_review(self, data: Dict[str, Any]) -> None:
        """
        Fill tour review specific fields.
        
        Args:
            data: Dictionary with tour review data
        """

        
        # Select tour review type
        await self.select_review_type('tour')
        
        # Fill common fields
        await self.fill_common_fields(data)
        
        # Fill tour-specific fields
        if 'tour_name' in data:
            await self.fill_and_validate(self.TOUR_NAME_INPUT, data['tour_name'])
        
        if 'tour_date' in data:
            await self.fill_and_validate(self.TOUR_DATE_INPUT, data['tour_date'])
        
        if 'duration' in data:
            await self.fill_and_validate(self.TOUR_DURATION_INPUT, str(data['duration']))
        
        if 'difficulty' in data:
            await self.page.select_option(self.TOUR_DIFFICULTY_SELECT, data['difficulty'])
        
        if 'tour_type' in data:
            await self.page.select_option(self.TOUR_TYPE_SELECT, data['tour_type'])
    
    async def fill_company_review(self, data: Dict[str, Any]) -> None:
        """
        Fill company review specific fields.
        
        Args:
            data: Dictionary with company review data
        """

        
        # Fill common fields
        await self.fill_common_fields(data)
        
        # Select country
        if 'country_code' in data:
            await self.page.select_option(self.COUNTRY_SELECT, data['country_code'])

        
        # Fill company name with autocomplete
        if 'company_name' in data:
            if data.get('select_autocomplete', False):
                await self.fill_company_name_with_autocomplete(data['company_name'])
            else:
                await self.page.fill(self.COMPANY_NAME_INPUT, data['company_name'])
        
        # Fill trip dates
        if 'trip_date_from' in data:
            await self.fill_and_validate(self.TRIP_DATE_FROM, data['trip_date_from'])
        
        if 'trip_date_to' in data:
            await self.fill_and_validate(self.TRIP_DATE_TO, data['trip_date_to'])
    
    async def select_country(self, country_code: str) -> None:
        """
        Select country from dropdown.
        
        Args:
            country_code: Country code to select (e.g., 'GE' for Georgia)
        """
        await self.page.select_option(self.COUNTRY_SELECT, country_code)
    
    async def fill_company_name_with_autocomplete(self, search_text: str) -> None:
        """
        Fill company name using autocomplete dropdown.
        Searches for company and selects first match.
        
        Args:
            search_text: Text to search for in company names
        """
        # Clear and type search text
        company_input = self.page.locator(self.COMPANY_NAME_INPUT)
        await company_input.clear()
        await company_input.type(search_text, delay=100)
        
        # Wait for dropdown and select first matching item
        await self.page.wait_for_selector(self.COMPANY_AUTOCOMPLETE, timeout=3000)
        dropdown_items = self.page.locator(self.COMPANY_AUTOCOMPLETE_ITEM)
        
        # Find and click the first company with search_text in name
        found = False
        for i in range(await dropdown_items.count()):
            item_text = await dropdown_items.nth(i).text_content()
            if search_text in item_text:
                await dropdown_items.nth(i).click()
                found = True
                break
        
        assert found, f"No company with '{search_text}' found in autocomplete dropdown"
    
    async def fill_trip_dates(self, date_from: str, date_to: str) -> None:
        """
        Fill trip date fields.
        
        Args:
            date_from: Start date in YYYY-MM-DD format
            date_to: End date in YYYY-MM-DD format
        """
        await self.page.fill(self.TRIP_DATE_FROM, date_from)
        await self.page.fill(self.TRIP_DATE_TO, date_to)
    
    async def fill_review_text(self, text: str) -> None:
        """
        Fill review text content.
        
        Args:
            text: Review text
        """
        await self.page.fill(self.CONTENT_TEXTAREA, text)
    
    async def fill_author_info(self, name: str, contact: str) -> None:
        """
        Fill author name and contact information.
        
        Args:
            name: Author name
            contact: Author contact (email or phone)
        """
        if name:  # Only fill if name is not empty
            await self.page.fill(self.AUTHOR_NAME_INPUT, name)
        await self.page.fill(self.AUTHOR_CONTACT_INPUT, contact)
    
    async def fill_guide_name_with_autocomplete(self, search_text: str, select_exact: str = None) -> None:
        """
        Fill guide name using autocomplete dropdown.
        Searches for guide and selects from dropdown.
        
        Args:
            search_text: Text to type in the search field
            select_exact: Exact name to select from dropdown (if None, selects first match)
        """
        # Clear and type search text
        guide_input = self.page.locator(self.GUIDE_NAME_INPUT)
        await guide_input.clear()
        await guide_input.type(search_text, delay=100)
        
        # Wait for dropdown
        await self.page.wait_for_selector(self.GUIDE_AUTOCOMPLETE, timeout=3000)
        await self.page.wait_for_timeout(500)  # Let dropdown fully populate
        
        dropdown_items = self.page.locator(self.GUIDE_AUTOCOMPLETE_ITEM)
        
        # Select the appropriate item
        found = False
        for i in range(await dropdown_items.count()):
            item_text = await dropdown_items.nth(i).text_content()
            if select_exact:
                # Select exact match
                if item_text and select_exact in item_text:
                    await dropdown_items.nth(i).click()
                    found = True
                    break
            else:
                # Select first item containing search text
                if item_text and search_text in item_text:
                    await dropdown_items.nth(i).click()
                    found = True
                    break
        
        assert found, f"No guide with '{select_exact or search_text}' found in autocomplete dropdown"
    
    async def fill_guide_review(self, data: Dict[str, Any]) -> None:
        """
        Fill guide review specific fields.
        
        Args:
            data: Dictionary with guide review data
        """

        
        # Select guide review type
        await self.select_review_type('guide')
        
        # Fill common fields
        await self.fill_common_fields(data)
        
        # Select or enter guide
        if 'guide_id' in data:
            await self.page.select_option(self.GUIDE_SELECT, str(data['guide_id']))
        elif 'guide_name' in data:
            # Enter new guide
            await self.fill_and_validate(self.GUIDE_NAME_INPUT, data['guide_name'])
            
            if 'languages' in data:
                languages = ', '.join(data['languages']) if isinstance(data['languages'], list) else data['languages']
                await self.fill_and_validate(self.GUIDE_LANGUAGES_INPUT, languages)
            
            if 'specialization' in data:
                await self.fill_and_validate(self.GUIDE_SPECIALIZATION_INPUT, data['specialization'])
        
        # Set additional ratings
        if 'experience_rating' in data:
            await self.set_rating(data['experience_rating'], self.GUIDE_EXPERIENCE_RATING)
        
        if 'communication_rating' in data:
            await self.set_rating(data['communication_rating'], self.GUIDE_COMMUNICATION_RATING)
    
    async def set_rating(self, rating: int, container_selector: Optional[str] = None) -> None:
        """
        Set star rating value.
        
        Args:
            rating: Rating value (1-5)
            container_selector: Optional specific rating container
        """
        if rating < 1 or rating > 5:
            raise ValueError(f"Rating must be between 1 and 5, got {rating}")
        

        
        # Find the star button with the exact rating
        star_selector = f"button[aria-label='Оценка {rating} из 5 звезд']"
        await self.page.click(star_selector)
        

    
    async def accept_rules(self) -> None:
        """
        Check the rules acceptance checkbox.
        """
        # Check if already checked
        is_checked = await self.page.is_checked(self.RULES_CHECKBOX)
        if not is_checked:
            await self.page.check(self.RULES_CHECKBOX)

    
    async def upload_photos(self, photo_paths: List[str]) -> None:
        """
        Upload photos to the review.
        
        Args:
            photo_paths: List of photo file paths
        """

        
        # Set files to the input
        await self.page.set_input_files(self.PHOTO_UPLOAD_INPUT, photo_paths)
        
        # Wait for previews to appear
        await self.page.wait_for_selector(self.PHOTO_PREVIEW, timeout=5000)
        
        # Verify all photos uploaded
        previews = await self.page.locator(self.PHOTO_PREVIEW).count()
        if previews != len(photo_paths):
            self.logger.error(f"Photo upload mismatch: expected {len(photo_paths)}, got {previews}")
        

    
    async def submit_form(self) -> None:
        """Submit the review form."""
        # Click submit button
        await self.page.click(self.SUBMIT_BUTTON)
        
        # Wait for redirect to home with success parameter
        await self.page.wait_for_url(f"{self.base_url}/?success=review_created", timeout=10000)
    
    async def get_validation_errors(self) -> List[str]:
        """
        Get all validation error messages displayed on the form.
        
        Returns:
            List of error messages
        """
        errors = []
        
        # Get field-level errors
        field_errors = self.page.locator(self.FIELD_ERROR)
        count = await field_errors.count()
        
        for i in range(count):
            error_text = await field_errors.nth(i).text_content()
            if error_text:
                errors.append(error_text.strip())
        
        # Get general error message
        if await self.is_element_visible(self.ERROR_MESSAGE, timeout=1000):
            general_error = await self.get_text(self.ERROR_MESSAGE)
            if general_error and general_error not in errors:
                errors.append(general_error)
        

        return errors
    
    async def validate_field_error(self, field_name: str, expected_error: str) -> bool:
        """
        Validate that a specific field shows expected error.
        
        Args:
            field_name: Name of the field
            expected_error: Expected error message
            
        Returns:
            True if error matches expectation
        """
        # Find error message near the field
        field_selector = f"[name='{field_name}']"
        field = self.page.locator(field_selector)
        
        # Look for error message near the field
        error_near_field = field.locator("..").locator(self.FIELD_ERROR)
        
        if await error_near_field.is_visible():
            actual_error = await error_near_field.text_content()
            return expected_error.lower() in actual_error.lower()
        
        return False
    
    async def cancel_form(self) -> None:
        """Cancel the review form and return to previous page."""

        await self.click_and_wait(self.CANCEL_BUTTON)
    
    async def wait_for_review_form(self) -> None:
        """
        Wait for review form page to be loaded.
        """
        # Wait for key form elements to be visible
        await self.wait_for_element(self.COUNTRY_SELECT, timeout=10000)
        await self.wait_for_element(self.COMPANY_NAME_INPUT, timeout=5000)

