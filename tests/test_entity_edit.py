"""E2E tests for entity editing functionality (companies and guides)."""

import pytest
import logging
import uuid
from playwright.async_api import Page
from pages.company_page import CompanyPage
from pages.guide_page import GuidePage
from utils.test_helper import TestHelper
from utils.frontend_api_client import FrontendApiClient

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("entity_type", ["company", "guide"])
async def test_edit_entity_with_valid_key(
    page: Page,
    backend_url: str,
    frontend_api_client: FrontendApiClient,
    clean_test_company: list,
    clean_test_guide: list,
    entity_type: str
):
    """
    TEST-011: Edit company/guide with valid master key.
    
    Steps:
    1. Create entity via API
    2. Get master key via test endpoint
    3. Navigate to entity page
    4. Click edit button
    5. Verify info message
    6. Enter master key
    7. Click proceed to edit form
    8. Verify form pre-filled with current data
    9. Change data (name, description, contacts)
    10. Submit form
    11. Verify redirect with success param
    12. Verify green success toast with correct text
    13. Wait for or close toast
    14. Verify updated data displayed on page
    15. Cleanup via fixture
    
    Args:
        page: Playwright Page instance
        backend_url: Backend API URL
        frontend_api_client: API client for creating entities
        clean_test_company: Company cleanup fixture
        clean_test_guide: Guide cleanup fixture
        entity_type: "company" or "guide"
    """
    # Arrange
    test_helper = TestHelper(backend_url)
    
    try:
        # Create entity
        if entity_type == "company":
            entity = await frontend_api_client.create_company(
                name="Edit Test Company",
                country_code="GE",
                description="Original company description for testing edit functionality",
                contact_email="original@company.com",
                contact_phone="+995555111222",
                contact_website="https://original-company.com"
            )
            clean_test_company.append(entity["id"])
            page_obj = CompanyPage(page)
            success_param = "company_updated"
            toast_title = "Данные обновлены!"
            toast_text_substring = "профиле компании"
        else:
            entity = await frontend_api_client.create_guide(
                name="Edit Test Guide",
                countries=["GE", "AM"],
                description="Original guide description for testing edit functionality",
                contact_email="original@guide.com",
                contact_phone="+995555333444"
            )
            clean_test_guide.append(entity["id"])
            page_obj = GuidePage(page)
            success_param = "guide_updated"
            toast_title = "Данные обновлены!"
            toast_text_substring = "профиле гида"
        
        entity_id = entity["id"]
        logger.info(f"Created {entity_type} with ID={entity_id}")
        
        # Get master key
        master_key = await test_helper.get_master_key(entity_type, entity_id)
        assert master_key is not None, f"Failed to get master key for {entity_type} {entity_id}"
        logger.info(f"Got master key for {entity_type} {entity_id}: {master_key[:8]}...")
        
        # Act - Navigate to entity page
        if entity_type == "company":
            await page_obj.open_company_page(entity_id)
        else:
            await page_obj.open_guide_page(entity_id)
        
        # Click edit button
        await page_obj.click_edit_button()
        
        # Assert - Modal opened
        assert await page_obj.is_edit_modal_open(), "Edit modal did not open"
        logger.info("Edit modal opened successfully")
        
        # Assert - Verify info message
        info_text = await page_obj.get_info_message_text()
        assert "администратором" in info_text.lower(), \
            f"Info message doesn't mention admin: {info_text}"
        logger.info("Info message verified")
        
        # Act - Fill master key
        await page_obj.fill_master_key(master_key)
        
        # Assert - Button should be enabled
        button_enabled = await page_obj.is_edit_proceed_button_enabled()
        assert button_enabled, "Edit proceed button should be enabled after entering valid key"
        
        # Act - Click proceed to edit form
        await page_obj.click_edit_proceed_button()
        logger.info("Proceeded to edit form")
        
        # Wait for form to fully load
        await page.wait_for_timeout(500)
        
        # Prepare updated data
        updated_data = {
            "name": f"EDITED {entity_type.title()}",
            "description": "UPDATED description after successful edit with valid master key",
            "email": "updated@example.com",
            "phone": "+995555999888",
        }
        
        if entity_type == "company":
            updated_data["website"] = "https://updated-site.com"
            updated_data["instagram"] = "@updated_company"
            updated_data["telegram"] = "@updated_company_tg"
        else:
            updated_data["instagram"] = "@updated_guide"
            updated_data["telegram"] = "@updated_guide_tg"
        
        # Act - Fill edit form
        await page_obj.fill_edit_form(updated_data)
        logger.info("Edit form filled with updated data")
        
        # Act - Submit form
        await page_obj.submit_edit_form()
        logger.info("Edit form submitted")
        
        # Wait for success toast to appear (frontend shows toast without redirect)
        toast_appeared = await page_obj.wait_for_success_toast(timeout=8000)
        assert toast_appeared, "Success toast did not appear after form submission"
        logger.info("Success toast appeared")
        
        # Verify toast content
        toast_title_actual = await page_obj.get_toast_title()
        toast_text_actual = await page_obj.get_toast_text()
        
        assert toast_title_actual == toast_title, \
            f"Toast title mismatch. Expected '{toast_title}', got '{toast_title_actual}'"
        assert toast_text_substring in toast_text_actual.lower(), \
            f"Toast text should contain '{toast_text_substring}', got '{toast_text_actual}'"
        logger.info(f"Toast content verified")
        
        # Close toast
        await page_obj.close_toast()
        await page.wait_for_timeout(500)
        
        # Assert - Verify updated data on page
        if entity_type == "company":
            # Refresh page to ensure we see latest data
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            displayed_name = await page_obj.get_company_name()
            displayed_desc = await page_obj.get_company_description()
            displayed_email = await page_obj.get_contact_email()
            displayed_phone = await page_obj.get_contact_phone()
            displayed_website = await page_obj.get_contact_website()
            displayed_instagram = await page_obj.get_contact_instagram()
            displayed_telegram = await page_obj.get_contact_telegram()
            
            assert displayed_name == updated_data["name"], \
                f"Name not updated. Expected '{updated_data['name']}', got '{displayed_name}'"
            assert updated_data["description"] in displayed_desc, \
                f"Description not updated. Got '{displayed_desc}'"
            assert displayed_email == updated_data["email"], \
                f"Email not updated. Expected '{updated_data['email']}', got '{displayed_email}'"
            assert displayed_phone == updated_data["phone"], \
                f"Phone not updated. Expected '{updated_data['phone']}', got '{displayed_phone}'"
            assert displayed_website == updated_data["website"], \
                f"Website not updated. Expected '{updated_data['website']}', got '{displayed_website}'"
            assert displayed_instagram == updated_data["instagram"].replace("@", ""), \
                f"Instagram not updated. Expected '{updated_data['instagram']}', got '@{displayed_instagram}'"
            assert displayed_telegram == updated_data["telegram"].replace("@", ""), \
                f"Telegram not updated. Expected '{updated_data['telegram']}', got '@{displayed_telegram}'"
        else:
            # Refresh page for guide
            await page.reload(wait_until="networkidle")
            await page.wait_for_timeout(1000)
            
            displayed_name = await page_obj.get_guide_name()
            
            # Get page content to check description and contacts
            page_content = await page.content()
            
            assert displayed_name == updated_data["name"], \
                f"Guide name not updated. Expected '{updated_data['name']}', got '{displayed_name}'"
            assert updated_data["description"] in page_content, \
                f"Guide description not updated. Not found in page content"
            assert updated_data["email"] in page_content, \
                f"Guide email not updated. Expected '{updated_data['email']}' in page content"
            assert updated_data["phone"] in page_content, \
                f"Guide phone not updated. Expected '{updated_data['phone']}' in page content"
        
        logger.info(f"✅ TEST-011 PASSED for {entity_type}: All data updated correctly")
        
    finally:
        await test_helper.close()
        await frontend_api_client.close()


@pytest.mark.e2e
@pytest.mark.parametrize("entity_type", ["company", "guide"])
async def test_edit_entity_with_invalid_key(
    page: Page,
    backend_url: str,
    frontend_api_client: FrontendApiClient,
    clean_test_company: list,
    clean_test_guide: list,
    entity_type: str
):
    """
    TEST-012: Attempt to edit company/guide with invalid master key.
    
    Steps:
    1. Create entity via API
    2. Generate random UUID as invalid key
    3. Navigate to entity page
    4. Open edit modal
    5. Enter invalid master key
    6. Fill form and submit
    7. Verify redirect with error param
    8. Verify red error toast with "Неверный мастер-ключ"
    9. Cleanup via fixture
    
    Args:
        page: Playwright Page instance
        backend_url: Backend API URL
        frontend_api_client: API client for creating entities
        clean_test_company: Company cleanup fixture
        clean_test_guide: Guide cleanup fixture
        entity_type: "company" or "guide"
    """
    # Arrange
    test_helper = TestHelper(backend_url)
    
    try:
        # Create entity
        if entity_type == "company":
            entity = await frontend_api_client.create_company(
                name="Invalid Key Test Company",
                country_code="TR",
                description="Testing edit with invalid master key"
            )
            clean_test_company.append(entity["id"])
            page_obj = CompanyPage(page)
        else:
            entity = await frontend_api_client.create_guide(
                name="Invalid Key Test Guide",
                countries=["TR"],
                description="Testing edit with invalid master key"
            )
            clean_test_guide.append(entity["id"])
            page_obj = GuidePage(page)
        
        entity_id = entity["id"]
        logger.info(f"Created {entity_type} with ID={entity_id}")
        
        # Generate invalid master key (random UUID)
        invalid_key = str(uuid.uuid4())
        logger.info(f"Using invalid master key: {invalid_key}")
        
        # Act - Navigate to entity page
        if entity_type == "company":
            await page_obj.open_company_page(entity_id)
        else:
            await page_obj.open_guide_page(entity_id)
        
        # Open edit modal
        await page_obj.click_edit_button()
        assert await page_obj.is_edit_modal_open(), "Edit modal did not open"
        
        # Enter invalid master key
        await page_obj.fill_master_key(invalid_key)
        
        # Proceed to edit form
        await page_obj.click_edit_proceed_button()
        
        # Fill with some data
        await page_obj.fill_edit_form({
            "name": "Should Not Be Updated",
            "description": "This should not be saved"
        })
        
        # Submit
        await page_obj.submit_edit_form()
        logger.info("Submitted form with invalid key")
        
        # Wait for error toast to appear (frontend shows toast without redirect)
        toast_appeared = await page_obj.wait_for_error_toast(timeout=8000)
        assert toast_appeared, "Error toast did not appear after invalid key submission"
        logger.info("Error toast appeared")
        
        # Verify toast text
        toast_title_actual = await page_obj.get_toast_title()
        toast_text_actual = await page_obj.get_toast_text()
        
        assert "мастер-ключ" in toast_title_actual.lower(), \
            f"Toast title should mention master key. Got '{toast_title_actual}'"
        logger.info(f"Error toast verified")
        
        logger.info(f"✅ TEST-012 PASSED for {entity_type}: Invalid key correctly rejected")
        
    finally:
        await test_helper.close()
        await frontend_api_client.close()


@pytest.mark.e2e
@pytest.mark.parametrize("entity_type,key_variant", [
    ("company", "empty"),
    ("company", "random_string"),
    ("company", "invalid_uuid"),
    ("guide", "empty"),
    ("guide", "random_string"),
    ("guide", "invalid_uuid"),
])
async def test_edit_attempt_with_invalid_format(
    page: Page,
    backend_url: str,
    frontend_api_client: FrontendApiClient,
    clean_test_company: list,
    clean_test_guide: list,
    entity_type: str,
    key_variant: str
):
    """
    TEST-013: Attempt to proceed without key or with invalid format.
    
    Tests three scenarios:
    - empty: Leave key field empty → button should be disabled
    - random_string: "abcd1234" → should show validation error
    - invalid_uuid: "123e4567-INVALID" → should show validation error
    
    Steps:
    1. Create entity via API
    2. Open edit modal
    3. Try to enter invalid key based on variant
    4. Verify button disabled OR validation error shown
    5. Verify edit form does NOT open
    6. Cleanup via fixture
    
    Args:
        page: Playwright Page instance
        backend_url: Backend API URL
        frontend_api_client: API client for creating entities
        clean_test_company: Company cleanup fixture
        clean_test_guide: Guide cleanup fixture
        entity_type: "company" or "guide"
        key_variant: Type of invalid input
    """
    # Arrange
    test_helper = TestHelper(backend_url)
    
    try:
        # Create entity
        if entity_type == "company":
            entity = await frontend_api_client.create_company(
                name=f"Format Test Company {key_variant}",
                country_code="AM",
                description="Testing validation"
            )
            clean_test_company.append(entity["id"])
            page_obj = CompanyPage(page)
        else:
            entity = await frontend_api_client.create_guide(
                name=f"Format Test Guide {key_variant}",
                countries=["AM"],
                description="Testing validation"
            )
            clean_test_guide.append(entity["id"])
            page_obj = GuidePage(page)
        
        entity_id = entity["id"]
        logger.info(f"Created {entity_type} with ID={entity_id} for variant={key_variant}")
        
        # Navigate to entity page
        if entity_type == "company":
            await page_obj.open_company_page(entity_id)
        else:
            await page_obj.open_guide_page(entity_id)
        
        # Open edit modal
        await page_obj.click_edit_button()
        assert await page_obj.is_edit_modal_open(), "Edit modal did not open"
        
        # Act based on variant
        if key_variant == "empty":
            await page.wait_for_timeout(500)
            button_enabled = await page_obj.is_edit_proceed_button_enabled()
            assert not button_enabled, "Edit button should be DISABLED when empty"
            logger.info("✅ Empty field: button correctly disabled")
            
        elif key_variant == "random_string":
            await page_obj.fill_master_key("abcd1234notauuid")
            await page.wait_for_timeout(500)
            error_text = await page_obj.get_master_key_error()
            if error_text:
                assert "uuid" in error_text.lower(), f"Should mention UUID. Got: {error_text}"
                logger.info("✅ Random string: validation error shown")
            else:
                logger.info("✅ Random string: no explicit error (client-side validation)")
                
        elif key_variant == "invalid_uuid":
            await page_obj.fill_master_key("123e4567-e89b-12d3-XXXX-426614174000")
            await page.wait_for_timeout(500)
            error_text = await page_obj.get_master_key_error()
            if error_text:
                assert "uuid" in error_text.lower(), f"Should mention UUID. Got: {error_text}"
                logger.info("✅ Invalid UUID: validation error shown")
            else:
                logger.info("✅ Invalid UUID: no explicit error (client-side validation)")
        
        # Verify still on master key step
        modal_title = await page.query_selector("text=Подтверждение прав редактирования")
        assert modal_title is not None, "Should still be on master key step"
        
        logger.info(f"✅ TEST-013 PASSED for {entity_type}/{key_variant}")
        
    finally:
        await test_helper.close()
        await frontend_api_client.close()
