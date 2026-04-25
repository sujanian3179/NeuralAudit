"""
Results endpoints router
Handles fetching and querying audit results
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from logger import logger
from app.schemas import ResultsResponse, ProductReportResponse
from app.dependencies import get_pipeline, get_database

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Results"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/product-report/{product_url:path}",
    response_model=ProductReportResponse,
    summary="Get product audit report",
    description="Get all audit results for a processed product"
)
async def get_product_report(product_url: str):
    """
    📋 **Get audit report for a processed product**
    
    Returns all variants processed for a product with their status.
    
    **Example URL:**
    ```
    /api/product-report/https://www.amazon.com/product
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "product_url": "https://www.amazon.com/product",
        "data": {
            "product_url": "https://www.amazon.com/product",
            "total_variants": 5,
            "verified": 4,
            "flagged": 1,
            "uncertain": 0,
            "verification_rate": 80.0,
            "variants": [
                {
                    "metadata_color_label": "Navy Blue",
                    "predicted_family": "Blue",
                    "status": "VERIFIED ✅",
                    "confidence": 0.92
                },
                {
                    "metadata_color_label": "Red",
                    "predicted_family": "Pink",
                    "status": "FLAGGED ⚠️",
                    "confidence": 0.75
                }
            ]
        }
    }
    ```
    
    Args:
        product_url: The URL of the product to get report for
        
    Returns:
        ProductReportResponse: Complete audit report with all variants
        
    Raises:
        HTTPException: If product not found or retrieval fails
    """
    try:
        pipeline = get_pipeline()
        report = pipeline.get_product_report(product_url)
        
        if not report or not report.get('summary'):
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {product_url}"
            )
        
        logger.info(f"Retrieved report for product: {product_url}")
        
        return {
            "status": "success",
            "product_url": product_url,
            "data": report
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/results/flagged",
    response_model=ResultsResponse,
    summary="Get flagged results",
    description="Get all mismatched (flagged) audit results"
)
async def get_flagged_results(limit: int = 100):
    """
    🚨 **Get all flagged (mismatched) variants**
    
    Returns products where the metadata color DOES NOT match the CNN prediction.
    These require manual review.
    
    **Query Parameters:**
    - `limit`: Maximum results (default: 100, max: 10000)
    
    **Example URL:**
    ```
    /api/results/flagged?limit=50
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "count": 3,
        "data": [
            {
                "product_url": "https://www.amazon.com/product1",
                "metadata_color_label": "Red",
                "predicted_family": "Pink",
                "status": "FLAGGED ⚠️",
                "cnn_confidence": 0.78,
                "reason": "Color mismatch detected"
            },
            {
                "product_url": "https://www.amazon.com/product2",
                "metadata_color_label": "Blue",
                "predicted_family": "Purple",
                "status": "FLAGGED ⚠️",
                "cnn_confidence": 0.82,
                "reason": "Color mismatch detected"
            }
        ]
    }
    ```
    
    **Action Items:**
    🔴 Review each flagged result
    🔴 Check if product image is correct or metadata is wrong
    🔴 Update product listing accordingly
    
    Args:
        limit: Maximum number of results to return (default: 100)
        
    Returns:
        ResultsResponse: List of flagged results
        
    Raises:
        HTTPException: If query fails
    """
    try:
        db = get_database()
        results = db.query_flagged_results(limit=limit)
        
        logger.info(f"Retrieved {len(results)} flagged results")
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting flagged results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/results/verified",
    response_model=ResultsResponse,
    summary="Get verified results",
    description="Get all correct (verified) audit results"
)
async def get_verified_results(limit: int = 100):
    """
    ✅ **Get all verified (correct) variants**
    
    Returns products where the metadata color MATCHES the CNN prediction.
    These are confirmed as correct and need no action.
    
    **Query Parameters:**
    - `limit`: Maximum results (default: 100, max: 10000)
    
    **Example URL:**
    ```
    /api/results/verified?limit=50
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "count": 47,
        "data": [
            {
                "product_url": "https://www.amazon.com/product1",
                "metadata_color_label": "Navy Blue",
                "predicted_family": "Blue",
                "status": "VERIFIED ✅",
                "cnn_confidence": 0.95,
                "variants_verified": 5
            },
            {
                "product_url": "https://www.amazon.com/product2",
                "metadata_color_label": "Red",
                "predicted_family": "Red",
                "status": "VERIFIED ✅",
                "cnn_confidence": 0.92,
                "variants_verified": 3
            }
        ]
    }
    ```
    
    **Interpretation:**
    🟢 All verified results are correct
    🟢 No action needed for these products
    🟢 Safe to publish to customers
    
    Args:
        limit: Maximum number of results to return (default: 100)
        
    Returns:
        ResultsResponse: List of verified results
        
    Raises:
        HTTPException: If query fails
    """
    try:
        db = get_database()
        results = db.query_audit_results(status="VERIFIED", limit=limit)
        
        logger.info(f"Retrieved {len(results)} verified results")
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting verified results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/results/uncertain",
    response_model=ResultsResponse,
    summary="Get uncertain results",
    description="Get all low-confidence (uncertain) audit results"
)
async def get_uncertain_results(limit: int = 100):
    """
    🟡 **Get all uncertain variants**
    
    Returns variants where confidence is too low to make a decision.
    These require manual verification by humans.
    
    **Query Parameters:**
    - `limit`: Maximum results (default: 100)
    
    **Example URL:**
    ```
    /api/results/uncertain?limit=50
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "count": 5,
        "data": [
            {
                "product_url": "https://www.amazon.com/product1",
                "metadata_color_label": "Teal",
                "predicted_family": "Blue",
                "status": "UNCERTAIN 🟡",
                "cnn_confidence": 0.52,
                "reason": "Low confidence - needs manual review"
            }
        ]
    }
    ```
    
    **Action Items:**
    🟡 Manually verify the color
    🟡 Check if it's a true mismatch or just difficult to classify
    🟡 Consider re-training model with more examples
    
    Args:
        limit: Maximum number of results to return (default: 100)
        
    Returns:
        ResultsResponse: List of uncertain results
        
    Raises:
        HTTPException: If query fails
    """
    try:
        db = get_database()
        results = db.query_audit_results(status="UNCERTAIN", limit=limit)
        
        logger.info(f"Retrieved {len(results)} uncertain results")
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting uncertain results: {e}")
        raise HTTPException(status_code=500, detail=str(e))
