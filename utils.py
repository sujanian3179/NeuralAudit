"""
Utility functions for NeuralAudit
"""
import os
from pathlib import Path
from logger import logger


def ensure_directories():
    """Create necessary directories for the application"""
    directories = [
        "./logs",
        "./models",
        "./data",
        "./screenshots",
        "./results",
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")


def load_csv_urls(csv_file: str) -> list:
    """
    Load product URLs from CSV file.
    CSV should have 'url' or 'product_url' column.
    
    Args:
        csv_file: Path to CSV file
    
    Returns:
        List of URLs
    """
    try:
        import csv
        urls = []
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Try different column names
                url = row.get('url') or row.get('product_url') or row.get('link')
                if url:
                    urls.append(url.strip())
        
        logger.info(f"Loaded {len(urls)} URLs from {csv_file}")
        return urls
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
        return []


def save_results_csv(results: list, output_file: str):
    """
    Save audit results to CSV file.
    
    Args:
        results: List of audit result dictionaries
        output_file: Path to output CSV file
    """
    try:
        import csv
        
        if not results:
            logger.warning("No results to save")
            return
        
        keys = results[0].keys()
        
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
        
        logger.info(f"Saved {len(results)} results to {output_file}")
    except Exception as e:
        logger.error(f"Error saving CSV: {e}")


def validate_url(url: str) -> bool:
    """
    Validate if URL is well-formed.
    
    Args:
        url: URL string
    
    Returns:
        True if valid
    """
    try:
        from urllib.parse import urlparse
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def get_image_dimensions(image_path: str) -> tuple:
    """
    Get image dimensions.
    
    Args:
        image_path: Path to image file
    
    Returns:
        Tuple of (width, height) or None
    """
    try:
        from PIL import Image
        img = Image.open(image_path)
        return img.size
    except Exception as e:
        logger.error(f"Error getting image dimensions: {e}")
        return None


def format_confidence(confidence: float) -> str:
    """
    Format confidence score as percentage.
    
    Args:
        confidence: Confidence value between 0 and 1
    
    Returns:
        Formatted string
    """
    return f"{confidence * 100:.1f}%"


def human_readable_time(seconds: float) -> str:
    """
    Convert seconds to human readable time.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted time string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    else:
        return f"{seconds/3600:.1f}h"


# Initialize directories on import
ensure_directories()
