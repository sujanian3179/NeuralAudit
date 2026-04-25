"""
Batch processing endpoints router
Handles batch audits and CSV uploads
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, File, UploadFile
from fastapi.responses import JSONResponse
import csv
import io

from logger import logger
from app.schemas import BatchAuditRequest
from app.dependencies import get_pipeline

# Create router
router = APIRouter(
    prefix="/api",
    tags=["Batch Processing"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "/process-batch",
    summary="Process batch of product URLs",
    description="Process multiple products simultaneously"
)
async def process_batch(
    request: BatchAuditRequest,
    background_tasks: BackgroundTasks
):
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
        "message": "Batch is being processed in background. Check /stats for progress"
    }
    ```
    
    **Features:**
    - Process up to 100+ products at once
    - Results saved to database automatically
    - Real-time statistics available via /stats endpoint
    - Background task processing for non-blocking API
    
    Returns:
        JSONResponse: Processing status with batch size
        
    Raises:
        HTTPException: If no URLs provided or processing fails
    """
    try:
        if not request.product_urls:
            raise ValueError("No product URLs provided")
        
        pipeline = get_pipeline()
        logger.info(f"Starting batch processing of {len(request.product_urls)} products")
        
        # Run in background
        background_tasks.add_task(
            pipeline.process_batch,
            request.product_urls,
            save_to_db=True
        )
        
        return JSONResponse({
            "status": "processing",
            "batch_size": len(request.product_urls),
            "product_urls": request.product_urls,
            "message": "Batch is being processed in background. Check /stats for progress"
        })
    except Exception as e:
        logger.error(f"Error starting batch processing: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/upload-csv",
    summary="Batch process from CSV file",
    description="Upload CSV file with product URLs for batch processing"
)
async def upload_csv(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    📤 **Batch process products from CSV file**
    
    Upload a CSV file with product URLs for large-scale processing.
    
    **CSV Requirements:**
    - Must have a `url` column containing product links
    - Column name can be: `url`, `product_url`, or `link`
    - One URL per row
    - Supports 100+ products per file
    
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
    ✅ Automatic CSV validation
    
    Returns:
        JSONResponse: Upload status with preview and message
        
    Raises:
        HTTPException: If file format is invalid or no URLs found
    """
    try:
        if not file.filename.endswith('.csv'):
            raise ValueError("File must be CSV format")
        
        contents = await file.read()
        stream = io.StringIO(contents.decode('utf8'))
        reader = csv.DictReader(stream)
        
        # Extract URLs from CSV
        urls = []
        for row in reader:
            # Try multiple column names
            url = None
            for col_name in ['url', 'product_url', 'link', 'URL', 'PRODUCT_URL', 'LINK']:
                if col_name in row and row[col_name]:
                    url = row[col_name]
                    break
            
            if url:
                urls.append(url)
        
        if not urls:
            raise ValueError("CSV must contain valid URLs in 'url', 'product_url', or 'link' column")
        
        logger.info(f"CSV uploaded with {len(urls)} URLs from {file.filename}")
        
        # Start processing in background
        if background_tasks:
            pipeline = get_pipeline()
            background_tasks.add_task(pipeline.process_batch, urls)
        
        return JSONResponse({
            "status": "processing",
            "filename": file.filename,
            "urls_count": len(urls),
            "urls_preview": urls[:5],  # Show first 5
            "message": f"All {len(urls)} products queued for processing. Check /stats for progress."
        })
    except Exception as e:
        logger.error(f"Error uploading CSV: {e}")
        raise HTTPException(status_code=400, detail=str(e))
