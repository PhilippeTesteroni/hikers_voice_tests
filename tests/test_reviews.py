"""
E2E tests for review creation functionality - REFACTORED VERSION.

This version uses FrontendApiClient to create unique companies/guides for each test,
ensuring proper test isolation and avoiding dependency on seed data.
"""
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage, ReviewFormPage, GuidePage, CompanyPage
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("rating", [1, 5])
async def test_create_company_review_with_autocomplete_refactored(
    page: Page,
    api_client: Dict[str, Any],
    frontend_api_client,
    review_test_data: dict,
    rating: int,
    clean_test_review: list,
    clean_test_company: list,
    frontend_url: str,
    backend_url: str
):
    """
    TEST-001 REFACTORED: Create company review using unique test company.
    
    Full test isolation - each run creates its own unique company via API,
    submits review through UI, and verifies display on all pages.
    
    Improvements over original:
    - No dependency on seed data
    - Guaranteed clean slate (new company with 0.0 rating, 0 reviews)
    - Exact autocomplete matching prevents selecting wrong company
    - Automatic cleanup of both review and company
    """
    
    # Step 1: Create unique test company via API
    test_company = await frontend_api_client.create_company(
        name="Mountain Adventures",  # Auto-timestamped for uniqueness
        country_code="GE",
        description="Professional mountain tours with experienced guides",
        contact_email="info@mountain-test.com",
        contact_phone="+995555123456"
    )
    clean_test_company.append(test_company["id"])
    logger.info(f"Created test company: ID={test_company['id']}, Name={test_company['name']}")
    
    # Step 2: Prepare review data
    date_to = datetime.now() - timedelta(days=5)
    date_from = date_to - timedelta(days=5)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    author_name = f"Test User {rating} *{timestamp}*"
    
    review_data = {
        "country_code": "GE",
        "company_search": test_company["name"][:10],  # First 10 chars for autocomplete
        "company_exact": test_company["name"],  # Full name for exact match
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": rating,
        "text": f"""Excellent mountain tour organization.
Professional guides, quality equipment, delicious food on the route.
The route was challenging but safety was at a high level.
Rating {rating} out of 5 stars. Highly recommended!""",
        "author_name": author_name,
        "author_contact": f"test_{rating}_{timestamp}@example.com",
    }
    
    # Step 3: Submit review via UI
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)

    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal("company")
    await review_form.wait_for_review_form()
    
    # Fill form with exact company matching
    await review_form.select_country(review_data["country_code"])
    await review_form.fill_company_name_with_autocomplete(
        search_text=review_data["company_search"],
        select_exact=review_data["company_exact"]  # Ensures correct company selection
    )
    await review_form.fill_trip_dates(
        review_data["trip_date_from"],
        review_data["trip_date_to"]
    )
    await review_form.set_rating(rating)
    await review_form.fill_review_text(review_data["text"])
    await review_form.fill_author_info(
        review_data["author_name"],
        review_data["author_contact"]
    )
    await review_form.accept_rules()
    await review_form.submit_form()
    
    # Step 4: Verify redirect
    await review_form.wait_for_success_redirect(timeout=15000)
    assert "success=review_created" in page.url
    
    # Step 5: Moderate review
    test_helper = TestHelper(backend_url)
    review_id = await test_helper.find_and_moderate_review(
        author_name=review_data["author_name"],
        action="approve",
        company_id=test_company["id"]  # ← Ensures we find OUR review
    )
    assert review_id is not None, f"Failed to moderate review for {review_data['author_name']}"
    clean_test_review.append(review_id)
    
    # Verify approval in DB
    response = await test_helper.client.get("/api/v1/test/reviews/all")
    assert response.status_code == 200
    all_reviews = response.json().get("reviews", [])
    our_review = next((r for r in all_reviews if r["id"] == review_id), None)
    assert our_review is not None and our_review["status"] == "approved"
    
    logger.info(f"Review {review_id} approved and linked to company {test_company['id']}")
    await test_helper.close()
    
    # Step 6: Verify on home page
    await home_page.open()
    await home_page.wait_for_load()
    await home_page.wait_for_reviews_to_load()
    
    # Find review by author (ISR cache issue fixed, no retries needed)
    review_card = await home_page.find_review_by_author(review_data["author_name"])
    assert review_card is not None, f"Review not found on home page for author {review_data['author_name']}"
    
    has_text = await home_page.check_review_card_content(review_card, review_data["text"], truncated=True)
    assert has_text, "Review card text mismatch"
    
    # Step 7: Verify on company page
    company_page = CompanyPage(page)
    await company_page.open_company_page(test_company["id"])
    await page.wait_for_load_state("networkidle")
    
    # Get company stats (ISR cache issue fixed, no retries needed)
    current_rating = await company_page.get_company_rating()
    current_reviews_count = await company_page.get_company_reviews_count()
    
    # New company should have exactly 1 review with our rating
    assert current_reviews_count == 1, f"Expected 1 review, got {current_reviews_count}"
    assert current_rating == float(rating), f"Expected rating {rating}, got {current_rating}"
    
    logger.info(f"✅ TEST-001 PASSED: company={test_company['id']}, review={review_id}, rating={rating}/5")


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("rating", [1, 5])
async def test_create_guide_review_with_autocomplete_refactored(
    page: Page,
    api_client: Dict[str, Any],
    frontend_api_client,
    review_test_data: dict,
    rating: int,
    clean_test_review: list,
    clean_test_guide: list,
    frontend_url: str,
    backend_url: str
):
    """
    TEST-002 REFACTORED: Create guide review using unique test guide.
    
    Full test isolation - each run creates its own unique guide via API,
    submits anonymous review through UI, and verifies display.
    
    Improvements over original:
    - No dependency on seed data (was using hardcoded "Георгий Челидзе")
    - Clean baseline (new guide with 0.0 rating, 0 reviews)
    - Tests anonymous author handling
    - Automatic cleanup of both review and guide
    """
    
    # Step 1: Create unique test guide via API
    test_guide = await frontend_api_client.create_guide(
        name="Aleksandr Petrov",  # Auto-timestamped for uniqueness
        countries=["GE", "AM"],
        description="Experienced mountain guide with 10+ years",
        contact_phone="+995555987654",
        contact_telegram="@test_guide"
    )
    clean_test_guide.append(test_guide["id"])
    logger.info(f"Created test guide: ID={test_guide['id']}, Name={test_guide['name']}")
    
    # Step 2: Prepare review data
    date_from = datetime.now() - timedelta(days=20)
    date_to = datetime.now() - timedelta(days=15)
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    review_text = (
        f"Отличный гид! Профессионал, знает маршруты как свои пять пальцев. Test {timestamp}"
        if rating == 5
        else f"Очень разочарован. Не рекомендую. Test {timestamp}"
    )
    
    review_data = {
        "country_code": "GE",
        "guide_search": test_guide["name"][:10],
        "guide_exact": test_guide["name"],
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": rating,
        "text": review_text,
        "author_name": "",  # Anonymous
        "author_contact": "+7 900 123-45-67",
    }
    
    # Step 3: Submit review via UI
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)
    
    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal("guide")
    await page.wait_for_selector("select[name='country_code']", timeout=10000)
    await page.wait_for_timeout(500)
    
    await review_form.select_country(review_data["country_code"])
    await review_form.fill_guide_name_with_autocomplete(
        review_data["guide_search"],
        review_data["guide_exact"]
    )
    await review_form.fill_trip_dates(
        review_data["trip_date_from"],
        review_data["trip_date_to"]
    )
    await review_form.set_rating(review_data["rating"])
    await review_form.fill_review_text(review_data["text"])
    await review_form.fill_author_info(
        review_data["author_name"],
        review_data["author_contact"]
    )
    await review_form.accept_rules()
    await review_form.submit_form()
    
    # Step 4: Verify redirect
    await review_form.wait_for_success_redirect(timeout=15000)
    assert "success=review_created" in page.url
    
    # Step 5: Moderate review
    test_helper = TestHelper(backend_url)
    review_id = await test_helper.find_and_moderate_review(
        author_name="Аноним",  # Empty name becomes "Аноним"
        action="approve",
        guide_id=test_guide["id"]  # ← Ensures we find OUR review
    )
    assert review_id is not None, "Failed to moderate anonymous review"
    clean_test_review.append(review_id)
    await test_helper.close()

    await page.wait_for_timeout(1000)

    # Step 6: Verify on guide page
    guide_page = GuidePage(page, frontend_url)
    await guide_page.open_guide_page(test_guide["id"])
    await page.wait_for_load_state("networkidle")

    # Verify guide name
    guide_name = await guide_page.get_guide_name()
    assert test_guide["name"] in guide_name

    # Verify stats (ISR cache issue fixed, no retries needed)
    updated_rating = await guide_page.get_guide_rating()
    updated_reviews_count = await guide_page.get_reviews_count()
    
    assert updated_reviews_count == 1, f"Expected 1 review, got {updated_reviews_count}"
    assert updated_rating == float(rating), f"Expected rating {rating}, got {updated_rating}"
    
    logger.info(f"Guide stats: {updated_rating}/5.0 with {updated_reviews_count} review(s)")
    
    # Verify review content
    review_found = await guide_page.check_review_exists(
        author_name="",
        review_text=review_data["text"][:50]
    )
    assert review_found, "Review not found on guide page"

    logger.info(f"✅ TEST-002 PASSED: guide={test_guide['id']}, review={review_id}, rating={rating}/5")


@pytest.mark.e2e
@pytest.mark.parametrize("review_type,entity_field_placeholder", [
    ("company", "Начните вводить название компании"),
    ("guide", "Начните вводить имя гида"),
])
async def test_review_form_validation_errors(
        page: Page,
        frontend_url: str,
        review_type: str,
        entity_field_placeholder: str
):
    """
    TEST-004: Test form validation for review creation (both company and guide forms).

    Tests validation errors for review forms including:
    - Required fields validation
    - Minimum/maximum text length
    - Rating requirement
    - Rules acceptance requirement
    - Submit button state based on form completeness

    Args:
        page: Playwright Page instance
        frontend_url: Frontend base URL
        review_type: Type of review - 'company' or 'guide'
        entity_field_placeholder: Placeholder text for company/guide input field
    """

    # Arrange
    home_page = HomePage(page, frontend_url)
    review_form = ReviewFormPage(page, frontend_url)

    # Act - Navigate to review form
    await home_page.open()
    await home_page.wait_for_load()

    # Open review form modal
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)

    # Select review type (company or guide)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal(review_type)

    # Wait for form to load - different elements for company vs guide
    if review_type == "company":
        await page.wait_for_selector("input[placeholder*='Начните вводить название компании']", state="visible",
                                     timeout=10000)
    else:  # guide
        await page.wait_for_selector("input[placeholder*='Начните вводить имя гида']", state="visible", timeout=10000)

    # Test 1: Verify submit button is disabled when form is empty
    submit_button = page.locator("button[type='submit']:has-text('Отправить отзыв')")
    await submit_button.wait_for(state="visible")
    is_disabled = await submit_button.is_disabled()
    assert is_disabled, "Submit button should be disabled for empty form"

    # Test 2: Test minimum text length validation
    text_area_locator = page.locator("textarea[name='text']")
    await text_area_locator.click()
    await text_area_locator.fill("Короткий")  # Less than 10 characters
    await text_area_locator.blur()  # Trigger validation
    await page.wait_for_timeout(500)

    # Check if error appears
    text_error = page.locator(".text-red-600").filter(has_text="символ")
    await text_error.wait_for(state="visible", timeout=2000)
    error_text = await text_error.text_content()
    assert "10 символов" in error_text, f"Expected min length error, got: {error_text}"

    # Test 3: Test maximum text length validation
    await text_area_locator.fill("")
    very_long_text = "A" * 4001  # Exceeds 4000 character limit
    await text_area_locator.fill(very_long_text)
    await text_area_locator.blur()
    await page.wait_for_timeout(500)

    max_length_error = page.locator(".text-red-600").filter(has_text="4000")
    await max_length_error.wait_for(state="visible", timeout=2000)
    error_text = await max_length_error.text_content()
    assert "4000" in error_text, f"Expected max length error, got: {error_text}"

    # Test 4: Fill all required fields to enable submit button (except rules)
    await review_form.select_country("GE")

    # Fill company or guide name based on review type
    entity_input = page.locator(f"input[placeholder*='{entity_field_placeholder}']")
    test_entity_name = "Test Company" if review_type == "company" else "Test Guide"
    await entity_input.fill(test_entity_name)

    # Fill dates
    past_date_from = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    past_date_to = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")
    await review_form.fill_trip_dates(past_date_from, past_date_to)

    # Set rating
    await review_form.set_rating(5)

    # Fill valid text
    await text_area_locator.fill("Это нормальный текст отзыва для тестирования валидации формы")

    # Check that submit button is still disabled without rules acceptance
    await page.wait_for_timeout(500)
    is_disabled = await submit_button.is_disabled()
    assert is_disabled, "Submit button should be disabled without rules acceptance"

    # Test 5: Accept rules - button should become enabled
    await review_form.accept_rules()
    await page.wait_for_timeout(500)

    # Now submit button should be enabled
    is_disabled = await submit_button.is_disabled()
    assert not is_disabled, "Submit button should be enabled when all fields are valid"

    # Test 6: Uncheck rules - button should be disabled again
    rules_checkbox = page.locator("input[type='checkbox'][name='rules_accepted']")
    await rules_checkbox.uncheck()
    await page.wait_for_timeout(500)

    # Button should be disabled again
    is_disabled = await submit_button.is_disabled()
    assert is_disabled, "Submit button should be disabled when rules not accepted"

    # Test completed successfully
    logger.info(f"TEST-004 completed for {review_type} form: All validation rules work correctly")