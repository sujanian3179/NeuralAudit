"""
Example scripts demonstrating NeuralAudit functionality
"""

# Example 1: Process a single product
def example_single_product():
    """Process one product and display results"""
    from pipeline import NeuralAuditPipeline
    
    pipeline = NeuralAuditPipeline(use_gpu=False)
    
    product_url = "https://example.com/product"
    results = pipeline.process_product(product_url)
    
    print(f"\n🔍 Audit Results for {product_url}\n")
    print(f"{'Color':<20} {'Predicted':<15} {'Status':<12} {'Confidence':<12}")
    print("-" * 60)
    
    for result in results:
        print(f"{result.metadata_color_label:<20} {result.predicted_family:<15} "
              f"{result.status:<12} {result.cnn_confidence:.2%}")
    
    # Summary
    verified = sum(1 for r in results if r.status == "VERIFIED")
    flagged = sum(1 for r in results if r.status == "FLAGGED")
    print(f"\n✓ Verified: {verified}")
    print(f"✗ Flagged: {flagged}")


# Example 2: Batch processing
def example_batch_processing():
    """Process multiple products"""
    from pipeline import NeuralAuditPipeline
    
    pipeline = NeuralAuditPipeline(use_gpu=False)
    
    products = [
        "https://example.com/product1",
        "https://example.com/product2",
        "https://example.com/product3",
    ]
    
    results = pipeline.process_batch(products)
    
    for product, audit_results in results.items():
        print(f"\n{product}")
        print(f"  Variants: {len(audit_results)}")
        if audit_results:
            flagged = sum(1 for r in audit_results if r.status == "FLAGGED")
            print(f"  Issues: {flagged}")


# Example 3: Manual audit without scraping
def example_manual_audit():
    """Manually audit a variant without scraping"""
    from auditor import AuditEngine
    
    result = AuditEngine.audit_variant(
        product_url="https://example.com/product",
        variant_image_url="https://cdn.example.com/blue.jpg",
        metadata_color_label="Royal Blue",
        cnn_predicted_class=1,  # Blue class
        cnn_confidence=0.92,
        heuristic_valid=True,
        heuristic_confidence=0.85
    )
    
    print(f"\nAudit Result:")
    print(f"  Status: {result.status}")
    print(f"  Expected: {result.metadata_family}")
    print(f"  Predicted: {result.predicted_family}")
    print(f"  Confidence: {result.confidence_score:.3f}")


# Example 4: Color family mapping
def example_color_mapping():
    """Demonstrate color family mapping"""
    from auditor import ColorFamilyMatcher
    
    labels = [
        "Navy Blue",
        "Crimson Red",
        "Forest Green",
        "Sky Blue",
        "Burgundy",
    ]
    
    print("\n📋 Color Family Mapping:\n")
    for label in labels:
        family = ColorFamilyMatcher.get_family_for_label(label)
        print(f"  {label:<20} → {family}")


# Example 5: Query results from database
def example_database_queries():
    """Query audit results from database"""
    from database import DatabaseManager
    
    db = DatabaseManager()
    
    # Get statistics
    stats = db.get_statistics()
    print("\n📊 Overall Statistics:")
    print(f"  Total audits: {stats.get('total_audits', 0)}")
    print(f"  Verified: {stats.get('verified', 0)}")
    print(f"  Flagged: {stats.get('flagged', 0)}")
    print(f"  Verification rate: {stats.get('verification_rate', 0):.1%}")
    
    # Get flagged results
    flagged = db.query_flagged_results(limit=5)
    if flagged:
        print("\n⚠️  Recent Flagged Results:")
        for result in flagged:
            print(f"  {result['metadata_color_label']} "
                  f"(predicted: {result['predicted_family']})")
    
    # Get product summary
    product_summary = db.get_product_summary("https://example.com/product")
    if product_summary and product_summary.get('total_variants'):
        print(f"\n📦 Product Summary:")
        print(f"  URL: {product_summary['product_url']}")
        print(f"  Variants: {product_summary['total_variants']}")
        print(f"  Flagged: {product_summary['flagged']}")


# Example 6: Process from CSV file
def example_csv_processing():
    """Process products from CSV file"""
    from pipeline import process_product_from_file
    
    # Expected CSV format:
    # url
    # https://example.com/product1
    # https://example.com/product2
    
    results = process_product_from_file("products.csv", use_gpu=False)
    
    print(f"\n📊 CSV Processing Results:")
    print(f"  Total variants processed: {len(results)}")
    
    verified = sum(1 for r in results if r.get('status') == 'VERIFIED')
    flagged = sum(1 for r in results if r.get('status') == 'FLAGGED')
    
    print(f"  ✓ Verified: {verified}")
    print(f"  ✗ Flagged: {flagged}")


# Example 7: Image preprocessing
def example_image_preprocessing():
    """Demonstrate image preprocessing"""
    from preprocessing import ImagePreprocessor
    
    image_url = "https://example.com/image.jpg"
    
    # Load and preprocess
    processed = ImagePreprocessor.preprocess_for_inference(image_url)
    
    if processed is not None:
        print(f"\n🖼️  Image Processing:")
        print(f"  Shape: {processed.shape}")
        print(f"  Dtype: {processed.dtype}")
        print(f"  Min: {processed.min():.3f}")
        print(f"  Max: {processed.max():.3f}")


# Example 8: Model inference
def example_model_inference():
    """Demonstrate model inference"""
    from model import ModelInference, tensor_from_numpy, get_color_family_name
    import torch
    
    inference = ModelInference(device='cpu')
    
    # Create dummy image
    dummy_image = torch.randn(1, 3, 224, 224)
    
    # Single prediction
    class_id, confidence = inference.predict(dummy_image)
    family_name = get_color_family_name(class_id)
    
    print(f"\n🤖 Model Inference:")
    print(f"  Predicted: {family_name} (Class {class_id})")
    print(f"  Confidence: {confidence:.4f}")
    
    # Top-k predictions
    top_k = inference.predict_with_top_k(dummy_image, k=3)
    print(f"\n  Top-3 Predictions:")
    for class_id, prob in top_k:
        print(f"    {get_color_family_name(class_id)}: {prob:.4f}")


# Example 9: Heuristic color validation
def example_heuristic_validation():
    """Demonstrate HSV-based heuristic validation"""
    from preprocessing import ImagePreprocessor, HeuristicColorChecker
    
    image_url = "https://example.com/image.jpg"
    
    # Load image and convert to HSV
    image = ImagePreprocessor.load_image_from_url(image_url)
    if image is not None:
        image_hsv = ImagePreprocessor.to_hsv(image)
        
        # Get dominant hue
        hue, saturation = ImagePreprocessor.get_dominant_hue(image_hsv)
        print(f"\n🎨 HSV Analysis:")
        print(f"  Dominant Hue: {hue}")
        print(f"  Saturation: {saturation:.2f}")
        
        # Validate against color families
        print(f"\n  Validation against families:")
        for family in ["Red", "Blue", "Green"]:
            is_valid = HeuristicColorChecker.is_hue_in_range(hue, family)
            print(f"    {family}: {'✓' if is_valid else '✗'}")


# Example 10: Generate audit report
def example_audit_report():
    """Generate comprehensive audit report"""
    from pipeline import NeuralAuditPipeline
    from auditor import AuditEngine
    
    pipeline = NeuralAuditPipeline()
    
    # Process product
    results = pipeline.process_product("https://example.com/product")
    
    if results:
        # Generate report
        report = AuditEngine.generate_report(results)
        
        print(f"\n📋 Audit Report:")
        print(f"  Total Variants: {report['total_variants']}")
        print(f"  Verification Rate: {report['verification_rate']:.1%}")
        print(f"  Flag Rate: {report['flag_rate']:.1%}")
        print(f"  Avg Confidence: {report['avg_confidence']:.3f}")
        
        if report['flagged_variants']:
            print(f"\n  Flagged Variants:")
            for variant in report['flagged_variants'][:5]:
                print(f"    - {variant['metadata_color_label']} "
                      f"(predicted: {variant['predicted_family']})")


if __name__ == "__main__":
    import sys
    
    examples = {
        "1": ("Single Product", example_single_product),
        "2": ("Batch Processing", example_batch_processing),
        "3": ("Manual Audit", example_manual_audit),
        "4": ("Color Mapping", example_color_mapping),
        "5": ("Database Queries", example_database_queries),
        "6": ("CSV Processing", example_csv_processing),
        "7": ("Image Preprocessing", example_image_preprocessing),
        "8": ("Model Inference", example_model_inference),
        "9": ("Heuristic Validation", example_heuristic_validation),
        "10": ("Audit Report", example_audit_report),
    }
    
    print("\n🎯 NeuralAudit Examples\n")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print(f"  0. Run all")
    print(f"  q. Quit\n")
    
    choice = input("Select example (0-10): ").strip()
    
    if choice == "0":
        for name, func in examples.values():
            try:
                print(f"\n\n{'='*60}")
                print(f"Running: {name}")
                print(f"{'='*60}")
                func()
            except Exception as e:
                print(f"Error: {e}")
    elif choice in examples:
        try:
            name, func = examples[choice]
            func()
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif choice != "q":
        print("Invalid selection")
        sys.exit(1)
