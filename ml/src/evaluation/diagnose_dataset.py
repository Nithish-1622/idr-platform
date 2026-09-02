import sys
import os
import glob
import pandas as pd
import numpy as np
import torch
import matplotlib.pyplot as plt

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

def diagnose(dataset_name):
    # Find dataset
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset"
    s_path = None
    v_path = None
    for root, dirs, files in os.walk(data_root):
        if dataset_name in dirs:
            target_dir = os.path.join(root, dataset_name)
            for f in os.listdir(target_dir):
                if f.startswith('S-') and f.endswith('.csv'):
                    s_path = os.path.join(target_dir, f)
                if (f.startswith('V-') or f.startswith('V_')) and f.endswith('.csv'):
                    v_path = os.path.join(target_dir, f)
            break
            
    if not s_path or not v_path:
        print(f"Could not find S and V files for {dataset_name}")
        return

    print(f"Loaded {s_path}")
    print(f"Loaded {v_path}")
    
    df_s_raw = pd.read_csv(s_path, encoding='latin1')
    df_v_raw = pd.read_csv(v_path)
    df_v_raw.columns = df_v_raw.columns.str.strip()
    df_s_raw.columns = df_s_raw.columns.str.strip()
    
    # Check dt
    time_s = [c for c in df_s_raw.columns if 'TIME' in c]
    time_v = [c for c in df_v_raw.columns if 'TIME' in c]
    if time_s:
        t_s = df_s_raw[time_s[0]].values
        dt_s = np.diff(t_s)
        print(f"S-dt: Mean={np.mean(dt_s):.4f}, Median={np.median(dt_s):.4f}, Min={np.min(dt_s):.4f}, Max={np.max(dt_s):.4f}")
    if time_v:
        t_v = df_v_raw[time_v[0]].values
        dt_v = np.diff(t_v)
        print(f"V-dt: Mean={np.mean(dt_v):.4f}, Median={np.median(dt_v):.4f}, Min={np.min(dt_v):.4f}, Max={np.max(dt_v):.4f}")

    # Process
    cleaner = DataCleaner()
    df_s, df_v = cleaner.clean(df_s_raw, df_v_raw)
    sync = Synchronizer()
    df_s_sync, df_v_sync = sync.sync_data(df_s, df_v)
    
    # Calculate GT Trajectory
    lat_cols = [c for c in df_v_sync.columns if 'Latitude' in c]
    lon_cols = [c for c in df_v_sync.columns if 'Longitude' in c]
    if not lat_cols or not lon_cols:
        print("Missing Latitude or Longitude in Ground Truth.")
        return
        
    lat = df_v_sync[lat_cols[0]].values
    lon = df_v_sync[lon_cols[0]].values
    true_traj = latlon_to_local_xy(lat, lon)
    true_dist = np.sum(np.linalg.norm(np.diff(true_traj, axis=0), axis=1))
    
    aligner = IMUAligner()
    df_aligned = aligner.align(df_s_sync)
    
    engineer = FeatureEngineer(window_size=10)
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
    # Model Evaluate
    model = DeepIDRModel(window_size=10, num_features=3)
    model.load_state_dict(torch.load(r"e:\idr-platform\ml\models\checkpoints\deep_idr_model.pth", weights_only=True))
    model.eval()
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_3d)).numpy()
        
    vel_pred = preds[:, 0]
    yaw_pred = preds[:, 1]
    vel_true = y_true[:, 0]
    yaw_true = y_true[:, 1]
    
    vel_rmse = np.sqrt(np.mean((vel_pred - vel_true)**2))
    yaw_rmse = np.sqrt(np.mean((yaw_pred - yaw_true)**2))
    
    heading_cols = [c for c in df_v_sync.columns if 'Heading' in c]
    initial_heading = df_v_sync[heading_cols[0]].values[0] if heading_cols else 0.0
    
    evaluator = DeadReckoningEvaluator(dt=0.1)
    pred_traj = evaluator.integrate_kinematics(vel_pred, yaw_pred, initial_heading)
    true_traj_aligned = true_traj[10 - 1:] # align with windows
    
    res = evaluator.calculate_drift(pred_traj, true_traj_aligned)
    pred_dist = np.sum(np.linalg.norm(np.diff(pred_traj, axis=0), axis=1))
    
    print("\n--- DIAGNOSTICS ---")
    print(f"FPE: {res['FPE_meters']:.2f} m")
    print(f"ADE: {res['ADE_meters']:.2f} m")
    print(f"GT Distance: {res['Total_Distance_meters']:.2f} m")
    print(f"Predicted Distance: {pred_dist:.2f} m")
    print(f"Distance Ratio (Pred/GT): {pred_dist/res['Total_Distance_meters']:.4f}")
    print(f"Drift: {res['Drift_Percentage']:.2f}%")
    print(f"Velocity RMSE: {vel_rmse:.4f}")
    print(f"Yaw Rate RMSE: {yaw_rmse:.4f}")
    
    # Feature Correlation
    heading_diff = np.diff(df_v_sync[heading_cols[0]].values)
    heading_diff = np.where(heading_diff > 180, heading_diff - 360, heading_diff)
    heading_diff = np.where(heading_diff < -180, heading_diff + 360, heading_diff)
    true_yaw_gnss = np.pad(heading_diff / 0.1, (0, 1), 'edge')
    
    try:
        corr_proj = np.corrcoef(df_aligned['PROJ_YAW'].values, true_yaw_gnss)[0,1]
        print(f"PROJ_YAW vs True Yaw Correlation: {corr_proj:.4f}")
    except:
        pass
    
    # Plot
    plt.figure(figsize=(10, 10))
    plt.plot(true_traj_aligned[:, 0], true_traj_aligned[:, 1], 'g-', label='Ground Truth (GNSS)', linewidth=2)
    plt.plot(pred_traj[:, 0], pred_traj[:, 1], 'r--', label='Predicted (Deep IDR)', linewidth=2)
    plt.legend()
    plt.title(f'Trajectory Comparison - {dataset_name}')
    plt.grid(True)
    plt.axis('equal')
    plot_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "ml", f"trajectory_{dataset_name}.png")
    plt.savefig(plot_path)
    print(f"Saved plot to {plot_path}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        diagnose(sys.argv[1])
    else:
        print("Usage: python diagnose_dataset.py <DatasetName>")
