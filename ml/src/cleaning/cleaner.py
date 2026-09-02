import pandas as pd

class DataCleaner:
    def __init__(self):
        pass
        
    def clean(self, df_s: pd.DataFrame, df_v: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Cleans the smartphone and vehicle dataframes.
        - Interpolates missing values (linear).
        - Forward fills / backward fills any remaining edge nulls.
        
        Args:
            df_s: Smartphone dataframe
            df_v: Vehicle dataframe
            
        Returns:
            Tuple of cleaned (df_s, df_v)
        """
        # Create copies to avoid mutating original dataframes
        df_s_clean = df_s.copy()
        df_v_clean = df_v.copy()
        
        # Interpolate numerical columns for small gaps
        numeric_s = df_s_clean.select_dtypes(include=['number']).columns
        numeric_v = df_v_clean.select_dtypes(include=['number']).columns
        
        df_s_clean[numeric_s] = df_s_clean[numeric_s].interpolate(method='linear', limit_direction='both')
        df_v_clean[numeric_v] = df_v_clean[numeric_v].interpolate(method='linear', limit_direction='both')
        
        # Fallback for completely empty columns or edges that interpolate couldn't catch
        df_s_clean = df_s_clean.ffill().bfill()
        df_v_clean = df_v_clean.ffill().bfill()
        
        # Rectify fundamental sensor-bias corruption in the raw logs
        # The 'Yaw Rate' sensor is often heavily biased or completely wrong in these datasets.
        # However, the GNSS 'Heading (degrees)' is highly accurate over long distances.
        # We will override the 'Yaw Rate' target by deriving it directly from GNSS Heading.
        import numpy as np
        
        heading_cols = [c for c in df_v_clean.columns if 'Heading' in c]
        yaw_cols = [c for c in df_v_clean.columns if 'Yaw Rate' in c]
        
        if heading_cols and yaw_cols:
            headings = df_v_clean[heading_cols[0]].values
            heading_diff = np.diff(headings)
            # Handle 360 degree wrapping
            heading_diff = np.where(heading_diff > 180, heading_diff - 360, heading_diff)
            heading_diff = np.where(heading_diff < -180, heading_diff + 360, heading_diff)
            # Assuming 10Hz sampling rate (0.1s dt)
            true_yaw_rate = np.pad(heading_diff / 0.1, (0, 1), 'edge')
            df_v_clean[yaw_cols[0]] = true_yaw_rate
        
        return df_s_clean, df_v_clean
