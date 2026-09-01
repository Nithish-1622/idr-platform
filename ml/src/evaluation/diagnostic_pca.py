import os
import sys
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from ml.src.ingestion.loader import DatasetLoader
from ml.src.cleaning.cleaner import DataCleaner
from ml.src.synchronization.sync import Synchronizer

def run_pca_diagnostics():
    print("--- Running Phase 5 PCA Diagnostics ---")
    data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    # Use Driver A's S2 session for diagnostic
    s_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S2\S-S2.csv"
    v_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\S (Driver A)\S2\V-S2.csv"
    
    loader = DatasetLoader(data_root)
    cleaner = DataCleaner()
    sync = Synchronizer()
    
    df_s, df_v = loader.load_session(s_path, v_path)
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    
    # Extract horizontal acceleration
    acc_cols = [c for c in df_s_sync.columns if 'ACCELEROMETER' in c]
    grav_cols = [c for c in df_s_sync.columns if 'GRAVITY' in c]
    
    dyn_x = df_s_sync[acc_cols[0]] - df_s_sync[grav_cols[0]]
    dyn_y = df_s_sync[acc_cols[1]] - df_s_sync[grav_cols[1]]
    dyn_z = df_s_sync[acc_cols[2]] - df_s_sync[grav_cols[2]]
    
    g_mag = np.sqrt(df_s_sync[grav_cols[0]]**2 + df_s_sync[grav_cols[1]]**2 + df_s_sync[grav_cols[2]]**2) + 1e-8
    nx = df_s_sync[grav_cols[0]] / g_mag
    ny = df_s_sync[grav_cols[1]] / g_mag
    nz = df_s_sync[grav_cols[2]] / g_mag
    
    dot = dyn_x*nx + dyn_y*ny + dyn_z*nz
    
    horiz_x = dyn_x - dot * nx
    horiz_y = dyn_y - dot * ny
    horiz_z = dyn_z - dot * nz
    
    horiz_acc = np.column_stack([horiz_x, horiz_y, horiz_z])
    
    # 1. Global PCA
    pca_global = PCA(n_components=2)
    pca_global.fit(horiz_acc)
    global_comp = pca_global.components_[0] # Primary axis
    
    print(f"\n1. Global PCA Basis (Forward Axis): {global_comp}")
    
    # 2. Local PCA (Rolling Window to detect orientation drift)
    # 10Hz data, let's use 60-second windows (600 samples)
    window_size = 600
    num_windows = len(horiz_acc) // window_size
    
    angles = []
    
    for i in range(num_windows):
        window_data = horiz_acc[i*window_size : (i+1)*window_size]
        if len(window_data) < window_size: continue
        
        pca_local = PCA(n_components=2)
        try:
            pca_local.fit(window_data)
            local_comp = pca_local.components_[0]
            
            # Compute angle difference between global and local forward axis
            cos_theta = np.dot(global_comp, local_comp) / (np.linalg.norm(global_comp) * np.linalg.norm(local_comp))
            cos_theta = np.clip(cos_theta, -1.0, 1.0)
            angle_deg = np.degrees(np.arccos(np.abs(cos_theta))) # Abs because sign doesn't matter (forward/backward ambiguous)
            angles.append(angle_deg)
        except Exception:
            pass
            
    print(f"\n2. Phone Orientation Shift Analysis (60-sec rolling windows):")
    print(f"   Max angle deviation from Global Basis: {np.max(angles):.2f} degrees")
    print(f"   Average angle deviation from Global Basis: {np.mean(angles):.2f} degrees")
    
    # 3. Leakage Analysis (Correlation)
    global_proj = pca_global.transform(horiz_acc)
    forward_acc = global_proj[:, 0]
    lateral_acc = global_proj[:, 1]
    
    # Correlate with True Velocity derivative (True Acceleration)
    true_vel = df_v_sync[[c for c in df_v_sync.columns if 'Velocity' in c][0]].values
    true_acc = np.gradient(true_vel) # Rough proxy for true forward acceleration
    
    fwd_corr = np.corrcoef(forward_acc, true_acc)[0, 1]
    lat_corr = np.corrcoef(lateral_acc, true_acc)[0, 1]
    
    print(f"\n3. Acceleration Leakage Correlation:")
    print(f"   Correlation of Global FORWARD_ACC to True Forward Accel: {fwd_corr:.4f}")
    print(f"   Correlation of Global LATERAL_ACC to True Forward Accel (Leakage): {lat_corr:.4f}")
    
    print("\n--- Diagnostic Complete ---")
    print("CONCLUSION: If Average Angle Deviation is high (>10 deg), it means the phone's orientation changed during the trip.")
    print("This invalidates the Global PCA basis. Furthermore, Global PCA 'looks into the future' to define the axis, which is impossible in real-time inference.")

if __name__ == "__main__":
    run_pca_diagnostics()
