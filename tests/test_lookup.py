"""E2E test for guide lookup/autocomplete in review forms.

REFACTORED: Creates unique duplicate guides via API, no seed data dependency.
"""

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
    frontend_api_client,
    clean_test_guide: list,
    form_type: str
):
    """
    TEST-009 REFACTORED: Test guide lookup with extended information display.
    
    Creates two guides with same name but different countries via API,
    then tests that autocomplete shows both with distinguishing info.
    
    Parametrized test with two scenarios:
    - form_type="guide_review": Lookup in guide review form (main guide field)
    - form_type="company_review": Lookup in company review form (guides section)
    
    Steps:
    1. Create first guide via API (country: GE)
    2. Create duplicate guide with same name via API (country: TR)
    3. Open review form (guide or company)
    4. Type partial guide name in autocomplete
    5. Wait for dropdown to appear
    6. Verify dropdown shows both guides with extended information
    7. Verify extended info includes countries and distinguishes duplicates
    8. Cleanup: delete both created guides
    
    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        frontend_api_client: API client for creating guides
        clean_test_guide: Cleanup fixture for guides
        form_type: Type of form ("guide_review" or "company_review")
    """
    
    # Step 1 & 2: Create two guides with same name but different countries
    logger.info("Creating two guides with same name for lookup test")
    
    guide_base_name = "Lookup Test Guide"
    
    # First guide - Georgia
    guide1 = await frontend_api_client.create_guide(
        name=guide_base_name,
        countries=["GE"],
        description="First guide for testing lookup functionality",
        contact_telegram="@lookuptest1"
    )
    clean_test_guide.append(guide1["id"])
    logger.info(f"✓ Created guide 1: ID={guide1['id']}, Name={guide1['name']}, Countries=GE")
    
    # Second guide - same name, different country (Turkey)
    guide2 = await frontend_api_client.create_guide(
        name=guide_base_name,
        countries=["TR"],
        description="Second guide for testing lookup functionality",
        contact_telegram="@lookuptest2",
        force_create=True  # Force creation despite duplicate name
    )
    clean_test_guide.append(guide2["id"])
    logger.info(f"✓ Created guide 2: ID={guide2['id']}, Name={guide2['name']}, Countries=TR")
    
    # Step 3: Open appropriate review form
    review_form = ReviewFormPage(page, frontend_url)
    
    # Extract search query from guide name (unique timestamp part)
    # E.g., "Lookup Test Guide TEST-20250104_153045" -> "Lookup Test Guide TEST"
    search_query = " ".join(guide1["name"].split()[:4])  # First 4 words should be unique enough
    expected_guide_name = guide1["name"]  # Both guides have same base name + timestamp
    
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
    
    # Step 4: Type partial guide name and wait for dropdown
    await review_form.type_guide_name_and_wait_dropdown(
        search_query, 
        form_type="company" if form_type == "company_review" else "guide"
    )
    
    logger.info(f"✓ Typed '{search_query}' and dropdown appeared")
    
    # Step 5: Get all dropdown items
    items = await review_form.get_guide_dropdown_items()
    
    assert len(items) >= 2, f"Expected at least 2 guides in dropdown, found {len(items)}"
    logger.info(f"✓ Found {len(items)} guide(s) in dropdown")
    
    # Step 6: Verify both guides appear in dropdown
    # Both guides should have the same base name (with timestamp)
    guides_with_expected_name = [
        item for item in items 
        if guide_base_name.split()[0] in item['name']  # Match by first word "Lookup"
    ]
    
    assert len(guides_with_expected_name) >= 2, \
        f"Expected at least 2 guides matching '{guide_base_name}', found {len(guides_with_expected_name)}"
    
    # Step 7: Verify each guide has extended info with countries
    line2_contents = []
    for i, item in enumerate(guides_with_expected_name[:2]):  # Check first 2 matches
        guide_name = item['name']
        line2 = item['line2']
        
        assert line2, f"Guide '{guide_name}' missing extended information (line 2)"
        assert '🌍' in line2, f"Guide '{guide_name}' missing countries icon"
        
        line2_contents.append(line2)
        logger.info(f"  Guide {i+1}: {guide_name}")
        logger.info(f"    Extended info: {line2}")
    
    # Step 8: Verify guides have different extended info (different countries)
    unique_line2 = set(line2_contents)
    assert len(unique_line2) >= 2, \
        "Guides should have different extended info to distinguish them. " \
        f"Both showed: {line2_contents}"
    
    # Verify one has "Грузия" (Georgia) and other has "Турция" (Turkey)
    has_georgia = any("Грузия" in info or "Georgia" in info for info in line2_contents)
    has_turkey = any("Турция" in info or "Turkey" in info for info in line2_contents)
    
    assert has_georgia, f"No guide shows Georgia. Extended info: {line2_contents}"
    assert has_turkey, f"No guide shows Turkey. Extended info: {line2_contents}"
    
    logger.info(f"✓ Guides have different extended info ({len(unique_line2)} unique variants)")
    logger.info(f"✓ Verified: One guide shows Georgia, another shows Turkey")
    
    logger.info(
        f"✅ TEST-009{'a' if form_type == 'guide_review' else 'b'} PASSED: "
        f"Extended info correctly distinguishes duplicate guides. "
        f"Created guides: {guide1['id']}, {guide2['id']} - cleanup will be automatic."
    )
