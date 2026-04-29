"""
MobileNetV2 Model Architecture for ASL Recognition
Based on train_cnn.py from notebooks
"""

import torch
import torch.nn as nn
from torchvision import models


class MobileNetV2ASL(nn.Module):
    """
    MobileNetV2 with Transfer Learning for ASL Alphabet Recognition
    
    Architecture:
    - Pre-trained MobileNetV2 features (frozen first 10 layers)
    - Custom classifier: Dropout(0.3) -> Linear(1280, 256) -> ReLU -> Dropout(0.2) -> Linear(256, 29)
    - Input size: 224x224
    - Number of classes: 29 (A-Z + delete, nothing, space)
    """
    
    def __init__(self, num_classes=29):
        super().__init__()
        
        # Load pre-trained MobileNetV2
        self.model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        
        # Freeze early layers (first 10 feature layers)
        for param in self.model.features[:10].parameters():
            param.requires_grad = False
        
        # Replace classifier head
        num_features = self.model.classifier[1].in_features  # 1280
        self.model.classifier = nn.Sequential(
            nn.Dropout(0.3),
            nn.Linear(num_features, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        return self.model(x)


def create_mobilenetv2_model(num_classes=29):
    """
    Create and return MobileNetV2 model for ASL recognition
    
    Args:
        num_classes: Number of output classes (default 29)
    
    Returns:
        MobileNetV2ASL model
    """
    return MobileNetV2ASL(num_classes=num_classes)
