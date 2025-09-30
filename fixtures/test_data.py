"""
Test data for Hiker's Voice E2E tests.
Provides valid and invalid test data for different review types.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
import random
import string


def generate_unique_email() -> str:
    """Generate a unique email address for testing."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"test_{timestamp}_{random_suffix}@example.com"


def generate_unique_name(prefix: str = "Test") -> str:
    """Generate a unique name for testing."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase, k=4))
    return f"{prefix}_{timestamp}_{random_suffix}"


def generate_company_data() -> Dict[str, Any]:
    """Generate test data for a new company."""
    unique_id = generate_unique_name("")
    return {
        "name": f"Test Adventure Tours {unique_id}",
        "country_code": "KZ",
        "description": "Организация туров по Алтаю и Тянь-Шаню. Профессиональные гиды, безопасные маршруты, незабываемые впечатления.",
        "email": "info@testadventure.kz",
        "phone": "+7 777 123-45-67",
        "website": "https://testadventure.kz",
        "instagram": "@testadventure",
        "telegram": "@testadventure_bot"
    }


def get_review_test_data() -> Dict[str, Any]:
    """
    Get comprehensive test data for all review types.
    
    Returns:
        Dictionary containing test data for various scenarios
    """
    
    # Base valid data for reviews
    base_review_data = {
        "author_name": "Иван Тестов",
        "author_email": generate_unique_email(),
        "title": f"Тестовый отзыв {generate_unique_name('Review')}",
        "content": "Это тестовый отзыв для проверки функциональности системы. " * 5,
        "rating": 5,
        "pros": "Отличный сервис, профессиональный подход, хорошая организация",
        "cons": "Немного дороговато, но качество оправдывает цену"
    }
    
    # Tour review specific data
    tour_review_valid = {
        **base_review_data,
        "tour_name": f"Поход к Эвересту {generate_unique_name('Tour')}",
        "tour_date": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "duration": 14,
        "difficulty": "hard",
        "tour_type": "mountain"
    }
    
    tour_review_invalid = {
        "author_name": "",  # Empty required field
        "author_email": "invalid-email",  # Invalid email format
        "title": "x",  # Too short
        "content": "Short",  # Too short content
        "rating": 0,  # Invalid rating
        "tour_name": "",  # Empty tour name
        "tour_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),  # Future date
        "duration": -5,  # Negative duration
    }
    
    # Company review specific data
    company_review_valid = {
        **base_review_data,
        "company_name": f"Горные Приключения {generate_unique_name('Company')}",
        "company_website": "https://example-tours.com",
        "service_quality": 5,
        "price_quality": 4
    }
    
    company_review_existing = {
        **base_review_data,
        "company_id": 1,  # Using existing company from seed data
        "service_quality": 4,
        "price_quality": 4
    }
    
    company_review_invalid = {
        "author_name": "A" * 256,  # Too long name
        "author_email": "@invalid.com",  # Invalid email
        "title": "",  # Empty title
        "content": "",  # Empty content
        "company_name": "",  # Empty company name
        "company_website": "not-a-url",  # Invalid URL
    }
    
    # Guide review specific data
    guide_review_valid = {
        **base_review_data,
        "guide_name": f"Петр Проводников {generate_unique_name('Guide')}",
        "languages": ["Русский", "English", "Deutsch"],
        "specialization": "Горные походы, альпинизм",
        "experience_rating": 5,
        "communication_rating": 5
    }
    
    guide_review_existing = {
        **base_review_data,
        "guide_id": 1,  # Using existing guide from seed data
        "experience_rating": 5,
        "communication_rating": 4
    }
    
    guide_review_invalid = {
        "author_name": "123456",  # Numbers only
        "author_email": "email@",  # Incomplete email
        "guide_name": "",  # Empty guide name
        "languages": "",  # Empty languages
        "experience_rating": 6,  # Out of range rating
    }
    
    # Existing entities from seed data
    existing_companies = [
        {
            "id": 1,
            "name": "Альпийские Приключения",
            "description": "Профессиональная компания с 15-летним опытом",
            "website": "https://alpine-adventures.ru"
        },
        {
            "id": 2,
            "name": "Горный Эксперт",
            "description": "Специализируемся на восхождениях",
            "website": "https://mountain-expert.ru"
        },
        {
            "id": 3,
            "name": "Дикая Природа Туры",
            "description": "Экологические туры и походы",
            "website": "https://wild-nature-tours.ru"
        }
    ]
    
    existing_guides = [
        {
            "id": 1,
            "name": "Александр Петров",
            "experience_years": 15,
            "languages": ["Русский", "English"],
            "specialization": "Альпинизм, горные походы"
        },
        {
            "id": 2,
            "name": "Мария Соколова",
            "experience_years": 10,
            "languages": ["Русский", "Deutsch", "English"],
            "specialization": "Треккинг, экотуризм"
        },
        {
            "id": 3,
            "name": "Сергей Волков",
            "experience_years": 8,
            "languages": ["Русский", "中文"],
            "specialization": "Скалолазание, via ferrata"
        }
    ]
    
    # Edge cases.txt and boundary tests
    edge_cases = {
        "min_valid_title": "Отзыв",  # Minimum valid title
        "max_valid_title": "О" * 200,  # Maximum valid title
        "min_valid_content": "Хороший тур, рекомендую всем.",  # Minimum valid content
        "max_valid_content": "Отличный опыт. " * 500,  # Very long content
        "special_characters": {
            "author_name": "Жан-Клод О'Коннор",
            "title": "Отзыв №1: «Лучший тур!»",
            "content": "Тур был просто супер! 100% рекомендую. Цена/качество = 10/10"
        },
        "unicode_characters": {
            "author_name": "山田太郎",
            "title": "素晴らしいツアー 🏔️",
            "content": "このツアーは本当に素晴らしかったです！😊"
        },
        "sql_injection_attempt": {
            "author_name": "'; DROP TABLE reviews; --",
            "title": "SELECT * FROM users WHERE 1=1",
            "content": "<script>alert('XSS')</script>"
        },
        "xss_attempt": {
            "author_name": "<img src=x onerror=alert('XSS')>",
            "title": "<script>document.location='http://evil.com'</script>",
            "content": "<%2Fscript%3E%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E"
        }
    }
    
    # Performance test data
    performance_data = {
        "bulk_reviews": [
            {
                **base_review_data,
                "title": f"Bulk Review {i}",
                "content": f"This is bulk review number {i} for performance testing.",
                "rating": (i % 5) + 1
            }
            for i in range(1, 51)  # 50 reviews for bulk testing
        ],
        "large_content": "A" * 10000,  # Very large content
        "many_photos": [f"photo_{i}.jpg" for i in range(20)]  # Many photos
    }
    
    return {
        "valid": {
            "tour_review": tour_review_valid,
            "company_review": company_review_valid,
            "guide_review": guide_review_valid,
            "company_review_existing": company_review_existing,
            "guide_review_existing": guide_review_existing,
            "base_review": base_review_data
        },
        "invalid": {
            "tour_review": tour_review_invalid,
            "company_review": company_review_invalid,
            "guide_review": guide_review_invalid
        },
        "entities": {
            "companies": existing_companies,
            "guides": existing_guides
        },
        "edge_cases": edge_cases,
        "performance": performance_data,
        "generators": {
            "email": generate_unique_email,
            "name": generate_unique_name
        }
    }


# Additional test data generators
class TestDataGenerator:
    """Class for generating dynamic test data."""
    
    @staticmethod
    def generate_review_batch(count: int, review_type: str = "tour") -> List[Dict[str, Any]]:
        """
        Generate a batch of review data.
        
        Args:
            count: Number of reviews to generate
            review_type: Type of reviews (tour, company, guide)
            
        Returns:
            List of review data dictionaries
        """
        reviews = []
        base_data = get_review_test_data()["valid"]["base_review"]
        
        for i in range(count):
            review = {
                **base_data,
                "author_name": f"Tester {i+1}",
                "author_email": generate_unique_email(),
                "title": f"Test Review {i+1} - {generate_unique_name()}",
                "rating": (i % 5) + 1
            }
            
            if review_type == "tour":
                review.update({
                    "tour_name": f"Tour {generate_unique_name()}",
                    "tour_date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
                    "duration": random.randint(1, 30),
                    "difficulty": random.choice(["easy", "medium", "hard", "extreme"])
                })
            elif review_type == "company":
                review.update({
                    "company_name": f"Company {generate_unique_name()}",
                    "service_quality": (i % 5) + 1,
                    "price_quality": (i % 5) + 1
                })
            elif review_type == "guide":
                review.update({
                    "guide_name": f"Guide {generate_unique_name()}",
                    "experience_rating": (i % 5) + 1,
                    "communication_rating": (i % 5) + 1
                })
            
            reviews.append(review)
        
        return reviews
    
    @staticmethod
    def generate_invalid_email() -> str:
        """Generate an invalid email for negative testing."""
        invalid_patterns = [
            "no-at-sign.com",
            "@no-local-part.com",
            "double@@at.com",
            "spaces in@email.com",
            "missing-domain@",
            ".starts-with-dot@example.com",
            "ends-with-dot.@example.com",
            "special#chars@example.com",
            "too..many..dots@example.com"
        ]
        return random.choice(invalid_patterns)
    
    @staticmethod
    def generate_boundary_string(length: int, char: str = "A") -> str:
        """
        Generate a string of specific length for boundary testing.
        
        Args:
            length: Desired string length
            char: Character to repeat
            
        Returns:
            String of specified length
        """
        return char * length
