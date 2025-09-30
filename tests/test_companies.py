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
    backend_url: str
):
    """
    TEST-003: Create new company with complete information.
    
    Steps:
    1. Open companies page
    2. Click "Add company" button  
    3. Fill form with test data
    4. Submit form
    5. Moderate company via API
    6. Verify company page displays all data correctly
    7. Verify company appears in catalog
    8. Clean up by deleting the company
    """
    # Arrange
    company_page = CompanyPage(page)
    test_helper = TestHelper(backend_url)
    company_data = generate_company_data()
    created_company_id = None
    
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
    
    # Moderate the company via API (companies don't need moderation, but for consistency)
    moderated_id = await test_helper.find_and_moderate_company(
        company_name=company_data["name"],
        action="approve"
    )
    assert moderated_id == created_company_id, f"Company not found after creation: expected ID {created_company_id}"
    
    # Navigate to the company page
    await company_page.open_company_page(created_company_id)
    
    # Assert - Verify URL changed
    current_url = await company_page.get_current_url()
    assert f"/companies/{created_company_id}" in current_url, f"URL did not change to company page: {current_url}"
    
    # Verify company data is displayed correctly
    displayed_name = await company_page.get_company_name()
    assert displayed_name == company_data["name"], "Company name mismatch"
    
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
    
    # Cleanup - delete the created company
    if created_company_id:
        deleted = await test_helper.delete_company(created_company_id)
        assert deleted, f"Failed to delete company {created_company_id} during cleanup - test data pollution!"
    
    await test_helper.close()
    
    # Test completed successfully
    logger.info(f"TEST-003 completed: company_id={created_company_id}")


@pytest.mark.e2e 
async def test_create_company_minimal_data(
    page: Page,
    backend_url: str
):
    """
    TEST-003b: Create company with only required fields.
    
    Steps:
    1. Open new company form
    2. Fill only required fields (name, country, description)
    3. Submit and moderate
    4. Verify company created successfully
    5. Clean up
    """
    # Arrange
    company_page = CompanyPage(page)
    test_helper = TestHelper(backend_url)
    minimal_data = {
        "name": f"Minimal Company {generate_company_data()['name'].split('_')[-1]}",
        "country_code": "RU",
        "description": "Минимальное описание компании для тестирования"
    }
    created_company_id = None
    
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
    
    # Moderate
    await test_helper.find_and_moderate_company(
        company_name=minimal_data["name"],
        action="approve"
    )
    
    # Verify on company page
    await company_page.open_company_page(created_company_id)
    
    displayed_name = await company_page.get_company_name()
    assert displayed_name == minimal_data["name"], "Company name mismatch"
    
    # Verify no contact info is displayed
    displayed_email = await company_page.get_contact_email()
    assert displayed_email is None, "Email should not be displayed when not provided"
    
    # Cleanup
    if created_company_id:
        deleted = await test_helper.delete_company(created_company_id)
        assert deleted, f"Failed to delete company {created_company_id} during cleanup - test data pollution!"
    await test_helper.close()
    
    logger.info(f"TEST-003b completed: company_id={created_company_id}")


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
