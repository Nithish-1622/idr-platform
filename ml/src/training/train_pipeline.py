import os
import sys
import numpy as np
import json
from sklearn.model_selection import train_test_split

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from ml.src.ingestion.loader import DatasetLoader
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import BaselineModel, DeepIDRModel
from ml.src.training.trainer import ModelTrainer

def run_training_pipeline():
    data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    # We will use two sessions from Driver B and Driver A for the MVP test
    sessions = [
        (r"Synchronised V abd S datasets\Categorised IOVNB Dataset\M (Driver B)\S-M.csv", 
         r"Synchronised V abd S datasets\Categorised IOVNB Dataset\M (Driver B)\V-M.csv"),
        (r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S1\S-S1.csv",
         r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S1\V-S1.csv")
    ]
    
    loader = DatasetLoader(data_root)
    cleaner = DataCleaner()
    sync = Synchronizer()
    aligner = IMUAligner()
    engineer = FeatureEngineer(window_size=10) # 1 second window
    
    all_X_2d = []
    all_X_3d = []
    all_y = []
    
    print("--- 1. Data Processing Pipeline ---")
    for s_path, v_path in sessions:
        print(f"Processing session: {s_path}")
        df_s, df_v = loader.load_session(s_path, v_path)
        df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
        df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
        df_aligned = aligner.align(df_s_sync)
        
        X_2d, X_3d, y = engineer.generate_features(df_aligned, df_v_sync)
        
        all_X_2d.append(X_2d)
        all_X_3d.append(X_3d)
        all_y.append(y)
        
    # Combine datasets
    X_2d = np.vstack(all_X_2d)
    X_3d = np.vstack(all_X_3d)
    y = np.vstack(all_y)
    
    print(f"Total dataset shape - X_2d: {X_2d.shape}, X_3d: {X_3d.shape}, y: {y.shape}")
    
    # Train-test split (80/20) - For MVP we just do random split, 
    # but in production, we should split by sessions.
    # To avoid row-level leakage, we'll split sequentially
    split_idx = int(len(X_3d) * 0.8)
    
    X_2d_train, X_2d_test = X_2d[:split_idx], X_2d[split_idx:]
    X_3d_train, X_3d_test = X_3d[:split_idx], X_3d[split_idx:]
    y_train, y_test = y[:split_idx], y[split_idx:]
    
    print("--- 2. Model Training Pipeline ---")
    trainer = ModelTrainer(checkpoint_dir=os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints"))
    
    # Baseline (Random Forest)
    rf_model = BaselineModel(n_estimators=10) # Small for fast MVP testing
    trainer.train_baseline(rf_model, X_2d_train, y_train, X_2d_test, y_test)
    
    # Deep IDR Model (Baseline 3-feature)
    deep_model = DeepIDRModel(num_features=3, window_size=10, hidden_dim=32, num_outputs=2)
    trainer.train_deep_model(deep_model, X_3d_train, y_train, X_3d_test, y_test, epochs=3, batch_size=128)
    
    # Save the MVP model weights explicitly
    import torch
    torch.save(deep_model.state_dict(), os.path.join(trainer.checkpoint_dir, "deep_idr_model.pth"))

if __name__ == "__main__":
    run_training_pipeline()
