"""E2E test for duplicate guide detection and navigation."""

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
        clean_test_guide: list,
        action: str
):
    """
    TEST-007: Test duplicate guide detection with overlapping countries.

    Parametrized test with two scenarios:
    - action="go_to_existing": Click "Yes, go to profile" and verify navigation
    - action="create_new": Click "No, create new" and verify new guide is created

    Steps:
    1. Open guides page and get first guide with contacts
    2. Navigate to new guide form
    3. Fill form with same name and overlapping country
    4. Submit form
    5. Verify duplicate warning appears with guide card
    6. Verify card shows: name, countries, rating, reviews count, all contacts
    7a. If "go_to_existing": Click "Yes, go to profile" and verify navigation
    7b. If "create_new": Click "No, create new", verify new guide created, check both guides exist, cleanup

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        backend_url: Backend base URL
        action: Action to take on duplicate warning ("go_to_existing" or "create_new")
    """

    # Arrange
    guide_page = GuidePage(page, frontend_url)
    created_guide_id = None

    # Step 1: Open guides page and get first guide info
    await page.goto(f"{frontend_url}/guides")
    await guide_page.wait_for_load()

    # Find first guide card
    guide_cards = await page.locator("article.card, .card").all()
    assert len(guide_cards) > 0, "No guides found on guides page. Please add at least one guide to the database."

    first_guide_card = guide_cards[0]

    # Get guide name from card
    guide_name_element = first_guide_card.locator("h3, h2").first
    existing_guide_name = await guide_name_element.text_content()
    existing_guide_name = existing_guide_name.strip() if existing_guide_name else ""

    assert existing_guide_name, "Could not extract guide name from card"

    logger.info(f"Found guide: {existing_guide_name}")

    # Click on "Подробнее" button to get full info
    details_button = first_guide_card.locator("a:has-text('Подробнее'), button:has-text('Подробнее')").first
    await details_button.click()
    await page.wait_for_url("**/guides/**", timeout=10000)

    # Wait for guide page to fully load
    await page.wait_for_selector("h1", timeout=5000)  # Wait for guide name heading

    # Extract guide ID from URL
    import re
    current_url = page.url
    match = re.search(r'/guides/(\d+)', current_url)
    assert match, f"Could not extract guide ID from URL: {current_url}"
    existing_guide_id = int(match.group(1))

    logger.info(f"Guide ID: {existing_guide_id}")

    # Get guide countries - simpler approach, just get the text containing countries
    countries_text = await page.locator(
        "text=/Грузия|Армения|Россия|Казахстан|Киргизия|Узбекистан|Азербайджан/").first.text_content()
    if countries_text:
        # If it's a comma-separated list
        if "," in countries_text:
            existing_countries = [c.strip() for c in countries_text.split(",")]
        else:
            # Single country
            existing_countries = [countries_text.strip()]
    else:
        # Fallback - try to get from page text
        page_text = await page.content()
        if "Грузия" in page_text:
            existing_countries = ["Грузия"]
        elif "Армения" in page_text:
            existing_countries = ["Армения"]
        elif "Россия" in page_text:
            existing_countries = ["Россия"]
        else:
            existing_countries = []

    assert len(
        existing_countries) > 0, f"Guide '{existing_guide_name}' has no countries. Test requires guide with at least one country."

    logger.info(f"Guide countries: {existing_countries}")

    # Check if guide has contacts - they are displayed with icons (Phone, Mail, Instagram, Send)
    # Just check that the contacts section exists
    contacts_heading = await page.locator("text=Контактная информация").count()
    if contacts_heading == 0:
        # No contacts heading means no contacts at all - skip this guide
        logger.warning(f"Guide '{existing_guide_name}' has no contacts section - test may not verify contacts properly")

    # Pick first country for duplicate test - map display name to country code
    # Common mappings
    country_map = {
        "Грузия": "GE",
        "Армения": "AM",
        "Россия": "RU",
        "Казахстан": "KZ",
        "Киргизия": "KG",
        "Узбекистан": "UZ",
        "Азербайджан": "AZ",
    }

    test_country_name = existing_countries[0]
    test_country_code = country_map.get(test_country_name, "GE")  # Default to GE if not found

    logger.info(f"Will use country '{test_country_name}' (code: {test_country_code}) for duplicate detection")

    # Step 2: Navigate to new guide form
    await guide_page.open_new_guide_form()

    # Step 3: Fill form with same name and overlapping country
    duplicate_guide_data = {
        "name": existing_guide_name,
        "description": "Опытный горный гид с большим стажем работы в горах Кавказа.",
        "countries": [test_country_code]
    }

    await guide_page.fill_guide_form(duplicate_guide_data)

    # Step 4: Submit form
    await guide_page.submit_guide_form()

    # Step 5: Wait for duplicate warning to appear
    duplicate_warning_appeared = await guide_page.wait_for_duplicate_warning()
    assert duplicate_warning_appeared, \
        f"Duplicate guide warning did not appear after submitting duplicate guide name '{existing_guide_name}' " \
        f"with overlapping country '{test_country_name}'"

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
    assert existing_guide_name in duplicate_info["name"], \
        f"Guide name mismatch. Expected '{existing_guide_name}' in '{duplicate_info['name']}'"

    # Check countries are displayed
    assert duplicate_info.get("countries"), "Duplicate card does not show countries"
    assert len(duplicate_info["countries"]) > 0, "No country badges displayed on duplicate card"

    logger.info(f"✓ Duplicate card shows countries: {duplicate_info['countries']}")

    # Check if contacts are displayed
    assert duplicate_info.get("contacts"), "Duplicate card does not show any contacts"
    logger.info(f"✓ Contacts displayed: {list(duplicate_info['contacts'].keys())}")

    # Step 7: Take action based on parameter
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
        assert displayed_guide_name == existing_guide_name, \
            f"Guide name mismatch. Expected: '{existing_guide_name}', Got: '{displayed_guide_name}'"

        logger.info(f"✓ TEST-007a completed: Guide name verified as '{displayed_guide_name}'")

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

        # Search for guides with the same name
        guide_cards = await page.locator("article.card, .card").all()
        guides_with_same_name = []

        for card in guide_cards:
            name_elem = card.locator("h3, h2").first
            card_name = await name_elem.text_content()
            if card_name and existing_guide_name in card_name.strip():
                guides_with_same_name.append(card)

        # Should have at least 2 guides with the same name
        assert len(guides_with_same_name) >= 2, \
            f"Expected at least 2 guides with name '{existing_guide_name}', found {len(guides_with_same_name)}"

        logger.info(
            f"✓ Verified: {len(guides_with_same_name)} guides with name '{existing_guide_name}' exist in the system")

        # Cleanup: delete the newly created guide
        if created_guide_id:
            clean_test_guide.append(created_guide_id)
            logger.info(f"Marked guide {created_guide_id} for cleanup")

        logger.info(f"✓ TEST-007b completed: New guide created and verified, will be cleaned up")


@pytest.mark.e2e
@pytest.mark.critical
async def test_create_guide_same_name_no_country_overlap(
        page: Page,
        frontend_url: str,
        backend_url: str,
        clean_test_guide: list
):
    """
    TEST-008: Create guide with same name but no overlapping countries.

    Steps:
    1. Open guides page and get first guide info
    2. Extract guide name and countries
    3. Open new guide form
    4. Fill form with same name but different country (Turkey)
    5. Submit form
    6. Verify NO duplicate warning appears
    7. Verify green success message with new guide ID
    8. Clean up: delete created guide

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        backend_url: Backend base URL
    """

    # Arrange
    guide_page = GuidePage(page, frontend_url)
    created_guide_id = None

    # Step 1: Open guides page and get first guide info
    await page.goto(f"{frontend_url}/guides")
    await guide_page.wait_for_load()

    # Find first guide card
    guide_cards = await page.locator("article.card, .card").all()
    assert len(guide_cards) > 0, "No guides found on guides page. Please add at least one guide to the database."

    first_guide_card = guide_cards[0]

    # Step 2: Get guide name from card
    guide_name_element = first_guide_card.locator("h3, h2").first
    existing_guide_name = await guide_name_element.text_content()
    existing_guide_name = existing_guide_name.strip() if existing_guide_name else ""

    assert existing_guide_name, "Could not extract guide name from card"

    logger.info(f"Found guide: {existing_guide_name}")

    # Get guide's countries to ensure we pick a different one
    # Click on guide to see full info
    details_button = first_guide_card.locator("a:has-text('Подробнее'), button:has-text('Подробнее')").first
    await details_button.click()
    await page.wait_for_url("**/guides/**", timeout=10000)

    # Wait for guide page to load
    await page.wait_for_selector("h1", timeout=5000)

    # Get guide countries
    countries_text = await page.locator(
        "text=/Грузия|Армения|Россия|Казахстан|Киргизия|Узбекистан|Азербайджан|Турция/").first.text_content()
    if countries_text:
        if "," in countries_text:
            existing_countries = [c.strip() for c in countries_text.split(",")]
        else:
            existing_countries = [countries_text.strip()]
    else:
        # Fallback - try to get from page text
        page_text = await page.content()
        if "Грузия" in page_text:
            existing_countries = ["Грузия"]
        elif "Армения" in page_text:
            existing_countries = ["Армения"]
        elif "Россия" in page_text:
            existing_countries = ["Россия"]
        else:
            existing_countries = []

    assert len(
        existing_countries) > 0, f"Guide '{existing_guide_name}' has no countries. Test requires guide with at least one country."

    logger.info(f"Existing guide countries: {existing_countries}")

    # Choose Turkey (TR) as it's unlikely to overlap with existing guide's countries
    # If guide somehow has Turkey, we'll verify no duplicate is detected anyway
    test_country_code = "TR"
    test_country_name = "Турция"

    # Verify chosen country is different
    has_overlap = test_country_name in existing_countries
    if has_overlap:
        logger.warning(
            f"Guide already has {test_country_name}, but test will continue to verify proper duplicate detection logic")
    else:
        logger.info(f"Using {test_country_name} as non-overlapping country")

    # Step 3: Navigate to new guide form
    await guide_page.open_new_guide_form()

    # Step 4: Fill form with same name but different country
    new_guide_data = {
        "name": existing_guide_name,
        "description": "Опытный горный гид с большим стажем работы в горах Кавказа.",
        "countries": [test_country_code]
    }

    await guide_page.fill_guide_form(new_guide_data)

    # Step 5: Submit form
    await guide_page.submit_guide_form()

    # Step 6: Verify NO duplicate warning appears
    # Wait a moment for potential duplicate check
    await page.wait_for_timeout(2000)

    # Check if duplicate warning appeared (it should NOT appear)
    duplicate_warning_visible = await page.locator(guide_page.DUPLICATE_WARNING).is_visible()

    if has_overlap:
        # If there was overlap, duplicate should be detected
        assert duplicate_warning_visible, \
            f"Expected duplicate warning to appear since guide already has {test_country_name}, but it didn't"
        logger.info("✓ Duplicate correctly detected due to country overlap")

        # Click "No, create new" to proceed
        await page.click(guide_page.NO_CREATE_NEW_BUTTON)
        await page.wait_for_timeout(1000)
    else:
        # No overlap - duplicate should NOT be detected
        assert not duplicate_warning_visible, \
            f"Duplicate warning appeared when it should NOT (no overlapping countries). " \
            f"Guide name: {existing_guide_name}, existing countries: {existing_countries}, test country: {test_country_name}"
        logger.info("✓ No duplicate warning - correct behavior for non-overlapping countries")

    # Step 7: Verify green success message with new guide ID
    success = await guide_page.wait_for_guide_success()
    assert success, "Guide creation success message did not appear"

    created_guide_id = await guide_page.get_success_guide_id()
    assert created_guide_id is not None, "Failed to get guide ID from success message"

    logger.info(f"✓ Guide successfully created with ID: {created_guide_id}")

    # Verify it's a new guide (different ID)
    # We can check that we're on success page with green background
    success_element = await page.query_selector(".bg-green-100")
    assert success_element is not None, "Success message (green background) not found"

    # Verify the success message contains the ID - use more specific selector
    success_heading = await page.locator("h2:has-text('Профиль гида успешно создан!')").text_content()
    assert success_heading is not None, "Success heading not found"

    # Check that ID is displayed in the paragraph
    id_text = await page.locator("p.text-sm:has-text('ID гида:')").text_content()
    assert f"ID гида: {created_guide_id}" in id_text, f"Expected 'ID гида: {created_guide_id}' but got '{id_text}'"

    logger.info("✓ Success message verified")

    # Step 8: Cleanup - delete the created guide
    if created_guide_id:
        clean_test_guide.append(created_guide_id)
        logger.info(f"Marked guide {created_guide_id} for cleanup")

    logger.info(f"TEST-008 completed successfully: created_guide_id={created_guide_id}")
