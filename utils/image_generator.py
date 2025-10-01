"""
Utility for generating test images.
Creates simple colored images for testing photo upload functionality.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)


def create_test_image(
    width: int = 800,
    height: int = 600,
    color: tuple = (100, 150, 200),
    text: str = "",
    output_path: str = None
) -> str:
    """
    Create a simple test image with solid color and optional text.
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        color: RGB color tuple
        text: Optional text to draw on image
        output_path: Path where to save the image
        
    Returns:
        Path to created image
    """
    # Create image with solid color
    img = Image.new('RGB', (width, height), color)
    
    # Add text if provided
    if text:
        draw = ImageDraw.Draw(img)
        # Use default font
        try:
            # Try to use a nicer font if available
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
        except:
            # Fall back to default font
            font = ImageFont.load_default()
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)
        
        # Draw white text with black outline
        draw.text(position, text, fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    
    # Save image
    if output_path:
        img.save(output_path, 'JPEG', quality=95)
        logger.info(f"Created test image: {output_path}")
        return output_path
    else:
        raise ValueError("output_path is required")


def generate_test_images_set(output_dir: Path, count: int = 5) -> list[str]:
    """
    Generate a set of test images with different colors.
    
    Args:
        output_dir: Directory where to save images
        count: Number of images to generate
        
    Returns:
        List of paths to generated images
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Define color palette for different images
    colors = [
        (220, 100, 100, "Красное фото"),  # Red
        (100, 180, 100, "Зелёное фото"),  # Green
        (100, 120, 220, "Синее фото"),    # Blue
        (220, 180, 100, "Жёлтое фото"),   # Yellow
        (180, 100, 220, "Фиолетовое фото"), # Purple
        (100, 200, 200, "Бирюзовое фото"), # Cyan
        (220, 150, 100, "Оранжевое фото"), # Orange
    ]
    
    image_paths = []
    
    for i in range(min(count, len(colors))):
        color_rgb = colors[i][:3]
        text = colors[i][3] if len(colors[i]) > 3 else f"Фото {i+1}"
        
        filename = f"test_photo_{i+1}.jpg"
        filepath = output_dir / filename
        
        create_test_image(
            width=800,
            height=600,
            color=color_rgb,
            text=text,
            output_path=str(filepath)
        )
        
        image_paths.append(str(filepath))
    
    logger.info(f"Generated {len(image_paths)} test images in {output_dir}")
    return image_paths


def create_large_test_image(output_path: str, size_mb: float = 6) -> str:
    """
    Create a large test image for testing file size validation.
    
    Args:
        output_path: Path where to save the image
        size_mb: Target size in megabytes
        
    Returns:
        Path to created image
    """
    # Calculate dimensions to achieve target file size
    # JPEG typically compresses to ~1/10 of raw size
    target_pixels = int(size_mb * 1024 * 1024 * 10 / 3)  # RGB = 3 bytes per pixel
    dimension = int(target_pixels ** 0.5)
    
    img = Image.new('RGB', (dimension, dimension), (150, 150, 150))
    
    # Save with low compression to increase file size
    img.save(output_path, 'JPEG', quality=100)
    
    actual_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
    logger.info(f"Created large test image: {output_path} ({actual_size_mb:.2f} MB)")
    
    return output_path


def create_invalid_file(output_path: str) -> str:
    """
    Create a non-image file for testing validation.
    
    Args:
        output_path: Path where to save the file
        
    Returns:
        Path to created file
    """
    with open(output_path, 'w') as f:
        f.write("This is not an image file")
    
    logger.info(f"Created invalid file: {output_path}")
    return output_path


if __name__ == "__main__":
    # Generate test images when run directly
    from pathlib import Path
    
    output_dir = Path(__file__).parent.parent / "fixtures" / "test_images"
    generate_test_images_set(output_dir, count=7)
    
    # Create a large image for size validation testing
    large_image_path = output_dir / "large_test_photo.jpg"
    create_large_test_image(str(large_image_path), size_mb=6)
    
    # Create invalid file
    invalid_file_path = output_dir / "invalid_file.txt"
    create_invalid_file(str(invalid_file_path))
    
    print(f"✅ Test images generated in {output_dir}")
