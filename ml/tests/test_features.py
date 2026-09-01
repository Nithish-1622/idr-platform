import numpy as np
import pandas as pd
from src.features.engineer import FeatureEngineer

def test_feature_engineer():
    engineer = FeatureEngineer(window_size=10)
    
    # Create dummy aligned df
    df_aligned = pd.DataFrame({
        'ACC_MAG': np.random.rand(100),
        'GYRO_MAG': np.random.rand(100),
        'DYN_ACC_MAG': np.random.rand(100)
    })
    
    # Create dummy vehicle df
    df_v = pd.DataFrame({
        'Velocity (km/hr)': np.random.rand(100),
        'Yaw Rate (deg/sec)': np.random.rand(100)
    })
    
    X_2d, X_3d, y = engineer.generate_features(df_aligned, df_v)
    
    assert X_3d.shape == (91, 10, 3) # 100 - 10 + 1 = 91 samples
    assert X_2d.shape == (91, 30) # flattened
    assert y.shape == (91, 2)
