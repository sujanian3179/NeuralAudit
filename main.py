#!/usr/bin/env python3
"""
NeuralAudit Main Entry Point
Provides CLI interface for product auditing
"""
import argparse
import sys
from logger import logger
from pipeline import NeuralAuditPipeline, process_product_from_file
from auditor import AuditEngine
import json


def main():
    """Main entry point with CLI arguments"""
    
    parser = argparse.ArgumentParser(
        description="NeuralAudit - E-commerce Variant Integrity System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single product
  python main.py --product "https://example.com/product"
  
  # Process multiple products from CSV
  python main.py --csv products.csv
  
  # Start API server
  python main.py --api
  
  # Process with GPU
  python main.py --product "https://example.com/product" --gpu
        """
    )
    
    parser.add_argument(
        "--product",
        type=str,
        help="Single product URL to audit"
    )
    
    parser.add_argument(
        "--csv",
        type=str,
        help="CSV file with product URLs (must have 'url' column)"
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Start the FastAPI server"
    )
    
    parser.add_argument(
        "--gpu",
        action="store_true",
        help="Use GPU for inference (if available)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="audit_results.json",
        help="Output file for results (default: audit_results.json)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to .env configuration file"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Load custom config if provided
    if args.config:
        from dotenv import load_dotenv
        load_dotenv(args.config)
        logger.info(f"Loaded config from {args.config}")
    
    # Set log level
    if args.verbose:
        import logging
        from logger import logger as root_logger
        root_logger.setLevel(logging.DEBUG)
        logger.info("Verbose logging enabled")
    
    try:
        if args.api:
            # Start API server
            logger.info("Starting FastAPI server...")
            start_api()
        
        elif args.product:
            # Process single product
            logger.info(f"Processing product: {args.product}")
            process_single_product(args.product, args.output, args.gpu)
        
        elif args.csv:
            # Process from CSV
            logger.info(f"Processing products from CSV: {args.csv}")
            process_from_csv(args.csv, args.output, args.gpu)
        
        else:
            # No action specified
            parser.print_help()
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def process_single_product(product_url: str, output_file: str, use_gpu: bool):
    """
    Process a single product and save results.
    
    Args:
        product_url: Product URL to audit
        output_file: File to save results
        use_gpu: Whether to use GPU
    """
    pipeline = NeuralAuditPipeline(use_gpu=use_gpu)
    
    logger.info(f"Auditing product: {product_url}")
    results = pipeline.process_product(product_url)
    
    if results:
        # Convert to dict for JSON serialization
        results_dict = [r.to_dict() for r in results]
        
        with open(output_file, 'w') as f:
            json.dump(results_dict, f, indent=2)
        
        logger.info(f"Results saved to {output_file}")
        
        # Print summary
        verified = sum(1 for r in results if r.status == "VERIFIED")
        flagged = sum(1 for r in results if r.status == "FLAGGED")
        uncertain = sum(1 for r in results if r.status == "UNCERTAIN")
        
        print("\n" + "="*50)
        print(f"Product: {product_url}")
        print("="*50)
        print(f"Total variants: {len(results)}")
        print(f"✓ Verified: {verified}")
        print(f"✗ Flagged: {flagged}")
        print(f"? Uncertain: {uncertain}")
        print("="*50 + "\n")
        
        if flagged > 0:
            print("FLAGGED VARIANTS:")
            for r in results:
                if r.status == "FLAGGED":
                    print(f"  - {r.metadata_color_label} (predicted: {r.predicted_family})")
    else:
        logger.warning("No results produced")


def process_from_csv(csv_file: str, output_file: str, use_gpu: bool):
    """
    Process products from a CSV file.
    
    Args:
        csv_file: Path to CSV file
        output_file: File to save results
        use_gpu: Whether to use GPU
    """
    try:
        results = process_product_from_file(csv_file, use_gpu=use_gpu)
        
        if results:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            logger.info(f"Results saved to {output_file}")
            
            # Print summary
            total = len(results)
            verified = sum(1 for r in results if r.get('status') == "VERIFIED")
            flagged = sum(1 for r in results if r.get('status') == "FLAGGED")
            
            print("\n" + "="*50)
            print("BATCH PROCESSING SUMMARY")
            print("="*50)
            print(f"Total variants: {total}")
            print(f"✓ Verified: {verified} ({100*verified/total:.1f}%)")
            print(f"✗ Flagged: {flagged} ({100*flagged/total:.1f}%)")
            print("="*50 + "\n")
        else:
            logger.warning("No results produced")
    
    except Exception as e:
        logger.error(f"Error processing CSV: {e}")
        sys.exit(1)


def start_api():
    """Start the FastAPI server using production-ready app.server module"""
    from app.server import app
    import uvicorn
    from config import API_HOST, API_PORT
    
    logger.info(f"Starting API server on {API_HOST}:{API_PORT}")
    print(f"\n🚀 NeuralAudit API Server")
    print(f"📍 Running at: http://{API_HOST}:{API_PORT}")
    print(f"📚 API Docs: http://{API_HOST}:{API_PORT}/docs")
    print(f"📖 ReDoc: http://{API_HOST}:{API_PORT}/redoc\n")
    
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
