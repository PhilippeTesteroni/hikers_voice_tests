"""
E2E tests for photo upload functionality - REFACTORED VERSION.

Tests photo upload for company and guide reviews using unique test entities.
Full test isolation - no dependency on seed data.
"""

import pytest
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage, ReviewFormPage, ReviewsPage
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("review_type,photo_count", [
    ("company", 1),  # Boundary: minimum photos
    ("company", 5),  # Boundary: maximum photos
    ("guide", 1),
    ("guide", 5),
])
async def test_review_with_photos_refactored(
    page: Page,
    api_client: Dict[str, Any],
    frontend_api_client,
    review_test_data: dict,
    clean_test_review: list,
    clean_test_company: list,
    clean_test_guide: list,
    frontend_url: str,
    backend_url: str,
    test_images: list[str],
    review_type: str,
    photo_count: int
):
    """
    TEST-003 REFACTORED: Review with photo upload using unique test entities.
    
    Full test isolation - creates unique company/guide per test run.
    Tests boundary values: 1 photo (min) and 5 photos (max).
    
    Verifies:
    - Photo upload in form
    - Photo preview display
    - Photo gallery on review page
    - Lightbox functionality with navigation
    
    Improvements over original:
    - No dependency on seed data
    - Creates unique entity per test
    - Automatic cleanup of review and entity
    """
    
    # Step 1: Create unique test entity via API
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    
    if review_type == "company":
        test_entity = await frontend_api_client.create_company(
            name="Photo Test Company",
            country_code="GE",
            description=f"Testing photo upload with {photo_count} photos",
            contact_email=f"photos{photo_count}@test.com"
        )
        clean_test_company.append(test_entity["id"])
        logger.info(f"Created test company: ID={test_entity['id']}, Name={test_entity['name']}")
    else:  # guide
        test_entity = await frontend_api_client.create_guide(
            name="Photo Test Guide",
            countries=["GE", "AM"],
            description=f"Testing photo upload with {photo_count} photos",
            contact_telegram="@phototest"
        )
        clean_test_guide.append(test_entity["id"])
        logger.info(f"Created test guide: ID={test_entity['id']}, Name={test_entity['name']}")
    
    # Step 2: Prepare review data
    date_from = datetime.now() - timedelta(days=20)
    date_to = datetime.now() - timedelta(days=15)
    
    author_name = f"Photo User {review_type} {photo_count}p *{timestamp}*"
    
    review_data = {
        "country_code": "GE",
        "entity_search": test_entity["name"][:10],
        "entity_exact": test_entity["name"],
        "trip_date_from": date_from.strftime("%Y-%m-%d"),
        "trip_date_to": date_to.strftime("%Y-%m-%d"),
        "rating": 5,
        "text": f"Отличный опыт! Проверка загрузки {photo_count} фотографий. " * 3,
        "author_name": author_name,
        "author_contact": f"test_photo_{review_type}_{photo_count}_{timestamp}@example.com",
    }
    
    photos_to_upload = test_images[:photo_count]
    
    # Step 3: Submit review via UI
    home_page = HomePage(page, frontend_url)
    await home_page.open()
    await home_page.wait_for_load()
    await home_page.click_leave_review()
    await page.wait_for_timeout(500)
    
    review_form = ReviewFormPage(page, frontend_url)
    await review_form.wait_for_modal()
    await review_form.select_review_type_in_modal(review_type)
    await review_form.wait_for_review_form(review_type)
    
    # Fill form based on type
    await review_form.select_country(review_data["country_code"])
    
    if review_type == "company":
        await review_form.fill_company_name_with_autocomplete(
            search_text=review_data["entity_search"],
            select_exact=review_data["entity_exact"]
        )
    else:  # guide
        await review_form.fill_guide_name_with_autocomplete(
            review_data["entity_search"],
            review_data["entity_exact"]
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
    
    # Step 4: Upload photos
    await review_form.scroll_to_photos_section()
    await page.wait_for_timeout(500)
    await review_form.upload_photos(photos_to_upload)
    
    # Verify photo previews in form
    photos_count = await review_form.get_uploaded_photos_count()
    assert photos_count == photo_count, f"Expected {photo_count} previews, got {photos_count}"
    
    previews_visible = await review_form.verify_photo_previews_visible()
    assert previews_visible, "Photo previews not properly displayed"
    
    logger.info(f"Uploaded and verified {photo_count} photos in form")
    
    # Accept rules and submit
    await review_form.accept_rules()
    await review_form.submit_form()
    
    # Step 5: Verify redirect
    timeout = 30000 if photo_count >= 5 else 15000
    await review_form.wait_for_success_redirect(timeout=timeout)
    assert "success=review_created" in page.url
    
    # Step 6: Moderate review
    test_helper = TestHelper(backend_url)
    
    # DEBUG: Check what reviews exist in DB
    response = await test_helper.client.get("/api/v1/test/reviews/all")
    if response.status_code == 200:
        all_reviews = response.json().get("reviews", [])
        logger.info(f"Total reviews in DB: {len(all_reviews)}")
        
        # Find our author
        our_reviews = [r for r in all_reviews if review_data["author_name"] in r.get("author_name", "")]
        logger.info(f"Reviews with author '{review_data['author_name']}': {len(our_reviews)}")
        
        for r in our_reviews:
            logger.info(f"  Review ID={r['id']}, status={r.get('status')}, company_id={r.get('company_id')}, guide_id={r.get('guide_id')}")
    
    # Find and moderate review by unique author name
    # Author name includes timestamp so it's already unique
    logger.info(f"Searching for review with author: '{review_data['author_name']}'")
    review_id = await test_helper.find_and_moderate_review(
        author_name=review_data["author_name"],
        action="approve"
    )
    logger.info(f"Moderation returned review_id: {review_id}")
    assert review_id is not None, f"Failed to moderate review for {review_data['author_name']}"
    clean_test_review.append(review_id)
    
    # CRITICAL: Verify the moderated review is for OUR entity
    response = await test_helper.client.get("/api/v1/test/reviews/all")
    assert response.status_code == 200
    all_reviews = response.json().get("reviews", [])
    our_review = next((r for r in all_reviews if r["id"] == review_id), None)
    
    assert our_review is not None, f"Review {review_id} not found"
    
    # Debug logging
    logger.info(f"Review {review_id} details:")
    logger.info(f"  Author: {our_review.get('author_name')}")
    logger.info(f"  Company ID: {our_review.get('company_id')}")
    logger.info(f"  Guide ID: {our_review.get('guide_id')}")
    logger.info(f"  Photos count: {len(our_review.get('photos', []))}")
    logger.info(f"Expected {review_type} ID: {test_entity['id']}")
    
    # Check entity ID matches
    if review_type == "company":
        actual_entity_id = our_review.get("company_id")
        assert actual_entity_id == test_entity["id"], \
            f"Review {review_id} is for company {actual_entity_id}, expected {test_entity['id']}"
    else:  # guide
        actual_entity_id = our_review.get("guide_id")
        assert actual_entity_id == test_entity["id"], \
            f"Review {review_id} is for guide {actual_entity_id}, expected {test_entity['id']}"
    
    logger.info(f"✅ Verified review {review_id} is for our {review_type} {test_entity['id']}")
    
    # Wait for photos to be saved to disk (base64 decoding + file I/O)
    # Each photo takes ~500-1000ms, so be generous
    wait_time = max(10000, photo_count * 2000)  # At least 10s, or 2s per photo
    logger.info(f"Waiting {wait_time/1000}s for {photo_count} photos to be saved...")
    await page.wait_for_timeout(wait_time)
    
    # RE-CHECK: Verify photos were saved to the review
    response = await test_helper.client.get("/api/v1/test/reviews/all")
    all_reviews = response.json().get("reviews", [])
    our_review = next((r for r in all_reviews if r["id"] == review_id), None)
    actual_photos_count = len(our_review.get('photos', []))
    logger.info(f"Review {review_id} now has {actual_photos_count} photos in DB")
    
    if actual_photos_count == 0:
        logger.error(f"❌ Photos were NOT saved! Expected {photo_count}, got 0")
        logger.error("This indicates a backend issue with photo upload processing")
        # Don't fail the test yet - maybe photos appear later on the page
    
    await test_helper.close()
    
    # Step 7: Navigate to review detail page
    review_url = f"{frontend_url}/reviews/{review_id}"
    await page.goto(review_url)
    await page.wait_for_load_state("networkidle")
    
    # Step 8: Verify photos in gallery with retry
    reviews_page = ReviewsPage(page, frontend_url)
    
    async def check_photos_in_gallery():
        if not await reviews_page.has_photo_gallery():
            logger.info("Photo gallery not found yet")
            return False
        count = await reviews_page.get_photos_count()
        logger.info(f"Gallery has {count} photos (expecting {photo_count})")
        return count == photo_count
    
    success = await reviews_page.wait_for_condition(
        check_fn=check_photos_in_gallery,
        timeout=30000,
        interval=5000,
        retry_with_reload=True,
        error_message=f"Photos did not appear in gallery (expected {photo_count})"
    )
    assert success, f"Expected {photo_count} photos in gallery"
    
    # Verify gallery details
    has_gallery = await reviews_page.has_photo_gallery()
    assert has_gallery, "Photo gallery not found"
    
    gallery_photos_count = await reviews_page.get_photos_count()
    assert gallery_photos_count == photo_count, \
        f"Expected {photo_count} photos, got {gallery_photos_count}"
    
    all_thumbnails_visible = await reviews_page.verify_all_thumbnails_visible()
    assert all_thumbnails_visible, "Not all thumbnails displayed properly"
    
    logger.info(f"Photo gallery verified: {gallery_photos_count} photos")
    
    # Step 9: Test lightbox functionality
    await reviews_page.open_photo_lightbox(0)
    
    is_open = await reviews_page.is_lightbox_open()
    assert is_open, "Lightbox did not open"
    
    counter_correct = await reviews_page.verify_lightbox_counter(1, photo_count)
    assert counter_correct, f"Lightbox counter incorrect, expected '1 / {photo_count}'"
    
    logger.info("Lightbox opened with correct counter")
    
    # Test navigation if multiple photos
    if photo_count > 1:
        await reviews_page.navigate_lightbox_next()
        await page.wait_for_timeout(500)
        
        counter_correct = await reviews_page.verify_lightbox_counter(2, photo_count)
        assert counter_correct, "Counter incorrect after next"
        
        await reviews_page.navigate_lightbox_prev()
        await page.wait_for_timeout(500)
        
        counter_correct = await reviews_page.verify_lightbox_counter(1, photo_count)
        assert counter_correct, "Counter incorrect after prev"
        
        logger.info("Lightbox navigation works correctly")
    
    await reviews_page.close_lightbox()
    
    is_closed = not await reviews_page.is_lightbox_open()
    assert is_closed, "Lightbox did not close"
    
    logger.info(f"✅ TEST-003 PASSED: {review_type} review with {photo_count} photos, "
                f"entity={test_entity['id']}, review={review_id}")
