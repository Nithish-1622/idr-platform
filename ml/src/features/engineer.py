import pandas as pd
import numpy as np

class FeatureEngineer:
    def __init__(self, window_size: int = 10):
        """
        Args:
            window_size: Number of timesteps (at 10Hz, 10 = 1 second) to look back for features.
        """
        self.window_size = window_size
        
        # Define the base features to use (Rotation Invariant + Gravity Compensated)
        self.feature_cols = ['ACC_MAG', 'PROJ_YAW', 'DYN_ACC_MAG']
        
        # Targets are dynamically found to bypass encoding issues
        self.target_base_names = ['Velocity', 'Yaw Rate']

    def generate_features(self, df_aligned: pd.DataFrame, df_v: pd.DataFrame):
        """
        Generates 2D features for Baseline models and 3D features for Deep models.
        Also extracts targets.
        
        Args:
            df_aligned: The smartphone DataFrame with rotation-invariant features.
            df_v: The vehicle DataFrame with targets.
            
        Returns:
            X_2d (np.ndarray): Shape (N, window_size * num_features) for Baseline (e.g. Random Forest).
            X_3d (np.ndarray): Shape (N, window_size, num_features) for Neural Networks.
            y (np.ndarray): Shape (N, 2) containing Velocity and Yaw Rate.
        """
        # Ensure we have our required features
        for c in self.feature_cols:
            if c not in df_aligned.columns:
                raise ValueError(f"Required feature {c} missing from aligned dataframe.")
                
        # Find exact target columns
        vel_cols = [c for c in df_v.columns if self.target_base_names[0] in c]
        yaw_cols = [c for c in df_v.columns if self.target_base_names[1] in c]
        
        if not vel_cols or not yaw_cols:
            raise ValueError(f"Targets missing. Found vel: {vel_cols}, yaw: {yaw_cols}")
            
        target_cols = [vel_cols[0], yaw_cols[0]]
        
        # Align lengths if they differ slightly
        min_len = min(len(df_aligned), len(df_v))
        X_base = df_aligned[self.feature_cols].iloc[:min_len].values
        Y_base = df_v[target_cols].iloc[:min_len].values
        
        # Create sliding windows
        num_samples = min_len - self.window_size + 1
        num_features = len(self.feature_cols)
        
        if num_samples <= 0:
            raise ValueError("Dataset is smaller than the window size.")
            
        X_3d = np.zeros((num_samples, self.window_size, num_features))
        y = np.zeros((num_samples, 2))
        
        # We predict the target at the END of the window
        for i in range(num_samples):
            X_3d[i] = X_base[i : i + self.window_size, :]
            y[i] = Y_base[i + self.window_size - 1, :]
            
        # Flatten for Baseline models
        X_2d = X_3d.reshape(num_samples, -1)
        
        return X_2d, X_3d, y
