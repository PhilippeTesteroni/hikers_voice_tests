"""
Fixtures for test images used in photo upload tests.
"""

import pytest
from pathlib import Path
from utils.image_generator import generate_test_images_set, create_large_test_image, create_invalid_file


@pytest.fixture(scope="session")
def test_images_dir() -> Path:
    """
    Get the directory for test images.
    
    Returns:
        Path to test images directory
    """
    return Path(__file__).parent.parent / "fixtures" / "test_images"


@pytest.fixture(scope="session")
def test_images(test_images_dir: Path) -> list[str]:
    """
    Generate and return paths to test images (7 images).
    
    Returns:
        List of paths to test images
    """
    # Generate images if they don't exist
    if not test_images_dir.exists() or len(list(test_images_dir.glob("test_photo_*.jpg"))) < 7:
        image_paths = generate_test_images_set(test_images_dir, count=7)
    else:
        # Use existing images
        image_paths = sorted([str(p) for p in test_images_dir.glob("test_photo_*.jpg")])
    
    return image_paths


@pytest.fixture(scope="session")
def large_test_image(test_images_dir: Path) -> str:
    """
    Generate and return path to a large test image (>5MB) for size validation.
    
    Returns:
        Path to large test image
    """
    large_image_path = test_images_dir / "large_test_photo.jpg"
    
    if not large_image_path.exists():
        create_large_test_image(str(large_image_path), size_mb=6)
    
    return str(large_image_path)


@pytest.fixture(scope="session")
def invalid_test_file(test_images_dir: Path) -> str:
    """
    Generate and return path to an invalid (non-image) file.
    
    Returns:
        Path to invalid file
    """
    invalid_file_path = test_images_dir / "invalid_file.txt"
    
    if not invalid_file_path.exists():
        create_invalid_file(str(invalid_file_path))
    
    return str(invalid_file_path)
