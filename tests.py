"""
Unit tests for NeuralAudit
Run with: pytest tests.py -v
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from config import COLOR_FAMILIES, COLOR_LABEL_TO_FAMILY


class TestColorMapping:
    """Test color label to family mapping"""
    
    def test_direct_mapping(self):
        """Test direct color label to family mapping"""
        from auditor import ColorFamilyMatcher
        
        assert ColorFamilyMatcher.get_family_for_label("navy") == "Blue"
        assert ColorFamilyMatcher.get_family_for_label("crimson") == "Red"
        assert ColorFamilyMatcher.get_family_for_label("forest") == "Green"
    
    def test_case_insensitive(self):
        """Test case insensitive mapping"""
        from auditor import ColorFamilyMatcher
        
        assert ColorFamilyMatcher.get_family_for_label("NAVY") == "Blue"
        assert ColorFamilyMatcher.get_family_for_label("Navy") == "Blue"
        assert ColorFamilyMatcher.get_family_for_label("nAvY") == "Blue"
    
    def test_unknown_color(self):
        """Test handling of unknown colors"""
        from auditor import ColorFamilyMatcher
        
        result = ColorFamilyMatcher.get_family_for_label("unknown_color")
        assert result is not None


class TestAuditResult:
    """Test AuditResult class"""
    
    def test_verified_status(self):
        """Test VERIFIED status assignment"""
        from auditor import AuditResult
        
        result = AuditResult(
            product_url="https://example.com/product",
            variant_image_url="https://example.com/image.jpg",
            metadata_color_label="Navy",  # Maps to Blue
            cnn_predicted_class=1,  # Blue
            cnn_confidence=0.95,
            heuristic_valid=True,
            heuristic_confidence=0.90
        )
        
        assert result.status == "VERIFIED"
        assert result.metadata_family == "Blue"
        assert result.predicted_family == "Blue"
    
    def test_flagged_status(self):
        """Test FLAGGED status assignment"""
        from auditor import AuditResult
        
        result = AuditResult(
            product_url="https://example.com/product",
            variant_image_url="https://example.com/image.jpg",
            metadata_color_label="Navy",  # Maps to Blue
            cnn_predicted_class=0,  # Red
            cnn_confidence=0.95,
            heuristic_valid=False,
            heuristic_confidence=-0.90
        )
        
        assert result.status == "FLAGGED"
        assert result.metadata_family == "Blue"
        assert result.predicted_family != result.metadata_family
    
    def test_to_dict(self):
        """Test conversion to dictionary"""
        from auditor import AuditResult
        
        result = AuditResult(
            product_url="https://example.com/product",
            variant_image_url="https://example.com/image.jpg",
            metadata_color_label="Navy",
            cnn_predicted_class=1,
            cnn_confidence=0.95
        )
        
        result_dict = result.to_dict()
        assert "status" in result_dict
        assert "product_url" in result_dict
        assert "cnn_confidence" in result_dict


class TestImagePreprocessing:
    """Test image preprocessing functions"""
    
    @patch('preprocessing.ImagePreprocessor.load_image_from_url')
    def test_preprocess_pipeline(self, mock_load):
        """Test image preprocessing pipeline"""
        from preprocessing import ImagePreprocessor
        
        # Mock image
        mock_image = np.random.rand(300, 300, 3).astype(np.uint8)
        mock_load.return_value = mock_image
        
        # Process
        result = ImagePreprocessor.preprocess_pipeline(mock_image)
        
        assert result is not None
        assert result.shape[-1] == 3  # 3 channels
    
    def test_resize_image(self):
        """Test image resizing"""
        from preprocessing import ImagePreprocessor
        
        image = np.random.rand(100, 100, 3).astype(np.uint8)
        resized = ImagePreprocessor.resize_image(image, size=224)
        
        assert resized.shape == (224, 224, 3)
    
    def test_center_crop(self):
        """Test center cropping"""
        from preprocessing import ImagePreprocessor
        
        image = np.random.rand(200, 200, 3).astype(np.uint8)
        cropped = ImagePreprocessor.center_crop(image, crop_ratio=0.5)
        
        assert cropped.shape[0] <= 200
        assert cropped.shape[1] <= 200
    
    def test_normalize_image(self):
        """Test image normalization"""
        from preprocessing import ImagePreprocessor
        
        image = np.random.randint(0, 255, (224, 224, 3)).astype(np.uint8)
        normalized = ImagePreprocessor.normalize_image(image)
        
        assert normalized.min() >= 0
        assert normalized.max() <= 1
        assert normalized.dtype == np.float32


class TestHeuristicValidation:
    """Test heuristic color validation"""
    
    def test_hue_range_red(self):
        """Test red hue range"""
        from preprocessing import HeuristicColorChecker
        
        # Red hue at 0
        assert HeuristicColorChecker.is_hue_in_range(5, "Red") == True
        assert HeuristicColorChecker.is_hue_in_range(175, "Red") == True
    
    def test_hue_range_blue(self):
        """Test blue hue range"""
        from preprocessing import HeuristicColorChecker
        
        # Blue hue around 110
        assert HeuristicColorChecker.is_hue_in_range(110, "Blue") == True
        assert HeuristicColorChecker.is_hue_in_range(50, "Blue") == False
    
    def test_hue_range_green(self):
        """Test green hue range"""
        from preprocessing import HeuristicColorChecker
        
        # Green hue around 60
        assert HeuristicColorChecker.is_hue_in_range(60, "Green") == True
        assert HeuristicColorChecker.is_hue_in_range(110, "Green") == False


class TestAuditEngine:
    """Test audit engine"""
    
    def test_audit_variant(self):
        """Test variant auditing"""
        from auditor import AuditEngine
        
        result = AuditEngine.audit_variant(
            product_url="https://example.com/product",
            variant_image_url="https://example.com/image.jpg",
            metadata_color_label="Navy",
            cnn_predicted_class=1,  # Blue
            cnn_confidence=0.92
        )
        
        assert result is not None
        assert result.status in ["VERIFIED", "FLAGGED", "UNCERTAIN"]
    
    def test_batch_audit(self):
        """Test batch auditing"""
        from auditor import AuditEngine
        
        audit_data = [
            {
                "product_url": "https://example.com/product1",
                "variant_image_url": "https://example.com/image1.jpg",
                "metadata_color_label": "Navy",
                "cnn_predicted_class": 1,
                "cnn_confidence": 0.92
            },
            {
                "product_url": "https://example.com/product2",
                "variant_image_url": "https://example.com/image2.jpg",
                "metadata_color_label": "Crimson",
                "cnn_predicted_class": 0,
                "cnn_confidence": 0.88
            }
        ]
        
        results = AuditEngine.audit_batch(audit_data)
        
        assert len(results) == 2
        assert all(isinstance(r, type(results[0])) for r in results)
    
    def test_generate_report(self):
        """Test report generation"""
        from auditor import AuditEngine, AuditResult
        
        results = [
            AuditResult(
                product_url="https://example.com/product",
                variant_image_url="https://example.com/image.jpg",
                metadata_color_label="Navy",
                cnn_predicted_class=1,
                cnn_confidence=0.92
            ) for _ in range(10)
        ]
        
        report = AuditEngine.generate_report(results)
        
        assert report["total_variants"] == 10
        assert "verification_rate" in report
        assert "flag_rate" in report


class TestModelTensor:
    """Test model tensor utilities"""
    
    def test_tensor_from_numpy(self):
        """Test numpy to tensor conversion"""
        from model import tensor_from_numpy
        
        image = np.random.rand(224, 224, 3).astype(np.float32)
        tensor = tensor_from_numpy(image)
        
        assert tensor.shape[0] == 3  # Channels first
        assert tensor.dtype == torch.float32
    
    def test_get_color_family_name(self):
        """Test color family name retrieval"""
        from model import get_color_family_name
        
        assert get_color_family_name(0) in COLOR_FAMILIES.values()
        assert get_color_family_name(1) in COLOR_FAMILIES.values()


class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_validate_url(self):
        """Test URL validation"""
        from utils import validate_url
        
        assert validate_url("https://example.com") == True
        assert validate_url("http://example.com") == True
        assert validate_url("invalid-url") == False
        assert validate_url("") == False
    
    def test_format_confidence(self):
        """Test confidence formatting"""
        from utils import format_confidence
        
        assert format_confidence(0.92) == "92.0%"
        assert format_confidence(0.5) == "50.0%"
        assert format_confidence(1.0) == "100.0%"
    
    def test_human_readable_time(self):
        """Test human readable time formatting"""
        from utils import human_readable_time
        
        assert "s" in human_readable_time(30)
        assert "m" in human_readable_time(120)
        assert "h" in human_readable_time(3600)


@pytest.mark.skipif(True, reason="Requires GPU")
class TestModelInference:
    """Test model inference (GPU dependent)"""
    
    @patch('model.torch.cuda.is_available')
    def test_inference_cpu(self, mock_cuda):
        """Test inference on CPU"""
        from model import ModelInference
        import torch
        
        mock_cuda.return_value = False
        inference = ModelInference(device='cpu')
        
        # Create dummy image
        image = torch.randn(1, 3, 224, 224)
        
        # Predict
        class_id, confidence = inference.predict(image)
        
        assert 0 <= class_id < len(COLOR_FAMILIES)
        assert 0 <= confidence <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
