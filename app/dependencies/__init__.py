"""
Dependency injection for routers
Provides shared instances of pipeline, database, etc.
"""
from pipeline import NeuralAuditPipeline
from database import DatabaseManager
from logger import logger

# Singleton instances
_pipeline: NeuralAuditPipeline = None
_db: DatabaseManager = None


def get_pipeline() -> NeuralAuditPipeline:
    """
    Get or create NeuralAuditPipeline instance
    Used for dependency injection in routers
    """
    global _pipeline
    if _pipeline is None:
        logger.info("Initializing NeuralAuditPipeline...")
        _pipeline = NeuralAuditPipeline(use_gpu=False)
    return _pipeline


def get_database() -> DatabaseManager:
    """
    Get or create DatabaseManager instance
    Used for dependency injection in routers
    """
    global _db
    if _db is None:
        logger.info("Initializing DatabaseManager...")
        _db = DatabaseManager()
    return _db


def cleanup():
    """Clean up resources"""
    global _pipeline, _db
    if _pipeline:
        logger.info("Cleaning up pipeline...")
        _pipeline = None
    if _db:
        logger.info("Cleaning up database...")
        _db = None
