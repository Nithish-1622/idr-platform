import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

def check_sanity(dataset_name="Vtb03"):
    data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vtb (Driver E)\Vtb03"
    s_path = os.path.join(data_root, "S-Vtb3.csv")
    v_path = os.path.join(data_root, "V-vtb3.csv")

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

    # GNSS True Yaw Rate vs PROJ_YAW
    heading_cols = [c for c in df_v_sync.columns if 'Heading' in c]
    heading_diff = np.diff(df_v_sync[heading_cols[0]].values)
    heading_diff = np.where(heading_diff > 180, heading_diff - 360, heading_diff)
    heading_diff = np.where(heading_diff < -180, heading_diff + 360, heading_diff)
    true_yaw_rate = np.pad(heading_diff / 0.1, (0, 1), 'edge')
    proj_yaw = df_aligned['PROJ_YAW'].values

    # GNSS Velocity vs ACC_MAG (smoothed for visual comparison)
    speed_cols = [c for c in df_v_sync.columns if 'Speed' in c or 'Velocity' in c]
    gnss_vel = df_v_sync[speed_cols[0]].values
    acc_mag = df_aligned['ACC_MAG'].values
    # Smooth acc_mag for visual comparison (1 sec rolling)
    acc_mag_smoothed = pd.Series(acc_mag).rolling(10, min_periods=1).mean().values

    # Plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 10))

    # YAW PLOT
    # We plot the first 2000 samples to see the waveform clearly
    plot_len = min(2000, len(true_yaw_rate))
    
    # Standardize them just to compare the shape
    true_yaw_norm = (true_yaw_rate[:plot_len] - np.mean(true_yaw_rate[:plot_len])) / (np.std(true_yaw_rate[:plot_len]) + 1e-6)
    proj_yaw_norm = (proj_yaw[:plot_len] - np.mean(proj_yaw[:plot_len])) / (np.std(proj_yaw[:plot_len]) + 1e-6)

    ax1.plot(true_yaw_norm, label='GNSS Derived Yaw Rate (Shape)', alpha=0.8, color='green')
    ax1.plot(proj_yaw_norm, label='Smartphone PROJ_YAW (Shape)', alpha=0.6, color='red')
    ax1.set_title(f'{dataset_name} - YAW CORRELATION SANITY CHECK')
    ax1.set_ylabel('Normalized Amplitude')
    ax1.legend()
    ax1.grid(True)

    # ACCEL PLOT
    gnss_vel_norm = (gnss_vel[:plot_len] - np.mean(gnss_vel[:plot_len])) / (np.std(gnss_vel[:plot_len]) + 1e-6)
    acc_norm = (acc_mag_smoothed[:plot_len] - np.mean(acc_mag_smoothed[:plot_len])) / (np.std(acc_mag_smoothed[:plot_len]) + 1e-6)
    
    ax2.plot(gnss_vel_norm, label='GNSS Speed (Shape)', alpha=0.8, color='blue')
    ax2.plot(acc_norm, label='Smartphone ACC_MAG (Shape)', alpha=0.6, color='orange')
    ax2.set_title(f'{dataset_name} - VELOCITY VS ACCEL SANITY CHECK')
    ax2.set_xlabel('Time (x0.1s)')
    ax2.set_ylabel('Normalized Amplitude')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()
    plot_path = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "ml", f"sanity_{dataset_name}.png")
    os.makedirs(os.path.dirname(plot_path), exist_ok=True)
    plt.savefig(plot_path)
    print(f"Saved sanity check plot to {plot_path}")

if __name__ == "__main__":
    check_sanity()
