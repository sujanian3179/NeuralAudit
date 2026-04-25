"""
Integration tests for NeuralAudit end-to-end workflow
"""
import os
import tempfile
import json
from pathlib import Path


def test_end_to_end_workflow():
    """
    Complete end-to-end workflow test
    """
    print("\n" + "="*60)
    print("🧪 NeuralAudit End-to-End Integration Test")
    print("="*60)
    
    # Test 1: Configuration
    print("\n✓ Test 1: Configuration")
    from config import COLOR_FAMILIES, COLOR_LABEL_TO_FAMILY
    assert len(COLOR_FAMILIES) == 10, "Should have 10 color families"
    assert "Blue" in COLOR_LABEL_TO_FAMILY.values(), "Blue mapping should exist"
    print("  Configuration loaded successfully")
    
    # Test 2: Color Mapping
    print("\n✓ Test 2: Color Mapping")
    from auditor import ColorFamilyMatcher
    assert ColorFamilyMatcher.get_family_for_label("navy") == "Blue"
    assert ColorFamilyMatcher.get_family_for_label("crimson") == "Red"
    print("  Color mapping working correctly")
    
    # Test 3: Audit Result Creation
    print("\n✓ Test 3: Audit Result Creation")
    from auditor import AuditResult
    result = AuditResult(
        product_url="https://example.com/product",
        variant_image_url="https://example.com/image.jpg",
        metadata_color_label="Navy Blue",
        cnn_predicted_class=1,
        cnn_confidence=0.92
    )
    assert result.status == "VERIFIED"
    assert result.metadata_family == "Blue"
    print(f"  Result created: {result.status}")
    
    # Test 4: Batch Auditing
    print("\n✓ Test 4: Batch Auditing")
    from auditor import AuditEngine
    audit_data = [
        {
            "product_url": "https://example.com/p1",
            "variant_image_url": "https://example.com/i1.jpg",
            "metadata_color_label": "Navy",
            "cnn_predicted_class": 1,
            "cnn_confidence": 0.92
        },
        {
            "product_url": "https://example.com/p2",
            "variant_image_url": "https://example.com/i2.jpg",
            "metadata_color_label": "Crimson",
            "cnn_predicted_class": 0,
            "cnn_confidence": 0.88
        }
    ]
    
    results = AuditEngine.audit_batch(audit_data)
    assert len(results) == 2
    print(f"  Batch audited: {len(results)} variants")
    
    # Test 5: Report Generation
    print("\n✓ Test 5: Report Generation")
    report = AuditEngine.generate_report(results)
    assert report["total_variants"] == 2
    assert "verification_rate" in report
    print(f"  Report generated: {report['verification_rate']:.1%} verified")
    
    # Test 6: Image Preprocessing
    print("\n✓ Test 6: Image Preprocessing")
    from preprocessing import ImagePreprocessor
    import numpy as np
    
    image = np.random.rand(300, 300, 3).astype(np.uint8)
    resized = ImagePreprocessor.resize_image(image)
    assert resized.shape == (224, 224, 3)
    print("  Image resizing: 300x300 → 224x224")
    
    cropped = ImagePreprocessor.center_crop(image)
    assert cropped.shape[0] <= 300
    print("  Center cropping: OK")
    
    normalized = ImagePreprocessor.normalize_image(image)
    assert normalized.min() >= 0 and normalized.max() <= 1
    print("  Normalization: [0, 1] range OK")
    
    # Test 7: HSV Analysis
    print("\n✓ Test 7: HSV Analysis")
    from preprocessing import HeuristicColorChecker
    image_hsv = ImagePreprocessor.to_hsv(image)
    hue, saturation = ImagePreprocessor.get_dominant_hue(image_hsv)
    assert 0 <= hue <= 179
    assert 0 <= saturation <= 1
    print(f"  Hue: {hue}, Saturation: {saturation:.2f}")
    
    # Test 8: Color Family Validation
    print("\n✓ Test 8: Color Family Validation")
    families = ["Red", "Blue", "Green"]
    for family in families:
        is_valid = HeuristicColorChecker.is_hue_in_range(hue, family)
        print(f"  Hue {hue} matches {family}: {is_valid}")
    
    # Test 9: Model Tensor Conversion
    print("\n✓ Test 9: Model Tensor Conversion")
    from model import tensor_from_numpy
    import torch
    
    image_array = np.random.rand(224, 224, 3).astype(np.float32)
    tensor = tensor_from_numpy(image_array)
    assert tensor.shape[0] == 3  # Channels first
    assert tensor.dtype == torch.float32
    print(f"  Tensor shape: {tensor.shape}")
    
    # Test 10: Utility Functions
    print("\n✓ Test 10: Utility Functions")
    from utils import validate_url, format_confidence, human_readable_time
    
    assert validate_url("https://example.com") == True
    assert format_confidence(0.92) == "92.0%"
    assert "s" in human_readable_time(30)
    print("  All utilities working correctly")
    
    # Test 11: Local Data Storage
    print("\n✓ Test 11: Local Data Storage")
    from database import LocalDataStore
    
    with tempfile.TemporaryDirectory() as tmpdir:
        store = LocalDataStore()
        test_results = [
            {
                "product_url": "https://example.com/p1",
                "status": "VERIFIED",
                "confidence": 0.92
            }
        ]
        
        store.save(test_results)
        loaded = store.load()
        assert len(loaded) > 0
        print("  Local storage: Save/Load OK")
    
    # Test 12: Configuration Loading
    print("\n✓ Test 12: Configuration Loading")
    from config import (
        SELENIUM_HEADLESS, IMAGE_SIZE, NUM_CLASSES,
        CONFIDENCE_THRESHOLD, API_PORT
    )
    
    assert SELENIUM_HEADLESS in [True, False]
    assert IMAGE_SIZE == 224
    assert NUM_CLASSES == 10
    assert CONFIDENCE_THRESHOLD > 0
    assert API_PORT > 0
    print("  All configs loaded successfully")
    
    print("\n" + "="*60)
    print("✅ All Integration Tests Passed!")
    print("="*60 + "\n")
    
    return True


def test_performance():
    """
    Performance and scalability tests
    """
    print("\n" + "="*60)
    print("⚡ NeuralAudit Performance Tests")
    print("="*60)
    
    import time
    from auditor import AuditEngine
    
    # Test 1: Single Audit Speed
    print("\n✓ Test 1: Single Audit Performance")
    start = time.time()
    
    for _ in range(100):
        AuditEngine.audit_variant(
            product_url="https://example.com/product",
            variant_image_url="https://example.com/image.jpg",
            metadata_color_label="Navy",
            cnn_predicted_class=1,
            cnn_confidence=0.92
        )
    
    elapsed = time.time() - start
    per_audit = (elapsed / 100) * 1000
    print(f"  100 audits: {elapsed:.3f}s ({per_audit:.2f}ms per audit)")
    
    # Test 2: Batch Processing Speed
    print("\n✓ Test 2: Batch Processing Performance")
    start = time.time()
    
    audit_data = [
        {
            "product_url": f"https://example.com/p{i}",
            "variant_image_url": f"https://example.com/i{i}.jpg",
            "metadata_color_label": "Navy",
            "cnn_predicted_class": 1,
            "cnn_confidence": 0.92
        }
        for i in range(1000)
    ]
    
    results = AuditEngine.audit_batch(audit_data)
    elapsed = time.time() - start
    print(f"  1000 variants: {elapsed:.3f}s ({len(results)/elapsed:.0f} variants/sec)")
    
    # Test 3: Report Generation Speed
    print("\n✓ Test 3: Report Generation Performance")
    start = time.time()
    
    for _ in range(100):
        AuditEngine.generate_report(results)
    
    elapsed = time.time() - start
    print(f"  100 reports: {elapsed:.3f}s ({(elapsed/100)*1000:.2f}ms per report)")
    
    print("\n" + "="*60)
    print("✅ Performance Tests Complete")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    try:
        test_end_to_end_workflow()
        test_performance()
        print("\n🎉 All tests passed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        exit(1)
