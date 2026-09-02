import os
import sys
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from ml.src.ingestion.loader import DatasetLoader
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel
from ml.src.evaluation.evaluator import DeadReckoningEvaluator

def latlon_to_local_xy(lat_arr, lon_arr):
    lat0, lon0 = lat_arr[0], lon_arr[0]
    lat_diff = lat_arr - lat0
    lon_diff = lon_arr - lon0
    
    y = lat_diff * 111320.0
    x = lon_diff * 111320.0 * np.cos(np.deg2rad(lat0))
    return np.column_stack((x, y))

def run_s1_pipeline():
    data_root = r"e:\idr-platform\ml\data"
    s_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S1\S-S1.csv"
    v_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S1\V-S1.csv"
    
    s_full = os.path.join(data_root, s_path)
    v_full = os.path.join(data_root, v_path)
    
    loader = DatasetLoader(data_root)
    cleaner = DataCleaner()
    sync = Synchronizer()
    aligner = IMUAligner()
    engineer = FeatureEngineer(window_size=10)
    
    print("CURRENT DATASET: S1")
    print("TRAINING FILES:")
    print(f"- {s_path}")
    print(f"- {v_path}")
    
    print("\n--- 1. Data Processing ---")
    df_s, df_v = loader.load_session(s_full, v_full)
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    df_aligned = aligner.align(df_s_sync)
    
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
    print(f"Dataset: S1")
    print(f"Samples (Windows): {len(y_true)}")
    
    # 80/20 train/test split for this single dataset
    split_idx = int(len(X_3d) * 0.8)
    X_train, X_test = X_3d[:split_idx], X_3d[split_idx:]
    y_train, y_test = y_true[:split_idx], y_true[split_idx:]
    
    print("\n--- 2. Model Training (Fine-tuning) ---")
    model_path = r"e:\idr-platform\ml\models\checkpoints\deep_idr_model.pth"
    model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=32, num_outputs=2)
    
    if os.path.exists(model_path):
        print(f"Loading existing checkpoint: {model_path}")
        model.load_state_dict(torch.load(model_path, weights_only=True))
    else:
        print("Starting from scratch (no checkpoint found).")
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    
    batch_size = 64
    epochs = 3
    lr = 0.001
    train_ds = TensorDataset(torch.FloatTensor(X_train), torch.FloatTensor(y_train))
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
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
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}")
        
    # Save checkpoint
    torch.save(model.state_dict(), model_path)
    
    print("\n--- 3. Inference & Evaluation (on Full S1 dataset) ---")
    model.eval()
    with torch.no_grad():
        outputs = model(torch.FloatTensor(X_3d).to(device))
        y_pred = outputs.cpu().numpy()
        
    true_vel = y_true[:, 0]
    true_yaw = y_true[:, 1]
    pred_vel = y_pred[:, 0]
    pred_yaw = y_pred[:, 1]
    
    # Ground truth coordinates
    offset = engineer.window_size - 1
    df_v_aligned = df_v_sync.iloc[offset:offset+len(y_true)].copy()
    df_v_aligned.columns = df_v_aligned.columns.str.strip()
    
    initial_heading_deg = df_v_aligned['Heading (degrees)'].iloc[0]
    lat = df_v_aligned['Latitude (degrees)'].values
    lon = df_v_aligned['Longitude (degrees)'].values
    true_traj = latlon_to_local_xy(lat, lon)
    
    evaluator = DeadReckoningEvaluator(dt=0.1)
    pred_traj = evaluator.integrate_kinematics(pred_vel, pred_yaw, initial_heading_deg=initial_heading_deg)
    
    metrics = evaluator.calculate_drift(pred_traj, true_traj)
    
    print("\nRESULTS:")
    print(f"FPE: {metrics['FPE_meters']:.2f} m")
    print(f"ADE: {metrics['ADE_meters']:.2f} m")
    
    gt_dist = metrics['Total_Distance_meters']
    pred_dist = np.sum(pred_vel / 3.6 * 0.1)
    print(f"GT Distance: {gt_dist:.2f} m")
    print(f"Predicted Distance: {pred_dist:.2f} m")
    print(f"Drift: {metrics['Drift_Percentage']:.2f}%")
    
    ratio = pred_dist / gt_dist if gt_dist > 0 else 0
    print(f"Predicted/GT Distance Ratio: {ratio:.4f}")
    
    # --- VISUAL ALIGNMENT (For plotting only, does not affect metrics) ---
    v_true = true_traj[-1]
    v_pred = pred_traj[-1]
    
    theta = np.arctan2(v_true[1], v_true[0]) - np.arctan2(v_pred[1], v_pred[0])
    scale = np.linalg.norm(v_true) / (np.linalg.norm(v_pred) + 1e-8)
    
    c, s = np.cos(theta), np.sin(theta)
    R = np.array(((c, -s), (s, c)))
    pred_traj_vis = np.dot(pred_traj, R.T) * scale
    
    plt.figure(figsize=(10, 8))
    plt.plot(true_traj[:, 0], true_traj[:, 1], label='Ground Truth (GNSS)', color='blue', linewidth=2)
    plt.plot(pred_traj_vis[:, 0], pred_traj_vis[:, 1], label='Deep IDR Prediction (Aligned for plot)', color='red', linestyle='dashed', linewidth=2)
    
    plt.scatter(true_traj[0, 0], true_traj[0, 1], color='green', marker='o', s=100, label='Start')
    plt.scatter(true_traj[-1, 0], true_traj[-1, 1], color='blue', marker='X', s=100, label='End (Truth)')
    plt.scatter(pred_traj_vis[-1, 0], pred_traj_vis[-1, 1], color='red', marker='X', s=100, label='End (Pred)')
    
    plt.title('Dead Reckoning: S1')
    plt.xlabel('Local X (meters)')
    plt.ylabel('Local Y (meters)')
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    plot_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "ml", "trajectory_S1.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    print(f"Saved trajectory plot to {plot_path}")

if __name__ == "__main__":
    run_s1_pipeline()
