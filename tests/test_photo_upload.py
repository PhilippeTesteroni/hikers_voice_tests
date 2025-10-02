"""
E2E tests for photo upload functionality in reviews.
Tests photo upload for both company and guide reviews.
"""

import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage
from pages import ReviewFormPage
from pages import ReviewsPage
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("review_type,photo_count", [
    ("company", 1),  # Boundary: minimum photos (1)
    ("company", 5),  # Boundary: maximum photos (5)
    ("guide", 1),    # Boundary: minimum photos (1)
    ("guide", 5),    # Boundary: maximum photos (5)
])
async def test_review_with_photos(
    page: Page,
    api_client: Dict[str, Any],
    review_test_data: dict,
    clean_test_review: list,
    frontend_url: str,
    backend_url: str,
    test_images: list[str],
    review_type: str,
    photo_count: int
):
    """
    E2E test for creating reviews with photos (company and guide).
    
    Tests boundary values:
    - 1 photo (minimum)
    - 5 photos (maximum)
    
    Steps:
        1. Open home page
        2. Click 'Leave Review' button
        3. Select review type (company or guide) in modal
        4. Fill review form
        5. Upload photos (1 or 5 depending on parametrization)
        6. Verify photo previews in form
        7. Submit form
        8. Check redirect with success parameter
        9. Moderate review via API
        10. Navigate to review detail page
        11. Verify photos are displayed in gallery
        12. Test photo lightbox functionality
    
    Args:
        page: Playwright Page instance
        api_client: API client for moderation
        review_test_data: Test data fixture
        clean_test_review: Cleanup fixture for created reviews
        frontend_url: Frontend base URL
        backend_url: Backend API URL
        test_images: List of test image paths
        review_type: Type of review ('company' or 'guide')
        photo_count: Number of photos to upload (1 or 5)
    """
    
    # Arrange - prepare test data based on review type
    date_from = datetime.now() - timedelta(days=20)
    date_to = datetime.now() - timedelta(days=15)
    
    author_name = f"Test Photo User {review_type} {photo_count}p"
    
    if review_type == "company":
        review_data = {
            "country_code": "GE",
            "company_name": "Svaneti",  # Existing company for autocomplete
            "select_autocomplete": True,
            "trip_date_from": date_from.strftime("%Y-%m-%d"),
            "trip_date_to": date_to.strftime("%Y-%m-%d"),
            "rating": 5,
            "text": f"Отличная компания! Проверка загрузки {photo_count} фотографий. " * 3,
            "author_name": author_name,
            "author_contact": f"test_photo_{review_type}_{photo_count}@example.com",
            "rules_accepted": True
        }
    else:  # guide
        review_data = {
            "country_code": "RU",
            "guide_search": "Георгий",
            "guide_name": "Георгий Челидзе",
            "trip_date_from": date_from.strftime("%Y-%m-%d"),
            "trip_date_to": date_to.strftime("%Y-%m-%d"),
            "rating": 5,
            "text": f"Отличный гид! Проверка загрузки {photo_count} фотографий. " * 3,
            "author_name": author_name,
            "author_contact": f"test_photo_{review_type}_{photo_count}@example.com",
            "rules_accepted": True
        }
    
    # Select photos to upload
    photos_to_upload = test_images[:photo_count]
    
    # Act - execute test
    
    # Step 1-2: Open home page and click 'Leave Review'
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)
    
    # Step 3: Select review type in modal
    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal(review_type)
    await review_form.wait_for_review_form(review_type)
    
    # Step 4: Fill review form based on type
    if review_type == "company":
        # Fill company review
        await review_form.select_country(review_data["country_code"])
        await review_form.fill_company_name_with_autocomplete(review_data["company_name"])
        await review_form.fill_trip_dates(
            review_data["trip_date_from"],
            review_data["trip_date_to"]
        )
    else:  # guide
        # Fill guide review
        await review_form.select_country(review_data["country_code"])
        await review_form.fill_guide_name_with_autocomplete(
            review_data["guide_search"],
            review_data["guide_name"]
        )
        await review_form.fill_trip_dates(
            review_data["trip_date_from"],
            review_data["trip_date_to"]
        )
    
    # Fill common fields
    await review_form.set_rating(review_data["rating"])
    await review_form.fill_review_text(review_data["text"])
    await review_form.fill_author_info(
        review_data["author_name"],
        review_data["author_contact"]
    )
    
    # Step 5: Scroll to photos section and upload photos
    await review_form.scroll_to_photos_section()
    await page.wait_for_timeout(500)
    await review_form.upload_photos(photos_to_upload)
    
    # Step 6: Verify photo previews are visible in form
    photos_count = await review_form.get_uploaded_photos_count()
    assert photos_count == photo_count, f"Expected {photo_count} photo previews, got {photos_count}"
    
    previews_visible = await review_form.verify_photo_previews_visible()
    assert previews_visible, "Not all photo previews are properly displayed"
    
    logger.info(f"Successfully uploaded and verified {photo_count} photos in form")
    
    # Accept rules and submit
    await review_form.accept_rules()
    
    # Step 7: Submit form
    await review_form.submit_form()
    
    # Step 8: Wait for redirect with success parameter
    # Use longer timeout for photo uploads (base64 encoding + upload takes time)
    timeout = 30000 if photo_count >= 5 else 15000
    await review_form.wait_for_success_redirect(timeout=timeout)
    assert "success=review_created" in page.url, f"Expected success redirect, got: {page.url}"
    
    # Step 9: Moderate review via API
    test_helper = TestHelper(backend_url)
    review_id = await test_helper.find_and_moderate_review(
        author_name=review_data["author_name"],
        action="approve"
    )
    
    assert review_id is not None, f"Failed to find and moderate review for author {review_data['author_name']}"
    clean_test_review.append(review_id)
    await test_helper.close()
    
    await page.wait_for_timeout(1000)
    
    # Step 10: Navigate to review detail page
    logger.info(f"Navigating to review detail page: /reviews/{review_id}")
    review_url = f"{frontend_url}/reviews/{review_id}"
    await page.goto(review_url)
    await page.wait_for_load_state("networkidle")
    
    # Verify we're on the review detail page
    assert f"/reviews/{review_id}" in page.url, f"Not on review detail page, URL: {page.url}"
    
    # Step 11: Verify photos are displayed in gallery
    reviews_page = ReviewsPage(page, frontend_url)
    
    has_gallery = await reviews_page.has_photo_gallery()
    assert has_gallery, "Photo gallery not found on review page"
    
    gallery_photos_count = await reviews_page.get_photos_count()
    assert gallery_photos_count == photo_count, \
        f"Expected {photo_count} photos in gallery, got {gallery_photos_count}"
    
    logger.info(f"Photo gallery contains {gallery_photos_count} photos")
    
    # Verify all thumbnails are visible
    all_thumbnails_visible = await reviews_page.verify_all_thumbnails_visible()
    assert all_thumbnails_visible, "Not all photo thumbnails are properly displayed"
    
    # Step 12: Test photo lightbox functionality
    # Open first photo in lightbox
    await reviews_page.open_photo_lightbox(0)
    
    is_open = await reviews_page.is_lightbox_open()
    assert is_open, "Lightbox did not open"
    
    # Verify counter shows correct values
    counter_correct = await reviews_page.verify_lightbox_counter(1, photo_count)
    assert counter_correct, f"Lightbox counter incorrect, expected '1 / {photo_count}'"
    
    logger.info("Lightbox opened successfully with correct counter")
    
    # If multiple photos, test navigation
    if photo_count > 1:
        # Navigate to next photo
        await reviews_page.navigate_lightbox_next()
        await page.wait_for_timeout(500)
        
        # Verify counter updated
        counter_correct = await reviews_page.verify_lightbox_counter(2, photo_count)
        assert counter_correct, f"Lightbox counter incorrect after navigation, expected '2 / {photo_count}'"
        
        # Navigate back
        await reviews_page.navigate_lightbox_prev()
        await page.wait_for_timeout(500)
        
        # Verify counter back to 1
        counter_correct = await reviews_page.verify_lightbox_counter(1, photo_count)
        assert counter_correct, f"Lightbox counter incorrect after back navigation, expected '1 / {photo_count}'"
        
        logger.info("Lightbox navigation works correctly")
    
    # Close lightbox
    await reviews_page.close_lightbox()
    
    is_closed = not await reviews_page.is_lightbox_open()
    assert is_closed, "Lightbox did not close"
    
    logger.info("Lightbox closed successfully")
    
    # Test completed successfully - cleanup will happen via fixture
    logger.info(
        f"TEST COMPLETED: {review_type} review with {photo_count} photos, "
        f"review_id={review_id}"
    )
