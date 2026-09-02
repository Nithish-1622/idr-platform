import os
import json
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel

def process_dataset(data_root, dataset_path, window_size=10):
    full_path = os.path.join(data_root, dataset_path)
    s_path = None
    v_path = None
    for f in os.listdir(full_path):
        if f.startswith('S-') and f.endswith('.csv'): s_path = os.path.join(full_path, f)
        if (f.startswith('V-') or f.startswith('V_')) and f.endswith('.csv'): v_path = os.path.join(full_path, f)
        
    df_s = pd.read_csv(s_path, encoding='latin1')
    df_v = pd.read_csv(v_path)
    df_v.columns = df_v.columns.str.strip()
    df_s.columns = df_s.columns.str.strip()

    cleaner = DataCleaner()
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    
    sync = Synchronizer()
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    
    aligner = IMUAligner()
    df_aligned = aligner.align(df_s_sync)
    
    engineer = FeatureEngineer(window_size=window_size)
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
    return X_3d, y_true

def train_combined():
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset"
    
    train_datasets = [
        r"S (Driver A)\S1",
        r"S (Driver A)\S2",
        r"S (Driver A)\S4"
    ]
    
    val_datasets = [
        r"S (Driver A)\S3b",
        r"S (Driver A)\S3c",
        r"M (Driver B)"
    ]
    
    print("Loading Training Datasets...")
    X_train_list, y_train_list = [], []
    for ds in train_datasets:
        print(f"  - {ds}")
        X, y = process_dataset(data_root, ds)
        X_train_list.append(X)
        y_train_list.append(y)
        
    print("Loading Validation Datasets...")
    X_val_list, y_val_list = [], []
    for ds in val_datasets:
        print(f"  - {ds}")
        X, y = process_dataset(data_root, ds)
        X_val_list.append(X)
        y_val_list.append(y)
        
    X_train_raw = np.concatenate(X_train_list, axis=0)
    y_train_raw = np.concatenate(y_train_list, axis=0)
    
    X_val_raw = np.concatenate(X_val_list, axis=0)
    y_val_raw = np.concatenate(y_val_list, axis=0)
    
    print(f"Total Train Samples: {len(X_train_raw)}")
    print(f"Total Val Samples: {len(X_val_raw)}")
    
    # 1. NORMALIZATION (Fit ONLY on Train Data)
    # X shape: (samples, window_size, num_features)
    # We normalize each feature independently across all samples and timesteps
    mean_vals = np.mean(X_train_raw, axis=(0, 1))
    std_vals = np.std(X_train_raw, axis=(0, 1))
    std_vals[std_vals == 0] = 1e-8 # Prevent division by zero
    
    # Save normalization parameters
    norm_params = {
        "mean": mean_vals.tolist(),
        "std": std_vals.tolist(),
        "features": ["ACC_MAG", "PROJ_YAW", "DYN_ACC_MAG"]
    }
    
    models_dir = r"e:\idr-platform\ml\models\checkpoints"
    os.makedirs(models_dir, exist_ok=True)
    with open(os.path.join(models_dir, "norm_params_combined.json"), "w") as f:
        json.dump(norm_params, f)
        
    # Apply Normalization
    X_train = (X_train_raw - mean_vals) / std_vals
    X_val = (X_val_raw - mean_vals) / std_vals
    y_train = y_train_raw
    y_val = y_val_raw
    
    # 2. CREATE DATALOADERS
    train_dataset = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    val_dataset = TensorDataset(torch.FloatTensor(X_val), torch.FloatTensor(y_val))
    
    train_loader = DataLoader(train_dataset, batch_size=256, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=256, shuffle=False)
    
    # 3. INITIALIZE MODEL
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Training on device: {device}")
    
    model = DeepIDRModel(window_size=10, num_features=3).to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    scheduler = torch.optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.5)
    criterion = nn.MSELoss()
    
    # 4. TRAINING LOOP WITH EARLY STOPPING
    epochs = 30
    patience = 5
    best_val_loss = float('inf')
    epochs_no_improve = 0
    
    best_model_path = os.path.join(models_dir, "best_combined_model.pth")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            batch_X, batch_y = batch_X.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
            
        train_loss /= len(train_loader)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                batch_X, batch_y = batch_X.to(device), batch_y.to(device)
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        val_loss /= len(val_loader)
        
        scheduler.step()
        
        print(f"Epoch {epoch+1:02d}/{epochs} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | LR: {scheduler.get_last_lr()[0]:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            torch.save(model.state_dict(), best_model_path)
            print("  --> Saved new best model")
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping triggered after {epoch+1} epochs.")
                break
                
    print(f"Training Complete. Best model saved to {best_model_path}")

if __name__ == '__main__':
    train_combined()
