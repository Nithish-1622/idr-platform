import json
import torch
import numpy as np
import sys

sys.path.append(r"e:\idr-platform")
from ml.src.training.models import DeepIDRModel

def test_user_input():
    raw_csv = """9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.80,0.00,0.04
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.80,0.00,0.04
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.80,0.00,0.04
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.80,0.00,0.04
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.80,0.00,0.04
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.82,0.00,0.05
9.81,0.00,0.06
9.82,0.00,0.05
9.81,0.00,0.04
9.80,0.00,0.05
9.81,0.00,0.05
9.82,0.00,0.05"""

    lines = raw_csv.strip().split('\n')
    data = []
    for line in lines:
        parts = line.strip().split(',')
        data.append([float(parts[0]), float(parts[1]), float(parts[2])])
    
    raw_input = np.array(data)
    
    # Create Sliding Windows of Size 10
    window_size = 10
    X_input = []
    for i in range(window_size, len(raw_input) + 1):
        X_input.append(raw_input[i-window_size:i])
    X_input = np.array(X_input)
    
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
    X_norm = (X_input - mean_vals) / std_vals
    
    # Predict
    with torch.no_grad():
        preds = model(torch.FloatTensor(X_norm).to(device)).cpu().numpy()
        
    print(f"=======================================================================")
    print(f"USER PROVIDED BATCH INPUT (Processed into {len(X_input)} sliding windows)")
    print(f"=======================================================================")
    print(f"{'WINDOW INDEX':<15} | {'PREDICTED VELOCITY (km/h)':<25} | {'PREDICTED YAW (deg/s)':<25}")
    print("-----------------------------------------------------------------------")
    
    for i, pred in enumerate(preds):
        vel, yaw = pred
        print(f"Window {i+1:<8} | {vel:>20.2f} km/h | {yaw:>20.2f} °/s")
    print("=======================================================================")

if __name__ == '__main__':
    test_user_input()
