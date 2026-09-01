import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import json

class ModelTrainer:
    def __init__(self, checkpoint_dir: str = 'ml/models/checkpoints'):
        self.checkpoint_dir = checkpoint_dir
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
    def evaluate_metrics(self, y_true, y_pred, model_name: str):
        """
        Calculates and logs metrics for both Velocity and Yaw Rate.
        y_true, y_pred shape: (N, 2)
        """
        metrics = {}
        target_names = ["Velocity", "Yaw_Rate"]
        
        for i, name in enumerate(target_names):
            mae = mean_absolute_error(y_true[:, i], y_pred[:, i])
            rmse = np.sqrt(mean_squared_error(y_true[:, i], y_pred[:, i]))
            r2 = r2_score(y_true[:, i], y_pred[:, i])
            
            metrics[name] = {
                "MAE": mae,
                "RMSE": rmse,
                "R2": r2
            }
            print(f"[{model_name}] {name} - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}")
            
        return metrics

    def train_baseline(self, model, X_train, y_train, X_test, y_test):
        print("Training Baseline Model...")
        model.fit(X_train, y_train)
        print("Evaluating Baseline Model...")
        y_pred = model.predict(X_test)
        metrics = self.evaluate_metrics(y_test, y_pred, "Baseline (RF)")
        return model, metrics

    def train_deep_model(self, model, X_train, y_train, X_test, y_test, 
                         epochs=10, batch_size=64, lr=0.001):
        """
        Trains the PyTorch model.
        """
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        
        # Create DataLoaders
        train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
        test_ds = TensorDataset(torch.FloatTensor(X_test), torch.FloatTensor(y_test))
        
        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
        test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)
        
        criterion = nn.MSELoss()
        optimizer = optim.Adam(model.parameters(), lr=lr)
        
        print(f"Training Deep IDR Model on {device}...")
        
        for epoch in range(epochs):
            model.train()
            train_loss = 0.0
            for batch_x, batch_y in train_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                
                optimizer.zero_grad()
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item() * batch_x.size(0)
                
            train_loss /= len(train_loader.dataset)
            
            # Validation
            model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for batch_x, batch_y in test_loader:
                    batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                    outputs = model(batch_x)
                    loss = criterion(outputs, batch_y)
                    val_loss += loss.item() * batch_x.size(0)
            val_loss /= len(test_loader.dataset)
            
            print(f"Epoch {epoch+1}/{epochs} - Train Loss (MSE): {train_loss:.4f}, Val Loss: {val_loss:.4f}")
            
        # Final evaluation metrics
        model.eval()
        all_preds = []
        with torch.no_grad():
            for batch_x, _ in test_loader:
                batch_x = batch_x.to(device)
                outputs = model(batch_x)
                all_preds.append(outputs.cpu().numpy())
                
        y_pred = np.vstack(all_preds)
        metrics = self.evaluate_metrics(y_test, y_pred, "Deep IDR Model")
        
        # Save checkpoint
        checkpoint_path = os.path.join(self.checkpoint_dir, "deep_idr_model.pth")
        torch.save(model.state_dict(), checkpoint_path)
        print(f"Saved checkpoint to {checkpoint_path}")
        
        return model, metrics
