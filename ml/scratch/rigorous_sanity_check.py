import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal
from scipy.stats import pearsonr, spearmanr
import os

def calculate_correlations(sig1, sig2, dt=0.1):
    # Ensure no NaNs
    valid = ~np.isnan(sig1) & ~np.isnan(sig2)
    sig1 = sig1[valid]
    sig2 = sig2[valid]
    
    if len(sig1) < 2:
        return 0, 0, 0, 0, 0
        
    pearson, _ = pearsonr(sig1, sig2)
    spearman, _ = spearmanr(sig1, sig2)
    
    # Cross correlation
    s1_norm = (sig1 - np.mean(sig1)) / (np.std(sig1) + 1e-8)
    s2_norm = (sig2 - np.mean(sig2)) / (np.std(sig2) + 1e-8)
    
    corr = signal.correlate(s1_norm, s2_norm, mode='full') / len(s1_norm)
    lags = signal.correlation_lags(len(s1_norm), len(s2_norm), mode='full')
    max_corr_idx = np.argmax(np.abs(corr))
    max_corr = corr[max_corr_idx]
    best_lag = lags[max_corr_idx]
    
    # RMSE after shifting by best lag (assuming best lag aligns them)
    # If best_lag is positive, sig1 is shifted forward relative to sig2
    if best_lag > 0:
        s1_shifted = s1_norm[best_lag:]
        s2_shifted = s2_norm[:-best_lag]
    elif best_lag < 0:
        s1_shifted = s1_norm[:best_lag]
        s2_shifted = s2_norm[-best_lag:]
    else:
        s1_shifted = s1_norm
        s2_shifted = s2_norm
        
    rmse = np.sqrt(np.mean((s1_shifted - s2_shifted)**2))
    return pearson, spearman, max_corr, best_lag * dt, rmse

def rigorous_sanity(dataset_name="Vtb05"):
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vtb (Driver E)\Vtb05"
    s_path = os.path.join(data_root, "S-Vtb5.csv")
    v_path = os.path.join(data_root, "V-vtb5.csv")

    df_s = pd.read_csv(s_path, encoding='latin1')
    df_v = pd.read_csv(v_path)
    df_v.columns = df_v.columns.str.strip()
    df_s.columns = df_s.columns.str.strip()

    from ml.src.cleaning.cleaner import DataCleaner
    from ml.src.synchronization.sync import Synchronizer
    from ml.src.alignment.aligner import IMUAligner

    cleaner = DataCleaner()
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    sync = Synchronizer()
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    aligner = IMUAligner()
    df_aligned = aligner.align(df_s_sync)

    dt = 0.1

    # 1. HEADING VS ORIENTATION
    heading_cols = [c for c in df_v_sync.columns if 'Heading' in c]
    gnss_heading = df_v_sync[heading_cols[0]].values
    
    orient_cols = [c for c in df_s_sync.columns if 'ORIENTATION (Yaw)' in c]
    phone_orient = df_s_sync[orient_cols[0]].values
    
    # Unwrap angles (convert to radians first, unwrap, back to degrees)
    gnss_heading_unwrapped = np.rad2deg(np.unwrap(np.deg2rad(gnss_heading)))
    phone_orient_unwrapped = np.rad2deg(np.unwrap(np.deg2rad(phone_orient)))
    
    # The coordinate frame of the phone might be rotated by some constant C or inverted.
    # We will compute correlations on the unwrapped angles.

    # 2. YAW RATE VS DERIVED YAW RATE
    # GNSS Yaw Rate
    gnss_yaw_rate = np.gradient(gnss_heading_unwrapped, dt)
    # Phone Yaw Rate (derived from orientation)
    phone_yaw_rate_derived = np.gradient(phone_orient_unwrapped, dt)
    # Phone Yaw Rate (from gyro projected)
    phone_proj_yaw = df_aligned['PROJ_YAW'].values # rad/s
    phone_proj_yaw_deg = np.rad2deg(phone_proj_yaw)

    # 3. ACCELERATION VS DYNAMIC ACCELERATION
    speed_cols = [c for c in df_v_sync.columns if 'Speed' in c or 'Velocity' in c]
    gnss_speed_kmh = df_v_sync[speed_cols[0]].values
    gnss_speed_ms = gnss_speed_kmh / 3.6
    
    # GNSS Acceleration (d(speed)/dt)
    gnss_accel = np.gradient(gnss_speed_ms, dt)
    
    # Smartphone Dynamic Acceleration Magnitude
    phone_dyn_acc = df_aligned['DYN_ACC_MAG'].values
    
    # --- CALCULATE METRICS ---
    print(f"--- {dataset_name} RIGOROUS SANITY CHECK ---")
    
    print("\n1. HEADING (Unwrapped GNSS Heading vs Unwrapped Phone Yaw)")
    p, s, mc, bl, rmse = calculate_correlations(gnss_heading_unwrapped, phone_orient_unwrapped)
    print(f"Pearson: {p:.4f} | Spearman: {s:.4f} | Max Cross-Corr: {mc:.4f} @ {bl:.1f}s | RMSE (norm): {rmse:.4f}")
    
    print("\n2. YAW RATE (GNSS d(Heading)/dt vs Phone d(Orientation)/dt)")
    p, s, mc, bl, rmse = calculate_correlations(gnss_yaw_rate, phone_yaw_rate_derived)
    print(f"Pearson: {p:.4f} | Spearman: {s:.4f} | Max Cross-Corr: {mc:.4f} @ {bl:.1f}s | RMSE (norm): {rmse:.4f}")
    
    print("\n2b. YAW RATE (GNSS d(Heading)/dt vs Phone Gyro PROJ_YAW)")
    p, s, mc, bl, rmse = calculate_correlations(gnss_yaw_rate, phone_proj_yaw_deg)
    print(f"Pearson: {p:.4f} | Spearman: {s:.4f} | Max Cross-Corr: {mc:.4f} @ {bl:.1f}s | RMSE (norm): {rmse:.4f}")

    print("\n3. ACCELERATION (GNSS d(Speed)/dt vs Phone DYN_ACC_MAG)")
    p, s, mc, bl, rmse = calculate_correlations(gnss_accel, phone_dyn_acc)
    print(f"Pearson: {p:.4f} | Spearman: {s:.4f} | Max Cross-Corr: {mc:.4f} @ {bl:.1f}s | RMSE (norm): {rmse:.4f}")
    
    # --- PLOT ---
    fig, axs = plt.subplots(4, 1, figsize=(15, 20))
    plot_len = min(4000, len(gnss_heading))
    
    def norm(arr):
        return (arr - np.mean(arr)) / (np.std(arr) + 1e-8)
        
    axs[0].plot(norm(gnss_heading_unwrapped[:plot_len]), label='GNSS Heading (Unwrapped)', color='green')
    axs[0].plot(norm(phone_orient_unwrapped[:plot_len]), label='Phone Orientation (Unwrapped)', color='red')
    axs[0].set_title('Normalized Unwrapped Heading/Orientation')
    axs[0].legend()
    
    axs[1].plot(norm(gnss_yaw_rate[:plot_len]), label='GNSS Yaw Rate', color='green')
    axs[1].plot(norm(phone_yaw_rate_derived[:plot_len]), label='Phone d(Orientation)/dt', color='red')
    axs[1].set_title('Normalized Yaw Rate (Derivative of Angle)')
    axs[1].legend()
    
    axs[2].plot(norm(gnss_yaw_rate[:plot_len]), label='GNSS Yaw Rate', color='green')
    axs[2].plot(norm(phone_proj_yaw_deg[:plot_len]), label='Phone Gyro PROJ_YAW', color='purple')
    axs[2].set_title('Normalized Yaw Rate (Gyroscope)')
    axs[2].legend()
    
    # Smooth accel for visual
    gnss_acc_smooth = pd.Series(gnss_accel).rolling(10, min_periods=1).mean().values
    phone_acc_smooth = pd.Series(phone_dyn_acc).rolling(10, min_periods=1).mean().values
    
    axs[3].plot(norm(gnss_acc_smooth[:plot_len]), label='GNSS d(Speed)/dt', color='blue')
    axs[3].plot(norm(phone_acc_smooth[:plot_len]), label='Phone DYN_ACC_MAG', color='orange')
    axs[3].set_title('Normalized Acceleration')
    axs[3].legend()
    
    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "ml", f"rigorous_sanity_{dataset_name}.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    print(f"\nSaved rigorous sanity check plot to {plot_path}")

if __name__ == "__main__":
    rigorous_sanity()
