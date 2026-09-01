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
        
        return df_s_clean, df_v_clean
