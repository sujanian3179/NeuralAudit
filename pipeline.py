"""
End-to-End Processing Pipeline
Orchestrates scraping, preprocessing, inference, and auditing
"""
from typing import List, Dict, Tuple
import torch
from logger import logger
from config import PROCESSING_BATCH_SIZE
from scraper import ProductScraper, scrape_batch
from preprocessing import ImagePreprocessor, HeuristicColorChecker
from model import ModelInference, tensor_from_numpy
from auditor import AuditEngine, AuditResult
from database import DatabaseManager, LocalDataStore


class NeuralAuditPipeline:
    """
    Main processing pipeline that coordinates all components.
    """
    
    def __init__(self, use_gpu: bool = False):
        """
        Initialize the pipeline.
        
        Args:
            use_gpu: Whether to use GPU for inference
        """
        device = "cuda" if (use_gpu and torch.cuda.is_available()) else "cpu"
        logger.info(f"Initializing NeuralAudit pipeline with device: {device}")
        
        self.device = device
        self.model_inference = ModelInference(device=device)
        self.db = DatabaseManager()
        self.local_store = LocalDataStore()
        self.preprocessor = ImagePreprocessor()
        
        logger.info("Pipeline initialized successfully")
    
    def process_product(self, product_url: str) -> List[AuditResult]:
        """
        Process a single product URL end-to-end.
        
        Args:
            product_url: URL of the product to audit
        
        Returns:
            List of AuditResult objects
        """
        logger.info(f"Processing product: {product_url}")
        audit_results = []
        
        try:
            # Step 1: Scrape variants
            logger.info("Step 1: Scraping variants...")
            scraper = ProductScraper()
            try:
                variant_pairs = scraper.scrape_product(product_url)
            finally:
                scraper.close()
            
            if not variant_pairs:
                logger.warning(f"No variants found for {product_url}")
                return audit_results
            
            logger.info(f"Found {len(variant_pairs)} variants")
            
            # Step 2: Process each variant
            for image_url, color_label in variant_pairs:
                try:
                    result = self._process_variant(
                        product_url=product_url,
                        image_url=image_url,
                        color_label=color_label
                    )
                    if result:
                        audit_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing variant {image_url}: {e}")
                    continue
            
            # Step 3: Save results
            self._save_results(audit_results)
            
            logger.info(f"Completed processing of {product_url}: {len(audit_results)} results")
            return audit_results
        
        except Exception as e:
            logger.error(f"Error processing product {product_url}: {e}")
            return audit_results
    
    def _process_variant(
        self,
        product_url: str,
        image_url: str,
        color_label: str
    ) -> AuditResult:
        """
        Process a single variant through the full pipeline.
        
        Args:
            product_url: Product URL
            image_url: Variant image URL
            color_label: Metadata color label
        
        Returns:
            AuditResult object
        """
        logger.debug(f"Processing variant: {color_label}")
        
        # Preprocess image
        processed_image = self.preprocessor.preprocess_for_inference(image_url)
        if processed_image is None:
            raise ValueError(f"Failed to preprocess image: {image_url}")
        
        # Get HSV for heuristic check
        image_bgr = self.preprocessor.load_image_from_url(image_url)
        image_hsv = self.preprocessor.to_hsv(image_bgr) if image_bgr is not None else None
        
        # CNN inference
        image_tensor = tensor_from_numpy(processed_image)
        predicted_class, cnn_confidence = self.model_inference.predict(image_tensor)
        
        # Heuristic validation
        heuristic_valid = True
        heuristic_confidence = 0.0
        if image_hsv is not None:
            from config import COLOR_FAMILIES
            predicted_family = COLOR_FAMILIES.get(predicted_class, "Unknown")
            heuristic_valid, heuristic_confidence = HeuristicColorChecker.validate_color(
                image_hsv,
                predicted_family
            )
        
        # Audit
        result = AuditEngine.audit_variant(
            product_url=product_url,
            variant_image_url=image_url,
            metadata_color_label=color_label,
            cnn_predicted_class=predicted_class,
            cnn_confidence=cnn_confidence,
            heuristic_valid=heuristic_valid,
            heuristic_confidence=heuristic_confidence
        )
        
        logger.debug(f"Variant result: {result}")
        return result
    
    def process_batch(
        self,
        product_urls: List[str],
        save_to_db: bool = True
    ) -> Dict[str, List[AuditResult]]:
        """
        Process multiple product URLs.
        
        Args:
            product_urls: List of product URLs
            save_to_db: Whether to save results to database
        
        Returns:
            Dictionary: {url: [AuditResult, ...], ...}
        """
        logger.info(f"Processing batch of {len(product_urls)} products")
        results = {}
        all_results = []
        
        for i, url in enumerate(product_urls, 1):
            logger.info(f"Processing {i}/{len(product_urls)}: {url}")
            try:
                audit_results = self.process_product(url)
                results[url] = audit_results
                all_results.extend(audit_results)
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                results[url] = []
        
        # Save batch results
        if save_to_db and all_results:
            self._save_results(all_results)
        
        logger.info(f"Batch processing complete: {len(all_results)} total results")
        return results
    
    def _save_results(self, audit_results: List[AuditResult]):
        """
        Save audit results to database and local storage.
        
        Args:
            audit_results: List of AuditResult objects
        """
        try:
            result_dicts = [r.to_dict() for r in audit_results]
            
            # Try database
            if self.db.client:
                self.db.insert_batch(result_dicts)
            else:
                logger.warning("Database not available, using local storage only")
            
            # Always save locally as backup
            existing = self.local_store.load()
            existing.extend(result_dicts)
            self.local_store.save(existing)
            
            logger.info(f"Saved {len(audit_results)} results")
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def get_product_report(self, product_url: str) -> Dict:
        """
        Get audit report for a product.
        
        Args:
            product_url: Product URL
        
        Returns:
            Report dictionary
        """
        try:
            summary = self.db.get_product_summary(product_url)
            results = self.db.query_audit_results(product_url=product_url)
            
            report = {
                "product_url": product_url,
                "summary": summary,
                "flagged_variants": [r for r in results if r.get("status") == "FLAGGED"],
                "uncertain_variants": [r for r in results if r.get("status") == "UNCERTAIN"],
            }
            
            return report
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return {}
    
    def get_global_statistics(self) -> Dict:
        """
        Get global audit statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            return self.db.get_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


def process_product_from_file(csv_file: str, use_gpu: bool = False) -> List[Dict]:
    """
    Process products from a CSV file.
    CSV should have 'url' column.
    
    Args:
        csv_file: Path to CSV file
        use_gpu: Whether to use GPU
    
    Returns:
        List of results
    """
    try:
        import pandas as pd
        
        df = pd.read_csv(csv_file)
        if 'url' not in df.columns:
            raise ValueError("CSV must have 'url' column")
        
        urls = df['url'].tolist()
        pipeline = NeuralAuditPipeline(use_gpu=use_gpu)
        
        results = pipeline.process_batch(urls)
        
        # Flatten results
        flat_results = []
        for url, audit_results in results.items():
            for result in audit_results:
                flat_results.append(result.to_dict())
        
        return flat_results
    except Exception as e:
        logger.error(f"Error processing CSV file: {e}")
        return []


if __name__ == "__main__":
    # Example usage
    pipeline = NeuralAuditPipeline(use_gpu=False)
    
    # Process single product
    results = pipeline.process_product("https://example.com/product")
    print(f"Processed {len(results)} variants")
    
    # Get statistics
    stats = pipeline.get_global_statistics()
    print(f"Statistics: {stats}")
