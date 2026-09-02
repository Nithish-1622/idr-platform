import torch
import pandas as pd
import numpy as np
import os
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel

def show_model_io():
    # We will use S1 which is a known good dataset
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S1"
    s_path = os.path.join(data_root, "S-s1.csv")
    v_path = os.path.join(data_root, "V-s1.csv")
    
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
    model = DeepIDRModel(window_size=10, num_features=3)
    model.load_state_dict(torch.load(r"e:\idr-platform\ml\models\checkpoints\deep_idr_model.pth", weights_only=True))
    model.eval()
    
    # Take first 25 samples
    X_sample = X_3d[:25]
    y_sample_true = y_true[:25]
    
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_sample)).numpy()
        
    print("=" * 120)
    print(f"{'INPUT WINDOW (10 timesteps x 3 features: ACC_MAG, PROJ_YAW, DYN_ACC_MAG)':<80} | {'PREDICTION':<18} | {'GROUND TRUTH':<18}")
    print(f"{'':<80} | {'Vel(km/h) Yaw(d/s)':<18} | {'Vel(km/h) Yaw(d/s)':<18}")
    print("=" * 120)
    
    for i in range(25):
        # Format the 10x3 window into a compact string
        # To avoid massive text, we'll just show the mean and std of the window features
        # Or we can show the last timestep of the window which represents the current state
        window = X_sample[i]
        
        # We will print the last timestep of the window for compactness, but mention it's a 10-step window
        last_step = window[-1]
        input_str = f"Mean: AccMag={np.mean(window[:,0]):.2f}, ProjYaw={np.mean(window[:,1]):.2f}, DynAcc={np.mean(window[:,2]):.2f} | Last: {last_step[0]:.2f}, {last_step[1]:.2f}, {last_step[2]:.2f}"
        
        pred_str = f"{preds[i][0]:>8.2f} {preds[i][1]:>8.2f}"
        true_str = f"{y_sample_true[i][0]:>8.2f} {y_sample_true[i][1]:>8.2f}"
        
        print(f"{input_str:<80} | {pred_str:<18} | {true_str:<18}")

if __name__ == '__main__':
    show_model_io()
