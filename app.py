import os
import time
from datetime import datetime
import pandas as pd

def run_pipeline():
    print("🚀 Starting Library Data Quality Pipeline...")
    start_time = time.time()
    
    # Define paths
    data_dir = "data"
    output_dir = "output"
    
    # CORRECTED FILE MAPPING:
    # Systembook.csv has the transaction details (id, books, checkout, etc.) -> borrowings
    # SystemCustomers.csv has the customer information -> customers
    customer_path = os.path.join(data_dir, "03_Library SystemCustomers.csv")       
    borrowings_path = os.path.join(data_dir, "03_Library Systembook.csv") 
    results_path = os.path.join(output_dir, "results.csv")
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if source files exist
    if not os.path.exists(customer_path) or not os.path.exists(borrowings_path):
        print("❌ Error: Source CSV files missing from 'data/' directory.")
        return

    # ==========================================
    # 1. INGESTION & HEADER NORMALIZATION
    # ==========================================
    print("📥 Ingesting source datasets...")
    df_customers = pd.read_csv(customer_path)
    df_borrowings = pd.read_csv(borrowings_path)
    
    # Force all headers to lowercase and strip whitespace to prevent KeyErrors
    df_customers.columns = df_customers.columns.str.strip().str.lower()
    df_borrowings.columns = df_borrowings.columns.str.strip().str.lower()
    
    # Track initial total records across both files
    total_raw_records = len(df_customers) + len(df_borrowings)
    
    # ==========================================
    # 2. CLEANING & TRANSFORMATION
    # ==========================================
    print("🧹 Cleaning data issues...")
    
    # --- Clean Customers ---
    # Drop duplicate customer profiles based on 'customer id'
    if 'customer id' in df_customers.columns:
        df_customers_clean = df_customers.drop_duplicates(subset=['customer id']).copy()
    else:
        df_customers_clean = df_customers.drop_duplicates().copy()
    
    # Fill missing customer names if the column exists
    if 'customer name' in df_customers_clean.columns:
        df_customers_clean['customer name'] = df_customers_clean['customer name'].fillna("Unknown Customer")
    
    # --- Clean Borrowings ---
    # Drop rows where critical transaction keys are entirely missing
    df_borrowings_clean = df_borrowings.dropna(subset=['id', 'customer id', 'books']).copy()
    
    # Deduplicate identical transaction logs
    df_borrowings_clean = df_borrowings_clean.drop_duplicates()
    
    # Issue: Inconsistent date handling for your actual date columns
    for date_col in ['book checkout', 'book returned']:
        if date_col in df_borrowings_clean.columns:
            df_borrowings_clean[date_col] = pd.to_datetime(df_borrowings_clean[date_col], errors='coerce')
            
    # Issue: Referential integrity (Drop customer IDs that don't exist in customer file)
    if 'customer id' in df_customers_clean.columns and 'customer id' in df_borrowings_clean.columns:
        valid_customer_ids = df_customers_clean['customer id'].unique()
        df_borrowings_clean = df_borrowings_clean[df_borrowings_clean['customer id'].isin(valid_customer_ids)]
    
    # ==========================================
    # 3. METRICS GATHERING
    # ==========================================
    print("📊 Calculating execution metrics...")
    
    # Calculate records processed and dropped
    total_cleaned_records = len(df_customers_clean) + len(df_borrowings_clean)
    records_dropped = total_raw_records - total_cleaned_records
    
    # Books & Customer specific counts
    unique_books_count = df_borrowings_clean['books'].nunique() if 'books' in df_borrowings_clean.columns else 0
    unique_customers_count = df_customers_clean['customer id'].nunique() if 'customer id' in df_customers_clean.columns else 0
    
    # Pipeline execution time
    execution_time_seconds = round(time.time() - start_time, 4)
    
    # ==========================================
    # 4. GENERATING THE RESULTS CSV
    # ==========================================
    metrics_summary = {
        "Execution_Timestamp": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Number_of_records_processed": [total_raw_records],
        "Number_of_records_dropped": [records_dropped],
        "Unique_Books_Count": [unique_books_count],
        "Unique_Customers_Count": [unique_customers_count],
        "Pipeline_Execution_Time_Sec": [execution_time_seconds]
    }
    
    df_results = pd.DataFrame(metrics_summary)
    
    # Write to local csv
    df_results.to_csv(results_path, index=False)
    print(f"💾 Results successfully exported to: {results_path}")
    print(f"⏱️ Total Execution Time: {execution_time_seconds} seconds\n")

if __name__ == "__main__":
    run_pipeline()