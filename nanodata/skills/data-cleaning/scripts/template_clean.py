"""
TEMPLATE: Data Cleaning Script
INSTRUCTION FOR AGENT:
1. Copy this code.
2. Replace 'INPUT_PATH' and 'OUTPUT_PATH' with actual paths.
3. Fill in the 'Cleaning Logic' section.
4. Run via python_executor.
"""

import pandas as pd
import numpy as np
import sys
import os

# Configuration
INPUT_PATH = "INPUT_PATH_HERE"   # Agent to replace
OUTPUT_PATH = "OUTPUT_PATH_HERE" # Agent to replace

def clean_data():
    print(f"[INFO] Loading data from {INPUT_PATH}...")
    
    # 1. Load Data (Auto-detect format)
    try:
        if INPUT_PATH.endswith('.csv'):
            df = pd.read_csv(INPUT_PATH)
        elif INPUT_PATH.endswith(('.xls', '.xlsx')):
            df = pd.read_excel(INPUT_PATH)
        elif INPUT_PATH.endswith('.parquet'):
            df = pd.read_parquet(INPUT_PATH)
        else:
            raise ValueError("Unsupported file format")
    except Exception as e:
        print(f"[FATAL] Failed to load data: {e}")
        sys.exit(1)

    print(f"[INFO] Initial Shape: {df.shape}")

    # ==========================================
    # SECTION: Cleaning Logic (Agent Fills This)
    # ==========================================
    
    # Example: df.drop_duplicates(inplace=True)
    # Example: df['date'] = pd.to_datetime(df['date'])
    # Example: df.fillna(0, inplace=True)
    
    # <YOUR CODE HERE>

    # ==========================================
    # END SECTION
    # ==========================================

    # Validation
    if df.empty:
        print("[WARN] Resulting dataset is empty!")
    
    # 3. Save Data
    print(f"[INFO] Saving cleaned data to {OUTPUT_PATH}...")
    if OUTPUT_PATH.endswith('.parquet'):
        df.to_parquet(OUTPUT_PATH, index=False)
    else:
        df.to_csv(OUTPUT_PATH, index=False)
        
    print(f"[SUCCESS] Process Complete. Final Shape: {df.shape}")
    print("AGENT REMINDER: Do not stop here. You MUST now proceed to Phase 4: Generate the Dataset Card.")

if __name__ == "__main__":
    clean_data()