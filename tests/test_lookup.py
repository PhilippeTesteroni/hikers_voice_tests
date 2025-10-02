"""E2E test for guide lookup/autocomplete in review forms."""

import pytest
import logging
from playwright.async_api import Page
from pages.review_form_page import ReviewFormPage

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("form_type", [
    "guide_review",   # TEST-009a: Lookup in guide review form
    "company_review",  # TEST-009b: Lookup in company review form (guides section)
])
async def test_guide_lookup_extended_info(
    page: Page,
    frontend_url: str,
    backend_url: str,
    clean_test_guide: list,
    form_type: str
):
    """
    TEST-009: Test guide lookup with extended information display.
    
    Parametrized test with two scenarios:
    - form_type="guide_review": Lookup in guide review form (main guide field)
    - form_type="company_review": Lookup in company review form (guides section)
    
    Steps:
    1. Create duplicate guide with same name but different country
    2. Open review form (guide or company)
    3. Type partial guide name: "Геор"
    4. Wait for dropdown to appear
    5. Verify dropdown shows multiple guides with extended information
    6. Cleanup: delete created guide
    
    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        backend_url: Backend base URL
        api_client: API client fixture
        form_type: Type of form ("guide_review" or "company_review")
    """
    from pages.guide_page import GuidePage
    
    guide_page = GuidePage(page, frontend_url)
    created_guide_id = None
    
    # Step 1: Create duplicate guide via UI
    logger.info("Создаём дубль гида для теста lookup")
    
    await guide_page.open_new_guide_form()
    
    duplicate_guide_data = {
        "name": "Георгий Челидзе",
        "description": "Тестовый гид для проверки lookup",
        "countries": ["TR"]
    }
    
    await guide_page.fill_guide_form(duplicate_guide_data)
    await guide_page.submit_guide_form()
    
    # Get created guide ID from success page
    success = await guide_page.wait_for_guide_success()
    assert success, "Guide creation failed"
    created_guide_id = await guide_page.get_success_guide_id()
    logger.info(f"✓ Дубль гида создан с ID: {created_guide_id}")
    
    # Mark for cleanup
    clean_test_guide.append(created_guide_id)
        
    # Arrange
    review_form = ReviewFormPage(page, frontend_url)
    search_query = "Геор"  # Partial name to search
    expected_guide_name = "Георгий Челидзе"  # Expected guide from seed data

    # Step 2: Open appropriate review form
    if form_type == "guide_review":
        logger.info("TEST-009a: Testing guide lookup in guide review form")

        # Open guide review form directly
        await page.goto(f"{frontend_url}/reviews/new?type=guide")
        await review_form.wait_for_review_form("guide")

        logger.info("✓ Guide review form opened")

    else:  # company_review
        logger.info("TEST-009b: Testing guide lookup in company review form (GuidesSelector)")

        # Open company review form
        await page.goto(f"{frontend_url}/reviews/new?type=company")
        await review_form.wait_for_review_form("company")

        logger.info("✓ Company review form opened")

    # Step 3: Type partial guide name and wait for dropdown
    await review_form.type_guide_name_and_wait_dropdown(search_query, form_type="company" if form_type == "company_review" else "guide")

    logger.info(f"✓ Typed '{search_query}' and dropdown appeared")

    # Step 4: Get all dropdown items
    items = await review_form.get_guide_dropdown_items()

    assert len(items) >= 2, f"Expected at least 2 guides with name '{expected_guide_name}', found {len(items)}"
    logger.info(f"✓ Found {len(items)} guide(s) in dropdown")

    # Step 5: Verify both guides have the expected name and different extended info
    guides_with_expected_name = [item for item in items if expected_guide_name in item['name']]
    assert len(guides_with_expected_name) >= 2, f"Expected at least 2 guides named '{expected_guide_name}'"

    # Verify each guide has extended info
    line2_contents = []
    for i, item in enumerate(guides_with_expected_name):
        guide_name = item['name']
        line2 = item['line2']

        assert line2, f"Guide '{guide_name}' missing extended information (line 2)"
        assert '🌍' in line2, f"Guide '{guide_name}' missing countries icon"

        line2_contents.append(line2)
        logger.info(f"  Guide {i+1}: {guide_name}")
        logger.info(f"    Info: {line2}")

    # Verify guides have different extended info (different countries or contacts)
    unique_line2 = set(line2_contents)
    assert len(unique_line2) >= 2, "Guides should have different extended info to distinguish them"
    logger.info(f"✓ Guides have different extended info ({len(unique_line2)} unique variants)")
    
    logger.info(f"✓ TEST-009{' a' if form_type == 'guide_review' else 'b'} completed: Extended info helps distinguish duplicate guides")

