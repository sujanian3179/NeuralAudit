"""
Health and statistics related schemas
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str = "1.0.0"
    timestamp: Optional[str] = None


class StatsResponse(BaseModel):
    """Statistics response"""
    status: str
    data: Dict[str, Any]
