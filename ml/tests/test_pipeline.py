import os
import pytest
import pandas as pd
from src.ingestion.loader import DatasetLoader
from src.cleaning.cleaner import DataCleaner
from src.synchronization.sync import Synchronizer
from src.alignment.aligner import IMUAligner

def test_full_pipeline():
    # We will use the M (Driver B) dataset as a test case
    data_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
    
    # Check if the dataset exists locally for testing
    s_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\M (Driver B)\S-M.csv"
    v_path = r"Synchronised V abd S datasets\Categorised IOVNB Dataset\M (Driver B)\V-M.csv"
    
    full_s = os.path.join(data_root, s_path)
    if not os.path.exists(full_s):
        pytest.skip(f"Test dataset not found locally: {full_s}")
        
    loader = DatasetLoader(data_root)
    df_s, df_v = loader.load_session(s_path, v_path)
    
    assert len(df_s) > 0
    assert len(df_v) > 0
    
    cleaner = DataCleaner()
    df_s_clean, df_v_clean = cleaner.clean(df_s, df_v)
    
    # Ensure no nulls
    assert df_s_clean.isnull().sum().sum() == 0
    assert df_v_clean.isnull().sum().sum() == 0
    
    sync = Synchronizer()
    df_s_sync, df_v_sync = sync.sync_data(df_s_clean, df_v_clean)
    
    assert len(df_s_sync) == len(df_v_sync)
    
    # Check if aligner works with column names
    aligner = IMUAligner()
    try:
        df_aligned = aligner.align(df_s_sync)
        assert 'ACC_MAG' in df_aligned.columns
    except KeyError as e:
        pytest.fail(f"KeyError during alignment: {e}")
