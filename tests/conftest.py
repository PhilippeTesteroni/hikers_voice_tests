"""
E2E test configuration for Hiker's Voice.
Provides Playwright fixtures and E2E specific settings.
"""

import asyncio
import logging
from typing import AsyncGenerator, Generator, Dict, Any
from pathlib import Path

import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright

logger = logging.getLogger("hikers.tests.pages")


@pytest_asyncio.fixture(scope="function")
async def playwright_instance() -> AsyncGenerator[Playwright, None]:
    """Create a Playwright instance for the test."""
    async with async_playwright() as playwright:
        yield playwright


@pytest_asyncio.fixture(scope="function")
async def browser(
    playwright_instance: Playwright,
    config_for_tests: Dict[str, Any]
) -> AsyncGenerator[Browser, None]:
    """
    Create a browser instance with visual mode and slow motion.
    
    Args:
        playwright_instance: Playwright instance
        config_for_tests: Test configuration from command line options
        
    Yields:
        Browser instance
    """
    print("\n=== BROWSER FIXTURE START ===")
    print(f"Config: {config_for_tests}")
    
    logger.info("Launching browser...")
    logger.info(f"Headless mode: {config_for_tests['headless']}")
    logger.info(f"Slow motion: {config_for_tests['slow_mo']}ms")
    
    print("About to launch browser...")
    
    try:
        browser = await playwright_instance.chromium.launch(
            headless=config_for_tests['headless'],
            slow_mo=config_for_tests['slow_mo'],
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
            ]
        )
        print("Browser launched!")
    except Exception as e:
        print(f"ERROR launching browser: {e}")
        raise
    
    logger.info("Browser launched successfully")
    yield browser
    
    logger.info("Closing browser...")
    await browser.close()


@pytest_asyncio.fixture(scope="function")
async def browser_context(
    browser: Browser,
    backend_url: str,
    frontend_url: str,
    config_for_tests: Dict[str, Any]
) -> AsyncGenerator[BrowserContext, None]:
    """
    Create a browser context for each test.
    
    Args:
        browser: Browser instance
        backend_url: Backend API URL
        frontend_url: Frontend URL
        config_for_tests: Test configuration
        
    Yields:
        Browser context
    """
    context_options = {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "base_url": frontend_url,
        "locale": "ru-RU",
        "timezone_id": "Europe/Moscow",
        "color_scheme": "dark",  # Принудительно темная тема
    }
    
    # Add storage state if needed for authenticated tests
    storage_state_file = Path("tests/auth_state.json")
    if storage_state_file.exists():
        context_options["storage_state"] = str(storage_state_file)
    
    context = await browser.new_context(**context_options)
    
    # Set up request/response logging
    context.on("request", lambda request: logger.debug(f"Request: {request.method} {request.url}"))
    context.on("response", lambda response: logger.debug(f"Response: {response.status} {response.url}"))
    
    yield context
    
    await context.close()


@pytest_asyncio.fixture(scope="function")
async def page(
    browser_context: BrowserContext,
    request: pytest.FixtureRequest
) -> AsyncGenerator[Page, None]:
    """
    Create a page for each test with viewport 1920x1080.
    
    Args:
        browser_context: Browser context
        request: Pytest request object for test metadata
        
    Yields:
        Page instance
    """
    page = await browser_context.new_page()
    
    # Set default timeout
    page.set_default_timeout(30000)  # 30 seconds
    page.set_default_navigation_timeout(30000)
    
    # Add console message handler
    page.on("console", lambda msg: logger.debug(f"Console {msg.type}: {msg.text}"))
    
    # Add page error handler
    page.on("pageerror", lambda error: logger.error(f"Page error: {error}"))
    
    yield page


@pytest_asyncio.fixture(scope="function")
async def api_client(backend_url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Create an API client for making test API calls.
    
    Args:
        backend_url: Backend API URL
        
    Yields:
        API client configuration
    """
    import httpx
    
    async with httpx.AsyncClient(
        base_url=backend_url,
        timeout=30.0,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    ) as client:
        yield {
            "client": client,
            "base_url": backend_url,
        }


@pytest.fixture(scope="function")
def review_test_data() -> Dict[str, Any]:
    """
    Provide basic test data for E2E tests.
    
    Returns:
        Dictionary with test data
    """
    from fixtures.test_data import get_review_test_data
    return get_review_test_data()


# Import test images fixtures
pytest_plugins = ["fixtures.test_images_fixtures"]


@pytest_asyncio.fixture(scope="function")
async def clean_test_review(backend_url: str):
    """
    Fixture to track and clean up test reviews created during tests.
    Uses admin panel endpoint for deletion.
    Test MUST fail if cleanup fails - no fallbacks.
    
    Args:
        backend_url: Backend API URL
        
    Yields:
        List to track review IDs
    """
    import httpx
    import base64
    
    # Admin credentials - EXACTLY as in backend
    ADMIN_USERNAME = "Philippe_testeroni"
    ADMIN_PASSWORD = "KeklikG0nnaKek!"
    
    # Create Basic Auth header
    credentials = f"{ADMIN_USERNAME}:{ADMIN_PASSWORD}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode('ascii')
    auth_headers = {"Authorization": f"Basic {encoded_credentials}"}
    
    review_ids = []
    yield review_ids
    
    # Cleanup: Delete test reviews using admin panel endpoint
    # This runs even if test fails, ensuring no test data accumulation
    if review_ids:
        logger.info(f"Cleaning up {len(review_ids)} test reviews: {review_ids}")
        
        async with httpx.AsyncClient(base_url=backend_url, timeout=10.0, follow_redirects=False) as client:
            for review_id in review_ids:
                try:
                    # Use admin panel endpoint: POST /admin/review/{id}/delete
                    response = await client.post(
                        f"/admin/review/{review_id}/delete",
                        headers=auth_headers
                    )
                    
                    # 303 See Other is the expected response (redirect after deletion)
                    if response.status_code == 303:
                        logger.info(f"Cleaned up review {review_id}")
                    elif response.status_code == 404:
                        # Review already deleted (by test itself) - this is OK
                        logger.info(f"Review {review_id} already deleted")
                    elif response.status_code == 401:
                        # Authentication failed - critical error
                        logger.error(f"Failed to authenticate with admin panel for review {review_id}")
                        pytest.fail(
                            f"CRITICAL: Failed to authenticate with admin panel. "
                            f"Check admin credentials: {ADMIN_USERNAME}"
                        )
                    else:
                        # ANY other status code = failure, no exceptions
                        logger.error(f"Failed to delete review {review_id}: HTTP {response.status_code}")
                        logger.error(f"Response headers: {dict(response.headers)}")
                        
                        # ALWAYS fail the test - no fallbacks, no alternatives
                        pytest.fail(
                            f"CLEANUP FAILED: Could not delete test review {review_id}. "
                            f"HTTP Status: {response.status_code}. "
                            f"Expected: 303 (redirect after delete) or 404 (already deleted). "
                            f"\n\nThis will cause test data accumulation! "
                            f"\n\nManual cleanup required: "
                            f"POST http://localhost:8000/admin/review/{review_id}/delete"
                        )
                        
                except Exception as e:
                    logger.error(f"Exception while deleting review {review_id}: {e}")
                    
                    # ANY exception = failure, no fallbacks
                    pytest.fail(
                        f"CLEANUP FAILED: Exception when deleting test review {review_id}. "
                        f"Error: {e}. "
                        f"\n\nThis will cause test data accumulation! "
                        f"\n\nManual cleanup required: "
                        f"POST http://localhost:8000/admin/review/{review_id}/delete"
                    )
    else:
        logger.info("No test reviews to clean up")


@pytest_asyncio.fixture(scope="function")
async def clean_test_guide(backend_url: str):
    """
    Fixture to track and clean up test guides created during tests.
    
    Usage:
        created_guide_id = None
        async with clean_test_guide(backend_url) as guide_ids:
            # Create guide
            created_guide_id = await create_guide()
            guide_ids.append(created_guide_id)
            # Test continues...
        # Cleanup happens automatically
    
    Args:
        backend_url: Backend API URL
        
    Yields:
        List to track guide IDs for cleanup
    """
    from utils.test_helper import TestHelper
    
    test_helper = TestHelper(backend_url)
    guide_ids = []
    
    yield guide_ids
    
    # Cleanup: Delete test guides
    if guide_ids:
        logger.info(f"Cleaning up {len(guide_ids)} test guides: {guide_ids}")
        
        for guide_id in guide_ids:
            deleted = await test_helper.delete_guide(guide_id)
            if not deleted:
                pytest.fail(
                    f"CLEANUP FAILED: Could not delete test guide {guide_id}. "
                    f"This will cause test data accumulation!"
                )
        
        await test_helper.close()
        logger.info(f"✓ All test guides cleaned up")
    else:
        logger.info("No test guides to clean up")


