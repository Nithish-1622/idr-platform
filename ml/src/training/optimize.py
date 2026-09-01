import os
import sys
import numpy as np
import torch

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.src.ingestion.loader import DatasetLoader
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer
from ml.src.alignment.aligner import IMUAligner
from ml.src.features.engineer import FeatureEngineer
from ml.src.training.models import DeepIDRModel
from ml.src.training.trainer import ModelTrainer

def run_optimization():
    data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
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
    
    window_sizes = [10]
    hidden_dims = [32, 64]
    
    best_rmse = float('inf')
    best_params = {}
    
    print("--- Starting Hyperparameter Grid Search ---")
    
    for w in window_sizes:
        engineer = FeatureEngineer(window_size=w)
        all_X = []
        all_y = []
        
        for s_path, v_path in sessions:
            df_s, df_v = loader.load_session(s_path, v_path)
            df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
            df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
            df_aligned = aligner.align(df_s_sync)
            
            _, X_3d, y = engineer.generate_features(df_aligned, df_v_sync)
            all_X.append(X_3d)
            all_y.append(y)
            
        X = np.vstack(all_X)
        y = np.vstack(all_y)
        
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        for hd in hidden_dims:
            print(f"\nEvaluating Window Size: {w}, Hidden Dim: {hd}")
            
            model = DeepIDRModel(num_features=5, window_size=w, hidden_dim=hd, num_outputs=2)
            trainer = ModelTrainer(checkpoint_dir=os.path.join(os.path.dirname(__file__), "..", "..", "models", "checkpoints"))
            
            model, metrics = trainer.train_deep_model(model, X_train, y_train, X_test, y_test, epochs=3, batch_size=128)
            
            # Use Velocity RMSE as the primary optimization target
            vel_rmse = metrics['Velocity']['RMSE']
            print(f"Velocity RMSE for w={w}, hd={hd} -> {vel_rmse:.4f}")
            
            if vel_rmse < best_rmse:
                best_rmse = vel_rmse
                best_params = {'window_size': w, 'hidden_dim': hd}
                
                # Save optimized model
                torch.save(model.state_dict(), os.path.join(trainer.checkpoint_dir, "deep_idr_model_optimized.pth"))
                
    print("\n--- Optimization Complete ---")
    print(f"Best RMSE: {best_rmse:.4f} with params: {best_params}")

if __name__ == "__main__":
    run_optimization()
