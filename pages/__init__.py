"""
Page Object Model initialization for Hiker's Voice E2E tests.
"""

from pages.base_page import BasePage
from pages.home_page import HomePage
from pages.review_form_page import ReviewFormPage

__all__ = [
    "BasePage",
    "HomePage", 
    "ReviewFormPage",
]
