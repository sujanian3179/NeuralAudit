"""
Health and utility endpoints router
Handles health checks, statistics, and color utilities
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from logger import logger
from app.schemas import HealthResponse, ColorLabel
from app.dependencies import get_pipeline

# Create router
router = APIRouter(
    tags=["Health & Utility"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if API is running and healthy"
)
async def health_check():
    """
    🏥 **Health check endpoint**
    
    Returns:
        HealthResponse: Health status and version information
        
    Example:
        GET /health
        
        Response:
        ```json
        {
            "status": "healthy",
            "version": "1.0.0",
            "timestamp": "2024-04-25T10:30:45.123456"
        }
        ```
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/stats",
    summary="Get global statistics",
    description="Get statistics about processed products and audit results"
)
async def get_statistics():
    """
    📊 **Get global audit statistics**
    
    Returns system-wide statistics including:
    - Total products processed
    - Total variants audited
    - Verification rate
    - System performance metrics
    
    Returns:
        JSONResponse: Statistics dictionary
        
    Example:
        GET /stats
        
        Response:
        ```json
        {
            "status": "success",
            "data": {
                "total_products": 150,
                "total_variants": 450,
                "verified_count": 420,
                "flagged_count": 20,
                "uncertain_count": 10,
                "verification_rate": 93.3,
                "avg_confidence": 0.87
            }
        }
        ```
        
    Raises:
        HTTPException: If statistics cannot be retrieved
    """
    try:
        pipeline = get_pipeline()
        stats = pipeline.get_global_statistics()
        
        logger.info("Statistics retrieved successfully")
        
        return JSONResponse({
            "status": "success",
            "data": stats
        })
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/color-families",
    summary="Get color family mapping",
    description="Map a color label to its family"
)
async def get_color_family(color: ColorLabel):
    """
    🎨 **Get color family for a label**
    
    Maps a color label (e.g., "Navy Blue") to its color family (e.g., "Blue").
    
    This is useful for understanding how the system normalizes color labels.
    
    **Example Input:**
    ```json
    {
        "label": "Navy Blue"
    }
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "label": "Navy Blue",
        "family": "Blue"
    }
    ```
    
    Args:
        color: ColorLabel with the label to map
        
    Returns:
        JSONResponse: Mapped color family
        
    Raises:
        HTTPException: If label cannot be mapped
    """
    try:
        from auditor import ColorFamilyMatcher
        
        family = ColorFamilyMatcher.get_family_for_label(color.label)
        
        logger.info(f"Color mapping: {color.label} → {family}")
        
        return JSONResponse({
            "status": "success",
            "label": color.label,
            "family": family
        })
    except Exception as e:
        logger.error(f"Error getting color family: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/color-similarity",
    summary="Check color similarity",
    description="Calculate similarity between two color labels"
)
async def check_color_similarity(color1: str, color2: str):
    """
    🎯 **Calculate similarity between two color labels**
    
    Returns a similarity score (0-1) indicating how similar two colors are.
    
    This is useful for debugging color mapping logic.
    
    **Example URL:**
    ```
    /color-similarity?color1=Navy Blue&color2=Blue
    ```
    
    **Example Output:**
    ```json
    {
        "status": "success",
        "color1": "Navy Blue",
        "color2": "Blue",
        "similarity": 0.95
    }
    ```
    
    Args:
        color1: First color label
        color2: Second color label
        
    Returns:
        JSONResponse: Similarity score between colors
        
    Raises:
        HTTPException: If calculation fails
    """
    try:
        from auditor import ColorFamilyMatcher
        
        score = ColorFamilyMatcher.similarity_score(color1, color2)
        
        logger.info(f"Color similarity: {color1} vs {color2} = {score}")
        
        return JSONResponse({
            "status": "success",
            "color1": color1,
            "color2": color2,
            "similarity": score
        })
    except Exception as e:
        logger.error(f"Error calculating color similarity: {e}")
        raise HTTPException(status_code=400, detail=str(e))
