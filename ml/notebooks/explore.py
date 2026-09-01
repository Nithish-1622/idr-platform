import os
import pandas as pd
import glob

def explore_all_datasets():
    data_dir = r"E:\idr-platform\ml\data"
    all_csvs = glob.glob(os.path.join(data_dir, "**", "*.csv"), recursive=True)
    
    summary = []
    
    for file_path in all_csvs:
        filename = os.path.basename(file_path)
        is_s_data = filename.startswith("S-") or "S-Dataset" in file_path
        is_v_data = filename.startswith("V-") or "V-Dataset" in file_path
        
        try:
            # Using latin1 to avoid utf-8 decode errors
            df = pd.read_csv(file_path, encoding='latin1', on_bad_lines='skip')
            shape = df.shape
            nulls = df.isnull().sum().sum()
            
            # extract category and driver info from path
            rel_path = os.path.relpath(file_path, data_dir)
            
            summary.append({
                "path": rel_path,
                "type": "Smartphone" if is_s_data else ("Vehicle" if is_v_data else "Unknown"),
                "rows": shape[0],
                "cols": shape[1],
                "null_count": nulls
            })
            print(f"Processed: {rel_path} - Shape: {shape} - Nulls: {nulls}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            
    # Print summary
    print("\n--- DATASET EXPLORATION SUMMARY ---")
    summary_df = pd.DataFrame(summary)
    print(summary_df.to_string(index=False))
    
    # Save to a CSV for our records
    summary_df.to_csv(os.path.join(r"E:\idr-platform\ml\notebooks", "dataset_inventory.csv"), index=False)

if __name__ == "__main__":
    explore_all_datasets()
