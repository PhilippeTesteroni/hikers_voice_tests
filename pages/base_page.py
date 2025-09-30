"""
Base Page Object class for all pages in Hiker's Voice.
Provides common methods and error handling.
"""

import logging
from typing import Optional, Any, Dict
from pathlib import Path
from playwright.async_api import Page, ElementHandle, Locator
import asyncio

logger = logging.getLogger("hikers.tests.pages.pages")


class BasePage:
    """
    Base class for all Page Objects.
    
    Provides common functionality for interacting with web pages,
    including wait methods, validation, and error handling.
    """
    
    def __init__(self, page: Page, base_url: str = "http://localhost:3000"):
        """
        Initialize BasePage.
        
        Args:
            page: Playwright Page instance
            base_url: Base URL of the application
        """
        self.page = page
        self.base_url = base_url
        self.logger = logger
        
    async def wait_for_load(self, timeout: int = 30000) -> None:
        """
        Wait for page to be fully loaded.
        
        Args:
            timeout: Maximum wait time in milliseconds
        """
        try:
            # Wait for network to be idle
            await self.page.wait_for_load_state("networkidle", timeout=timeout)
            # Additional wait for React/Next.js hydration
            await self.page.wait_for_timeout(1000)
            # Wait for any loading indicators to disappear
            await self.page.wait_for_function(
                "document.fonts.ready.then(() => true)",
                timeout=5000
            )

        except Exception as e:
            self.logger.error(f"Page load timeout: {e}")
            raise
    
    async def click_and_wait(
        self,
        selector: str,
        wait_for: Optional[str] = None,
        timeout: int = 10000
    ) -> None:
        """
        Click an element and wait for navigation or selector.
        
        Args:
            selector: Element selector to click
            wait_for: Optional selector to wait for after click
            timeout: Maximum wait time in milliseconds
        """
        try:
            # Click the element
            await self.page.click(selector, timeout=timeout)
            
            # Wait for navigation or specific element
            if wait_for:
                await self.page.wait_for_selector(wait_for, timeout=timeout)

            else:
                await self.page.wait_for_load_state("networkidle", timeout=timeout)
                
        except Exception as e:
            self.logger.error(f"Click and wait failed: {e}")
            raise
    
    async def fill_and_validate(
        self,
        selector: str,
        value: str,
        validate: bool = True,
        timeout: int = 5000
    ) -> None:
        """
        Fill input field and validate the value was set correctly.
        
        Args:
            selector: Input field selector
            value: Value to fill
            validate: Whether to validate after filling
            timeout: Maximum wait time in milliseconds
        """
        try:
            # Clear and fill the field
            await self.page.fill(selector, "", timeout=timeout)
            await self.page.fill(selector, value, timeout=timeout)
            
            # Validate if requested
            if validate:
                actual_value = await self.page.input_value(selector, timeout=timeout)
                if actual_value != value:
                    raise ValueError(
                        f"Field validation failed. Expected: {value[:20]}..., "
                        f"Got: {actual_value[:20]}..."
                    )

                
        except Exception as e:
            self.logger.error(f"Fill and validate failed: {e}")
            raise
    
    async def check_url(self, expected_path: str, timeout: int = 10000) -> bool:
        """
        Check if current URL matches expected path.
        
        Args:
            expected_path: Expected URL path (relative to base_url)
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if URL matches, False otherwise
        """
        try:
            expected_url = f"{self.base_url}{expected_path}"
            
            # Wait for URL to match
            await self.page.wait_for_url(expected_url, timeout=timeout)
            
            current_url = self.page.url

            return True
            
        except Exception as e:
            current_url = self.page.url
            self.logger.error(f"URL mismatch. Expected: {expected_path}, Current: {current_url}")
            return False
    

    
    async def wait_for_element(
        self,
        selector: str,
        state: str = "visible",
        timeout: int = 10000
    ) -> Locator:
        """
        Wait for element to be in specified state.
        
        Args:
            selector: Element selector
            state: Expected state (visible, hidden, attached, detached)
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Element locator
        """
        try:
            element = self.page.locator(selector)
            await element.wait_for(state=state, timeout=timeout)

            return element
            
        except Exception as e:
            self.logger.error(f"Wait for element failed: {selector}")
            raise
    
    async def get_text(self, selector: str, timeout: int = 5000) -> str:
        """
        Get text content of an element.
        
        Args:
            selector: Element selector
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Element text content
        """
        try:
            element = await self.wait_for_element(selector, timeout=timeout)
            text = await element.text_content()
            return text or ""
            
        except Exception as e:
            self.logger.error(f"Failed to get text from {selector}: {e}")
            raise
    
    async def is_element_visible(self, selector: str, timeout: int = 1000) -> bool:
        """
        Check if element is visible on the page.
        
        Args:
            selector: Element selector
            timeout: Maximum wait time in milliseconds
            
        Returns:
            True if element is visible, False otherwise
        """
        try:
            element = self.page.locator(selector)
            await element.wait_for(state="visible", timeout=timeout)
            return True
        except:
            return False
    
    async def scroll_to_element(self, selector: str) -> None:
        """
        Scroll to make element visible in viewport.
        
        Args:
            selector: Element selector
        """
        try:
            await self.page.locator(selector).scroll_into_view_if_needed()

        except Exception as e:
            self.logger.error(f"Failed to scroll to element: {e}")
            raise
    
    async def wait_for_api_response(
        self,
        url_pattern: str,
        timeout: int = 10000
    ) -> Dict[str, Any]:
        """
        Wait for specific API response.
        
        Args:
            url_pattern: URL pattern to match
            timeout: Maximum wait time in milliseconds
            
        Returns:
            Response data
        """
        try:
            async with self.page.expect_response(
                lambda response: url_pattern in response.url,
                timeout=timeout
            ) as response_info:
                response = await response_info.value
                data = await response.json()

                return data
        except Exception as e:
            self.logger.error(f"Failed to wait for API response: {e}")
            raise
    
    async def handle_dialog(self, accept: bool = True, text: Optional[str] = None) -> None:
        """
        Handle JavaScript dialogs (alert, confirm, prompt).
        
        Args:
            accept: Whether to accept or dismiss the dialog
            text: Optional text to enter (for prompts)
        """
        async def dialog_handler(dialog):

            if accept:
                await dialog.accept(text)
            else:
                await dialog.dismiss()
        
        self.page.on("dialog", dialog_handler)
