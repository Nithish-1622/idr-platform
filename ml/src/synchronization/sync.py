import pandas as pd
import numpy as np

class Synchronizer:
    def __init__(self, tolerance_ms: int = 200):
        self.tolerance_ms = tolerance_ms

    def validate_synchronised(self, df_s: pd.DataFrame, df_v: pd.DataFrame) -> bool:
        """
        Validates if the provided dataframes are already row-to-row synchronized.
        Checks if lengths match.
        """
        return len(df_s) == len(df_v)

    def sync_data(self, df_s: pd.DataFrame, df_v: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Synchronizes smartphone and vehicle data.
        If already same length (from the 'Synchronised' folder), just returns them.
        Otherwise, uses time-based nearest merge on timestamps.
        """
        if self.validate_synchronised(df_s, df_v):
            return df_s.copy(), df_v.copy()
            
        print("Data is unsynchronised. Applying time-based synchronization (merge_asof).")
        
        # We need absolute time or relative time from start.
        # Smartphone: ' TIME SINCE START (ms)'
        # Vehicle: ' Time Since Start of Day (seconds)'
        # We will assume they started at approximately the same time for this session.
        # This is a naive alignment for unsynchronized data.
        
        s_time_col = [c for c in df_s.columns if 'TIME SINCE START' in c][0]
        v_time_col = [c for c in df_v.columns if 'Time Since Start of Day' in c][0]
        
        df_s_copy = df_s.copy()
        df_v_copy = df_v.copy()
        
        # Convert to relative time in seconds, starting from 0
        df_s_copy['rel_time_s'] = (df_s_copy[s_time_col] - df_s_copy[s_time_col].iloc[0]) / 1000.0
        df_v_copy['rel_time_s'] = df_v_copy[v_time_col] - df_v_copy[v_time_col].iloc[0]
        
        # Sort for merge_asof
        df_s_copy = df_s_copy.sort_values('rel_time_s')
        df_v_copy = df_v_copy.sort_values('rel_time_s')
        
        # Merge S onto V to match the vehicle's ground truth timestamps
        merged = pd.merge_asof(
            df_v_copy, df_s_copy,
            on='rel_time_s',
            direction='nearest',
            tolerance=self.tolerance_ms / 1000.0
        )
        
        # Drop rows where smartphone data couldn't be matched within tolerance
        merged = merged.dropna(subset=[s_time_col])
        
        # Separate back into df_s and df_v with matched rows
        s_cols = df_s.columns.tolist()
        v_cols = df_v.columns.tolist()
        
        df_s_synced = merged[s_cols].copy()
        df_v_synced = merged[v_cols].copy()
        
        return df_s_synced, df_v_synced
