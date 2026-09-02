import os
import sys
import json
import torch
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

def evaluate_combined():
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset"
    
    datasets = [
        ("S1", r"S (Driver A)\S1"),
        ("S2", r"S (Driver A)\S2"),
        ("S4", r"S (Driver A)\S4"),
        ("S3b", r"S (Driver A)\S3b"),
        ("S3c", r"S (Driver A)\S3c"),
        ("M", r"M (Driver B)"),
        ("Y1", r"Y (Driver D)\Y1")
    ]
    
    # Load Model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DeepIDRModel(window_size=10, num_features=3).to(device)
    model.load_state_dict(torch.load(r"e:\idr-platform\ml\models\checkpoints\best_combined_model.pth", weights_only=True))
    model.eval()
    
    # Load Normalizer
    with open(r"e:\idr-platform\ml\models\checkpoints\norm_params_combined.json", "r") as f:
        norm_params = json.load(f)
    mean_vals = np.array(norm_params["mean"])
    std_vals = np.array(norm_params["std"])
    
    results = []
    
    for name, path in datasets:
        print(f"\nEvaluating {name}...")
        full_path = os.path.join(data_root, path)
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
        
        # Ground Truth
        lat_cols = [c for c in df_v_sync.columns if 'Latitude' in c]
        lon_cols = [c for c in df_v_sync.columns if 'Longitude' in c]
        lat = df_v_sync[lat_cols[0]].values
        lon = df_v_sync[lon_cols[0]].values
        true_traj = latlon_to_local_xy(lat, lon)
        true_dist = np.sum(np.linalg.norm(np.diff(true_traj, axis=0), axis=1))
        
        aligner = IMUAligner()
        df_aligned = aligner.align(df_s_sync)
        
        engineer = FeatureEngineer(window_size=10)
        _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
        
        # Apply combined normalization
        X_norm = (X_3d - mean_vals) / std_vals
        
        with torch.no_grad():
            preds = model(torch.FloatTensor(X_norm).to(device)).cpu().numpy()
            
        vel_pred = preds[:, 0]
        yaw_pred = preds[:, 1]
        
        heading_cols = [c for c in df_v_sync.columns if 'Heading' in c]
        initial_heading = df_v_sync[heading_cols[0]].values[0] if heading_cols else 0.0
        
        evaluator = DeadReckoningEvaluator(dt=0.1)
        pred_traj = evaluator.integrate_kinematics(vel_pred, yaw_pred, initial_heading)
        true_traj_aligned = true_traj[10 - 1:]
        
        res = evaluator.calculate_drift(pred_traj, true_traj_aligned)
        drift = res['Drift_Percentage']
        
        print(f"{name} | Drift: {drift:.2f}% | FPE: {res['FPE_meters']:.2f}m | Dist: {res['Total_Distance_meters']/1000:.2f}km")
        
        results.append({
            "Dataset": name,
            "Drift (%)": drift,
            "FPE (m)": res['FPE_meters'],
            "ADE (m)": res['ADE_meters'],
            "Distance (km)": res['Total_Distance_meters'] / 1000
        })
        
        # Plot Trajectory
        plt.figure(figsize=(10,10))
        plt.plot(true_traj_aligned[:,0], true_traj_aligned[:,1], label='Ground Truth', color='black', linewidth=2)
        plt.plot(pred_traj[:,0], pred_traj[:,1], label='Predicted (Combined Model)', color='blue', linestyle='--')
        plt.title(f"Trajectory - {name} (Drift: {drift:.2f}%)")
        plt.xlabel("X (m)")
        plt.ylabel("Y (m)")
        plt.legend()
        plt.grid(True)
        plt.axis('equal')
        plt.savefig(f"e:\\idr-platform\\docs\\ml\\trajectory_combined_{name}.png")
        plt.close()
        
    df_results = pd.DataFrame(results)
    print("\n--- FINAL COMBINED MODEL PERFORMANCE ---")
    print(df_results.to_markdown(index=False))

if __name__ == '__main__':
    evaluate_combined()
