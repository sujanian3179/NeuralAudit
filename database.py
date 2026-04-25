"""
Database Module
Handles Supabase PostgreSQL integration for audit trails
"""
from typing import List, Dict, Optional
from datetime import datetime
from logger import logger
from config import SUPABASE_URL, SUPABASE_KEY

try:
    from supabase import create_client, Client
except ImportError:
    logger.warning("Supabase not installed. Install with: pip install supabase")
    Client = None


class DatabaseManager:
    """
    Manages database operations with Supabase.
    """
    
    def __init__(self):
        """Initialize database connection."""
        self.client: Optional[Client] = None
        self._init_connection()
    
    def _init_connection(self):
        """Initialize Supabase connection."""
        try:
            if not SUPABASE_URL or not SUPABASE_KEY:
                logger.warning("Supabase credentials not configured. Database disabled.")
                return
            
            if Client is None:
                logger.warning("Supabase client not available")
                return
            
            self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
            logger.info("Connected to Supabase database")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
    
    def _ensure_connection(self) -> bool:
        """Check if database connection is available."""
        if self.client is None:
            logger.warning("Database connection not available")
            return False
        return True
    
    def insert_audit_result(self, result_dict: Dict) -> Optional[Dict]:
        """
        Insert audit result into database.
        
        Args:
            result_dict: Dictionary with audit result
        
        Returns:
            Database response or None
        """
        if not self._ensure_connection():
            return None
        
        try:
            # Add timestamp
            result_dict["created_at"] = datetime.utcnow().isoformat()
            
            response = self.client.table("audit_results").insert(result_dict).execute()
            logger.info(f"Inserted audit result: {result_dict['variant_image_url']}")
            return response.data
        except Exception as e:
            logger.error(f"Error inserting audit result: {e}")
            return None
    
    def insert_batch(self, results: List[Dict]) -> int:
        """
        Insert multiple audit results.
        
        Args:
            results: List of audit result dictionaries
        
        Returns:
            Number of successfully inserted records
        """
        if not self._ensure_connection():
            return 0
        
        inserted = 0
        for result in results:
            try:
                if self.insert_audit_result(result):
                    inserted += 1
            except Exception as e:
                logger.error(f"Error inserting result: {e}")
                continue
        
        logger.info(f"Inserted {inserted}/{len(results)} audit results")
        return inserted
    
    def query_audit_results(
        self,
        product_url: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Query audit results from database.
        
        Args:
            product_url: Filter by product URL
            status: Filter by status (VERIFIED, FLAGGED, UNCERTAIN)
            limit: Maximum number of results
        
        Returns:
            List of audit result dictionaries
        """
        if not self._ensure_connection():
            return []
        
        try:
            query = self.client.table("audit_results").select("*")
            
            if product_url:
                query = query.eq("product_url", product_url)
            
            if status:
                query = query.eq("status", status)
            
            response = query.limit(limit).execute()
            logger.info(f"Retrieved {len(response.data)} audit results")
            return response.data
        except Exception as e:
            logger.error(f"Error querying audit results: {e}")
            return []
    
    def query_flagged_results(self, limit: int = 100) -> List[Dict]:
        """
        Get all flagged results for review.
        
        Args:
            limit: Maximum number of results
        
        Returns:
            List of flagged audit results
        """
        return self.query_audit_results(status="FLAGGED", limit=limit)
    
    def get_product_summary(self, product_url: str) -> Dict:
        """
        Get summary statistics for a product.
        
        Args:
            product_url: Product URL
        
        Returns:
            Summary dictionary
        """
        if not self._ensure_connection():
            return {}
        
        try:
            results = self.query_audit_results(product_url=product_url)
            
            if not results:
                return {
                    "product_url": product_url,
                    "total_variants": 0,
                    "verified": 0,
                    "flagged": 0,
                    "uncertain": 0
                }
            
            verified = sum(1 for r in results if r.get("status") == "VERIFIED")
            flagged = sum(1 for r in results if r.get("status") == "FLAGGED")
            uncertain = sum(1 for r in results if r.get("status") == "UNCERTAIN")
            
            return {
                "product_url": product_url,
                "total_variants": len(results),
                "verified": verified,
                "flagged": flagged,
                "uncertain": uncertain,
                "verification_rate": round(verified / len(results), 4) if results else 0.0,
                "flag_rate": round(flagged / len(results), 4) if results else 0.0,
            }
        except Exception as e:
            logger.error(f"Error getting product summary: {e}")
            return {}
    
    def update_audit_result(self, result_id: int, updates: Dict) -> bool:
        """
        Update an audit result.
        
        Args:
            result_id: Result ID
            updates: Dictionary of updates
        
        Returns:
            True if successful
        """
        if not self._ensure_connection():
            return False
        
        try:
            response = self.client.table("audit_results").update(updates).eq("id", result_id).execute()
            logger.info(f"Updated audit result {result_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating audit result: {e}")
            return False
    
    def delete_audit_result(self, result_id: int) -> bool:
        """
        Delete an audit result.
        
        Args:
            result_id: Result ID
        
        Returns:
            True if successful
        """
        if not self._ensure_connection():
            return False
        
        try:
            self.client.table("audit_results").delete().eq("id", result_id).execute()
            logger.info(f"Deleted audit result {result_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting audit result: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get overall database statistics.
        
        Returns:
            Statistics dictionary
        """
        if not self._ensure_connection():
            return {}
        
        try:
            results = self.client.table("audit_results").select("*").execute()
            data = results.data
            
            if not data:
                return {
                    "total_audits": 0,
                    "verified": 0,
                    "flagged": 0,
                    "uncertain": 0,
                }
            
            verified = sum(1 for r in data if r.get("status") == "VERIFIED")
            flagged = sum(1 for r in data if r.get("status") == "FLAGGED")
            uncertain = sum(1 for r in data if r.get("status") == "UNCERTAIN")
            
            avg_confidence = sum(r.get("overall_confidence", 0) for r in data) / len(data)
            
            return {
                "total_audits": len(data),
                "verified": verified,
                "flagged": flagged,
                "uncertain": uncertain,
                "verification_rate": round(verified / len(data), 4),
                "flag_rate": round(flagged / len(data), 4),
                "avg_confidence": round(avg_confidence, 4),
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


class LocalDataStore:
    """
    Local file-based storage as fallback when Supabase is unavailable.
    """
    
    def __init__(self, filename: str = "audit_results.json"):
        """
        Initialize local store.
        
        Args:
            filename: JSON file to store results
        """
        self.filename = f"./data/{filename}"
        import os
        os.makedirs(os.path.dirname(self.filename), exist_ok=True)
    
    def save(self, results: List[Dict]):
        """
        Save results to local file.
        
        Args:
            results: List of audit results
        """
        try:
            import json
            with open(self.filename, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Saved {len(results)} results to {self.filename}")
        except Exception as e:
            logger.error(f"Error saving to local store: {e}")
    
    def load(self) -> List[Dict]:
        """
        Load results from local file.
        
        Returns:
            List of audit results
        """
        try:
            import json
            with open(self.filename, 'r') as f:
                results = json.load(f)
            logger.info(f"Loaded {len(results)} results from {self.filename}")
            return results
        except FileNotFoundError:
            logger.warning(f"Local store file not found: {self.filename}")
            return []
        except Exception as e:
            logger.error(f"Error loading from local store: {e}")
            return []


if __name__ == "__main__":
    # Example usage
    db = DatabaseManager()
    
    # Query results
    results = db.query_audit_results(limit=10)
    print(f"Retrieved {len(results)} results")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
