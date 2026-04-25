"""
Deep Learning Model Module
ResNet-18 based CNN for color family classification

KEY COMPONENTS:
1. ColorClassificationModel: Transfer learning architecture
   - Pre-trained ResNet-18 backbone (from ImageNet)
   - Custom classification head (for 10 color families)
   - Handles feature extraction + color classification
   
2. ModelInference: Inference engine wrapper
   - Loads model from checkpoint or initializes fresh
   - Provides predict(), predict_batch() methods
   - Handles GPU/CPU device management
   - Manages model state and checkpoint saving
"""
import torch  # Deep learning framework
import torch.nn as nn  # Neural network modules
import torch.nn.functional as F  # Activation functions
import torchvision.models as models  # Pre-trained models (ResNet, VGG, etc.)
from typing import Tuple  # Type hints
import os  # Operating system operations
from logger import logger  # Custom logging
from config import MODEL_NAME, NUM_CLASSES, MODEL_CHECKPOINT, DEVICE  # Config variables


class ColorClassificationModel(nn.Module):
    """
    ResNet-18 based model for color family classification.
    
    Architecture:
    - Backbone: ResNet-18 (pre-trained on ImageNet)
      * Extracts visual features from image
      * 18 layers of convolutions + residual connections
      * Output: 512-dimensional feature vector
    
    - Classification Head: Custom FC layers
      * Takes 512-dim features from backbone
      * 512 → 256 (ReLU activation)
      * Dropout (0.5) for regularization
      * 256 → 10 (output logits for 10 color classes)
    
    Transfer Learning:
    - Backbone weights frozen (trained on ImageNet)
    - Only FC head trained on color images
    - Requires ~1000 color images vs 100,000+ from scratch
    """
    
    def __init__(self, num_classes: int = NUM_CLASSES):
        """
        Initialize model.
        
        Args:
            num_classes: Number of color classes (default 10)
                        Red, Blue, Green, Yellow, Orange, Purple, Pink, Gray, Black, White
        """
        # Call parent class constructor
        super(ColorClassificationModel, self).__init__()
        
        # Handle SSL certificate issues (for downloading pre-trained weights)
        import ssl
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Load pre-trained ResNet-18 from PyTorch model zoo
        # weights=ResNet18_Weights.DEFAULT uses ImageNet pre-trained weights
        # This gives us 512-dim feature extraction for free!
        self.backbone = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        
        # Get number of input features to final FC layer (512 for ResNet-18)
        in_features = self.backbone.fc.in_features  # 512
        
        # REPLACE the original classification layer (1000 ImageNet classes)
        # with our custom head for 10 color families
        # Architecture: 512 → 256 → 10
        self.backbone.fc = nn.Sequential(
            # First fully connected layer: 512 dimensions → 256 dimensions
            nn.Linear(in_features, 256),  # Reduces dimensionality
            # ReLU activation: Introduces non-linearity (essential for learning)
            # inplace=True means modify tensor in-place (saves memory)
            nn.ReLU(inplace=True),
            # Dropout regularization: Randomly zeros 50% of activations during training
            # Prevents overfitting when training data is limited (~1000 images)
            nn.Dropout(0.5),
            # Final fully connected layer: 256 dimensions → 10 output logits
            # Each output corresponds to probability of one color class
            nn.Linear(256, num_classes)
        )
        
        logger.info(f"Initialized ColorClassificationModel with {num_classes} classes")
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the model.
        
        Process:
        1. Input image (224x224x3)
        2. ResNet backbone extracts 512-dim features
        3. Custom FC head maps 512 dims → 256 dims (with ReLU + Dropout)
        4. Output layer maps 256 dims → 10 logits (one per color class)
        5. Return logits (NOT probabilities - done with softmax in inference)
        
        Args:
            x: Input tensor of shape (batch_size, 3, 224, 224)
               Where: batch_size = number of images
                      3 = RGB channels
                      224x224 = image resolution (ResNet-18 standard input)
        
        Returns:
            Logits tensor of shape (batch_size, num_classes=10)
            Each value represents raw score for that color class
            Higher logit = model thinks this color is more likely
        """
        # Pass image through backbone (ResNet-18)
        # This includes: convolutions, residual connections, pooling
        # Output: (batch_size, 512) feature tensor
        return self.backbone(x)


class ModelInference:
    """
    Handles model inference, prediction, and confidence scoring.
    """
    
    def __init__(self, model_path: str = MODEL_CHECKPOINT, device: str = DEVICE):
        """
        Initialize inference engine.
        
        Args:
            model_path: Path to saved model checkpoint
            device: Device to run inference on ('cpu' or 'cuda')
        """
        self.device = torch.device(device)
        self.model = None
        self.model_path = model_path
        
        try:
            self._load_model()
        except Exception as e:
            logger.warning(f"Model checkpoint not found. Using pre-trained model only: {e}")
            self._initialize_model()
    
    def _initialize_model(self):
        """Initialize a fresh model without loading checkpoint."""
        try:
            import ssl
            # Handle SSL certificate issues
            ssl._create_default_https_context = ssl._create_unverified_context
            
            self.model = ColorClassificationModel(num_classes=NUM_CLASSES)
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Initialized fresh model on device: {self.device}")
        except Exception as e:
            logger.error(f"Failed to initialize model: {e}")
            raise
    
    def _load_model(self):
        """Load model from checkpoint."""
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model checkpoint not found at {self.model_path}")
            
            self.model = ColorClassificationModel(num_classes=NUM_CLASSES)
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Handle different checkpoint formats
            if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
                self.model.load_state_dict(checkpoint['model_state_dict'])
            else:
                self.model.load_state_dict(checkpoint)
            
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"Loaded model from {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model from {self.model_path}: {e}")
            raise
    
    def save_model(self, save_path: str = MODEL_CHECKPOINT):
        """
        Save model checkpoint.
        
        Args:
            save_path: Path to save the model
        """
        try:
            os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
            torch.save({
                'model_state_dict': self.model.state_dict(),
                'num_classes': NUM_CLASSES,
            }, save_path)
            logger.info(f"Model saved to {save_path}")
        except Exception as e:
            logger.error(f"Error saving model: {e}")
    
    def predict(self, image_tensor: torch.Tensor) -> Tuple[int, float]:
        """
        Predict color class for a single image.
        
        Args:
            image_tensor: Image tensor of shape (3, 224, 224) or (1, 3, 224, 224)
        
        Returns:
            Tuple of (predicted_class, confidence_score)
        """
        try:
            # Ensure correct shape
            if image_tensor.ndim == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            
            with torch.no_grad():
                logits = self.model(image_tensor)
                probabilities = F.softmax(logits, dim=1)
                confidence, predicted_class = torch.max(probabilities, 1)
            
            predicted_class = predicted_class.item()
            confidence = confidence.item()
            
            logger.debug(f"Prediction: class={predicted_class}, confidence={confidence:.4f}")
            return predicted_class, confidence
        except Exception as e:
            logger.error(f"Error during prediction: {e}")
            raise
    
    def predict_batch(self, image_tensors: torch.Tensor) -> Tuple[list, list]:
        """
        Predict color classes for a batch of images.
        
        Args:
            image_tensors: Batch of image tensors of shape (batch_size, 3, 224, 224)
        
        Returns:
            Tuple of (predicted_classes_list, confidences_list)
        """
        try:
            image_tensors = image_tensors.to(self.device)
            
            with torch.no_grad():
                logits = self.model(image_tensors)
                probabilities = F.softmax(logits, dim=1)
                confidences, predicted_classes = torch.max(probabilities, 1)
            
            predicted_classes = predicted_classes.cpu().numpy().tolist()
            confidences = confidences.cpu().numpy().tolist()
            
            logger.debug(f"Batch prediction: {len(predicted_classes)} images")
            return predicted_classes, confidences
        except Exception as e:
            logger.error(f"Error during batch prediction: {e}")
            raise
    
    def predict_with_top_k(self, image_tensor: torch.Tensor, k: int = 3) -> list:
        """
        Get top-k predictions for an image.
        
        Args:
            image_tensor: Image tensor
            k: Number of top predictions to return
        
        Returns:
            List of tuples: [(class, confidence), ...]
        """
        try:
            if image_tensor.ndim == 3:
                image_tensor = image_tensor.unsqueeze(0)
            
            image_tensor = image_tensor.to(self.device)
            
            with torch.no_grad():
                logits = self.model(image_tensor)
                probabilities = F.softmax(logits, dim=1)
            
            top_k_probs, top_k_classes = torch.topk(probabilities[0], k)
            
            results = [
                (cls.item(), prob.item())
                for cls, prob in zip(top_k_classes, top_k_probs)
            ]
            
            logger.debug(f"Top-{k} predictions: {results}")
            return results
        except Exception as e:
            logger.error(f"Error getting top-k predictions: {e}")
            raise


# Utility functions
def tensor_from_numpy(image_array) -> torch.Tensor:
    """
    Convert numpy array to PyTorch tensor.
    Assumes image is in shape (H, W, 3) or (3, H, W) with values in [0, 1].
    
    Args:
        image_array: Numpy array of image
    
    Returns:
        PyTorch tensor in shape (3, 224, 224)
    """
    try:
        if isinstance(image_array, torch.Tensor):
            tensor = image_array
        else:
            tensor = torch.from_numpy(image_array)
        
        # Ensure float32
        tensor = tensor.float()
        
        # Handle channel ordering
        if tensor.ndim == 3:
            if tensor.shape[0] == 3:
                pass  # Already in (C, H, W)
            elif tensor.shape[2] == 3:
                tensor = tensor.permute(2, 0, 1)  # Convert (H, W, C) to (C, H, W)
        
        return tensor
    except Exception as e:
        logger.error(f"Error converting to tensor: {e}")
        raise


def get_color_family_name(class_id: int) -> str:
    """
    Get color family name from class ID.
    
    Args:
        class_id: Class ID from model prediction
    
    Returns:
        Color family name
    """
    from config import COLOR_FAMILIES
    return COLOR_FAMILIES.get(class_id, "Unknown")


if __name__ == "__main__":
    import numpy as np
    
    # Test model initialization
    inference = ModelInference()
    
    # Create dummy image tensor
    dummy_image = torch.randn(1, 3, 224, 224)
    
    # Test prediction
    class_id, confidence = inference.predict(dummy_image)
    color_name = get_color_family_name(class_id)
    
    print(f"Prediction: {color_name} (Class {class_id}, Confidence: {confidence:.4f})")
    
    # Test top-k prediction
    top_k = inference.predict_with_top_k(dummy_image, k=3)
    print("Top-3 predictions:")
    for class_id, prob in top_k:
        print(f"  {get_color_family_name(class_id)}: {prob:.4f}")
