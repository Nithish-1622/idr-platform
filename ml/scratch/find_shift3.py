import pandas as pd
import numpy as np
from scipy import signal
import os
import glob

dataset_name = "Vtb03"
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

heading_cols = [c for c in df_v_sync.columns if 'Heading' in c]
heading_diff = np.diff(df_v_sync[heading_cols[0]].values)
heading_diff = np.where(heading_diff > 180, heading_diff - 360, heading_diff)
heading_diff = np.where(heading_diff < -180, heading_diff + 360, heading_diff)
true_yaw_rate = np.pad(heading_diff / 0.1, (0, 1), 'edge')

proj_yaw = df_aligned['PROJ_YAW'].values

# Cross correlation
corr = signal.correlate(true_yaw_rate - np.mean(true_yaw_rate), proj_yaw - np.mean(proj_yaw), mode='full')
lags = signal.correlation_lags(len(true_yaw_rate), len(proj_yaw), mode='full')
lag = lags[np.argmax(corr)]
max_corr = np.max(corr) / (np.std(true_yaw_rate) * len(true_yaw_rate) * np.std(proj_yaw))

print(f"Max cross-correlation: {max_corr:.4f} at lag: {lag} (which is {lag*0.1:.2f} seconds)")
