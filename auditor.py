"""
Audit Engine Module
Performs family mapping and verification logic
"""
from typing import Tuple, List, Dict, Optional
from logger import logger
from config import COLOR_LABEL_TO_FAMILY, CONFIDENCE_THRESHOLD, COLOR_FAMILIES


class AuditResult:
    """
    Represents the result of auditing a single product variant.
    """
    
    def __init__(
        self,
        product_url: str,
        variant_image_url: str,
        metadata_color_label: str,
        cnn_predicted_class: int,
        cnn_confidence: float,
        heuristic_valid: bool = True,
        heuristic_confidence: float = 0.0
    ):
        """
        Initialize audit result.
        
        Args:
            product_url: Source product URL
            variant_image_url: URL of variant image
            metadata_color_label: Color label from metadata
            cnn_predicted_class: CNN predicted class ID
            cnn_confidence: CNN prediction confidence
            heuristic_valid: Heuristic check result
            heuristic_confidence: Heuristic confidence
        """
        self.product_url = product_url
        self.variant_image_url = variant_image_url
        self.metadata_color_label = metadata_color_label
        self.cnn_predicted_class = cnn_predicted_class
        self.cnn_confidence = cnn_confidence
        self.heuristic_valid = heuristic_valid
        self.heuristic_confidence = heuristic_confidence
        
        # Normalize metadata label
        self.metadata_family = self._normalize_metadata_label(metadata_color_label)
        self.predicted_family = COLOR_FAMILIES.get(cnn_predicted_class, "Unknown")
        
        # Determine status
        self.status = self._determine_status()
        self.confidence_score = self._calculate_confidence()
    
    def _normalize_metadata_label(self, label: str) -> str:
        """
        Normalize metadata color label to family.
        
        Args:
            label: Raw metadata label
        
        Returns:
            Normalized family name
        """
        try:
            normalized = label.lower().strip()
            
            # Direct lookup
            if normalized in COLOR_LABEL_TO_FAMILY:
                return COLOR_LABEL_TO_FAMILY[normalized]
            
            # Partial matching
            for key, family in COLOR_LABEL_TO_FAMILY.items():
                if key in normalized or normalized in key:
                    return family
            
            # Not found, return original for manual review
            logger.warning(f"Color label not found in mapping: {label}")
            return label
        except Exception as e:
            logger.error(f"Error normalizing label '{label}': {e}")
            return label
    
    def _determine_status(self) -> str:
        """
        Determine if variant is verified or flagged.
        
        Returns:
            Status: "VERIFIED", "FLAGGED", or "UNCERTAIN"
        """
        # Check if metadata family matches CNN prediction
        if self.metadata_family == self.predicted_family:
            if self.cnn_confidence >= CONFIDENCE_THRESHOLD:
                return "VERIFIED"
            else:
                return "UNCERTAIN"
        else:
            return "FLAGGED"
    
    def _calculate_confidence(self) -> float:
        """
        Calculate overall confidence score.
        
        Returns:
            Confidence score between -1 and 1
        """
        # Base confidence from CNN
        confidence = self.cnn_confidence - CONFIDENCE_THRESHOLD
        
        # Boost if heuristic also validates
        if self.heuristic_valid:
            confidence += 0.1
        else:
            confidence -= 0.1
        
        return max(-1.0, min(1.0, confidence))
    
    def to_dict(self) -> dict:
        """
        Convert result to dictionary for storage/API response.
        
        Returns:
            Dictionary representation
        """
        return {
            "product_url": self.product_url,
            "variant_image_url": self.variant_image_url,
            "metadata_color_label": self.metadata_color_label,
            "metadata_family": self.metadata_family,
            "cnn_predicted_class": self.cnn_predicted_class,
            "predicted_family": self.predicted_family,
            "cnn_confidence": round(self.cnn_confidence, 4),
            "heuristic_valid": self.heuristic_valid,
            "heuristic_confidence": round(self.heuristic_confidence, 4),
            "status": self.status,
            "overall_confidence": round(self.confidence_score, 4),
        }
    
    def __repr__(self) -> str:
        """String representation of audit result."""
        return (
            f"AuditResult("
            f"status={self.status}, "
            f"metadata={self.metadata_family}, "
            f"predicted={self.predicted_family}, "
            f"confidence={self.confidence_score:.3f}"
            f")"
        )


class AuditEngine:
    """
    Main audit engine that orchestrates the verification process.
    """
    
    @staticmethod
    def audit_variant(
        product_url: str,
        variant_image_url: str,
        metadata_color_label: str,
        cnn_predicted_class: int,
        cnn_confidence: float,
        heuristic_valid: bool = True,
        heuristic_confidence: float = 0.0
    ) -> AuditResult:
        """
        Audit a single product variant.
        
        Args:
            product_url: Product page URL
            variant_image_url: Variant image URL
            metadata_color_label: Color label from metadata
            cnn_predicted_class: CNN predicted class ID
            cnn_confidence: CNN confidence score
            heuristic_valid: Result of heuristic validation
            heuristic_confidence: Heuristic confidence score
        
        Returns:
            AuditResult object
        """
        try:
            result = AuditResult(
                product_url=product_url,
                variant_image_url=variant_image_url,
                metadata_color_label=metadata_color_label,
                cnn_predicted_class=cnn_predicted_class,
                cnn_confidence=cnn_confidence,
                heuristic_valid=heuristic_valid,
                heuristic_confidence=heuristic_confidence
            )
            
            logger.info(f"Audited variant: {result}")
            return result
        except Exception as e:
            logger.error(f"Error auditing variant: {e}")
            raise
    
    @staticmethod
    def audit_batch(
        audit_data: List[Dict]
    ) -> List[AuditResult]:
        """
        Audit multiple variants.
        
        Args:
            audit_data: List of audit dictionaries with keys:
                - product_url
                - variant_image_url
                - metadata_color_label
                - cnn_predicted_class
                - cnn_confidence
                - heuristic_valid (optional)
                - heuristic_confidence (optional)
        
        Returns:
            List of AuditResult objects
        """
        results = []
        
        for item in audit_data:
            try:
                result = AuditEngine.audit_variant(
                    product_url=item.get("product_url"),
                    variant_image_url=item.get("variant_image_url"),
                    metadata_color_label=item.get("metadata_color_label"),
                    cnn_predicted_class=item.get("cnn_predicted_class"),
                    cnn_confidence=item.get("cnn_confidence"),
                    heuristic_valid=item.get("heuristic_valid", True),
                    heuristic_confidence=item.get("heuristic_confidence", 0.0)
                )
                results.append(result)
            except Exception as e:
                logger.error(f"Error auditing item {item}: {e}")
                continue
        
        logger.info(f"Audited {len(results)} variants")
        return results
    
    @staticmethod
    def generate_report(audit_results: List[AuditResult]) -> Dict:
        """
        Generate summary report from audit results.
        
        Args:
            audit_results: List of AuditResult objects
        
        Returns:
            Report dictionary with statistics
        """
        try:
            total = len(audit_results)
            if total == 0:
                return {
                    "total_variants": 0,
                    "verified": 0,
                    "flagged": 0,
                    "uncertain": 0,
                    "verification_rate": 0.0,
                    "flag_rate": 0.0,
                }
            
            verified = sum(1 for r in audit_results if r.status == "VERIFIED")
            flagged = sum(1 for r in audit_results if r.status == "FLAGGED")
            uncertain = sum(1 for r in audit_results if r.status == "UNCERTAIN")
            
            avg_confidence = sum(r.confidence_score for r in audit_results) / total
            avg_cnn_confidence = sum(r.cnn_confidence for r in audit_results) / total
            
            report = {
                "total_variants": total,
                "verified": verified,
                "flagged": flagged,
                "uncertain": uncertain,
                "verification_rate": round(verified / total, 4),
                "flag_rate": round(flagged / total, 4),
                "uncertain_rate": round(uncertain / total, 4),
                "avg_confidence": round(avg_confidence, 4),
                "avg_cnn_confidence": round(avg_cnn_confidence, 4),
                "flagged_variants": [r.to_dict() for r in audit_results if r.status == "FLAGGED"]
            }
            
            logger.info(f"Generated report: {verified}/{total} verified, {flagged} flagged")
            return report
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            raise


class ColorFamilyMatcher:
    """
    Utility class for color family matching operations.
    """
    
    @staticmethod
    def get_family_for_label(label: str) -> str:
        """
        Get color family for a metadata label.
        
        Args:
            label: Metadata color label
        
        Returns:
            Color family name
        """
        normalized = label.lower().strip()
        return COLOR_LABEL_TO_FAMILY.get(normalized, label)
    
    @staticmethod
    def get_possible_families(label: str) -> List[str]:
        """
        Get all possible color families that might match a label.
        
        Args:
            label: Metadata color label
        
        Returns:
            List of possible color families
        """
        normalized = label.lower().strip()
        possible = set()
        
        # Direct match
        if normalized in COLOR_LABEL_TO_FAMILY:
            possible.add(COLOR_LABEL_TO_FAMILY[normalized])
        
        # Partial matches
        for key, family in COLOR_LABEL_TO_FAMILY.items():
            if key in normalized or normalized in key:
                possible.add(family)
        
        return list(possible) if possible else [label]
    
    @staticmethod
    def similarity_score(label1: str, label2: str) -> float:
        """
        Calculate similarity between two color labels.
        
        Args:
            label1: First color label
            label2: Second color label
        
        Returns:
            Similarity score between 0 and 1
        """
        family1 = ColorFamilyMatcher.get_family_for_label(label1)
        family2 = ColorFamilyMatcher.get_family_for_label(label2)
        
        if family1.lower() == family2.lower():
            return 1.0
        
        # Check for overlapping characters
        set1 = set(family1.lower())
        set2 = set(family2.lower())
        if set1 and set2:
            overlap = len(set1 & set2) / max(len(set1), len(set2))
            return overlap
        
        return 0.0


if __name__ == "__main__":
    # Example usage
    result = AuditEngine.audit_variant(
        product_url="https://example.com/product1",
        variant_image_url="https://example.com/image1.jpg",
        metadata_color_label="Royal Blue",
        cnn_predicted_class=1,  # Blue class
        cnn_confidence=0.92,
        heuristic_valid=True,
        heuristic_confidence=0.85
    )
    
    print(result)
    print(result.to_dict())
