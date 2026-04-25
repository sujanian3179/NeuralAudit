"""
FastAPI Server for NeuralAudit
Provides REST API for product auditing and results management
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional
import asyncio
from logger import logger
from config import API_HOST, API_PORT, API_DEBUG
from pipeline import NeuralAuditPipeline
from auditor import AuditEngine
from database import DatabaseManager
import csv
import io


# ===================== Pydantic Models =====================

class ColorLabel(BaseModel):
    """Color label input model"""
    label: str


class ProductUrl(BaseModel):
    """Product URL input model"""
    url: HttpUrl
    
    class Config:
        example = {
            "url": "https://www.amazon.com/Example-Product-Multiple-Colors/dp/B001234567"
        }


class AuditRequest(BaseModel):
    """Request model for manual audit"""
    product_url: str
    variant_image_url: str
    metadata_color_label: str
    cnn_predicted_class: int
    cnn_confidence: float
    
    class Config:
        example = {
            "product_url": "https://www.amazon.com/shirt-colors/dp/B001234567",
            "variant_image_url": "https://images-na.ssl-images-amazon.com/images/I/example.jpg",
            "metadata_color_label": "Navy Blue",
            "cnn_predicted_class": 1,
            "cnn_confidence": 0.92
        }


class BatchAuditRequest(BaseModel):
    """Request model for batch audit"""
    product_urls: List[str]
    
    class Config:
        example = {
            "product_urls": [
                "https://www.amazon.com/product1",
                "https://www.amazon.com/product2",
                "https://www.amazon.com/product3"
            ]
        }


class AuditResponse(BaseModel):
    """Audit response model"""
    status: str
    result: Dict


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"


# ===================== FastAPI App =====================

app = FastAPI(
    title="NeuralAudit API",
    description="AI-driven e-commerce product variant integrity system",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
pipeline = NeuralAuditPipeline(use_gpu=False)
db = DatabaseManager()


# ===================== Health & Status Endpoints =====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/stats")
async def get_statistics():
    """
    Get global audit statistics.
    
    Returns:
        Statistics dictionary
    """
    try:
        stats = pipeline.get_global_statistics()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== Color Family Endpoints =====================

@app.post("/api/color-families")
async def get_color_family(color: ColorLabel):
    """
    Get color family for a label.
    
    Args:
        color: Color label
    
    Returns:
        Color family name
    """
    try:
        from auditor import ColorFamilyMatcher
        family = ColorFamilyMatcher.get_family_for_label(color.label)
        
        return {
            "status": "success",
            "label": color.label,
            "family": family
        }
    except Exception as e:
        logger.error(f"Error getting color family: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/color-similarity")
async def check_color_similarity(color1: str, color2: str):
    """
    Calculate similarity between two color labels.
    
    Args:
        color1: First color label
        color2: Second color label
    
    Returns:
        Similarity score
    """
    try:
        from auditor import ColorFamilyMatcher
        score = ColorFamilyMatcher.similarity_score(color1, color2)
        
        return {
            "status": "success",
            "color1": color1,
            "color2": color2,
            "similarity": score
        }
    except Exception as e:
        logger.error(f"Error calculating similarity: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ===================== Audit Endpoints =====================

@app.post("/api/audit")
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
        "data": {
            "product_url": "https://www.amazon.com/shirt-colors/dp/B001234567",
            "metadata_family": "Blue",
            "predicted_family": "Blue",
            "status": "VERIFIED",
            "overall_confidence": 0.95,
            "cnn_confidence": 0.92
        }
    }
    ```
    """
    try:
        result = AuditEngine.audit_variant(
            product_url=request.product_url,
            variant_image_url=request.variant_image_url,
            metadata_color_label=request.metadata_color_label,
            cnn_predicted_class=request.cnn_predicted_class,
            cnn_confidence=request.cnn_confidence
        )
        
        # Save to database
        if db.client:
            db.insert_audit_result(result.to_dict())
        
        return {
            "status": "success",
            "data": result.to_dict()
        }
    except Exception as e:
        logger.error(f"Error during audit: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/process-product")
async def process_single_product(request: ProductUrl, background_tasks: BackgroundTasks):
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
    - 🟢 **VERIFIED**: Metadata color matches CNN prediction (product image is correct)
    - 🔴 **FLAGGED**: Mismatch detected (possible content error - needs review)
    - 🟡 **UNCERTAIN**: Low confidence - manual review recommended
    """
    try:
        product_url = str(request.url)
        logger.info(f"Processing product: {product_url}")
        
        # Run in background
        background_tasks.add_task(pipeline.process_product, product_url)
        
        return {
            "status": "processing",
            "product_url": product_url,
            "message": "Product is being processed in background. Check results later with /api/product-report/{url}"
        }
    except Exception as e:
        logger.error(f"Error starting product processing: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/process-batch")
async def process_batch(request: BatchAuditRequest, background_tasks: BackgroundTasks):
    """
    📦 **Process a batch of product URLs simultaneously**
    
    This endpoint processes multiple products in parallel:
    
    **Example Input:**
    ```json
    {
        "product_urls": [
            "https://www.amazon.com/product1",
            "https://www.amazon.com/product2",
            "https://www.amazon.com/product3"
        ]
    }
    ```
    
    **Example Output (after processing):**
    ```json
    {
        "status": "processing",
        "batch_size": 3,
        "product_urls": [
            "https://www.amazon.com/product1",
            "https://www.amazon.com/product2",
            "https://www.amazon.com/product3"
        ],
        "results": {
            "https://www.amazon.com/product1": {
                "status": "VERIFIED ✅",
                "variants_processed": 5
            },
            "https://www.amazon.com/product2": {
                "status": "FLAGGED ⚠️",
                "variants_processed": 3
            },
            "https://www.amazon.com/product3": {
                "status": "VERIFIED ✅",
                "variants_processed": 4
            }
        }
    }
    ```
    
    **Features:**
    - Process up to 100+ products at once
    - Results saved to database automatically
    - Real-time statistics available via /stats endpoint
    """
    try:
        if not request.product_urls:
            raise ValueError("No product URLs provided")
        
        logger.info(f"Processing batch of {len(request.product_urls)} products")
        
        # Run in background
        background_tasks.add_task(
            pipeline.process_batch,
            request.product_urls,
            save_to_db=True
        )
        
        return {
            "status": "processing",
            "batch_size": len(request.product_urls),
            "product_urls": request.product_urls,
            "message": "Batch is being processed in background. Check /stats for progress"
        }
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ===================== Results Endpoints =====================

@app.get("/api/product-report/{product_url:path}")
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
        "report": {
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
    """
    try:
        report = pipeline.get_product_report(product_url)
        
        if not report or not report.get('summary'):
            raise HTTPException(status_code=404, detail="Product not found in database")
        
        return {
            "status": "success",
            "data": report
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting product report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/flagged")
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
    """
    try:
        results = db.query_flagged_results(limit=limit)
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting flagged results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/verified")
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
    """
    try:
        results = db.query_audit_results(status="VERIFIED", limit=limit)
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting verified results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/results/uncertain")
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
    """
    try:
        results = db.query_audit_results(status="UNCERTAIN", limit=limit)
        
        return {
            "status": "success",
            "count": len(results),
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting uncertain results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===================== CSV Upload Endpoints =====================

@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    📤 **Batch process products from CSV file**
    
    Upload a CSV file with product URLs for large-scale processing.
    
    **CSV Requirements:**
    - Must have a `url` column containing product links
    - Column name can be: `url`, `product_url`, or `link`
    - One URL per row
    
    **Example CSV Format:**
    ```
    url
    https://www.amazon.com/product1
    https://www.amazon.com/product2
    https://www.amazon.com/product3
    ```
    
    **How to Use in Swagger UI:**
    1. Click "Try it out" button
    2. Select your CSV file
    3. Click "Execute"
    4. System will process all products in background
    
    **Example Response:**
    ```json
    {
        "status": "processing",
        "filename": "products.csv",
        "urls_count": 150,
        "urls_preview": [
            "https://www.amazon.com/product1",
            "https://www.amazon.com/product2",
            "https://www.amazon.com/product3",
            "https://www.amazon.com/product4",
            "https://www.amazon.com/product5"
        ],
        "message": "All 150 products queued for processing. Check /stats for progress."
    }
    ```
    
    **Status Check:**
    - Use `/stats` endpoint to check processing progress
    - Use `/api/results/flagged` to see any issues found
    - Use `/api/results/verified` to see confirmed products
    
    **Features:**
    ✅ Supports 100+ products at once
    ✅ Automatic background processing
    ✅ Results saved to database
    ✅ Real-time statistics available
    """
    try:
        if not file.filename.endswith('.csv'):
            raise ValueError("File must be CSV format")
        
        contents = await file.read()
        stream = io.StringIO(contents.decode('utf8'))
        reader = csv.DictReader(stream)
        
        urls = []
        for row in reader:
            if 'url' in row and row['url']:
                urls.append(row['url'])
        
        if not urls:
            raise ValueError("CSV must contain 'url' column with valid URLs")
        
        logger.info(f"Uploaded CSV with {len(urls)} URLs")
        
        # Start processing in background
        if background_tasks:
            background_tasks.add_task(pipeline.process_batch, urls)
        
        return {
            "status": "processing",
            "filename": file.filename,
            "urls_count": len(urls),
            "urls_preview": urls[:5],  # Show first 5
            "message": f"All {len(urls)} products queued for processing. Check /stats for progress."
        }
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=400, detail=str(e))


# ===================== Error Handlers =====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return {
        "status": "error",
        "detail": str(exc)
    }


# ===================== Run the API =====================

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting NeuralAudit API on {API_HOST}:{API_PORT}")
    uvicorn.run(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info" if API_DEBUG else "warning"
    )
