import pandas as pd
import os

def get_stats(dataset_path):
    s_path = None
    v_path = None
    for f in os.listdir(dataset_path):
        if f.startswith('S-') and f.endswith('.csv'): s_path = os.path.join(dataset_path, f)
        if (f.startswith('V-') or f.startswith('V_')) and f.endswith('.csv'): v_path = os.path.join(dataset_path, f)
        
    df_s = pd.read_csv(s_path, encoding='latin1')
    df_v = pd.read_csv(v_path)
    df_v.columns = df_v.columns.str.strip()
    df_s.columns = df_s.columns.str.strip()

    from ml.src.cleaning.cleaner import DataCleaner
    from ml.src.synchronization.sync import Synchronizer
    
    cleaner = DataCleaner()
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    sync = Synchronizer()
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    
    samples = len(df_v_sync)
    
    # distance
    import numpy as np
    lat_cols = [c for c in df_v_sync.columns if 'Latitude' in c]
    lon_cols = [c for c in df_v_sync.columns if 'Longitude' in c]
    lat = df_v_sync[lat_cols[0]].values
    lon = df_v_sync[lon_cols[0]].values
    
    lat0, lon0 = lat[0], lon[0]
    lat_diff = lat - lat0
    lon_diff = lon - lon0
    y = lat_diff * 111320.0
    x = lon_diff * 111320.0 * np.cos(np.deg2rad(lat0))
    traj = np.column_stack((x, y))
    dist = np.sum(np.linalg.norm(np.diff(traj, axis=0), axis=1))
    
    duration = samples * 0.1 # assuming 10Hz
    return samples, dist, duration

data_root = r"e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset"
valid_datasets = [
    r"S (Driver A)\S1",
    r"S (Driver A)\S2",
    r"S (Driver A)\S3b",
    r"S (Driver A)\S3c",
    r"S (Driver A)\S4",
    r"M (Driver B)",
    r"Y (Driver D)\Y1"
]

print("dataset,samples,distance(km),duration(min)")
for ds in valid_datasets:
    s, dist, dur = get_stats(os.path.join(data_root, ds))
    print(f"{os.path.basename(ds)},{s},{dist/1000:.2f},{dur/60:.2f}")
