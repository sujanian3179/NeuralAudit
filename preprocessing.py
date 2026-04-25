"""
Image Preprocessing Module
Normalizes and preprocesses images for CNN inference using OpenCV
"""
import cv2
import numpy as np
from typing import Tuple, Optional
from io import BytesIO
import requests
from PIL import Image
from logger import logger
from config import IMAGE_SIZE, CROP_RATIO, HSV_HUE_THRESHOLD


class ImagePreprocessor:
    """
    Handles image normalization, resizing, cropping, and HSV transformation.
    """
    
    @staticmethod
    def load_image_from_url(image_url: str, timeout: int = 30) -> Optional[np.ndarray]:
        """
        Load image from URL.
        
        Args:
            image_url: URL of the image
            timeout: Request timeout in seconds
        
        Returns:
            numpy array (BGR format) or None if loading fails
        """
        try:
            response = requests.get(image_url, timeout=timeout)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            logger.debug(f"Loaded image from URL: {image_url}")
            return image_cv
        except requests.RequestException as e:
            logger.error(f"Failed to load image from {image_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing image from {image_url}: {e}")
            return None
    
    @staticmethod
    def load_image_from_file(file_path: str) -> Optional[np.ndarray]:
        """
        Load image from local file.
        
        Args:
            file_path: Path to the image file
        
        Returns:
            numpy array (BGR format) or None if loading fails
        """
        try:
            image = cv2.imread(file_path)
            if image is None:
                logger.error(f"Failed to read image: {file_path}")
                return None
            logger.debug(f"Loaded image from file: {file_path}")
            return image
        except Exception as e:
            logger.error(f"Error loading image from {file_path}: {e}")
            return None
    
    @staticmethod
    def resize_image(image: np.ndarray, size: int = IMAGE_SIZE) -> np.ndarray:
        """
        Resize image to square dimensions.
        
        Args:
            image: Input image array
            size: Target size (default 224x224)
        
        Returns:
            Resized image array
        """
        try:
            resized = cv2.resize(image, (size, size), interpolation=cv2.INTER_LINEAR)
            logger.debug(f"Resized image to {size}x{size}")
            return resized
        except Exception as e:
            logger.error(f"Error resizing image: {e}")
            return image
    
    @staticmethod
    def center_crop(image: np.ndarray, crop_ratio: float = CROP_RATIO) -> np.ndarray:
        """
        Center-crop image to remove background noise.
        
        Args:
            image: Input image array
            crop_ratio: Ratio of image to keep (e.g., 0.6 = keep middle 60%)
        
        Returns:
            Center-cropped image array
        """
        try:
            height, width = image.shape[:2]
            crop_height = int(height * crop_ratio)
            crop_width = int(width * crop_ratio)
            
            y_start = (height - crop_height) // 2
            x_start = (width - crop_width) // 2
            
            cropped = image[y_start:y_start + crop_height, x_start:x_start + crop_width]
            logger.debug(f"Center-cropped image with ratio {crop_ratio}")
            return cropped
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return image
    
    @staticmethod
    def to_hsv(image: np.ndarray) -> np.ndarray:
        """
        Convert image from BGR to HSV color space.
        
        Args:
            image: Input image in BGR format
        
        Returns:
            Image in HSV format
        """
        try:
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            logger.debug("Converted image to HSV color space")
            return hsv
        except Exception as e:
            logger.error(f"Error converting to HSV: {e}")
            return image
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """
        Normalize image pixel values to [0, 1] range.
        
        Args:
            image: Input image array
        
        Returns:
            Normalized image array
        """
        try:
            normalized = image.astype(np.float32) / 255.0
            logger.debug("Normalized image to [0, 1] range")
            return normalized
        except Exception as e:
            logger.error(f"Error normalizing image: {e}")
            return image
    
    @staticmethod
    def get_dominant_hue(image_hsv: np.ndarray) -> Tuple[int, float]:
        """
        Calculate dominant hue from HSV image.
        Used as a preliminary color check before CNN.
        
        Args:
            image_hsv: Image in HSV format
        
        Returns:
            Tuple of (dominant_hue, saturation_level)
        """
        try:
            # Extract hue channel (0-179 in OpenCV HSV)
            hue = image_hsv[:, :, 0]
            saturation = image_hsv[:, :, 1]
            
            # Mask out low saturation (likely background/white areas)
            mask = saturation > 30
            
            if np.sum(mask) == 0:
                return 0, 0.0
            
            # Calculate mean hue
            dominant_hue = int(np.mean(hue[mask]))
            mean_saturation = float(np.mean(saturation[mask]) / 255.0)
            
            logger.debug(f"Dominant hue: {dominant_hue}, Saturation: {mean_saturation:.2f}")
            return dominant_hue, mean_saturation
        except Exception as e:
            logger.error(f"Error calculating dominant hue: {e}")
            return 0, 0.0
    
    @staticmethod
    def preprocess_pipeline(image: np.ndarray) -> np.ndarray:
        """
        Full preprocessing pipeline for CNN inference.
        
        Args:
            image: Input image array
        
        Returns:
            Preprocessed image ready for CNN
        """
        try:
            # Step 1: Resize
            image = ImagePreprocessor.resize_image(image)
            
            # Step 2: Center crop
            image = ImagePreprocessor.center_crop(image)
            
            # Step 3: Resize to target size (may be different after crop)
            image = ImagePreprocessor.resize_image(image)
            
            # Step 4: Normalize to [0, 1]
            image = ImagePreprocessor.normalize_image(image)
            
            # Step 5: Convert to RGB (for PyTorch models expecting RGB)
            image = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
            image = image.astype(np.float32) / 255.0
            
            logger.debug("Preprocessing pipeline completed")
            return image
        except Exception as e:
            logger.error(f"Error in preprocessing pipeline: {e}")
            return image
    
    @staticmethod
    def preprocess_for_inference(image_url: str) -> Optional[np.ndarray]:
        """
        Complete preprocessing from URL to inference-ready tensor.
        
        Args:
            image_url: URL of the image to process
        
        Returns:
            Preprocessed image array or None if processing fails
        """
        try:
            # Load image
            image = ImagePreprocessor.load_image_from_url(image_url)
            if image is None:
                return None
            
            # Apply preprocessing pipeline
            processed_image = ImagePreprocessor.preprocess_pipeline(image)
            return processed_image
        except Exception as e:
            logger.error(f"Error in preprocessing for inference: {e}")
            return None


class HeuristicColorChecker:
    """
    Provides heuristic color checks based on HSV analysis.
    Used to validate CNN predictions.
    """
    
    # Hue ranges for different color families (0-179 in OpenCV)
    HUE_RANGES = {
        "Red": [(0, 10), (170, 179)],      # Wraps around 0/179
        "Orange": [(10, 25)],
        "Yellow": [(25, 35)],
        "Green": [(35, 85)],
        "Cyan": [(85, 95)],
        "Blue": [(95, 130)],
        "Purple": [(130, 150)],
        "Pink": [(150, 170)],
    }
    
    @staticmethod
    def is_hue_in_range(hue: int, color_family: str) -> bool:
        """
        Check if a hue value falls within the range for a color family.
        
        Args:
            hue: Hue value (0-179)
            color_family: Color family name
        
        Returns:
            True if hue matches color family
        """
        if color_family not in HeuristicColorChecker.HUE_RANGES:
            logger.warning(f"Unknown color family: {color_family}")
            return True  # Accept if family not in lookup
        
        ranges = HeuristicColorChecker.HUE_RANGES[color_family]
        for hue_min, hue_max in ranges:
            if hue_min <= hue <= hue_max:
                return True
        return False
    
    @staticmethod
    def validate_color(image_hsv: np.ndarray, expected_family: str) -> Tuple[bool, float]:
        """
        Validate if image HSV matches expected color family.
        
        Args:
            image_hsv: Image in HSV format
            expected_family: Expected color family
        
        Returns:
            Tuple of (is_valid, confidence_score)
        """
        try:
            hue, saturation = ImagePreprocessor.get_dominant_hue(image_hsv)
            is_valid = HeuristicColorChecker.is_hue_in_range(hue, expected_family)
            
            # Confidence is based on saturation (more saturated = more confident)
            confidence = saturation * (0.5 if is_valid else -0.5)
            
            logger.debug(f"Heuristic validation: {expected_family} - Valid: {is_valid}, Confidence: {confidence:.2f}")
            return is_valid, confidence
        except Exception as e:
            logger.error(f"Error validating color: {e}")
            return False, 0.0


if __name__ == "__main__":
    # Example usage
    test_image_url = "https://example.com/image.jpg"
    
    preprocessor = ImagePreprocessor()
    processed = preprocessor.preprocess_for_inference(test_image_url)
    
    if processed is not None:
        print(f"Processed image shape: {processed.shape}")
        print(f"Image dtype: {processed.dtype}")
        print(f"Image value range: [{processed.min():.3f}, {processed.max():.3f}]")
