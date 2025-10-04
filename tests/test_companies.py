"""E2E tests for company creation functionality."""

import pytest
import logging
from playwright.async_api import Page
from pages.company_page import CompanyPage
from fixtures.test_data import generate_company_data
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
async def test_create_new_company(
    page: Page,
    backend_url: str,
    clean_test_company: list
):
    """
    TEST-003: Create new company with complete information.
    
    Steps:
    1. Open companies page
    2. Click "Add company" button
    3. Fill form with test data
    4. Submit form
    5. Moderate company via API
    6. Navigate to company page via UI button
    7. Verify company page displays all data correctly
    8. Verify company appears in catalog
    9. Cleanup handled automatically by clean_test_company fixture
    """
    # Arrange
    company_page = CompanyPage(page)
    test_helper = TestHelper(backend_url)
    company_data = generate_company_data()
    
    try:
        # Act - Navigate to new company form
        await company_page.open_companies_page()
        await company_page.click_add_company_button()
        
        # Fill and submit the form
        await company_page.fill_company_form(company_data)
        await company_page.submit_company_form()
        
        # Wait for success and get company ID
        success = await company_page.wait_for_company_success()
        assert success, "Company creation success message did not appear"
        
        created_company_id = await company_page.get_success_company_id()
        assert created_company_id is not None, "Failed to get company ID from success message"
        
        # Track for cleanup
        clean_test_company.append(created_company_id)
        
        # Note: Companies are created as approved, no moderation needed
        
        # Navigate to company page via UI button (more realistic than direct URL)
        await company_page.click_view_company_button()
        
        # Assert - Verify URL changed to company page
        current_url = await company_page.get_current_url()
        assert f"/companies/{created_company_id}" in current_url, f"URL did not change to company page: {current_url}"
        
        # Verify company data is displayed correctly (no ISR cache issues since we just created it)
        displayed_name = await company_page.get_company_name()
        assert displayed_name == company_data["name"], f"Company name mismatch: expected '{company_data['name']}', got '{displayed_name}'"
        
        displayed_country = await company_page.get_company_country()
        assert "Казахстан" in displayed_country, f"Country not displayed correctly: {displayed_country}"
        
        displayed_description = await company_page.get_company_description()
        assert company_data["description"] in displayed_description, "Description not displayed correctly"
        
        # Verify rating shows "Нет отзывов" for new company
        rating_text = await company_page.get_company_rating_text()
        assert "0 отзыв" in rating_text or "Нет отзывов" in rating_text, f"Unexpected rating text: {rating_text}"
        
        # Verify contact information
        displayed_email = await company_page.get_contact_email()
        assert displayed_email == company_data["email"], "Email mismatch"
        
        displayed_phone = await company_page.get_contact_phone()
        assert displayed_phone == company_data["phone"], "Phone mismatch"
        
        displayed_website = await company_page.get_contact_website()
        assert displayed_website == company_data["website"], "Website mismatch"
        
        displayed_instagram = await company_page.get_contact_instagram()
        expected_instagram = company_data["instagram"].replace("@", "")
        assert displayed_instagram == expected_instagram, "Instagram mismatch"
        
        displayed_telegram = await company_page.get_contact_telegram()
        expected_telegram = company_data["telegram"].replace("@", "")
        assert displayed_telegram == expected_telegram, "Telegram mismatch"
        
        # Verify company appears in catalog
        company_in_catalog = await company_page.check_company_in_catalog(company_data["name"])
        assert company_in_catalog, f"Company '{company_data['name']}' not found in catalog"
        
        # Test completed successfully - cleanup will be automatic
        logger.info(f"TEST-003 completed: company_id={created_company_id}, cleanup will be automatic")
        
    finally:
        await test_helper.close()


@pytest.mark.e2e 
async def test_create_company_minimal_data(
    page: Page,
    backend_url: str,
    clean_test_company: list
):
    """
    TEST-003b: Create company with only required fields.
    
    Steps:
    1. Open new company form
    2. Fill only required fields (name, country, description)
    3. Submit and moderate
    4. Verify company created successfully
    5. Cleanup handled automatically by clean_test_company fixture
    """
    # Arrange
    company_page = CompanyPage(page)
    test_helper = TestHelper(backend_url)
    minimal_data = {
        "name": f"Minimal Company {generate_company_data()['name'].split('_')[-1]}",
        "country_code": "RU",
        "description": "Минимальное описание компании для тестирования"
    }
    
    try:
        # Navigate to form
        await company_page.open_companies_page()
        await company_page.click_add_company_button()
        
        # Fill only required fields
        await company_page.fill_company_form(minimal_data)
        await company_page.submit_company_form()
        
        # Get company ID
        success = await company_page.wait_for_company_success()
        assert success, "Company creation failed"
        
        created_company_id = await company_page.get_success_company_id()
        assert created_company_id is not None, "Failed to get company ID"
        
        # Track for cleanup
        clean_test_company.append(created_company_id)
        
        # Note: Companies are created as approved, no moderation needed
        
        # Verify on company page (ISR cache issue fixed, no retries needed)
        await company_page.open_company_page(created_company_id)
        await page.wait_for_load_state("networkidle")
        
        # Verify company name
        displayed_name = await company_page.get_company_name()
        assert displayed_name == minimal_data["name"], \
            f"Company name mismatch. Expected '{minimal_data['name']}', got '{displayed_name}'"
        
        # Verify no contact info is displayed
        displayed_email = await company_page.get_contact_email()
        assert displayed_email is None, "Email should not be displayed when not provided"
        
        logger.info(f"TEST-003b completed: company_id={created_company_id}, cleanup will be automatic")
        
    finally:
        await test_helper.close()


@pytest.mark.e2e
async def test_company_validation_errors(
    page: Page
):
    """
    TEST-003c: Test form validation for company creation.
    
    Steps:
    1. Open new company form
    2. Try to submit empty form
    3. Verify validation errors appear
    4. Fill invalid data
    5. Verify appropriate error messages
    """
    # Arrange
    company_page = CompanyPage(page)
    
    # Navigate to form
    await company_page.open_companies_page()
    await company_page.click_add_company_button()
    
    # Try to submit empty form
    await company_page.submit_company_form()
    
    # Check for validation errors
    await page.wait_for_timeout(1000)  # Wait for validation
    
    # Verify required field errors are visible
    name_error = await page.query_selector("text=Название компании обязательно")
    assert name_error is not None, "Name validation error not shown"
    
    country_error = await page.query_selector("text=Выберите страну")
    assert country_error is not None, "Country validation error not shown"
    
    description_error = await page.query_selector("text=Описание должно содержать минимум 10 символов")
    assert description_error is not None, "Description validation error not shown"
    
    # Test invalid email format
    invalid_data = {
        "name": "Test Company",
        "country_code": "RU", 
        "description": "Valid description for testing",
        "email": "invalid-email-format"
    }
    
    await company_page.fill_company_form(invalid_data)
    await company_page.submit_company_form()
    
    await page.wait_for_timeout(1000)
    email_error = await page.query_selector("text=Неверный формат email")
    assert email_error is not None, "Email validation error not shown"
    
    # Test invalid website URL
    await company_page.fill_company_form({"website": "not-a-url"})
    await company_page.submit_company_form()
    
    await page.wait_for_timeout(1000)
    website_error = await page.query_selector("text=Неверный формат URL")
    assert website_error is not None, "Website validation error not shown"
    
    logger.info("TEST-003c completed: Form validation works correctly")


@pytest.mark.e2e
@pytest.mark.critical
async def test_duplicate_company_detection_and_navigation(
    page: Page,
    frontend_url: str,
    frontend_api_client,
    clean_test_company: list
):
    """
    TEST-006 REFACTORED: Test duplicate company detection and navigation to existing company.
    
    Creates unique company via API, then attempts to create duplicate via UI.
    No dependency on seed data.

    Steps:
    1. Create company via API
    2. Navigate to new company form
    3. Fill form with same company name
    4. Submit form
    5. Verify duplicate warning appears with two buttons
    6. Click "View existing company" button
    7. Verify navigation to correct company page
    8. Verify company name matches the original
    9. Cleanup handled automatically

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        frontend_api_client: API client for creating entities
        clean_test_company: Cleanup fixture
    """
    # Step 1: Create company via API
    company = await frontend_api_client.create_company(
        name="Duplicate Detection Company",
        country_code="GE",
        description="Test company for duplicate detection test"
    )
    clean_test_company.append(company["id"])
    
    existing_company_name = company["name"]
    existing_company_id = company["id"]
    
    logger.info(f"Created company via API: ID={existing_company_id}, Name={existing_company_name}")

    # Step 2: Navigate to new company form
    company_page = CompanyPage(page)
    await company_page.open_companies_page()
    await company_page.click_add_company_button()

    # Step 3: Fill form with existing company name and other required fields
    duplicate_company_data = {
        "name": existing_company_name,
        "country_code": "GE",
        "description": "This is a test duplicate company description for testing purposes."
    }

    await company_page.fill_company_form(duplicate_company_data)

    # Step 4: Submit form
    await company_page.submit_company_form()

    # Step 5: Wait for duplicate warning to appear
    duplicate_warning_appeared = await company_page.wait_for_duplicate_warning()
    assert duplicate_warning_appeared, "Duplicate company warning did not appear after submitting duplicate company name"

    # Verify warning message contains company name
    duplicate_message_element = await page.query_selector(company_page.DUPLICATE_MESSAGE)
    assert duplicate_message_element is not None, "Duplicate message element not found"

    # Verify both buttons are present
    view_button = await page.query_selector(company_page.VIEW_EXISTING_COMPANY_BUTTON)
    try_again_button = await page.query_selector(company_page.TRY_AGAIN_BUTTON)

    assert view_button is not None, "'View existing company' button not found"
    assert try_again_button is not None, "'Try again' button not found"

    logger.info("Duplicate warning displayed with both buttons")

    # Step 6: Click "View existing company" button
    await company_page.click_view_existing_company()

    # Step 7: Verify we're on company details page
    await page.wait_for_url("**/companies/**", timeout=10000)
    current_url = await company_page.get_current_url()
    assert "/companies/" in current_url, f"Not redirected to company page, current URL: {current_url}"
    
    # Verify redirected to correct company ID
    assert f"/companies/{existing_company_id}" in current_url, \
        f"Redirected to wrong company. Expected ID {existing_company_id}, got: {current_url}"

    logger.info(f"Navigated to company page: {current_url}")

    # Step 8: Verify company name matches original
    displayed_company_name = await company_page.get_company_name()
    assert displayed_company_name == existing_company_name, \
        f"Company name mismatch. Expected: '{existing_company_name}', Got: '{displayed_company_name}'"

    logger.info(
        f"✅ TEST-006 PASSED: company={existing_company_id}, "
        f"duplicate detection works, navigation correct. Cleanup will be automatic."
    )
