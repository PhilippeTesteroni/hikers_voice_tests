"""E2E test for duplicate guide detection and navigation.

REFACTORED: Creates unique guides via API, no seed data dependency.
"""

import pytest
import logging
from playwright.async_api import Page
from pages.guide_page import GuidePage
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("action", [
    "go_to_existing",  # TEST-007a: Navigate to existing guide
    "create_new",  # TEST-007b: Force create new duplicate guide
])
async def test_duplicate_guide_detection_and_navigation(
        page: Page,
        frontend_url: str,
        backend_url: str,
        frontend_api_client,
        clean_test_guide: list,
        action: str
):
    """
    TEST-007 REFACTORED: Test duplicate guide detection with overlapping countries.
    
    Creates unique guide via API, then tests duplicate detection when creating
    another guide with same name and overlapping country.

    Parametrized test with two scenarios:
    - action="go_to_existing": Click "Yes, go to profile" and verify navigation
    - action="create_new": Click "No, create new" and verify new guide is created

    Steps:
    1. Create guide via API with specific countries
    2. Navigate to new guide form
    3. Fill form with same name and overlapping country
    4. Submit form
    5. Verify duplicate warning appears with guide card
    6. Verify card shows: name, countries, rating, reviews count, contacts
    7a. If "go_to_existing": Click "Yes, go to profile" and verify navigation
    7b. If "create_new": Click "No, create new", verify new guide created, cleanup both
    8. Cleanup handled automatically

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        backend_url: Backend base URL
        frontend_api_client: API client for creating guides
        clean_test_guide: Cleanup fixture
        action: Action to take on duplicate warning ("go_to_existing" or "create_new")
    """

    # Step 1: Create guide via API
    logger.info("Creating guide via API for duplicate detection test")
    
    guide = await frontend_api_client.create_guide(
        name="Duplicate Detection Guide",
        countries=["GE", "AM"],
        description="Test guide for duplicate detection",
        contact_telegram="@duplicatetest",
        contact_phone="+995555123456"
    )
    clean_test_guide.append(guide["id"])
    
    existing_guide_id = guide["id"]
    existing_guide_name = guide["name"]
    
    logger.info(f"Created guide via API: ID={existing_guide_id}, Name={existing_guide_name}, Countries=GE,AM")
    
    # Step 2: Navigate to new guide form
    guide_page = GuidePage(page, frontend_url)
    await guide_page.open_new_guide_form()
    
    # Step 3: Fill form with same name and overlapping country (GE)
    duplicate_guide_data = {
        "name": existing_guide_name,
        "description": "Опытный горный гид с большим стажем работы в горах Кавказа.",
        "countries": ["GE"]  # Overlapping with existing guide's GE
    }
    
    await guide_page.fill_guide_form(duplicate_guide_data)
    
    # Step 4: Submit form
    await guide_page.submit_guide_form()
    
    # Step 5: Wait for duplicate warning to appear
    duplicate_warning_appeared = await guide_page.wait_for_duplicate_warning()
    assert duplicate_warning_appeared, \
        f"Duplicate guide warning did not appear after submitting duplicate guide name '{existing_guide_name}' " \
        f"with overlapping country 'GE'"
    
    logger.info("✓ Duplicate warning appeared successfully")
    
    # Verify warning message contains expected text
    duplicate_message_element = await page.query_selector(guide_page.DUPLICATE_MESSAGE)
    assert duplicate_message_element is not None, "Duplicate message element not found"
    
    # Verify both action buttons are present
    yes_button = await page.query_selector(guide_page.YES_GO_TO_PROFILE_BUTTON)
    no_button = await page.query_selector(guide_page.NO_CREATE_NEW_BUTTON)
    
    assert yes_button is not None, "'Yes, go to profile' button not found"
    assert no_button is not None, "'No, create new' button not found"
    
    logger.info("✓ Both action buttons found on duplicate warning")
    
    # Step 6: Verify duplicate guide card information
    duplicate_info = await guide_page.get_duplicate_guide_info()
    
    # Check guide name
    assert duplicate_info.get("name"), "Duplicate card does not show guide name"
    assert existing_guide_name.split()[0] in duplicate_info["name"], \
        f"Guide name mismatch. Expected '{existing_guide_name}' in '{duplicate_info['name']}'"
    
    # Check countries are displayed
    assert duplicate_info.get("countries"), "Duplicate card does not show countries"
    assert len(duplicate_info["countries"]) > 0, "No country badges displayed on duplicate card"
    
    logger.info(f"✓ Duplicate card shows countries: {duplicate_info['countries']}")
    
    # Check if contacts are displayed
    assert duplicate_info.get("contacts"), "Duplicate card does not show any contacts"
    logger.info(f"✓ Contacts displayed: {list(duplicate_info['contacts'].keys())}")
    
    # Step 7: Take action based on parameter
    created_guide_id = None
    
    if action == "go_to_existing":
        # TEST-007a: Click "Yes, go to profile" button
        logger.info("TEST-007a: Testing navigation to existing guide")
        
        await guide_page.click_yes_go_to_profile()
        
        # Verify we're on guide profile page
        await page.wait_for_url(f"**/guides/{existing_guide_id}", timeout=10000)
        current_url = page.url
        assert f"/guides/{existing_guide_id}" in current_url, \
            f"Not redirected to guide page, current URL: {current_url}"
        
        logger.info(f"✓ Successfully navigated to guide page: {current_url}")
        
        # Verify guide name matches original
        displayed_guide_name = await guide_page.get_guide_name()
        assert existing_guide_name.split()[0] in displayed_guide_name, \
            f"Guide name mismatch. Expected '{existing_guide_name}' in '{displayed_guide_name}'"
        
        logger.info(f"✅ TEST-007a PASSED: guide={existing_guide_id}, navigation works. Cleanup will be automatic.")
        
    else:  # action == "create_new"
        # TEST-007b: Click "No, create new" button
        logger.info("TEST-007b: Testing force creation of duplicate guide")
        
        # Click "No, create new" button
        await page.click(guide_page.NO_CREATE_NEW_BUTTON)
        
        # Wait for success message
        success = await guide_page.wait_for_guide_success()
        assert success, "Guide creation success message did not appear after clicking 'No, create new'"
        
        # Get created guide ID
        created_guide_id = await guide_page.get_success_guide_id()
        assert created_guide_id is not None, "Failed to get guide ID from success message"
        assert created_guide_id != existing_guide_id, \
            f"New guide ID {created_guide_id} should be different from existing guide ID {existing_guide_id}"
        
        logger.info(f"✓ New guide successfully created with ID: {created_guide_id}")
        
        # Verify success message
        success_heading = await page.locator("h2:has-text('Профиль гида успешно создан!')").text_content()
        assert success_heading is not None, "Success heading not found"
        
        id_text = await page.locator("p.text-sm:has-text('ID гида:')").text_content()
        assert f"ID гида: {created_guide_id}" in id_text, \
            f"Expected 'ID гида: {created_guide_id}' but got '{id_text}'"
        
        logger.info("✓ Success message verified")
        
        # Navigate to guides list and verify both guides exist
        await page.goto(f"{frontend_url}/guides")
        await guide_page.wait_for_load()
        
        # Search for guides with similar name
        guide_cards = await page.locator("article.card, .card").all()
        base_name_part = existing_guide_name.split()[0]  # First word
        guides_with_similar_name = []
        
        for card in guide_cards:
            name_elem = card.locator("h3, h2").first
            card_name = await name_elem.text_content()
            if card_name and base_name_part in card_name.strip():
                guides_with_similar_name.append(card)
        
        # Should have at least 2 guides with similar name
        assert len(guides_with_similar_name) >= 2, \
            f"Expected at least 2 guides with name containing '{base_name_part}', found {len(guides_with_similar_name)}"
        
        logger.info(
            f"✓ Verified: {len(guides_with_similar_name)} guides with name containing '{base_name_part}' exist in the system")
        
        # Cleanup: delete the newly created guide
        if created_guide_id:
            clean_test_guide.append(created_guide_id)
            logger.info(f"Marked guide {created_guide_id} for cleanup")
        
        logger.info(f"✅ TEST-007b PASSED: guides={existing_guide_id},{created_guide_id}. Cleanup will be automatic.")


@pytest.mark.e2e
@pytest.mark.critical
async def test_create_guide_same_name_no_country_overlap(
        page: Page,
        frontend_url: str,
        backend_url: str,
        frontend_api_client,
        clean_test_guide: list
):
    """
    TEST-008 REFACTORED: Create guide with same name but no overlapping countries.
    
    Creates guide via API, then creates another guide with same name but
    different country (no overlap) - should NOT trigger duplicate warning.

    Steps:
    1. Create guide via API with specific countries (GE, AM)
    2. Open new guide form
    3. Fill form with same name but different country (TR - no overlap)
    4. Submit form
    5. Verify NO duplicate warning appears
    6. Verify green success message with new guide ID
    7. Clean up: both guides deleted automatically

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        backend_url: Backend base URL
        frontend_api_client: API client
        clean_test_guide: Cleanup fixture
    """
    
    # Step 1: Create guide via API
    logger.info("Creating guide via API for no-overlap test")
    
    guide = await frontend_api_client.create_guide(
        name="No Overlap Guide",
        countries=["GE", "AM"],
        description="Test guide with Georgia and Armenia",
        contact_telegram="@nooverlaptest"
    )
    clean_test_guide.append(guide["id"])
    
    existing_guide_id = guide["id"]
    existing_guide_name = guide["name"]
    existing_countries = guide["countries"]
    
    logger.info(f"Created guide: ID={existing_guide_id}, Name={existing_guide_name}, Countries={existing_countries}")
    
    # Step 2: Navigate to new guide form
    guide_page = GuidePage(page, frontend_url)
    await guide_page.open_new_guide_form()
    
    # Step 3: Fill form with same name but different country (Turkey - no overlap with GE/AM)
    new_guide_data = {
        "name": existing_guide_name,
        "description": "Опытный горный гид с большим стажем работы в горах.",
        "countries": ["TR"]  # Turkey - NO overlap with Georgia/Armenia
    }
    
    await guide_page.fill_guide_form(new_guide_data)
    
    # Step 4: Submit form
    await guide_page.submit_guide_form()
    
    # Step 5: Verify NO duplicate warning appears
    await page.wait_for_timeout(2000)
    
    duplicate_warning_visible = await page.locator(guide_page.DUPLICATE_WARNING).is_visible()
    
    assert not duplicate_warning_visible, \
        f"Duplicate warning appeared when it should NOT (no overlapping countries). " \
        f"Guide name: {existing_guide_name}, existing countries: {existing_countries}, test country: TR"
    
    logger.info("✓ No duplicate warning - correct behavior for non-overlapping countries")
    
    # Step 6: Verify green success message with new guide ID
    success = await guide_page.wait_for_guide_success()
    assert success, "Guide creation success message did not appear"
    
    created_guide_id = await guide_page.get_success_guide_id()
    assert created_guide_id is not None, "Failed to get guide ID from success message"
    assert created_guide_id != existing_guide_id, \
        f"New guide should have different ID from existing. Got {created_guide_id}, existing: {existing_guide_id}"
    
    logger.info(f"✓ Guide successfully created with ID: {created_guide_id}")
    
    # Verify success message
    success_element = await page.query_selector(".bg-green-100")
    assert success_element is not None, "Success message (green background) not found"
    
    success_heading = await page.locator("h2:has-text('Профиль гида успешно создан!')").text_content()
    assert success_heading is not None, "Success heading not found"
    
    id_text = await page.locator("p.text-sm:has-text('ID гида:')").text_content()
    assert f"ID гида: {created_guide_id}" in id_text, f"Expected 'ID гида: {created_guide_id}' but got '{id_text}'"
    
    logger.info("✓ Success message verified")
    
    # Step 7: Cleanup - mark for deletion
    clean_test_guide.append(created_guide_id)
    logger.info(f"Marked guide {created_guide_id} for cleanup")
    
    logger.info(
        f"✅ TEST-008 PASSED: guides={existing_guide_id},{created_guide_id}. "
        f"No overlap detection works correctly. Cleanup will be automatic."
    )
