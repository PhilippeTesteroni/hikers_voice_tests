"""
Page Object Model initialization for Hiker's Voice E2E tests.
"""

from pages.base_page import BasePage
from pages.home_page import HomePage
from pages.review_form_page import ReviewFormPage
from pages.guide_page import GuidePage
from pages.company_page import CompanyPage
from pages.reviews_page import ReviewsPage

__all__ = [
    "BasePage",
    "HomePage", 
    "ReviewFormPage",
    "GuidePage",
    "CompanyPage",
    "ReviewsPage",
]
