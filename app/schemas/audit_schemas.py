"""
Audit-related request/response schemas
"""
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Optional


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


class VariantResult(BaseModel):
    """Single variant audit result"""
    metadata_color_label: str
    predicted_family: str
    status: str
    cnn_confidence: float
    overall_confidence: float


class ProductReportSummary(BaseModel):
    """Product report summary statistics"""
    total_variants: int
    verified_count: int
    flagged_count: int
    uncertain_count: int
    verification_rate: float
