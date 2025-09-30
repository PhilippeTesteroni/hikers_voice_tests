"""E2E tests for review creation functionality."""
import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage
from pages import ReviewFormPage
from pages import GuidePage
from pages import ReviewsPage
from utils.test_helper import TestHelper
from utils.rating_calculator import RatingCalculator

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("rating", [5])
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
    
    # Step 6: Check redirect with success parameter
    await page.wait_for_url(f"{frontend_url}/?success=review_created", timeout=10000)
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

    # Test completed successfully
    logger.info(f"TEST-001 completed: review_id={review_id if review_id else 'N/A'}")


@pytest.mark.e2e
@pytest.mark.critical
async def test_create_guide_review_with_autocomplete(
    page: Page,
    api_client: Dict[str, Any],
    review_test_data: dict,
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
    
    review_data = {
        "country_code": "RU",
        "guide_search": "Георгий",
        "guide_name": "Георгий Челидзе",
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": 4,
        "text": "Хороший гид, знает маршруты. Немного не хватило организованности с тайм-менеджментом, но в целом всё понравилось.",
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
    
    # Verify redirect
    await page.wait_for_url(f"{frontend_url}/?success=review_created", timeout=10000)
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
    # Check guide page
    await guide_page.open_guide_page(1)

    # Verify guide name
    guide_name = await guide_page.get_guide_name()
    assert "Георгий Челидзе" in guide_name, f"Expected guide name not found: {guide_name}"

    # Get updated stats
    updated_rating = await guide_page.get_guide_rating()
    updated_reviews_count = await guide_page.get_reviews_count()

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

    # Verify reviews count increased
    assert updated_reviews_count == initial_reviews_count + 1, \
        f"Reviews count should increase by 1: was {initial_reviews_count}, now {updated_reviews_count}"

    # Verify rating calculation (with tolerance for backend rounding)
    if updated_rating is not None:
        rating_calc = RatingCalculator()
        expected_rating, _ = rating_calc.calculate_new_rating(
            initial_rating,
            initial_reviews_count,
            review_data["rating"]
        )

        # Backend rounds to 1 decimal, allow 0.05 tolerance
        is_correct, explanation = rating_calc.verify_rating_change(
            initial_rating,
            initial_reviews_count,
            review_data["rating"],
            updated_rating,
            updated_reviews_count,
            tolerance=0.05
        )
        assert is_correct, f"Rating calculation error: {explanation}"

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

    # Test completed successfully
    logger.info(f"TEST-002 completed: review_id={review_id}")
