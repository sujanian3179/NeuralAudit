"""
Model Training Script
Trains ResNet-18 CNN for color family classification
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Dataset
import torchvision.transforms as transforms
from pathlib import Path
from logger import logger
from model import ColorClassificationModel
from config import NUM_CLASSES, MODEL_CHECKPOINT, DEVICE


class ColorDataset(Dataset):
    """
    Custom dataset for color classification.
    Expects directory structure:
    data/
      - red/
      - blue/
      - green/
      ... etc
    """
    
    def __init__(self, root_dir: str, transform=None):
        """
        Initialize dataset.
        
        Args:
            root_dir: Root directory containing class folders
            transform: Image transformations
        """
        self.root_dir = Path(root_dir)
        self.transform = transform
        self.images = []
        self.labels = []
        self.class_to_idx = {}
        
        # Scan directories
        for idx, class_dir in enumerate(sorted(self.root_dir.iterdir())):
            if class_dir.is_dir():
                self.class_to_idx[class_dir.name] = idx
                for img_path in class_dir.glob("*.jpg"):
                    self.images.append(str(img_path))
                    self.labels.append(idx)
        
        logger.info(f"Loaded {len(self.images)} images from {root_dir}")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        from PIL import Image
        img_path = self.images[idx]
        label = self.labels[idx]
        
        image = Image.open(img_path).convert('RGB')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


class ModelTrainer:
    """
    Trainer class for color classification model.
    """
    
    def __init__(self, model=None, learning_rate=0.001, device=DEVICE):
        """
        Initialize trainer.
        
        Args:
            model: Model to train (if None, creates new ResNet-18)
            learning_rate: Learning rate for optimizer
            device: Device to train on
        """
        self.device = torch.device(device)
        self.model = model or ColorClassificationModel(num_classes=NUM_CLASSES)
        self.model.to(self.device)
        
        self.criterion = nn.CrossEntropyLoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=10, gamma=0.1)
        
        logger.info(f"Initialized trainer on device: {self.device}")
    
    def train_epoch(self, train_loader: DataLoader) -> float:
        """
        Train for one epoch.
        
        Args:
            train_loader: Training data loader
        
        Returns:
            Average training loss
        """
        self.model.train()
        total_loss = 0
        total_samples = 0
        
        for images, labels in train_loader:
            images = images.to(self.device)
            labels = labels.to(self.device)
            
            # Forward pass
            outputs = self.model(images)
            loss = self.criterion(outputs, labels)
            
            # Backward pass
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            
            total_loss += loss.item() * images.size(0)
            total_samples += images.size(0)
        
        avg_loss = total_loss / total_samples
        logger.info(f"Train loss: {avg_loss:.4f}")
        return avg_loss
    
    def validate(self, val_loader: DataLoader) -> tuple:
        """
        Validate model.
        
        Args:
            val_loader: Validation data loader
        
        Returns:
            Tuple of (accuracy, loss)
        """
        self.model.eval()
        correct = 0
        total = 0
        total_loss = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(self.device)
                labels = labels.to(self.device)
                
                outputs = self.model(images)
                loss = self.criterion(outputs, labels)
                
                _, predicted = torch.max(outputs.data, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
                total_loss += loss.item() * images.size(0)
        
        accuracy = correct / total
        avg_loss = total_loss / total
        
        logger.info(f"Validation accuracy: {accuracy:.4f}, loss: {avg_loss:.4f}")
        return accuracy, avg_loss
    
    def train(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader = None,
        epochs: int = 50,
        early_stopping_patience: int = 10
    ):
        """
        Full training loop.
        
        Args:
            train_loader: Training data loader
            val_loader: Validation data loader (optional)
            epochs: Number of training epochs
            early_stopping_patience: Epochs to wait for improvement
        """
        best_accuracy = 0
        patience_counter = 0
        
        for epoch in range(1, epochs + 1):
            logger.info(f"Epoch {epoch}/{epochs}")
            
            # Train
            train_loss = self.train_epoch(train_loader)
            
            # Validate
            if val_loader:
                val_accuracy, val_loss = self.validate(val_loader)
                
                # Early stopping
                if val_accuracy > best_accuracy:
                    best_accuracy = val_accuracy
                    patience_counter = 0
                    self.save_model()
                else:
                    patience_counter += 1
                    if patience_counter >= early_stopping_patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break
            
            # Update learning rate
            self.scheduler.step()
        
        logger.info("Training completed")
    
    def save_model(self, path: str = MODEL_CHECKPOINT):
        """
        Save model checkpoint.
        
        Args:
            path: Path to save model
        """
        import os
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'num_classes': NUM_CLASSES,
        }, path)
        
        logger.info(f"Model saved to {path}")


def create_data_loaders(
    data_dir: str,
    train_split: float = 0.8,
    batch_size: int = 32,
    num_workers: int = 4
):
    """
    Create training and validation data loaders.
    
    Args:
        data_dir: Root directory with class subdirectories
        train_split: Fraction of data for training
        batch_size: Batch size
        num_workers: Number of data loading workers
    
    Returns:
        Tuple of (train_loader, val_loader)
    """
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        ),
    ])
    
    # Load full dataset
    dataset = ColorDataset(data_dir, transform=transform)
    
    # Split into train/val
    train_size = int(len(dataset) * train_split)
    val_size = len(dataset) - train_size
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset,
        [train_size, val_size]
    )
    
    # Create data loaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers
    )
    
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers
    ) if val_size > 0 else None
    
    logger.info(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    return train_loader, val_loader


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Train color classification model")
    parser.add_argument("--data-dir", type=str, required=True, help="Directory with color class subdirectories")
    parser.add_argument("--epochs", type=int, default=50, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.001, help="Learning rate")
    parser.add_argument("--output", type=str, default=MODEL_CHECKPOINT, help="Output model path")
    parser.add_argument("--gpu", action="store_true", help="Use GPU if available")
    
    args = parser.parse_args()
    
    # Determine device
    device = "cuda" if (args.gpu and torch.cuda.is_available()) else "cpu"
    logger.info(f"Using device: {device}")
    
    # Create data loaders
    train_loader, val_loader = create_data_loaders(
        args.data_dir,
        batch_size=args.batch_size
    )
    
    # Initialize trainer
    model = ColorClassificationModel(num_classes=NUM_CLASSES)
    trainer = ModelTrainer(model=model, learning_rate=args.lr, device=device)
    
    # Train
    trainer.train(
        train_loader=train_loader,
        val_loader=val_loader,
        epochs=args.epochs
    )
    
    # Save model
    trainer.save_model(args.output)
    logger.info(f"Model saved to {args.output}")
