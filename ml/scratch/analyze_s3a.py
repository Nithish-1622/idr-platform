import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.ingestion.loader import DatasetLoader
from src.cleaning.cleaner import DataCleaner
from src.synchronization.sync import Synchronizer
from src.alignment.aligner import IMUAligner
from src.features.engineer import FeatureEngineer

def analyze_s3a():
    data_root = r"e:\idr-platform\ml\data"
    s_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S3a\S-S3a.csv"
    v_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S3a\V-S3a.csv"
    
    s_full = os.path.join(data_root, s_path)
    v_full = os.path.join(data_root, v_path)
    
    loader = DatasetLoader(data_root)
    cleaner = DataCleaner()
    sync = Synchronizer()
    aligner = IMUAligner()
    engineer = FeatureEngineer(window_size=10)
    
    print("Loading data...")
    df_s, df_v = loader.load_session(s_full, v_full)
    print(f"Vehicle data: {len(df_v)} rows")
    
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    
    df_v_sync.columns = df_v_sync.columns.str.strip()
    
    print("\nVehicle stats:")
    print("Speed (km/h):")
    print(df_v_sync['Speed (km/h)'].describe())
    print("\nHeading (degrees):")
    print(df_v_sync['Heading (degrees)'].describe())
    
    # Calculate truth yaw rate manually to see if there's a discontinuity (like 360 to 0)
    headings = df_v_sync['Heading (degrees)'].values
    heading_diffs = np.diff(headings)
    # Fix wrap around
    heading_diffs = (heading_diffs + 180) % 360 - 180
    
    yaw_rates_deg_per_s = heading_diffs / 0.1 # assuming 10Hz
    yaw_rates_rad_per_s = np.deg2rad(yaw_rates_deg_per_s)
    
    print("\nCalculated true yaw rate (rad/s):")
    print(pd.Series(yaw_rates_rad_per_s).describe())
    
    df_aligned = aligner.align(df_s_sync)
    _, X_3d, y_true = engineer.generate_features(df_aligned, df_v_sync)
    
    print("\nTarget y_true yaw rate (rad/s) from engineer:")
    print(pd.Series(y_true[:, 1]).describe())

    # Check for NaNs or outliers in features
    print("\nFeatures X_3d shape:", X_3d.shape)
    for i in range(3):
        print(f"Feature {i} min: {X_3d[:, :, i].min()}, max: {X_3d[:, :, i].max()}")

if __name__ == "__main__":
    analyze_s3a()
