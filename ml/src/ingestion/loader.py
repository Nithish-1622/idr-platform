import os
import pandas as pd
from typing import Tuple, Optional

class DatasetLoader:
    def __init__(self, data_root: str):
        self.data_root = data_root

    def load_session(self, s_file_path: str, v_file_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Loads the smartphone (S) and vehicle (V) CSV files for a single session.
        Handles the specific latin1 encoding required for the IO-VNBD dataset.
        
        Args:
            s_file_path: Absolute or relative path to the smartphone CSV
            v_file_path: Absolute or relative path to the vehicle CSV
            
        Returns:
            Tuple of (df_s, df_v)
        """
        full_s_path = os.path.join(self.data_root, s_file_path)
        full_v_path = os.path.join(self.data_root, v_file_path)
        
        if not os.path.exists(full_s_path):
            raise FileNotFoundError(f"Smartphone dataset not found: {full_s_path}")
        if not os.path.exists(full_v_path):
            raise FileNotFoundError(f"Vehicle dataset not found: {full_v_path}")
            
        # Using latin1 to bypass any hidden utf-8 decode errors (common in this dataset)
        df_s = pd.read_csv(full_s_path, encoding='latin1', on_bad_lines='skip')
        df_v = pd.read_csv(full_v_path, encoding='latin1', on_bad_lines='skip')
        
        # Clean column names by stripping leading/trailing whitespace
        df_s.columns = df_s.columns.str.strip()
        df_v.columns = df_v.columns.str.strip()
        
        return df_s, df_v
