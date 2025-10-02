"""
E2E test for photo gallery on guide/company pages.
Tests that photos from multiple reviews are correctly displayed in gallery.
"""

import pytest
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from playwright.async_api import Page

from pages import HomePage, ReviewFormPage, GuidePage, CompanyPage
from utils.test_helper import TestHelper

logger = logging.getLogger(__name__)


@pytest.mark.e2e
@pytest.mark.critical
@pytest.mark.parametrize("entity_type", ["guide", "company"])
async def test_entity_photo_gallery(
    page: Page,
    api_client: Dict[str, Any],
    review_test_data: dict,
    clean_test_review: list,
    frontend_url: str,
    backend_url: str,
    test_images: list[str],
    entity_type: str
):
    """
    E2E test for photo gallery on guide/company pages.
    
    Test scenario:
        1. Create entity (guide or company)
        2. Create 3 reviews with 5 photos each (total 15 photos)
        3. Navigate to entity page
        4. Verify photo gallery displays 6 photo thumbnails
        5. Click on first photo to open lightbox
        6. Verify lightbox shows correct counter (1 / 15)
        7. Navigate through all photos in lightbox
        8. Close lightbox
        9. Delete all test reviews
        10. Verify photo gallery is no longer displayed
    
    Args:
        page: Playwright Page instance
        api_client: API client for backend interactions
        review_test_data: Test data fixture
        clean_test_review: Cleanup fixture for created reviews
        frontend_url: Frontend base URL
        backend_url: Backend API URL
        test_images: List of test image paths
        entity_type: Type of entity ('guide' or 'company')
    """
    test_helper = TestHelper(backend_url)
    review_ids = []
    entity_id = None
    
    try:
        # Step 1: Create entity (guide or company)
        logger.info(f"Step 1: Creating test {entity_type}")
        
        if entity_type == "guide":
            # Используем существующего гида из базы для тестирования
            # Георгий Челидзе (ID обычно 1 или 2)
            entity_id = 1
            entity_name = "Георгий Челидзе"
            country_code = "RU"
        else:  # company
            # Используем существующую компанию из базы
            # Georgian Adventures (ID 1)
            entity_id = 1
            entity_name = "Georgian Adventures"
            country_code = "GE"
        
        logger.info(f"Using existing {entity_type}: {entity_name} (ID: {entity_id})")
        
        # Step 2: Create 3 reviews with 5 photos each
        logger.info("Step 2: Creating 3 reviews with 5 photos each")
        
        photos_to_upload = test_images[:5]  # Select 5 photos
        
        for i in range(3):
            date_from = datetime.now() - timedelta(days=30 + i * 10)
            date_to = datetime.now() - timedelta(days=25 + i * 10)
            
            author_name = f"Test Gallery User {entity_type} {i+1}"
            
            # Prepare review data
            if entity_type == "company":
                review_data = {
                    "country_code": country_code,
                    "company_name": entity_name,
                    "select_autocomplete": True,
                    "trip_date_from": date_from.strftime("%Y-%m-%d"),
                    "trip_date_to": date_to.strftime("%Y-%m-%d"),
                    "rating": 5,
                    "text": f"Отличная компания! Отзыв #{i+1} для проверки галереи фотографий. " * 3,
                    "author_name": author_name,
                    "author_contact": f"test_gallery_{entity_type}_{i+1}@example.com",
                    "rules_accepted": True
                }
            else:  # guide
                review_data = {
                    "country_code": country_code,
                    "guide_search": "Георгий",
                    "guide_name": entity_name,
                    "trip_date_from": date_from.strftime("%Y-%m-%d"),
                    "trip_date_to": date_to.strftime("%Y-%m-%d"),
                    "rating": 5,
                    "text": f"Отличный гид! Отзыв #{i+1} для проверки галереи фотографий. " * 3,
                    "author_name": author_name,
                    "author_contact": f"test_gallery_{entity_type}_{i+1}@example.com",
                    "rules_accepted": True
                }
            
            # Open home page and start review creation
            home_page = HomePage(page, frontend_url)
            await home_page.open()
            await home_page.wait_for_load()
            await home_page.click_leave_review()
            await page.wait_for_timeout(500)
            
            # Fill review form
            review_form = ReviewFormPage(page, frontend_url)
            await review_form.wait_for_modal()
            await review_form.select_review_type_in_modal(entity_type)
            await review_form.wait_for_review_form(entity_type)
            
            # Fill form based on type
            if entity_type == "company":
                await review_form.select_country(review_data["country_code"])
                await review_form.fill_company_name_with_autocomplete(review_data["company_name"])
                await review_form.fill_trip_dates(
                    review_data["trip_date_from"],
                    review_data["trip_date_to"]
                )
            else:  # guide
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
            
            # Upload photos
            await review_form.scroll_to_photos_section()
            await page.wait_for_timeout(500)
            await review_form.upload_photos(photos_to_upload)
            
            # Verify photos uploaded
            photos_count = await review_form.get_uploaded_photos_count()
            assert photos_count == 5, f"Expected 5 photos, got {photos_count}"
            
            logger.info(f"Review #{i+1}: Successfully uploaded 5 photos")
            
            # Accept rules and submit
            await review_form.accept_rules()
            await review_form.submit_form()
            
            # Wait for redirect
            await review_form.wait_for_success_redirect(timeout=30000)
            assert "success=review_created" in page.url, f"Expected success redirect, got: {page.url}"
            
            # Moderate review
            review_id = await test_helper.find_and_moderate_review(
                author_name=review_data["author_name"],
                action="approve"
            )
            
            assert review_id is not None, f"Failed to moderate review for {author_name}"
            review_ids.append(review_id)
            clean_test_review.append(review_id)
            
            logger.info(f"Review #{i+1} created and approved: review_id={review_id}")
            
            await page.wait_for_timeout(1000)
        
        logger.info(f"All 3 reviews created: {review_ids}")
        
        # Step 3: Navigate to entity page
        logger.info(f"Step 3: Navigating to {entity_type} page")
        
        if entity_type == "guide":
            guide_page = GuidePage(page, frontend_url)
            await guide_page.open_guide_page(entity_id)
            entity_page = guide_page
        else:  # company
            company_page = CompanyPage(page)
            company_page.base_url = frontend_url
            await company_page.open_company_page(entity_id)
            entity_page = company_page
        
        await page.wait_for_timeout(2000)  # Wait for page to fully load
        
        # Debug: Check if reviews are visible on the page
        review_cards = page.locator("article.card")
        reviews_count = await review_cards.count()
        logger.info(f"Found {reviews_count} review cards on {entity_type} page")
        
        # If no reviews visible, something went wrong with review creation/moderation
        if reviews_count == 0:
            logger.error(f"No reviews found on {entity_type} page! Reviews may not be associated with entity.")
            logger.error(f"Expected reviews: {review_ids}")
            logger.error(f"Entity ID: {entity_id}, Name: {entity_name}")
            
            # Try to fetch entity data via API to debug
            if entity_type == "guide":
                entity_data = await test_helper.get_guide_by_id(entity_id)
            else:
                # Use API client to fetch company
                response = await api_client["client"].get(f"/api/v1/companies/{entity_id}")
                entity_data = response.json() if response.status_code == 200 else None
            
            if entity_data:
                logger.error(f"Entity data: reviews_count={entity_data.get('reviews_count')}, "
                           f"reviews_array_length={len(entity_data.get('reviews', []))}")
            
            assert False, f"No reviews found on {entity_type} page after creating {len(review_ids)} reviews"
        
        # Step 4: Verify photo gallery displays 6 thumbnails
        logger.info("Step 4: Verifying photo gallery displays 6 thumbnails")
        
        # Wait a bit more for SSR hydration on company pages
        await page.wait_for_timeout(1000)
        
        # Try to find gallery section with better selector
        # The gallery might take longer to render on company pages due to SSR/API
        gallery_section = page.locator(".card").filter(has=page.locator("h3:has-text('Фотографии')"))
        
        try:
            await gallery_section.wait_for(state="visible", timeout=15000)
        except:
            # Debug: log all cards on page
            all_cards = await page.locator(".card").all()
            logger.error(f"Found {len(all_cards)} cards on page, but none contain photo gallery")
            
            for i, card in enumerate(all_cards[:5]):  # Log first 5 cards
                text = await card.text_content()
                logger.error(f"Card {i+1} preview: {text[:100]}...")
            
            raise AssertionError(
                f"Photo gallery not found on {entity_type} page after 15 seconds. "
                f"Created {len(review_ids)} reviews with photos, but gallery did not appear."
            )
        
        # Log total photos count from gallery header
        gallery_header = gallery_section.locator("h3")
        header_text = await gallery_header.text_content()
        logger.info(f"Gallery header: {header_text}")
        
        # Extract total photos from header (e.g., "Фотографии из отзывов (15)")
        total_match = re.search(r'\((\d+)\)', header_text or '')
        assert total_match, f"Could not parse total photos from header: {header_text}"
        
        total_photos = int(total_match.group(1))
        logger.info(f"Total photos in gallery: {total_photos}")
        
        # We expect 15 photos (3 reviews × 5 photos)
        assert total_photos == 15, f"Expected 15 total photos, got {total_photos}"
        
        # Count photo thumbnails in grid
        photo_thumbnails = page.locator("button.relative.aspect-square")
        thumbnails_count = await photo_thumbnails.count()
        
        # Gallery shows max 6 thumbnails
        assert thumbnails_count == 6, f"Expected 6 photo thumbnails, got {thumbnails_count}"
        logger.info("✓ Photo gallery displays 6 thumbnails as expected")
        
        # Verify "+9" overlay on 6th thumbnail (15 total - 6 shown = 9 remaining)
        sixth_thumbnail = photo_thumbnails.nth(5)
        overlay_text_elem = sixth_thumbnail.locator("span.text-white.text-xl")
        
        assert await overlay_text_elem.count() > 0, "Overlay text not found on 6th thumbnail"
        
        overlay_text = await overlay_text_elem.text_content()
        logger.info(f"Overlay text: {overlay_text}")
        
        # Parse remaining count
        overlay_match = re.search(r'\+(\d+)', overlay_text or '')
        assert overlay_match, f"Could not parse overlay text: {overlay_text}"
        
        remaining_count = int(overlay_match.group(1))
        expected_remaining = 9  # 15 - 6
        assert remaining_count == expected_remaining, \
            f"Expected +{expected_remaining} overlay, got +{remaining_count}"
        
        logger.info(f"✓ Correct overlay displayed: +{remaining_count}")
        
        # Step 5: Click on first photo to open lightbox
        logger.info("Step 5: Opening lightbox by clicking first photo")
        
        first_thumbnail = photo_thumbnails.first
        await first_thumbnail.click()
        await page.wait_for_timeout(500)
        
        # Step 6: Verify lightbox shows correct counter
        logger.info("Step 6: Verifying lightbox counter")
        
        lightbox = page.locator("div[role='dialog']")
        await lightbox.wait_for(state="visible", timeout=5000)
        
        lightbox_visible = await lightbox.is_visible()
        assert lightbox_visible, "Lightbox did not open"
        
        # Get counter text
        counter_elem = page.locator(".absolute.top-4.left-4.text-white").first
        counter_text = await counter_elem.text_content()
        logger.info(f"Lightbox counter: {counter_text}")
        
        # Verify counter shows "1 / 15"
        assert counter_text == "1 / 15", f"Expected counter '1 / 15', got '{counter_text}'"
        logger.info("✓ Lightbox opened with correct counter (1 / 15)")
        
        # Step 7: Navigate through photos in lightbox
        logger.info("Step 7: Navigating through photos in lightbox")
        
        # Click next button several times
        next_button = page.locator("button[aria-label='Следующее фото']")
        
        # Navigate to photos 2, 3, 4, 5
        for photo_num in range(2, 6):
            await next_button.click()
            await page.wait_for_timeout(300)
            
            # Verify counter
            counter_elem = page.locator(".absolute.top-4.left-4.text-white").first
            current_counter = await counter_elem.text_content()
            expected_counter = f"{photo_num} / 15"
            
            assert current_counter == expected_counter, \
                f"Expected counter '{expected_counter}', got '{current_counter}'"
            logger.info(f"✓ Navigated to photo {photo_num}")
        
        # Navigate back
        prev_button = page.locator("button[aria-label='Предыдущее фото']")
        await prev_button.click()
        await page.wait_for_timeout(300)
        
        counter_elem = page.locator(".absolute.top-4.left-4.text-white").first
        current_counter = await counter_elem.text_content()
        
        assert current_counter == "4 / 15", \
            f"Expected counter '4 / 15' after back navigation, got '{current_counter}'"
        logger.info("✓ Back navigation works correctly")
        
        # Step 8: Close lightbox
        logger.info("Step 8: Closing lightbox")
        
        close_button = page.locator("button[aria-label='Закрыть']")
        await close_button.click()
        await page.wait_for_timeout(500)
        
        lightbox_closed = not await lightbox.is_visible()
        assert lightbox_closed, "Lightbox did not close"
        logger.info("✓ Lightbox closed successfully")
        
        # Step 9: Delete all test reviews
        logger.info("Step 9: Deleting all test reviews")
        
        for review_id in review_ids:
            deleted = await test_helper.delete_review(review_id)
            
            assert deleted, f"Failed to delete review {review_id}. Cannot proceed with cleanup verification."
            logger.info(f"✓ Deleted review {review_id}")
        
        # Remove from cleanup list since we successfully deleted them
        for review_id in review_ids:
            if review_id in clean_test_review:
                clean_test_review.remove(review_id)
        
        # Step 10: Verify photo gallery is no longer displayed
        logger.info("Step 10: Verifying photo gallery is no longer displayed")
        
        # Refresh page
        await page.reload()
        await page.wait_for_timeout(2000)
        
        # Check that gallery section is not present
        gallery_section = page.locator(".card:has-text('Фотографии из отзывов')")
        gallery_count = await gallery_section.count()
        
        assert gallery_count == 0, f"Photo gallery still visible after deleting reviews (found {gallery_count} sections)"
        logger.info("✓ Photo gallery removed after deleting all reviews")
        
        logger.info(
            f"TEST COMPLETED: {entity_type} photo gallery test passed. "
            f"Created 3 reviews with 5 photos each, verified gallery display, "
            f"tested lightbox navigation, and cleaned up successfully."
        )
        
    finally:
        await test_helper.close()
