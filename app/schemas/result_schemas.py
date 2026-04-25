"""
Results and reports related schemas
"""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional


class ResultsResponse(BaseModel):
    """General results response"""
    status: str
    count: int
    data: List[Dict[str, Any]]


class ProductReportResponse(BaseModel):
    """Product audit report response"""
    status: str
    product_url: str
    data: Dict[str, Any]
