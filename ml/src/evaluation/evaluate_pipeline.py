import os
import sys
import numpy as np
import torch
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.src.ingestion.loader import DatasetLoader
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel
from ml.src.evaluation.evaluator import DeadReckoningEvaluator

def run_real_evaluation():
    print("--- Running Real Dead Reckoning Evaluation ---")
    data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    weights_path = os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints", "deep_idr_model.pth")
    
    # We will use Driver A's S2 session as a completely held-out test set
    s_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S2\S-S2.csv"
    v_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S2\V-S2.csv"
    
    # 1. Pipeline execution
    loader = DatasetLoader(data_root)
    cleaner = DataCleaner()
    sync = Synchronizer()
    aligner = IMUAligner()
    engineer = FeatureEngineer(window_size=10)
    
    df_s, df_v = loader.load_session(s_path, v_path)
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    df_aligned = aligner.align(df_s_sync)
    
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
    # 2. Load Model & Predict
    model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=32, num_outputs=2)
    model.load_state_dict(torch.load(weights_path, weights_only=True))
    model.eval()
    
    with torch.no_grad():
        inputs = torch.FloatTensor(X_3d)
        y_pred = model(inputs).numpy()
        
    true_vel = y_true[:, 0]
    true_yaw = y_true[:, 1]
    pred_vel = y_pred[:, 0]
    pred_yaw = y_pred[:, 1]
    
    # 3. Dead Reckoning Evaluation
    evaluator = DeadReckoningEvaluator(dt=0.1)
    
    true_traj = evaluator.integrate_kinematics(true_vel, true_yaw)
    pred_traj = evaluator.integrate_kinematics(pred_vel, pred_yaw)
    
    metrics = evaluator.calculate_drift(pred_traj, true_traj)
    
    print("\nEvaluation Results on Held-out Set (S2):")
    for k, v in metrics.items():
        print(f"  {k}: {v:.2f}")
        
    # 4. Plotting
    plt.figure(figsize=(10, 8))
    plt.plot(true_traj[:, 0], true_traj[:, 1], label='Ground Truth (GNSS)', color='blue', linewidth=2)
    plt.plot(pred_traj[:, 0], pred_traj[:, 1], label='Deep IDR Prediction', color='red', linestyle='dashed', linewidth=2)
    
    plt.scatter(true_traj[0, 0], true_traj[0, 1], color='green', marker='o', s=100, label='Start')
    plt.scatter(true_traj[-1, 0], true_traj[-1, 1], color='blue', marker='X', s=100, label='End (Truth)')
    plt.scatter(pred_traj[-1, 0], pred_traj[-1, 1], color='red', marker='X', s=100, label='End (Pred)')
    
    plt.title('Dead Reckoning: Predicted vs Ground Truth Trajectory')
    plt.xlabel('Local X (meters)')
    plt.ylabel('Local Y (meters)')
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    plot_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "docs", "trajectory.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    print(f"\nSaved trajectory plot to {plot_path}")

if __name__ == "__main__":
    run_real_evaluation()
