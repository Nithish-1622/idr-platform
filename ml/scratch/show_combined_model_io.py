import os
import json
import torch
import numpy as np
import pandas as pd
import sys
sys.path.append(r"e:\idr-platform")

from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel
from ml.src.evaluation.evaluator import DeadReckoningEvaluator

def show_combined_io():
    # We will use S2 as requested (which had 23.44% drift)
    dataset_name = "S2"
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S2"
    s_path = os.path.join(data_root, "S-s2.csv")
    v_path = os.path.join(data_root, "V-s2.csv")
    
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
    engineer = FeatureEngineer(window_size=10)
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
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
    
    # Apply normalization
    X_norm = (X_3d - mean_vals) / std_vals
    
    # Take 25 random contiguous samples (e.g. from the middle of the trip)
    start_idx = 1000
    X_sample = X_norm[start_idx:start_idx+25]
    X_sample_raw = X_3d[start_idx:start_idx+25]
    y_sample_true = y_true[start_idx:start_idx+25]
    
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_sample).to(device)).cpu().numpy()
        
    print(f"===================================================================================================================================")
    print(f"COMBINED MODEL IO REPORT - DATASET: {dataset_name} (Overall Dataset Drift: 1.71%)")
    print(f"===================================================================================================================================")
    print(f"{'INPUT WINDOW (Last Timestep: ACC_MAG, PROJ_YAW, DYN_ACC)':<65} | {'PREDICTION':<18} | {'GROUND TRUTH':<18} | {'ABSOLUTE ERROR':<15}")
    print(f"{'':<65} | {'Vel(km/h) Yaw(d/s)':<18} | {'Vel(km/h) Yaw(d/s)':<18} | {'Vel(km/h) Yaw(d/s)':<15}")
    print("-----------------------------------------------------------------------------------------------------------------------------------")
    
    for i in range(25):
        raw_window = X_sample_raw[i]
        last_step = raw_window[-1]
        
        # Format input string
        input_str = f"Current Sensor Reading: AccMag={last_step[0]:.2f}, ProjYaw={last_step[1]:.2f}, DynAcc={last_step[2]:.2f}"
        
        # Prediction and Truth
        pred_vel, pred_yaw = preds[i]
        true_vel, true_yaw = y_sample_true[i]
        
        # Absolute Errors
        err_vel = abs(pred_vel - true_vel)
        err_yaw = abs(pred_yaw - true_yaw)
        
        pred_str = f"{pred_vel:>8.2f} {pred_yaw:>8.2f}"
        true_str = f"{true_vel:>8.2f} {true_yaw:>8.2f}"
        err_str = f"{err_vel:>8.2f} {err_yaw:>8.2f}"
        
        print(f"{input_str:<65} | {pred_str:<18} | {true_str:<18} | {err_str:<15}")
    print("===================================================================================================================================")

if __name__ == '__main__':
    show_combined_io()
