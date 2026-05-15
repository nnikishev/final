"""
"""
import torch
import torch.nn as nn

class StateClassifier(nn.Module):
    """
    3D CNN для классификации состояния конвейера на основе временного окна кадров.
    Вход: тензор (batch, channels=3, time_depth, height=224, width=224)
    Выход: логиты для двух классов (BOARD=0, GAP=1)
    """
    def __init__(self, num_classes: int = 2):
        super().__init__()
        
        self.conv1 = nn.Sequential(
            nn.Conv3d(3, 32, kernel_size=3, padding=1),
            nn.BatchNorm3d(32),
            nn.ReLU(),
            nn.MaxPool3d((1, 2, 2))
        )
        
        self.conv2 = nn.Sequential(
            nn.Conv3d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm3d(64),
            nn.ReLU(),
            nn.MaxPool3d((2, 2, 2))
        )
        
        self.conv3 = nn.Sequential(
            nn.Conv3d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm3d(128),
            nn.ReLU(),
            nn.AdaptiveAvgPool3d((4, 4, 4))
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(128 * 4 * 4 * 4, 256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, num_classes)
        )
    
    def forward(self, x):
        x = self.conv1(x)
        x = self.conv2(x)
        x = self.conv3(x)
        x = x.view(x.size(0), -1)
        x = self.classifier(x)
        return x