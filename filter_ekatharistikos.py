#!/usr/bin/env python3
"""
Filter electricity bills data based on εκαθαριστικος field
"""

import pandas as pd
import glob
import os

def filter_ekatharistikos():
    # Target specific data files
    data_files = ['ολα.csv', 'φoπ.csv', 'επαγγελματικα.csv']
    
    # Combine all data
    all_data = []
    
    # Process CSV files
    for csv_file in data_files:
        if os.path.exists(csv_file):
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
                all_data.append(df)
                print(f"Processed {csv_file}: {len(df)} rows")
            except Exception as e:
                print(f"Error reading {csv_file}: {e}")
    
    if not all_data:
        print("No data files found")
        return
    
    # Combine all dataframes
    combined_df = pd.concat(all_data, ignore_index=True)
    print(f"Combined data: {len(combined_df)} rows")
    
    # Check if εκαθαριστικος column exists
    if 'Εκαθαριστικός' not in combined_df.columns:
        print("Column 'Εκαθαριστικός' not found in data")
        return
    
    # Show original counts
    true_count = len(combined_df[combined_df['Εκαθαριστικός'] == True])
    false_count = len(combined_df[combined_df['Εκαθαριστικός'] == False])
    print(f"Original - True: {true_count}, False: {false_count}")
    
    # Filter rows where εκαθαριστικος = True
    filtered_df = combined_df[combined_df['Εκαθαριστικός'] == True]
    print(f"Filtered data: {len(filtered_df)} rows")
    
    # Export to CSV
    filtered_df.to_csv('filtered.csv', index=False, encoding='utf-8-sig')
    
    # Export to XLSX
    filtered_df.to_excel('filtered.xlsx', index=False)
    
    print("Files created: filtered.csv, filtered.xlsx")

if __name__ == "__main__":
    filter_ekatharistikos()
