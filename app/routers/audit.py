"""
Audit endpoints router
Handles manual audits and single product processing
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Callable

from logger import logger
from app.schemas import (
    AuditRequest,
    AuditResponse,
    ProductUrl,
)
from app.dependencies import get_pipeline, get_database

# Create router with prefix and tags
router = APIRouter(
    prefix="/api",
    tags=["Audit"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/audit",
    response_model=AuditResponse,
    summary="Manual audit without web scraping",
    description="Audit a product variant using pre-collected data"
)
async def manual_audit(request: AuditRequest):
    """
    🔍 **Manually audit a product variant without web scraping**
    
    Use this when you have:
    - Product URL
    - Product image URL
    - Expected color label (metadata)
    - CNN prediction (class ID 0-9)
    - Confidence score (0-1)
    
    The API will:
    1. Map metadata color to color family
    2. Map CNN prediction to color family
    3. Compare and return status (VERIFIED/FLAGGED/UNCERTAIN)
    
    **Example Input:**
    ```json
    {
        "product_url": "https://www.amazon.com/shirt-colors/dp/B001234567",
        "variant_image_url": "https://images-na.ssl-images-amazon.com/images/I/example.jpg",
        "metadata_color_label": "Navy Blue",
        "cnn_predicted_class": 1,
        "cnn_confidence": 0.92
    }
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "result": {
            "product_url": "https://www.amazon.com/shirt-colors/dp/B001234567",
            "metadata_family": "Blue",
            "predicted_family": "Blue",
            "status": "VERIFIED",
            "overall_confidence": 0.95,
            "cnn_confidence": 0.92
        }
    }
    ```
    
    Returns:
        AuditResponse: Audit result with status and confidence
        
    Raises:
        HTTPException: If audit fails or invalid input provided
    """
    try:
        from auditor import AuditEngine
        
        result = AuditEngine.audit_variant(
            product_url=request.product_url,
            variant_image_url=request.variant_image_url,
            metadata_color_label=request.metadata_color_label,
            cnn_predicted_class=request.cnn_predicted_class,
            cnn_confidence=request.cnn_confidence
        )
        
        # Save to database
        db = get_database()
        if db.client:
            db.insert_audit_result(result.to_dict())
        
        logger.info(f"Manual audit completed: {request.product_url}")
        
        return {
            "status": "success",
            "result": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Error during manual audit: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/process-product",
    summary="Process single product URL",
    description="Full scraping, image analysis, and color family mapping"
)
async def process_single_product(
    request: ProductUrl,
    background_tasks: BackgroundTasks
):
    """
    🌐 **Process a single e-commerce product URL (Full Scraping + AI Analysis)**
    
    This endpoint:
    1. Opens the product page in a headless browser
    2. Finds all color swatch elements
    3. Clicks each swatch sequentially
    4. Captures the product image URL for each color
    5. Extracts the color label from metadata
    6. Analyzes each image with ResNet-18 CNN
    7. Maps color families and determines status
    
    **Processing Flow:**
    ```
    E-commerce URL 
      → Click Color Swatches 
      → Capture (Image, Label) Pairs 
      → AI Analysis 
      → Family Mapping 
      → Status Decision
    ```
    
    **Example Input:**
    ```json
    {
        "url": "https://www.amazon.com/Example-Product-Multiple-Colors/dp/B001234567"
    }
    ```
    
    **Example Output (after processing):**
    ```json
    {
        "product_url": "https://www.amazon.com/Example-Product-Multiple-Colors/dp/B001234567",
        "variants": [
            {
                "metadata_color_label": "Navy Blue",
                "predicted_family": "Blue",
                "status": "VERIFIED ✅",
                "cnn_confidence": 0.92,
                "overall_confidence": 0.95
            },
            {
                "metadata_color_label": "Red",
                "predicted_family": "Red",
                "status": "VERIFIED ✅",
                "cnn_confidence": 0.88,
                "overall_confidence": 0.91
            }
        ],
        "summary": {
            "total_variants": 2,
            "verified_count": 2,
            "flagged_count": 0,
            "verification_rate": 100.0
        }
    }
    ```
    
    **Status Meanings:**
    - 🟢 **VERIFIED**: Metadata color matches CNN prediction
    - 🔴 **FLAGGED**: Mismatch detected (possible content error)
    - 🟡 **UNCERTAIN**: Low confidence - manual review recommended
    
    Returns:
        JSONResponse: Processing status and message
        
    Raises:
        HTTPException: If product URL is invalid or processing fails
    """
    try:
        product_url = str(request.url)
        pipeline = get_pipeline()
        
        logger.info(f"Starting product processing: {product_url}")
        
        # Run in background
        background_tasks.add_task(pipeline.process_product, product_url)
        
        return JSONResponse({
            "status": "processing",
            "product_url": product_url,
            "message": "Product is being processed in background. Check results with /api/product-report/{url}"
        })
    except Exception as e:
        logger.error(f"Error starting product processing: {e}")
        raise HTTPException(status_code=400, detail=str(e))
