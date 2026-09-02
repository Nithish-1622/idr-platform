import pandas as pd
import numpy as np

df_s = pd.read_csv(r'e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vf (Driver E)\V-Vfa01\S-Vfa01.csv', encoding='latin1')
df_v = pd.read_csv(r'e:\idr-platform\ml\data\Synchronised V abd S datasets\Categorised IOVNB Dataset\Vf (Driver E)\V-Vfa01\V-Vfa01.csv')

df_v.columns = df_v.columns.str.strip()
df_s.columns = df_s.columns.str.strip()

acc_cols = [
    [c for c in df_s.columns if 'ACCELEROMETER X' in c][0],
    [c for c in df_s.columns if 'ACCELEROMETER Y' in c][0],
    [c for c in df_s.columns if 'ACCELEROMETER Z' in c][0]
]

true_acc = np.diff(df_v['Velocity (km/hr)'].values / 3.6) / 0.1
true_acc = np.pad(true_acc, (0, 1), 'edge')

acc_mag = np.sqrt(df_s[acc_cols[0]].values**2 + 
                  df_s[acc_cols[1]].values**2 + 
                  df_s[acc_cols[2]].values**2)
                  
dyn_acc_mag = np.abs(acc_mag - 9.81)

corrs = []
for shift in range(-5000, 5000, 10):
    v_shifted = true_acc[max(0, shift) : min(len(true_acc), len(true_acc)+shift)]
    s_shifted = dyn_acc_mag[max(0, -shift) : min(len(dyn_acc_mag), len(dyn_acc_mag)-shift)]
    if len(v_shifted) > 0:
        corrs.append((shift, np.corrcoef(v_shifted, s_shifted)[0,1]))

best = max(corrs, key=lambda x: x[1])
print('Best shift for Vfa01 (10Hz steps):', best)
