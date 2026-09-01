import torch
import torch.nn as nn
from sklearn.ensemble import RandomForestRegressor
from sklearn.multioutput import MultiOutputRegressor

class BaselineModel:
    def __init__(self, n_estimators=50, max_depth=10, random_state=42):
        """
        Random Forest for baseline. We use MultiOutputRegressor since 
        we are predicting both Velocity and Yaw Rate.
        """
        rf = RandomForestRegressor(
            n_estimators=n_estimators, 
            max_depth=max_depth, 
            random_state=random_state,
            n_jobs=-1
        )
        self.model = MultiOutputRegressor(rf)
        
    def fit(self, X_train, y_train):
        self.model.fit(X_train, y_train)
        
    def predict(self, X):
        return self.model.predict(X)

class DeepIDRModel(nn.Module):
    def __init__(self, num_features=3, window_size=10, hidden_dim=32, num_outputs=2):
        """
        A lightweight 1D-CNN for processing IMU windows.
        Input shape: (Batch, window_size, num_features)
        """
        super(DeepIDRModel, self).__init__()
        
        # PyTorch Conv1d expects (Batch, Channels, Length), so we will transpose in forward
        self.conv1 = nn.Conv1d(in_channels=num_features, out_channels=hidden_dim, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.pool = nn.MaxPool1d(kernel_size=2)
        
        self.conv2 = nn.Conv1d(in_channels=hidden_dim, out_channels=hidden_dim * 2, kernel_size=3, padding=1)
        
        # Calculate flattened dimension
        self.flat_dim = (hidden_dim * 2) * (window_size // 2 // 2) 
        
        self.fc1 = nn.Linear(self.flat_dim, 32)
        self.fc2 = nn.Linear(32, num_outputs)
        
    def forward(self, x):
        # x is (B, window_size, num_features) -> we want (B, num_features, window_size) for Conv1D
        x = x.transpose(1, 2)
        
        x = self.conv1(x)
        x = self.relu(x)
        x = self.pool(x)
        
        x = self.conv2(x)
        x = self.relu(x)
        x = self.pool(x) # (B, 64, window_size // 4)
        
        x = x.reshape(x.size(0), -1)
        
        x = self.fc1(x)
        x = self.relu(x)
        x = self.fc2(x)
        
        return x
