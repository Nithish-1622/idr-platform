import pandas as pd
import numpy as np
from sklearn.decomposition import PCA

class IMUAligner:
    def __init__(self):
        pass

    def align(self, df_s: pd.DataFrame) -> pd.DataFrame:
        """
        Aligns the smartphone IMU data.
        Since the exact mounting orientation in the vehicle is unknown, 
        this method computes rotation-invariant features and gravity-projected dynamics.
        
        Args:
            df_s: Cleaned and synchronized smartphone dataframe
            
        Returns:
            DataFrame with added aligned/invariant features
        """
        df_aligned = df_s.copy()
        
        # Dynamically find columns to avoid encoding issues with 'm/s²'
        acc_cols = [
            [c for c in df_aligned.columns if 'ACCELEROMETER X' in c][0],
            [c for c in df_aligned.columns if 'ACCELEROMETER Y' in c][0],
            [c for c in df_aligned.columns if 'ACCELEROMETER Z' in c][0]
        ]
        grav_cols = [
            [c for c in df_aligned.columns if 'GRAVITY X' in c][0],
            [c for c in df_aligned.columns if 'GRAVITY Y' in c][0],
            [c for c in df_aligned.columns if 'GRAVITY Z' in c][0]
        ]
        gyro_cols = [
            [c for c in df_aligned.columns if 'GYROSCOPE Yaw' in c][0],
            [c for c in df_aligned.columns if 'GYROSCOPE Pitch' in c][0],
            [c for c in df_aligned.columns if 'GYROSCOPE Roll' in c][0]
        ]
        
        # 1. Total Acceleration Magnitude (Rotation Invariant)
        df_aligned['ACC_MAG'] = np.sqrt(df_aligned[acc_cols[0]]**2 + 
                                        df_aligned[acc_cols[1]]**2 + 
                                        df_aligned[acc_cols[2]]**2)
                                        
        # 2. Total Gyroscope Magnitude (Rotation Invariant)
        df_aligned['GYRO_MAG'] = np.sqrt(df_aligned[gyro_cols[0]]**2 + 
                                         df_aligned[gyro_cols[1]]**2 + 
                                         df_aligned[gyro_cols[2]]**2)
                                         
        # 3. Dynamic Acceleration (Total Accel - Gravity)
        df_aligned['DYN_ACC_X'] = df_aligned[acc_cols[0]] - df_aligned[grav_cols[0]]
        df_aligned['DYN_ACC_Y'] = df_aligned[acc_cols[1]] - df_aligned[grav_cols[1]]
        df_aligned['DYN_ACC_Z'] = df_aligned[acc_cols[2]] - df_aligned[grav_cols[2]]
        
        # 4. Dynamic Acceleration Magnitude
        df_aligned['DYN_ACC_MAG'] = np.sqrt(df_aligned['DYN_ACC_X']**2 + 
                                            df_aligned['DYN_ACC_Y']**2 + 
                                            df_aligned['DYN_ACC_Z']**2)
                                            
        # 5. Gravity Projection (Horizontal Plane)
        # Unit gravity vector
        g_mag = np.sqrt(df_aligned[grav_cols[0]]**2 + df_aligned[grav_cols[1]]**2 + df_aligned[grav_cols[2]]**2) + 1e-8
        nx = df_aligned[grav_cols[0]] / g_mag
        ny = df_aligned[grav_cols[1]] / g_mag
        nz = df_aligned[grav_cols[2]] / g_mag
        
        # Dot product of dynamic acc and normal
        dot = df_aligned['DYN_ACC_X']*nx + df_aligned['DYN_ACC_Y']*ny + df_aligned['DYN_ACC_Z']*nz
        
        # Horizontal acceleration (subtracting vertical component)
        df_aligned['HORIZ_ACC_X'] = df_aligned['DYN_ACC_X'] - dot * nx
        df_aligned['HORIZ_ACC_Y'] = df_aligned['DYN_ACC_Y'] - dot * ny
        df_aligned['HORIZ_ACC_Z'] = df_aligned['DYN_ACC_Z'] - dot * nz
        
        # 6. PCA to find Forward and Lateral Axes
        horiz_acc = df_aligned[['HORIZ_ACC_X', 'HORIZ_ACC_Y', 'HORIZ_ACC_Z']].values
        
        pca = PCA(n_components=2)
        try:
            pca.fit(horiz_acc)
            pca_proj = pca.transform(horiz_acc)
            # The first principal component is assumed to be the Forward axis
            df_aligned['FORWARD_ACC'] = pca_proj[:, 0]
            # The second principal component is the Lateral axis
            df_aligned['LATERAL_ACC'] = pca_proj[:, 1]
        except Exception:
            # Fallback if PCA fails
            df_aligned['FORWARD_ACC'] = 0.0
            df_aligned['LATERAL_ACC'] = 0.0
        # 7. Projected Yaw Rate (Yaw around Gravity axis)
        df_aligned['PROJ_YAW'] = df_aligned[gyro_cols[0]]*nx + df_aligned[gyro_cols[1]]*ny + df_aligned[gyro_cols[2]]*nz
        
        # 8. Horizontal Acceleration Magnitude (Alternative Rotation-Invariant Feature)
        df_aligned['HORIZ_ACC_MAG'] = np.sqrt(df_aligned['HORIZ_ACC_X']**2 + 
                                              df_aligned['HORIZ_ACC_Y']**2 + 
                                              df_aligned['HORIZ_ACC_Z']**2)
                                              
        return df_aligned
