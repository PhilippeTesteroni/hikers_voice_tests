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
