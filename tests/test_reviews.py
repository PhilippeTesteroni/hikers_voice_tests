"""E2E tests for review creation functionality."""
import re
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage
from pages import ReviewFormPage
from pages import GuidePage
from pages import CompanyPage
from pages import ReviewsPage
from utils.test_helper import TestHelper
from utils.rating_calculator import RatingCalculator

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("rating", [1, 5])
async def test_create_company_review_with_autocomplete(
    page: Page,
    api_client: Dict[str, Any],
    review_test_data: dict,
    rating: int,
    clean_test_review: list,
    frontend_url: str,
    backend_url: str
):
    """
    E2E test for creating company review with autocomplete and moderation.
    
    Steps:
        1. Open home page
        2. Click 'Leave Review' button
        3. Select company review type in modal
        4. Fill review form with autocomplete
        5. Submit form
        6. Check redirect with success parameter
        7. Moderate review via API
        8. Check review display on home page
    
    Args:
        page: Playwright Page instance
        api_client: API client for moderation
        review_test_data: Test data fixture
        rating: Star rating (parametrized 1-5)
        clean_test_review: Cleanup fixture for created reviews
        frontend_url: Frontend base URL
        backend_url: Backend API URL
    """
    
    # Arrange - prepare test data
    
    # Prepare trip dates
    date_to = datetime.now() - timedelta(days=5)
    date_from = date_to - timedelta(days=5)
    
    # Review data
    review_data = {
        "country_code": "GE",  # Georgia
        "company_name": "Svaneti",  # For autocomplete search
        "select_autocomplete": True,  # Select from dropdown
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": rating,
        "text": f"""Excellent mountain tour organization in Svaneti.
Professional guides, quality equipment, delicious food on the route.
The route was challenging but safety was at a high level.
Rating {rating} out of 5 stars. Highly recommended!""",
        "author_name": f"Test User {rating}",
        "author_contact": f"test_{rating}@example.com",
        "rules_accepted": True
    }
    
    # Act - execute test
    
    # Step 1: Open home page
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    
    # Step 2: Click 'Leave Review' button
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)  # Wait for animation

    # Step 3: Select company review type in modal
    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    
    await review_form.select_review_type_in_modal("company")
    
    # Wait for form to load
    await review_form.wait_for_review_form()
    
    # Step 4: Fill review form
    # Use Page Object methods instead of direct locator access
    
    # 4.1: Select country
    await review_form.select_country(review_data["country_code"])
    
    # 4.2: Fill company name with autocomplete
    await review_form.fill_company_name_with_autocomplete("Svaneti")
    
    # 4.3: Fill trip dates
    await review_form.fill_trip_dates(
        review_data["trip_date_from"],
        review_data["trip_date_to"]
    )
    
    # 4.4: Set rating
    await review_form.set_rating(rating)
    
    # 4.5: Fill review text
    await review_form.fill_review_text(review_data["text"])
    
    # 4.6: Fill author info
    await review_form.fill_author_info(
        review_data["author_name"],
        review_data["author_contact"]
    )
    
    # 4.7: Accept rules
    await review_form.accept_rules()

    # Step 5: Submit form
    await review_form.submit_form()
    
    # Step 6: Wait for redirect with success parameter
    await review_form.wait_for_success_redirect(timeout=15000)
    assert "success=review_created" in page.url, f"Expected success redirect, got: {page.url}"
    
    # Step 7: Moderate review via API
    test_helper = TestHelper(backend_url)
    review_id = await test_helper.find_and_moderate_review(
        author_name=review_data["author_name"],
        action="approve"
    )
    
    assert review_id is not None, f"Failed to find and moderate review for author {review_data['author_name']}"
    clean_test_review.append(review_id)
    await test_helper.close()
    
    await page.wait_for_timeout(1000)  # Wait for DB update after moderation
    
    # Step 8: Refresh page
    await page.reload()
    await home_page.wait_for_load()
    
    # Step 9: Check review display on home page
    
    # Wait for reviews to load
    await home_page.wait_for_reviews_to_load()
    
    # Check review count
    reviews_count = await home_page.get_review_cards_count()
    assert reviews_count > 0, f"Expected at least one review, but found {reviews_count}"

    
    # Find review by author name
    review_card = await home_page.find_review_by_author(review_data["author_name"])
    assert review_card is not None, f"Review by author {review_data['author_name']} not found"
    
    # Check review card content (text truncated to 120 chars)
    has_expected_text = await home_page.check_review_card_content(
        review_card, 
        review_data["text"],
        truncated=True
    )
    assert has_expected_text, "Review card does not contain expected truncated text"
    
    # Get review card info
    card_info = await home_page.get_review_card_info(review_card)

    
    # Verify card info
    assert card_info.get('author') == review_data["author_name"], f"Author mismatch: {card_info.get('author')} != {review_data['author_name']}"
    assert card_info.get('has_rating'), "Rating not displayed on card"
    
    # Step 10: Check full review page
    
    # Click 'Read' to open full review
    await home_page.click_read_review(review_card)
    
    # Verify we're on review page
    await page.wait_for_url("**/reviews/**")
    current_url = page.url
    assert "/reviews/" in current_url, f"Not on review page, URL: {current_url}"
    
    # Extract review ID from URL (format: /reviews/123)
    import re
    match = re.search(r'/reviews/(\d+)', current_url)
    assert match is not None, f"Could not extract review ID from URL: {current_url}"
    
    actual_review_id = int(match.group(1))
    if review_id and review_id in clean_test_review:
        clean_test_review.remove(review_id)
    clean_test_review.append(actual_review_id)
    review_id = actual_review_id

    # Check full review text
    full_review_text = await home_page.get_full_review_text()
    
    # Verify each line from original text is present
    expected_lines = review_data["text"].strip().split('\n')
    for line in expected_lines:
        line_normalized = ' '.join(line.split())
        review_normalized = ' '.join(full_review_text.split())
        assert line_normalized in review_normalized, f"Line not found in review: {line_normalized}"
    
    # Check rating display
    assert await home_page.check_rating_on_review_page(rating), f"Rating {rating}/5 not displayed on review page"
    
    # Check author name display
    assert await home_page.check_author_on_review_page(review_data['author_name']), \
        f"Author name '{review_data['author_name']}' not found on review page"
    
    # Step 11: Navigate to company page and verify rating/reviews count
    # Get company name from review page where we currently are
    company_link = await page.query_selector("a[href*='/companies/']")
    assert company_link is not None, "Company link not found on review page"
    
    company_name = await company_link.text_content()
    company_href = await company_link.get_attribute("href")
    
    # Extract company ID from href like "/companies/123"
    match = re.search(r'/companies/(\d+)', company_href)
    assert match is not None, f"Could not extract company ID from href: {company_href}"
    
    company_id = int(match.group(1))
    logger.info(f"Review is for company: {company_name} (ID: {company_id})")
    
    # Navigate to company page
    company_page = CompanyPage(page)
    await company_page.open_company_page(company_id)
    current_rating = await company_page.get_company_rating()
    current_reviews_count = await company_page.get_company_reviews_count()
    
    logger.info(f"Company page - Rating: {current_rating}, Reviews count: {current_reviews_count}")
    
    # Verify review count is positive
    assert current_reviews_count > 0, f"Expected at least 1 review on company page, got {current_reviews_count}"
    
    # Verify rating is displayed and within valid range
    assert current_rating is not None, "Rating element not found on company page"
    assert 1.0 <= current_rating <= 5.0, f"Rating should be between 1.0 and 5.0, got {current_rating}"
    logger.info(f"✓ Company rating verified: {current_rating:.1f}/5.0 with {current_reviews_count} reviews")
    
    # Test completed successfully
    logger.info(f"TEST-001 completed: review_id={review_id if review_id else 'N/A'}, rating={rating}/5")


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("rating", [1, 5])
async def test_create_guide_review_with_autocomplete(
    page: Page,
    api_client: Dict[str, Any],
    review_test_data: dict,
    rating: int,
    clean_test_review: list,
    frontend_url: str,
    backend_url: str
):
    """
    TEST-002: Create review for an existing guide with autocomplete.
    
    Tests the complete flow of creating a guide review including:
    - Guide selection via autocomplete
    - Anonymous author handling
    - Rating calculation verification
    - Multi-page review display
    
    Args:
        page: Playwright Page instance
        api_client: API client for moderation
        review_test_data: Test data fixture
        clean_test_review: Cleanup fixture for created reviews
        frontend_url: Frontend base URL
        backend_url: Backend API URL
    """
    
    # Arrange - prepare test data
    date_from = datetime.now() - timedelta(days=20)
    date_to = datetime.now() - timedelta(days=15)
    
    # Adjust review text based on rating
    if rating == 5:
        review_text = "Отличный гид! Профессионал, знает маршруты как свои пять пальцев. Все на высшем уровне!"
    else:  # rating == 1
        review_text = "Очень разочарован. Не рекомендую."
    
    review_data = {
        "country_code": "RU",
        "guide_search": "Георгий",
        "guide_name": "Георгий Челидзе",
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": rating,
        "text": review_text,
        "author_name": "",  # Empty for anonymity
        "author_contact": "+7 900 123-45-67",
        "rules_accepted": True
    }
    
    # Act - execute test
    
    # Get initial guide stats
    guide_page = GuidePage(page, frontend_url)
    await guide_page.open_guide_page(1)
    initial_rating = await guide_page.get_guide_rating()
    initial_reviews_count = await guide_page.get_reviews_count()
    
    # Open home page and create review
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    
    # Open review form
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)
    
    # Select guide review type
    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal("guide")
    
    # Wait for form to load
    await page.wait_for_selector("select[name='country_code']", timeout=10000)
    await page.wait_for_timeout(500)
    
    # Fill the form
    await review_form.select_country(review_data["country_code"])
    await review_form.fill_guide_name_with_autocomplete(
        review_data["guide_search"],
        review_data["guide_name"]
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
    
    # Submit form
    await review_form.submit_form()
    
    # Wait for redirect with success parameter
    await review_form.wait_for_success_redirect(timeout=15000)
    assert "success=review_created" in page.url, f"Expected success redirect, got: {page.url}"
    
    # Moderate review via API
    test_helper = TestHelper(backend_url)
    review_id = await test_helper.find_and_moderate_review(
        author_name="Аноним",  # Empty name becomes "Аноним"
        action="approve"
    )
    assert review_id is not None, "Failed to find and moderate anonymous review"
    clean_test_review.append(review_id)
    await test_helper.close()

    await page.wait_for_timeout(1000)

    # Assert - verify results
    # Check guide page (Georgy Chelidze is guide ID 1)
    await guide_page.open_guide_page(1)

    # Verify guide name
    guide_name = await guide_page.get_guide_name()
    assert "Георгий Челидзе" in guide_name, f"Expected guide name not found: {guide_name}"

    # Get updated stats
    updated_rating = await guide_page.get_guide_rating()
    updated_reviews_count = await guide_page.get_reviews_count()
    
    logger.info(f"Guide page stats - Rating: {updated_rating}, Reviews: {updated_reviews_count}")

    # Verify review count is displayed correctly
    assert updated_reviews_count == initial_reviews_count + 1, \
        f"Reviews count should increase by 1: was {initial_reviews_count}, now {updated_reviews_count}"
    
    # Verify rating is displayed and within valid range
    assert updated_rating is not None, "Rating element not found on guide page"
    assert 1.0 <= updated_rating <= 5.0, f"Rating should be between 1.0 and 5.0, got {updated_rating}"
    logger.info(f"Guide rating verified: {updated_rating:.1f}/5.0 with {updated_reviews_count} reviews")
    
    # Verify rating calculation (with tolerance for backend rounding)
    rating_calc = RatingCalculator()
    expected_rating, _ = rating_calc.calculate_new_rating(
        initial_rating,
        initial_reviews_count,
        rating
    )
    
    # Allow 0.05 tolerance for rounding
    is_correct, explanation = rating_calc.verify_rating_change(
        initial_rating,
        initial_reviews_count,
        rating,
        updated_rating,
        updated_reviews_count,
        tolerance=0.05
    )
    assert is_correct, f"Rating calculation error: {explanation}"
    logger.info(f"Rating calculation verified: {explanation}")

    # Verify review exists
    review_found = await guide_page.check_review_exists(
        author_name="",
        review_text=review_data["text"][:50]
    )
    assert review_found, "Review not found on guide page"

    # Get review element for detailed checks
    review_element = await guide_page.get_review_by_author("")
    assert review_element is not None, "Could not find anonymous review element"

    # Check anonymous author
    review_content = await review_element.text_content()
    assert "Автор: Аноним" in review_content, "Author not shown as anonymous"

    # Check review text
    assert await guide_page.check_review_text(review_element, review_data["text"][:100]), \
        "Review text does not match"

    # Check rating stars
    assert await guide_page.check_review_rating(review_element, review_data["rating"]), \
        f"Rating does not show {review_data['rating']} stars"

    # Check main page
    await home_page.open()
    await home_page.wait_for_reviews_to_load()

    main_page_review = await home_page.find_review_by_author("Аноним")
    assert main_page_review is not None, "Review not found on main page"

    # Check reviews page
    reviews_page = ReviewsPage(page, frontend_url)
    await reviews_page.open()

    reviews_page_found = await reviews_page.check_review_exists(
        author_name="",
        review_text=review_data["text"][:50]
    )
    assert reviews_page_found, "Review not found on Reviews page"
    
    # Step: Navigate to guides catalog and verify rating/reviews count on guide card
    # Get guide name and ID from review page where we currently are
    guide_link = await page.query_selector("a[href*='/guides/']")
    assert guide_link is not None, "Guide link not found on review page"
    
    guide_name_from_review = await guide_link.text_content()
    guide_href = await guide_link.get_attribute("href")
    
    # Extract guide ID from href like "/guides/123"
    match = re.search(r'/guides/(\d+)', guide_href)
    assert match is not None, f"Could not extract guide ID from href: {guide_href}"
    
    guide_id = int(match.group(1))
    logger.info(f"Review is for guide: {guide_name_from_review} (ID: {guide_id})")
    
    # Navigate to guides catalog
    await page.goto(f"{frontend_url}/guides")
    await page.wait_for_load_state("networkidle")
    
    # Find guide card by exact guide name from review
    guide_card = await page.query_selector(f"article.card:has-text('{guide_name_from_review}')")
    assert guide_card is not None, f"Guide card for '{guide_name_from_review}' not found in catalog"
    
    # Get rating from card - Rating component shows score in <span class="text-sm font-medium">
    card_rating_element = await guide_card.query_selector("span.text-sm.font-medium")
    assert card_rating_element is not None, "Rating element not found on guide card"
    
    rating_text = await card_rating_element.text_content()
    assert rating_text, f"Rating text is empty on card"
    
    # Rating is displayed as "3.7" without "/5"
    card_rating = float(rating_text.strip())
    logger.info(f"Guide card - Rating: {card_rating}")
    
    # Verify rating matches the one from guide page
    assert abs(card_rating - updated_rating) < 0.1, \
        f"Card rating {card_rating} doesn't match guide page rating {updated_rating}"
    
    # Get reviews count from card - look for pattern like "3 отзыва" or "1 отзыв"
    card_content = await guide_card.text_content()
    reviews_match = re.search(r'(\d+)\s+отзыв', card_content)
    assert reviews_match is not None, "Reviews count not found on guide card"
    
    card_reviews_count = int(reviews_match.group(1))
    logger.info(f"Guide card - Reviews count: {card_reviews_count}")
    
    # Verify count matches
    assert card_reviews_count == updated_reviews_count, \
        f"Card shows {card_reviews_count} reviews but guide page shows {updated_reviews_count}"
    logger.info(f"✓ Guide card stats verified: {card_rating}/5.0 with {card_reviews_count} reviews")

    # Test completed successfully
    logger.info(f"TEST-002 completed: review_id={review_id}, rating={rating}/5")


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
        await page.wait_for_selector("input[placeholder*='Начните вводить название компании']", state="visible", timeout=10000)
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
