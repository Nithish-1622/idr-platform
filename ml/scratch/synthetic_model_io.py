import os
import json
import torch
import numpy as np
import pandas as pd
import sys

sys.path.append(r"e:\idr-platform")
from ml.src.training.models import DeepIDRModel

def synthesize_and_test():
    # 1. GENERATE SYNTHETIC DATA (2.5 seconds + 0.9 seconds for the initial window build-up)
    # Total required frames to get 25 windows of size 10 is: 25 + 10 - 1 = 34 frames
    num_frames = 34
    
    # Simulate a car accelerating smoothly while taking a gentle right turn.
    # Acceleration Magnitude (gravity ~9.81 + some forward dynamic acceleration)
    acc_mag = np.linspace(9.81, 10.5, num_frames)
    
    # Dynamic Acceleration (pure forward acceleration isolated from gravity)
    # Starts at 0, goes up to 1.5 m/s^2
    dyn_acc = np.linspace(0.0, 1.5, num_frames)
    
    # Projected Yaw (Heading rate of change)
    # Car is turning right at roughly 5 degrees per second. (We'll feed ~5 deg/sec into the yaw feature)
    proj_yaw = np.linspace(4.5, 5.5, num_frames)
    
    # Ground Truth values we are simulating (for the table)
    # If DynAcc is ~1 m/s^2, velocity should be increasing.
    # Let's say velocity goes from 5 km/h to 15 km/h over these 34 frames.
    true_vel = np.linspace(5.0, 15.0, num_frames)
    true_yaw = proj_yaw.copy()
    
    # 2. CREATE WINDOWS (10 timesteps each)
    X_synthetic = []
    y_synthetic_true = []
    
    for i in range(10, num_frames + 1):
        # The window is the previous 10 frames
        window_acc_mag = acc_mag[i-10:i]
        window_proj_yaw = proj_yaw[i-10:i]
        window_dyn_acc = dyn_acc[i-10:i]
        
        # Combine features into shape (10, 3)
        window = np.column_stack((window_acc_mag, window_proj_yaw, window_dyn_acc))
        X_synthetic.append(window)
        
        # The ground truth is the value at the very end of the window (the target)
        y_synthetic_true.append([true_vel[i-1], true_yaw[i-1]])
        
    X_synthetic = np.array(X_synthetic)      # Shape: (25, 10, 3)
    y_synthetic_true = np.array(y_synthetic_true) # Shape: (25, 2)
    
    # 3. LOAD MODEL & NORMALIZER
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = DeepIDRModel(window_size=10, num_features=3).to(device)
    model.load_state_dict(torch.load(r"e:\idr-platform\ml\models\checkpoints\best_combined_model.pth", weights_only=True))
    model.eval()
    
    with open(r"e:\idr-platform\ml\models\checkpoints\norm_params_combined.json", "r") as f:
        norm_params = json.load(f)
    mean_vals = np.array(norm_params["mean"])
    std_vals = np.array(norm_params["std"])
    
    # 4. PREDICT
    X_norm = (X_synthetic - mean_vals) / std_vals
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_norm).to(device)).cpu().numpy()
        
    # 5. PRINT REPORT
    print(f"===================================================================================================================================")
    print(f"SYNTHETIC DATASET MODEL IO REPORT")
    print(f"Scenario: Simulating a vehicle accelerating forward (0 to 1.5 m/s^2) while turning right (~5 deg/s).")
    print(f"===================================================================================================================================")
    print(f"{'INPUT WINDOW (Last Timestep: ACC_MAG, PROJ_YAW, DYN_ACC)':<65} | {'PREDICTION':<18} | {'SYNTHETIC TRUTH':<18} | {'ABSOLUTE ERROR':<15}")
    print(f"{'':<65} | {'Vel(km/h) Yaw(d/s)':<18} | {'Vel(km/h) Yaw(d/s)':<18} | {'Vel(km/h) Yaw(d/s)':<15}")
    print("-----------------------------------------------------------------------------------------------------------------------------------")
    
    for i in range(25):
        raw_window = X_synthetic[i]
        last_step = raw_window[-1]
        
        # Format input string
        input_str = f"Synthetic Sensors: AccMag={last_step[0]:.2f}, ProjYaw={last_step[1]:.2f}, DynAcc={last_step[2]:.2f}"
        
        # Prediction and Truth
        pred_vel, pred_yaw = preds[i]
        true_vel, true_yaw = y_synthetic_true[i]
        
        # Absolute Errors
        err_vel = abs(pred_vel - true_vel)
        err_yaw = abs(pred_yaw - true_yaw)
        
        pred_str = f"{pred_vel:>8.2f} {pred_yaw:>8.2f}"
        true_str = f"{true_vel:>8.2f} {true_yaw:>8.2f}"
        err_str = f"{err_vel:>8.2f} {err_yaw:>8.2f}"
        
        print(f"{input_str:<65} | {pred_str:<18} | {true_str:<18} | {err_str:<15}")
    print("===================================================================================================================================")

if __name__ == '__main__':
    synthesize_and_test()
